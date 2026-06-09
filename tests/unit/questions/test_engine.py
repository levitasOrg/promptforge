from promptforge.analyzer.models import AnalysisReport, Issue, IssueSeverity
from promptforge.questions.engine import QuestionEngine


def make_report(issues):
    return AnalysisReport(
        raw_prompt="test",
        issues=issues,
        detected_intent="",
        detected_domain="",
    )


def make_issue(detector_id, severity, fragment="some fragment"):
    return Issue(
        detector_id=detector_id,
        severity=severity,
        description="desc",
        fragment=fragment,
    )


def test_empty_report_returns_empty_list():
    engine = QuestionEngine()
    result = engine.generate(make_report([]))
    assert result == []


def test_high_severity_before_medium():
    engine = QuestionEngine()
    issues = [
        make_issue("audience", IssueSeverity.MEDIUM),
        make_issue("output_format", IssueSeverity.HIGH),
    ]
    result = engine.generate(make_report(issues))
    ids = [q.question_id for q in result]
    assert ids.index("q_output_format") < ids.index("q_audience")


def test_duplicate_question_ids_deduplicated():
    engine = QuestionEngine()
    issues = [
        make_issue("output_format", IssueSeverity.HIGH),
        make_issue("output_format", IssueSeverity.MEDIUM),
    ]
    result = engine.generate(make_report(issues))
    q_ids = [q.question_id for q in result]
    assert q_ids.count("q_output_format") == 1


def test_fragment_substituted():
    engine = QuestionEngine()
    issues = [make_issue("missing_context", IssueSeverity.HIGH, fragment="the thing")]
    result = engine.generate(make_report(issues))
    assert len(result) == 1
    assert "the thing" in result[0].question_text
    assert "{fragment}" not in result[0].question_text


def test_max_questions_capped_at_seven():
    engine = QuestionEngine()
    # All 7 template keys + one duplicate to push over 7
    detector_ids = [
        "output_format", "missing_context", "audience", "scope",
        "input_schema", "action_verb", "examples",
        "output_format",  # duplicate, won't add but ensures we have 8 issues
    ]
    issues = [make_issue(d, IssueSeverity.LOW) for d in detector_ids]
    result = engine.generate(make_report(issues))
    assert len(result) <= QuestionEngine.MAX_QUESTIONS


def test_max_questions_with_eight_distinct_unknown_mixed():
    """8 issues with known detector_ids produces at most 7 questions."""
    engine = QuestionEngine()
    detector_ids = [
        "output_format", "missing_context", "audience", "scope",
        "input_schema", "action_verb", "examples",
    ]
    # Create 10 issues all with known ids (duplicates will be dropped)
    issues = [make_issue(d, IssueSeverity.HIGH) for d in detector_ids * 2]
    result = engine.generate(make_report(issues))
    assert len(result) <= 7


def test_unknown_detector_id_skipped():
    engine = QuestionEngine()
    issues = [
        make_issue("nonexistent_detector", IssueSeverity.HIGH),
        make_issue("output_format", IssueSeverity.HIGH),
    ]
    result = engine.generate(make_report(issues))
    q_ids = [q.question_id for q in result]
    assert "q_output_format" in q_ids
    assert len(result) == 1
