"""Recommendation eligibility and gating helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from src.models import (
    CompetitorSnapshot,
    FinalScore,
    GigVisualAnalysis,
    Keyword,
    Recommendation,
    SearchResult,
    get_registered_model_classes,
)

_TAG_ORDER = ["STRONG_GO", "CONDITIONAL_GO", "MONITOR", "CAUTION", "PASS"]


def get_eligible_keywords(run_id: str, db: Any, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return keyword rows eligible for recommendation generation."""
    min_tag = str(config.get("recommendations", {}).get("min_tag", "CONDITIONAL_GO"))
    eligible_tags = _tags_at_or_above(min_tag)
    recommendation_flags = config.get("recommendations", {}).get("niches", {})

    ranking_model = _model_by_name("OpportunityRanking")
    rows: list[Any]
    if ranking_model is not None:
        rows = (
            db.query(ranking_model)
            .filter(ranking_model.run_id == run_id, ranking_model.tag.in_(eligible_tags))
            .all()
        )
    else:
        final_score_query = db.query(FinalScore)
        if str(run_id).isdigit():
            final_score_query = final_score_query.filter(FinalScore.run_id == int(run_id))
        fallback_rows = final_score_query.order_by(FinalScore.created_at.desc()).all()
        latest_by_keyword: dict[int, Any] = {}
        for row in fallback_rows:
            keyword_id = int(getattr(row, "keyword_id", 0) or 0)
            if keyword_id <= 0 or keyword_id in latest_by_keyword:
                continue
            latest_by_keyword[keyword_id] = row
        rows = list(latest_by_keyword.values())

    eligible: list[dict[str, Any]] = []
    for row in rows:
        keyword_id = int(getattr(row, "keyword_id", 0) or 0)
        if keyword_id <= 0:
            continue
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword is None:
            continue
        final_score = _to_float(getattr(row, "final_score", None), default=0.0)
        tag = _normalize_tag(getattr(row, "tag", None) or _extract_tag_from_raw(row))
        if tag not in eligible_tags:
            continue
        niche_cfg = recommendation_flags.get(str(keyword.niche_id), {})
        if isinstance(niche_cfg, Mapping) and niche_cfg.get("recommendation_generation") is False:
            continue
        eligible.append(
            {
                "keyword_id": keyword.id,
                "keyword_text": keyword.keyword,
                "niche_id": keyword.niche_id,
                "tag": tag,
                "final_score": final_score,
                "confidence_modifier": _extract_confidence_modifier(row),
                "force_recommended": bool(_extract_flag(keyword, "force_recommended")),
                "run_id": run_id,
            }
        )
    return eligible


def _tags_at_or_above(min_tag: str) -> list[str]:
    normalized = _normalize_tag(min_tag)
    if normalized not in _TAG_ORDER:
        normalized = "CONDITIONAL_GO"
    idx = _TAG_ORDER.index(normalized)
    return _TAG_ORDER[: idx + 1]


def passes_recommendation_gates(keyword_data: dict[str, Any], db: Any) -> tuple[bool, str]:
    """Evaluate recommendation gating checks."""
    keyword_id = int(keyword_data.get("keyword_id", 0))
    if keyword_id <= 0:
        return False, "Invalid keyword id."

    if bool(keyword_data.get("force_recommended")):
        return True, "User override — forced recommendation"

    confidence_modifier = _to_float(keyword_data.get("confidence_modifier"), default=0.0)
    if confidence_modifier < 0.40:
        return False, "Confidence modifier below 0.40 — data too unreliable for recommendations"

    demand_score = _resolve_demand_score(keyword_id, keyword_data, db)
    if demand_score is None or demand_score < 20:
        return False, "Demand score missing or below 20 — insufficient buyer interest"

    if not _has_gig_analysis(keyword_id, db):
        return False, "No gig quality analysis available — cannot generate differentiation angle"

    return True, "All gates passed"


def should_regenerate_recommendation(keyword_id: int, current_final_score: float, db: Any) -> bool:
    """Return true when recommendation should be regenerated for this keyword."""
    existing = (
        db.query(Recommendation)
        .filter(Recommendation.keyword_id == keyword_id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
    if existing is None:
        return True

    raw = existing.raw_json if isinstance(existing.raw_json, dict) else {}
    generation_complete = bool(raw.get("generation_complete", True))
    if not generation_complete:
        return True

    previous_score = _to_float(raw.get("final_score"), default=_to_float(getattr(existing, "confidence", 0.0), 0.0))
    if abs(current_final_score - previous_score) > 5.0:
        return True

    latest_competitor = (
        db.query(CompetitorSnapshot)
        .filter(CompetitorSnapshot.keyword_id == keyword_id)
        .order_by(CompetitorSnapshot.created_at.desc())
        .first()
    )
    existing_time = _coerce_datetime(raw.get("generated_at")) or getattr(existing, "created_at", None)
    latest_competitor_time = getattr(latest_competitor, "created_at", None)
    if existing_time is not None and latest_competitor_time is not None and latest_competitor_time > existing_time:
        return True

    return False


def _model_by_name(name: str) -> Any | None:
    for cls in get_registered_model_classes():
        if cls.__name__ == name:
            return cls
    return None


def _normalize_tag(tag: Any) -> str:
    value = str(tag or "").strip().upper().replace(" ", "_")
    return value or "MONITOR"


def _extract_tag_from_raw(row: Any) -> str:
    raw = getattr(row, "raw_json", {})
    if isinstance(raw, dict):
        return _normalize_tag(raw.get("tag"))
    return "MONITOR"


def _extract_confidence_modifier(row: Any) -> float:
    raw = getattr(row, "raw_json", {})
    if isinstance(raw, dict):
        return _to_float(raw.get("confidence_modifier"), default=1.0)
    return 1.0


def _extract_flag(keyword: Keyword, key: str) -> Any:
    meta = keyword.metadata_json if isinstance(keyword.metadata_json, dict) else {}
    return meta.get(key)


def _resolve_demand_score(keyword_id: int, keyword_data: dict[str, Any], db: Any) -> float | None:
    if keyword_data.get("demand_score") is not None:
        return _to_float(keyword_data["demand_score"], default=0.0)
    keyword_score_model = _model_by_name("KeywordScore")
    if keyword_score_model is not None:
        row = db.query(keyword_score_model).filter(keyword_score_model.keyword_id == keyword_id).first()
        if row is not None:
            return _to_float(getattr(row, "demand_score", None), default=0.0)
    final_row = (
        db.query(FinalScore)
        .filter(FinalScore.keyword_id == keyword_id)
        .order_by(FinalScore.created_at.desc())
        .first()
    )
    raw = final_row.raw_json if final_row and isinstance(final_row.raw_json, dict) else {}
    return _to_float(raw.get("demand_score"), default=0.0) if raw else None


def _has_gig_analysis(keyword_id: int, db: Any) -> bool:
    gig_quality_model = _model_by_name("GigQualityScore")
    if gig_quality_model is not None:
        count = (
            db.query(gig_quality_model)
            .filter(gig_quality_model.keyword_id == keyword_id, gig_quality_model.analysis_complete.is_(True))
            .count()
        )
        return count > 0
    # Fallback: visual analysis records indicate at least one analyzed gig.
    count = (
        db.query(GigVisualAnalysis)
        .join(SearchResult, SearchResult.gig_id == GigVisualAnalysis.gig_id)
        .filter(SearchResult.keyword_id == keyword_id)
        .count()
    )
    return count > 0


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
