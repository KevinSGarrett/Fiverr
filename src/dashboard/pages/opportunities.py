"""Page 1: Opportunities — dashboard landing page (Story 9.3)."""
from __future__ import annotations

from sqlalchemy import and_, func

from src.dashboard.db_helpers import get_db_session
from src.dashboard.opportunities import build_opportunities_payload


def render_price_distribution_chart(keyword_id: int, db: object) -> None:
    """Render a compact Basic-tier competitor price histogram for one keyword."""
    import streamlit as st
    import plotly.graph_objects as go

    from src.models.price_analysis import PriceAnalysis
    from src.pricing.analysis import extract_tier_prices
    from src.models.gig import Gig

    price_data = db.query(PriceAnalysis).filter(PriceAnalysis.keyword_id == keyword_id).first()
    if not price_data or not price_data.basic_n:
        st.caption("No pricing data available")
        return

    gigs = db.query(Gig).filter(Gig.keyword_id == keyword_id).all()
    basic_prices = [price for price in extract_tier_prices(gigs, "basic") if price > 0]
    if not basic_prices:
        st.caption("No price data")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=basic_prices,
            nbinsx=min(20, len(basic_prices)),
            name="Competitors",
            marker_color="rgba(99,110,250,0.6)",
        )
    )
    if price_data.basic_median:
        fig.add_vline(
            x=price_data.basic_median,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Median ${price_data.basic_median:.0f}",
        )
    fig.update_layout(
        height=200,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        showlegend=False,
        xaxis_title="Price ($)",
        yaxis_title="Count",
    )
    if hasattr(st, "plotly_chart"):
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Price distribution chart unavailable in current Streamlit runtime.")


def render_opportunities_page() -> None:
    import streamlit as st

    from src.models import Keyword, KeywordScore

    st.title("Opportunities")
    with get_db_session() as db:
        try:
            latest_score_subquery = (
                db.query(
                    KeywordScore.keyword_id.label("keyword_id"),
                    KeywordScore.scoring_profile.label("scoring_profile"),
                    func.max(KeywordScore.scored_at).label("latest_scored_at"),
                )
                .group_by(KeywordScore.keyword_id, KeywordScore.scoring_profile)
                .subquery()
            )
            query_rows = (
                db.query(KeywordScore, Keyword)
                .join(Keyword, Keyword.id == KeywordScore.keyword_id)
                .join(
                    latest_score_subquery,
                    and_(
                        KeywordScore.keyword_id == latest_score_subquery.c.keyword_id,
                        KeywordScore.scoring_profile == latest_score_subquery.c.scoring_profile,
                        KeywordScore.scored_at == latest_score_subquery.c.latest_scored_at,
                    ),
                )
                .order_by(KeywordScore.final_score.desc())
                .limit(50)
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            st.info(f"No scored keywords yet. Database not ready ({exc}).")
            return
    if not query_rows:
        st.info("No scored keywords yet. Run: py -3.12 run.py run --mode score-only")
        return

    top_keyword_id = query_rows[0][0].keyword_id if query_rows else None
    records = [
        {
            "id": f"opportunity-{score.keyword_id}",
            "opportunity": keyword.keyword,
            "keyword_text": keyword.keyword,
            "niche": str(keyword.niche_id),
            "score": float(score.final_score or 0.0),
            "confidence": float(score.confidence_modifier or 0.0),
            "status": score.tag or "unknown",
            "keyword_links": [],
        }
        for score, keyword in query_rows
    ]
    payload = build_opportunities_payload(records=records)

    st.subheader(payload["title"])
    st.write(payload["state"]["message"])

    metrics = payload.get("metric_cards", [])
    if metrics:
        cols = st.columns(len(metrics))
        for col, metric in zip(cols, metrics, strict=False):
            col.metric(metric.get("label", "Metric"), metric.get("value", "n/a"))

    rows = payload.get("table", {}).get("rows", [])
    st.dataframe(rows, use_container_width=True, hide_index=True)

    warning_summary = payload.get("warning_summary", {})
    if warning_summary.get("warnings"):
        st.warning(" | ".join(warning_summary["warnings"]))
    else:
        st.success("Opportunity data loaded successfully.")

    if top_keyword_id:
        if hasattr(st, "markdown"):
            st.markdown("#### W-PRICE-1 Basic Tier Distribution")
        else:
            st.caption("W-PRICE-1 Basic Tier Distribution")
        with get_db_session() as db:
            render_price_distribution_chart(int(top_keyword_id), db)


if __name__ == "__main__":
    render_opportunities_page()
