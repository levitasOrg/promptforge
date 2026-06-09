from dataclasses import dataclass, field


@dataclass
class PromptContext:
    raw_prompt: str
    detected_intent: str
    detected_domain: str
    role_definition: str | None = None
    target_audience: str | None = None
    output_format: str | None = None
    output_schema: str | None = None
    input_description: str | None = None
    examples_requested: bool = False
    additional_context: str | None = None
    scope_constraints: list[str] = field(default_factory=list)
