from __future__ import annotations

from podmaxxer.summarize.openai_client import call_openai


def build_prompt(template: str, transcript: str) -> str:
    return f"{template.strip()}\n\n---\n\nTranscript:\n{transcript.strip()}"


def summarize(template: str, transcript: str, api_key: str) -> str:
    prompt = build_prompt(template, transcript)
    return call_openai(prompt, api_key)
