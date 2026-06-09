"""Integration tests for the `configure` command."""

from unittest.mock import patch

from typer.testing import CliRunner

from promptforge.cli import app
from promptforge.config.models import AppConfig

runner = CliRunner()


def _invoke(inputs: list[str]):
    """Helper: join inputs with newlines and invoke the configure command."""
    return runner.invoke(app, ["configure"], input="\n".join(inputs) + "\n")


# ---------------------------------------------------------------------------
# Happy path: provider 1 (OpenAI), model 1, valid key on first attempt
# ---------------------------------------------------------------------------

def test_happy_path_exit_0_and_save_called():
    with (
        patch("promptforge.config.manager.ConfigManager.validate_key", return_value=True) as mock_validate,
        patch("promptforge.config.manager.ConfigManager.save") as mock_save,
    ):
        result = _invoke(["1", "1", "sk-validkey"])

    assert result.exit_code == 0, result.output
    mock_validate.assert_called_once()
    mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# Invalid key on first attempt, valid on second → save called, exit 0
# ---------------------------------------------------------------------------

def test_invalid_then_valid_key_save_called():
    with (
        patch("promptforge.config.manager.ConfigManager.validate_key", side_effect=[False, True]) as mock_validate,
        patch("promptforge.config.manager.ConfigManager.save") as mock_save,
    ):
        # provider 1, model 1, bad key, then good key
        result = _invoke(["1", "1", "sk-bad", "sk-good"])

    assert result.exit_code == 0, result.output
    assert mock_validate.call_count == 2
    mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# Three consecutive failures → exit 2, save NOT called
# ---------------------------------------------------------------------------

def test_three_failures_exit_2_no_save():
    with (
        patch("promptforge.config.manager.ConfigManager.validate_key", return_value=False),
        patch("promptforge.config.manager.ConfigManager.save") as mock_save,
    ):
        result = _invoke(["1", "1", "bad1", "bad2", "bad3"])

    assert result.exit_code == 2, result.output
    mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Correct provider/model values are passed to save
# ---------------------------------------------------------------------------

def test_save_called_with_correct_provider_and_model():
    captured: list[AppConfig] = []

    def fake_save(self, config: AppConfig) -> None:  # noqa: ANN001
        captured.append(config)

    with (
        patch("promptforge.config.manager.ConfigManager.validate_key", return_value=True),
        patch("promptforge.config.manager.ConfigManager.save", fake_save),
    ):
        # provider 1 = OpenAI, model 2 = gpt-4.1 (second in list)
        result = _invoke(["1", "2", "sk-test"])

    assert result.exit_code == 0, result.output
    assert len(captured) == 1
    saved = captured[0]
    assert saved.provider == "openai"
    assert saved.model == "gpt-4.1"
    assert saved.api_key == "sk-test"
    assert saved.litellm_model_string == "openai/gpt-4.1"
    assert saved.litellm_base_url is None
