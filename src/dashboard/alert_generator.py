"""R10 relevance alert catalog and run-level generation."""

from __future__ import annotations

from typing import Any

from sqlalchemy import distinct, func, select

ALERT_TYPES: dict[str, dict[str, str]] = {
    "ghost_market_detected": {
        "severity": "critical",
        "message": 'Ghost market detected: {niche} keyword "{keyword}" flagged as irrelevant market.',
        "action": "Review niche definition; consider dropping keyword.",
    },
    "relevance_deduction_applied": {
        "severity": "warning",
        "message": "Relevance deduction applied: RSV={rsv:.2f} below threshold.",
        "action": "Inspect result set for contamination.",
    },
    "llm_validation_triggered": {
        "severity": "info",
        "message": "LLM Stage 7.5 triggered for {count} ambiguous keywords.",
        "action": "Review LLM verdicts in analysis tab.",
    },
    "external_signal_partial": {
        "severity": "warning",
        "message": "External signals partial: {n_present}/4 signal families have data.",
        "action": "Run live ScrapFly collection to populate missing signal families.",
    },
    "contamination_flagged": {
        "severity": "warning",
        "message": "Category contamination flagged: {n} keywords show off-niche results.",
        "action": "Review category filter and niche config.",
    },
    "data_integrity_gap": {
        "severity": "info",
        "message": "Data integrity gap: {n} keywords missing RSV data.",
        "action": "Re-run Stage 3.5 validation for affected keywords.",
    },
}

_SEVERITY_ORDER = ["critical", "warning", "info"]


def _safe_scalar(db: Any, stmt: Any) -> int:
    try:
        value = db.execute(stmt).scalar()
    except Exception:
        return 0
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _append_alert(
    alerts: list[dict[str, Any]],
    *,
    alert_type: str,
    count: int,
    **fields: Any,
) -> None:
    if count <= 0:
        return
    alert_meta = ALERT_TYPES.get(alert_type, {})
    alerts.append(
        {
            "type": alert_type,
            "count": int(count),
            "severity": str(alert_meta.get("severity", "info")),
            "action": alert_meta.get("action"),
            **fields,
        }
    )


def generate_relevance_alerts_for_run(run_id: str, db: Any) -> list[dict[str, Any]]:
    """Generate 6 alert families for a completed run (sorted by severity)."""
    if db is None:
        return []

    from src.models.external_signal import ExternalSignal
    from src.models.keyword_score import KeywordScore
    from src.models.result_set_validation import ResultSetValidation
    from src.models.search_result import SearchResult

    alerts: list[dict[str, Any]] = []

    ghost_count = _safe_scalar(
        db,
        select(func.count()).where(
            ResultSetValidation.run_id == run_id,
            ResultSetValidation.ghost_market_flag.is_(True),
        ),
    )
    _append_alert(alerts, alert_type="ghost_market_detected", count=ghost_count)

    deduction_count = _safe_scalar(
        db,
        select(func.count()).where(
            ResultSetValidation.run_id == run_id,
            ResultSetValidation.relevance_deduction != 0,
        ),
    )
    _append_alert(alerts, alert_type="relevance_deduction_applied", count=deduction_count)

    latest_score_id = (
        select(func.max(KeywordScore.id))
        .where(KeywordScore.keyword_id == ResultSetValidation.keyword_id)
        .correlate(ResultSetValidation)
        .scalar_subquery()
    )
    latest_llm_present = (
        select(func.count())
        .where(
            KeywordScore.keyword_id == ResultSetValidation.keyword_id,
            KeywordScore.id == latest_score_id,
            KeywordScore.llm_inputs_used.is_not(None),
            KeywordScore.llm_inputs_used != "null",
        )
        .correlate(ResultSetValidation)
        .scalar_subquery()
    )
    llm_count = _safe_scalar(
        db,
        select(func.count(distinct(ResultSetValidation.keyword_id))).where(
            ResultSetValidation.run_id == run_id,
            latest_llm_present > 0,
        ),
    )
    _append_alert(alerts, alert_type="llm_validation_triggered", count=llm_count)

    signal_family_count = _safe_scalar(
        db,
        select(func.count(distinct(ExternalSignal.signal_type))).where(ExternalSignal.run_id == run_id),
    )
    if 0 < signal_family_count < 4:
        _append_alert(
            alerts,
            alert_type="external_signal_partial",
            count=1,
            n_present=signal_family_count,
            expected=4,
        )

    contamination_count = _safe_scalar(
        db,
        select(func.count()).where(
            ResultSetValidation.run_id == run_id,
            ResultSetValidation.category_contamination_flag.is_(True),
        ),
    )
    _append_alert(alerts, alert_type="contamination_flagged", count=contamination_count)

    total_keywords = _safe_scalar(
        db,
        select(func.count(distinct(SearchResult.keyword_id))).where(SearchResult.run_id == run_id),
    )
    rsv_keywords = _safe_scalar(
        db,
        select(func.count(distinct(ResultSetValidation.keyword_id))).where(ResultSetValidation.run_id == run_id),
    )
    gap = max(total_keywords - rsv_keywords, 0)
    _append_alert(alerts, alert_type="data_integrity_gap", count=gap)

    return sorted(
        alerts,
        key=lambda item: _SEVERITY_ORDER.index(str(item.get("severity", "info"))),
    )
