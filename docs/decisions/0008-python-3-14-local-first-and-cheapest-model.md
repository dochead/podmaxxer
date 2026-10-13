# 0008. Stay on Python 3.14, local-first processing, cheapest current model

Date: 2026-10-13
Status: Accepted

## Context

Revisiting the MVP after a few months. Python 3.15.0 had been out only weeks, and the native
dependencies behind faster-whisper (ctranslate2, onnxruntime) typically lag new CPython releases.
The project also pointed at an internal package index, which is wrong for a personal project, and
defaulted to `gpt-4o-mini`, now two generations old.

## Decision

- **Python 3.14** (`requires-python = ">=3.14"`, `.python-version` = 3.14). Revisit 3.15 once
  dependency wheels are established.
- **Public PyPI** only; the internal index is removed from `pyproject.toml`.
- **Default model `gpt-6-luna`**, the cheapest model of the current OpenAI generation
  ($0.10 / $0.50 per 1M input/output tokens at time of writing). Overridable with `PODMAXXER_MODEL`.
- **Local-first.** Transcription is always local (faster-whisper, CPU int8, size configurable via
  `PODMAXXER_WHISPER_MODEL`, default `small`). Summarization can target any OpenAI-compatible
  endpoint via `PODMAXXER_OPENAI_BASE_URL` (Ollama, llama.cpp), in which case no API key is needed.
- **Injected seams.** `process()` accepts a `transcriber` and an `llm` callable so stages can be
  faked in tests without monkeypatching and swapped for other backends later.

## Consequences

- Fully offline, zero-marginal-cost operation is possible.
- Pricing is a snapshot; the default should be re-checked periodically.
- A cloud transcription fallback (e.g. OpenAI `gpt-transcribe`) is deliberately not built; add it
  only if local quality or speed proves inadequate.
