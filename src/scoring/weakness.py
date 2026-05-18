"""S4.8 Gig Quality Weakness Score calculator."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from src.scoring.contracts import ScoreComponent, WeaknessScoreResult


class GigQualityWeaknessScoreCalculator:
    """Calculate competitor weakness/opportunity from quality and collection signals."""

    DEFAULT_WEIGHT = 0.10
    _DESCRIPTION_QUALITY_INV_WEIGHT = 0.15
    _WEAKNESS_COUNT_WEIGHT = 0.20
    _VIDEO_ABSENCE_WEIGHT = 0.15
    _PORTFOLIO_ABSENCE_WEIGHT = 0.15
    _THUMBNAIL_QUALITY_INV_WEIGHT = 0.10
    _FAQ_COMPLETENESS_INV_WEIGHT = 0.10
    _PACKAGE_DIFFERENTIATION_INV_WEIGHT = 0.10
    _NICHE_SPECIFICITY_INV_WEIGHT = 0.05

    def calculate(self, keyword_id: int, db: Any) -> WeaknessScoreResult:
        """Calculate weakness score with graceful degradation for missing LLM inputs."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0

        description_quality = self._resolve_llm_value(
            "llm_description_quality_score",
            signals,
            self._llm_description_quality_stub,
            missing_data_warnings,
        )
        if description_quality is not None:
            description_weakness = self._invert_quality_score(description_quality)
            score_components["description_quality_inverted"] = ScoreComponent(
                value=description_weakness,
                weight=self._DESCRIPTION_QUALITY_INV_WEIGHT,
                raw=description_quality,
            )
            weighted_sum += description_weakness * self._DESCRIPTION_QUALITY_INV_WEIGHT
            total_weight_available += self._DESCRIPTION_QUALITY_INV_WEIGHT
            source_evidence.append("llm.description_quality_score")

        weakness_count = self._resolve_llm_value(
            "llm_weakness_count_per_gig",
            signals,
            self._llm_weakness_count_stub,
            missing_data_warnings,
        )
        if weakness_count is not None:
            weakness_count_score = self._normalize_weakness_count(weakness_count)
            score_components["weakness_count"] = ScoreComponent(
                value=weakness_count_score,
                weight=self._WEAKNESS_COUNT_WEIGHT,
                raw=weakness_count,
            )
            weighted_sum += weakness_count_score * self._WEAKNESS_COUNT_WEIGHT
            total_weight_available += self._WEAKNESS_COUNT_WEIGHT
            source_evidence.append("llm.weakness_count_per_gig")

        video_absence_rate = self._resolve_absence_rate(signals, "video_absence_rate", "top10_has_video")
        if video_absence_rate is not None:
            video_absence_score = video_absence_rate * 100.0
            score_components["video_absence_rate"] = ScoreComponent(
                value=video_absence_score,
                weight=self._VIDEO_ABSENCE_WEIGHT,
                raw=video_absence_rate,
            )
            weighted_sum += video_absence_score * self._VIDEO_ABSENCE_WEIGHT
            total_weight_available += self._VIDEO_ABSENCE_WEIGHT
            source_evidence.append("gig_details.video_presence")
        else:
            missing_data_warnings.append("Missing video absence signal.")

        portfolio_absence_rate = self._resolve_absence_rate(
            signals,
            "portfolio_absence_rate",
            "top10_has_portfolio",
        )
        if portfolio_absence_rate is not None:
            portfolio_absence_score = portfolio_absence_rate * 100.0
            score_components["portfolio_absence_rate"] = ScoreComponent(
                value=portfolio_absence_score,
                weight=self._PORTFOLIO_ABSENCE_WEIGHT,
                raw=portfolio_absence_rate,
            )
            weighted_sum += portfolio_absence_score * self._PORTFOLIO_ABSENCE_WEIGHT
            total_weight_available += self._PORTFOLIO_ABSENCE_WEIGHT
            source_evidence.append("gig_details.portfolio_presence")
        else:
            missing_data_warnings.append("Missing portfolio absence signal.")

        thumbnail_quality = self._resolve_llm_value(
            "llm_thumbnail_quality_score",
            signals,
            self._llm_thumbnail_quality_stub,
            missing_data_warnings,
        )
        if thumbnail_quality is not None:
            thumbnail_weakness = self._invert_quality_score(thumbnail_quality)
            score_components["thumbnail_quality_inverted"] = ScoreComponent(
                value=thumbnail_weakness,
                weight=self._THUMBNAIL_QUALITY_INV_WEIGHT,
                raw=thumbnail_quality,
            )
            weighted_sum += thumbnail_weakness * self._THUMBNAIL_QUALITY_INV_WEIGHT
            total_weight_available += self._THUMBNAIL_QUALITY_INV_WEIGHT
            source_evidence.append("llm.thumbnail_quality_score")

        faq_completeness = self._resolve_llm_value(
            "llm_faq_completeness_score",
            signals,
            self._llm_faq_completeness_stub,
            missing_data_warnings,
        )
        if faq_completeness is not None:
            faq_weakness = self._invert_quality_score(faq_completeness)
            score_components["faq_completeness_inverted"] = ScoreComponent(
                value=faq_weakness,
                weight=self._FAQ_COMPLETENESS_INV_WEIGHT,
                raw=faq_completeness,
            )
            weighted_sum += faq_weakness * self._FAQ_COMPLETENESS_INV_WEIGHT
            total_weight_available += self._FAQ_COMPLETENESS_INV_WEIGHT
            source_evidence.append("llm.faq_completeness_score")

        package_differentiation = self._resolve_llm_value(
            "llm_package_differentiation_score",
            signals,
            self._llm_package_differentiation_stub,
            missing_data_warnings,
        )
        if package_differentiation is not None:
            package_weakness = self._invert_quality_score(package_differentiation)
            score_components["package_differentiation_inverted"] = ScoreComponent(
                value=package_weakness,
                weight=self._PACKAGE_DIFFERENTIATION_INV_WEIGHT,
                raw=package_differentiation,
            )
            weighted_sum += package_weakness * self._PACKAGE_DIFFERENTIATION_INV_WEIGHT
            total_weight_available += self._PACKAGE_DIFFERENTIATION_INV_WEIGHT
            source_evidence.append("llm.package_differentiation_score")

        niche_specificity = self._resolve_llm_value(
            "llm_niche_specificity_score",
            signals,
            self._llm_niche_specificity_stub,
            missing_data_warnings,
        )
        if niche_specificity is not None:
            niche_genericness = self._invert_quality_score(niche_specificity)
            score_components["niche_specificity_inverted"] = ScoreComponent(
                value=niche_genericness,
                weight=self._NICHE_SPECIFICITY_INV_WEIGHT,
                raw=niche_specificity,
            )
            weighted_sum += niche_genericness * self._NICHE_SPECIFICITY_INV_WEIGHT
            total_weight_available += self._NICHE_SPECIFICITY_INV_WEIGHT
            source_evidence.append("llm.niche_specificity_score")

        if total_weight_available < 0.30:
            return WeaknessScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient weakness signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text=(
                    "Insufficient signals to estimate gig quality weakness opportunity."
                ),
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
            )

        weakness_score = round(min(100.0, max(0.0, weighted_sum / total_weight_available)), 2)
        return WeaknessScoreResult(
            keyword_id=keyword_id,
            score_value=weakness_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Higher weakness score indicates more exploitable competitor gaps."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Weakness score combines LLM quality weaknesses and collection-derived"
                " absence rates to estimate exploitable opportunity."
            ),
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
        )

    def _resolve_llm_value(
        self,
        key: str,
        signals: dict[str, Any],
        fallback: Callable[[], float | None],
        warnings: list[str],
    ) -> float | None:
        explicit = self._as_float(signals.get(key))
        if explicit is not None:
            return explicit
        warnings.append(f"llm_not_implemented: missing {key}.")
        return self._as_float(fallback())

    @staticmethod
    def _invert_quality_score(raw_score: float) -> float:
        scaled = raw_score * 10.0 if raw_score <= 10.0 else raw_score
        return max(0.0, min(100.0, 100.0 - scaled))

    @staticmethod
    def _normalize_weakness_count(raw_count: float) -> float:
        if raw_count <= 0:
            return 0.0
        return max(0.0, min(100.0, raw_count * 10.0))

    def _resolve_absence_rate(
        self,
        signals: dict[str, Any],
        rate_key: str,
        presence_key: str,
    ) -> float | None:
        explicit_rate = self._as_float(signals.get(rate_key))
        if explicit_rate is not None:
            return max(0.0, min(1.0, explicit_rate))

        presence_list = signals.get(presence_key)
        if not isinstance(presence_list, list) or not presence_list:
            return None
        known_presence = [value for value in presence_list if isinstance(value, bool)]
        if not known_presence:
            return None
        present_count = sum(1 for value in known_presence if value)
        return 1.0 - (present_count / len(known_presence))

    @staticmethod
    def _llm_description_quality_stub() -> float | None:
        return None

    @staticmethod
    def _llm_weakness_count_stub() -> float | None:
        return None

    @staticmethod
    def _llm_thumbnail_quality_stub() -> float | None:
        return None

    @staticmethod
    def _llm_faq_completeness_stub() -> float | None:
        return None

    @staticmethod
    def _llm_package_differentiation_stub() -> float | None:
        return None

    @staticmethod
    def _llm_niche_specificity_stub() -> float | None:
        return None

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if hasattr(db, "get_weakness_inputs"):
            loaded = db.get_weakness_inputs(keyword_id)
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
