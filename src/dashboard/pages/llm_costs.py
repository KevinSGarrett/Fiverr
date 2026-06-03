"""Page 6: LLM Costs (Story 9.8)."""
from __future__ import annotations

from src.dashboard.sample_data import build_dashboard_demo_data


def render_llm_costs_page() -> None:
    import streamlit as st

    st.title("LLM Costs")
    data = build_dashboard_demo_data()
    keyword_count = len(data["keywords"])
    est_tokens = keyword_count * 1200
    est_cost_usd = round(est_tokens / 1_000_000 * 5.0, 4)

    st.caption("Current deterministic estimate based on analyzed keyword volume.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Analyzed keywords", keyword_count)
    col2.metric("Estimated tokens", f"{est_tokens:,}")
    col3.metric("Estimated cost (USD)", f"${est_cost_usd}")


if __name__ == "__main__":
    render_llm_costs_page()
