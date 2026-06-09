"""Provider registry for PromptForge."""

from promptforge.config.models import Model, Provider

COPILOT_BASE_URL = "https://api.githubcopilot.com"

_PROVIDERS: list[Provider] = [
    Provider(
        id="openai",
        display_name="OpenAI",
        auth_label="OpenAI API Key",
        models=[
            Model(id="gpt-4o-mini", display_name="GPT-4o Mini", litellm_string="openai/gpt-4o-mini", is_recommended=True),
            Model(id="gpt-4o", display_name="GPT-4o", litellm_string="openai/gpt-4o"),
            Model(id="gpt-4-turbo", display_name="GPT-4 Turbo", litellm_string="openai/gpt-4-turbo"),
        ],
    ),
    Provider(
        id="anthropic",
        display_name="Anthropic",
        auth_label="Anthropic API Key",
        models=[
            Model(id="claude-haiku-3-5", display_name="Claude Haiku 3.5", litellm_string="anthropic/claude-haiku-3-5", is_recommended=True),
            Model(id="claude-sonnet-4-5", display_name="Claude Sonnet 4.5", litellm_string="anthropic/claude-sonnet-4-5"),
            Model(id="claude-opus-4-5", display_name="Claude Opus 4.5", litellm_string="anthropic/claude-opus-4-5"),
        ],
    ),
    Provider(
        id="google",
        display_name="Google Gemini",
        auth_label="Google AI API Key",
        models=[
            Model(id="gemini-1.5-flash", display_name="Gemini 1.5 Flash", litellm_string="gemini/gemini-1.5-flash", is_recommended=True),
            Model(id="gemini-1.5-pro", display_name="Gemini 1.5 Pro", litellm_string="gemini/gemini-1.5-pro"),
        ],
    ),
    Provider(
        id="mistral",
        display_name="Mistral",
        auth_label="Mistral API Key",
        models=[
            Model(id="mistral-small", display_name="Mistral Small", litellm_string="mistral/mistral-small", is_recommended=True),
            Model(id="mistral-medium", display_name="Mistral Medium", litellm_string="mistral/mistral-medium"),
            Model(id="mistral-large", display_name="Mistral Large", litellm_string="mistral/mistral-large"),
        ],
    ),
    Provider(
        id="groq",
        display_name="Groq",
        auth_label="Groq API Key",
        models=[
            Model(id="llama-3.1-8b-instant", display_name="LLaMA 3.1 8B Instant", litellm_string="groq/llama-3.1-8b-instant", is_recommended=True),
            Model(id="llama-3.1-70b", display_name="LLaMA 3.1 70B", litellm_string="groq/llama-3.1-70b-versatile"),
            Model(id="mixtral-8x7b", display_name="Mixtral 8x7B", litellm_string="groq/mixtral-8x7b-32768"),
        ],
    ),
    Provider(
        id="copilot",
        display_name="GitHub Copilot",
        auth_label="GitHub Personal Access Token (copilot scope)",
        models=[
            Model(id="gpt-4o", display_name="GPT-4o", litellm_string="openai/gpt-4o", is_recommended=True),
            Model(id="gpt-4o-mini", display_name="GPT-4o Mini", litellm_string="openai/gpt-4o-mini"),
        ],
    ),
]


class ProviderRegistry:
    def get_providers(self) -> list[Provider]:
        return list(_PROVIDERS)

    def get_provider(self, id: str) -> Provider | None:
        for p in _PROVIDERS:
            if p.id == id:
                return p
        return None
