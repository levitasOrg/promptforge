import logging
from unittest.mock import patch

from promptforge.analyzer.engine import Analyzer


def make_vague_prompt():
    return "fix it"  # fires missing_context, action_verb, output_format, input_schema (maybe)

def test_analyze_returns_analysis_report():
    analyzer = Analyzer()
    report = analyzer.analyze("fix it")
    assert report.raw_prompt == "fix it"
    assert isinstance(report.issues, list)
    assert report.detected_intent != ""
    assert report.detected_domain != ""

def test_analyze_detects_multiple_issues():
    analyzer = Analyzer()
    report = analyzer.analyze("fix it")
    assert len(report.issues) >= 1

def test_has_output_format_issue_set_correctly():
    analyzer = Analyzer()
    # A clear prompt with no format keywords should set has_output_format_issue=True
    report = analyzer.analyze("Write a summary of the document")
    assert report.has_output_format_issue is True

def test_issue_count_by_severity_populated():
    analyzer = Analyzer()
    report = analyzer.analyze("fix it")
    assert "high" in report.issue_count_by_severity
    assert "medium" in report.issue_count_by_severity
    assert "low" in report.issue_count_by_severity

def test_broken_detector_does_not_crash_pipeline(caplog):
    analyzer = Analyzer()
    # Patch one detector to raise
    with patch("promptforge.analyzer.detectors.audience.detect", side_effect=RuntimeError("boom")), caplog.at_level(logging.WARNING):
        report = analyzer.analyze("Write a detailed guide to Python programming best practices for web developers.")
    assert report is not None
    assert any("audience" in r.message for r in caplog.records)

def test_intent_detection_generate():
    analyzer = Analyzer()
    report = analyzer.analyze("Write a blog post about climate change")
    assert report.detected_intent == "generate content"

def test_domain_detection_software():
    analyzer = Analyzer()
    report = analyzer.analyze("Write a Python function to sort a list")
    assert report.detected_domain == "software engineering"

def test_empty_prompt_does_not_crash():
    analyzer = Analyzer()
    report = analyzer.analyze("")
    assert report is not None
