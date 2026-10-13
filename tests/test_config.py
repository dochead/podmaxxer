from pathlib import Path

from podmaxxer.config import get_state_db_path


def test_uses_env_override(monkeypatch):
    monkeypatch.setenv("PODMAXXER_STATE_DB", "/tmp/custom/state.db")
    assert get_state_db_path() == Path("/tmp/custom/state.db")


def test_falls_back_to_platformdirs_default(monkeypatch):
    monkeypatch.delenv("PODMAXXER_STATE_DB", raising=False)
    path = get_state_db_path()
    assert path.name == "state.db"
    assert "podmaxxer" in str(path).lower()
