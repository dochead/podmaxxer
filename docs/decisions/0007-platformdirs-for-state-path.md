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
