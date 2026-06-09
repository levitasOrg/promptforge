import logging
import re

from promptforge.analyzer.detectors import (
    action_verb,
    audience,
    examples,
    input_schema,
    missing_context,
    output_format,
    scope,
)
from promptforge.analyzer.models import AnalysisReport, Issue, IssueSeverity

logger = logging.getLogger(__name__)

# Intent detection — first match wins
_INTENT_PATTERNS = [
    (re.compile(r"\b(generate|write|create|draft)\b", re.I), "generate content"),
    (re.compile(r"\b(summarize|recap|tldr|condense)\b", re.I), "summarize"),
    (re.compile(r"\b(analyze|analyse|review|evaluate|assess)\b", re.I), "analyze"),
    (re.compile(r"\b(refactor|improve|fix|debug|optimize)\b", re.I), "transform existing content"),
    (re.compile(r"\b(explain|describe|define|what is)\b", re.I), "explain concept"),
    (re.compile(r"\b(compare|contrast|difference between)\b", re.I), "compare options"),
    (re.compile(r"\b(translate|convert)\b", re.I), "transform format"),
]

# Domain detection — first match wins
_DOMAIN_PATTERNS = [
    (re.compile(r"\b(code|function|class|api|database|sql|python|java|javascript)\b", re.I), "software engineering"),
    (re.compile(r"\b(write|essay|blog|article|story|copy|marketing)\b", re.I), "writing"),
    (re.compile(r"\b(data|dataset|csv|analysis|chart|statistics)\b", re.I), "data analysis"),
    (re.compile(r"\b(email|message|slack|communication)\b", re.I), "communication"),
    (re.compile(r"\b(legal|contract|compliance|policy)\b", re.I), "legal/compliance"),
]


def _detect_intent(raw_prompt: str) -> str:
    for pattern, intent in _INTENT_PATTERNS:
        if pattern.search(raw_prompt):
            return intent
    return "general task"


def _detect_domain(raw_prompt: str) -> str:
    for pattern, domain in _DOMAIN_PATTERNS:
        if pattern.search(raw_prompt):
            return domain
    return "general"


class Analyzer:
    def analyze(self, raw_prompt: str) -> AnalysisReport:
        all_issues: list[Issue] = []

        # Run pure detectors (catch exceptions per detector)
        pure_detectors = [
            ("missing_context", missing_context.detect),
            ("audience", audience.detect),
            ("output_format", output_format.detect),
            ("scope", scope.detect),
            ("input_schema", input_schema.detect),
            ("action_verb", action_verb.detect),
        ]
        has_output_format_issue = False
        for detector_id, fn in pure_detectors:
            try:
                issues = fn(raw_prompt)
                if detector_id == "output_format" and issues:
                    has_output_format_issue = True
                all_issues.extend(issues)
            except Exception as e:
                logger.warning("Detector %s failed: %s. Skipping.", detector_id, e)

        # Run ExampleDetector last with partial report
        partial_report = AnalysisReport(
            raw_prompt=raw_prompt,
            issues=all_issues,
            detected_intent=_detect_intent(raw_prompt),
            detected_domain=_detect_domain(raw_prompt),
            has_output_format_issue=has_output_format_issue,
        )
        try:
            example_issues = examples.detect(raw_prompt, partial_report)
            all_issues.extend(example_issues)
        except Exception as e:
            logger.warning("Detector examples failed: %s. Skipping.", e)

        count_by_severity = {s.value: 0 for s in IssueSeverity}
        for issue in all_issues:
            count_by_severity[issue.severity.value] += 1

        return AnalysisReport(
            raw_prompt=raw_prompt,
            issues=all_issues,
            detected_intent=_detect_intent(raw_prompt),
            detected_domain=_detect_domain(raw_prompt),
            issue_count_by_severity=count_by_severity,
            has_output_format_issue=has_output_format_issue,
        )
