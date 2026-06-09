from dataclasses import dataclass


@dataclass(kw_only=True)
class UsageRecord:
    session_id: str
    timestamp: str
    command: str
    mode: str
    original_token_estimate: int
    optimized_token_estimate: int
    tool_input_tokens: int
    tool_output_tokens: int
    tool_total_tokens: int
    provider: str
    model: str
    issues_detected: int
    questions_asked: int
    questions_answered: int
    reduction_pct: float
    injected_tokens: int | None = None
    repo_slug: str | None = None
    files_indexed: int | None = None
    files_injected: int | None = None
    template_id: str | None = None
    rating: int | None = None
    rated_at: str | None = None
    record_type: str = "session"


@dataclass(kw_only=True)
class RatingRecord:
    session_id: str
    rating: int
    rated_at: str
    record_type: str = "rating"
