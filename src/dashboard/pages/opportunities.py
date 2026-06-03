"""Page 1: Opportunities — dashboard landing page (Story 9.3)."""
from __future__ import annotations

from sqlalchemy import and_, func

from src.dashboard.db_helpers import get_db_session
from src.dashboard.opportunities import build_opportunities_payload


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
            rows = (
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
    if not rows:
        st.info("No scored keywords yet. Run: py -3.12 run.py run --mode score-only")
        return

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
        for score, keyword in rows
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


if __name__ == "__main__":
    render_opportunities_page()
