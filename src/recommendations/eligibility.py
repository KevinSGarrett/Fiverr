"""Recommendation eligibility and gating helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from src.models import (
    FinalScore,
    GigQualityScore,
    GigVisualAnalysis,
    Keyword,
    KeywordScore,
    Recommendation,
    SearchResult,
    get_registered_model_classes,
)
from src.recommendations.context_builder import get_confidence_modifier

_TAG_ORDER = ["STRONG GO", "CONDITIONAL GO", "MONITOR", "CAUTION", "PASS"]


def get_eligible_keywords(run_id: str, db: Any, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return keywords eligible for recommendation generation in this run."""
    recommendations = config.get("recommendations", {}) if isinstance(config, Mapping) else {}
    min_tag = str(recommendations.get("min_tag", "CONDITIONAL GO"))
    eligible_tags = _canonical_tags_at_or_above(min_tag)
    niche_flags = recommendations.get("niches", {}) if isinstance(recommendations, Mapping) else {}

    rows = _load_ranking_rows(run_id=run_id, db=db)
    eligible: list[dict[str, Any]] = []
    for row in rows:
        keyword_id = _to_optional_int(getattr(row, "keyword_id", None))
        if keyword_id is None or keyword_id <= 0:
            continue

        keyword = _query_first(db, Keyword, Keyword.id == keyword_id)
        if keyword is None:
            continue

        tag = _canonical_tag(getattr(row, "tag", None) or _extract_tag_from_raw(row))
        if tag not in eligible_tags:
            continue

        if _is_recommendation_disabled_for_niche(keyword_niche_id=getattr(keyword, "niche_id", None), flags=niche_flags):
            continue

        final_score = _to_float(
            getattr(row, "final_score", None),
            default=_to_float(getattr(row, "score_at_generation", None), default=0.0),
        )
        eligible.append(
            {
                "keyword_id": keyword_id,
                "keyword_text": str(
                    getattr(keyword, "keyword", None)
                    or getattr(keyword, "keyword_text", None)
                    or ""
                ),
                "niche_id": getattr(keyword, "niche_id", ""),
                "tag": tag,
                "final_score": final_score,
                "confidence_modifier": get_confidence_modifier(keyword_id, db),
                "run_id": run_id,
                "force_recommended": bool(_extract_flag(keyword, "force_recommended")),
            }
        )
    return eligible


def _tags_at_or_above(min_tag: str) -> list[str]:
    """
    Return tags at-or-above `min_tag`.

    For compatibility with older underscore tags, the output style matches input style:
    - "CONDITIONAL GO" -> ["STRONG GO", "CONDITIONAL GO"]
    - "CONDITIONAL_GO" -> ["STRONG_GO", "CONDITIONAL_GO"]
    """
    raw_input = str(min_tag)
    style_uses_underscore = "_" in raw_input or (" " not in raw_input and raw_input.isupper())
    tags = _canonical_tags_at_or_above(min_tag)
    if style_uses_underscore:
        return [tag.replace(" ", "_") for tag in tags]
    return tags


def passes_recommendation_gates(keyword_data: dict[str, Any], db: Any) -> tuple[bool, str]:
    """Evaluate all four recommendation gates defined by the E05 spec."""
    keyword_id = _to_optional_int(keyword_data.get("keyword_id"))
    if keyword_id is None or keyword_id <= 0:
        return False, "Invalid keyword id."

    if bool(keyword_data.get("force_recommended")) or is_keyword_force_recommended(keyword_id, db):
        return True, "User override — forced recommendation"

    confidence_modifier = _to_float(keyword_data.get("confidence_modifier"), default=0.0)
    if confidence_modifier < 0.40:
        return False, "Confidence modifier below 0.40 — data too unreliable for recommendations"

    demand_score = _resolve_demand_score(keyword_id, keyword_data, db)
    if demand_score is None or demand_score <= 20:
        return False, "Demand score missing or below 20 — insufficient buyer interest"

    if not _has_gig_analysis(keyword_id, db):
        return False, "No gig quality analysis available — cannot generate differentiation angle"

    return True, "All gates passed"


def is_keyword_force_recommended(keyword_id: int, db: Any) -> bool:
    """Temporary override stub for user-forced recommendation behavior."""
    del keyword_id, db
    return False


def should_regenerate_recommendation(keyword_id: int, current_final_score: float, db: Any) -> bool:
    """Return True when a recommendation should be regenerated."""
    query = _safe_query(db, Recommendation)
    if query is None:
        return True

    rows = query.filter(Recommendation.keyword_id == keyword_id).order_by(Recommendation.created_at.desc()).all()
    if not rows:
        return True

    existing_complete = next((row for row in rows if _is_generation_complete(row)), None)
    if existing_complete is None:
        return True

    previous_score = _extract_recommendation_score(existing_complete)
    if previous_score is None:
        return True

    return abs(current_final_score - previous_score) >= 5.0


def _load_ranking_rows(run_id: str, db: Any) -> list[Any]:
    ranking_model = _model_by_name("OpportunityRanking")
    if ranking_model is not None:
        ranking_query = _safe_query(db, ranking_model)
        if ranking_query is not None:
            run_column = getattr(ranking_model, "run_id", None)
            if run_column is not None:
                ranking_query = ranking_query.filter(run_column == str(run_id))
            rows = ranking_query.all()
            if rows:
                return rows

    keyword_score_query = _safe_query(db, KeywordScore)
    if keyword_score_query is not None:
        keyword_rows = keyword_score_query.order_by(KeywordScore.scored_at.desc()).all()
        deduped: dict[int, Any] = {}
        for row in keyword_rows:
            keyword_id = _to_optional_int(getattr(row, "keyword_id", None))
            if keyword_id is None or keyword_id in deduped:
                continue
            deduped[keyword_id] = row
        if deduped:
            return list(deduped.values())

    final_score_query = _safe_query(db, FinalScore)
    if final_score_query is None:
        return []
    if str(run_id).isdigit():
        final_score_query = final_score_query.filter(FinalScore.run_id == int(run_id))
    final_rows = final_score_query.order_by(FinalScore.created_at.desc()).all()
    latest: dict[int, Any] = {}
    for row in final_rows:
        keyword_id = _to_optional_int(getattr(row, "keyword_id", None))
        if keyword_id is None or keyword_id in latest:
            continue
        latest[keyword_id] = row
    return list(latest.values())


def _canonical_tags_at_or_above(min_tag: str) -> list[str]:
    normalized = _canonical_tag(min_tag)
    if normalized not in _TAG_ORDER:
        normalized = "CONDITIONAL GO"
    index = _TAG_ORDER.index(normalized)
    return _TAG_ORDER[: index + 1]


def _canonical_tag(tag: Any) -> str:
    raw = str(tag or "").strip().upper().replace("_", " ")
    return raw or "MONITOR"


def _extract_tag_from_raw(row: Any) -> str:
    raw = getattr(row, "raw_json", {})
    if isinstance(raw, dict):
        return _canonical_tag(raw.get("tag"))
    return "MONITOR"


def _extract_confidence_modifier(row: Any) -> float:
    raw = getattr(row, "raw_json", {})
    if isinstance(raw, dict):
        return _to_float(raw.get("confidence_modifier"), default=1.0)
    return 1.0


def _is_recommendation_disabled_for_niche(keyword_niche_id: Any, flags: Any) -> bool:
    if not isinstance(flags, Mapping):
        return False
    niche_flag = flags.get(str(keyword_niche_id), flags.get(keyword_niche_id))
    return isinstance(niche_flag, Mapping) and niche_flag.get("recommendation_generation") is False


def _extract_flag(keyword: Keyword, key: str) -> Any:
    metadata = keyword.metadata_json if isinstance(keyword.metadata_json, dict) else {}
    return metadata.get(key)


def _resolve_demand_score(keyword_id: int, keyword_data: dict[str, Any], db: Any) -> float | None:
    explicit_demand = _to_optional_float(keyword_data.get("demand_score"))
    if explicit_demand is not None:
        return explicit_demand

    keyword_score_model = _model_by_name("KeywordScore") or KeywordScore
    keyword_query = _safe_query(db, keyword_score_model)
    keyword_row = None
    if keyword_query is not None:
        keyword_row = keyword_query.filter(keyword_score_model.keyword_id == keyword_id).first()
    if keyword_row is not None:
        keyword_score_demand = _to_optional_float(getattr(keyword_row, "demand_score", None))
        if keyword_score_demand is not None:
            return keyword_score_demand

    final_row = _query_latest_final_score(keyword_id, db)
    raw = getattr(final_row, "raw_json", {}) if final_row is not None else {}
    if isinstance(raw, dict):
        return _to_optional_float(raw.get("demand_score"))
    return None


def _has_gig_analysis(keyword_id: int, db: Any) -> bool:
    gig_quality_model = _model_by_name("GigQualityScore") or GigQualityScore
    query = _safe_query(db, gig_quality_model)
    if query is not None:
        count = (
            query.filter(
                gig_quality_model.keyword_id == keyword_id,
                gig_quality_model.analysis_complete.is_(True),
            )
            .count()
        )
        if count > 0:
            return True

    fallback_query = _safe_query(db, GigVisualAnalysis)
    if fallback_query is None:
        return False
    count = (
        fallback_query.join(SearchResult, SearchResult.gig_id == GigVisualAnalysis.gig_id)
        .filter(SearchResult.keyword_id == keyword_id)
        .count()
    )
    return count > 0


def _is_generation_complete(row: Any) -> bool:
    explicit = getattr(row, "generation_complete", None)
    if isinstance(explicit, bool):
        return explicit
    raw = getattr(row, "raw_json", {})
    if isinstance(raw, dict) and "generation_complete" in raw:
        return bool(raw.get("generation_complete"))
    return True


def _extract_recommendation_score(row: Any) -> float | None:
    for value in (
        getattr(row, "score_at_generation", None),
        getattr(row, "final_score", None),
        getattr(row, "confidence", None),
    ):
        parsed = _to_optional_float(value)
        if parsed is not None:
            return parsed

    raw = getattr(row, "raw_json", {})
    if isinstance(raw, dict):
        return _to_optional_float(raw.get("final_score"))
    return None


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


def _query_first(db: Any, model: Any, *predicates: Any) -> Any | None:
    query = _safe_query(db, model)
    if query is None:
        return None
    for predicate in predicates:
        query = query.filter(predicate)
    return query.first()


def _safe_query(db: Any, model: Any) -> Any | None:
    query_fn = getattr(db, "query", None)
    if query_fn is None:
        return None
    return query_fn(model)


def _model_by_name(name: str) -> Any | None:
    for cls in get_registered_model_classes():
        if cls.__name__ == name:
            return cls
    return None


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


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
