# 0001. Stage-pipeline architecture with a `Source` abstraction

Date: 2026-07-24
Status: Accepted

## Context

The MVP pipeline is: acquire content → get transcript (existing or Whisper) → summarize → output.
Beyond the MVP, the product vision adds more input kinds (RSS feeds, YouTube) that must slot into
the same downstream transcription/summarization/state logic.

Three approaches were considered:
- **Flat scripts per input kind** — least code now, but duplicates acquisition/orchestration logic
  per input kind and makes stages hard to unit test in isolation from CLI glue.
- **Stage-per-module pipeline with a `Source` interface** — each stage (acquire, transcript,
  summarize, output) is a small module with a narrow contract; input kinds implement `Source.fetch()
  -> Content` and everything downstream is blind to where content came from.
- **Job-queue-in-SQLite model** — stages as decoupled workers picking up jobs by state; natural fit
  for batch/RSS processing but substantial overreach for an MVP processing one item at a time
  synchronously.

## Decision

Use the stage-per-module pipeline with a `Source` abstraction (`src/podmaxxer/sources/base.py`).

## Consequences

- Each stage is independently testable against fixtures — a good match for the TDD requirement.
- Adding RSS/YouTube later means adding another `Source` implementation; no changes needed to
  transcription, summarization, or state logic.
- Idempotency checks live in one place (`state/repository.py`), not scattered per input kind.
- Slightly more upfront structure (an interface plus several small classes) than a flat script,
  accepted as the smaller long-term cost.
