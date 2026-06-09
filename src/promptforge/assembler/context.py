from promptforge.analyzer.models import AnalysisReport
from promptforge.assembler.models import PromptContext
from promptforge.questions.models import UserAnswer

# Map question_id → PromptContext field name
_QUESTION_FIELD_MAP = {
    "q_output_format": "output_format",
    "q_audience": "target_audience",
    "q_input_schema": "input_description",
    "q_scope": None,  # goes to scope_constraints list
    "q_missing_context": "additional_context",
    "q_action_verb": "additional_context",
    "q_examples": None,  # sets examples_requested=True if non-empty
}

class ContextAssembler:
    def assemble(
        self,
        raw_prompt: str,
        report: AnalysisReport,
        answers: list[UserAnswer],
    ) -> PromptContext:
        answer_map = {a.question_id: a for a in answers if not a.skipped}

        output_format = answer_map.get("q_output_format")
        target_audience = answer_map.get("q_audience")
        input_description = answer_map.get("q_input_schema")
        scope_answer = answer_map.get("q_scope")
        missing_ctx = answer_map.get("q_missing_context")
        action_answer = answer_map.get("q_action_verb")
        examples_answer = answer_map.get("q_examples")

        # Build additional_context from missing_context + action_verb answers
        additional_parts = []
        if missing_ctx:
            additional_parts.append(missing_ctx.answer_text)
        if action_answer:
            additional_parts.append(action_answer.answer_text)
        additional_context = "; ".join(additional_parts) if additional_parts else None

        scope_constraints: list[str] = []
        if scope_answer:
            scope_constraints = [scope_answer.answer_text]

        return PromptContext(
            raw_prompt=raw_prompt,
            detected_intent=report.detected_intent,
            detected_domain=report.detected_domain,
            role_definition=None,  # not asked in current question set
            target_audience=target_audience.answer_text if target_audience else None,
            output_format=output_format.answer_text if output_format else None,
            output_schema=None,
            input_description=input_description.answer_text if input_description else None,
            scope_constraints=scope_constraints,
            examples_requested=bool(examples_answer and examples_answer.answer_text.strip()),
            additional_context=additional_context,
        )
