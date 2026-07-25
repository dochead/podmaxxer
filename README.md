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
