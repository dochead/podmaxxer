import pytest

from podmaxxer.content import ContentKind
from podmaxxer.errors import UnsupportedContentError
from podmaxxer.sources.local_file import LocalFileSource


def test_fetch_text_file(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello world", encoding="utf-8")

    content = LocalFileSource(path=path).fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "hello world"
    assert content.source_uri == str(path)
    assert content.content_hash


def test_fetch_html_file_extracts_article_text(tmp_path, monkeypatch):
    path = tmp_path / "article.html"
    path.write_text("<html><body><p>Real article text.</p></body></html>", encoding="utf-8")

    import podmaxxer.sources.local_file as local_file_module
    monkeypatch.setattr(local_file_module.trafilatura, "extract", lambda raw: "Real article text.")

    content = LocalFileSource(path=path).fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "Real article text."


def test_fetch_html_file_raises_if_extraction_fails(tmp_path, monkeypatch):
    path = tmp_path / "article.html"
    path.write_text("<html></html>", encoding="utf-8")

    import podmaxxer.sources.local_file as local_file_module
    monkeypatch.setattr(local_file_module.trafilatura, "extract", lambda raw: None)

    with pytest.raises(UnsupportedContentError):
        LocalFileSource(path=path).fetch()


def test_fetch_audio_file(tmp_path):
    path = tmp_path / "episode.mp3"
    path.write_bytes(b"fake-audio-bytes")

    content = LocalFileSource(path=path).fetch()

    assert content.kind == ContentKind.AUDIO_VIDEO
    assert content.path == path
    assert content.text is None
    assert content.content_hash
