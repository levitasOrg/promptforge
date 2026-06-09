from promptforge.analyzer.detectors.scope import detect
from promptforge.analyzer.models import IssueSeverity


def test_fires_on_everything_without_qualifier():
    issues = detect("Tell me everything, I need all of it now")
    assert len(issues) >= 1
    assert any(i.detector_id == "scope" for i in issues)


def test_no_fire_everything_with_about():
    issues = detect("Tell me everything about neural networks in two paragraphs")
    assert issues == []


def test_fires_on_comprehensive():
    issues = detect("Write a comprehensive guide to Python programming")
    assert len(issues) == 1
    assert issues[0].fragment == "comprehensive"


def test_no_fire_comprehensive_with_for():
    issues = detect("Write a comprehensive guide for beginners learning Python")
    assert issues == []


def test_no_fire_no_scope_words():
    issues = detect("Write a short function to sort a list")
    assert issues == []


def test_fires_on_in_detail():
    issues = detect("Explain memory management in detail")
    assert len(issues) == 1
    assert issues[0].fragment == "in detail"


def test_no_fire_entire_with_regarding():
    issues = detect("Rewrite the entire section regarding authentication flows")
    assert issues == []
