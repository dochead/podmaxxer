from __future__ import annotations

from typing import Protocol

from podmaxxer.content import Content


class Source(Protocol):
    def fetch(self) -> Content: ...
