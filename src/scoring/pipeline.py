"""Async scoring pipeline wiring for keyword-level scoring and persistence."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from sqlalchemy.orm import Session

from src.analysis.llm_relevance_classifier import LLMRelevanceClassifier, LLMRelevanceConfig
from src.models import ExternalSignal, Gig, Keyword, SearchResult
from src.models.keyword_score import KeywordScore
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.contracts import ScoreComponent
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.final import FinalRecommendationScoreCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.result_set_relevance import get_result_set_validation
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator

logger = logging.getLogger(__name__)


def _normalized_profile(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return dict(weights)
    return {name: (value / total) for name, value in weights.items()}


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

DEPTH_SCORE_AVAILABILITY: dict[str, list[int]] = {
    "full": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "standard": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "feasibility": [1, 2, 3, 4, 5, 11],
    "keyword_only": [1, 2, 3, 11],
}

DEPTH_LABELS: dict[str, str] = {
    "full": "all_11",
    "standard": "all_11",
    "feasibility": "scores_1_to_5",
    "keyword_only": "scores_1_to_3",
}

OPPORTUNITY_TAGS: list[tuple[str, float, float]] = [
    ("STRONG_GO", 80.0, 100.0),
    ("CONDITIONAL_GO", 60.0, 80.0),
    ("MONITOR", 40.0, 60.0),
    ("CAUTION", 20.0, 40.0),
    ("PASS", 0.0, 20.0),
]

_AUTO_RECOMMENDATION_TAGS = {"STRONG_GO", "CONDITIONAL_GO"}

SCORING_PROFILES: dict[str, dict[str, float]] = {
    "default": _normalized_profile({
        "demand": 0.20,
        "competition_inv": 0.20,
        "opportunity": 0.25,
        "feasibility": 0.15,
        "profitability": 0.10,
        "intent": 0.10,
        "saturation_inv": 0.05,
        "weakness": 0.10,
        "trend": 0.05,
    }),
    "aggressive_new_seller": _normalized_profile({
        "feasibility": 0.25,
        "weakness": 0.20,
        "opportunity": 0.20,
        "demand": 0.15,
        "competition_inv": 0.10,
        "profitability": 0.05,
        "intent": 0.05,
        "saturation_inv": 0.00,
        "trend": 0.00,
    }),
    "profitability_focus": _normalized_profile({
        "profitability": 0.25,
        "intent": 0.20,
        "opportunity": 0.20,
        "demand": 0.15,
        "competition_inv": 0.10,
        "feasibility": 0.05,
        "weakness": 0.05,
        "saturation_inv": 0.00,
        "trend": 0.00,
    }),
    "trend_chaser": _normalized_profile({
        "trend": 0.25,
        "demand": 0.25,
        "opportunity": 0.20,
        "competition_inv": 0.15,
        "feasibility": 0.10,
        "profitability": 0.05,
        "intent": 0.00,
        "weakness": 0.00,
        "saturation_inv": 0.00,
    }),
}

_SCORE_TO_PROFILE_KEY: dict[str, str] = {
    "demand_score": "demand",
    "competition_score": "competition_inv",
    "opportunity_score": "opportunity",
    "feasibility_score": "feasibility",
    "profitability_score": "profitability",
    "intent_score": "intent",
    "saturation_score": "saturation_inv",
    "weakness_score": "weakness",
    "trend_score": "trend",
}

_SIDE_CAR_DIR = Path("data/scoring_results")


def validate_scoring_profile(profile_name: str, weights: dict[str, float]) -> None:
    """Raise ValueError when profile weights are not approximately 1.0."""
    total = sum(weights.values())
    if not (0.999 <= total <= 1.001):
        raise ValueError(
            f"Scoring profile '{profile_name}' weights sum to {total:.4f}, must equal 1.0."
        )


def calculate_weighted_composite(
    scores: dict[str, float | None],
    profile_weights: dict[str, float],
) -> tuple[float, dict[str, dict[str, Any]]]:
    """Calculate weighted composite and detailed score components."""
    weighted_sum = 0.0
    weight_used = 0.0
    components: dict[str, dict[str, Any]] = {}

    for score_field, weight_key in _SCORE_TO_PROFILE_KEY.items():
        weight = profile_weights.get(weight_key, 0.0)
        score_value = scores.get(score_field)
        if weight == 0.0:
            continue
        if score_value is None:
            components[score_field] = {
                "value": None,
                "effective_value": None,
                "weight": weight,
                "contribution": None,
            }
            continue

        effective_value = 100.0 - score_value if weight_key in {"competition_inv", "saturation_inv"} else score_value
        contribution = effective_value * weight
        weighted_sum += contribution
        weight_used += weight
        components[score_field] = {
            "value": round(score_value, 2),
            "effective_value": round(effective_value, 2),
            "weight": weight,
            "contribution": round(contribution, 2),
        }

    if weight_used < 0.50:
        return 0.0, components
    composite = weighted_sum / weight_used
    clamped = min(100.0, max(0.0, composite))
    return round(clamped, 2), components


def calculate_final_score(
    weighted_composite: float,
    confidence_modifier: float,
    confidence_floor: float = 0.20,
) -> float:
    """Apply confidence modifier floor and return final clamped score."""
    effective_modifier = max(confidence_modifier, confidence_floor)
    final_score = weighted_composite * effective_modifier
    return round(min(100.0, max(0.0, final_score)), 2)


def assign_tag(final_score: float, confidence_modifier: float) -> str:
    """Return recommendation tag and demote one tier for low confidence."""
    base_tag = "PASS"
    for tag, low, high in OPPORTUNITY_TAGS:
        in_range = low <= final_score < high
        if in_range or (tag == "STRONG_GO" and final_score >= high):
            base_tag = tag
            break

    if confidence_modifier < 0.5:
        demotion_map = {
            "STRONG_GO": "CONDITIONAL_GO",
            "CONDITIONAL_GO": "MONITOR",
            "MONITOR": "CAUTION",
            "CAUTION": "PASS",
            "PASS": "PASS",
        }
        return demotion_map[base_tag]
    return base_tag


def _demote_tag_for_ghost_market(keyword_id: int, tag: str, db: Any) -> str:
    rsv = get_result_set_validation(keyword_id, db)
    if rsv is not None and bool(rsv.ghost_market_flag):
        return "PASS"
    return tag


def detect_red_flags_from_scores(
    scores: dict[str, float | None],
    components: dict[str, Any],
    keyword_id: int,
    db: Any,
) -> list[dict[str, str]]:
    """Return score-derived red flags for downstream recommendation gating."""
    del keyword_id, db
    flags: list[dict[str, str]] = []
    competition_score = scores.get("competition_score")
    demand_score = scores.get("demand_score")
    trend_score = scores.get("trend_score")
    confidence_modifier = float(components.get("confidence_modifier", 1.0))

    if competition_score is not None and competition_score > 75:
        flags.append(
            {"flag": "High competition barrier", "severity": "HIGH", "source": "competition_score"}
        )
    if confidence_modifier < 0.4:
        flags.append(
            {
                "flag": "Low confidence — insufficient data",
                "severity": "HIGH",
                "source": "confidence_modifier",
            }
        )
    if demand_score is not None and demand_score < 20:
        flags.append({"flag": "Low demand signal", "severity": "MEDIUM", "source": "demand_score"})
    if trend_score is not None and trend_score < 25:
        flags.append(
            {"flag": "Declining trend detected", "severity": "MEDIUM", "source": "trend_score"}
        )
    return flags


def _apply_weakness_feedback_to_feasibility(
    feasibility_result: Any | None,
    weakness_result: Any | None,
) -> None:
    """
    Adjust Score 4 using Score 8 output.

    Lower weakness_score values (stronger competitors) raise feasibility slightly, while
    higher weakness_score values reduce it. This keeps Score 4 responsive to Score 8
    without replacing the core feasibility inputs.
    """
    if feasibility_result is None or weakness_result is None:
        return

    feasibility_score = _score_value(feasibility_result)
    weakness_score = _score_value(weakness_result)
    if feasibility_score is None or weakness_score is None:
        return

    # Center around 50 to keep adjustment bounded to +/- 7.5 points.
    adjustment = round((50.0 - weakness_score) * 0.15, 2)
    adjusted_score = round(min(100.0, max(0.0, feasibility_score + adjustment)), 2)
    feasibility_result.score_value = adjusted_score

    score_components = getattr(feasibility_result, "score_components", None)
    if isinstance(score_components, dict):
        score_components["weakness_feedback"] = ScoreComponent(
            value=adjusted_score,
            weight=0.0,
            raw={"weakness_score": weakness_score, "adjustment": adjustment},
            note="Score 4 adjusted using Score 8 weakness signal.",
        )

    source_evidence = getattr(feasibility_result, "source_evidence", None)
    if isinstance(source_evidence, list):
        source_evidence.append("score8.weakness_score")


async def score_keyword(
    keyword_id: int,
    profile_name: str,
    db: Any,
    llm_client: Any,
    cache: Any,
    config: dict[str, Any] | None = None,
    llm_relevance_classifier: LLMRelevanceClassifier | None = None,
) -> dict[str, Any]:
    """Run full keyword scoring pipeline, compute final score, and persist result."""
    profile_weights = SCORING_PROFILES.get(profile_name)
    if profile_weights is None:
        raise ValueError(f"Unknown scoring profile: {profile_name}")
    validate_scoring_profile(profile_name, profile_weights)

    depth = _resolve_depth(keyword_id, db)
    available_scores = DEPTH_SCORE_AVAILABILITY.get(depth, DEPTH_SCORE_AVAILABILITY["standard"])

    demand_calculator = DemandScoreCalculator()
    competition_calculator = CompetitionScoreCalculator()
    opportunity_calculator = OpportunityScoreCalculator(
        demand_calculator=demand_calculator,
        competition_calculator=competition_calculator,
    )
    feasibility_calculator = NewSellerFeasibilityCalculator()
    profitability_calculator = ProfitabilityScoreCalculator()
    intent_calculator = ConversionIntentScoreCalculator()
    saturation_calculator = SaturationScoreCalculator()
    weakness_calculator = GigQualityWeaknessScoreCalculator()
    trend_calculator = TrendScoreCalculator()
    confidence_modifier_calculator = ConfidenceScoreModifier()
    final_calculator = FinalRecommendationScoreCalculator()

    source_evidence: list[str] = []
    missing_data_warnings: list[str] = []

    # Stage 8.5 — R7 External Signal Qualifiers (toggle: external_signals_enabled)
    # Qualifier application lives in demand/confidence calculators and is gated by
    # config.analysis.external_signals_enabled.
    demand_result = demand_calculator.calculate(keyword_id, db, config=config) if 1 in available_scores else None
    competition_result = (
        competition_calculator.calculate(keyword_id, db, config=config) if 2 in available_scores else None
    )
    opportunity_result = None
    if 3 in available_scores:
        opportunity_result = opportunity_calculator.calculate(
            keyword_id=keyword_id,
            db=db,
            demand_result=demand_result,
            competition_result=competition_result,
            config=config,
        )
    feasibility_result = (
        feasibility_calculator.calculate(keyword_id, db, config=config) if 4 in available_scores else None
    )
    profitability_result = (
        profitability_calculator.calculate(keyword_id, db, config=config) if 5 in available_scores else None
    )
    intent_result = intent_calculator.calculate(keyword_id, db, config=config) if 6 in available_scores else None
    saturation_result = (
        saturation_calculator.calculate(keyword_id, db, config=config) if 7 in available_scores else None
    )
    weakness_result = weakness_calculator.calculate(keyword_id, db) if 8 in available_scores else None
    _apply_weakness_feedback_to_feasibility(feasibility_result, weakness_result)
    trend_result = trend_calculator.calculate(keyword_id, db) if 9 in available_scores else None

    llm_relevance_verdict: str | None = None
    if llm_relevance_classifier is not None:
        # Stage 7.5 wiring: run after core scoring signals are computed and before reporting output.
        llm_relevance_verdict = llm_relevance_classifier.classify_keyword(session=db, keyword_id=keyword_id)

    for result in (
        demand_result,
        competition_result,
        opportunity_result,
        feasibility_result,
        profitability_result,
        intent_result,
        saturation_result,
        weakness_result,
        trend_result,
    ):
        if result is None:
            continue
        source_evidence.extend(result.source_evidence)
        missing_data_warnings.extend(result.missing_data_warnings)

    scores: dict[str, float | None] = {
        "demand_score": _score_value(demand_result),
        "competition_score": _score_value(competition_result),
        "opportunity_score": _score_value(opportunity_result),
        "feasibility_score": _score_value(feasibility_result),
        "profitability_score": _score_value(profitability_result),
        "intent_score": _score_value(intent_result),
        "saturation_score": _score_value(saturation_result),
        "weakness_score": _score_value(weakness_result),
        "trend_score": _score_value(trend_result),
    }

    confidence_context = _build_confidence_context(
        keyword_id=keyword_id,
        scores=scores,
        depth=depth,
        warnings=missing_data_warnings,
        db=db,
        config=config,
    )
    confidence_modifier = confidence_modifier_calculator.calculate(keyword_id, confidence_context, db)
    confidence_breakdown = dict(confidence_modifier_calculator.last_breakdown)

    weighted_composite, score_components = calculate_weighted_composite(scores, profile_weights)
    if llm_relevance_verdict is not None:
        score_components["_stage_7_5_llm_relevance"] = {
            "value": llm_relevance_verdict,
            "weight": 0.0,
            "contribution": None,
            "note": "Stage 7.5 LLM relevance verdict applied for ambiguous RSV band.",
        }
    if demand_result is not None and "cluster_boost" in demand_result.score_components:
        cluster_component = demand_result.score_components["cluster_boost"]
        score_components["_demand_score_details"] = {
            "value": round(cluster_component.value, 2),
            "weight": 0.0,
            "contribution": None,
            "note": cluster_component.note,
            "raw": cluster_component.raw,
        }
    calculated_final_score = calculate_final_score(weighted_composite, confidence_modifier)
    final_payload = final_calculator.calculate(
        keyword_id=keyword_id,
        profile=profile_name,
        db={
            keyword_id: {
                **scores,
                "confidence_modifier": confidence_modifier,
            }
        },
    )
    final_score = calculated_final_score
    tag = assign_tag(final_score, confidence_modifier)
    tag = _demote_tag_for_ghost_market(keyword_id, tag, db)
    explanation_scores = {
        **scores,
        "confidence_modifier": confidence_modifier,
        "scoring_profile": profile_name,
    }
    keyword_text, niche_id = _resolve_keyword_context(keyword_id=keyword_id, db=db)
    explanation_text = await generate_score_explanation(
        keyword_id=keyword_id,
        keyword_text=keyword_text,
        scores=explanation_scores,
        components=score_components,
        final_score=final_score,
        tag=tag,
        llm_client=llm_client,
        cache=cache,
    )
    red_flags = detect_red_flags_from_scores(
        scores=scores,
        components={"confidence_modifier": confidence_modifier, **confidence_breakdown},
        keyword_id=keyword_id,
        db=db,
    )
    score_depth = DEPTH_LABELS.get(depth, DEPTH_LABELS["standard"])
    persisted = write_keyword_score(
        keyword_id=keyword_id,
        scores=scores,
        weighted_composite=weighted_composite,
        confidence_modifier=confidence_modifier,
        final_score=final_score,
        tag=tag,
        score_components=score_components,
        confidence_breakdown=confidence_breakdown,
        explanation_text=explanation_text,
        red_flags=red_flags,
        scoring_profile=profile_name,
        score_depth=score_depth,
        integrity_fields={
            "trc_reliability": getattr(demand_result, "trc_reliability", None),
            "opportunity_relevance_factor": getattr(opportunity_result, "opportunity_relevance_factor", None),
            "price_outliers_excluded": _as_optional_int(getattr(competition_result, "price_outliers_excluded", None)),
            "clean_gig_count": _as_optional_int(getattr(feasibility_result, "clean_gig_count", None)),
            "competitor_profile_source": getattr(competition_result, "competitor_profile_source", None),
        },
        db=db,
    )
    await _maybe_auto_generate_recommendation(
        keyword_id=keyword_id,
        keyword_text=keyword_text,
        niche_id=niche_id,
        tag=tag,
        final_score=final_score,
        scores=scores,
        score_components=score_components,
        db=db,
        llm_client=llm_client,
        cache=cache,
        config=config,
    )

    return {
        "keyword_id": keyword_id,
        "keyword_text": keyword_text,
        "niche_id": niche_id,
        "scoring_profile": profile_name,
        "score_depth": score_depth,
        "scores": scores,
        "weighted_composite": weighted_composite,
        "confidence_modifier": confidence_modifier,
        "final_score": final_score,
        "tag": tag,
        "llm_relevance_verdict": llm_relevance_verdict,
        "final_payload": final_payload,
        "score_components": score_components,
        "confidence_breakdown": confidence_breakdown,
        "explanation_text": explanation_text,
        "red_flags": red_flags,
        "missing_data_warnings": missing_data_warnings,
        "source_evidence": source_evidence,
        "persisted": persisted,
    }


async def score_keyword_batch(
    keyword_ids: list[int],
    profile_name: str,
    db: Any,
    llm_client: Any,
    cache: Any,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Sequentially score keywords and return per-keyword success/failure payloads."""
    if not keyword_ids:
        return []

    llm_relevance_classifier = _build_llm_relevance_classifier(config=config, db=db)
    results: list[dict[str, Any]] = []
    for keyword_id in keyword_ids:
        try:
            score_kwargs: dict[str, Any] = {
                "keyword_id": keyword_id,
                "profile_name": profile_name,
                "db": db,
                "llm_client": llm_client,
                "cache": cache,
                "config": config,
            }
            if llm_relevance_classifier is not None:
                score_kwargs["llm_relevance_classifier"] = llm_relevance_classifier
            result = await score_keyword(
                **score_kwargs,
            )
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Scoring failed for keyword %s", keyword_id)
            results.append(
                {
                    "keyword_id": keyword_id,
                    "error": str(exc),
                    "final_score": 0.0,
                    "tag": "PASS",
                    "persisted": False,
                }
            )
    return results


async def run_scoring_pipeline(
    keyword_ids: list[int],
    profile_name: str,
    db: Any,
    llm_client: Any,
    cache: Any,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper for batch scoring orchestration imports."""
    return await score_keyword_batch(
        keyword_ids=keyword_ids,
        profile_name=profile_name,
        db=db,
        llm_client=llm_client,
        cache=cache,
        config=config,
    )


def _build_llm_relevance_classifier(
    config: dict[str, Any] | None,
    db: Any,
) -> LLMRelevanceClassifier | None:
    if not isinstance(config, dict) or not isinstance(db, Session):
        return None
    relevance_cfg = config.get("relevance", {})
    if not isinstance(relevance_cfg, dict):
        return None
    llm_cfg = LLMRelevanceConfig.from_relevance_config(relevance_cfg)
    if not llm_cfg.enabled:
        return None
    return LLMRelevanceClassifier(config=llm_cfg)


async def generate_score_explanation(
    keyword_id: int,
    keyword_text: str,
    scores: dict[str, Any],
    components: dict[str, dict[str, Any]],
    final_score: float,
    tag: str,
    llm_client: Any,
    cache: Any,
) -> str:
    """
    Generates a human-readable explanation for a keyword's final recommendation score.
    Feature-flagged: returns template explanation when llm_client is None.
    """
    del keyword_id, cache
    component_contributions: list[tuple[str, float]] = []
    for name, component in components.items():
        contribution = component.get("contribution")
        if contribution is None:
            continue
        component_contributions.append((name, float(contribution)))
    top_components = sorted(component_contributions, key=lambda value: value[1], reverse=True)[:3]
    top_text = ", ".join(f"{name.replace('_score', '')}={value:.1f}" for name, value in top_components)
    template_explanation = (
        f"Final score: {final_score:.1f} ({tag}). "
        f"Confidence: {scores.get('confidence_modifier', 0):.2f}. "
        f"Top drivers: {top_text}. "
        f"Profile: {scores.get('scoring_profile', 'default')}."
    )
    if llm_client is None:
        return template_explanation

    try:
        prompt = (
            f"Explain in 2-3 sentences why '{keyword_text}' scored {final_score:.1f}/100 "
            f"with tag {tag}. Top score drivers: {top_text}. "
            f"Confidence modifier: {scores.get('confidence_modifier', 0):.2f}. "
            "Be specific and actionable for a new Fiverr seller."
        )
        llm_result = llm_client.complete(
            prompt=prompt,
            model="gpt-4o",
            temperature=0.3,
        )
        if isinstance(llm_result, Awaitable):
            llm_result = await llm_result
        return getattr(llm_result, "text", None) or template_explanation
    except Exception:  # noqa: BLE001
        return template_explanation


def write_keyword_score(
    keyword_id: int,
    scores: dict[str, float | None],
    weighted_composite: float,
    confidence_modifier: float,
    final_score: float,
    tag: str,
    score_components: dict[str, Any],
    confidence_breakdown: dict[str, Any],
    explanation_text: str,
    red_flags: list[dict[str, str]],
    scoring_profile: str,
    score_depth: str,
    integrity_fields: dict[str, Any] | None = None,
    db: Any = None,
) -> bool:
    """Persist score to KeywordScore model when available, else JSON sidecar fallback."""
    missing_data_warnings = [key for key, value in scores.items() if value is None]
    payload = {
        "keyword_id": keyword_id,
        **scores,
        "weighted_composite": weighted_composite,
        "confidence_modifier": confidence_modifier,
        "final_score": final_score,
        "tag": tag,
        "score_components": score_components,
        "confidence_breakdown": confidence_breakdown,
        "explanation_text": explanation_text,
        "red_flags": red_flags,
        "scoring_profile": scoring_profile,
        "score_depth": score_depth,
        "source_evidence": [],
        "llm_inputs_used": {},
        "missing_data_warnings": missing_data_warnings,
        "niche_tier": "standard",
        "data_as_of": None,
    }

    if isinstance(db, Session):
        try:
            row = KeywordScore(
                keyword_id=keyword_id,
                scoring_profile=scoring_profile,
                score_depth=score_depth,
                scored_at=datetime.now(UTC),
                data_as_of=None,
                demand_score=scores.get("demand_score"),
                competition_score=scores.get("competition_score"),
                opportunity_score=scores.get("opportunity_score"),
                feasibility_score=scores.get("feasibility_score"),
                profitability_score=scores.get("profitability_score"),
                intent_score=scores.get("intent_score"),
                saturation_score=scores.get("saturation_score"),
                weakness_score=scores.get("weakness_score"),
                trend_score=scores.get("trend_score"),
                final_score=final_score,
                confidence_modifier=confidence_modifier,
                trc_reliability=integrity_fields.get("trc_reliability") if isinstance(integrity_fields, dict) else None,
                opportunity_relevance_factor=(
                    integrity_fields.get("opportunity_relevance_factor")
                    if isinstance(integrity_fields, dict)
                    else None
                ),
                price_outliers_excluded=(
                    integrity_fields.get("price_outliers_excluded")
                    if isinstance(integrity_fields, dict)
                    else None
                ),
                clean_gig_count=integrity_fields.get("clean_gig_count") if isinstance(integrity_fields, dict) else None,
                competitor_profile_source=(
                    integrity_fields.get("competitor_profile_source")
                    if isinstance(integrity_fields, dict)
                    else None
                ),
                tag=tag,
                score_components=score_components,
                confidence_breakdown=confidence_breakdown,
                explanation_text=explanation_text,
                red_flags=red_flags,
                missing_data_warnings=missing_data_warnings,
                source_evidence=[],
                llm_inputs_used={},
                niche_tier="standard",
            )
            db.merge(row)
            db.commit()
            return True
        except Exception:  # noqa: BLE001
            db.rollback()
            logger.exception("DB write failed for keyword %s; falling back to sidecar.", keyword_id)

    try:
        _SIDE_CAR_DIR.mkdir(parents=True, exist_ok=True)
        sidecar_path = _SIDE_CAR_DIR / f"{keyword_id}.json"
        sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return True
    except OSError:
        logger.exception("Sidecar write failed for keyword %s.", keyword_id)
        return False
def _resolve_depth(keyword_id: int, db: Any) -> str:
    if db is not None and hasattr(db, "get_keyword_depth"):
        depth = db.get_keyword_depth(keyword_id)
        if isinstance(depth, str) and depth in DEPTH_SCORE_AVAILABILITY:
            return depth

    if isinstance(db, dict):
        payload = db.get(keyword_id, db)
        if isinstance(payload, dict):
            depth = payload.get("depth") or payload.get("score_depth") or payload.get("current_depth")
            if isinstance(depth, str) and depth in DEPTH_SCORE_AVAILABILITY:
                return depth
    return "standard"


# Exact marker substrings for the 5 scoring-stage LLM-dependent signals tracked by
# llm_analysis_completion_ratio: buyer intent (intent.py), upsell potential
# (profitability.py), saturation assessment (saturation_score.py), trend
# classification (trend.py), entry-gap assessment (feasibility.py).
#
# An explicit allowlist (rather than excluding "quality"/"competitor" substrings)
# is required because other calculators emit their own llm_not_implemented warnings
# whose text does not contain "quality" or "competitor" at all - e.g. weakness.py's
# llm_weakness_count_per_gig/llm_faq_completeness_score/llm_package_differentiation_
# score/llm_niche_specificity_score, and feasibility.py's "missing LLM gig weakness
# assessment" - which an exclude-filter would miscount as "other", capping
# llm_analysis_completion_ratio at 0.0 in the common no-LLM-key case even when the
# 5 intended signals are otherwise complete (Codex review, PR #176).
_OTHER_LLM_SIGNAL_MARKERS = (
    "missing LLM buyer intent classification",
    "missing LLM upsell potential assessment",
    "missing LLM saturation assessment",
    "no llm_trend_classification signal available",
    "missing LLM entry gap assessment",
    "missing LLM gig weakness assessment",
)
_OTHER_LLM_SIGNAL_COUNT = len(_OTHER_LLM_SIGNAL_MARKERS)

# The per-gig LLM quality fields src/scoring/weakness.py emits llm_not_implemented
# warnings for when GigQualityWeaknessScoreCalculator runs without an llm_client. Only
# two of these six contain "quality" in their text, so an exclude/include filter keyed
# on that one substring silently drops the other four (Codex review, PR #176).
_GIG_QUALITY_LLM_MARKERS = (
    "quality",
    "llm_weakness_count_per_gig",
    "llm_faq_completeness_score",
    "llm_package_differentiation_score",
    "llm_niche_specificity_score",
)


_DEFAULT_TTL_HOURS = 168.0


def _as_ttl_hours(value: Any) -> float:
    try:
        ttl = float(value)
    except (TypeError, ValueError):
        return _DEFAULT_TTL_HOURS
    return ttl if ttl > 0 else _DEFAULT_TTL_HOURS


def _normalize_gig_url_identity(raw_url: Any) -> str | None:
    """Mirror ProfitabilityScoreCalculator._normalize_gig_url_identity so a card URL
    that differs only by tracking query string, fragment, URL-encoded path, or
    trailing slash still resolves to the same persisted Gig row (Codex review,
    PR #176)."""
    if not isinstance(raw_url, str):
        return None
    stripped = raw_url.strip()
    if not stripped:
        return None
    split = urlsplit(stripped)
    normalized_path = unquote(split.path).strip().rstrip("/")
    if normalized_path:
        return normalized_path.lower()
    base = stripped.split("?", 1)[0].split("#", 1)[0].strip().rstrip("/")
    return base.lower() if base else None


# The fields DemandScoreCalculator (trends_12mo_score) and TrendScoreCalculator
# (slope, series-derived slope, avg-derived acceleration) actually read - a
# google_trends ExternalSignal row with none of these populated is treated as
# missing by both calculators (their own missing_google_trends deductions fire),
# so source_diversity_score must not count it as available either (Codex review,
# PR #176).
_GOOGLE_TRENDS_SCALAR_FIELDS = (
    "trends_12mo_score",
    "trends_3mo_score",
    "trends_3mo_avg",
    "trends_12mo_avg",
    "google_trends_slope",
)
_GOOGLE_TRENDS_SERIES_FIELDS = ("google_trends_12mo_series", "google_trends_3mo_series")


def _google_trends_signal_has_usable_data(signal: Any) -> bool:
    raw_payload = signal.raw_value_json if isinstance(signal.raw_value_json, dict) else {}
    for field in _GOOGLE_TRENDS_SCALAR_FIELDS:
        value = raw_payload.get(field)
        if value is None:
            continue
        try:
            float(value)
        except (TypeError, ValueError):
            continue
        return True
    for field in _GOOGLE_TRENDS_SERIES_FIELDS:
        series = raw_payload.get(field)
        if isinstance(series, list) and len(series) >= 2:
            return True
    # DemandScoreCalculator._signal_float falls back to the row's own
    # signal_value/normalized_value when trends_12mo_score is absent from the JSON
    # payload (a legacy/back-compat shape) - that fallback still feeds demand
    # scoring, so it counts as usable too (Codex review, PR #176).
    return getattr(signal, "normalized_value", None) is not None


def _build_confidence_context(
    keyword_id: int,
    scores: dict[str, float | None],
    depth: str,
    warnings: list[str],
    db: Any,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    total_scores = len(scores)
    present_scores = sum(1 for value in scores.values() if value is not None)
    reddit_warning_missing = any("reddit_not_implemented" in warning for warning in warnings)
    reddit_signals_available = not reddit_warning_missing
    relevance_cfg = config.get("relevance", {}) if isinstance(config, dict) else {}
    analysis_cfg = config.get("analysis", {}) if isinstance(config, dict) else {}
    external_signals_enabled = False
    external_signals_config: dict[str, Any] = {}
    if isinstance(analysis_cfg, dict):
        external_signals_enabled = bool(analysis_cfg.get("external_signals_enabled", False))
        raw_external_cfg = analysis_cfg.get("external_signals", {})
        if isinstance(raw_external_cfg, dict):
            external_signals_config = dict(raw_external_cfg)
    enable_zombie_filter = bool(relevance_cfg.get("enable_zombie_filter", True))
    top_n_for_scoring = max(1, int(relevance_cfg.get("top_n_for_scoring", 10)))
    zombie_fraction = 0.0
    youtube_video_count: int | None = None
    signal_age_days = 0
    signal_relevance_score = 1.0
    external_signal_context_present = False
    # Unknown collection state (no Session available to check) must not be treated as
    # "missing" - only the ORM-backed branch below can actually determine this, so it
    # defaults to the pre-fix lenient assumption and only downgrades on real evidence
    # (Codex review, PR #176).
    gig_detail_collected = True
    seller_profiles_collected = True
    # Fallback proxy for non-Session/unknown db paths, where no ExternalSignal query
    # is possible - a real google_trends row is checked directly below when a Session
    # is available (Codex review, PR #176).
    trends_available = scores.get("trend_score") is not None
    data_age_hours = 0.0
    data_ttl_hours = _DEFAULT_TTL_HOURS
    if isinstance(db, Session):
        gig_detail_collected = False
        seller_profiles_collected = False
        top_results = (
            db.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= top_n_for_scoring)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        # Scope to the active run the same way ProfitabilityScoreCalculator/
        # FeasibilityCalculator/WeaknessCalculator do: the run_id of the lowest-rank
        # row. A keyword recollected across multiple runs can otherwise mix an old
        # run's stale rows into freshness/detail checks even though the current score
        # was computed only from the active run's data (Codex review, PR #176).
        active_run_id = next(
            (
                result.run_id.strip()
                for result in top_results
                if isinstance(result.run_id, str) and result.run_id.strip()
            ),
            None,
        )
        if active_run_id is not None:
            top_results = [
                result
                for result in top_results
                if isinstance(result.run_id, str) and result.run_id.strip() == active_run_id
            ]
        total_organic = 0
        zombie_count = 0
        # data_freshness_score is the MEAN of each contributing record's individual
        # freshness (max(0, 1 - age/ttl)), per FRESHNESS_MODEL.md's
        # calculate_data_freshness_score - not just the single worst record, so a few
        # aging inputs don't collapse confidence when most of the data is fresh.
        # data_age_hours/data_ttl_hours are tracked separately from the single most
        # overdue record (highest age/ttl ratio) purely to drive the existing discrete
        # data_stale_over_2x_ttl deduction gate in confidence.py (Codex review, PR #176).
        freshness_ratios: list[float] = []
        worst_ratio = -1.0

        def _consider_freshness(candidate_at: Any, candidate_ttl: Any) -> None:
            nonlocal data_age_hours, data_ttl_hours, worst_ratio
            if not isinstance(candidate_at, datetime):
                return
            now_for_candidate = datetime.now(UTC) if candidate_at.tzinfo is not None else datetime.now()
            try:
                candidate_age_hours = max(0.0, (now_for_candidate - candidate_at).total_seconds() / 3600.0)
            except TypeError:
                # Mixed naive/aware datetimes (SQLite round-trip inconsistency) - skip
                # rather than raising.
                return
            candidate_ttl_hours = _as_ttl_hours(candidate_ttl)
            candidate_ratio = candidate_age_hours / candidate_ttl_hours
            freshness_ratios.append(candidate_ratio)
            if candidate_ratio > worst_ratio:
                worst_ratio = candidate_ratio
                data_age_hours = candidate_age_hours
                data_ttl_hours = candidate_ttl_hours

        processed_gig_ids: set[int] = set()

        def _process_gig(gig: Any) -> None:
            nonlocal gig_detail_collected, seller_profiles_collected
            gig_id = getattr(gig, "id", None)
            if isinstance(gig_id, int):
                if gig_id in processed_gig_ids:
                    return
                processed_gig_ids.add(gig_id)
            gig_detail_collected_at = getattr(gig, "detail_collected_at", None)
            # Gig.is_stale() requires BOTH detail_collected (bool) and
            # detail_collected_at: write_gig_card() resets detail_collected=False on
            # every re-seen search card WITHOUT clearing the old detail_collected_at,
            # so a stale timestamp alone is not proof detail collection succeeded for
            # the current run (Codex review, PR #176).
            if bool(getattr(gig, "detail_collected", False)) and gig_detail_collected_at is not None:
                gig_detail_collected = True
            # Prefer the actual collection timestamp over updated_at: a gig's metadata
            # (relevance/zombie flags, price) can be touched long after its detail
            # payload was scraped, which would otherwise mask stale gig-detail data
            # behind an unrelated recent write (Codex review, PR #176).
            gig_freshness_at = gig_detail_collected_at if isinstance(gig_detail_collected_at, datetime) else gig.updated_at
            _consider_freshness(gig_freshness_at, getattr(gig, "ttl_hours", None))
            seller = getattr(gig, "seller", None)
            if seller is not None:
                seller_profile_collected_at = getattr(seller, "profile_collected_at", None)
                if bool(getattr(seller, "profile_collected", False)):
                    seller_profiles_collected = True
                seller_freshness_at = (
                    seller_profile_collected_at if isinstance(seller_profile_collected_at, datetime) else seller.updated_at
                )
                _consider_freshness(seller_freshness_at, getattr(seller, "ttl_hours", None))

        for result in top_results:
            # collected_at (when this search snapshot was actually fetched) rather
            # than updated_at, which a later reprocessing pass can bump without
            # recollecting the underlying marketplace data (Codex review, PR #176).
            _consider_freshness(result.collected_at, getattr(result, "ttl_hours", None))
            gig = getattr(result, "gig", None)
            if gig is None:
                continue
            if getattr(gig, "is_sponsored", None) is True:
                continue
            total_organic += 1
            if bool(getattr(gig, "is_zombie", False)):
                zombie_count += 1
            _process_gig(gig)
        # A page-level SearchResult row can carry multiple gig cards in gig_cards
        # (write_search_result's raw scrape payload) beyond the single gig_id it links
        # to. ProfitabilityScoreCalculator/GigQualityWeaknessScoreCalculator resolve
        # those card URLs to real top-N gigs too, so one linked fresh gig must not hide
        # additional stale/missing-detail/missing-seller/zombie card gigs from
        # confidence (Codex review, PR #176). write_search_result stamps a whole page's
        # row with its first card's rank, so a page row can carry card positions well
        # outside top_n_for_scoring - sort by each card's own position and slice to the
        # same scoring window the loaders use, rather than resolving every card on the
        # page (Codex review, PR #176).
        ranked_card_urls: list[tuple[int, str]] = []
        for result in top_results:
            cards = result.gig_cards if isinstance(result.gig_cards, list) else []
            for card in cards:
                if not isinstance(card, dict):
                    continue
                raw_url = card.get("gig_url")
                if not isinstance(raw_url, str) or not raw_url.strip():
                    continue
                normalized_url = raw_url.strip()
                raw_position = card.get("position")
                if isinstance(raw_position, int) and raw_position > 0:
                    position = raw_position
                elif isinstance(raw_position, str) and raw_position.strip().isdigit():
                    position = int(raw_position.strip())
                else:
                    position = 10_000
                ranked_card_urls.append((position, normalized_url))
        ranked_card_urls.sort(key=lambda value: value[0])
        card_gig_urls: set[str] = set()
        seen_card_urls: set[str] = set()
        for _, normalized_url in ranked_card_urls:
            if normalized_url in seen_card_urls:
                continue
            seen_card_urls.add(normalized_url)
            card_gig_urls.add(normalized_url)
            if len(card_gig_urls) >= top_n_for_scoring:
                break
        if card_gig_urls:
            card_gigs_query = db.query(Gig).filter(Gig.gig_url.in_(card_gig_urls))
            # A gig_url is only unique within a run's own collection, not globally -
            # without this filter a page from an older/different run can pull in that
            # run's stale Gig row for the same URL, reporting its detail/freshness/
            # zombie state (and short-circuiting the identity fallback below) instead
            # of the active run's. ProfitabilityScoreCalculator's equivalent exact-URL
            # lookup applies the same active-run filter (Codex review, PR #176).
            if active_run_id is not None:
                card_gigs_query = card_gigs_query.filter(Gig.run_id == active_run_id)
            card_gigs = card_gigs_query.all()
            # An exact string match misses persisted Gig rows whose gig_url differs
            # only by a tracking query string, fragment, URL-encoded path, or
            # trailing slash from the card's URL. ProfitabilityScoreCalculator
            # normalizes by path identity and falls back through the keyword's own
            # gigs for exactly this reason - mirror that so those gigs' missing
            # detail/staleness/zombie state isn't silently dropped from confidence
            # (Codex review, PR #176).
            wanted_identities = {
                identity
                for identity in (_normalize_gig_url_identity(card_url) for card_url in card_gig_urls)
                if identity is not None
            }
            matched_identities = {
                identity
                for identity in (_normalize_gig_url_identity(getattr(gig, "gig_url", None)) for gig in card_gigs)
                if identity is not None
            }
            missing_identities = wanted_identities - matched_identities
            if missing_identities:
                identity_fallback_query = db.query(Gig).filter(Gig.keyword_id == keyword_id, Gig.gig_url.isnot(None))
                if active_run_id is not None:
                    identity_fallback_query = identity_fallback_query.filter(Gig.run_id == active_run_id)
                existing_ids = {gig.id for gig in card_gigs if getattr(gig, "id", None) is not None}
                for candidate_gig in identity_fallback_query.all():
                    if candidate_gig.id in existing_ids:
                        continue
                    if _normalize_gig_url_identity(candidate_gig.gig_url) not in missing_identities:
                        continue
                    card_gigs.append(candidate_gig)
                    if candidate_gig.id is not None:
                        existing_ids.add(candidate_gig.id)
            for card_gig in card_gigs:
                if getattr(card_gig, "id", None) in processed_gig_ids:
                    continue
                if getattr(card_gig, "is_sponsored", None) is True:
                    continue
                total_organic += 1
                if bool(getattr(card_gig, "is_zombie", False)):
                    zombie_count += 1
                _process_gig(card_gig)
        zombie_fraction = zombie_count / max(total_organic, 1)
        if total_organic == 0:
            # ProfitabilityScoreCalculator/GigQualityWeaknessScoreCalculator both fall
            # back to Gig.keyword_id (bypassing SearchResult.gig_id entirely) when no
            # gig could be resolved through search-result linkage - mirror that final
            # fallback tier here, including its active-run scoping and
            # position.asc().nullslast()/id.asc() ordering, so scores actually computed
            # from those gigs aren't penalized as if no (or the wrong) gig data existed
            # (Codex review, PR #176).
            fallback_query = db.query(Gig).filter(Gig.keyword_id == keyword_id)
            if active_run_id is not None:
                fallback_query = fallback_query.filter(Gig.run_id == active_run_id)
            fallback_gigs = (
                fallback_query.order_by(Gig.position.asc().nullslast(), Gig.id.asc()).limit(top_n_for_scoring).all()
            )
            # A stale active_run_id can point to unlinked SearchResult rows with no
            # matching Gig.run_id at all - retry unscoped, matching the same final
            # recovery tier profitability.py/weakness.py fall back to (Codex review,
            # PR #176).
            if not fallback_gigs and active_run_id is not None:
                fallback_gigs = (
                    db.query(Gig)
                    .filter(Gig.keyword_id == keyword_id)
                    .order_by(Gig.position.asc().nullslast(), Gig.id.asc())
                    .limit(top_n_for_scoring)
                    .all()
                )
            fallback_organic = 0
            fallback_zombie_count = 0
            for gig in fallback_gigs:
                if getattr(gig, "is_sponsored", None) is True:
                    continue
                fallback_organic += 1
                if bool(getattr(gig, "is_zombie", False)):
                    fallback_zombie_count += 1
                _process_gig(gig)
            if fallback_organic > 0:
                # These gigs are the only ones contributing to this keyword's score
                # (the search-result-linked path found none), so zombie concentration
                # must be measured against them too, not left at 0.0 (Codex review,
                # PR #176).
                zombie_fraction = fallback_zombie_count / fallback_organic
        # DemandScoreCalculator._resolve_marketplace_snapshot reads the SearchResult
        # row with the highest total_result_count regardless of rank (it can be
        # unranked or outside the top-N), so demand can be driven by a row this
        # function's rank-filtered top_results never sees - fold its freshness in too
        # (Codex review, PR #176).
        marketplace_snapshot_row = (
            db.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.total_result_count.isnot(None))
            .order_by(
                SearchResult.total_result_count.desc(), SearchResult.collected_at.desc(), SearchResult.id.desc()
            )
            .first()
        )
        if marketplace_snapshot_row is not None:
            _consider_freshness(marketplace_snapshot_row.collected_at, marketplace_snapshot_row.ttl_hours)
        # Keyword.updated_at reflects when the keyword ROW's own metadata was last
        # touched (niche reassignment, etc.), not when any underlying market data was
        # collected - it has no TTL category in FRESHNESS_MODEL.md's reference table
        # unlike every genuine collected-record type, and a keyword can go untouched
        # for weeks while its search results/gigs/signals stay current. Folding it in
        # here wrongly ages otherwise-fresh scores (Codex review, PR #176).
        reddit_count = (
            db.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type.in_(["reddit_demand", "reddit_activity"]),
            )
            .count()
        )
        reddit_signals_available = reddit_count > 0
        youtube_signal = (
            db.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == ExternalSignal.SIGNAL_YOUTUBE_COUNT,
            )
            .order_by(ExternalSignal.collected_at.desc(), ExternalSignal.id.desc())
            .first()
        )
        if youtube_signal is not None:
            raw_payload = youtube_signal.raw_value_json if isinstance(youtube_signal.raw_value_json, dict) else {}
            raw_count = raw_payload.get("youtube_result_count", youtube_signal.normalized_value)
            try:
                if raw_count is not None:
                    youtube_video_count = int(raw_count)
            except (TypeError, ValueError):
                youtube_video_count = None
        # Aggregate only the newest row PER exact signal_type, matching the "only the
        # latest row counts" semantics most scoring loaders use (e.g.
        # DemandScoreCalculator/ConversionIntentScoreCalculator read reddit_demand
        # specifically) - an old, superseded row from a prior run must not drive
        # staleness when a fresher same-type row is the one actually scored.
        all_signals = (
            db.query(ExternalSignal)
            .filter(ExternalSignal.keyword_id == keyword_id)
            .order_by(ExternalSignal.created_at.desc(), ExternalSignal.id.desc())
            .all()
        )
        # A non-null trend_score does not prove Google Trends contributed -
        # TrendScoreCalculator can produce a score from Reddit plus LLM classification
        # alone with Google Trends absent, which would overstate source diversity.
        # Check the actual signal instead (Codex review, PR #176). A mere row is not
        # enough either: DemandScoreCalculator/TrendScoreCalculator both treat an
        # empty or field-less payload as missing (their own missing_google_trends
        # deductions fire) - require the newest row's payload to carry a field either
        # calculator actually reads (Codex review, PR #176).
        newest_google_trends_signal = next(
            (signal for signal in all_signals if signal.signal_type == ExternalSignal.SIGNAL_GOOGLE_TRENDS),
            None,
        )
        trends_available = newest_google_trends_signal is not None and _google_trends_signal_has_usable_data(
            newest_google_trends_signal
        )
        # reddit_activity is never read on its own by any scoring loader - it only
        # ever contributes via TrendScoreCalculator's combined-with-reddit_demand pool
        # below - so it must not be folded in independently here, or a reddit_activity
        # row staler than reddit_demand would wrongly count even though nothing reads
        # it in that scenario (Codex review, PR #176).
        #
        # youtube_count is only ever consumed by ConfidenceScoreModifier's own
        # youtube-confidence-gate when external_signals_enabled is true - a stale
        # leftover youtube_count row must not depress freshness while that feature is
        # disabled, since nothing reads it in that case (Codex review, PR #176).
        seen_signal_types: set[str] = set()
        latest_signal_per_type: list[ExternalSignal] = []
        for signal in all_signals:
            if signal.signal_type == "reddit_activity":
                continue
            if signal.signal_type == ExternalSignal.SIGNAL_YOUTUBE_COUNT and not external_signals_enabled:
                continue
            if signal.signal_type in seen_signal_types:
                continue
            seen_signal_types.add(signal.signal_type)
            latest_signal_per_type.append(signal)
        for signal in latest_signal_per_type:
            _consider_freshness(signal.collected_at, signal.ttl_hours)
        # TrendScoreCalculator._load_signals_from_db additionally treats reddit_demand
        # and reddit_activity as one combined pool
        # (signal_type.in_([...]).order_by(created_at.desc()).first()) - fold that
        # combined value in too, in addition to (not instead of) reddit_demand's own
        # per-type entry above, since demand/intent scoring still reads reddit_demand
        # specifically regardless of reddit_activity's freshness (Codex review, PR #176).
        # Only TrendScoreCalculator reads reddit_activity, and only when trend scoring
        # actually ran for this call (score 9 is skipped for keyword_only/feasibility
        # depth, leaving trend_score None) - gate on that so an unused, possibly stale
        # reddit_activity row cannot demote a partial-depth run's freshness for a
        # signal nothing in that run reads (Codex review, PR #176).
        if scores.get("trend_score") is not None:
            reddit_combined_newest = next(
                (signal for signal in all_signals if signal.signal_type in ("reddit_demand", "reddit_activity")),
                None,
            )
            if reddit_combined_newest is not None:
                _consider_freshness(reddit_combined_newest.collected_at, reddit_combined_newest.ttl_hours)
        newest_signal = (
            db.query(ExternalSignal)
            .filter(ExternalSignal.keyword_id == keyword_id)
            .order_by(ExternalSignal.collected_at.desc(), ExternalSignal.id.desc())
            .first()
        )
        if newest_signal is not None and isinstance(newest_signal.collected_at, datetime):
            external_signal_context_present = True
            collected_at = newest_signal.collected_at
            # SQLite often round-trips timestamps as naive datetimes even when written as UTC.
            if collected_at.tzinfo is None:
                now = datetime.now()
            else:
                now = datetime.now(collected_at.tzinfo)
            delta = now - collected_at
            signal_age_days = max(0, int(delta.total_seconds() // 86400))
        rsv = get_result_set_validation(keyword_id, db)
        if rsv is not None and rsv.result_set_relevance_score is not None:
            signal_relevance_score = float(rsv.result_set_relevance_score)
        if freshness_ratios:
            data_freshness_score = sum(max(0.0, 1.0 - ratio) for ratio in freshness_ratios) / len(freshness_ratios)
        else:
            data_freshness_score = 1.0
    else:
        data_freshness_score = 1.0
    available_core_sources = sum([trends_available, gig_detail_collected, seller_profiles_collected])
    source_diversity_score = min(1.0, available_core_sources / 3.0)
    # Whether gig detail was scraped and whether LLM quality analysis ran on it are
    # unrelated: a gig can have a fully-collected detail payload with no LLM quality
    # score yet, so this must not be gated on gig_detail_collected (Codex review, PR #176).
    llm_quality_incomplete_count = sum(
        1
        for warning in warnings
        if "llm_not_implemented" in warning and any(marker in warning for marker in _GIG_QUALITY_LLM_MARKERS)
    )
    llm_other_missing = sum(
        1 for warning in warnings if any(marker in warning for marker in _OTHER_LLM_SIGNAL_MARKERS)
    )
    llm_analysis_completion_ratio = max(0.0, 1.0 - (min(llm_other_missing, _OTHER_LLM_SIGNAL_COUNT) / _OTHER_LLM_SIGNAL_COUNT))
    return {
        "data_completeness_ratio": present_scores / max(1, total_scores),
        "data_freshness_score": data_freshness_score,
        "source_diversity_score": source_diversity_score,
        "llm_analysis_completion_ratio": llm_analysis_completion_ratio,
        "google_trends_available": trends_available,
        "gig_detail_collected": gig_detail_collected,
        "seller_profiles_collected": seller_profiles_collected,
        "reddit_signals_available": reddit_signals_available,
        "llm_gig_quality_incomplete_count": llm_quality_incomplete_count,
        "llm_competitor_synthesis_failed": any(
            "competitor" in warning and "llm_not_implemented" in warning for warning in warnings
        ),
        "data_age_hours": data_age_hours,
        "data_ttl_hours": data_ttl_hours,
        "mode": depth,
        "enable_zombie_filter": enable_zombie_filter,
        "zombie_fraction": zombie_fraction,
        "youtube_video_count": youtube_video_count,
        "signal_age_days": signal_age_days,
        "signal_relevance_score": signal_relevance_score,
        "external_signal_context_present": external_signal_context_present,
        "external_signals_enabled": external_signals_enabled,
        "external_signals_config": external_signals_config,
    }


def _resolve_keyword_context(keyword_id: int, db: Any) -> tuple[str, int | None]:
    if isinstance(db, Session):
        keyword_row = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword_row is not None:
            return str(getattr(keyword_row, "keyword", f"keyword-{keyword_id}")), getattr(keyword_row, "niche_id", None)
    return f"keyword-{keyword_id}", None


def _score_value(result: Any) -> float | None:
    if result is None:
        return None
    return getattr(result, "score_value", None)


def _auto_recommendation_enabled(config: dict[str, Any] | None) -> bool:
    if not isinstance(config, dict):
        return True
    recommendation_config = config.get("recommendations", {})
    if not isinstance(recommendation_config, dict):
        return True
    return bool(recommendation_config.get("auto_generate", True))


def _build_auto_recommendation_context(
    *,
    keyword_id: int,
    keyword_text: str,
    niche_id: int | None,
    tag: str,
    final_score: float,
    scores: dict[str, float | None],
    score_components: dict[str, Any],
    db: Any,
    config: dict[str, Any] | None,
) -> Any:
    """Build the richest available context for score-triggered auto recommendations.

    Previously this path hand-built a minimal RecommendationContext with only identity
    and score fields, so the full DB-backed builder (competitor weaknesses, buyer
    review signals, price_distribution/price ladder, market_type, ...) was reachable
    from NO production path at all - generate_pricing_strategy silently skipped on
    every real auto run because context.price_distribution was always None
    (SCRUM-1112). Now the full builder runs when a real queryable db is available,
    with the fresh in-hand scoring results overlaid on top (they are newer than
    anything persisted); any failure falls back to the minimal context so a context
    hiccup can never block the recommendation itself.
    """
    from src.recommendations.context import RecommendationContext, build_recommendation_context

    resolved_niche_id = niche_id if niche_id is not None else 0
    minimal_fields: dict[str, Any] = {
        "keyword_id": keyword_id,
        "keyword_text": keyword_text,
        "niche_id": resolved_niche_id,
        "niche_name": str(resolved_niche_id) if resolved_niche_id else "Unknown",
        "tag": tag,
        "final_score": final_score,
        "demand_score": scores.get("demand_score"),
        "competition_score": scores.get("competition_score"),
        "opportunity_score": scores.get("opportunity_score"),
        "feasibility_score": scores.get("feasibility_score"),
        "profitability_score": scores.get("profitability_score"),
        "score_components": score_components,
    }

    if hasattr(db, "query"):
        try:
            full_context = build_recommendation_context(
                keyword_id, db, config if isinstance(config, dict) else {}
            )
            # This run's results are authoritative: tag/final_score/components always
            # overlay; individual sub-scores overlay only when computed this run (a
            # None here should not clobber a persisted value the builder resolved).
            overlay = {key: value for key, value in minimal_fields.items() if value is not None}
            if not keyword_text:
                overlay.pop("keyword_text", None)
            if niche_id is None:
                overlay.pop("niche_id", None)
            if full_context.niche_name and full_context.niche_name != "Unknown":
                overlay.pop("niche_name", None)
            if not score_components:
                overlay.pop("score_components", None)
            return full_context.model_copy(update=overlay)
        except Exception:
            logger.debug(
                "Full auto-recommendation context failed for keyword=%s; using minimal context",
                keyword_id,
                exc_info=True,
            )
            # A failed query leaves a real Session in pending-rollback state, which
            # would poison the fallback path's own generate/write calls on the same
            # session - roll back before continuing (Codex review, PR #168).
            rollback = getattr(db, "rollback", None)
            if callable(rollback):
                try:
                    rollback()
                except Exception:
                    logger.debug(
                        "Session rollback after context failure also failed for keyword=%s",
                        keyword_id,
                        exc_info=True,
                    )

    return RecommendationContext(**minimal_fields)


async def _maybe_auto_generate_recommendation(
    *,
    keyword_id: int,
    keyword_text: str,
    niche_id: int | None,
    tag: str,
    final_score: float,
    scores: dict[str, float | None],
    score_components: dict[str, Any],
    db: Any,
    llm_client: Any,
    cache: Any,
    config: dict[str, Any] | None,
) -> None:
    if tag not in _AUTO_RECOMMENDATION_TAGS:
        return
    if not _auto_recommendation_enabled(config):
        return

    try:
        from src.recommendations.eligibility import should_regenerate_recommendation
        from src.recommendations.storage import write_recommendation
        from src.recommendations.tasks import generate_recommendation

        should_regen = True
        if hasattr(db, "query"):
            try:
                should_regen = should_regenerate_recommendation(keyword_id, final_score, db)
            except Exception:
                should_regen = True
        if not should_regen:
            return

        context = _build_auto_recommendation_context(
            keyword_id=keyword_id,
            keyword_text=keyword_text,
            niche_id=niche_id,
            tag=tag,
            final_score=final_score,
            scores=scores,
            score_components=score_components,
            db=db,
            config=config,
        )
        recommendation_data = await generate_recommendation(
            keyword_id=keyword_id,
            context=context,
            llm_client=llm_client,
            cache=cache,
            db=db,
        )
        wrote = write_recommendation(
            keyword_id=keyword_id,
            run_id="auto-score",
            context=context,
            recommendation_data=recommendation_data,
            db=db,
        )
        if not wrote:
            logger.warning("Auto-recommendation persistence failed keyword=%s tag=%s", keyword_id, tag)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Auto-recommendation failed keyword=%s tag=%s: %s", keyword_id, tag, exc)
