"""Page 1: Opportunities — dashboard landing page (Story 9.3)."""
from __future__ import annotations

from src.dashboard.opportunities import build_opportunities_payload
from src.dashboard.sample_data import build_dashboard_demo_data


def render_opportunities_page() -> None:
    import streamlit as st

    st.title("Opportunities")
    data = build_dashboard_demo_data()
    payload = build_opportunities_payload(records=data["opportunities"])

    st.subheader(payload["title"])
    st.write(payload["state"]["message"])

    metrics = payload.get("metric_cards", [])
    if metrics:
        cols = st.columns(len(metrics))
        for col, metric in zip(cols, metrics, strict=False):
            col.metric(metric.get("label", "Metric"), metric.get("value", "n/a"))

    rows = payload.get("table", {}).get("rows", [])
    st.dataframe(rows, use_container_width=True, hide_index=True)

    warning_summary = payload.get("warning_summary", {})
    if warning_summary.get("warnings"):
        st.warning(" | ".join(warning_summary["warnings"]))
    else:
        st.success("Opportunity payload is healthy.")


if __name__ == "__main__":
    render_opportunities_page()
