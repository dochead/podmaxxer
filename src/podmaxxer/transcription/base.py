from __future__ import annotations

from podmaxxer.content import Content, ContentKind
from podmaxxer.transcription.existing import find_sidecar_transcript
from podmaxxer.transcription.whisper_backend import transcribe as whisper_transcribe


def get_transcript(content: Content) -> tuple[str, str]:
    if content.kind is ContentKind.TEXT:
        return content.text, "existing"
    sidecar = find_sidecar_transcript(content.path)
    if sidecar is not None:
        return sidecar, "existing"
    return whisper_transcribe(content.path), "whisper"
