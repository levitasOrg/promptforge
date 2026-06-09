from promptforge.analyzer.models import Issue, IssueSeverity

WEAK_VERBS = [
    "help", "do", "make", "handle", "deal with", "work on",
    "look at", "think about", "figure out", "fix", "improve"
]


def detect(raw_prompt: str) -> list[Issue]:
    lower = raw_prompt.lower().strip()
    # Extract first imperative verb: first word or word after "please "
    if lower.startswith("please "):
        first_verb = lower[7:].split()[0] if lower[7:].split() else ""
    else:
        first_verb = lower.split()[0] if lower.split() else ""
    # Strip punctuation
    first_verb = first_verb.strip(".,!?;:")
    # Check multi-word weak verbs first
    for weak in WEAK_VERBS:
        if " " in weak:
            if lower.startswith(weak) or lower.startswith("please " + weak):
                return [Issue(detector_id="action_verb", severity=IssueSeverity.MEDIUM,
                             description=f"Weak action verb '{weak}' found.",
                             fragment=weak)]
    if first_verb in WEAK_VERBS:
        return [Issue(detector_id="action_verb", severity=IssueSeverity.MEDIUM,
                     description=f"Weak action verb '{first_verb}' found.",
                     fragment=first_verb)]
    return []
