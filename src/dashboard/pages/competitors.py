"""Page 3: Competitors (Story 9.5)."""
from __future__ import annotations

from src.dashboard.sample_data import build_dashboard_demo_data


def render_competitors_page() -> None:
    import streamlit as st

    st.title("Competitors")
    data = build_dashboard_demo_data()
    by_niche: dict[str, int] = {}
    for row in data["keywords"]:
        niche = str(row.get("niche", "unknown"))
        by_niche[niche] = by_niche.get(niche, 0) + 1

    st.caption("Competitor-facing niche density (proxy) derived from analyzed keyword sets.")
    table = [{"niche": niche, "keyword_count": count} for niche, count in sorted(by_niche.items())]
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.metric("Tracked niches", len(table))


if __name__ == "__main__":
    render_competitors_page()
