"""Integration tests for the `run` command."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from promptforge.cli import app
from promptforge.config.models import AppConfig

runner = CliRunner()


def make_mock_llm_response(text="You are a helpful assistant. Do the task clearly."):
    mock = MagicMock()
    mock.choices[0].message.content = text
    return mock


def make_app_config(provider="anthropic", model="claude-haiku-3-5"):
    return AppConfig(
        provider=provider,
        model=model,
        api_key="sk-test-key",
        litellm_model_string=f"{provider}/{model}",
        litellm_base_url=None,
    )


def test_run_happy_path_no_questions(tmp_path):
    with (
        patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()),
        patch("litellm.completion", return_value=make_mock_llm_response("Optimized prompt here.")),
        patch("promptforge.stats.logger.UsageLogger.record"),
    ):
        result = runner.invoke(app, ["run", "help me fix the code", "--no-questions", "--no-clipboard"])
    assert result.exit_code == 0, result.output
    assert "Optimized prompt here." in result.output


def test_run_missing_config_exits_1():
    from promptforge.config.manager import ConfigError
    with patch("promptforge.config.manager.ConfigManager.load", side_effect=ConfigError("not found")):
        result = runner.invoke(app, ["run", "help me", "--no-questions", "--no-clipboard"])
    assert result.exit_code == 1
    assert "configure" in result.output.lower()


def test_run_auth_error_exits_2():
    import litellm
    with (
        patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()),
        patch("litellm.completion", side_effect=litellm.AuthenticationError("bad", llm_provider="anthropic", model="claude-haiku-3-5")),
    ):
        result = runner.invoke(app, ["run", "help me", "--no-questions", "--no-clipboard"])
    assert result.exit_code == 2
    assert "configure" in result.output.lower()


def test_run_rate_limit_exits_2():
    import litellm
    with (
        patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()),
        patch("litellm.completion", side_effect=litellm.RateLimitError("limit", llm_provider="anthropic", model="claude-haiku-3-5")),
    ):
        result = runner.invoke(app, ["run", "help me", "--no-questions", "--no-clipboard"])
    assert result.exit_code == 2
    assert "rate limit" in result.output.lower()


def test_run_file_flag_reads_prompt_from_file(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("help me write a blog post about AI")
    with (
        patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()),
        patch("litellm.completion", return_value=make_mock_llm_response("Optimized.")),
        patch("promptforge.stats.logger.UsageLogger.record"),
    ):
        result = runner.invoke(app, ["run", "--file", str(prompt_file), "--no-questions", "--no-clipboard"])
    assert result.exit_code == 0
    assert "Optimized." in result.output


def test_run_stdout_contains_optimized_text():
    expected = "You are an expert. Do the thing precisely."
    with (
        patch("promptforge.config.manager.ConfigManager.load", return_value=make_app_config()),
        patch("litellm.completion", return_value=make_mock_llm_response(expected)),
        patch("promptforge.stats.logger.UsageLogger.record"),
    ):
        result = runner.invoke(app, ["run", "fix it", "--no-questions", "--no-clipboard"])
    assert expected in result.output
