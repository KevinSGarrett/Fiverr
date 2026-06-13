"""Page 2: Keywords (Story 9.4)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.dashboard.db_helpers import get_db_session
from src.dashboard.keywords import build_keywords_payload


def get_pricing_summary_for_keyword(keyword_id: int, db: Session) -> dict[str, float | str | None]:
    """Return median tier pricing summary for a keyword."""
    from src.models.price_analysis import PriceAnalysis

    row = db.query(PriceAnalysis).filter(PriceAnalysis.keyword_id == keyword_id).first()
    if row is None:
        return {"basic": None, "standard": None, "premium": None}
    return {
        "basic": row.basic_median,
        "standard": row.standard_median,
        "premium": row.premium_median,
        "market_type": row.market_type,
    }


def render_price_heatmap(niche_id: str, db: Session) -> None:
    """Render cross-keyword pricing heatmap for basic/standard/premium medians."""
    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st

    from src.models import Keyword
    from src.models.price_analysis import PriceAnalysis

    analyses = (
        db.query(PriceAnalysis, Keyword)
        .join(Keyword, PriceAnalysis.keyword_id == Keyword.id)
        .filter(Keyword.niche_id == niche_id)
        .all()
    )
    if not analyses:
        st.info("No pricing data yet for this niche.")
        return

    rows: list[dict[str, object]] = []
    for price_analysis, keyword in analyses:
        rows.append(
            {
                "keyword": keyword.keyword[:30],
                "basic": price_analysis.basic_median,
                "standard": price_analysis.standard_median,
                "premium": price_analysis.premium_median,
            }
        )

    dataframe = pd.DataFrame(rows).set_index("keyword")
    fig = go.Figure(
        data=go.Heatmap(
            z=dataframe.values,
            x=dataframe.columns.tolist(),
            y=dataframe.index.tolist(),
            colorscale="Blues",
            hoverongaps=False,
            hovertemplate="Keyword: %{y}<br>Tier: %{x}<br>Median: $%{z:.0f}<extra></extra>",
        )
    )
    fig.update_layout(height=min(400, 60 + 30 * len(dataframe)), margin={"l": 0, "r": 0, "t": 20, "b": 0})
    if hasattr(st, "plotly_chart"):
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Price heatmap unavailable in current Streamlit runtime.")


def render_keywords_page() -> None:
    import streamlit as st

    from src.models import Keyword, KeywordScore

    st.title("Keywords")
    with get_db_session() as db:
        try:
            rows = (
                db.query(Keyword, KeywordScore)
                .join(KeywordScore, KeywordScore.keyword_id == Keyword.id, isouter=True)
                .order_by(KeywordScore.final_score.desc())
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            st.info(f"No data yet. Database not ready ({exc}).")
            return
    if not rows:
        st.info("No data yet. Run collection first.")
        return

    records = [
        {
            "id": keyword.id,
            "keyword": keyword.keyword,
            "niche": str(keyword.niche_id),
            "cluster": keyword.cluster_id,
            "score": (score.final_score if score else None),
            "confidence": (score.confidence_modifier if score else None),
            "status": (score.tag if score else "unknown"),
            "source_name": "live_db",
        }
        for keyword, score in rows
    ]
    payload = build_keywords_payload(records=records)

    st.subheader(payload["title"])
    st.write(payload["state"]["message"])

    metrics = payload.get("metric_cards", [])
    if metrics:
        cols = st.columns(len(metrics))
        for col, metric in zip(cols, metrics, strict=False):
            col.metric(metric.get("label", "Metric"), metric.get("value", "n/a"))

    table_rows = payload.get("table", {}).get("rows", [])
    enriched_rows: list[dict[str, object]] = []
    with get_db_session() as db:
        for row in table_rows:
            drill_metadata = row.get("drill_metadata", {}) if isinstance(row, dict) else {}
            keyword_id = drill_metadata.get("keyword_id") if isinstance(drill_metadata, dict) else None
            pricing = get_pricing_summary_for_keyword(int(keyword_id), db) if keyword_id else {}
            basic = pricing.get("basic")
            standard = pricing.get("standard")
            premium = pricing.get("premium")
            row_copy = dict(row)
            if basic is None and standard is None and premium is None:
                row_copy["price"] = "N/A"
            else:
                row_copy["price"] = f"B:${(basic or 0):.0f} S:${(standard or 0):.0f} P:${(premium or 0):.0f}"
            enriched_rows.append(row_copy)

    st.dataframe(enriched_rows, use_container_width=True, hide_index=True)
    cluster_summary = payload.get("cluster_summary", {})
    st.caption(
        f"Clusters: {cluster_summary.get('cluster_count', 0)} | "
        f"Unclustered: {cluster_summary.get('unclustered_count', 0)}"
    )
    if records:
        if hasattr(st, "markdown"):
            st.markdown("#### W-PRICE-3 Niche Price Heatmap")
        else:
            st.caption("W-PRICE-3 Niche Price Heatmap")
        with get_db_session() as db:
            render_price_heatmap(str(records[0]["niche"]), db)


if __name__ == "__main__":
    render_keywords_page()
