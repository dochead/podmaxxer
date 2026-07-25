from podmaxxer import pipeline
from podmaxxer.content import Content, ContentKind
from podmaxxer.state.db import connect


class FakeSource:
    def __init__(self, content):
        self._content = content

    def fetch(self):
        return self._content


def test_process_runs_all_stages_and_persists_state(monkeypatch, tmp_path):
    conn = connect(":memory:")
    content = Content(kind=ContentKind.TEXT, source_uri="x", content_hash="h1", text="raw transcript")
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    monkeypatch.setattr(pipeline, "summarize", lambda template, transcript, api_key: f"SUMMARY({transcript})")

    result = pipeline.process(FakeSource(content), conn, api_key="sk-test", template_path=template_path)

    assert result == "SUMMARY(raw transcript)"
    assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM summaries").fetchone()[0] == 1


def test_process_skips_summarize_call_when_already_cached(monkeypatch, tmp_path):
    conn = connect(":memory:")
    content = Content(kind=ContentKind.TEXT, source_uri="x", content_hash="h1", text="raw transcript")
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    calls = []
    monkeypatch.setattr(pipeline, "summarize", lambda template, transcript, api_key: calls.append(1) or "SUMMARY")

    pipeline.process(FakeSource(content), conn, api_key="sk-test", template_path=template_path)
    pipeline.process(FakeSource(content), conn, api_key="sk-test", template_path=template_path)

    assert len(calls) == 1
