from __future__ import annotations

import requests

from podmaxxer.errors import SummarizationError

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


def call_openai(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    session: requests.Session | None = None,
) -> str:
    http = session or requests
    try:
        response = http.post(
            OPENAI_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=60,
        )
    except requests.RequestException as exc:
        raise SummarizationError(f"OpenAI request failed: {exc}") from exc

    if response.status_code != 200:
        raise SummarizationError(f"OpenAI API error {response.status_code}: {response.text}")

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise SummarizationError(f"Unexpected OpenAI response shape: {data}") from exc
