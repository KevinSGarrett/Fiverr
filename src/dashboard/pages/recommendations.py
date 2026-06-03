"""Page 4: Recommendations (Story 9.6)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session


def render_recommendations_page() -> None:
    import streamlit as st

    from src.models import Recommendation

    st.title("Recommendations")
    with get_db_session() as db:
        try:
            recommendations = (
                db.query(Recommendation)
                .order_by(Recommendation.generated_at.desc())
                .limit(100)
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            st.info(f"No data yet. Database not ready ({exc}).")
            return
    if not recommendations:
        st.info("No data yet. Run collection first.")
        return

    rows = []
    for recommendation in recommendations:
        score = float(recommendation.final_score or 0.0)
        confidence = float(recommendation.confidence or 0.0)
        decision = "GO" if score >= 85 and confidence >= 0.8 else "CONDITIONAL_GO"
        rows.append(
            {
                "recommendation_type": recommendation.recommendation_type,
                "score": score,
                "confidence": confidence,
                "decision": decision,
                "niche": recommendation.niche_id,
            }
        )

    st.caption("Live recommendation outputs from scoring/generation pipelines.")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.metric("GO recommendations", sum(1 for row in rows if row["decision"] == "GO"))


if __name__ == "__main__":
    render_recommendations_page()
