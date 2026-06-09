"""Config manager for PromptForge."""

import logging
import os
import sys
import tomllib
from pathlib import Path

import tomli_w

from promptforge.config.models import AppConfig

CONFIG_PATH = Path.home() / ".config" / "promptforge" / "config.toml"

_KEYRING_SERVICE = "promptforge"
_KEYRING_USERNAME = "api_key"
_KEYRING_PLACEHOLDER = "__keyring__"

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


def _keyring_set(api_key: str) -> bool:
    """Store api_key in the OS keychain. Returns True on success."""
    try:
        import keyring
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, api_key)
        return True
    except Exception as e:
        logger.warning("keyring unavailable, key stored in plain text: %s", e)
        return False


def _keyring_get() -> str | None:
    """Retrieve api_key from the OS keychain. Returns None if not found."""
    try:
        import keyring
        return keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception as e:
        logger.warning("keyring read failed: %s", e)
        return None


def _keyring_delete() -> None:
    """Remove api_key from the OS keychain."""
    try:
        import keyring
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        pass


class ConfigManager:
    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self.config_path = config_path

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")
        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Malformed TOML: {e}") from e

        try:
            llm = data["llm"]
            raw_key: str = llm["api_key"]

            # If key was stored in the OS keychain, retrieve it from there
            if raw_key == _KEYRING_PLACEHOLDER:
                keychain_key = _keyring_get()
                if not keychain_key:
                    raise ConfigError(
                        "API key not found in system keychain. "
                        "Run `promptforge configure` to re-enter it."
                    )
                api_key = keychain_key
            else:
                api_key = raw_key

            return AppConfig(
                provider=llm["provider"],
                model=llm["model"],
                api_key=api_key,
                litellm_model_string=llm["litellm_model_string"],
                litellm_base_url=llm.get("litellm_base_url"),
            )
        except KeyError as e:
            raise ConfigError(f"Missing required config field: {e}") from e

    def save(self, config: AppConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to store the API key securely in the OS keychain
        stored_in_keyring = _keyring_set(config.api_key)
        stored_key = _KEYRING_PLACEHOLDER if stored_in_keyring else config.api_key

        llm_section: dict[str, str] = {
            "provider": config.provider,
            "model": config.model,
            "api_key": stored_key,
            "litellm_model_string": config.litellm_model_string,
        }
        if config.litellm_base_url is not None:
            llm_section["litellm_base_url"] = config.litellm_base_url

        doc = {
            "llm": llm_section,
            "preferences": {
                "default_mode": "interactive",
                "show_diff": False,
                "default_inject_code": False,
            },
        }
        with open(self.config_path, "wb") as f:
            tomli_w.dump(doc, f)

        if sys.platform != "win32":
            os.chmod(self.config_path, 0o600)

    def delete(self) -> None:
        """Remove config file and keychain entry."""
        _keyring_delete()
        if self.config_path.exists():
            self.config_path.unlink()

    def validate_key(self, config: AppConfig) -> bool:
        import litellm

        kwargs: dict[str, object] = {
            "model": config.litellm_model_string,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "api_key": config.api_key,
            "num_retries": 0,  # no retries during validation
        }
        if config.litellm_base_url is not None:
            kwargs["base_url"] = config.litellm_base_url

        try:
            litellm.completion(**kwargs)
            return True
        except Exception as e:
            err = str(e).lower()
            is_auth_failure = any(kw in err for kw in (
                "auth", "api key", "api_key", "invalid key",
                "missing", "unauthorized", "permission", "credential",
            ))
            if is_auth_failure:
                return False
            raise
