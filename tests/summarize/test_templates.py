from podmaxxer.content import hash_text
from podmaxxer.summarize.templates import load_template


def test_load_default_template_when_no_path_given():
    text, template_hash = load_template(None)
    assert "summarizing a transcript" in text
    assert template_hash == hash_text(text)


def test_load_custom_template_from_path(tmp_path):
    custom = tmp_path / "custom.txt"
    custom.write_text("Focus only on action items.", encoding="utf-8")

    text, template_hash = load_template(custom)

    assert text == "Focus only on action items."
    assert template_hash == hash_text(text)


def test_different_templates_hash_differently(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("Template A", encoding="utf-8")
    b.write_text("Template B", encoding="utf-8")

    _, hash_a = load_template(a)
    _, hash_b = load_template(b)

    assert hash_a != hash_b
