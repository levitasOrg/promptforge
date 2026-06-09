import copy

from promptforge.analyzer.models import AnalysisReport, IssueSeverity
from promptforge.questions.models import ClarifyingQuestion
from promptforge.questions.templates import TEMPLATES


class QuestionEngine:
    MAX_QUESTIONS = 7

    def generate(self, report: AnalysisReport) -> list[ClarifyingQuestion]:
        # Sort issues by severity: HIGH → MEDIUM → LOW
        severity_order = {IssueSeverity.HIGH: 0, IssueSeverity.MEDIUM: 1, IssueSeverity.LOW: 2}
        sorted_issues = sorted(report.issues, key=lambda i: severity_order[i.severity])

        questions: list[ClarifyingQuestion] = []
        seen_ids: set[str] = set()

        for issue in sorted_issues:
            template = TEMPLATES.get(issue.detector_id)
            if template is None:
                continue

            # Deduplicate by question_id
            if template.question_id in seen_ids:
                continue
            seen_ids.add(template.question_id)

            # Fill {fragment} placeholder if present
            q = copy.copy(template)
            if "{fragment}" in q.question_text:
                q = ClarifyingQuestion(
                    question_id=q.question_id,
                    question_text=q.question_text.replace("{fragment}", issue.fragment),
                    source_issue_ids=q.source_issue_ids,
                    is_required=q.is_required,
                )

            questions.append(q)
            if len(questions) >= self.MAX_QUESTIONS:
                break

        return questions
