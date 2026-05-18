"""S4.6 Conversion Intent Score calculator."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

from src.scoring.contracts import IntentScoreResult, ScoreComponent


class ConversionIntentScoreCalculator:
    """Calculate how close keyword searchers are to a purchasing action."""

    DEFAULT_WEIGHT = 0.10
    _SPECIFICITY_WEIGHT = 0.25
    _COMMERCIAL_MODIFIER_WEIGHT = 0.25
    _REVIEW_SIGNAL_WEIGHT = 0.20
    _LLM_INTENT_WEIGHT = 0.20
    _REDDIT_INTENT_WEIGHT = 0.10

    _COMMERCIAL_MODIFIER_PATTERN = re.compile(
        r"\b(hire|buy|need|looking\s+for|best)\b",
        flags=re.IGNORECASE,
    )
    _LLM_INTENT_MAP = {
        "INFORMATIONAL": 10.0,
        "CONSIDERATION": 40.0,
        "HIGH_INTENT": 70.0,
        "TRANSACTIONAL": 100.0,
    }

    def calculate(self, keyword_id: int, db: Any) -> IntentScoreResult:
        """Calculate a conversion intent score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0

        keyword_text = str(signals.get("keyword", "")).strip()
        if keyword_text:
            specificity_score = self._specificity_score_from_keyword(keyword_text)
            score_components["keyword_specificity"] = ScoreComponent(
                value=specificity_score,
                weight=self._SPECIFICITY_WEIGHT,
                raw=keyword_text,
            )
            weighted_sum += specificity_score * self._SPECIFICITY_WEIGHT
            total_weight_available += self._SPECIFICITY_WEIGHT
            source_evidence.append("keywords.keyword")
        else:
            missing_data_warnings.append("Missing keyword text for specificity signal.")

        commercial_modifier_score = self._resolve_commercial_modifier_score(signals, keyword_text)
        if commercial_modifier_score is not None:
            score_components["commercial_modifier_presence"] = ScoreComponent(
                value=commercial_modifier_score,
                weight=self._COMMERCIAL_MODIFIER_WEIGHT,
                raw={
                    "keyword": keyword_text,
                    "commercial_modifier_score": signals.get("commercial_modifier_score"),
                },
            )
            weighted_sum += commercial_modifier_score * self._COMMERCIAL_MODIFIER_WEIGHT
            total_weight_available += self._COMMERCIAL_MODIFIER_WEIGHT
            source_evidence.append("keywords.commercial_modifier_presence")
        else:
            missing_data_warnings.append("Missing commercial modifier signal.")

        avg_review_count_top10 = self._as_float(signals.get("avg_review_count_top10"))
        if avg_review_count_top10 is not None:
            review_signal = self._normalize_review_count(avg_review_count_top10)
            score_components["buyer_proof_reviews"] = ScoreComponent(
                value=review_signal,
                weight=self._REVIEW_SIGNAL_WEIGHT,
                raw=avg_review_count_top10,
            )
            weighted_sum += review_signal * self._REVIEW_SIGNAL_WEIGHT
            total_weight_available += self._REVIEW_SIGNAL_WEIGHT
            source_evidence.append("gig_details.avg_review_count_top10")
        else:
            missing_data_warnings.append("Missing average review count signal from top gigs.")

        llm_intent_raw = signals.get("llm_buyer_intent_classification")
        llm_intent_class = ""
        if isinstance(llm_intent_raw, str):
            llm_intent_class = llm_intent_raw.strip().upper()
        if llm_intent_class:
            llm_intent_score = self._LLM_INTENT_MAP.get(llm_intent_class)
            if llm_intent_score is None:
                llm_intent_score = 40.0
                confidence_breakdown["llm_intent_unrecognized"] = -0.05
                missing_data_warnings.append(
                    f"Unrecognized LLM intent class '{llm_intent_class}', defaulted to CONSIDERATION."
                )
            score_components["llm_buyer_intent"] = ScoreComponent(
                value=llm_intent_score,
                weight=self._LLM_INTENT_WEIGHT,
                raw=llm_intent_class,
            )
            weighted_sum += llm_intent_score * self._LLM_INTENT_WEIGHT
            total_weight_available += self._LLM_INTENT_WEIGHT
            source_evidence.append("llm.buyer_intent_classification")
        else:
            default_class = "CONSIDERATION"
            default_score = self._LLM_INTENT_MAP[default_class]
            score_components["llm_buyer_intent"] = ScoreComponent(
                value=default_score,
                weight=self._LLM_INTENT_WEIGHT,
                raw=default_class,
                note="Defaulted because LLM intent classification unavailable.",
            )
            weighted_sum += default_score * self._LLM_INTENT_WEIGHT
            total_weight_available += self._LLM_INTENT_WEIGHT
            confidence_breakdown["missing_llm_intent_classification"] = -0.10
            missing_data_warnings.append(
                "llm_not_implemented: missing LLM buyer intent classification; defaulted to CONSIDERATION (40)."
            )

        reddit_intent_signal = self._as_float(signals.get("reddit_demand_intent_score"))
        if reddit_intent_signal is not None:
            reddit_intent_score = self._normalize_reddit_intent(reddit_intent_signal)
            score_components["reddit_intent_signal"] = ScoreComponent(
                value=reddit_intent_score,
                weight=self._REDDIT_INTENT_WEIGHT,
                raw=reddit_intent_signal,
            )
            weighted_sum += reddit_intent_score * self._REDDIT_INTENT_WEIGHT
            total_weight_available += self._REDDIT_INTENT_WEIGHT
            source_evidence.append("external_signals.reddit_demand.reddit_demand_intent_score")
        else:
            missing_data_warnings.append("Missing Reddit demand intent signal.")
            confidence_breakdown["missing_reddit_intent_signal"] = -0.05

        if total_weight_available < 0.30:
            return IntentScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient conversion-intent signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate conversion intent explanation.",
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
            )

        intent_score = round(min(100.0, max(0.0, weighted_sum / total_weight_available)), 2)
        return IntentScoreResult(
            keyword_id=keyword_id,
            score_value=intent_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Conversion intent combines keyword specificity, commercial language, social demand,"
                " review proof, and LLM buyer-intent classification."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Intent score estimates purchase readiness using long-tail specificity, commercial"
                " modifier detection, top-gig review proof, LLM buyer intent class, and Reddit"
                " intent signals."
            ),
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
        )

    def _resolve_commercial_modifier_score(self, signals: dict[str, Any], keyword_text: str) -> float | None:
        explicit_modifier_score = self._as_float(signals.get("commercial_modifier_score"))
        if explicit_modifier_score is not None:
            if explicit_modifier_score <= 1.0:
                return max(0.0, min(100.0, explicit_modifier_score * 100.0))
            return max(0.0, min(100.0, explicit_modifier_score))

        if not keyword_text:
            return None
        if self._COMMERCIAL_MODIFIER_PATTERN.search(keyword_text):
            return 90.0
        return 20.0

    @staticmethod
    def _specificity_score_from_keyword(keyword: str) -> float:
        word_count = len([part for part in keyword.split() if part.strip()])
        if word_count <= 1:
            return 20.0
        if word_count == 2:
            return 50.0
        if word_count == 3:
            return 80.0
        return 100.0

    @staticmethod
    def _normalize_review_count(avg_review_count: float) -> float:
        if avg_review_count <= 0:
            return 0.0
        return max(0.0, min(100.0, (math.log10(avg_review_count + 1.0) / 3.0) * 100.0))

    @staticmethod
    def _normalize_reddit_intent(raw_value: float) -> float:
        if raw_value <= 10.0:
            return max(0.0, min(100.0, raw_value * 10.0))
        return max(0.0, min(100.0, raw_value))

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if hasattr(db, "get_intent_inputs"):
            loaded = db.get_intent_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
