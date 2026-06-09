from promptforge.assembler.models import PromptContext
from promptforge.synthesizer.engine import MetaPromptBuilder, _estimate_tokens


def make_context(**kwargs):
    defaults = dict(
        raw_prompt="help me",
        detected_intent="general task",
        detected_domain="general",
        role_definition=None,
        target_audience=None,
        output_format=None,
        output_schema=None,
        input_description=None,
        scope_constraints=[],
        examples_requested=False,
        additional_context=None,
    )
    defaults.update(kwargs)
    return PromptContext(**defaults)

def test_build_returns_system_and_user_messages():
    builder = MetaPromptBuilder()
    msgs = builder.build(make_context())
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"

def test_null_fields_omitted_from_user_message():
    builder = MetaPromptBuilder()
    msgs = builder.build(make_context(target_audience=None, output_format=None))
    user_text = msgs[1]["content"]
    assert "Target audience:" not in user_text
    assert "Output format:" not in user_text

def test_non_null_fields_included():
    builder = MetaPromptBuilder()
    msgs = builder.build(make_context(output_format="JSON", target_audience="junior developer"))
    user_text = msgs[1]["content"]
    assert "Output format: JSON" in user_text
    assert "Target audience: junior developer" in user_text

def test_system_prompt_loaded():
    builder = MetaPromptBuilder()
    msgs = builder.build(make_context())
    assert len(msgs[0]["content"]) > 50  # system prompt is non-trivial

def test_estimate_tokens():
    # 3 words → ~4 tokens
    assert _estimate_tokens("one two three") == int(3 * 1.33)
