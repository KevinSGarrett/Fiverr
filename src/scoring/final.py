"""S4.10 Final Recommendation Score calculator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class FinalRecommendationScoreCalculator:
    """Calculate final recommendation score using profile-weighted components."""

    PROFILE_WEIGHTS: dict[str, dict[str, float]] = {
        "default": {
            "demand": 0.20,
            "competition_inv": 0.20,
            "opportunity": 0.25,
            "feasibility": 0.15,
            "profitability": 0.10,
            "intent": 0.10,
            "saturation_inv": 0.05,
            "weakness": 0.10,
            "trend": 0.05,
        },
        "aggressive_new_seller": {
            "feasibility": 0.25,
            "weakness": 0.20,
            "opportunity": 0.20,
            "demand": 0.15,
            "competition_inv": 0.10,
            "profitability": 0.05,
            "intent": 0.05,
            "saturation_inv": 0.00,
            "trend": 0.00,
        },
        "profitability_focus": {
            "profitability": 0.25,
            "intent": 0.20,
            "opportunity": 0.20,
            "demand": 0.15,
            "competition_inv": 0.10,
            "feasibility": 0.05,
            "weakness": 0.05,
            "saturation_inv": 0.00,
            "trend": 0.00,
        },
        "trend_chaser": {
            "trend": 0.25,
            "demand": 0.25,
            "opportunity": 0.20,
            "competition_inv": 0.15,
            "feasibility": 0.10,
            "profitability": 0.05,
            "intent": 0.00,
            "weakness": 0.00,
            "saturation_inv": 0.00,
        },
    }

    _SCORE_FIELDS = {
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

    def calculate(self, keyword_id: int, profile: str, db: Any) -> dict[str, Any]:
        """Calculate final recommendation score and metadata payload."""
        profile_name = profile if profile in self.PROFILE_WEIGHTS else "default"
        weights = self._normalized_profile_weights(self.PROFILE_WEIGHTS[profile_name])
        signals = self._load_signals(keyword_id, db)
        confidence_modifier = self._clamp_0_1(self._as_float(signals.get("confidence_modifier"), 1.0))

        weighted_sum = 0.0
        used_weight = 0.0
        missing_components: list[str] = []
        component_scores: dict[str, float | None] = {}

        for score_field, weight_key in self._SCORE_FIELDS.items():
            score_value = self._as_optional_float(signals.get(score_field))
            weight = weights.get(weight_key, 0.0)
            component_scores[score_field] = score_value

            if weight == 0.0:
                continue
            if score_value is None:
                missing_components.append(score_field)
                continue

            effective_score = score_value
            if weight_key in {"competition_inv", "saturation_inv"}:
                effective_score = 100.0 - score_value

            weighted_sum += effective_score * weight
            used_weight += weight

        composite_score = 0.0 if used_weight == 0.0 else (weighted_sum / used_weight)
        final_score = round(self._clamp_0_100(composite_score * confidence_modifier), 2)
        tag = self._assign_tag(final_score)

        explanation_text = self._build_explanation(
            final_score=final_score,
            tag=tag,
            profile=profile,
            missing_components=missing_components,
            confidence_modifier=confidence_modifier,
        )

        return {
            "keyword_id": keyword_id,
            "final_score": final_score,
            "tag": tag,
            "profile_used": profile_name,
            "weights_applied": dict(weights),
            "component_scores": component_scores,
            "confidence_modifier": confidence_modifier,
            "missing_components": missing_components,
            "explanation_text": explanation_text,
        }

    @staticmethod
    def validate_profile_weights() -> dict[str, float]:
        """Return profile weight sums for validation and tests."""
        return {
            name: round(sum(FinalRecommendationScoreCalculator._normalized_profile_weights(weights).values()), 3)
            for name, weights in FinalRecommendationScoreCalculator.PROFILE_WEIGHTS.items()
        }

    @staticmethod
    def _normalized_profile_weights(weights: dict[str, float]) -> dict[str, float]:
        total = sum(weights.values())
        if total <= 0:
            return dict(weights)
        return {key: (value / total) for key, value in weights.items()}

    @staticmethod
    def _assign_tag(final_score: float) -> str:
        if final_score >= 80.0:
            return "STRONG_GO"
        if final_score >= 60.0:
            return "CONDITIONAL_GO"
        if final_score >= 40.0:
            return "MONITOR"
        if final_score >= 20.0:
            return "CAUTION"
        return "PASS"

    @staticmethod
    def _build_explanation(
        final_score: float,
        tag: str,
        profile: str,
        missing_components: list[str],
        confidence_modifier: float,
    ) -> str:
        missing_note = (
            " All components were available."
            if not missing_components
            else f" Missing components skipped: {', '.join(missing_components)}."
        )
        return (
            f"Profile '{profile}' produced final score {final_score:.2f} tagged {tag}. "
            f"Confidence modifier applied: {confidence_modifier:.3f}.{missing_note}"
        )

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if hasattr(db, "get_final_inputs"):
            loaded = db.get_final_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    @staticmethod
    def _as_optional_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp_0_100(value: float) -> float:
        return max(0.0, min(100.0, value))

    @staticmethod
    def _clamp_0_1(value: float) -> float:
        return max(0.0, min(1.0, value))
