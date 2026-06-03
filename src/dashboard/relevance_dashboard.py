"""R10 display-oriented relevance dashboard helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from src.dashboard.alert_generator import generate_relevance_alerts_for_run


def calculate_niche_relevance_quality_score(niche_id: int, run_id: str, db: Any) -> float:
    """Compute average relevance score for a niche/run and clamp to [0, 1]."""
    if db is None:
        return 0.0

    from src.models.market import Keyword
    from src.models.result_set_validation import ResultSetValidation

    stmt = (
        select(func.avg(ResultSetValidation.result_set_relevance_score))
        .join(Keyword, Keyword.id == ResultSetValidation.keyword_id)
        .where(
            ResultSetValidation.run_id == run_id,
            Keyword.niche_id == niche_id,
        )
    )
    result = db.execute(stmt).scalar()
    if result is None:
        return 0.0
    return max(0.0, min(1.0, float(result)))


def build_data_integrity_block(keyword_score_row: Any) -> dict[str, Any]:
    """Build a display block where missing score components are rendered as N/A."""
    components = getattr(keyword_score_row, "score_components", None)
    if not isinstance(components, dict):
        return {"status": "gap", "score_components": "N/A", "note": "No score components available."}

    return {
        "status": "ok",
        "score_components": components,
        "component_count": len(components),
    }


def run_summary_relevance_block(run_id: str, db: Any) -> dict[str, Any]:
    """Build run summary with alert inventory and ghost-market headline."""
    alerts = generate_relevance_alerts_for_run(run_id, db)
    ghost_alert = next((row for row in alerts if row.get("type") == "ghost_market_detected"), None)
    ghost_count = int(ghost_alert.get("count", 0)) if isinstance(ghost_alert, dict) else 0
    return {
        "run_id": run_id,
        "alerts": alerts,
        "alert_count": len(alerts),
        "ghost_market_count": ghost_count,
        "ghost_market_print": (
            f"⚠ {ghost_count} ghost market keyword(s) flagged"
            if ghost_count > 0
            else "✓ No ghost markets detected"
        ),
    }


def get_opportunities_for_display(
    run_id: str,
    db: Any,
    show_ghost_markets: bool = False,
) -> list[Any]:
    """Return run-scoped opportunities, hiding ghost-market rows by default."""
    if db is None:
        return []

    from src.models.market import Keyword
    from src.models.result_set_validation import ResultSetValidation

    stmt = (
        select(ResultSetValidation)
        .join(Keyword, Keyword.id == ResultSetValidation.keyword_id)
        .where(ResultSetValidation.run_id == run_id)
    )
    if not show_ghost_markets:
        stmt = stmt.where(
            ResultSetValidation.ghost_market_flag.is_not(True),
            Keyword.ghost_market_flag.is_not(True),
        )
    return list(db.execute(stmt).scalars().all())
