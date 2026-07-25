from __future__ import annotations

import os
from pathlib import Path

import platformdirs


def get_state_db_path() -> Path:
    override = os.environ.get("PODMAXXER_STATE_DB")
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir("podmaxxer")) / "state.db"
