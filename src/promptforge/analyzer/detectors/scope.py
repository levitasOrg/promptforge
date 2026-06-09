from promptforge.analyzer.models import Issue, IssueSeverity

UNBOUNDED_SCOPE_WORDS = [
    "everything", "all of", "complete", "entire", "fully",
    "comprehensive", "thoroughly", "in detail", "in depth"
]
QUALIFYING_LIMITERS = ["related to", "about", "regarding", "for", "on the topic of"]


def detect(raw_prompt: str) -> list[Issue]:
    lower = raw_prompt.lower()
    tokens = lower.split()
    issues = []
    for scope_word in UNBOUNDED_SCOPE_WORDS:
        if scope_word not in lower:
            continue
        # find position of the scope word
        scope_tokens = scope_word.split()
        scope_len = len(scope_tokens)
        for i in range(len(tokens) - scope_len + 1):
            if tokens[i:i + scope_len] == scope_tokens:
                # check within 5 tokens after
                window_start = i + scope_len
                window_end = window_start + 5
                window_text = " ".join(tokens[window_start:window_end])
                has_qualifier = any(lim in window_text for lim in QUALIFYING_LIMITERS)
                if not has_qualifier:
                    issues.append(Issue(detector_id="scope", severity=IssueSeverity.MEDIUM,
                                       description=f"Unbounded scope word '{scope_word}' found without qualifier.",
                                       fragment=scope_word))
                break  # only report once per scope word
    return issues
