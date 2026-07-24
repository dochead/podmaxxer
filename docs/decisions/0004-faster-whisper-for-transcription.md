# 0004. `faster-whisper` over `openai-whisper` for local transcription

Date: 2026-07-24
Status: Accepted

## Context

The MVP needs local Whisper transcription as a fallback when no existing transcript/captions are
available. Two libraries were considered: `openai-whisper` (the original PyPI package, PyTorch-
based) and `faster-whisper` (a CTranslate2-based reimplementation using the same model weights).

## Decision

Use `faster-whisper`.

## Consequences

- Notably faster and lower-memory on CPU-only machines — the expected common case for a local CLI
  tool, not a GPU server.
- Same transcription quality/model weights as OpenAI's original implementation.
- Actively maintained; adds a CTranslate2 dependency instead of PyTorch.
