"""R10 keyword integrity badge rendering helpers."""

from __future__ import annotations

from typing import Any

BADGE_TYPES: dict[str, dict[str, Any]] = {
    "STRONG_GO": {"label": "Strong Go", "color": "green", "icon": "arrow-up"},
    "CONDITIONAL_GO": {"label": "Conditional Go", "color": "yellow", "icon": "check"},
    "MONITOR": {"label": "Monitor", "color": "orange", "icon": "eye"},
    "CAUTION": {"label": "Caution", "color": "red", "icon": "warning"},
    "GHOST_MARKET": {"label": "Ghost Market", "color": "dark", "icon": "ghost"},
    "EMERGING": {"label": "Emerging", "color": "blue", "icon": "rocket"},
    "DATA_INTEGRITY_GAP": {"label": "Data Gap", "color": "gray", "icon": "question"},
}


def render_keyword_integrity_badge(keyword_score_row: Any) -> dict[str, Any]:
    """Return badge metadata for a keyword score-like row."""
    if keyword_score_row is None:
        return {**BADGE_TYPES["DATA_INTEGRITY_GAP"], "type": "DATA_INTEGRITY_GAP"}

    if bool(getattr(keyword_score_row, "ghost_market_flag", False)):
        badge = {**BADGE_TYPES["GHOST_MARKET"], "type": "GHOST_MARKET"}
    else:
        tag = getattr(keyword_score_row, "tag", None)
        if isinstance(tag, str) and tag in BADGE_TYPES:
            badge = {**BADGE_TYPES[tag], "type": tag}
        else:
            badge = {**BADGE_TYPES["DATA_INTEGRITY_GAP"], "type": "DATA_INTEGRITY_GAP"}

    if getattr(keyword_score_row, "autocomplete_status", None) == "emerging":
        badge["emerging_overlay"] = True
    return badge
