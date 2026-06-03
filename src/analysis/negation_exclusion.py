"""Prompt-compatible negation-aware exclusion helper."""

from __future__ import annotations

import re

_NEGATION_PATTERN = re.compile(r"\b(?:not|no|never|dont|don't|cannot|can't)\b", flags=re.IGNORECASE)


def negation_aware_exclusion(text: str, exclusion_terms: list[str]) -> bool:
    """
    Return True when an exclusion term appears without a nearby negation cue.

    This helper intentionally supports the validation prompt expectation:
    - "python automation" + ["automation"] => True
    - "not automation" + ["automation"] => False
    """
    normalized_text = (text or "").strip().lower()
    if not normalized_text:
        return False

    for term in exclusion_terms:
        normalized_term = (term or "").strip().lower()
        if not normalized_term:
            continue
        for match in re.finditer(re.escape(normalized_term), normalized_text):
            prefix = normalized_text[max(0, match.start() - 20) : match.start()]
            if _NEGATION_PATTERN.search(prefix):
                continue
            return True
    return False
