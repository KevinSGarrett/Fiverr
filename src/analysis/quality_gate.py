"""R11 first-recommendation quality gate."""

from __future__ import annotations

from typing import Any


def first_recommendation_quality_gate(
    keyword_score_row: Any,
    rsv_row: Any,
    db: Any | None = None,
) -> dict[str, Any]:
    """Evaluate 5 mandatory checks before a first recommendation is emitted."""
    _ = db
    failing: list[str] = []
    if rsv_row is None:
        failing.append("missing_rsv")
    if bool(getattr(keyword_score_row, "ghost_market_flag", False)):
        failing.append("ghost_market")

    rsv_score = float(getattr(rsv_row, "result_set_relevance_score", 0.0) or 0.0) if rsv_row else 0.0
    if rsv_score < 0.70:
        failing.append(f"relevance_below_threshold_{rsv_score:.2f}")

    llm_used = getattr(keyword_score_row, "llm_inputs_used", None)
    llm_validated = getattr(keyword_score_row, "llm_validated", None)
    if llm_validated is False:
        failing.append("llm_not_validated")
    elif llm_validated is None and llm_used is False:
        failing.append("llm_not_validated")

    strictness = getattr(rsv_row, "search_strictness_used", None) if rsv_row else None
    if strictness == "NONE":
        failing.append("unconstrained_search")

    return {
        "passed": len(failing) == 0,
        "failing_checks": failing,
    }
