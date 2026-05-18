"""Recommendation context model and builder."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

from src.models import (
    AnalysisResult,
    CompetitorSnapshot,
    ExternalSignal,
    FinalScore,
    Keyword,
    Niche,
    Review,
    ScoreComponent,
    SearchResult,
)


class RecommendationContext(BaseModel):
    """Shared source-traceable context for recommendation generation tasks."""

    keyword_id: int
    keyword_text: str
    niche_id: int | str
    niche_name: str
    tag: str
    final_score: float
    demand_score: float | None = None
    competition_score: float | None = None
    opportunity_score: float | None = None
    feasibility_score: float | None = None
    profitability_score: float | None = None
    score_components: dict[str, Any] = Field(default_factory=dict)
    top_competitor_weaknesses: list[dict[str, Any]] = Field(default_factory=list)
    cluster_synthesis_narrative: str | None = None
    entry_feasibility_rating: float | None = None
    dominant_sellers: list[dict[str, Any]] | None = None
    positioning_gaps: list[dict[str, Any]] | None = None
    top_buyer_complaints: list[str] = Field(default_factory=list)
    top_buyer_praise: list[str] = Field(default_factory=list)
    red_flag_patterns: list[str] = Field(default_factory=list)
    starter_price_basic: int = 0
    starter_price_standard: int = 0
    starter_price_premium: int = 0
    hard_exclusions: list[str] = Field(default_factory=list)
    total_result_count: int | None = None
    trends_slope: str | None = None
    reddit_intent_score: float | None = None
    cluster_label: str | None = None
    opportunity_narrative: str | None = None


def build_recommendation_context(keyword_id: int, db: Any, config: Mapping[str, Any]) -> RecommendationContext:
    """Build recommendation context with graceful fallbacks for sparse data."""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if keyword is None:
        return RecommendationContext(
            keyword_id=keyword_id,
            keyword_text="",
            niche_id=0,
            niche_name="Unknown",
            tag="MONITOR",
            final_score=0.0,
        )

    niche = db.query(Niche).filter(Niche.id == keyword.niche_id).first()
    latest_final = (
        db.query(FinalScore)
        .filter(FinalScore.keyword_id == keyword_id)
        .order_by(FinalScore.created_at.desc())
        .first()
    )
    latest_snapshot = (
        db.query(CompetitorSnapshot)
        .filter(CompetitorSnapshot.keyword_id == keyword_id)
        .order_by(CompetitorSnapshot.created_at.desc())
        .first()
    )
    top_snapshots = (
        db.query(CompetitorSnapshot)
        .filter(CompetitorSnapshot.keyword_id == keyword_id)
        .order_by(CompetitorSnapshot.created_at.desc())
        .all()
    )
    review_rows = (
        db.query(Review)
        .join(SearchResult, SearchResult.gig_id == Review.gig_id)
        .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
        .all()
    )
    component_rows = db.query(ScoreComponent).filter(ScoreComponent.keyword_id == keyword_id).all()
    search_result_count = db.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).count()
    trends_signal = (
        db.query(ExternalSignal)
        .filter(
            ExternalSignal.keyword_id == keyword_id,
            ExternalSignal.signal_type == "google_trends",
        )
        .order_by(ExternalSignal.created_at.desc())
        .first()
    )
    reddit_signal = (
        db.query(ExternalSignal)
        .filter(
            ExternalSignal.keyword_id == keyword_id,
            ExternalSignal.signal_type == "reddit_demand",
        )
        .order_by(ExternalSignal.created_at.desc())
        .first()
    )
    cluster_result = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.keyword_id == keyword_id,
            AnalysisResult.analysis_type.in_(["cluster_synthesis", "opportunity_cluster"]),
        )
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )

    final_raw = latest_final.raw_json if latest_final and isinstance(latest_final.raw_json, dict) else {}
    score_components = _score_component_payload(component_rows, final_raw)
    snapshot_json = latest_snapshot.snapshot_json if latest_snapshot and isinstance(latest_snapshot.snapshot_json, dict) else {}
    trends_raw = trends_signal.raw_value_json if trends_signal and isinstance(trends_signal.raw_value_json, dict) else {}
    reddit_raw = reddit_signal.raw_value_json if reddit_signal and isinstance(reddit_signal.raw_value_json, dict) else {}
    cluster_raw = cluster_result.raw_json if cluster_result and isinstance(cluster_result.raw_json, dict) else {}
    niche_settings = _resolve_niche_settings(config, keyword.niche_id)

    return RecommendationContext(
        keyword_id=keyword.id,
        keyword_text=keyword.keyword,
        niche_id=keyword.niche_id,
        niche_name=niche.name if niche else str(keyword.niche_id),
        tag=_to_str(final_raw.get("tag"), default="MONITOR"),
        final_score=_to_float(latest_final.final_score if latest_final else final_raw.get("final_score"), default=0.0),
        demand_score=_to_opt_float(final_raw.get("demand_score")),
        competition_score=_to_opt_float(final_raw.get("competition_score")),
        opportunity_score=_to_opt_float(final_raw.get("opportunity_score")),
        feasibility_score=_to_opt_float(final_raw.get("feasibility_score")),
        profitability_score=_to_opt_float(final_raw.get("profitability_score")),
        score_components=score_components,
        top_competitor_weaknesses=_extract_top_weaknesses(top_snapshots),
        cluster_synthesis_narrative=_to_opt_str(snapshot_json.get("synthesis_narrative")),
        entry_feasibility_rating=_to_opt_float(snapshot_json.get("entry_feasibility_rating")),
        dominant_sellers=_to_opt_list_of_dict(snapshot_json.get("dominant_sellers")),
        positioning_gaps=_to_opt_list_of_dict(snapshot_json.get("positioning_gaps")),
        top_buyer_complaints=_extract_review_bucket(review_rows, "complaint"),
        top_buyer_praise=_extract_review_bucket(review_rows, "praise"),
        red_flag_patterns=_extract_red_flags(snapshot_json),
        starter_price_basic=_to_int(niche_settings.get("starter_price_basic"), default=0),
        starter_price_standard=_to_int(niche_settings.get("starter_price_standard"), default=0),
        starter_price_premium=_to_int(niche_settings.get("starter_price_premium"), default=0),
        hard_exclusions=_to_list_of_str(niche_settings.get("hard_exclusions")),
        total_result_count=search_result_count if search_result_count > 0 else None,
        trends_slope=_to_opt_str(trends_raw.get("google_trends_slope") or trends_raw.get("trends_slope")),
        reddit_intent_score=_to_opt_float(
            reddit_raw.get("reddit_demand_intent_score") or reddit_raw.get("reddit_intent_score")
        ),
        cluster_label=_to_opt_str(cluster_raw.get("cluster_label")),
        opportunity_narrative=_to_opt_str(cluster_raw.get("opportunity_narrative")),
    )


def _score_component_payload(component_rows: list[ScoreComponent], final_raw: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for row in component_rows:
        payload[row.score_name] = {
            "score_value": row.score_value,
            "weight": row.weight,
            "explanation": row.explanation,
        }
    if not payload and isinstance(final_raw.get("score_components"), dict):
        payload = dict(final_raw["score_components"])
    return payload


def _extract_top_weaknesses(snapshots: list[CompetitorSnapshot]) -> list[dict[str, Any]]:
    weaknesses: list[dict[str, Any]] = []
    for snapshot in snapshots[:5]:
        payload = snapshot.snapshot_json if isinstance(snapshot.snapshot_json, dict) else {}
        item = payload.get("weaknesses")
        if isinstance(item, list):
            weaknesses.append(
                {
                    "gig_title": payload.get("gig_title") or payload.get("title") or "",
                    "weaknesses": item,
                }
            )
    return weaknesses


def _extract_review_bucket(review_rows: list[Review], bucket: str) -> list[str]:
    values: list[str] = []
    for row in review_rows:
        text = row.review_text or ""
        lowered = text.lower()
        if bucket == "complaint" and any(word in lowered for word in ("bad", "poor", "late", "issue", "problem")):
            values.append(text)
        if bucket == "praise" and any(word in lowered for word in ("great", "excellent", "fast", "amazing", "good")):
            values.append(text)
    return values[:5]


def _extract_red_flags(snapshot_json: dict[str, Any]) -> list[str]:
    value = snapshot_json.get("red_flag_patterns") or snapshot_json.get("risks")
    return _to_list_of_str(value)


def _resolve_niche_settings(config: Mapping[str, Any], niche_id: int | str) -> Mapping[str, Any]:
    recommendations = config.get("recommendations", {}) if isinstance(config, Mapping) else {}
    niches = recommendations.get("niches", {}) if isinstance(recommendations, Mapping) else {}
    resolved = niches.get(str(niche_id)) or niches.get(niche_id)
    return resolved if isinstance(resolved, Mapping) else {}


def _to_opt_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_str(value: Any, *, default: str) -> str:
    text = _to_opt_str(value)
    return text if text is not None else default


def _to_opt_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any, *, default: float) -> float:
    parsed = _to_opt_float(value)
    return parsed if parsed is not None else default


def _to_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _to_opt_list_of_dict(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    result = [item for item in value if isinstance(item, dict)]
    return result or None
