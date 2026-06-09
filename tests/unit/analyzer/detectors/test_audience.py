from promptforge.analyzer.detectors.audience import detect
from promptforge.analyzer.models import IssueSeverity


def test_fires_when_no_audience_and_long_prompt():
    prompt = "Write a detailed explanation of how neural networks work with backpropagation and gradient descent algorithms and how they are trained on large datasets."
    issues = detect(prompt)
    assert len(issues) == 1
    assert issues[0].detector_id == "audience"
    assert issues[0].severity == IssueSeverity.MEDIUM


def test_no_fire_with_for_a_marker():
    prompt = "Write a detailed explanation of how neural networks work for a beginner audience learning ML."
    issues = detect(prompt)
    assert issues == []


def test_no_fire_with_you_are_marker():
    prompt = "You are a Python expert. Explain decorators in detail including use cases and best practices."
    issues = detect(prompt)
    assert issues == []


def test_no_fire_short_prompt():
    prompt = "Explain recursion"
    issues = detect(prompt)
    assert issues == []


def test_no_fire_with_technical_level():
    prompt = "Write a detailed explanation of dependency injection for a senior developer audience."
    issues = detect(prompt)
    assert issues == []


def test_fires_fragment_is_first_word():
    prompt = "Describe the architecture of a distributed system including load balancing, data replication, consensus algorithms, and fault tolerance patterns used in modern cloud infrastructure deployments."
    issues = detect(prompt)
    assert len(issues) == 1
    assert issues[0].fragment == "Describe"
