"""Page: Playbook (Story 8.7)."""
from __future__ import annotations

from src.dashboard.sample_data import build_dashboard_demo_data


def render_playbook_page() -> None:
    import streamlit as st

    st.title("Playbook")
    data = build_dashboard_demo_data()
    actions = [str(run.get("next_action", "")).strip() for run in data["run_history"]]
    actions = [action for action in actions if action]

    st.caption("Operator next-step guidance derived from latest run outcomes.")
    for idx, action in enumerate(actions, start=1):
        st.write(f"{idx}. {action}")
    if not actions:
        st.info("No actions available yet.")


if __name__ == "__main__":
    render_playbook_page()
