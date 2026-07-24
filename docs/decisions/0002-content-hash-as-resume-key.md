# 0002. Content hash as the resume/idempotency key

Date: 2026-07-24
Status: Accepted

## Context

Podmaxxer must avoid redundant downloads/transcription/summarization when re-run on the same
input, and must resume cleanly after a crash mid-pipeline. Candidate keys considered: the raw
input string (file path or URL), or a hash of the fetched content itself.

A file path or URL is not a reliable identity for the underlying content — a URL's content can
change, and a local file can be moved/renamed without its content changing.

## Decision

Key all state rows (`items`, `transcripts`, `summaries`) by `content_hash`, a SHA-256 hash computed
over the fetched bytes/text after acquisition. `summaries` additionally key on `template_hash` so
the same content can be re-summarized under a different template without re-transcribing.

## Consequences

- Re-running the tool on identical content is a no-op past whatever stage already has a row,
  regardless of how that content was referenced (path/URL).
- Fetching must complete before a content identity exists — the `items` row is written only after
  a successful fetch, not before.
- If the same content is deliberately re-summarized with a new template, only the summarize stage
  re-runs.
