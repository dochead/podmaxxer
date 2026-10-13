from __future__ import annotations

import os
from pathlib import Path

import platformdirs

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
# Cheapest model of the current OpenAI generation (checked 2026-10).
DEFAULT_SUMMARY_MODEL = "gpt-6-luna"
DEFAULT_WHISPER_MODEL = "small"


def get_state_db_path() -> Path:
    override = os.environ.get("PODMAXXER_STATE_DB")
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir("podmaxxer")) / "state.db"


def get_openai_base_url() -> str:
    """Any OpenAI-compatible endpoint works, e.g. a local Ollama/llama.cpp server."""
    return os.environ.get("PODMAXXER_OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL).rstrip("/")


def get_summary_model() -> str:
    return os.environ.get("PODMAXXER_MODEL", DEFAULT_SUMMARY_MODEL)


def get_whisper_model() -> str:
    return os.environ.get("PODMAXXER_WHISPER_MODEL", DEFAULT_WHISPER_MODEL)


def uses_default_openai() -> bool:
    return get_openai_base_url() == DEFAULT_OPENAI_BASE_URL
