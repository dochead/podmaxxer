from __future__ import annotations

import sqlite3
from pathlib import Path

from podmaxxer.sources.base import Source
from podmaxxer.state import repository
from podmaxxer.summarize.summarizer import summarize
from podmaxxer.summarize.templates import load_template
from podmaxxer.transcription.base import get_transcript


def process(
    source: Source,
    conn: sqlite3.Connection,
    api_key: str,
    template_path: Path | None = None,
) -> str:
    content = source.fetch()
    repository.upsert_item(conn, content.content_hash, content.kind.value, content.source_uri)

    try:
        transcript = repository.get_transcript(conn, content.content_hash)
        if transcript is None:
            transcript, transcript_source = get_transcript(content)
            repository.save_transcript(conn, content.content_hash, transcript, transcript_source)
    finally:
        if content.is_temp and content.path is not None:
            content.path.unlink(missing_ok=True)

    template_text, template_hash = load_template(template_path)

    summary = repository.get_summary(conn, content.content_hash, template_hash)
    if summary is None:
        summary = summarize(template_text, transcript, api_key)
        repository.save_summary(conn, content.content_hash, template_hash, summary)

    return summary
