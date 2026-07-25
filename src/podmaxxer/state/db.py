from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    content_hash TEXT PRIMARY KEY,
    source_kind TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transcripts (
    content_hash TEXT PRIMARY KEY REFERENCES items(content_hash),
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS summaries (
    content_hash TEXT NOT NULL REFERENCES items(content_hash),
    template_hash TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (content_hash, template_hash)
);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
