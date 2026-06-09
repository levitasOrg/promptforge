"""Tests for config/providers.py."""

from promptforge.config.providers import ProviderRegistry


def test_six_providers():
    registry = ProviderRegistry()
    providers = registry.get_providers()
    assert len(providers) == 6


def test_each_provider_has_at_least_one_model():
    registry = ProviderRegistry()
    for provider in registry.get_providers():
        assert len(provider.models) >= 1, f"{provider.id} has no models"


def test_each_model_has_nonempty_litellm_string():
    registry = ProviderRegistry()
    for provider in registry.get_providers():
        for model in provider.models:
            assert model.litellm_string, f"{provider.id}/{model.id} has empty litellm_string"


def test_each_provider_has_exactly_one_recommended_model():
    registry = ProviderRegistry()
    for provider in registry.get_providers():
        recommended = [m for m in provider.models if m.is_recommended]
        assert len(recommended) == 1, f"{provider.id} has {len(recommended)} recommended models"


def test_copilot_auth_label_contains_personal_access_token():
    registry = ProviderRegistry()
    copilot = registry.get_provider("copilot")
    assert copilot is not None
    assert "Personal Access Token" in copilot.auth_label


def test_get_provider_returns_none_for_unknown():
    registry = ProviderRegistry()
    assert registry.get_provider("nonexistent") is None


def test_get_provider_returns_correct_provider():
    registry = ProviderRegistry()
    anthropic = registry.get_provider("anthropic")
    assert anthropic is not None
    assert anthropic.display_name == "Anthropic"
