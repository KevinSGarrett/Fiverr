"""S4.11 Confidence Score modifier calculator."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models import (
    ExternalSignal,
    Gig,
    GigVisualAnalysis,
    Keyword,
    KeywordScore,
    NicheConfigRecord,
    SearchResult,
    Seller,
)


class ConfidenceScoreModifier:
    """Calculate confidence modifier used by final recommendation scoring."""

    def __init__(self) -> None:
        self.last_breakdown: dict[str, float] = {}

    def calculate(
        self,
        keyword_id: int,
        run_context: dict[str, Any] | None,
        db: Any,
    ) -> float:
        """Return the confidence modifier in range [0.0, 1.0]."""
        modifier, breakdown = self.calculate_with_breakdown(keyword_id, run_context, db)
        self.last_breakdown = breakdown
        return modifier

    def calculate_with_breakdown(
        self,
        keyword_id: int,
        run_context: dict[str, Any] | None,
        db: Any,
    ) -> tuple[float, dict[str, float]]:
        """Return confidence modifier and deduction breakdown."""
        context = self._load_context(keyword_id, run_context, db)

        completeness = self._clamp_0_1(self._as_float(context.get("data_completeness_ratio"), 1.0))
        freshness = self._clamp_0_1(self._as_float(context.get("data_freshness_score"), 1.0))
        diversity = self._clamp_0_1(self._as_float(context.get("source_diversity_score"), 1.0))
        llm_completion = self._clamp_0_1(self._as_float(context.get("llm_analysis_completion_ratio"), 1.0))

        base_modifier = ((completeness * 0.50) + (freshness * 0.30) + (diversity * 0.20)) * llm_completion

        deductions: dict[str, float] = {}
        if not self._as_bool(context.get("google_trends_available"), True):
            deductions["missing_google_trends"] = -0.15
        if not self._as_bool(context.get("gig_detail_collected"), True):
            deductions["missing_gig_detail"] = -0.20
        if not self._as_bool(context.get("seller_profiles_collected"), True):
            deductions["missing_seller_profiles"] = -0.10
        if not self._as_bool(context.get("reddit_signals_available"), True):
            deductions["missing_reddit_signals"] = -0.05

        incomplete_gig_count = max(0.0, self._as_float(context.get("llm_gig_quality_incomplete_count"), 0.0))
        llm_gig_quality_penalty = max(-0.20, -(incomplete_gig_count * 0.08))
        if llm_gig_quality_penalty < 0:
            deductions["llm_gig_quality_incomplete"] = llm_gig_quality_penalty

        if self._as_bool(context.get("llm_competitor_synthesis_failed"), False):
            deductions["llm_competitor_synthesis_failed"] = -0.10

        data_age_hours = self._as_float(context.get("data_age_hours"), 0.0)
        data_ttl_hours = self._as_float(context.get("data_ttl_hours"), 168.0)
        if data_ttl_hours > 0 and data_age_hours > (2.0 * data_ttl_hours):
            deductions["data_stale_over_2x_ttl"] = -0.15

        mode = str(context.get("mode", "")).strip().lower()
        if mode in {"keyword_only", "feasibility"}:
            deductions["partial_depth_mode"] = -0.25

        if self._as_bool(context.get("enable_zombie_filter"), True):
            zombie_fraction = max(0.0, self._as_float(context.get("zombie_fraction"), 0.0))
            if zombie_fraction >= 0.50:
                deductions["zombie_concentration_high"] = -0.10
            elif zombie_fraction >= 0.25:
                deductions["zombie_concentration_moderate"] = -0.05

        deduction_total = sum(deductions.values())
        raw_modifier = base_modifier + deduction_total
        final_modifier = self._clamp_0_1(raw_modifier)

        breakdown: dict[str, float] = {
            "data_completeness_ratio": completeness,
            "data_freshness_score": freshness,
            "source_diversity_score": diversity,
            "llm_analysis_completion_ratio": llm_completion,
            "base_modifier": round(base_modifier, 4),
        }
        breakdown.update({key: round(value, 4) for key, value in deductions.items()})
        breakdown["deduction_total"] = round(deduction_total, 4)
        breakdown["remaining_modifier"] = round(final_modifier, 4)

        return round(final_modifier, 4), breakdown

    def _load_context(
        self,
        keyword_id: int,
        run_context: dict[str, Any] | None,
        db: Any,
    ) -> dict[str, Any]:
        context = dict(run_context or {})
        if context:
            return context
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if db is not None and hasattr(db, "get_confidence_inputs"):
            loaded = db.get_confidence_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        top_results = (
            session.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        gig_ids = [result.gig_id for result in top_results if result.gig_id is not None]
        seller_ids = [
            seller_id
            for seller_id in (
                session.query(Gig.seller_id)
                .filter(Gig.id.in_(gig_ids))
                .all()
                if gig_ids
                else []
            )
            if seller_id[0] is not None
        ]
        gig_visual_count = (
            session.query(GigVisualAnalysis)
            .join(Gig, GigVisualAnalysis.gig_id == Gig.id)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id)
            .count()
        )
        gig_detail_collected = (gig_visual_count > 0) or (len(gig_ids) > 0)
        seller_profiles_collected = len(seller_ids) > 0
        reddit_count = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type.in_(["reddit_demand", "reddit_activity"]),
            )
            .count()
        )
        google_trends_available = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == "google_trends",
            )
            .count()
            > 0
        )
        freshest = self._latest_timestamp(keyword, top_results, keyword_id, session)
        now = datetime.now(UTC)
        data_age_hours = (
            max(0.0, (now - freshest).total_seconds() / 3600.0)
            if freshest is not None and freshest.tzinfo is not None
            else 0.0
        )
        current_depth = "standard"
        if keyword is not None:
            config = session.query(NicheConfigRecord).filter(NicheConfigRecord.niche_id == str(keyword.niche_id)).first()
            if config is not None and config.depth:
                current_depth = str(config.depth)
        # Reddit is treated as an explicit deduction signal below; excluding it from
        # base completeness/diversity avoids double-penalizing missing Reddit data.
        available_core_sources = sum([google_trends_available, gig_detail_collected, seller_profiles_collected])
        source_diversity = min(1.0, available_core_sources / 3.0)
        data_completeness = min(1.0, available_core_sources / 3.0)
        return {
            "data_completeness_ratio": data_completeness,
            "data_freshness_score": max(0.0, min(1.0, 1.0 - (data_age_hours / 168.0))),
            "source_diversity_score": source_diversity,
            "llm_analysis_completion_ratio": 1.0,
            "google_trends_available": google_trends_available,
            "gig_detail_collected": gig_detail_collected,
            "seller_profiles_collected": seller_profiles_collected,
            "reddit_signals_available": reddit_count > 0,
            "llm_gig_quality_incomplete_count": 0.0,
            "llm_competitor_synthesis_failed": False,
            "data_age_hours": data_age_hours,
            "data_ttl_hours": 168.0,
            "mode": current_depth,
        }

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return default

    @staticmethod
    def _clamp_0_1(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _latest_timestamp(
        keyword: Keyword | None,
        top_results: list[SearchResult],
        keyword_id: int,
        session: Session,
    ) -> datetime | None:
        timestamps: list[datetime] = []
        if keyword is not None and isinstance(keyword.updated_at, datetime):
            timestamps.append(keyword.updated_at)
        for result in top_results:
            if isinstance(result.updated_at, datetime):
                timestamps.append(result.updated_at)
        newest_signal = (
            session.query(ExternalSignal)
            .filter(ExternalSignal.keyword_id == keyword_id)
            .order_by(ExternalSignal.updated_at.desc())
            .first()
        )
        if newest_signal is not None and isinstance(newest_signal.updated_at, datetime):
            timestamps.append(newest_signal.updated_at)
        newest_gig = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id)
            .order_by(Gig.updated_at.desc())
            .first()
        )
        if newest_gig is not None and isinstance(newest_gig.updated_at, datetime):
            timestamps.append(newest_gig.updated_at)
        newest_seller = (
            session.query(Seller)
            .join(Gig, Gig.seller_id == Seller.id)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id)
            .order_by(Seller.updated_at.desc())
            .first()
        )
        if newest_seller is not None and isinstance(newest_seller.updated_at, datetime):
            timestamps.append(newest_seller.updated_at)
        if not timestamps:
            return None
        return max(timestamps)


def compute_confidence_score(
    keyword_id: int,
    db: Any,
    run_context: dict[str, Any] | None = None,
) -> float:
    """
    Compute confidence modifier with compatibility for legacy call sites.

    Behavior:
    1) Prefer latest persisted `keyword_scores.confidence_modifier` for the keyword
       when a DB session is available and no explicit run context is provided.
    2) Fall back to live recomputation via `ConfidenceScoreModifier`.
    """
    if run_context is None and isinstance(db, Session):
        latest_persisted = (
            db.query(KeywordScore)
            .filter(
                KeywordScore.keyword_id == keyword_id,
                KeywordScore.confidence_modifier.isnot(None),
            )
            .order_by(KeywordScore.final_score.desc(), KeywordScore.id.desc())
            .first()
        )
        if latest_persisted is not None and latest_persisted.confidence_modifier is not None:
            return float(latest_persisted.confidence_modifier)

    calculator = ConfidenceScoreModifier()
    return calculator.calculate(keyword_id=keyword_id, run_context=run_context, db=db)
