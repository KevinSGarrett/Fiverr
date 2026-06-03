"""Page 2: Keywords (Story 9.4)."""
from __future__ import annotations

from src.dashboard.db_helpers import get_db_session
from src.dashboard.keywords import build_keywords_payload


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

    st.dataframe(payload.get("table", {}).get("rows", []), use_container_width=True, hide_index=True)
    cluster_summary = payload.get("cluster_summary", {})
    st.caption(
        f"Clusters: {cluster_summary.get('cluster_count', 0)} | "
        f"Unclustered: {cluster_summary.get('unclustered_count', 0)}"
    )


if __name__ == "__main__":
    render_keywords_page()
