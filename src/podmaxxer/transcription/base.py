from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from podmaxxer.content import Content, ContentKind
from podmaxxer.errors import TranscriptionError
from podmaxxer.transcription import whisper_backend
from podmaxxer.transcription.existing import find_sidecar_transcript

Transcriber = Callable[[Path], str]


def get_transcript(content: Content, transcriber: Transcriber | None = None) -> tuple[str, str]:
    """Return (text, source). Prefers existing text, then sidecar files, then local Whisper."""
    if content.kind is ContentKind.TEXT:
        if content.text is None:
            raise TranscriptionError(f"Text content has no text: {content.source_uri}")
        return content.text, "existing"
    if content.path is None:
        raise TranscriptionError(f"Media content has no file: {content.source_uri}")
    sidecar = find_sidecar_transcript(content.path)
    if sidecar is not None:
        return sidecar, "existing"
    transcribe = transcriber or whisper_backend.transcribe
    return transcribe(content.path), "whisper"
