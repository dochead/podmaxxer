from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura

from podmaxxer.content import (
    Content,
    ContentKind,
    detect_kind_from_content_type,
    detect_kind_from_suffix,
    hash_bytes,
    hash_text,
)
from podmaxxer.errors import FetchError, UnsupportedContentError


@dataclass
class UrlSource:
    url: str
    session: requests.Session = field(default_factory=requests.Session)

    def fetch(self) -> Content:
        try:
            response = self.session.get(self.url, timeout=60)
        except requests.RequestException as exc:
            raise FetchError(f"Failed to fetch {self.url}: {exc}") from exc
        if response.status_code != 200:
            raise FetchError(f"Failed to fetch {self.url}: HTTP {response.status_code}")

        content_type = response.headers.get("Content-Type", "")
        kind = self._detect_kind(content_type)

        if kind is ContentKind.AUDIO_VIDEO:
            return self._audio_video_content(response.content)
        return self._text_content(response.text, content_type)

    def _detect_kind(self, content_type: str) -> ContentKind:
        try:
            return detect_kind_from_content_type(content_type)
        except UnsupportedContentError:
            suffix = Path(urlparse(self.url).path).suffix
            return detect_kind_from_suffix(suffix)

    def _audio_video_content(self, data: bytes) -> Content:
        suffix = Path(urlparse(self.url).path).suffix or ".media"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        return Content(
            kind=ContentKind.AUDIO_VIDEO,
            source_uri=self.url,
            content_hash=hash_bytes(data),
            path=Path(tmp_path),
            is_temp=True,
        )

    def _text_content(self, raw_text: str, content_type: str) -> Content:
        text = raw_text
        if "html" in content_type.lower():
            extracted = trafilatura.extract(raw_text)
            if not extracted:
                raise UnsupportedContentError(f"Could not extract article text from {self.url}")
            text = extracted
        return Content(
            kind=ContentKind.TEXT,
            source_uri=self.url,
            content_hash=hash_text(text),
            text=text,
        )
