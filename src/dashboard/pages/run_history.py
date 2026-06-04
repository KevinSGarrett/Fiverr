"""Page 5: Run History (Story 9.7)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session
from src.dashboard.run_history import build_run_history_payload


def render_revenue_projection(keyword_id: int, db: object) -> None:
    """Render projected monthly revenue for pricing ladder milestones."""
    import json

    import streamlit as st

    from src.models.price_analysis import PricingSnapshot

    snapshot = db.query(PricingSnapshot).filter(PricingSnapshot.keyword_id == keyword_id).first()
    if not snapshot or not snapshot.price_ladder:
        st.caption("Revenue projection requires pricing snapshot data.")
        return

    ladder = snapshot.price_ladder
    if isinstance(ladder, str):
        try:
            ladder = json.loads(ladder)
        except json.JSONDecodeError:
            ladder = []
    if not isinstance(ladder, list):
        st.caption("Revenue projection requires pricing snapshot data.")
        return

    monthly_orders = 4
    st.caption("Projected monthly revenue (basic tier, 4 orders/month estimate):")
    for step in ladder:
        if not isinstance(step, dict):
            continue
        milestone = step.get("milestone_reviews", step.get("milestone", 0))
        basic_price = float(step.get("basic", 0) or 0)
        revenue = basic_price * monthly_orders
        st.write(f"At {int(milestone)} reviews: ${basic_price:.0f}/gig -> ${revenue:.0f}/mo")


def render_run_history_page() -> None:
    import streamlit as st

    from src.models import RunLog

    st.title("Run History")
    with get_db_session() as db:
        try:
            rows = (
                db.query(RunLog)
                .order_by(RunLog.created_at.desc())
                .limit(100)
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            st.info(f"No data yet. Database not ready ({exc}).")
            return
    if not rows:
        st.info("No data yet. Run collection first.")
        return

    records = [
        {
            "run_id": str(row.run_id or ""),
            "status": row.status or "unknown",
            "warning_count": 0,
            "duration_seconds": 0,
            "failure_summary": "None" if (row.status or "").lower() in {"pass", "ready"} else row.message,
            "stages": [{"name": row.stage}],
            "next_action": row.message,
        }
        for row in rows
    ]
    payload = build_run_history_payload(records=records)

    st.subheader(payload["title"])
    st.write(payload["state"]["message"])

    metrics = payload.get("metric_cards", [])
    if metrics:
        cols = st.columns(len(metrics))
        for col, metric in zip(cols, metrics, strict=False):
            col.metric(metric.get("label", "Metric"), metric.get("value", "n/a"))

    st.dataframe(payload.get("table", {}).get("rows", []), use_container_width=True, hide_index=True)
    if payload.get("warning_summary", {}).get("warnings"):
        st.warning(" | ".join(payload["warning_summary"]["warnings"]))

    with get_db_session() as db:
        from src.models.price_analysis import PricingSnapshot

        snapshot = db.query(PricingSnapshot).order_by(PricingSnapshot.created_at.desc()).first()
        if snapshot is not None:
            if hasattr(st, "markdown"):
                st.markdown("#### W-PRICE-4 Revenue Projection")
            else:
                st.caption("W-PRICE-4 Revenue Projection")
            render_revenue_projection(int(snapshot.keyword_id or 0), db)


if __name__ == "__main__":
    render_run_history_page()
