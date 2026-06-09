from promptforge.analyzer.detectors.action_verb import detect
from promptforge.analyzer.models import IssueSeverity


def test_fires_on_help():
    issues = detect("Help me write a function that sorts a list")
    assert len(issues) == 1
    assert issues[0].detector_id == "action_verb"
    assert issues[0].severity == IssueSeverity.MEDIUM
    assert issues[0].fragment == "help"


def test_fires_on_please_fix():
    issues = detect("Please fix the bug in the authentication module")
    assert len(issues) == 1
    assert issues[0].fragment == "fix"


def test_no_fire_on_strong_verb():
    issues = detect("Write a Python function that implements binary search")
    assert issues == []


def test_no_fire_on_generate():
    issues = detect("Generate a detailed report of all API endpoints")
    assert issues == []


def test_fires_on_improve():
    issues = detect("Improve this code so it runs faster")
    assert len(issues) == 1
    assert issues[0].fragment == "improve"


def test_fires_on_make():
    issues = detect("Make the code more readable and maintainable")
    assert len(issues) == 1
    assert issues[0].fragment == "make"
