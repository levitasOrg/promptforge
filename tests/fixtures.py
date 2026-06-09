"""
Fixture factories — single source of truth for test data.
Per § 10 of the plan. Filled in as later phases need them.
"""

from promptforge.config.models import AppConfig


def make_app_config(**kwargs) -> AppConfig:
    defaults = {
        "provider": "anthropic",
        "model": "claude-haiku-3-5",
        "api_key": "sk-ant-test-key-1234567890",
        "litellm_model_string": "anthropic/claude-haiku-3-5",
        "litellm_base_url": None,
    }
    defaults.update(kwargs)
    return AppConfig(**defaults)
