from click.testing import CliRunner

from podmaxxer import cli as cli_module
from podmaxxer.errors import PodmaxxerError


def test_file_command_prints_summary(monkeypatch, tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(cli_module, "connect", lambda db_path: "fake-conn")
    monkeypatch.setattr(cli_module, "process", lambda source, conn, api_key, template_path=None: "the summary")

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["file", str(path)])

    assert result.exit_code == 0
    assert "the summary" in result.output


def test_missing_api_key_exits_nonzero(monkeypatch, tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["file", str(path)])

    assert result.exit_code != 0
    assert "OPENAI_API_KEY" in result.output


def test_pipeline_error_reported_on_stderr_with_nonzero_exit(monkeypatch, tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(cli_module, "connect", lambda db_path: "fake-conn")

    def raise_error(source, conn, api_key, template_path=None):
        raise PodmaxxerError("boom")

    monkeypatch.setattr(cli_module, "process", raise_error)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["file", str(path)])

    assert result.exit_code != 0
    assert "boom" in result.output


def test_url_command_invokes_pipeline(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(cli_module, "connect", lambda db_path: "fake-conn")
    monkeypatch.setattr(cli_module, "process", lambda source, conn, api_key, template_path=None: "url summary")

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["url", "https://example.com/a.mp3"])

    assert result.exit_code == 0
    assert "url summary" in result.output
