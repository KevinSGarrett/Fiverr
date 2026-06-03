"""Page 7: Discovery (Story 9.9)."""
from __future__ import annotations

from src.dashboard.sample_data import build_dashboard_demo_data


def render_discovery_page() -> None:
    import streamlit as st

    st.title("Discovery")
    data = build_dashboard_demo_data()
    rows = []
    for run in data["run_history"]:
        rows.append(
            {
                "run_id": run.get("run_id"),
                "status": run.get("status"),
                "stages": ", ".join(stage.get("name", "unknown") for stage in run.get("stages", [])),
                "warnings": run.get("warning_count", 0),
            }
        )

    st.caption("Discovery readiness view from run-stage evidence.")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.metric("Runs with warnings", sum(1 for row in rows if int(row["warnings"]) > 0))


if __name__ == "__main__":
    render_discovery_page()
