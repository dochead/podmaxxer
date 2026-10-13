from __future__ import annotations

from pathlib import Path

from faster_whisper import WhisperModel

from podmaxxer.config import get_whisper_model
from podmaxxer.errors import TranscriptionError

_MODEL_CACHE: dict[str, WhisperModel] = {}


def _get_model(model_size: str) -> WhisperModel:
    if model_size not in _MODEL_CACHE:
        # Local-only: runs on this machine, so transcription costs nothing per minute.
        _MODEL_CACHE[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _MODEL_CACHE[model_size]


def transcribe(path: Path, model_size: str | None = None) -> str:
    size = model_size or get_whisper_model()
    try:
        model = _get_model(size)
        segments, _info = model.transcribe(str(path))
        return " ".join(segment.text.strip() for segment in segments)
    except Exception as exc:
        raise TranscriptionError(f"Whisper transcription failed for {path}: {exc}") from exc
