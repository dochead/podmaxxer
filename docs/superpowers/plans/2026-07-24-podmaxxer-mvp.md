# Podmaxxer MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working MVP of Podmaxxer: a Click CLI that takes a local file or direct URL (audio/video or text article), gets a transcript (existing sidecar or local Whisper), summarizes it against a plain-text template via the OpenAI API, and prints the summary — with SQLite-backed resumability at every stage.

**Architecture:** Stage-per-module pipeline (`sources` → `transcription` → `summarize`) coordinated by `pipeline.py`, with idempotency checks living entirely in `state/repository.py`. Input kinds implement a `Source.fetch() -> Content` protocol so RSS/YouTube can be added later without touching downstream code. See `docs/superpowers/specs/2026-07-24-podmaxxer-mvp-design.md` for the full design and `docs/decisions/` for ADRs.

**Tech Stack:** Python (`uv`-managed), Click, Requests, faster-whisper, trafilatura, platformdirs, SQLite (stdlib `sqlite3`). Dev: pytest, ruff, `responses` (HTTP mocking).

---

## File Structure

```
pyproject.toml
src/podmaxxer/
  __init__.py
  errors.py
  content.py
  config.py
  pipeline.py
  cli.py
  templates/
    default.txt
  sources/
    __init__.py
    base.py
    local_file.py
    remote_url.py
  transcription/
    __init__.py
    base.py
    existing.py
    whisper_backend.py
  summarize/
    __init__.py
    templates.py
    openai_client.py
    summarizer.py
  state/
    __init__.py
    db.py
    repository.py
tests/
  test_content.py
  test_config.py
  sources/test_local_file.py
  sources/test_remote_url.py
  transcription/test_existing.py
  transcription/test_whisper_backend.py
  transcription/test_base.py
  summarize/test_templates.py
  summarize/test_openai_client.py
  summarize/test_summarizer.py
  state/test_db.py
  state/test_repository.py
  test_pipeline.py
  test_cli.py
```

---

### Task 1: Project scaffolding with uv

**Files:**
- Create: `pyproject.toml` (via `uv init`)
- Create: `src/podmaxxer/__init__.py`, `src/podmaxxer/sources/__init__.py`, `src/podmaxxer/transcription/__init__.py`, `src/podmaxxer/summarize/__init__.py`, `src/podmaxxer/state/__init__.py`
- Create: `tests/sources/`, `tests/transcription/`, `tests/summarize/`, `tests/state/` (empty dirs, will hold test files)

- [ ] **Step 1: Initialize the uv package**

Run from repo root:
```bash
uv init --package --name podmaxxer .
```
Expected: creates `pyproject.toml`, `src/podmaxxer/__init__.py`. If it also creates a `README.md` that conflicts with plans for Task 17, leave it for now — Task 17 will overwrite it.

- [ ] **Step 2: Add runtime dependencies**

```bash
uv add click requests faster-whisper trafilatura platformdirs
```
Expected: `pyproject.toml` gains a `[project] dependencies = [...]` list; `uv.lock` is created/updated.

- [ ] **Step 3: Add dev dependencies**

```bash
uv add --dev pytest ruff responses
```
Expected: `pyproject.toml` gains `[dependency-groups] dev = [...]`.

- [ ] **Step 4: Create package subpackage skeleton**

```bash
mkdir -p src/podmaxxer/sources src/podmaxxer/transcription src/podmaxxer/summarize src/podmaxxer/state src/podmaxxer/templates
touch src/podmaxxer/sources/__init__.py src/podmaxxer/transcription/__init__.py src/podmaxxer/summarize/__init__.py src/podmaxxer/state/__init__.py
mkdir -p tests/sources tests/transcription tests/summarize tests/state
```

- [ ] **Step 5: Add `[project.scripts]` entry point**

Edit `pyproject.toml`, add under `[project]`:
```toml
[project.scripts]
podmaxxer = "podmaxxer.cli:main"
```
(`cli.py` doesn't exist yet — that's fine, it's created in Task 16.)

- [ ] **Step 6: Sync and verify**

```bash
uv sync
uv run python -c "import podmaxxer; print('ok')"
```
Expected: `ok` printed, no import errors.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock src/ tests/
git commit -m "chore: scaffold podmaxxer as a uv-managed Python package"
```

---

### Task 2: Errors module

**Files:**
- Create: `src/podmaxxer/errors.py`
- Test: `tests/test_errors.py` (Not implementing this as its own test — errors are exercised via consumers in later tasks. Skip standalone test for this trivial module; proceed directly to implementation.)

- [ ] **Step 1: Write the module**

```python
# src/podmaxxer/errors.py
class PodmaxxerError(Exception):
    """Base class for all Podmaxxer errors."""


class UnsupportedContentError(PodmaxxerError):
    """Raised when content kind cannot be determined or extracted."""


class FetchError(PodmaxxerError):
    """Raised when acquiring content (file read or URL download) fails."""


class TranscriptionError(PodmaxxerError):
    """Raised when transcription fails."""


class SummarizationError(PodmaxxerError):
    """Raised when calling the summarization backend fails."""
```

- [ ] **Step 2: Verify it imports cleanly**

```bash
uv run python -c "from podmaxxer.errors import PodmaxxerError, UnsupportedContentError, FetchError, TranscriptionError, SummarizationError; print('ok')"
```
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add src/podmaxxer/errors.py
git commit -m "feat: add Podmaxxer error hierarchy"
```

---

### Task 3: Content model and kind detection

**Files:**
- Create: `src/podmaxxer/content.py`
- Test: `tests/test_content.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_content.py
import pytest

from podmaxxer.content import (
    ContentKind,
    detect_kind_from_content_type,
    detect_kind_from_suffix,
    hash_bytes,
    hash_text,
)
from podmaxxer.errors import UnsupportedContentError


def test_detect_kind_from_suffix_audio_video():
    assert detect_kind_from_suffix(".mp3") == ContentKind.AUDIO_VIDEO
    assert detect_kind_from_suffix(".MP4") == ContentKind.AUDIO_VIDEO


def test_detect_kind_from_suffix_text():
    assert detect_kind_from_suffix(".txt") == ContentKind.TEXT
    assert detect_kind_from_suffix(".html") == ContentKind.TEXT


def test_detect_kind_from_suffix_unknown_raises():
    with pytest.raises(UnsupportedContentError):
        detect_kind_from_suffix(".exe")


def test_detect_kind_from_content_type_audio_video():
    assert detect_kind_from_content_type("audio/mpeg") == ContentKind.AUDIO_VIDEO
    assert detect_kind_from_content_type("video/mp4; charset=binary") == ContentKind.AUDIO_VIDEO


def test_detect_kind_from_content_type_text():
    assert detect_kind_from_content_type("text/html; charset=utf-8") == ContentKind.TEXT
    assert detect_kind_from_content_type("text/plain") == ContentKind.TEXT


def test_detect_kind_from_content_type_unknown_raises():
    with pytest.raises(UnsupportedContentError):
        detect_kind_from_content_type("application/json")


def test_hash_bytes_is_deterministic():
    assert hash_bytes(b"hello") == hash_bytes(b"hello")
    assert hash_bytes(b"hello") != hash_bytes(b"world")


def test_hash_text_matches_hash_bytes_utf8():
    assert hash_text("hello") == hash_bytes("hello".encode("utf-8"))
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_content.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.content'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/content.py
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
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
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
    if normalized.startswith("audio/") or normalized.startswith("video/"):
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
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/test_content.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/content.py tests/test_content.py
git commit -m "feat: add Content model and content-kind detection"
```

---

### Task 4: State database schema and connection

**Files:**
- Create: `src/podmaxxer/state/db.py`
- Test: `tests/state/test_db.py`
- Test config: `tests/state/__init__.py` (empty, marks package)

- [ ] **Step 1: Write the failing test**

```python
# tests/state/__init__.py
```

```python
# tests/state/test_db.py
from podmaxxer.state.db import connect


def test_connect_creates_expected_tables():
    conn = connect(":memory:")
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"items", "transcripts", "summaries"} <= tables
    conn.close()


def test_connect_creates_parent_dir(tmp_path):
    db_path = tmp_path / "nested" / "state.db"
    conn = connect(db_path)
    assert db_path.parent.is_dir()
    conn.close()
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/state/test_db.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.state.db'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/state/db.py
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    content_hash TEXT PRIMARY KEY,
    source_kind TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transcripts (
    content_hash TEXT PRIMARY KEY REFERENCES items(content_hash),
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS summaries (
    content_hash TEXT NOT NULL REFERENCES items(content_hash),
    template_hash TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (content_hash, template_hash)
);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/state/test_db.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/state/db.py tests/state/__init__.py tests/state/test_db.py
git commit -m "feat: add SQLite schema and connection helper"
```

---

### Task 5: State repository (idempotency reads/writes)

**Files:**
- Create: `src/podmaxxer/state/repository.py`
- Test: `tests/state/test_repository.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/state/test_repository.py
from podmaxxer.state import repository
from podmaxxer.state.db import connect


def _conn():
    return connect(":memory:")


def test_upsert_item_is_idempotent():
    conn = _conn()
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    rows = conn.execute("SELECT content_hash FROM items").fetchall()
    assert len(rows) == 1


def test_transcript_round_trip():
    conn = _conn()
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    assert repository.get_transcript(conn, "hash1") is None
    repository.save_transcript(conn, "hash1", "hello world", "existing")
    assert repository.get_transcript(conn, "hash1") == "hello world"


def test_summary_round_trip_keyed_by_template():
    conn = _conn()
    repository.upsert_item(conn, "hash1", "text", "file.txt")
    assert repository.get_summary(conn, "hash1", "tmpl-a") is None
    repository.save_summary(conn, "hash1", "tmpl-a", "summary A")
    repository.save_summary(conn, "hash1", "tmpl-b", "summary B")
    assert repository.get_summary(conn, "hash1", "tmpl-a") == "summary A"
    assert repository.get_summary(conn, "hash1", "tmpl-b") == "summary B"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/state/test_repository.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.state.repository'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/state/repository.py
from __future__ import annotations

import sqlite3


def upsert_item(
    conn: sqlite3.Connection, content_hash: str, source_kind: str, source_uri: str
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO items (content_hash, source_kind, source_uri) VALUES (?, ?, ?)",
        (content_hash, source_kind, source_uri),
    )
    conn.commit()


def get_transcript(conn: sqlite3.Connection, content_hash: str) -> str | None:
    row = conn.execute(
        "SELECT text FROM transcripts WHERE content_hash = ?", (content_hash,)
    ).fetchone()
    return row[0] if row else None


def save_transcript(conn: sqlite3.Connection, content_hash: str, text: str, source: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO transcripts (content_hash, text, source) VALUES (?, ?, ?)",
        (content_hash, text, source),
    )
    conn.commit()


def get_summary(conn: sqlite3.Connection, content_hash: str, template_hash: str) -> str | None:
    row = conn.execute(
        "SELECT summary_text FROM summaries WHERE content_hash = ? AND template_hash = ?",
        (content_hash, template_hash),
    ).fetchone()
    return row[0] if row else None


def save_summary(
    conn: sqlite3.Connection, content_hash: str, template_hash: str, summary_text: str
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO summaries (content_hash, template_hash, summary_text) VALUES (?, ?, ?)",
        (content_hash, template_hash, summary_text),
    )
    conn.commit()
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/state/test_repository.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/state/repository.py tests/state/test_repository.py
git commit -m "feat: add state repository for idempotent stage tracking"
```

---

### Task 6: Local file source

**Files:**
- Create: `src/podmaxxer/sources/base.py`
- Create: `src/podmaxxer/sources/local_file.py`
- Test: `tests/sources/__init__.py` (empty)
- Test: `tests/sources/test_local_file.py`

- [ ] **Step 1: Write `base.py` (no test needed — a `Protocol` has no behavior)**

```python
# src/podmaxxer/sources/base.py
from __future__ import annotations

from typing import Protocol

from podmaxxer.content import Content


class Source(Protocol):
    def fetch(self) -> Content: ...
```

- [ ] **Step 2: Write the failing tests for `LocalFileSource`**

```python
# tests/sources/__init__.py
```

```python
# tests/sources/test_local_file.py
import pytest

from podmaxxer.content import ContentKind
from podmaxxer.errors import UnsupportedContentError
from podmaxxer.sources.local_file import LocalFileSource


def test_fetch_text_file(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello world", encoding="utf-8")

    content = LocalFileSource(path=path).fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "hello world"
    assert content.source_uri == str(path)
    assert content.content_hash


def test_fetch_html_file_extracts_article_text(tmp_path, monkeypatch):
    path = tmp_path / "article.html"
    path.write_text("<html><body><p>Real article text.</p></body></html>", encoding="utf-8")

    import podmaxxer.sources.local_file as local_file_module

    monkeypatch.setattr(local_file_module.trafilatura, "extract", lambda raw: "Real article text.")

    content = LocalFileSource(path=path).fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "Real article text."


def test_fetch_html_file_raises_if_extraction_fails(tmp_path, monkeypatch):
    path = tmp_path / "article.html"
    path.write_text("<html></html>", encoding="utf-8")

    import podmaxxer.sources.local_file as local_file_module

    monkeypatch.setattr(local_file_module.trafilatura, "extract", lambda raw: None)

    with pytest.raises(UnsupportedContentError):
        LocalFileSource(path=path).fetch()


def test_fetch_audio_file(tmp_path):
    path = tmp_path / "episode.mp3"
    path.write_bytes(b"fake-audio-bytes")

    content = LocalFileSource(path=path).fetch()

    assert content.kind == ContentKind.AUDIO_VIDEO
    assert content.path == path
    assert content.text is None
    assert content.content_hash
```

- [ ] **Step 3: Run to verify failure**

```bash
uv run pytest tests/sources/test_local_file.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.sources.local_file'`.

- [ ] **Step 4: Implement**

```python
# src/podmaxxer/sources/local_file.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import trafilatura

from podmaxxer.content import Content, ContentKind, detect_kind_from_suffix, hash_bytes, hash_text
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
```

- [ ] **Step 5: Run to verify pass**

```bash
uv run pytest tests/sources/test_local_file.py -v
```
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add src/podmaxxer/sources/base.py src/podmaxxer/sources/local_file.py tests/sources/__init__.py tests/sources/test_local_file.py
git commit -m "feat: add Source protocol and LocalFileSource"
```

---

### Task 7: Remote URL source

**Files:**
- Create: `src/podmaxxer/sources/remote_url.py`
- Test: `tests/sources/test_remote_url.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/sources/test_remote_url.py
import responses

from podmaxxer.content import ContentKind
from podmaxxer.sources.remote_url import UrlSource


@responses.activate
def test_fetch_text_plain():
    responses.add(
        responses.GET,
        "https://example.com/notes.txt",
        body="hello from the web",
        status=200,
        content_type="text/plain",
    )

    content = UrlSource(url="https://example.com/notes.txt").fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "hello from the web"
    assert content.source_uri == "https://example.com/notes.txt"


@responses.activate
def test_fetch_html_extracts_article_text(monkeypatch):
    responses.add(
        responses.GET,
        "https://example.com/article",
        body="<html><body><p>Real article text.</p></body></html>",
        status=200,
        content_type="text/html; charset=utf-8",
    )

    import podmaxxer.sources.remote_url as remote_url_module

    monkeypatch.setattr(remote_url_module.trafilatura, "extract", lambda raw: "Real article text.")

    content = UrlSource(url="https://example.com/article").fetch()

    assert content.kind == ContentKind.TEXT
    assert content.text == "Real article text."


@responses.activate
def test_fetch_audio_saves_to_temp_file():
    responses.add(
        responses.GET,
        "https://example.com/episode.mp3",
        body=b"fake-audio-bytes",
        status=200,
        content_type="audio/mpeg",
    )

    content = UrlSource(url="https://example.com/episode.mp3").fetch()

    assert content.kind == ContentKind.AUDIO_VIDEO
    assert content.path is not None
    assert content.path.read_bytes() == b"fake-audio-bytes"


@responses.activate
def test_fetch_raises_on_http_error():
    from podmaxxer.errors import FetchError

    responses.add(responses.GET, "https://example.com/missing.mp3", status=404)

    try:
        UrlSource(url="https://example.com/missing.mp3").fetch()
        assert False, "expected FetchError"
    except FetchError:
        pass
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/sources/test_remote_url.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.sources.remote_url'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/sources/remote_url.py
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import requests
import trafilatura

from podmaxxer.content import (
    Content,
    ContentKind,
    detect_kind_from_content_type,
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
        kind = detect_kind_from_content_type(content_type)

        if kind is ContentKind.AUDIO_VIDEO:
            return self._audio_video_content(response.content)
        return self._text_content(response.text, content_type)

    def _audio_video_content(self, data: bytes) -> Content:
        suffix = Path(self.url).suffix or ".media"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()
        return Content(
            kind=ContentKind.AUDIO_VIDEO,
            source_uri=self.url,
            content_hash=hash_bytes(data),
            path=Path(tmp.name),
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
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/sources/test_remote_url.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/sources/remote_url.py tests/sources/test_remote_url.py
git commit -m "feat: add UrlSource for direct-URL input"
```

---

### Task 8: Sidecar transcript lookup

**Files:**
- Create: `src/podmaxxer/transcription/existing.py`
- Test: `tests/transcription/__init__.py` (empty)
- Test: `tests/transcription/test_existing.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/transcription/__init__.py
```

```python
# tests/transcription/test_existing.py
from podmaxxer.transcription.existing import find_sidecar_transcript


def test_returns_none_when_no_sidecar(tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    assert find_sidecar_transcript(media) is None


def test_finds_txt_sidecar(tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    (tmp_path / "episode.txt").write_text("  hello transcript  ", encoding="utf-8")
    assert find_sidecar_transcript(media) == "hello transcript"


def test_finds_and_cleans_vtt_sidecar(tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    (tmp_path / "episode.vtt").write_text(
        "WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\nHello there.\n\n"
        "2\n00:00:02.000 --> 00:00:04.000\nWelcome back.\n",
        encoding="utf-8",
    )
    assert find_sidecar_transcript(media) == "Hello there. Welcome back."
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/transcription/test_existing.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.transcription.existing'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/transcription/existing.py
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
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/transcription/test_existing.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/transcription/existing.py tests/transcription/__init__.py tests/transcription/test_existing.py
git commit -m "feat: add sidecar transcript/caption lookup"
```

---

### Task 9: Whisper backend wrapper

**Files:**
- Create: `src/podmaxxer/transcription/whisper_backend.py`
- Test: `tests/transcription/test_whisper_backend.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/transcription/test_whisper_backend.py
from dataclasses import dataclass
from pathlib import Path

import podmaxxer.transcription.whisper_backend as whisper_backend


@dataclass
class FakeSegment:
    text: str


class FakeModel:
    def __init__(self, segments):
        self._segments = segments

    def transcribe(self, path):
        return self._segments, None


def test_transcribe_joins_segment_text(monkeypatch, tmp_path):
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"fake-audio")

    fake_model = FakeModel([FakeSegment(" Hello "), FakeSegment("world. ")])
    monkeypatch.setattr(whisper_backend, "_get_model", lambda model_size: fake_model)

    result = whisper_backend.transcribe(audio, model_size="base")

    assert result == "Hello world."


def test_get_model_is_cached(monkeypatch):
    calls = []

    class DummyWhisperModel:
        def __init__(self, model_size, device, compute_type):
            calls.append(model_size)

    monkeypatch.setattr(whisper_backend, "WhisperModel", DummyWhisperModel)
    whisper_backend._MODEL_CACHE.clear()

    whisper_backend._get_model("base")
    whisper_backend._get_model("base")

    assert calls == ["base"]
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/transcription/test_whisper_backend.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.transcription.whisper_backend'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/transcription/whisper_backend.py
from __future__ import annotations

from pathlib import Path

from faster_whisper import WhisperModel

_MODEL_CACHE: dict[str, WhisperModel] = {}


def _get_model(model_size: str) -> WhisperModel:
    if model_size not in _MODEL_CACHE:
        _MODEL_CACHE[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _MODEL_CACHE[model_size]


def transcribe(path: Path, model_size: str = "base") -> str:
    model = _get_model(model_size)
    segments, _info = model.transcribe(str(path))
    return " ".join(segment.text.strip() for segment in segments)
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/transcription/test_whisper_backend.py -v
```
Expected: 2 passed. (No real model is downloaded — both tests monkeypatch the model.)

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/transcription/whisper_backend.py tests/transcription/test_whisper_backend.py
git commit -m "feat: add faster-whisper transcription backend"
```

---

### Task 10: Transcript orchestration

**Files:**
- Create: `src/podmaxxer/transcription/base.py`
- Test: `tests/transcription/test_base.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/transcription/test_base.py
from pathlib import Path

from podmaxxer.content import Content, ContentKind
from podmaxxer.transcription import base as transcription_base


def test_text_content_returns_its_own_text():
    content = Content(kind=ContentKind.TEXT, source_uri="x", content_hash="h", text="already text")
    text, source = transcription_base.get_transcript(content)
    assert text == "already text"
    assert source == "existing"


def test_audio_content_uses_sidecar_when_present(monkeypatch, tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    content = Content(kind=ContentKind.AUDIO_VIDEO, source_uri="x", content_hash="h", path=media)

    monkeypatch.setattr(transcription_base, "find_sidecar_transcript", lambda path: "sidecar text")
    monkeypatch.setattr(
        transcription_base,
        "whisper_transcribe",
        lambda path: (_ for _ in ()).throw(AssertionError("should not be called")),
    )

    text, source = transcription_base.get_transcript(content)
    assert text == "sidecar text"
    assert source == "existing"


def test_audio_content_falls_back_to_whisper(monkeypatch, tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    content = Content(kind=ContentKind.AUDIO_VIDEO, source_uri="x", content_hash="h", path=media)

    monkeypatch.setattr(transcription_base, "find_sidecar_transcript", lambda path: None)
    monkeypatch.setattr(transcription_base, "whisper_transcribe", lambda path: "whispered text")

    text, source = transcription_base.get_transcript(content)
    assert text == "whispered text"
    assert source == "whisper"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/transcription/test_base.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.transcription.base'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/transcription/base.py
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
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/transcription/test_base.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/transcription/base.py tests/transcription/test_base.py
git commit -m "feat: orchestrate transcript-or-transcribe stage"
```

---

### Task 11: Template loader and default template

**Files:**
- Create: `src/podmaxxer/templates/default.txt`
- Create: `src/podmaxxer/summarize/templates.py`
- Test: `tests/summarize/__init__.py` (empty)
- Test: `tests/summarize/test_templates.py`

- [ ] **Step 1: Write the default template**

```
# src/podmaxxer/templates/default.txt
You are summarizing a transcript for someone who wants the key points quickly.

Write a concise summary that includes:
- The main topic(s) discussed
- Key takeaways or arguments
- Any notable facts, figures, or recommendations mentioned

Keep the summary under 300 words. Use plain prose or short bullet points, whichever fits the
content better.
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/summarize/__init__.py
```

```python
# tests/summarize/test_templates.py
from podmaxxer.content import hash_text
from podmaxxer.summarize.templates import load_template


def test_load_default_template_when_no_path_given():
    text, template_hash = load_template(None)
    assert "summarizing a transcript" in text
    assert template_hash == hash_text(text)


def test_load_custom_template_from_path(tmp_path):
    custom = tmp_path / "custom.txt"
    custom.write_text("Focus only on action items.", encoding="utf-8")

    text, template_hash = load_template(custom)

    assert text == "Focus only on action items."
    assert template_hash == hash_text(text)


def test_different_templates_hash_differently(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("Template A", encoding="utf-8")
    b.write_text("Template B", encoding="utf-8")

    _, hash_a = load_template(a)
    _, hash_b = load_template(b)

    assert hash_a != hash_b
```

- [ ] **Step 3: Run to verify failure**

```bash
uv run pytest tests/summarize/test_templates.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.summarize.templates'`.

- [ ] **Step 4: Implement**

```python
# src/podmaxxer/summarize/templates.py
from __future__ import annotations

from pathlib import Path

from podmaxxer.content import hash_text

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # src/podmaxxer/
DEFAULT_TEMPLATE_PATH = _PACKAGE_ROOT / "templates" / "default.txt"


def load_template(path: Path | None) -> tuple[str, str]:
    template_path = Path(path) if path is not None else DEFAULT_TEMPLATE_PATH
    text = template_path.read_text(encoding="utf-8")
    return text, hash_text(text)
```

- [ ] **Step 5: Run to verify pass**

```bash
uv run pytest tests/summarize/test_templates.py -v
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add src/podmaxxer/templates/default.txt src/podmaxxer/summarize/templates.py tests/summarize/__init__.py tests/summarize/test_templates.py
git commit -m "feat: add plain-text template loading with default template"
```

> **Note for a later task:** `DEFAULT_TEMPLATE_PATH` is resolved relative to `__file__`, which works for `uv run` from source. If the package is later built as a wheel and `templates/default.txt` isn't bundled, this will break — file a follow-up if/when packaging for distribution becomes a real need.

---

### Task 12: OpenAI client

**Files:**
- Create: `src/podmaxxer/summarize/openai_client.py`
- Test: `tests/summarize/test_openai_client.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/summarize/test_openai_client.py
import pytest
import responses

from podmaxxer.errors import SummarizationError
from podmaxxer.summarize.openai_client import OPENAI_CHAT_COMPLETIONS_URL, call_openai


@responses.activate
def test_call_openai_returns_message_content():
    responses.add(
        responses.POST,
        OPENAI_CHAT_COMPLETIONS_URL,
        json={"choices": [{"message": {"content": "  the summary  "}}]},
        status=200,
    )

    result = call_openai("summarize this", api_key="sk-test")

    assert result == "the summary"
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer sk-test"


@responses.activate
def test_call_openai_raises_on_non_200():
    responses.add(responses.POST, OPENAI_CHAT_COMPLETIONS_URL, body="server error", status=500)

    with pytest.raises(SummarizationError):
        call_openai("summarize this", api_key="sk-test")


@responses.activate
def test_call_openai_raises_on_unexpected_shape():
    responses.add(
        responses.POST, OPENAI_CHAT_COMPLETIONS_URL, json={"unexpected": "shape"}, status=200
    )

    with pytest.raises(SummarizationError):
        call_openai("summarize this", api_key="sk-test")
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/summarize/test_openai_client.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.summarize.openai_client'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/summarize/openai_client.py
from __future__ import annotations

import requests

from podmaxxer.errors import SummarizationError

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


def call_openai(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    session: requests.Session | None = None,
) -> str:
    http = session or requests
    try:
        response = http.post(
            OPENAI_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=60,
        )
    except requests.RequestException as exc:
        raise SummarizationError(f"OpenAI request failed: {exc}") from exc

    if response.status_code != 200:
        raise SummarizationError(f"OpenAI API error {response.status_code}: {response.text}")

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise SummarizationError(f"Unexpected OpenAI response shape: {data}") from exc
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/summarize/test_openai_client.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/summarize/openai_client.py tests/summarize/test_openai_client.py
git commit -m "feat: call OpenAI chat completions via requests"
```

---

### Task 13: Summarizer

**Files:**
- Create: `src/podmaxxer/summarize/summarizer.py`
- Test: `tests/summarize/test_summarizer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/summarize/test_summarizer.py
from podmaxxer.summarize import summarizer


def test_build_prompt_includes_template_and_transcript():
    prompt = summarizer.build_prompt("Focus on action items.", "We discussed the roadmap.")
    assert "Focus on action items." in prompt
    assert "We discussed the roadmap." in prompt


def test_summarize_calls_openai_with_built_prompt(monkeypatch):
    captured = {}

    def fake_call_openai(prompt, api_key):
        captured["prompt"] = prompt
        captured["api_key"] = api_key
        return "final summary"

    monkeypatch.setattr(summarizer, "call_openai", fake_call_openai)

    result = summarizer.summarize("template text", "transcript text", api_key="sk-test")

    assert result == "final summary"
    assert "template text" in captured["prompt"]
    assert "transcript text" in captured["prompt"]
    assert captured["api_key"] == "sk-test"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/summarize/test_summarizer.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.summarize.summarizer'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/summarize/summarizer.py
from __future__ import annotations

from podmaxxer.summarize.openai_client import call_openai


def build_prompt(template: str, transcript: str) -> str:
    return f"{template.strip()}\n\n---\n\nTranscript:\n{transcript.strip()}"


def summarize(template: str, transcript: str, api_key: str) -> str:
    prompt = build_prompt(template, transcript)
    return call_openai(prompt, api_key)
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/summarize/test_summarizer.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/summarize/summarizer.py tests/summarize/test_summarizer.py
git commit -m "feat: combine template and transcript into a summarization call"
```

---

### Task 14: State DB path configuration

**Files:**
- Create: `src/podmaxxer/config.py`
- Create: `docs/decisions/0007-platformdirs-for-state-path.md`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
from pathlib import Path

from podmaxxer.config import get_state_db_path


def test_uses_env_override(monkeypatch):
    monkeypatch.setenv("PODMAXXER_STATE_DB", "/tmp/custom/state.db")
    assert get_state_db_path() == Path("/tmp/custom/state.db")


def test_falls_back_to_platformdirs_default(monkeypatch):
    monkeypatch.delenv("PODMAXXER_STATE_DB", raising=False)
    path = get_state_db_path()
    assert path.name == "state.db"
    assert "podmaxxer" in str(path).lower()
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.config'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/config.py
from __future__ import annotations

import os
from pathlib import Path

import platformdirs


def get_state_db_path() -> Path:
    override = os.environ.get("PODMAXXER_STATE_DB")
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir("podmaxxer")) / "state.db"
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/test_config.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Write the ADR for this decision**

```markdown
# 0007. Use platformdirs for the default state DB location

Date: 2026-07-24
Status: Accepted

## Context

CLAUDE.md requires the SQLite state file location to be configurable (flag/env var) with a
sensible default under a user config/cache directory, rather than hardcoding a path or assuming
the CWD is writable. Computing that default correctly is OS-specific (XDG on Linux, `~/Library` on
macOS, `%LOCALAPPDATA%` on Windows).

## Decision

Use the `platformdirs` library (`platformdirs.user_data_dir("podmaxxer")`) for the default state
DB directory, overridable via the `PODMAXXER_STATE_DB` environment variable.

## Consequences

- Correct default state directory per OS without hand-rolled path logic.
- `platformdirs` is the actively maintained successor to the older `appdirs` package.
- A CLI flag for overriding the path (in addition to the env var) is deferred — the env var covers
  the MVP need; add a `--state-db` flag later if it proves necessary.
```

- [ ] **Step 6: Commit**

```bash
git add src/podmaxxer/config.py tests/test_config.py docs/decisions/0007-platformdirs-for-state-path.md
git commit -m "feat: configurable state DB path via platformdirs and env override"
```

---

### Task 15: Pipeline orchestrator

**Files:**
- Create: `src/podmaxxer/pipeline.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pipeline.py
from podmaxxer.content import Content, ContentKind
from podmaxxer.state.db import connect
from podmaxxer import pipeline


class FakeSource:
    def __init__(self, content):
        self._content = content

    def fetch(self):
        return self._content


def test_process_runs_all_stages_and_persists_state(monkeypatch, tmp_path):
    conn = connect(":memory:")
    content = Content(
        kind=ContentKind.TEXT, source_uri="x", content_hash="h1", text="raw transcript"
    )
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    monkeypatch.setattr(
        pipeline, "summarize", lambda template, transcript, api_key: f"SUMMARY({transcript})"
    )

    result = pipeline.process(
        FakeSource(content), conn, api_key="sk-test", template_path=template_path
    )

    assert result == "SUMMARY(raw transcript)"
    assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM summaries").fetchone()[0] == 1


def test_process_skips_summarize_call_when_already_cached(monkeypatch, tmp_path):
    conn = connect(":memory:")
    content = Content(
        kind=ContentKind.TEXT, source_uri="x", content_hash="h1", text="raw transcript"
    )
    template_path = tmp_path / "tmpl.txt"
    template_path.write_text("Focus on X.", encoding="utf-8")

    calls = []
    monkeypatch.setattr(
        pipeline, "summarize", lambda template, transcript, api_key: calls.append(1) or "SUMMARY"
    )

    pipeline.process(FakeSource(content), conn, api_key="sk-test", template_path=template_path)
    pipeline.process(FakeSource(content), conn, api_key="sk-test", template_path=template_path)

    assert len(calls) == 1
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_pipeline.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.pipeline'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/pipeline.py
from __future__ import annotations

import sqlite3
from pathlib import Path

from podmaxxer.sources.base import Source
from podmaxxer.state import repository
from podmaxxer.summarize.summarizer import summarize
from podmaxxer.summarize.templates import load_template
from podmaxxer.transcription.base import get_transcript


def process(
    source: Source,
    conn: sqlite3.Connection,
    api_key: str,
    template_path: Path | None = None,
) -> str:
    content = source.fetch()
    repository.upsert_item(conn, content.content_hash, content.kind.value, content.source_uri)

    transcript = repository.get_transcript(conn, content.content_hash)
    if transcript is None:
        transcript, transcript_source = get_transcript(content)
        repository.save_transcript(conn, content.content_hash, transcript, transcript_source)

    template_text, template_hash = load_template(template_path)

    summary = repository.get_summary(conn, content.content_hash, template_hash)
    if summary is None:
        summary = summarize(template_text, transcript, api_key)
        repository.save_summary(conn, content.content_hash, template_hash, summary)

    return summary
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/test_pipeline.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/podmaxxer/pipeline.py tests/test_pipeline.py
git commit -m "feat: wire pipeline orchestrator with per-stage idempotency"
```

---

### Task 16: CLI

**Files:**
- Create: `src/podmaxxer/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli.py
from click.testing import CliRunner

from podmaxxer import cli as cli_module
from podmaxxer.errors import PodmaxxerError


def test_file_command_prints_summary(monkeypatch, tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(cli_module, "connect", lambda db_path: "fake-conn")
    monkeypatch.setattr(
        cli_module, "process", lambda source, conn, api_key, template_path=None: "the summary"
    )

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["file", str(path)])

    assert result.exit_code == 0
    assert "the summary" in result.output


def test_missing_api_key_exits_nonzero(monkeypatch, tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["file", str(path)])

    assert result.exit_code != 0
    assert "OPENAI_API_KEY" in result.output


def test_pipeline_error_reported_on_stderr_with_nonzero_exit(monkeypatch, tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(cli_module, "connect", lambda db_path: "fake-conn")

    def raise_error(source, conn, api_key, template_path=None):
        raise PodmaxxerError("boom")

    monkeypatch.setattr(cli_module, "process", raise_error)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["file", str(path)])

    assert result.exit_code != 0
    assert "boom" in result.output


def test_url_command_invokes_pipeline(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(cli_module, "connect", lambda db_path: "fake-conn")
    monkeypatch.setattr(
        cli_module, "process", lambda source, conn, api_key, template_path=None: "url summary"
    )

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["url", "https://example.com/a.mp3"])

    assert result.exit_code == 0
    assert "url summary" in result.output
```

Note: these tests monkeypatch `cli_module.connect` to avoid touching the real filesystem-backed
state DB, and `cli_module.process` to isolate CLI wiring from pipeline logic (already covered by
Task 15's tests).

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_cli.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'podmaxxer.cli'`.

- [ ] **Step 3: Implement**

```python
# src/podmaxxer/cli.py
from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from podmaxxer.config import get_state_db_path
from podmaxxer.errors import PodmaxxerError
from podmaxxer.pipeline import process
from podmaxxer.sources.local_file import LocalFileSource
from podmaxxer.sources.remote_url import UrlSource
from podmaxxer.state.db import connect


@click.group()
def cli() -> None:
    """Podmaxxer: download and summarize podcasts, articles, and videos."""


@cli.command("file")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--template", type=click.Path(exists=True, path_type=Path), default=None)
def file_command(path: Path, template: Path | None) -> None:
    _run(LocalFileSource(path=path), template)


@cli.command("url")
@click.argument("url")
@click.option("--template", type=click.Path(exists=True, path_type=Path), default=None)
def url_command(url: str, template: Path | None) -> None:
    _run(UrlSource(url=url), template)


def _run(source, template: Path | None) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        click.echo("Error: OPENAI_API_KEY environment variable is not set.", err=True)
        sys.exit(1)

    conn = connect(get_state_db_path())
    try:
        summary = process(source, conn, api_key, template_path=template)
    except PodmaxxerError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    finally:
        if hasattr(conn, "close"):
            conn.close()

    click.echo(summary)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/test_cli.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Verify the installed entry point works end-to-end (manual smoke test)**

```bash
echo "The quick brown fox jumps over the lazy dog many times." > /tmp/note.txt
OPENAI_API_KEY=sk-fake uv run podmaxxer file /tmp/note.txt
```
Expected: either a real (if `sk-fake` were valid) or a clear `Error: OpenAI API error 401: ...`
printed to stderr with a non-zero exit — confirming the CLI wiring reaches the real OpenAI client
when not monkeypatched. Re-run the same command a second time to confirm `pytest`-covered
idempotency also holds in practice (fetch/transcript stage will be skipped on the second run,
observable by adding a temporary `print` or by inspecting the state DB with
`sqlite3 "$(uv run python -c 'from podmaxxer.config import get_state_db_path; print(get_state_db_path())')" '.tables'`).

- [ ] **Step 6: Commit**

```bash
git add src/podmaxxer/cli.py tests/test_cli.py
git commit -m "feat: add Click CLI with file and url subcommands"
```

---

### Task 17: README

**Files:**
- Create/overwrite: `README.md`

- [ ] **Step 1: Write the README**

```markdown
# Podmaxxer

A stateful CLI that downloads podcasts, articles, or videos and produces a summary of them.

## Install

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

Summarize a local audio/video file or text article:

```bash
OPENAI_API_KEY=sk-... uv run podmaxxer file path/to/episode.mp3
OPENAI_API_KEY=sk-... uv run podmaxxer file path/to/article.html
```

Summarize a direct URL (audio/video file or article page):

```bash
OPENAI_API_KEY=sk-... uv run podmaxxer url https://example.com/episode.mp3
```

Use a custom summarization template instead of the bundled default:

```bash
uv run podmaxxer file path/to/episode.mp3 --template my-template.txt
```

A template is a plain text file containing prompt instructions describing what the summary
should focus on.

## Configuration

| Variable              | Purpose                                              | Default                          |
|------------------------|-------------------------------------------------------|-----------------------------------|
| `OPENAI_API_KEY`       | Required. API key used to call OpenAI for summarization. | none (errors if unset)        |
| `PODMAXXER_STATE_DB`   | Path to the SQLite state database.                    | OS-appropriate user data dir (via `platformdirs`) |

## Statefulness

Podmaxxer records progress per pipeline stage (fetch, transcript, summarize) in SQLite, keyed by
a content hash. Re-running the same input skips any stage already completed.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

See `docs/superpowers/specs/` for design specs and `docs/decisions/` for architecture decision
records (ADRs) explaining the "why" behind notable choices.

## Current scope (MVP)

Supports local file and direct-URL input for audio/video and text-article content. RSS feed input
and YouTube-specific handling are planned but not yet implemented — see the MVP design spec for
details.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage, configuration, and dev instructions"
```

---

### Task 18: Update CLAUDE.md with real commands and architecture

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Replace the "Project status" section**

Change the opening section from describing a greenfield/no-code repo to reflecting the real,
implemented MVP:

```markdown
## Project status

MVP implemented: a Click CLI supporting local-file and direct-URL input for audio/video and text
content, transcript-or-Whisper transcription, template-based summarization via OpenAI, and
SQLite-backed resumability. RSS feed and YouTube input are not yet implemented.

### Commands

```bash
uv sync                 # install/sync dependencies
uv run pytest            # run the test suite
uv run pytest -m "not slow"   # skip the real-Whisper integration test
uv run ruff check .      # lint
uv run podmaxxer file <path> [--template <path>]
uv run podmaxxer url <url> [--template <path>]
```

### Architecture

See `docs/superpowers/specs/2026-07-24-podmaxxer-mvp-design.md` for the full design and
`docs/decisions/` for ADRs. In brief: input kinds implement a `Source.fetch() -> Content`
protocol (`src/podmaxxer/sources/`); content flows through transcription
(`src/podmaxxer/transcription/`) and summarization (`src/podmaxxer/summarize/`) stages;
`src/podmaxxer/state/repository.py` is the sole place idempotency is tracked, keyed by a SHA-256
content hash; `src/podmaxxer/pipeline.py` orchestrates stage order; `src/podmaxxer/cli.py` is the
thin Click entry point.
```

Leave the rest of `CLAUDE.md` (the "What Podmaxxer is", "Statefulness", "Python tooling: uv", and
"Python CLI best practices" sections) as-is — they describe the product vision and conventions,
which still hold.

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md project status with MVP commands and architecture"
```

---

### Task 19: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

```bash
uv run pytest -v
```
Expected: all tests pass (no `@pytest.mark.slow` tests were added in this plan, since the whisper
backend is fully covered by monkeypatched unit tests — no real-model integration test is required
for the MVP to be considered done).

- [ ] **Step 2: Run lint**

```bash
uv run ruff check .
```
Expected: no errors. Fix any that appear (import order, unused imports, etc.) and re-run.

- [ ] **Step 3: Confirm git state is clean**

```bash
git status --short
```
Expected: empty (everything from this plan committed task-by-task already).

- [ ] **Step 4: Final commit if lint fixes were needed**

```bash
git add -A
git commit -m "chore: fix lint issues found in final verification pass"
```
(Skip this step if Step 3 showed a clean tree.)
