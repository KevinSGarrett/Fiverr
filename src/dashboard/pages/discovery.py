"""Page 7: Discovery (Story 9.9)."""
from __future__ import annotations

from typing import Any

from src.dashboard.db_helpers import get_db_session


def get_discovery_stats(db: Any) -> dict[str, Any]:
    try:
        from sqlalchemy import func

        from src.models import DiscoveryCycleLog

        total_runs, total_inserted, total_gated, last_run_at = (
            db.query(
                func.count(DiscoveryCycleLog.id),
                func.sum(DiscoveryCycleLog.hypotheses_accepted),
                func.sum(DiscoveryCycleLog.hypotheses_gated),
                func.max(DiscoveryCycleLog.cycle_at),
            )
            .one()
        )
        latest = db.query(DiscoveryCycleLog).order_by(DiscoveryCycleLog.cycle_at.desc()).first()
        return {
            "total_runs": int(total_runs or 0),
            "total_inserted": int(total_inserted or 0),
            "total_gated": int(total_gated or 0),
            "last_run_at": last_run_at,
            "last_run_id": getattr(latest, "run_id", None),
        }
    except Exception:  # noqa: BLE001
        return {
            "total_runs": 0,
            "total_inserted": 0,
            "total_gated": 0,
            "last_run_at": None,
            "last_run_id": None,
        }


def get_gold_discoveries(db: Any, limit: int = 50) -> list[dict[str, Any]]:
    try:
        from src.models import Keyword

        specificity_col = getattr(Keyword, "specificity_score", None) or getattr(Keyword, "hypothesis_confidence", None)
        query = db.query(Keyword).filter(Keyword.is_discovery.is_(True))
        if specificity_col is not None:
            query = query.filter(specificity_col >= 0.70).order_by(specificity_col.desc())
        rows = query.limit(limit).all()
        payload: list[dict[str, Any]] = []
        for row in rows:
            score = getattr(row, "specificity_score", None)
            if score is None:
                score = getattr(row, "hypothesis_confidence", None)
            payload.append(
                {
                    "keyword_text": getattr(row, "keyword", ""),
                    "niche_id": str(getattr(row, "niche_id", "")),
                    "discovery_mode": getattr(row, "discovery_mode", None),
                    "specificity_score": score,
                    "discovered_in_run": getattr(row, "discovered_in_run", None),
                }
            )
        return payload
    except Exception:  # noqa: BLE001
        return []


def get_mode_performance(db: Any) -> dict[str, dict[str, Any]]:
    try:
        from sqlalchemy import func

        from src.models import Keyword

        specificity_col = getattr(Keyword, "specificity_score", None) or getattr(Keyword, "hypothesis_confidence", None)
        if specificity_col is not None:
            rows = (
                db.query(
                    Keyword.discovery_mode,
                    func.count(Keyword.id),
                    func.avg(specificity_col),
                )
                .filter(Keyword.is_discovery.is_(True))
                .group_by(Keyword.discovery_mode)
                .all()
            )
        else:
            rows = (
                db.query(
                    Keyword.discovery_mode,
                    func.count(Keyword.id),
                )
                .filter(Keyword.is_discovery.is_(True))
                .group_by(Keyword.discovery_mode)
                .all()
            )

        payload: dict[str, dict[str, Any]] = {}
        for row in rows:
            mode = row[0] or "unknown"
            count = row[1]
            avg_score = row[2] if len(row) > 2 else None
            payload[mode] = {
                "count": int(count or 0),
                "avg_specificity": round(float(avg_score), 3) if avg_score is not None else None,
            }
        return payload
    except Exception:  # noqa: BLE001
        return {}


def render_discovery_page() -> None:
    import streamlit as st

    st.title("Discovery")
    try:
        with get_db_session() as db:
            stats = get_discovery_stats(db)
            gold_discoveries = get_gold_discoveries(db)
            mode_performance = get_mode_performance(db)
    except Exception as exc:  # noqa: BLE001
        st.info(f"Requires live collection run. Database not ready ({exc}).")
        return

    cols = list(st.columns(3))
    metrics = [
        ("Total discovery runs", stats["total_runs"]),
        ("Total inserted", stats["total_inserted"]),
        ("Total gated", stats["total_gated"]),
    ]
    for index, (label, value) in enumerate(metrics):
        if index < len(cols):
            cols[index].metric(label, value)
        else:
            st.metric(label, value)

    if stats.get("last_run_id"):
        st.caption(f"Most recent discovery run: {stats['last_run_id']}")

    st.subheader("Gold discoveries")
    if gold_discoveries:
        st.dataframe(gold_discoveries, use_container_width=True, hide_index=True)
    else:
        st.info("No gold discoveries yet. Run discovery to populate this widget.")

    st.subheader("Mode performance")
    if mode_performance:
        mode_rows = [
            {
                "discovery_mode": mode,
                "count": data["count"],
                "avg_specificity": data["avg_specificity"],
            }
            for mode, data in sorted(mode_performance.items())
        ]
        st.dataframe(mode_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No mode performance data available yet.")

if __name__ == "__main__":
    render_discovery_page()
