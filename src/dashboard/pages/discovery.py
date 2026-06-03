"""Page 7: Discovery (Story 9.9)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session


def render_discovery_page() -> None:
    import streamlit as st

    from src.models import DiscoveryOutcome

    st.title("Discovery")
    with get_db_session() as db:
        try:
            outcomes = (
                db.query(DiscoveryOutcome)
                .order_by(DiscoveryOutcome.created_at.desc())
                .limit(100)
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            st.info(f"Requires live collection run. Database not ready ({exc}).")
            return
    if not outcomes:
        st.info("Requires live collection run.")
        return

    rows = [
        {
            "run_id": row.run_id,
            "niche_id": row.niche_id,
            "keyword_text": row.keyword_text,
            "is_invalid": row.is_invalid,
            "is_contaminated": row.is_contaminated,
            "relevance_score": row.relevance_score,
        }
        for row in outcomes
    ]

    st.caption("Live discovery outcomes and relevance-gate results.")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.metric("Flagged outcomes", sum(1 for row in rows if row["is_invalid"] or row["is_contaminated"]))


if __name__ == "__main__":
    render_discovery_page()
