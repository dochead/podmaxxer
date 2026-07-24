# 0003. Call the OpenAI API directly via `requests`, not the official SDK

Date: 2026-07-24
Status: Accepted

## Context

Summarization requires calling a hosted LLM API. The official `openai` Python SDK wraps this in a
typed client; alternatively, `requests` can call the REST API directly. The project's stated
first-class libraries for this MVP are Click and Requests.

## Decision

Implement `summarize/openai_client.py` as a thin wrapper making direct HTTPS calls to OpenAI's
REST API using `requests`, rather than adding the `openai` SDK as a dependency.

## Consequences

- One fewer dependency; consistent with the project's stated preference for `requests` as the HTTP
  library.
- The wrapper owns request/response shaping (auth header, JSON body, error mapping) that the SDK
  would otherwise provide — kept intentionally thin since the MVP only needs one endpoint.
- If a second LLM provider or more complex API usage (streaming, retries, etc.) is needed later,
  revisit whether a dedicated SDK is worth the dependency.
