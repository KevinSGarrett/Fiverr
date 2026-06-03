"""R11 monitoring functions for stealth-sponsored, relevance-cliff, and filter health."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

FILTER_HEALTH_NONE_RATE_THRESHOLD = 0.10

MONTHLY_KPI_THRESHOLDS: dict[str, float] = {
    "ghost_rate_max": 0.08,
    "avg_relevance_min": 0.78,
    "fallback_rate_max": 0.10,
    "llm_validation_rate_min": 0.03,
    "contamination_rate_max": 0.12,
    "recommendation_pass_rate_min": 0.35,
    "stage8_completion_rate_min": 0.95,
    "data_integrity_gap_rate_max": 0.05,
}


def get_monthly_kpi_thresholds() -> dict[str, float]:
    """Return a copy of R11 health KPI thresholds for dashboards and audits."""
    return dict(MONTHLY_KPI_THRESHOLDS)


def detect_stealth_sponsored(keyword_score_row: Any, competition_rows: list[Any]) -> dict[str, Any]:
    """Detect sponsored competition rows that escaped exclusion."""
    _ = keyword_score_row
    stealth_count = sum(
        1
        for row in competition_rows
        if bool(getattr(row, "is_sponsored", False)) and not bool(getattr(row, "sponsored_excluded", False))
    )
    if stealth_count == 0:
        severity = "none"
    elif stealth_count <= 2:
        severity = "info"
    elif stealth_count <= 5:
        severity = "warning"
    else:
        severity = "critical"
    return {
        "detected": stealth_count > 0,
        "count": stealth_count,
        "severity": severity,
    }


def detect_relevance_cliff(current_score: float, prev_score: float, cliff_threshold: float = 15.0) -> dict[str, Any]:
    """Detect sudden relevance score drops based on percentage-point delta."""
    safe_prev = max(float(prev_score), 1.0)
    drop = float(prev_score) - float(current_score)
    return {
        "detected": drop >= float(cliff_threshold),
        "drop_pct": round((drop / safe_prev) * 100.0, 1),
    }


def check_category_filter_health(niche_id: int, run_id: str, db: Any) -> dict[str, Any]:
    """Check fallback strictness usage for one run."""
    _ = niche_id
    from src.models.result_set_validation import ResultSetValidation

    total = db.execute(select(func.count()).where(ResultSetValidation.run_id == run_id)).scalar() or 0
    none_count = (
        db.execute(
            select(func.count()).where(
                ResultSetValidation.run_id == run_id,
                ResultSetValidation.search_strictness_used == "NONE",
            )
        ).scalar()
        or 0
    )
    fallback_rate = (float(none_count) / float(total)) if total else 0.0
    return {
        "healthy": fallback_rate < FILTER_HEALTH_NONE_RATE_THRESHOLD,
        "fallback_rate": round(fallback_rate, 3),
        "none_count": int(none_count),
        "total": int(total),
    }
