from promptforge.questions.models import ClarifyingQuestion

TEMPLATES: dict[str, ClarifyingQuestion] = {
    "output_format": ClarifyingQuestion(
        question_id="q_output_format",
        question_text="What format should the output be in? (e.g. JSON, markdown list, code function, plain paragraph)",
        source_issue_ids=["output_format"],
        is_required=True,
    ),
    "missing_context": ClarifyingQuestion(
        question_id="q_missing_context",
        question_text="'{fragment}' — what specific thing does this refer to? Add 1-2 sentences of context.",
        source_issue_ids=["missing_context"],
        is_required=True,
    ),
    "audience": ClarifyingQuestion(
        question_id="q_audience",
        question_text="Who is the target audience or reader? (e.g. junior developer, non-technical manager, general public)",
        source_issue_ids=["audience"],
        is_required=False,
    ),
    "scope": ClarifyingQuestion(
        question_id="q_scope",
        question_text="The scope seems open-ended. What are the specific limits? (e.g. max length, specific aspect only, particular version)",
        source_issue_ids=["scope"],
        is_required=False,
    ),
    "input_schema": ClarifyingQuestion(
        question_id="q_input_schema",
        question_text="What exactly will the agent receive as input? Describe the format, structure, or provide a sample.",
        source_issue_ids=["input_schema"],
        is_required=True,
    ),
    "action_verb": ClarifyingQuestion(
        question_id="q_action_verb",
        question_text="'{fragment}' is vague. What specifically should happen? (e.g. generate new, refactor existing, extract from, validate against)",
        source_issue_ids=["action_verb"],
        is_required=False,
    ),
    "examples": ClarifyingQuestion(
        question_id="q_examples",
        question_text="Should the optimized prompt include an example of the expected output? If yes, paste one here.",
        source_issue_ids=["examples"],
        is_required=False,
    ),
}
