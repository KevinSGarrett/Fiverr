"""Page 4: Recommendations (Story 9.6)."""
from __future__ import annotations

from src.dashboard.sample_data import build_dashboard_demo_data


def render_recommendations_page() -> None:
    import streamlit as st

    st.title("Recommendations")
    data = build_dashboard_demo_data()
    rows = []
    for record in data["opportunities"]:
        score = float(record.get("score", 0.0))
        confidence = float(record.get("confidence", 0.0))
        decision = "GO" if score >= 85 and confidence >= 0.8 else "CONDITIONAL_GO"
        rows.append(
            {
                "opportunity": record.get("opportunity"),
                "score": score,
                "confidence": confidence,
                "decision": decision,
                "niche": record.get("niche"),
            }
        )

    st.caption("Derived recommendation output from current dashboard payload contracts.")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.metric("GO recommendations", sum(1 for row in rows if row["decision"] == "GO"))


if __name__ == "__main__":
    render_recommendations_page()
