"""Real-data context builders for customer-facing PDF reports.

Each function returns a plain dict matching the Jinja2 variables expected by
the corresponding template in src/reports/templates/. No fabricated values --
fields with no real data source are simply omitted so the template renders
its own "no data" fallback rather than showing a fake number.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from src.models.job import Job
from src.models.keyword_score import KeywordScore
from src.models.market import Keyword
from src.models.niche import Niche, NicheConfigRecord
from src.models.scoring import Recommendation


def _resolve_niche_depth(niche_slug: str, db: Session) -> str:
    depth = (
        db.query(NicheConfigRecord.depth).filter(NicheConfigRecord.niche_id == niche_slug).scalar()
    )
    return str(depth) if isinstance(depth, str) and depth.strip() else "standard"


def build_opportunity_report_context(db: Any, niche_ids: list[int] | None = None) -> dict[str, Any]:
    """Cross-niche (or filtered) keyword rankings with real scores, latest per keyword."""
    if not isinstance(db, Session):
        return {"summary_metrics": [], "niches": []}

    niche_query = db.query(Niche).filter(Niche.is_active.is_(True))
    if niche_ids:
        niche_query = niche_query.filter(Niche.id.in_(niche_ids))
    niche_rows = niche_query.order_by(Niche.name.asc()).all()

    niche_payloads: list[dict[str, Any]] = []
    total_keywords = 0
    total_strong_go = 0
    for niche in niche_rows:
        keyword_score_rows = (
            db.query(Keyword, KeywordScore)
            .join(KeywordScore, Keyword.id == KeywordScore.keyword_id)
            .filter(Keyword.niche_id == niche.id)
            .order_by(KeywordScore.keyword_id.asc(), KeywordScore.scored_at.desc())
            .all()
        )
        latest_by_keyword: dict[int, tuple[Keyword, KeywordScore]] = {}
        for keyword, score in keyword_score_rows:
            if keyword.id not in latest_by_keyword:
                latest_by_keyword[keyword.id] = (keyword, score)

        keyword_entries = [
            {
                "keyword_text": keyword.keyword,
                "tag": score.tag,
                "final_score": score.final_score,
                "demand": score.demand_score,
                "competition": score.competition_score,
                "opportunity": score.opportunity_score,
                "feasibility": score.feasibility_score,
                "trend": score.trend_score,
                "confidence": score.confidence_modifier,
            }
            for keyword, score in sorted(
                latest_by_keyword.values(),
                key=lambda pair: pair[1].final_score if pair[1].final_score is not None else -1.0,
                reverse=True,
            )
        ]
        if not keyword_entries:
            continue

        total_strong_go += sum(1 for entry in keyword_entries if entry["tag"] == "STRONG GO")
        total_keywords += len(keyword_entries)
        niche_payloads.append(
            {
                "name": niche.name,
                "depth": _resolve_niche_depth(niche.slug, db),
                "keyword_count": len(keyword_entries),
                "keywords": keyword_entries,
            }
        )

    summary_metrics = [
        {"label": "Niches", "value": len(niche_payloads)},
        {"label": "Keywords Scored", "value": total_keywords},
        {"label": "STRONG GO", "value": total_strong_go},
    ]
    return {"summary_metrics": summary_metrics, "niches": niche_payloads}


def build_recommendation_report_context(db: Any, run_id: str | None = None) -> dict[str, Any]:
    """All STRONG GO + CONDITIONAL GO recommendations with generation_complete=True."""
    if not isinstance(db, Session):
        return {"recommendations": []}

    query = (
        db.query(Recommendation, Keyword, Niche)
        .join(Keyword, Recommendation.keyword_id == Keyword.id)
        .join(Niche, Keyword.niche_id == Niche.id)
        .filter(Recommendation.generation_complete.is_(True))
        .filter(Recommendation.tag.in_(["STRONG GO", "CONDITIONAL GO"]))
    )
    if run_id:
        query = query.filter(Recommendation.run_id_text == run_id)
    rows = query.order_by(Recommendation.final_score.desc()).all()

    recommendations = []
    for rec, keyword, niche in rows:
        recommendations.append(
            {
                "tag": rec.tag,
                "keyword_text": keyword.keyword,
                "niche_name": niche.name,
                "final_score": rec.final_score,
                "generated_at": rec.generated_at.strftime("%Y-%m-%d") if rec.generated_at else "—",
                "viability": rec.niche_viability,
                "gig_titles": rec.gig_titles,
                "package_structure": rec.package_structure,
                "differentiation": rec.differentiation_angle,
                "faq_entries": rec.faq_entries,
                "red_flags": rec.red_flags,
            }
        )
    return {"recommendations": recommendations}


def build_run_summary_context(
    *,
    run_id: str,
    duration_seconds: float,
    collection_result: dict[str, Any],
    scored_count: int,
    recommendations_result: dict[str, Any],
    db: Any = None,
) -> dict[str, Any]:
    """Single-run stats assembled from the full pipeline's own in-memory
    results (real and unambiguous) plus a best-effort DB lookup for
    dead-letter jobs and new STRONG GO keywords tied to this run_id."""
    keywords_expanded = int(collection_result.get("search_jobs_run", 0) or 0)
    gigs_collected = int(collection_result.get("gig_detail_jobs_run", 0) or 0)
    error_count = len(collection_result.get("errors", []) or [])
    llm_cost = float(recommendations_result.get("total_cost_usd", 0.0) or 0.0)

    dead_letters: list[dict[str, Any]] = []
    new_strong_go: list[dict[str, Any]] = []
    if isinstance(db, Session):
        try:
            for job_type, error_log in (
                db.query(Job.job_type, Job.error_log)
                .filter(Job.run_id == run_id, Job.status == "DEAD_LETTER")
                .all()
            ):
                message = (
                    str(error_log[-1])
                    if isinstance(error_log, list) and error_log
                    else "Unknown error"
                )
                dead_letters.append({"job_type": job_type, "error_message": message})
        except Exception:  # noqa: BLE001
            dead_letters = []

        try:
            strong_go_rows = (
                db.query(Recommendation, Keyword, Niche)
                .join(Keyword, Recommendation.keyword_id == Keyword.id)
                .join(Niche, Keyword.niche_id == Niche.id)
                .filter(Recommendation.run_id_text == run_id, Recommendation.tag == "STRONG GO")
                .all()
            )
            new_strong_go = [
                {
                    "keyword_text": keyword.keyword,
                    "niche_name": niche.name,
                    "final_score": rec.final_score,
                }
                for rec, keyword, niche in strong_go_rows
            ]
        except Exception:  # noqa: BLE001
            new_strong_go = []

    minutes, seconds = divmod(int(duration_seconds), 60)
    duration_label = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    summary_text = (
        f"Processed {keywords_expanded} search job(s) and {gigs_collected} gig-detail job(s); "
        f"{scored_count} keyword(s) scored; {error_count} collection error(s)."
    )

    return {
        "run": {
            "duration": duration_label,
            "llm_cost": llm_cost,
            "keywords_expanded": keywords_expanded,
            "gigs_collected": gigs_collected,
            "error_count": error_count,
            "summary_text": summary_text,
            "new_strong_go": new_strong_go,
            "dead_letters": dead_letters,
        }
    }
