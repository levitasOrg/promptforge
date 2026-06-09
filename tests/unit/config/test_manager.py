"""Tests for config/manager.py."""

import os
import sys
from pathlib import Path

import pytest

from promptforge.config.manager import ConfigError, ConfigManager
from tests.fixtures import make_app_config


def write_config(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


VALID_TOML = """
[llm]
provider = "anthropic"
model = "claude-haiku-3-5"
api_key = "sk-ant-test"
litellm_model_string = "anthropic/claude-haiku-3-5"

[preferences]
default_mode = "interactive"
show_diff = false
default_inject_code = false
"""


def test_load_happy_path(tmp_path):
    config_path = tmp_path / "config.toml"
    write_config(config_path, VALID_TOML)
    manager = ConfigManager(config_path=config_path)
    config = manager.load()
    assert config.provider == "anthropic"
    assert config.model == "claude-haiku-3-5"
    assert config.api_key == "sk-ant-test"
    assert config.litellm_model_string == "anthropic/claude-haiku-3-5"
    assert config.litellm_base_url is None


def test_load_raises_config_error_for_missing_file(tmp_path):
    manager = ConfigManager(config_path=tmp_path / "nonexistent.toml")
    with pytest.raises(ConfigError, match="not found"):
        manager.load()


def test_load_raises_config_error_for_malformed_toml(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("this is not [valid toml <<<", encoding="utf-8")
    manager = ConfigManager(config_path=config_path)
    with pytest.raises(ConfigError, match="Malformed TOML"):
        manager.load()


def test_load_raises_config_error_for_missing_required_field(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[llm]\nprovider = 'anthropic'\n", encoding="utf-8")
    manager = ConfigManager(config_path=config_path)
    with pytest.raises(ConfigError, match="Missing required config field"):
        manager.load()


def test_save_writes_correct_toml(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path=config_path)
    config = make_app_config()
    manager.save(config)

    assert config_path.exists()
    import tomllib
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["llm"]["provider"] == config.provider
    # API key is stored in OS keychain; config file holds the placeholder or the raw key
    assert data["llm"]["api_key"] in ("__keyring__", config.api_key)
    assert data["llm"]["litellm_model_string"] == config.litellm_model_string
    assert "litellm_base_url" not in data["llm"]


def test_save_includes_base_url_when_set(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path=config_path)
    config = make_app_config(litellm_base_url="https://api.githubcopilot.com")
    manager.save(config)

    import tomllib
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    assert data["llm"]["litellm_base_url"] == "https://api.githubcopilot.com"


@pytest.mark.skipif(sys.platform == "win32", reason="chmod not applicable on Windows")
def test_save_sets_chmod_600(tmp_path):
    config_path = tmp_path / "config.toml"
    manager = ConfigManager(config_path=config_path)
    manager.save(make_app_config())
    mode = oct(os.stat(config_path).st_mode)[-3:]
    assert mode == "600"


def test_validate_key_returns_true_on_success(tmp_path):
    from unittest.mock import MagicMock, patch

    config = make_app_config()
    manager = ConfigManager(config_path=tmp_path / "config.toml")

    mock_response = MagicMock()
    with patch("litellm.completion", return_value=mock_response):
        result = manager.validate_key(config)

    assert result is True


def test_validate_key_returns_false_on_auth_error(tmp_path):
    from unittest.mock import patch

    import litellm

    config = make_app_config()
    manager = ConfigManager(config_path=tmp_path / "config.toml")

    with patch("litellm.completion", side_effect=litellm.AuthenticationError("bad key", llm_provider="anthropic", model="claude-haiku-3-5")):
        result = manager.validate_key(config)

    assert result is False
