"""Integration tests for the `correct` command."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from promptforge.cli import app
from promptforge.config.models import AppConfig

runner = CliRunner()


def make_mock_llm_response(text="Corrected prompt."):
    mock = MagicMock()
    mock.choices[0].message.content = text
    return mock


def make_app_config():
    return AppConfig(
        provider="anthropic",
        model="claude-haiku-3-5",
        api_key="sk-test-key",
        litellm_model_string="anthropic/claude-haiku-3-5",
        litellm_base_url=None,
    )


def test_correct_command_reads_file(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("help me with the code")
    with (
        patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()),
        patch("litellm.completion", return_value=make_mock_llm_response("Corrected.")),
        patch("promptforge.stats.logger.UsageLogger.record"),
    ):
        result = runner.invoke(app, ["correct", str(prompt_file), "--no-questions", "--no-clipboard"])
    assert result.exit_code == 0, result.output
    assert "Corrected." in result.output


def test_correct_missing_file_exits_1(tmp_path):
    with patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()):
        result = runner.invoke(app, ["correct", str(tmp_path / "nonexistent.txt"), "--no-questions", "--no-clipboard"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_correct_missing_config_exits_1(tmp_path):
    from promptforge.config.manager import ConfigError
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("fix my prompt")
    with patch("promptforge.config.manager.ConfigManager.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["correct", str(prompt_file), "--no-questions", "--no-clipboard"])
    assert result.exit_code == 1
    assert "configure" in result.output.lower()
