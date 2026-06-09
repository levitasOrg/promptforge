from promptforge.analyzer.models import Issue, IssueSeverity

FORMAT_KEYWORDS = [
    "json", "markdown", "list", "table", "code", "function", "paragraph",
    "bullet", "csv", "yaml", "xml", "plain text", "numbered", "step by step"
]
OUTPUT_SIGNAL_PHRASES = ["output:", "return:", "format:", "respond with", "give me a"]


def detect(raw_prompt: str) -> list[Issue]:
    lower = raw_prompt.lower()
    has_format = any(kw in lower for kw in FORMAT_KEYWORDS)
    has_signal = any(ph in lower for ph in OUTPUT_SIGNAL_PHRASES)
    if not has_format and not has_signal:
        return [Issue(detector_id="output_format", severity=IssueSeverity.HIGH,
                     description="No output format specified.",
                     fragment="(none)")]
    return []
