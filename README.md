# Podmaxxer

A stateful CLI that downloads podcasts, articles, or videos and produces a summary of them.

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14 (uv will fetch it).

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

| Variable                    | Purpose                                                        | Default                                   |
|-----------------------------|----------------------------------------------------------------|-------------------------------------------|
| `OPENAI_API_KEY`            | API key for the summarization endpoint. Not needed for local endpoints. | none (required for api.openai.com) |
| `PODMAXXER_MODEL`           | Chat model used for summaries.                                 | `gpt-6-luna` (cheapest current OpenAI model) |
| `PODMAXXER_OPENAI_BASE_URL` | Any OpenAI-compatible endpoint, e.g. Ollama `http://localhost:11434/v1`. | `https://api.openai.com/v1`   |
| `PODMAXXER_WHISPER_MODEL`   | faster-whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`). | `small`                       |
| `PODMAXXER_STATE_DB`        | Path to the SQLite state database.                             | OS user data dir (via `platformdirs`)     |

### Running fully local (no per-use cost)

Transcription always runs locally via faster-whisper. To summarize locally too, point at an
OpenAI-compatible local server:

```bash
PODMAXXER_OPENAI_BASE_URL=http://localhost:11434/v1 PODMAXXER_MODEL=llama3.2 \
  uv run podmaxxer file episode.mp3
```

## Statefulness

Podmaxxer records progress per pipeline stage (fetch, transcript, summarize) in SQLite, keyed by
a content hash. Re-running the same input skips any stage already completed.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run basedpyright
```

See `docs/superpowers/specs/` for design specs and `docs/decisions/` for architecture decision
records (ADRs) explaining the "why" behind notable choices.

## Current scope (MVP)

Supports local file and direct-URL input for audio/video and text-article content. RSS feed input
and YouTube-specific handling are planned but not yet implemented — see the MVP design spec for
details.

See `docs/review-2026-10.md` for known limitations and the roadmap.
