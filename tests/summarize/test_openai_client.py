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
    responses.add(responses.POST, OPENAI_CHAT_COMPLETIONS_URL, json={"unexpected": "shape"}, status=200)

    with pytest.raises(SummarizationError):
        call_openai("summarize this", api_key="sk-test")
