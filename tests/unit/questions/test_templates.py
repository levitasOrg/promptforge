import pytest
from promptforge.questions.templates import TEMPLATES


EXPECTED_KEYS = {
    "output_format",
    "missing_context",
    "audience",
    "scope",
    "input_schema",
    "action_verb",
    "examples",
}

REQUIRED_KEYS = {"output_format", "missing_context", "input_schema"}
OPTIONAL_KEYS = {"audience", "scope", "action_verb", "examples"}


def test_all_seven_keys_present():
    assert set(TEMPLATES.keys()) == EXPECTED_KEYS


def test_each_question_has_non_empty_fields():
    for key, q in TEMPLATES.items():
        assert q.question_id, f"{key}: question_id is empty"
        assert q.question_text, f"{key}: question_text is empty"
        assert q.source_issue_ids, f"{key}: source_issue_ids is empty"


def test_required_flags():
    for key in REQUIRED_KEYS:
        assert TEMPLATES[key].is_required is True, f"{key} should be required"

    for key in OPTIONAL_KEYS:
        assert TEMPLATES[key].is_required is False, f"{key} should not be required"
