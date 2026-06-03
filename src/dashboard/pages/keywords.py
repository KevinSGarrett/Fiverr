"""Page 2: Keywords (Story 9.4)."""
from __future__ import annotations

from src.dashboard.keywords import build_keywords_payload
from src.dashboard.sample_data import build_dashboard_demo_data


def render_keywords_page() -> None:
    import streamlit as st

    st.title("Keywords")
    data = build_dashboard_demo_data()
    payload = build_keywords_payload(records=data["keywords"])

    st.subheader(payload["title"])
    st.write(payload["state"]["message"])

    metrics = payload.get("metric_cards", [])
    if metrics:
        cols = st.columns(len(metrics))
        for col, metric in zip(cols, metrics, strict=False):
            col.metric(metric.get("label", "Metric"), metric.get("value", "n/a"))

    st.dataframe(payload.get("table", {}).get("rows", []), use_container_width=True, hide_index=True)
    cluster_summary = payload.get("cluster_summary", {})
    st.caption(
        f"Clusters: {cluster_summary.get('cluster_count', 0)} | "
        f"Unclustered: {cluster_summary.get('unclustered_count', 0)}"
    )


if __name__ == "__main__":
    render_keywords_page()
