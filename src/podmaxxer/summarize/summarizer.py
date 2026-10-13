from __future__ import annotations

from collections.abc import Callable

from podmaxxer.summarize.openai_client import call_openai

# prompt -> summary text. The seam for swapping/faking the LLM backend.
Summarizer = Callable[[str], str]


def build_prompt(template: str, transcript: str) -> str:
    return f"{template.strip()}\n\n---\n\nTranscript:\n{transcript.strip()}"


def summarize(
    template: str, transcript: str, api_key: str | None, llm: Summarizer | None = None
) -> str:
    prompt = build_prompt(template, transcript)
    if llm is not None:
        return llm(prompt)
    return call_openai(prompt, api_key)
