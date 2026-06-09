from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Issue:
    detector_id: str
    severity: IssueSeverity
    description: str
    fragment: str


@dataclass
class AnalysisReport:
    raw_prompt: str
    issues: list[Issue]
    detected_intent: str
    detected_domain: str
    issue_count_by_severity: dict[str, int] = field(default_factory=dict)
    has_output_format_issue: bool = False
