from podmaxxer import pipeline
from podmaxxer.content import Content, ContentKind
from podmaxxer.state.db import connect


class FakeSource:
    def __init__(self, content):
        self._content = content

    def fetch(self):
        return self._content


def test_process_runs_all_stages_and_persists_state(tmp_path):
    conn = connect(":memory:")
    content = Content(
        kind=ContentKind.TEXT, source_uri="x", content_hash="h1", text="raw transcript"
    )
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    result = pipeline.process(
        FakeSource(content),
        conn,
        api_key=None,
        template_path=template_path,
        llm=lambda p: f"SUMMARY({p.splitlines()[-1]})",
    )

    assert result == "SUMMARY(raw transcript)"
    assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM summaries").fetchone()[0] == 1


def test_process_skips_summarize_call_when_already_cached(tmp_path):
    conn = connect(":memory:")
    content = Content(
        kind=ContentKind.TEXT, source_uri="x", content_hash="h1", text="raw transcript"
    )
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    calls = []

    def fake_llm(prompt):
        calls.append(prompt)
        return "SUMMARY"

    for _ in range(2):
        pipeline.process(
            FakeSource(content), conn, api_key=None, template_path=template_path, llm=fake_llm
        )

    assert len(calls) == 1


def test_process_deletes_temp_file_after_use(tmp_path):
    conn = connect(":memory:")
    media_path = tmp_path / "episode.mp3"
    media_path.write_bytes(b"audio")
    content = Content(
        kind=ContentKind.AUDIO_VIDEO,
        source_uri="https://example.com/episode.mp3",
        content_hash="h1",
        path=media_path,
        is_temp=True,
    )
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    pipeline.process(
        FakeSource(content),
        conn,
        None,
        template_path,
        transcriber=lambda p: "transcript text",
        llm=lambda p: "SUMMARY",
    )

    assert not media_path.exists()


def test_process_does_not_delete_non_temp_file(tmp_path):
    conn = connect(":memory:")
    media_path = tmp_path / "episode.mp3"
    media_path.write_bytes(b"audio")
    content = Content(
        kind=ContentKind.AUDIO_VIDEO,
        source_uri="/local/episode.mp3",
        content_hash="h1",
        path=media_path,
        is_temp=False,
    )
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    pipeline.process(
        FakeSource(content),
        conn,
        None,
        template_path,
        transcriber=lambda p: "transcript text",
        llm=lambda p: "SUMMARY",
    )

    assert media_path.exists()


def test_process_cleans_temp_file_even_when_transcription_fails(tmp_path):
    conn = connect(":memory:")
    media_path = tmp_path / "episode.mp3"
    media_path.write_bytes(b"audio")
    content = Content(
        kind=ContentKind.AUDIO_VIDEO,
        source_uri="u",
        content_hash="h1",
        path=media_path,
        is_temp=True,
    )

    def boom(path):
        raise RuntimeError("transcription exploded")

    try:
        pipeline.process(FakeSource(content), conn, None, transcriber=boom, llm=lambda p: "S")
    except RuntimeError:
        pass

    assert not media_path.exists()
