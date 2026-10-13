import pytest
import responses

from podmaxxer.errors import SummarizationError
from podmaxxer.summarize.openai_client import OPENAI_CHAT_COMPLETIONS_URL, call_openai


@responses.activate
def test_call_openai_returns_message_content():
    responses.add(
        responses.POST,
        OPENAI_CHAT_COMPLETIONS_URL,
        json={"choices": [{"message": {"content": "  the summary  "}}]},
        status=200,
    )

    result = call_openai("summarize this", api_key="sk-test")

    assert result == "the summary"
    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer sk-test"


@responses.activate
def test_call_openai_raises_on_non_200():
    responses.add(responses.POST, OPENAI_CHAT_COMPLETIONS_URL, body="server error", status=500)

    with pytest.raises(SummarizationError):
        call_openai("summarize this", api_key="sk-test")


@responses.activate
def test_call_openai_raises_on_unexpected_shape():
    responses.add(
        responses.POST, OPENAI_CHAT_COMPLETIONS_URL, json={"unexpected": "shape"}, status=200
    )

    with pytest.raises(SummarizationError):
        call_openai("summarize this", api_key="sk-test")


@responses.activate
def test_call_openai_uses_configured_base_url_and_model_without_key(monkeypatch):
    monkeypatch.setenv("PODMAXXER_OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("PODMAXXER_MODEL", "llama3.2")
    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        json={"choices": [{"message": {"content": "local summary"}}]},
        status=200,
    )

    result = call_openai("summarize this", api_key=None)

    assert result == "local summary"
    sent = responses.calls[0].request
    assert "Authorization" not in sent.headers
    assert b'"model": "llama3.2"' in sent.body


@responses.activate
def test_default_model_is_gpt_6_luna(monkeypatch):
    monkeypatch.delenv("PODMAXXER_MODEL", raising=False)
    monkeypatch.delenv("PODMAXXER_OPENAI_BASE_URL", raising=False)
    responses.add(
        responses.POST,
        OPENAI_CHAT_COMPLETIONS_URL,
        json={"choices": [{"message": {"content": "x"}}]},
    )

    call_openai("p", api_key="sk-test")

    assert b'"model": "gpt-6-luna"' in responses.calls[0].request.body
