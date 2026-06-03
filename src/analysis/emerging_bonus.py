"""R11 emerging opportunity bonus and negation-aware exclusion helpers."""

from __future__ import annotations

import re
from typing import Any

_NEGATION_PATTERN = re.compile(r"\b(?:not|no|never|dont|don't|cannot|can't)\b", flags=re.IGNORECASE)


def compute_emerging_opportunity_bonus(keyword_score_row: Any, rsv_row: Any) -> float:
    """Apply a bounded bonus only to high-integrity emerging opportunities."""
    if rsv_row is None:
        return 0.0
    if bool(getattr(keyword_score_row, "ghost_market_flag", False)):
        return 0.0

    relevance = float(getattr(rsv_row, "result_set_relevance_score", 0.0) or 0.0)
    if relevance < 0.70:
        return 0.0

    if str(getattr(keyword_score_row, "autocomplete_status", "")).strip().lower() != "emerging":
        return 0.0
    if bool(getattr(rsv_row, "category_contamination_flag", False)):
        return 0.0
    return 3.0


def negation_aware_exclusion(text: str, exclusion_terms: list[str]) -> bool:
    """Return True when an exclusion term appears without nearby negation."""
    normalized_text = str(text or "").lower()
    if not normalized_text:
        return False

    for term in exclusion_terms:
        normalized_term = str(term or "").strip().lower()
        if not normalized_term:
            continue
        for match in re.finditer(re.escape(normalized_term), normalized_text):
            prefix = normalized_text[max(0, match.start() - 30) : match.start()]
            if _NEGATION_PATTERN.search(prefix):
                continue
            return True
    return False
