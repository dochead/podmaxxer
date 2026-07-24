# Podmaxxer MVP — Design Spec

Date: 2026-07-24
Status: Approved

## Purpose

Ship a minimal, real, end-to-end slice of Podmaxxer: take a local file or a direct URL pointing
at audio/video or a text article, produce a transcript (existing sidecar/captions, or local
Whisper transcription for audio/video), summarize it against a template, and print the summary.
State is persisted in SQLite so re-running on the same input is cheap and safe. Full product
vision (RSS feeds, YouTube, custom template discovery beyond a path) is deferred to follow-up
work — see "Out of scope" below.

## Scope (MVP)

**In scope:**
- Input kinds: local file path, direct URL (via `requests`).
- Content kinds: audio/video (transcribe) and text articles (summarize directly).
- Transcript acquisition: reuse an existing sidecar transcript/captions file if present; otherwise
  transcribe locally with `faster-whisper`.
- Article text extraction from HTML via `trafilatura`.
- Summarization: OpenAI's REST API, called directly via `requests` (no SDK), combining a
  plain-text prompt template with the transcript.
- Templates: plain text/markdown prompt files; a generic default ships with the tool, users may
  pass `--template <path>`.
- State: SQLite, keyed by content hash, tracking per-stage completion (fetch, transcript, summary)
  so re-running the same input skips completed stages.
- Output: summary printed to stdout (Unix conventions — logs/progress on stderr).
- CLI: Click, with one subcommand per input kind (`podmaxxer file <path>`, `podmaxxer url <url>`).

**Out of scope (explicitly deferred):**
- RSS feed input (with last-N/newest selection).
- YouTube-specific handling (captions API, `yt-dlp`, age-gating, etc.).
- Provider-agnostic summarization backend (only OpenAI in MVP).
- Retry/backoff policies for network or API failures.
- Structured (Jinja2/YAML) templates.
- Any queue/batch processing model.

## Architecture

Stage-per-module pipeline built around a `Source` abstraction, chosen over (a) flat per-input
scripts and (b) a job-queue-in-SQLite model — see "Design decisions" below for the full rationale.

```
src/podmaxxer/
  cli.py                    # Click group + subcommands: `file`, `url`
  sources/
    base.py                 # Source protocol: fetch() -> Content
    local_file.py            # FileSource
    remote_url.py            # UrlSource (requests-based download)
  content.py                # Content dataclass: kind (audio/video/text), path_or_text, source_uri, content_hash
  transcription/
    base.py                 # get_transcript(content) -> Transcript
    existing.py              # sidecar/caption lookup
    whisper_backend.py       # faster-whisper wrapper
  summarize/
    templates.py             # load/find template files (plain text prompt)
    openai_client.py          # thin wrapper over `requests` calls to OpenAI's REST API
    summarizer.py             # combine template + transcript -> prompt -> summary
  state/
    db.py                    # SQLite connection/schema setup
    repository.py             # idempotency checks + record-writes per stage
  pipeline.py                # orchestrator: source -> transcript -> summarize -> output, consulting state
  config.py                  # paths (state DB location), env/flags
```

Design principle: `Source` is the only extension point for input kinds — file/URL now, RSS/YouTube
later plug in here without touching anything downstream. `state/repository.py` is the single place
idempotency logic lives; every other module is stateless (input in, output out). `pipeline.py` is
the only module that knows stage *order*.

## Data flow

```
file/URL input
  -> Source.fetch() -> Content(kind, path_or_text, source_uri, content_hash)
  -> state: upsert content row keyed by content_hash (sha256 of bytes/text) if not present
  -> if kind == text: transcript = content.text (skip transcription)
  -> if kind == audio/video:
      -> check for existing sidecar transcript/captions -> use if found
      -> else Whisper-transcribe via faster-whisper -> persist transcript
  -> state: record transcript stage done for this content_hash
  -> load template (default or --template path)
  -> build prompt(template, transcript) -> call OpenAI API via requests
  -> state: record summary stage done, store summary text
  -> print summary to stdout
```

## State schema (SQLite, MVP)

```sql
items(content_hash TEXT PRIMARY KEY, source_kind TEXT, source_uri TEXT, created_at TEXT)
transcripts(content_hash TEXT PRIMARY KEY REFERENCES items, text TEXT, source TEXT /* 'existing'|'whisper' */, created_at TEXT)
summaries(content_hash TEXT, template_hash TEXT, summary_text TEXT, created_at TEXT, PRIMARY KEY (content_hash, template_hash))
```

`content_hash` is the resume key: re-running `podmaxxer file x.mp3` (or the same URL) is a no-op
past whatever stage already has a row. `template_hash` lets the same content be summarized again
under a different template without re-transcribing.

## Error handling

- Network/download failures (URL fetch, OpenAI call) raise a typed `PodmaxxerError` subclass,
  caught at the CLI layer, printed to stderr, non-zero exit. No silent retries in MVP.
- Missing/unreadable local file fails fast, before any DB interaction.
- Whisper/model load failure produces a clear stderr message; no partial transcript row is left
  behind.
- Every state write happens only after a stage genuinely succeeds — a crash mid-stage is always
  safely re-run on the next invocation.

## Testing & tooling (TDD)

- Test runner: `pytest` (`uv add --dev pytest`).
- HTTP mocking: `responses` (or `requests-mock`) stubs OpenAI calls and URL downloads — no real
  network calls in the unit test suite.
- Whisper in tests: `whisper_backend` sits behind the same `get_transcript` interface as the
  sidecar-lookup path; pipeline tests use a fake transcription backend. A single
  `@pytest.mark.slow` integration test (skipped by default) runs real `faster-whisper` against a
  tiny fixture audio file.
- DB in tests: SQLite `:memory:` per test, no shared fixtures across tests.
- Lint/format: `ruff` (`uv add --dev ruff`).
- TDD loop per stage: write a failing test against the stage's narrow interface (`Source.fetch()`,
  `get_transcript()`, `summarize()`) before implementing it.

## Design decisions

Recorded as lightweight ADRs under `docs/decisions/`, one file per notable decision, starting with:
1. Stage-pipeline + `Source` abstraction over flat scripts or a job queue.
2. `content_hash` as the resume/idempotency key.
3. `requests`-direct OpenAI calls instead of the official SDK.
4. `faster-whisper` over `openai-whisper`.
5. `trafilatura` over hand-rolled HTML extraction.
6. Plain-text prompt templates over Jinja2/structured YAML.

## Open questions / follow-ups for later work

- RSS feed support (last-N/newest selection) — natural next `Source` implementation.
- YouTube support — likely its own `Source` plus a captions-fetch strategy.
- Retry/backoff policy for transient network/API failures.
- Config file location and precedence rules once more settings exist beyond the state DB path.
