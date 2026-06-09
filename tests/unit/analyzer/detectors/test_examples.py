from promptforge.analyzer.detectors.examples import detect
from promptforge.analyzer.models import AnalysisReport, IssueSeverity


def make_report(has_output_format_issue: bool) -> AnalysisReport:
    return AnalysisReport(
        raw_prompt="",
        issues=[],
        detected_intent="",
        detected_domain="",
        has_output_format_issue=has_output_format_issue
    )


LONG_PROMPT = (
    "Transform the user data from the legacy database format into the new schema. "
    "The transformation should handle edge cases like missing fields and null values. "
    "Make sure to validate the output against the schema definition before returning. "
    "The process must be idempotent and safe to run multiple times on the same dataset "
    "without causing duplicate records or data corruption in the target system."
)  # > 50 words


SHORT_PROMPT = "Transform the data and return the result."  # <= 50 words


def test_fires_when_long_no_example_has_format_issue():
    report = make_report(has_output_format_issue=True)
    issues = detect(LONG_PROMPT, report)
    assert len(issues) == 1
    assert issues[0].detector_id == "examples"
    assert issues[0].severity == IssueSeverity.LOW
    assert issues[0].fragment == "(no example)"


def test_no_fire_when_no_format_issue():
    report = make_report(has_output_format_issue=False)
    issues = detect(LONG_PROMPT, report)
    assert issues == []


def test_no_fire_when_short_prompt():
    report = make_report(has_output_format_issue=True)
    issues = detect(SHORT_PROMPT, report)
    assert issues == []


def test_no_fire_when_example_present():
    report = make_report(has_output_format_issue=True)
    prompt = LONG_PROMPT + " For instance, {name: 'Alice', age: 30} becomes {full_name: 'Alice', years: 30}."
    issues = detect(prompt, report)
    assert issues == []


def test_no_fire_with_eg_marker():
    report = make_report(has_output_format_issue=True)
    prompt = LONG_PROMPT + " e.g. use snake_case for all field names in the output."
    issues = detect(prompt, report)
    assert issues == []
