from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import trafilatura

from podmaxxer.content import (
    Content,
    ContentKind,
    detect_kind_from_suffix,
    hash_bytes,
    hash_text,
)
from podmaxxer.errors import UnsupportedContentError


@dataclass
class LocalFileSource:
    path: Path

    def fetch(self) -> Content:
        kind = detect_kind_from_suffix(self.path.suffix)
        if kind is ContentKind.AUDIO_VIDEO:
            data = self.path.read_bytes()
            return Content(
                kind=kind,
                source_uri=str(self.path),
                content_hash=hash_bytes(data),
                path=self.path,
            )
        text = self._read_text()
        return Content(
            kind=kind,
            source_uri=str(self.path),
            content_hash=hash_text(text),
            text=text,
        )

    def _read_text(self) -> str:
        raw = self.path.read_text(encoding="utf-8")
        if self.path.suffix.lower() in (".html", ".htm"):
            extracted = trafilatura.extract(raw)
            if not extracted:
                raise UnsupportedContentError(f"Could not extract article text from {self.path}")
            return extracted
        return raw
