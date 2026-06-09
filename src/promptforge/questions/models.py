from dataclasses import dataclass, field


@dataclass
class ClarifyingQuestion:
    question_id: str
    question_text: str
    is_required: bool
    source_issue_ids: list[str] = field(default_factory=list)


@dataclass
class UserAnswer:
    question_id: str
    answer_text: str
    skipped: bool = False
