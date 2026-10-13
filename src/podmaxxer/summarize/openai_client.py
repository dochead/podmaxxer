from __future__ import annotations

import requests

from podmaxxer.config import get_openai_base_url, get_summary_model
from podmaxxer.errors import SummarizationError

# Kept for tests/back-compat; the live URL is derived from PODMAXXER_OPENAI_BASE_URL.
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def call_openai(
    prompt: str,
    api_key: str | None,
    model: str | None = None,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> str:
    http = session or requests
    url = f"{(base_url or get_openai_base_url()).rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = http.post(
            url,
            headers=headers,
            json={
                "model": model or get_summary_model(),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
    except requests.RequestException as exc:
        raise SummarizationError(f"Summarization request failed: {exc}") from exc

    if response.status_code != 200:
        raise SummarizationError(
            f"Summarization API error {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise SummarizationError(f"Unexpected response shape: {str(data)[:500]}") from exc
