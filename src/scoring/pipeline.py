"""Async scoring pipeline wiring for keyword-level scoring and persistence."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable
from pathlib import Path
from typing import Any

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.final import FinalRecommendationScoreCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator

logger = logging.getLogger(__name__)


def _normalized_profile(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return dict(weights)
    return {name: (value / total) for name, value in weights.items()}

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
) -> tuple[float, dict[str, dict[str, float | None]]]:
    """Calculate weighted composite and detailed score components."""
    weighted_sum = 0.0
    weight_used = 0.0
    components: dict[str, dict[str, float | None]] = {}

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


async def score_keyword(
    keyword_id: int,
    profile_name: str,
    db: Any,
    llm_client: Any,
    cache: Any,
) -> dict[str, Any]:
    """Run full keyword scoring pipeline, compute final score, and persist result."""
    del cache
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

    demand_result = demand_calculator.calculate(keyword_id, db) if 1 in available_scores else None
    competition_result = (
        competition_calculator.calculate(keyword_id, db) if 2 in available_scores else None
    )
    opportunity_result = None
    if 3 in available_scores:
        opportunity_result = opportunity_calculator.calculate(
            keyword_id=keyword_id,
            db=db,
            demand_result=demand_result,
            competition_result=competition_result,
        )
    feasibility_result = (
        feasibility_calculator.calculate(keyword_id, db) if 4 in available_scores else None
    )
    profitability_result = (
        profitability_calculator.calculate(keyword_id, db) if 5 in available_scores else None
    )
    intent_result = intent_calculator.calculate(keyword_id, db) if 6 in available_scores else None
    saturation_result = (
        saturation_calculator.calculate(keyword_id, db) if 7 in available_scores else None
    )
    weakness_result = weakness_calculator.calculate(keyword_id, db) if 8 in available_scores else None
    trend_result = trend_calculator.calculate(keyword_id, db) if 9 in available_scores else None

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

    confidence_context = _build_confidence_context(scores=scores, depth=depth, warnings=missing_data_warnings)
    confidence_modifier = confidence_modifier_calculator.calculate(keyword_id, confidence_context, db)
    confidence_breakdown = dict(confidence_modifier_calculator.last_breakdown)

    weighted_composite, score_components = calculate_weighted_composite(scores, profile_weights)
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
    explanation_text = await _generate_score_explanation(
        keyword_id=keyword_id,
        scores=scores,
        score_components=score_components,
        final_score=final_score,
        tag=tag,
        llm_client=llm_client,
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
        db=db,
    )

    return {
        "keyword_id": keyword_id,
        "scoring_profile": profile_name,
        "score_depth": score_depth,
        "scores": scores,
        "weighted_composite": weighted_composite,
        "confidence_modifier": confidence_modifier,
        "final_score": final_score,
        "tag": tag,
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
) -> list[dict[str, Any]]:
    """Sequentially score keywords and return per-keyword success/failure payloads."""
    if not keyword_ids:
        return []

    results: list[dict[str, Any]] = []
    for keyword_id in keyword_ids:
        try:
            result = await score_keyword(
                keyword_id=keyword_id,
                profile_name=profile_name,
                db=db,
                llm_client=llm_client,
                cache=cache,
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
    db: Any,
) -> bool:
    """Persist score to KeywordScore model when available, else JSON sidecar fallback."""
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
    }

    keyword_score_model = _resolve_keyword_score_model()
    if keyword_score_model is not None and hasattr(db, "query"):
        try:
            row = db.query(keyword_score_model).filter(keyword_score_model.keyword_id == keyword_id).first()
            if row is None:
                row = keyword_score_model(keyword_id=keyword_id)
                db.add(row)
            for key, value in payload.items():
                if hasattr(row, key):
                    setattr(row, key, value)
            if hasattr(db, "commit"):
                db.commit()
            return True
        except Exception:  # noqa: BLE001
            if hasattr(db, "rollback"):
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


def _resolve_keyword_score_model() -> Any:
    try:
        from src.models import scoring as scoring_models  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None
    return getattr(scoring_models, "KeywordScore", None)


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


def _build_confidence_context(
    scores: dict[str, float | None],
    depth: str,
    warnings: list[str],
) -> dict[str, Any]:
    total_scores = len(scores)
    present_scores = sum(1 for value in scores.values() if value is not None)
    reddit_warning_missing = any("reddit_not_implemented" in warning for warning in warnings)
    trends_available = scores.get("trend_score") is not None
    return {
        "data_completeness_ratio": present_scores / max(1, total_scores),
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": trends_available,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": not reddit_warning_missing,
        "llm_gig_quality_incomplete_count": sum(
            1 for warning in warnings if "llm_not_implemented" in warning
        ),
        "llm_competitor_synthesis_failed": any(
            "competitor" in warning and "llm_not_implemented" in warning for warning in warnings
        ),
        "data_age_hours": 0.0,
        "data_ttl_hours": 168.0,
        "mode": depth,
    }


async def _generate_score_explanation(
    keyword_id: int,
    scores: dict[str, float | None],
    score_components: dict[str, dict[str, float | None]],
    final_score: float,
    tag: str,
    llm_client: Any,
) -> str:
    if llm_client is not None and hasattr(llm_client, "generate_score_explanation"):
        maybe_awaitable = llm_client.generate_score_explanation(
            keyword_id=keyword_id,
            scores=scores,
            score_components=score_components,
            final_score=final_score,
            tag=tag,
        )
        if isinstance(maybe_awaitable, Awaitable):
            return str(await maybe_awaitable)
        return str(maybe_awaitable)
    return (
        f"Keyword {keyword_id} final score is {final_score:.2f} ({tag}) based on weighted "
        "score components and confidence-adjusted composite."
    )


def _score_value(result: Any) -> float | None:
    if result is None:
        return None
    return getattr(result, "score_value", None)
