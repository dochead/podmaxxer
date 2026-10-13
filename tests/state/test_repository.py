from podmaxxer.state import repository
from podmaxxer.state.db import connect


def _conn():
    return connect(":memory:")


def test_upsert_item_is_idempotent():
    conn = _conn()
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    rows = conn.execute("SELECT content_hash FROM items").fetchall()
    assert len(rows) == 1


def test_transcript_round_trip():
    conn = _conn()
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    assert repository.get_transcript(conn, "hash1") is None
    repository.save_transcript(conn, "hash1", "hello world", "existing")
    assert repository.get_transcript(conn, "hash1") == "hello world"


def test_summary_round_trip_keyed_by_template():
    conn = _conn()
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    assert repository.get_summary(conn, "hash1", "tmpl-a") is None
    repository.save_summary(conn, "hash1", "tmpl-a", "summary A")
    repository.save_summary(conn, "hash1", "tmpl-b", "summary B")
    assert repository.get_summary(conn, "hash1", "tmpl-a") == "summary A"
    assert repository.get_summary(conn, "hash1", "tmpl-b") == "summary B"
