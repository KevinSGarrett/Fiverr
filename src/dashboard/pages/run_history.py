"""Page 5: Run History (Story 9.7)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session
from src.dashboard.run_history import build_run_history_payload


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


if __name__ == "__main__":
    render_run_history_page()
