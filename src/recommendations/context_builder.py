"""Stage 13 recommendation context builder helpers."""

from __future__ import annotations

from typing import Any

from src.models import (
    ClusterAssignment,
    ClusterLabel,
    CompetitorProfile,
    FinalScore,
    Gig,
    Keyword,
    KeywordScore,
    Niche,
    SearchResult,
    get_registered_model_classes,
)
from src.recommendations.contracts import RecommendationContext


def build_recommendation_context(
    keyword_id: int,
    niche_id: int | str | None,
    run_id: str | int | None,
    db: Any,
) -> RecommendationContext | None:
    """Assemble recommendation context from scoring + analysis persistence layers."""
    keyword = _query_first(db, Keyword, Keyword.id == keyword_id)
    score_row = _latest_keyword_score(keyword_id, db)
    if keyword is None or score_row is None:
        return None

    resolved_niche_id = niche_id if niche_id is not None else getattr(keyword, "niche_id", None)
    resolved_niche_name = _resolve_niche_name(resolved_niche_id, db)
    ranking_row = _latest_opportunity_ranking(keyword_id=keyword_id, run_id=run_id, db=db)

    tag = _normalize_tag(getattr(ranking_row, "tag", None) or getattr(score_row, "tag", None))
    final_score = _to_float(
        getattr(ranking_row, "final_score", None),
        default=_to_float(getattr(score_row, "final_score", None), default=0.0),
    )
    cluster_label, cluster_size = _load_cluster_context(
        keyword_id=keyword_id,
        niche_id=resolved_niche_id,
        run_id=run_id,
        db=db,
    )

    competitor_weaknesses = _load_competitor_weaknesses(
        keyword_id=keyword_id,
        niche_id=resolved_niche_id,
        run_id=run_id,
        db=db,
    )
    confidence_modifier = get_confidence_modifier(keyword_id=keyword_id, db=db)
    keyword_text = str(getattr(keyword, "keyword", "") or "")

    return RecommendationContext(
        keyword_id=keyword_id,
        keyword_text=keyword_text,
        keyword=keyword_text,
        niche_id=resolved_niche_id if resolved_niche_id is not None else "",
        niche_name=resolved_niche_name,
        run_id=run_id,
        tag=tag,
        final_score=final_score,
        confidence_modifier=confidence_modifier,
        demand_score=_to_optional_float(getattr(score_row, "demand_score", None)),
        competition_score=_to_optional_float(getattr(score_row, "competition_score", None)),
        opportunity_score=_to_optional_float(getattr(score_row, "opportunity_score", None)),
        feasibility_score=_to_optional_float(getattr(score_row, "feasibility_score", None)),
        saturation_score=_to_optional_float(getattr(score_row, "saturation_score", None)),
        top_competitor_weaknesses=competitor_weaknesses,
        cluster_label=cluster_label,
        cluster_size=cluster_size,
        score_data={
            "demand_score": _to_optional_float(getattr(score_row, "demand_score", None)),
            "competition_score": _to_optional_float(getattr(score_row, "competition_score", None)),
            "opportunity_score": _to_optional_float(getattr(score_row, "opportunity_score", None)),
            "feasibility_score": _to_optional_float(getattr(score_row, "feasibility_score", None)),
            "saturation_score": _to_optional_float(getattr(score_row, "saturation_score", None)),
            "confidence_modifier": confidence_modifier,
        },
        competitor_data={"top_competitor_weaknesses": competitor_weaknesses},
    )


def get_confidence_modifier(keyword_id: int, db: Any) -> float:
    """Return confidence modifier in [0.0, 1.0], defaulting to 0.5."""
    score_row = _latest_keyword_score(keyword_id, db)
    if score_row is not None:
        score_value = _to_optional_float(getattr(score_row, "confidence_modifier", None))
        if score_value is not None:
            return max(0.0, min(1.0, score_value))

    final_row = _query_latest_final_score(keyword_id, db)
    raw_json = getattr(final_row, "raw_json", {}) if final_row is not None else {}
    if isinstance(raw_json, dict):
        raw_confidence = _to_optional_float(raw_json.get("confidence_modifier"))
        if raw_confidence is not None:
            return max(0.0, min(1.0, raw_confidence))
    return 0.5


def _latest_keyword_score(keyword_id: int, db: Any) -> Any | None:
    query = _safe_query(db, KeywordScore)
    if query is None:
        return None
    return query.filter(KeywordScore.keyword_id == keyword_id).order_by(KeywordScore.scored_at.desc()).first()


def _query_latest_final_score(keyword_id: int, db: Any) -> Any | None:
    query = _safe_query(db, FinalScore)
    if query is None:
        return None
    return query.filter(FinalScore.keyword_id == keyword_id).order_by(FinalScore.created_at.desc()).first()


def _latest_opportunity_ranking(keyword_id: int, run_id: str | int | None, db: Any) -> Any | None:
    ranking_model = _model_by_name("OpportunityRanking")
    if ranking_model is None:
        return None
    query = _safe_query(db, ranking_model)
    if query is None:
        return None

    keyword_column = getattr(ranking_model, "keyword_id", None)
    if keyword_column is not None:
        query = query.filter(keyword_column == keyword_id)

    run_column = getattr(ranking_model, "run_id", None)
    if run_column is not None and run_id is not None:
        query = query.filter(run_column == str(run_id))

    scored_at_column = getattr(ranking_model, "scored_at", None)
    if scored_at_column is not None:
        query = query.order_by(scored_at_column.desc())
    return query.first()


def _load_cluster_context(
    keyword_id: int,
    niche_id: int | str | None,
    run_id: str | int | None,
    db: Any,
) -> tuple[str | None, int | None]:
    assignment_query = _safe_query(db, ClusterAssignment)
    if assignment_query is None:
        return None, None
    assignment_query = assignment_query.filter(ClusterAssignment.keyword_id == keyword_id)
    if run_id is not None:
        assignment_query = assignment_query.filter(ClusterAssignment.run_id == str(run_id))
    assignment = assignment_query.order_by(ClusterAssignment.assigned_at.desc()).first()
    if assignment is None:
        return None, None

    label_query = _safe_query(db, ClusterLabel)
    if label_query is None:
        return None, None
    label_query = label_query.filter(ClusterLabel.cluster_id == assignment.cluster_id)
    if niche_id is not None:
        label_query = label_query.filter(ClusterLabel.niche_id == str(niche_id))
    if run_id is not None:
        label_query = label_query.filter(ClusterLabel.run_id == str(run_id))
    label_row = label_query.order_by(ClusterLabel.created_at.desc()).first()
    if label_row is None:
        return None, None
    return _to_optional_str(getattr(label_row, "label_text", None)), _to_optional_int(
        getattr(label_row, "keyword_count", None)
    )


def _load_competitor_weaknesses(
    keyword_id: int,
    niche_id: int | str | None,
    run_id: str | int | None,
    db: Any,
    limit: int = 5,
) -> list[dict[str, Any]]:
    profile_query = _safe_query(db, CompetitorProfile)
    if profile_query is not None:
        if niche_id is not None:
            profile_query = profile_query.filter(CompetitorProfile.niche_id == str(niche_id))
        if run_id is not None:
            profile_query = profile_query.filter(CompetitorProfile.run_id == str(run_id))
        profile = profile_query.order_by(CompetitorProfile.collected_at.desc()).first()
        if profile is not None:
            new_seller_gap = getattr(profile, "new_seller_gap", {})
            if isinstance(new_seller_gap, dict):
                seeded = new_seller_gap.get("top_competitor_weaknesses")
                if isinstance(seeded, list):
                    normalized = [item for item in seeded if isinstance(item, dict)]
                    if normalized:
                        return normalized[:limit]

    search_query = _safe_query(db, SearchResult)
    if search_query is None:
        return []
    rows = (
        search_query.join(Gig, SearchResult.gig_id == Gig.id, isouter=True)
        .filter(SearchResult.keyword_id == keyword_id)
        .order_by(SearchResult.rank.asc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    output: list[dict[str, Any]] = []
    for row in rows:
        gig_title = ""
        if isinstance(row, tuple):
            search_result = row[0]
            gig_row = row[1] if len(row) > 1 else None
            gig_title = _coalesce_title(search_result=search_result, gig_row=gig_row)
        else:
            gig_title = _coalesce_title(search_result=row, gig_row=getattr(row, "gig", None))
        output.append({"gig_title": gig_title, "weaknesses": []})
    return output


def _coalesce_title(search_result: Any, gig_row: Any) -> str:
    for candidate in (
        getattr(gig_row, "title", None),
        getattr(gig_row, "gig_title_full", None),
        getattr(search_result, "title", None),
    ):
        value = _to_optional_str(candidate)
        if value is not None:
            return value
    return ""


def _resolve_niche_name(niche_id: int | str | None, db: Any) -> str:
    if niche_id is None:
        return "Unknown"

    parsed_niche_id = _to_optional_int(niche_id)
    if parsed_niche_id is not None:
        niche = _query_first(db, Niche, Niche.id == parsed_niche_id)
        if niche is not None:
            return str(getattr(niche, "name", "") or str(niche_id))
    return str(niche_id)


def _query_first(db: Any, model: Any, *filters: Any) -> Any | None:
    query = _safe_query(db, model)
    if query is None:
        return None
    for predicate in filters:
        query = query.filter(predicate)
    return query.first()


def _safe_query(db: Any, model: Any) -> Any | None:
    query_fn = getattr(db, "query", None)
    if query_fn is None:
        return None
    return query_fn(model)


def _model_by_name(name: str) -> Any | None:
    for model in get_registered_model_classes():
        if getattr(model, "__name__", "") == name:
            return model
    return None


def _normalize_tag(value: Any) -> str:
    text = _to_optional_str(value)
    if text is None:
        return "MONITOR"
    return text.replace("_", " ").upper()


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_optional_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None
