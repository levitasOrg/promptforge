"""Provider registry for PromptForge — models current as of June 2025."""

from promptforge.config.models import Model, Provider

COPILOT_BASE_URL = "https://api.githubcopilot.com"

_PROVIDERS: list[Provider] = [
    # ── OpenAI ───────────────────────────────────────────────────────────────
    Provider(
        id="openai",
        display_name="OpenAI",
        auth_label="OpenAI API Key",
        models=[
            Model(
                id="gpt-4.1-mini",
                display_name="GPT-4.1 Mini ★  (fast, cheap — recommended)",
                litellm_string="openai/gpt-4.1-mini",
                is_recommended=True,
            ),
            Model(
                id="gpt-4.1",
                display_name="GPT-4.1       (latest, most capable)",
                litellm_string="openai/gpt-4.1",
            ),
            Model(
                id="gpt-4o",
                display_name="GPT-4o        (stable, widely used)",
                litellm_string="openai/gpt-4o",
            ),
            Model(
                id="gpt-4o-mini",
                display_name="GPT-4o Mini   (previous gen, budget)",
                litellm_string="openai/gpt-4o-mini",
            ),
            Model(
                id="o4-mini",
                display_name="o4-mini       (reasoning model)",
                litellm_string="openai/o4-mini",
            ),
        ],
    ),

    # ── Anthropic ────────────────────────────────────────────────────────────
    Provider(
        id="anthropic",
        display_name="Anthropic",
        auth_label="Anthropic API Key",
        models=[
            Model(
                id="claude-haiku-4-5",
                display_name="Claude Haiku 4.5 ★  (fastest, cheapest — recommended)",
                litellm_string="anthropic/claude-haiku-4-5-20251001",
                is_recommended=True,
            ),
            Model(
                id="claude-sonnet-4-6",
                display_name="Claude Sonnet 4.6   (balanced, current flagship)",
                litellm_string="anthropic/claude-sonnet-4-6",
            ),
            Model(
                id="claude-opus-4-7",
                display_name="Claude Opus 4.7     (most capable, highest cost)",
                litellm_string="anthropic/claude-opus-4-7",
            ),
        ],
    ),

    # ── Google Gemini ────────────────────────────────────────────────────────
    Provider(
        id="google",
        display_name="Google Gemini",
        auth_label="Google AI API Key",
        models=[
            Model(
                id="gemini-2.5-flash",
                display_name="Gemini 2.5 Flash ★  (latest, fast — recommended)",
                litellm_string="gemini/gemini-2.5-flash",
                is_recommended=True,
            ),
            Model(
                id="gemini-2.5-pro",
                display_name="Gemini 2.5 Pro      (latest, most capable)",
                litellm_string="gemini/gemini-2.5-pro",
            ),
            Model(
                id="gemini-2.0-flash",
                display_name="Gemini 2.0 Flash    (previous gen, solid)",
                litellm_string="gemini/gemini-2.0-flash",
            ),
            Model(
                id="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash    (legacy, widest availability)",
                litellm_string="gemini/gemini-1.5-flash",
            ),
        ],
    ),

    # ── Mistral ──────────────────────────────────────────────────────────────
    Provider(
        id="mistral",
        display_name="Mistral",
        auth_label="Mistral API Key",
        models=[
            Model(
                id="mistral-small-latest",
                display_name="Mistral Small ★  (fast, cheap — recommended)",
                litellm_string="mistral/mistral-small-latest",
                is_recommended=True,
            ),
            Model(
                id="mistral-large-latest",
                display_name="Mistral Large    (most capable)",
                litellm_string="mistral/mistral-large-latest",
            ),
            Model(
                id="codestral-latest",
                display_name="Codestral        (optimised for code tasks)",
                litellm_string="mistral/codestral-latest",
            ),
            Model(
                id="mistral-nemo",
                display_name="Mistral Nemo     (lightweight, open-weight)",
                litellm_string="mistral/open-mistral-nemo",
            ),
        ],
    ),

    # ── Groq ─────────────────────────────────────────────────────────────────
    Provider(
        id="groq",
        display_name="Groq",
        auth_label="Groq API Key",
        models=[
            Model(
                id="llama-3.3-70b-versatile",
                display_name="LLaMA 3.3 70B ★  (latest, best quality — recommended)",
                litellm_string="groq/llama-3.3-70b-versatile",
                is_recommended=True,
            ),
            Model(
                id="llama-3.1-8b-instant",
                display_name="LLaMA 3.1 8B Instant  (fastest, lowest cost)",
                litellm_string="groq/llama-3.1-8b-instant",
            ),
            Model(
                id="gemma2-9b-it",
                display_name="Gemma 2 9B            (Google open-weight)",
                litellm_string="groq/gemma2-9b-it",
            ),
            Model(
                id="mixtral-8x7b",
                display_name="Mixtral 8x7B          (mixture-of-experts)",
                litellm_string="groq/mixtral-8x7b-32768",
            ),
        ],
    ),

    # ── GitHub Copilot ───────────────────────────────────────────────────────
    Provider(
        id="copilot",
        display_name="GitHub Copilot",
        auth_label="GitHub Personal Access Token (copilot scope)",
        models=[
            Model(
                id="gpt-4.1",
                display_name="GPT-4.1     ★  (latest — recommended)",
                litellm_string="openai/gpt-4.1",
                is_recommended=True,
            ),
            Model(
                id="gpt-4o",
                display_name="GPT-4o         (stable)",
                litellm_string="openai/gpt-4o",
            ),
            Model(
                id="gpt-4o-mini",
                display_name="GPT-4o Mini    (budget)",
                litellm_string="openai/gpt-4o-mini",
            ),
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
