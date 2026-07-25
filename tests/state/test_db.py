from podmaxxer.state.db import connect


def test_connect_creates_expected_tables():
    conn = connect(":memory:")
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"items", "transcripts", "summaries"} <= tables
    conn.close()


def test_connect_creates_parent_dir(tmp_path):
    db_path = tmp_path / "nested" / "state.db"
    conn = connect(db_path)
    assert db_path.parent.is_dir()
    conn.close()
