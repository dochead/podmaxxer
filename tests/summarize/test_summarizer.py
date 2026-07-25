from podmaxxer.summarize import summarizer


def test_build_prompt_includes_template_and_transcript():
    prompt = summarizer.build_prompt("Focus on action items.", "We discussed the roadmap.")
    assert "Focus on action items." in prompt
    assert "We discussed the roadmap." in prompt


def test_summarize_calls_openai_with_built_prompt(monkeypatch):
    captured = {}

    def fake_call_openai(prompt, api_key):
        captured["prompt"] = prompt
        captured["api_key"] = api_key
        return "final summary"

    monkeypatch.setattr(summarizer, "call_openai", fake_call_openai)

    result = summarizer.summarize("template text", "transcript text", api_key="sk-test")

    assert result == "final summary"
    assert "template text" in captured["prompt"]
    assert "transcript text" in captured["prompt"]
    assert captured["api_key"] == "sk-test"
