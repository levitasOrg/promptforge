from promptforge.analyzer.models import AnalysisReport, Issue, IssueSeverity

EXAMPLE_MARKERS = ["example:", "e.g.", "for instance", "such as", "like this:", "input:"]


def detect(raw_prompt: str, analysis_report: AnalysisReport) -> list[Issue]:
    word_count = len(raw_prompt.split())
    has_example = any(m in raw_prompt.lower() for m in EXAMPLE_MARKERS)
    if word_count > 50 and not has_example and analysis_report.has_output_format_issue:
        return [Issue(detector_id="examples", severity=IssueSeverity.LOW,
                     description="Complex prompt with unclear output would benefit from an example.",
                     fragment="(no example)")]
    return []
