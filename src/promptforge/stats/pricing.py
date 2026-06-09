# Pricing as of 2025-06. Always verify at provider's pricing page — rates change.
# Format: model_substring → (input_price_per_1m_tokens, output_price_per_1m_tokens)
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-3-5": (0.80, 4.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-5": (15.00, 75.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    "mistral-small": (0.20, 0.60),
    "mistral-medium": (2.70, 8.10),
    "mistral-large": (4.00, 12.00),
    "llama-3.1-8b": (0.05, 0.08),
    "llama-3.1-70b": (0.59, 0.79),
    "mixtral-8x7b": (0.24, 0.24),
}


def get_price(model: str) -> tuple[float, float] | None:
    """Return (input, output) $/1M tokens for the given model string (substring match)."""
    model_lower = model.lower()
    for key, price in PRICING.items():
        if key in model_lower:
            return price
    return None
