"""Config manager for PromptForge."""

import os
import sys
import tomllib
from pathlib import Path

import tomli_w

from promptforge.config.models import AppConfig

CONFIG_PATH = Path.home() / ".config" / "promptforge" / "config.toml"


class ConfigError(Exception):
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
            return AppConfig(
                provider=llm["provider"],
                model=llm["model"],
                api_key=llm["api_key"],
                litellm_model_string=llm["litellm_model_string"],
                litellm_base_url=llm.get("litellm_base_url"),
            )
        except KeyError as e:
            raise ConfigError(f"Missing required config field: {e}") from e

    def save(self, config: AppConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        llm_section: dict[str, str] = {
            "provider": config.provider,
            "model": config.model,
            "api_key": config.api_key,
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
            # Treat any auth / missing-key / bad-key error as invalid.
            # LiteLLM raises different exception types per provider:
            #   AuthenticationError  — OpenAI, Anthropic, Mistral, Groq
            #   APIConnectionError   — Gemini (wraps ValueError for missing key)
            #   BadRequestError      — some providers on bad model/key combos
            # A network timeout is a different kind of failure — re-raise it
            # so the wizard can show a more specific message.
            err = str(e).lower()
            is_auth_failure = any(kw in err for kw in (
                "auth", "api key", "api_key", "invalid key",
                "missing", "unauthorized", "permission", "credential",
            ))
            if is_auth_failure:
                return False
            raise  # re-raise network / unexpected errors
