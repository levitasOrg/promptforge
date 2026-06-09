from dataclasses import dataclass, field


@dataclass
class OptimizedPrompt:
    text: str
    token_estimate: int
    model_used: str
    session_id: str
    sections: dict[str, str] = field(default_factory=dict)
    repo_slug: str | None = None
    injected_files: list[str] = field(default_factory=list)
