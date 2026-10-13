from __future__ import annotations

from pathlib import Path

SIDECAR_SUFFIXES = (".txt", ".vtt", ".srt")


def find_sidecar_transcript(media_path: Path) -> str | None:
    for suffix in SIDECAR_SUFFIXES:
        candidate = media_path.with_suffix(suffix)
        if candidate.exists():
            return _clean(candidate.read_text(encoding="utf-8"), suffix)
    return None


def _clean(raw: str, suffix: str) -> str:
    if suffix == ".txt":
        return raw.strip()
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "WEBVTT" or stripped.isdigit() or "-->" in stripped:
            continue
        lines.append(stripped)
    return " ".join(lines)
