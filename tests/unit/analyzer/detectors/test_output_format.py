from promptforge.analyzer.detectors.output_format import detect
from promptforge.analyzer.models import IssueSeverity


def test_fires_when_no_format():
    issues = detect("Explain how photosynthesis works")
    assert len(issues) == 1
    assert issues[0].detector_id == "output_format"
    assert issues[0].severity == IssueSeverity.HIGH
    assert issues[0].fragment == "(none)"


def test_no_fire_with_json_keyword():
    issues = detect("Return the results as JSON with keys name and value")
    assert issues == []


def test_no_fire_with_markdown():
    issues = detect("Write a markdown document explaining the API endpoints")
    assert issues == []


def test_no_fire_with_output_signal():
    issues = detect("Respond with a summary of the document")
    assert issues == []


def test_no_fire_with_list():
    issues = detect("Give me a list of the top 10 Python frameworks")
    assert issues == []


def test_no_fire_with_step_by_step():
    issues = detect("Explain step by step how to set up a virtualenv")
    assert issues == []
