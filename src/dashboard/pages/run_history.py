"""Page 5: Run History (Story 9.7)."""
from __future__ import annotations

from src.dashboard.run_history import build_run_history_payload
from src.dashboard.sample_data import build_dashboard_demo_data


def render_run_history_page() -> None:
    import streamlit as st

    st.title("Run History")
    data = build_dashboard_demo_data()
    payload = build_run_history_payload(records=data["run_history"])

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
