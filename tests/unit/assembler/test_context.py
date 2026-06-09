from promptforge.analyzer.models import AnalysisReport
from promptforge.assembler.context import ContextAssembler
from promptforge.questions.models import UserAnswer


def make_report():
    return AnalysisReport(
        raw_prompt="fix it",
        issues=[],
        detected_intent="transform existing content",
        detected_domain="general",
    )

def make_answer(question_id, text, skipped=False):
    return UserAnswer(question_id=question_id, answer_text=text, skipped=skipped)

def test_all_fields_populated():
    assembler = ContextAssembler()
    answers = [
        make_answer("q_output_format", "JSON"),
        make_answer("q_audience", "junior developer"),
        make_answer("q_input_schema", "a Python dict"),
        make_answer("q_scope", "max 100 lines"),
        make_answer("q_examples", "yes, show one"),
    ]
    ctx = assembler.assemble("fix it", make_report(), answers)
    assert ctx.output_format == "JSON"
    assert ctx.target_audience == "junior developer"
    assert ctx.input_description == "a Python dict"
    assert ctx.scope_constraints == ["max 100 lines"]
    assert ctx.examples_requested is True

def test_skipped_answers_produce_none():
    assembler = ContextAssembler()
    answers = [
        make_answer("q_output_format", "", skipped=True),
        make_answer("q_audience", "", skipped=True),
    ]
    ctx = assembler.assemble("fix it", make_report(), answers)
    assert ctx.output_format is None
    assert ctx.target_audience is None

def test_empty_answers_returns_null_fields():
    assembler = ContextAssembler()
    ctx = assembler.assemble("fix it", make_report(), [])
    assert ctx.output_format is None
    assert ctx.target_audience is None
    assert ctx.scope_constraints == []
    assert ctx.examples_requested is False
    assert ctx.additional_context is None

def test_missing_context_answer_goes_to_additional_context():
    assembler = ContextAssembler()
    answers = [make_answer("q_missing_context", "the auth service")]
    ctx = assembler.assemble("fix it", make_report(), answers)
    assert ctx.additional_context == "the auth service"

def test_detected_intent_and_domain_preserved():
    assembler = ContextAssembler()
    ctx = assembler.assemble("fix it", make_report(), [])
    assert ctx.detected_intent == "transform existing content"
    assert ctx.detected_domain == "general"
