from __future__ import annotations

import sqlite3


def upsert_item(conn: sqlite3.Connection, content_hash: str, source_kind: str, source_uri: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO items (content_hash, source_kind, source_uri) VALUES (?, ?, ?)",
        (content_hash, source_kind, source_uri),
    )
    conn.commit()


def get_transcript(conn: sqlite3.Connection, content_hash: str) -> str | None:
    row = conn.execute(
        "SELECT text FROM transcripts WHERE content_hash = ?", (content_hash,)
    ).fetchone()
    return row[0] if row else None


def save_transcript(conn: sqlite3.Connection, content_hash: str, text: str, source: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO transcripts (content_hash, text, source) VALUES (?, ?, ?)",
        (content_hash, text, source),
    )
    conn.commit()


def get_summary(conn: sqlite3.Connection, content_hash: str, template_hash: str) -> str | None:
    row = conn.execute(
        "SELECT summary_text FROM summaries WHERE content_hash = ? AND template_hash = ?",
        (content_hash, template_hash),
    ).fetchone()
    return row[0] if row else None


def save_summary(conn: sqlite3.Connection, content_hash: str, template_hash: str, summary_text: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO summaries (content_hash, template_hash, summary_text) VALUES (?, ?, ?)",
        (content_hash, template_hash, summary_text),
    )
    conn.commit()
