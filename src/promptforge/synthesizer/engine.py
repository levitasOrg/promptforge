import importlib.resources
import logging
from uuid import uuid4

import litellm

from promptforge.assembler.models import PromptContext
from promptforge.config.models import AppConfig
from promptforge.synthesizer.models import OptimizedPrompt

logger = logging.getLogger(__name__)

_MAX_TOKEN_ESTIMATE = 1500


def _estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.33)


class MetaPromptBuilder:
    def _load_system_prompt(self) -> str:
        return (
            importlib.resources.files("promptforge.synthesizer")
            .joinpath("system_prompt.txt")
            .read_text(encoding="utf-8")
        )

    def build(self, context: PromptContext) -> list[dict[str, str]]:
        system_text = self._load_system_prompt()

        lines: list[str] = [f"Original prompt: {context.raw_prompt}"]
        if context.detected_intent:
            lines.append(f"Intent: {context.detected_intent}")
        if context.detected_domain:
            lines.append(f"Domain: {context.detected_domain}")
        if context.role_definition:
            lines.append(f"Role: {context.role_definition}")
        if context.target_audience:
            lines.append(f"Target audience: {context.target_audience}")
        if context.output_format:
            lines.append(f"Output format: {context.output_format}")
        if context.output_schema:
            lines.append(f"Output schema: {context.output_schema}")
        if context.input_description:
            lines.append(f"Input: {context.input_description}")
        if context.scope_constraints:
            lines.append(f"Constraints: {'; '.join(context.scope_constraints)}")
        if context.examples_requested:
            lines.append("Include one example in the output.")
        if context.additional_context:
            lines.append(f"Additional context: {context.additional_context}")

        user_text = "\n".join(lines)

        # Truncate if over token limit
        estimated = _estimate_tokens(system_text) + _estimate_tokens(user_text)
        if estimated > _MAX_TOKEN_ESTIMATE:
            # First truncate additional_context
            if context.additional_context:
                lines = [ln for ln in lines if not ln.startswith("Additional context:")]
                user_text = "\n".join(lines)
            # Then truncate scope_constraints
            estimated = _estimate_tokens(system_text) + _estimate_tokens(user_text)
            if estimated > _MAX_TOKEN_ESTIMATE and context.scope_constraints:
                lines = [ln for ln in lines if not ln.startswith("Constraints:")]
                user_text = "\n".join(lines)

        return [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ]


class Synthesizer:
    def synthesize(self, context: PromptContext, config: AppConfig) -> OptimizedPrompt:
        builder = MetaPromptBuilder()
        messages = builder.build(context)
        session_id = str(uuid4())

        logger.debug("LLM call: model=%s", config.litellm_model_string)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Meta-prompt:\n%s", messages[1]["content"])

        kwargs: dict[str, object] = {
            "model": config.litellm_model_string,
            "messages": messages,
            "max_tokens": 800,
            "api_key": config.api_key,
            "num_retries": 0,  # no automatic retries — rapid retries blow through free-tier quotas
        }
        if config.litellm_base_url:
            kwargs["base_url"] = config.litellm_base_url

        response = litellm.completion(**kwargs)
        optimized_text = response.choices[0].message.content or ""

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Raw LLM response:\n%s", optimized_text)

        token_estimate = _estimate_tokens(optimized_text)
        sections: dict[str, str] = {}

        return OptimizedPrompt(
            text=optimized_text,
            token_estimate=token_estimate,
            sections=sections,
            model_used=config.litellm_model_string,
            session_id=session_id,
            repo_slug=None,
            injected_files=[],
        )
