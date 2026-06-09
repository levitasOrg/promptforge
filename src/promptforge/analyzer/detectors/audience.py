from promptforge.analyzer.models import Issue, IssueSeverity

AUDIENCE_MARKERS = ["for a", "as a", "you are", "act as", "role:", "audience:"]
TECHNICAL_LEVEL_SIGNALS = ["beginner", "expert", "junior", "senior", "non-technical"]


def detect(raw_prompt: str) -> list[Issue]:
    lower = raw_prompt.lower()
    word_count = len(raw_prompt.split())
    has_marker = any(m in lower for m in AUDIENCE_MARKERS)
    has_level = any(s in lower for s in TECHNICAL_LEVEL_SIGNALS)
    if not has_marker and not has_level and word_count > 20:
        first_word = raw_prompt.split()[0] if raw_prompt.split() else ""
        return [Issue(detector_id="audience", severity=IssueSeverity.MEDIUM,
                     description="No audience or technical level specified.",
                     fragment=first_word)]
    return []
