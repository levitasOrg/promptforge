from promptforge.analyzer.models import Issue, IssueSeverity

SKIP_TOKENS = {"please", "can", "could", "would", "i", "we", "you", "ll"}
# Weak imperative verbs at prompt start — skip to reach the implicit subject
WEAK_IMPERATIVE_VERBS = {"fix", "help", "do", "make", "handle", "deal", "work", "look", "think", "figure", "improve"}
PRONOUNS = {"it", "they", "this", "that", "these", "those", "them"}
# Suffixes that indicate verbs/adverbs rather than nouns
_VERB_SUFFIXES = ("ing", "ed", "ly")


_ALL_NON_NOUNS = SKIP_TOKENS | WEAK_IMPERATIVE_VERBS | PRONOUNS


def _is_noun_like(tok: str) -> bool:
    return (
        len(tok) >= 4
        and tok.isalpha()
        and tok not in _ALL_NON_NOUNS
        and not any(tok.endswith(s) for s in _VERB_SUFFIXES)
    )


def detect(raw_prompt: str) -> list[Issue]:
    tokens = raw_prompt.lower().split()
    all_skip = SKIP_TOKENS | WEAK_IMPERATIVE_VERBS
    first_content_token = None
    for tok in tokens[:10]:
        if tok in all_skip:
            continue
        if len(tok) <= 2 and not tok.isalpha():
            continue
        first_content_token = tok
        break
    if first_content_token and first_content_token in PRONOUNS:
        noun_found = any(_is_noun_like(t) for t in tokens[:10])
        if not noun_found:
            return [
                Issue(
                    detector_id="missing_context",
                    severity=IssueSeverity.HIGH,
                    description="Prompt opens with a pronoun with no prior referent.",
                    fragment=first_content_token,
                )
            ]
    return []
