"""Page 6: LLM Costs (Story 9.8)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session


def render_llm_costs_page() -> None:
    import streamlit as st

    from src.models import LLMUsageLog

    st.title("LLM Costs")
    with get_db_session() as db:
        try:
            rows = db.query(LLMUsageLog).order_by(LLMUsageLog.created_at.desc()).limit(500).all()
        except Exception as exc:  # noqa: BLE001
            st.info(f"No data yet. Database not ready ({exc}).")
            return
    if not rows:
        st.info("No data yet. Run collection first.")
        return

    total_prompt_tokens = sum(int(row.prompt_tokens or 0) for row in rows)
    total_completion_tokens = sum(int(row.completion_tokens or 0) for row in rows)
    total_tokens = total_prompt_tokens + total_completion_tokens
    total_cost_usd = round(sum(float(row.total_cost_usd or 0.0) for row in rows), 4)

    st.caption("Live usage totals from `llm_usage_logs`.")
    col1, col2, col3 = st.columns(3)
    col1.metric("LLM calls", len(rows))
    col2.metric("Total tokens", f"{total_tokens:,}")
    col3.metric("Total cost (USD)", f"${total_cost_usd}")


if __name__ == "__main__":
    render_llm_costs_page()
