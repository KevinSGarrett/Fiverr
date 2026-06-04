"""Page 4: Recommendations (Story 9.6)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.dashboard.db_helpers import get_db_session


def render_pricing_strategy_card(keyword_id: int, recommendation: object, db: Session) -> None:
    """Render pricing summary and LLM narrative for a recommendation keyword."""
    import streamlit as st

    from src.models.price_analysis import PricingSnapshot

    snapshot = db.query(PricingSnapshot).filter(PricingSnapshot.keyword_id == keyword_id).first()
    if not snapshot:
        st.info("Pricing analysis not yet available for this keyword.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Entry Basic", f"${snapshot.entry_basic:.0f}" if snapshot.entry_basic else "N/A")
    col2.metric("Entry Standard", f"${snapshot.entry_standard:.0f}" if snapshot.entry_standard else "N/A")
    col3.metric("Entry Premium", f"${snapshot.entry_premium:.0f}" if snapshot.entry_premium else "N/A")

    if snapshot.market_type:
        st.caption(f"Market Type: {snapshot.market_type} | Confidence: {snapshot.confidence}")

    narrative = getattr(recommendation, "pricing_strategy", None)
    if isinstance(narrative, str) and narrative.strip():
        if hasattr(st, "markdown"):
            st.markdown("**Pricing Strategy:**")
        else:
            st.caption("Pricing Strategy:")
        st.write(narrative)


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
    if hasattr(st, "tabs"):
        overview_tab, pricing_tab, details_tab = st.tabs(["Overview", "Pricing Strategy", "Details"])
        with overview_tab:
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.metric("GO recommendations", sum(1 for row in rows if row["decision"] == "GO"))
        with pricing_tab:
            latest = recommendations[0]
            with get_db_session() as db:
                render_pricing_strategy_card(int(getattr(latest, "keyword_id", 0) or 0), latest, db)
        with details_tab:
            st.write(
                {
                    "total_recommendations": len(rows),
                    "go_recommendations": sum(1 for row in rows if row["decision"] == "GO"),
                }
            )
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.metric("GO recommendations", sum(1 for row in rows if row["decision"] == "GO"))
        latest = recommendations[0]
        with get_db_session() as db:
            render_pricing_strategy_card(int(getattr(latest, "keyword_id", 0) or 0), latest, db)


if __name__ == "__main__":
    render_recommendations_page()
