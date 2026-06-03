"""Page 3: Competitors (Story 9.5)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session


def render_competitors_page() -> None:
    import streamlit as st

    from src.models import CompetitorProfile

    st.title("Competitors")
    with get_db_session() as db:
        try:
            rows = (
                db.query(CompetitorProfile)
                .order_by(CompetitorProfile.collected_at.desc())
                .limit(100)
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            st.info(f"No data yet. Database not ready ({exc}).")
            return
    if not rows:
        st.info("No data yet. Run collection first.")
        return

    table = [
        {
            "niche_id": row.niche_id,
            "run_id": row.run_id,
            "top_gig_count": row.top_gig_count,
            "median_price": row.median_price,
            "mean_reviews": row.mean_reviews,
        }
        for row in rows
    ]
    st.caption("Live competitor profile snapshots from collection/analysis runs.")
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.metric("Tracked niches", len(table))


if __name__ == "__main__":
    render_competitors_page()
