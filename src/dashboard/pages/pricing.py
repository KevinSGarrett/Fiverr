"""Page: Pricing (Story 9.16)."""
from __future__ import annotations

from src.dashboard.sample_data import build_dashboard_demo_data


def render_pricing_page() -> None:
    import streamlit as st

    st.title("Pricing")
    data = build_dashboard_demo_data()
    rows = []
    for record in data["opportunities"]:
        score = float(record.get("score", 0.0))
        tier = "Premium" if score >= 85 else ("Standard" if score >= 70 else "Entry")
        rows.append(
            {
                "service": record.get("opportunity"),
                "niche": record.get("niche"),
                "score": score,
                "suggested_tier": tier,
            }
        )

    st.caption("Pricing tier guidance derived from opportunity score bands.")
    st.dataframe(rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_pricing_page()
