import pytest
from promptforge.analyzer.detectors.missing_context import detect
from promptforge.analyzer.models import IssueSeverity


def test_fires_on_pronoun_it():
    issues = detect("fix it")
    assert len(issues) == 1
    assert issues[0].detector_id == "missing_context"
    assert issues[0].severity == IssueSeverity.HIGH
    assert issues[0].fragment == "it"


def test_fires_on_them():
    issues = detect("Please handle them carefully")
    assert len(issues) == 1
    assert issues[0].fragment == "them"


def test_no_fire_write_is_first_content():
    issues = detect("Write a function that sorts. It should be fast.")
    assert issues == []


def test_no_fire_mid_prompt_pronoun():
    issues = detect("Refactor this code. They should be cleaner.")
    # "this" is first content token but "code" is a noun in first 10 tokens
    # Actually "this" is in PRONOUNS, but "refactor" comes before it
    assert issues == []


def test_fires_on_they():
    issues = detect("they are not working correctly")
    assert len(issues) == 1
    assert issues[0].fragment == "they"


def test_no_fire_empty_prompt():
    issues = detect("")
    assert issues == []


def test_no_fire_noun_present_with_pronoun():
    issues = detect("this function should be refactored")
    # "this" is PRONOUN, but "function" is a noun (len>=4)
    assert issues == []
