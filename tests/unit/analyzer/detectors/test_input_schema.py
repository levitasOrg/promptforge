from promptforge.analyzer.detectors.input_schema import detect
from promptforge.analyzer.models import IssueSeverity


def test_fires_on_analyze_without_input():
    issues = detect("Analyze the performance characteristics of this algorithm")
    assert len(issues) == 1
    assert issues[0].detector_id == "input_schema"
    assert issues[0].severity == IssueSeverity.HIGH
    assert issues[0].fragment == "analyze"


def test_no_fire_analyze_with_input_marker():
    issues = detect("Analyze the following code:\n```\ndef foo(): pass\n```")
    assert issues == []


def test_no_fire_analyze_with_here_is():
    issues = detect("Analyze the code. Here is the function: def foo(): pass")
    assert issues == []


def test_no_fire_no_input_verb():
    issues = detect("Write a poem about the ocean")
    assert issues == []


def test_fires_on_summarize():
    issues = detect("Summarize the main points of the article")
    assert len(issues) == 1
    assert issues[0].fragment == "summarize"


def test_no_fire_with_given_marker():
    issues = detect("Review the implementation. Given: a REST API with rate limiting")
    assert issues == []
