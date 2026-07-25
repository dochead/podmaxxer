from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from podmaxxer.errors import UnsupportedContentError


class ContentKind(str, Enum):
    AUDIO_VIDEO = "audio_video"
    TEXT = "text"


AUDIO_VIDEO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".flac", ".ogg",
    ".mp4", ".mov", ".mkv", ".webm",
}
TEXT_EXTENSIONS = {".txt", ".md"}
HTML_EXTENSIONS = {".html", ".htm"}


def detect_kind_from_suffix(suffix: str) -> ContentKind:
    suffix = suffix.lower()
    if suffix in AUDIO_VIDEO_EXTENSIONS:
        return ContentKind.AUDIO_VIDEO
    if suffix in TEXT_EXTENSIONS or suffix in HTML_EXTENSIONS:
        return ContentKind.TEXT
    raise UnsupportedContentError(f"Unrecognized file extension: {suffix!r}")


def detect_kind_from_content_type(content_type: str) -> ContentKind:
    normalized = content_type.split(";")[0].strip().lower()
    if normalized.startswith(("audio/", "video/")):
        return ContentKind.AUDIO_VIDEO
    if normalized in ("text/html", "text/plain"):
        return ContentKind.TEXT
    raise UnsupportedContentError(f"Unsupported content type: {content_type!r}")


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))


@dataclass(frozen=True)
class Content:
    kind: ContentKind
    source_uri: str
    content_hash: str
    path: Path | None = None
    text: str | None = None
