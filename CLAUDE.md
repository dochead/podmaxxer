# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## What Podmaxxer is

Podmaxxer is a text-based, stateful CLI tool that downloads podcasts, articles, or videos and
produces a summary of them.

Core flow:
1. **Input** — accepts an RSS feed (with options to process the last N episodes or only the
   newest), a local file path, or a URL (direct media file or YouTube).
2. **Acquisition** — downloads the source media/content. Prefers fetching an existing transcript
   if one is available; otherwise transcribes audio locally using Whisper.
3. **Summarization** — summarizes the transcript according to a template that defines what the
   summary should focus on (a generic default template, or a user-provided one).
4. **Output** — produces the resulting summary.

## Statefulness

Podmaxxer persists state in a SQLite database and is designed to resume interrupted work rather
than restart from scratch. Before doing any downloading or transcription work, it should check
state to avoid redundant downloads/transcriptions for content it has already processed (e.g. an
RSS feed item already fetched and transcribed on a previous run).

When implementing state-related logic, keep this idempotency goal central: any pipeline stage
(download, transcript-fetch, transcribe, summarize) should be checked against and recorded in the
database so re-running the tool on the same input is cheap and safe.

## Python tooling: uv

This project is built around [uv](https://docs.astral.sh/uv/) for packaging, dependency, and
environment management — do not use pip/venv/poetry directly.

- Use a `src/` layout package (e.g. `src/podmaxxer/`) with `pyproject.toml` at the root, created
  via `uv init --package`.
- Add runtime dependencies with `uv add <package>`; add dev-only dependencies (test/lint tooling,
  once chosen) with `uv add --dev <package>`. Don't hand-edit dependency versions in
  `pyproject.toml` — let `uv add`/`uv lock` manage `uv.lock`.
- Run the app and any scripts through `uv run ...` rather than activating a venv manually, so the
  lockfile-resolved environment is always what executes.
- Expose the CLI as an installable entry point via `[project.scripts]` in `pyproject.toml` (e.g.
  `podmaxxer = "podmaxxer.cli:main"`), so it's runnable as `uv run podmaxxer ...` in development
  and as a plain `podmaxxer ...` command once installed.
- Commit `uv.lock` for reproducible installs. After changing dependencies, run `uv sync` before
  testing to ensure the environment matches the lockfile.
- Once a linter/formatter/test runner is chosen, add the actual `uv run <tool>` commands here.

## Python CLI best practices

- Keep the CLI/argument-parsing layer thin — a `cli.py` (or `__main__.py`) that parses input and
  calls into plain, importable functions/classes in other modules. Business logic should be
  testable without going through the CLI entry point.
- Structure subcommands/flags around the three input kinds already defined by the product
  (RSS feed, file path, URL), rather than one generic "process" command with ad-hoc flags bolted
  on.
- Follow standard Unix conventions: human-readable results to stdout, logs/progress/diagnostics to
  stderr, non-zero exit codes on failure, and a non-interactive mode that never blocks on a prompt
  (needed for RSS/batch runs).
- Make the SQLite state file location configurable (flag/env var, with a sensible default under a
  user config/cache directory) rather than hardcoding a path — don't assume the CWD is writable or
  stable across runs.
- Every operation that touches the network, disk, or the transcription/summarization pipeline
  should be resumable and safe to re-run, consistent with the statefulness design above — design
  new commands with that idempotency in mind from the start rather than retrofitting it.
- Prefer explicit, typed function signatures (type hints throughout) so state-machine/pipeline
  logic stays easy to follow as it grows.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
