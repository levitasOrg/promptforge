from promptforge.analyzer.models import Issue, IssueSeverity

INPUT_VERBS = [
    "analyze", "review", "process", "evaluate", "check", "read",
    "summarize", "translate", "convert", "transform"
]
INPUT_DESCRIPTION_MARKERS = ["input:", "given:", "here is", "```"]


def detect(raw_prompt: str) -> list[Issue]:
    lower = raw_prompt.lower()
    matched_verb = None
    for verb in INPUT_VERBS:
        if verb in lower.split() or lower.startswith(verb):
            matched_verb = verb
            break
        # also check as substring with word boundary
        tokens = lower.split()
        if verb in tokens:
            matched_verb = verb
            break
    if matched_verb is None:
        # check as substring more carefully: verb as whole word
        tokens = lower.split()
        # strip punctuation from tokens for matching
        cleaned = [t.strip(".,!?;:") for t in tokens]
        for verb in INPUT_VERBS:
            if verb in cleaned:
                matched_verb = verb
                break
    if matched_verb is not None:
        has_input_desc = any(m in lower for m in INPUT_DESCRIPTION_MARKERS)
        if not has_input_desc:
            return [Issue(detector_id="input_schema", severity=IssueSeverity.HIGH,
                         description=f"Input verb '{matched_verb}' found but no input description provided.",
                         fragment=matched_verb)]
    return []
