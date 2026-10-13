import responses

from podmaxxer.content import ContentKind
from podmaxxer.sources.remote_url import UrlSource


@responses.activate
def test_fetch_text_plain():
    responses.add(
        responses.GET,
        "https://example.com/notes.txt",
        body="hello from the web",
        status=200,
        content_type="text/plain",
    )

    content = UrlSource(url="https://example.com/notes.txt").fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "hello from the web"
    assert content.source_uri == "https://example.com/notes.txt"


@responses.activate
def test_fetch_html_extracts_article_text(monkeypatch):
    responses.add(
        responses.GET,
        "https://example.com/article",
        body="<html><body><p>Real article text.</p></body></html>",
        status=200,
        content_type="text/html; charset=utf-8",
    )

    import podmaxxer.sources.remote_url as remote_url_module

    monkeypatch.setattr(remote_url_module.trafilatura, "extract", lambda raw: "Real article text.")

    content = UrlSource(url="https://example.com/article").fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "Real article text."


@responses.activate
def test_fetch_audio_saves_to_temp_file():
    responses.add(
        responses.GET,
        "https://example.com/episode.mp3",
        body=b"fake-audio-bytes",
        status=200,
        content_type="audio/mpeg",
    )

    content = UrlSource(url="https://example.com/episode.mp3").fetch()

    assert content.kind == ContentKind.AUDIO_VIDEO
    assert content.path is not None
    assert content.path.read_bytes() == b"fake-audio-bytes"
    assert content.is_temp is True


@responses.activate
def test_fetch_audio_strips_query_string_from_temp_suffix():
    responses.add(
        responses.GET,
        "https://cdn.example.com/episode.mp3?token=abc123&exp=999",
        body=b"fake-audio-bytes",
        status=200,
        content_type="audio/mpeg",
    )

    content = UrlSource(url="https://cdn.example.com/episode.mp3?token=abc123&exp=999").fetch()

    assert content.path.suffix == ".mp3"


@responses.activate
def test_fetch_raises_on_http_error():
    from podmaxxer.errors import FetchError

    responses.add(responses.GET, "https://example.com/missing.mp3", status=404)

    try:
        UrlSource(url="https://example.com/missing.mp3").fetch()
        assert False, "expected FetchError"
    except FetchError:
        pass


@responses.activate
def test_fetch_falls_back_to_url_extension_when_content_type_is_generic():
    responses.add(
        responses.GET,
        "https://cdn.example.com/episode.mp3",
        body=b"fake-audio-bytes",
        status=200,
        content_type="application/octet-stream",
    )

    content = UrlSource(url="https://cdn.example.com/episode.mp3").fetch()

    assert content.kind == ContentKind.AUDIO_VIDEO
    assert content.path.read_bytes() == b"fake-audio-bytes"


@responses.activate
def test_fetch_raises_when_content_type_and_extension_both_unrecognized():
    from podmaxxer.errors import UnsupportedContentError

    responses.add(
        responses.GET,
        "https://cdn.example.com/episode.xyz",
        body=b"???",
        status=200,
        content_type="application/octet-stream",
    )

    try:
        UrlSource(url="https://cdn.example.com/episode.xyz").fetch()
        assert False, "expected UnsupportedContentError"
    except UnsupportedContentError:
        pass
