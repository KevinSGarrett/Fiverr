"""S4.2 Competition Score calculator."""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from src.models import CompetitorProfile, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.contracts import CompetitionScoreResult, ScoreComponent
from src.scoring.result_set_relevance import get_result_set_validation

_GAP_FLAG_LOW_VIDEO_PRESENCE = "LOW_VIDEO_PRESENCE"
log = logging.getLogger(__name__)


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_float(value: Any, default: float) -> float:
    if value is None or isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _scoring_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    scoring_cfg = config.get("scoring")
    if not isinstance(scoring_cfg, Mapping):
        return {}
    return dict(scoring_cfg)


def _competition_config(config: dict[str, Any] | None) -> dict[str, Any]:
    scoring_cfg = _scoring_config(config)
    if not scoring_cfg:
        return {}
    competition_cfg = scoring_cfg.get("competition")
    if not isinstance(competition_cfg, Mapping):
        return {}
    return dict(competition_cfg)


def _is_profile_empty(profile: Mapping[str, Any] | None) -> bool:
    if profile is None:
        return True
    competitors = profile.get("competitors")
    if isinstance(competitors, list):
        return len(competitors) == 0
    signal_fields = (
        "mean_reviews",
        "median_price",
        "mean_price",
        "seller_level_distribution",
        "video_present_rate",
        "portfolio_present_rate",
    )
    return all(profile.get(field) in (None, {}, []) for field in signal_fields)


def _select_competitor_profile(
    per_keyword: Mapping[str, Any] | None,
    per_niche: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, str]:
    if per_keyword is not None and not _is_profile_empty(per_keyword):
        return dict(per_keyword), "per_keyword"
    if per_niche is None:
        return None, "per_niche"
    return dict(per_niche), "per_niche"


def _exclude_contaminated_competitors(
    profile: Mapping[str, Any] | None,
    contaminated_keyword_ids: set[int] | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    if not contaminated_keyword_ids:
        return dict(profile)
    competitors = profile.get("competitors")
    if not isinstance(competitors, list):
        return dict(profile)
    kept: list[Any] = []
    for competitor in competitors:
        if not isinstance(competitor, Mapping):
            kept.append(competitor)
            continue
        source_keyword_id = competitor.get("source_keyword_id")
        if source_keyword_id is None:
            kept.append(dict(competitor))
            continue
        try:
            if int(source_keyword_id) in contaminated_keyword_ids:
                continue
        except (TypeError, ValueError):
            kept.append(dict(competitor))
            continue
        kept.append(dict(competitor))
    updated = dict(profile)
    updated["competitors"] = kept
    return updated


def _quartiles(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    n = len(ordered)
    if n <= 1:
        return ordered[0] if ordered else 0.0, ordered[0] if ordered else 0.0

    def _percentile(percent: float) -> float:
        rank = (n - 1) * percent
        lower = int(math.floor(rank))
        upper = int(math.ceil(rank))
        if lower == upper:
            return ordered[lower]
        fraction = rank - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction

    return _percentile(0.25), _percentile(0.75)


def _exclude_price_outliers_iqr(prices: list[float] | None) -> tuple[list[float], int]:
    vals = [float(price) for price in (prices or []) if price is not None]
    if len(vals) < 4:
        return vals, 0
    q1, q3 = _quartiles(vals)
    iqr = q3 - q1
    lower = q1 - (1.5 * iqr)
    upper = q3 + (1.5 * iqr)
    # Preserve low-tail values for the SRDI EX-2 contract; only clear extreme outliers.
    lower = min(lower, min(vals))
    kept = [price for price in vals if lower <= price <= upper]
    return kept, len(vals) - len(kept)


def _relevance_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {
            "enable_sponsored_exclusion": True,
            "enable_zombie_filter": True,
            "top_n_for_scoring": 10,
        }
    relevance_cfg = config.get("relevance")
    if not isinstance(relevance_cfg, Mapping):
        return {
            "enable_sponsored_exclusion": True,
            "enable_zombie_filter": True,
            "top_n_for_scoring": 10,
        }
    return {
        "enable_sponsored_exclusion": bool(relevance_cfg.get("enable_sponsored_exclusion", True)),
        "enable_zombie_filter": bool(relevance_cfg.get("enable_zombie_filter", True)),
        "top_n_for_scoring": max(1, int(relevance_cfg.get("top_n_for_scoring", 10))),
    }


def _normalize_text_key(value: str) -> str:
    return value.strip().upper().replace("-", "_").replace(" ", "_")


def _normalize_level_key(value: str) -> str:
    normalized = _normalize_text_key(value)
    alias_map = {
        "TRS": "TOP_RATED",
        "TOPRATED": "TOP_RATED",
        "TOP_RATED_SELLER": "TOP_RATED",
        "LEVEL1": "LEVEL_1",
        "LEVEL2": "LEVEL_2",
        "L1": "LEVEL_1",
        "L2": "LEVEL_2",
        "NOLEVEL": "NO_LEVEL",
        "NEW_SELLER": "NO_LEVEL",
    }
    return alias_map.get(normalized, normalized)


def _normalize_gap_flags(raw_flags: Any) -> list[str]:
    if not isinstance(raw_flags, list):
        return []
    normalized: list[str] = []
    for raw_flag in raw_flags:
        if not isinstance(raw_flag, str):
            continue
        cleaned = _normalize_text_key(raw_flag)
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _extract_profile_gap_flags(profile_inputs: Mapping[str, Any]) -> list[str]:
    gap_payload = profile_inputs.get("new_seller_gap")
    raw_flags: Any = None
    if isinstance(gap_payload, Mapping):
        raw_flags = gap_payload.get("gap_flags")
    if raw_flags is None:
        raw_flags = profile_inputs.get("gap_flags")
    return _normalize_gap_flags(raw_flags)


def compute_seller_level_competition_signal(distribution: dict[str, float]) -> float:
    """
    Convert seller-level distribution into a 0-100 competition signal.

    TOP_RATED/PRO concentrations push the signal higher.
    LEVEL_1 / NO_LEVEL concentrations pull the signal lower.
    """
    if not distribution:
        return 50.0

    level_weights: dict[str, float] = {
        "PRO": 100.0,
        "TOP_RATED": 95.0,
        "LEVEL_2": 60.0,
        "LEVEL_1": 20.0,
        "NO_LEVEL": 10.0,
        "UNKNOWN": 50.0,
    }

    weighted_sum = 0.0
    total_share = 0.0
    for raw_level, raw_share in distribution.items():
        if not isinstance(raw_level, str):
            continue
        share = _coerce_float(raw_share, -1.0)
        if share <= 0.0:
            continue

        level_key = _normalize_level_key(raw_level)
        level_weight = level_weights.get(level_key)
        if level_weight is None:
            if "TOP" in level_key or "PRO" in level_key:
                level_weight = 95.0
            elif "LEVEL_2" in level_key or level_key == "2":
                level_weight = 60.0
            elif "LEVEL_1" in level_key or level_key in {"1", "NEW", "NO_LEVEL"}:
                level_weight = 20.0
            else:
                level_weight = 50.0

        weighted_sum += level_weight * share
        total_share += share

    if total_share <= 0.0:
        return 50.0
    return round(min(100.0, max(0.0, weighted_sum / total_share)), 2)


def get_competitor_profile_inputs(niche_id: str, run_id: str, db: Any) -> dict[str, Any]:
    """Return Stage 10 competitor profile benchmarks for Score 2 use."""
    if not niche_id.strip() or not run_id.strip():
        return {}

    if isinstance(db, Session):
        profile = (
            db.query(CompetitorProfile)
            .filter(
                CompetitorProfile.niche_id == niche_id,
                CompetitorProfile.run_id == run_id,
            )
            .one_or_none()
        )
        if profile is None:
            profile = (
                db.query(CompetitorProfile)
                .filter(CompetitorProfile.niche_id == niche_id)
                .order_by(CompetitorProfile.collected_at.desc(), CompetitorProfile.id.desc())
                .first()
            )
        if profile is None:
            return {}
        payload: dict[str, Any] = {
            "mean_reviews": profile.mean_reviews,
            "median_price": profile.median_price,
            "seller_level_distribution": (
                dict(profile.seller_level_distribution)
                if isinstance(profile.seller_level_distribution, dict)
                else {}
            ),
            "video_present_rate": profile.video_present_rate,
            "portfolio_present_rate": profile.portfolio_present_rate,
            "top_gig_count": profile.top_gig_count,
        }
        if isinstance(profile.new_seller_gap, dict):
            payload["new_seller_gap"] = dict(profile.new_seller_gap)
        return payload

    if hasattr(db, "get_competitor_profile_inputs"):
        loaded = db.get_competitor_profile_inputs(niche_id, run_id)
        if isinstance(loaded, Mapping):
            return dict(loaded)

    if isinstance(db, Mapping):
        direct = db.get("competitor_profile")
        if isinstance(direct, Mapping):
            return dict(direct)
    return {}


class CompetitionScoreCalculator:
    """Calculate competition strength from marketplace and seller signals."""

    _COUNT_WEIGHT = 0.20
    _REVIEWS_WEIGHT = 0.25
    _SELLER_LEVEL_WEIGHT = 0.20
    _HUNDRED_PLUS_WEIGHT = 0.15
    _PRO_VERIFIED_WEIGHT = 0.10
    _PRICE_WEIGHT = 0.05
    _LLM_WEIGHT = 0.05

    _LEVEL_MAP = {
        "level 1": 20.0,
        "level1": 20.0,
        "1": 20.0,
        "level 2": 60.0,
        "level2": 60.0,
        "2": 60.0,
        "top rated": 100.0,
        "top rated seller": 100.0,
        "trs": 100.0,
        "pro": 100.0,
    }

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> CompetitionScoreResult:
        """Calculate a competition score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db, config=config)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0
        profile_used = bool(signals.get("_profile_used"))
        competitor_profile_source = (
            str(signals.get("_competitor_profile_source"))
            if signals.get("_competitor_profile_source") is not None
            else None
        )
        raw_price_outliers_excluded = signals.get("_price_outliers_excluded")
        price_outliers_excluded = (
            int(raw_price_outliers_excluded)
            if isinstance(raw_price_outliers_excluded, int | float)
            else None
        )

        total_result_count = self._as_float(signals.get("total_result_count"))
        if total_result_count is not None:
            count_score = self._normalize_count(total_result_count)
            score_components["fiverr_count"] = ScoreComponent(
                value=count_score,
                weight=self._COUNT_WEIGHT,
                raw=total_result_count,
            )
            weighted_sum += count_score * self._COUNT_WEIGHT
            total_weight_available += self._COUNT_WEIGHT
            source_evidence.append("fiverr_search_results.total_result_count")
        else:
            missing_data_warnings.append("Missing Fiverr total result count.")

        avg_review_count_top10 = self._as_float(signals.get("avg_review_count_top10"))
        if avg_review_count_top10 is not None:
            review_score = self._normalize_review_count(avg_review_count_top10)
            score_components["avg_reviews"] = ScoreComponent(
                value=review_score,
                weight=self._REVIEWS_WEIGHT,
                raw=avg_review_count_top10,
            )
            weighted_sum += review_score * self._REVIEWS_WEIGHT
            total_weight_available += self._REVIEWS_WEIGHT
            if bool(signals.get("_profile_used_for_reviews")):
                source_evidence.append("competitor_profiles.mean_reviews")
            else:
                source_evidence.append("gig_details.avg_review_count_top10")
        else:
            missing_data_warnings.append("Missing average review count for top 10 gigs.")

        avg_seller_level_top10 = signals.get("avg_seller_level_top10")
        seller_level_raw = (
            signals.get("seller_level_distribution")
            if bool(signals.get("_profile_used_for_seller_level"))
            else avg_seller_level_top10
        )
        seller_level_score = self._normalize_seller_level(avg_seller_level_top10)
        if seller_level_score is not None:
            score_components["seller_level"] = ScoreComponent(
                value=seller_level_score,
                weight=self._SELLER_LEVEL_WEIGHT,
                raw=seller_level_raw,
            )
            weighted_sum += seller_level_score * self._SELLER_LEVEL_WEIGHT
            total_weight_available += self._SELLER_LEVEL_WEIGHT
            if bool(signals.get("_profile_used_for_seller_level")):
                source_evidence.append("competitor_profiles.seller_level_distribution")
            else:
                source_evidence.append("seller_profiles.avg_seller_level_top10")
        else:
            missing_data_warnings.append("Missing average seller level in top 10 gigs.")

        proportion_with_100_plus_reviews = self._as_float(signals.get("proportion_with_100_plus_reviews"))
        if proportion_with_100_plus_reviews is not None:
            clamped_ratio = max(0.0, min(1.0, proportion_with_100_plus_reviews))
            ratio_score = clamped_ratio * 100.0
            score_components["hundred_plus_review_ratio"] = ScoreComponent(
                value=ratio_score,
                weight=self._HUNDRED_PLUS_WEIGHT,
                raw=proportion_with_100_plus_reviews,
            )
            weighted_sum += ratio_score * self._HUNDRED_PLUS_WEIGHT
            total_weight_available += self._HUNDRED_PLUS_WEIGHT
            source_evidence.append("gig_details.proportion_with_100_plus_reviews")
        else:
            missing_data_warnings.append("Missing 100+ reviews ratio in top 10 gigs.")

        pro_verified_presence_ratio = self._as_float(signals.get("pro_verified_presence_ratio"))
        if pro_verified_presence_ratio is not None:
            pro_ratio_score = max(0.0, min(1.0, pro_verified_presence_ratio)) * 100.0
            score_components["pro_verified_presence"] = ScoreComponent(
                value=pro_ratio_score,
                weight=self._PRO_VERIFIED_WEIGHT,
                raw=pro_verified_presence_ratio,
            )
            weighted_sum += pro_ratio_score * self._PRO_VERIFIED_WEIGHT
            total_weight_available += self._PRO_VERIFIED_WEIGHT
            source_evidence.append("seller_profiles.pro_verified_presence_ratio")
        else:
            missing_data_warnings.append("Missing pro-verified seller presence ratio.")

        avg_starting_price_top10 = self._as_float(signals.get("avg_starting_price_top10"))
        if avg_starting_price_top10 is not None:
            price_score = self._normalize_price(avg_starting_price_top10)
            price_note = (
                f"Excluded {price_outliers_excluded} price outlier(s) via IQR."
                if price_outliers_excluded
                else ""
            )
            score_components["avg_starting_price"] = ScoreComponent(
                value=price_score,
                weight=self._PRICE_WEIGHT,
                raw=avg_starting_price_top10,
                note=price_note,
            )
            weighted_sum += price_score * self._PRICE_WEIGHT
            total_weight_available += self._PRICE_WEIGHT
            if bool(signals.get("_profile_used_for_price")):
                source_evidence.append("competitor_profiles.median_price")
            else:
                source_evidence.append("gig_details.avg_starting_price_top10")
        else:
            missing_data_warnings.append("Missing average starting price for top 10 gigs.")

        llm_competitor_strength_rating = self._as_float(signals.get("llm_competitor_strength_rating"))
        if llm_competitor_strength_rating is not None:
            llm_score = self._normalize_llm_competitor_strength(llm_competitor_strength_rating)
            llm_note = str(signals.get("_llm_adjustment_note") or "")
            score_components["llm_competitor_strength"] = ScoreComponent(
                value=llm_score,
                weight=self._LLM_WEIGHT,
                raw=llm_competitor_strength_rating,
                note=llm_note,
            )
            weighted_sum += llm_score * self._LLM_WEIGHT
            total_weight_available += self._LLM_WEIGHT
            if bool(signals.get("_profile_used_for_llm")):
                source_evidence.append("competitor_profiles.new_seller_gap")
            else:
                source_evidence.append("llm.competitor_strength_rating")
        else:
            confidence_breakdown["missing_llm_competitor_strength"] = -0.10
            missing_data_warnings.append("Missing LLM competitor strength rating.")

        missing_gig_detail_fields = [
            "avg_review_count_top10",
            "avg_seller_level_top10",
            "proportion_with_100_plus_reviews",
            "pro_verified_presence_ratio",
            "avg_starting_price_top10",
        ]
        if not any(self._has_value(signals.get(field_name)) for field_name in missing_gig_detail_fields):
            confidence_breakdown["missing_gig_detail_dataset"] = -0.20

        if total_weight_available < 0.30:
            return CompetitionScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient competition signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate a competition explanation.",
                total_weight_available=total_weight_available,
                price_outliers_excluded=price_outliers_excluded,
                competitor_profile_source=competitor_profile_source,
            )

        competition_score = weighted_sum / total_weight_available
        competition_score = round(min(100.0, max(0.0, competition_score)), 2)
        return CompetitionScoreResult(
            keyword_id=keyword_id,
            score_value=competition_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Competition calculated from available marketplace strength signals"
                " with confidence penalties for missing data."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Competition reflects how entrenched the top listings are by review density,"
                " seller seniority, pro presence, pricing, and optional LLM synthesis."
                + (
                    " CompetitorProfile benchmarks were applied where available."
                    if profile_used
                    else ""
                )
            ),
            total_weight_available=total_weight_available,
            price_outliers_excluded=price_outliers_excluded,
            competitor_profile_source=competitor_profile_source,
        )

    @staticmethod
    def _normalize_count(total_result_count: float) -> float:
        if total_result_count <= 0:
            return 0.0
        return min(100.0, (math.log10(total_result_count + 1.0) / 4.0) * 100.0)

    @staticmethod
    def _normalize_review_count(avg_review_count: float) -> float:
        if avg_review_count <= 0:
            return 0.0
        return min(100.0, (math.log10(avg_review_count + 1.0) / 4.0) * 100.0)

    def _normalize_seller_level(self, raw_level: Any) -> float | None:
        if raw_level is None:
            return None
        if isinstance(raw_level, int | float):
            if raw_level <= 3:
                return max(0.0, min(100.0, float(raw_level) * 20.0))
            return max(0.0, min(100.0, float(raw_level)))
        if isinstance(raw_level, str):
            normalized = raw_level.strip().lower()
            return self._LEVEL_MAP.get(normalized)
        return None

    @staticmethod
    def _normalize_price(avg_price: float) -> float:
        if avg_price <= 0:
            return 0.0
        return min(100.0, avg_price * 2.0)

    @staticmethod
    def _normalize_llm_competitor_strength(raw_rating: float) -> float:
        if raw_rating <= 10.0:
            return max(0.0, min(100.0, raw_rating * 10.0))
        return max(0.0, min(100.0, raw_rating))

    def _load_signals(
        self,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        use_profile = _coerce_bool(_competition_config(config).get("use_competitor_profile"), True)
        use_per_keyword_profile = _coerce_bool(_competition_config(config).get("use_per_keyword_profile"), False)
        exclude_contaminated = _coerce_bool(_competition_config(config).get("exclude_contaminated"), False)
        exclude_price_outliers = _coerce_bool(_scoring_config(config).get("exclude_price_outliers"), False)
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db, config=config)
        loaded: dict[str, Any] = {}
        if hasattr(db, "get_competition_inputs"):
            loaded = db.get_competition_inputs(keyword_id)
            if isinstance(loaded, Mapping):
                loaded = dict(loaded)
        elif isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                loaded = dict(loaded)

        if not loaded:
            return {}
        if exclude_price_outliers and isinstance(loaded.get("top10_prices"), list):
            kept_prices, excluded_count = _exclude_price_outliers_iqr(
                [float(price) for price in loaded.get("top10_prices", []) if self._as_float(price) is not None]
            )
            loaded["top10_prices"] = kept_prices
            loaded["avg_starting_price_top10"] = (sum(kept_prices) / len(kept_prices)) if kept_prices else None
            loaded["_price_outliers_excluded"] = excluded_count
        if not use_profile:
            loaded.pop("competitor_profile", None)
            loaded.pop("competitor_profile_per_keyword", None)
            return loaded

        per_keyword_profile = loaded.get("competitor_profile_per_keyword")
        per_niche_profile = loaded.get("competitor_profile")
        selected_profile: dict[str, Any] | None = None
        selected_source: str | None = None
        if use_per_keyword_profile:
            selected_profile, selected_source = _select_competitor_profile(
                dict(per_keyword_profile) if isinstance(per_keyword_profile, Mapping) else None,
                dict(per_niche_profile) if isinstance(per_niche_profile, Mapping) else None,
            )
        elif isinstance(per_niche_profile, Mapping):
            selected_profile = dict(per_niche_profile)
        if selected_profile is not None and exclude_contaminated:
            contaminated_ids: set[int] = set()
            raw_ids = loaded.get("contaminated_keyword_ids")
            if isinstance(raw_ids, list):
                for raw_id in raw_ids:
                    try:
                        contaminated_ids.add(int(raw_id))
                    except (TypeError, ValueError):
                        continue
            selected_profile = _exclude_contaminated_competitors(selected_profile, contaminated_ids)
        if selected_profile is not None:
            merged = self._merge_competitor_profile_signals(loaded, selected_profile)
            if selected_source is not None:
                merged["_competitor_profile_source"] = selected_source
            return merged
        return loaded

    def _load_signals_from_db(
        self,
        keyword_id: int,
        session: Session,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        relevance_cfg = _relevance_config(config)
        scoring_cfg = _scoring_config(config)
        competition_cfg = _competition_config(config)
        top_n_for_scoring = int(relevance_cfg["top_n_for_scoring"])
        candidate_window = max(top_n_for_scoring, 10) * 3

        def _eligible(gig: Gig) -> bool:
            if relevance_cfg["enable_sponsored_exclusion"] and getattr(gig, "is_sponsored", None) is True:
                return False
            if relevance_cfg["enable_zombie_filter"] and bool(getattr(gig, "is_zombie", False)):
                return False
            return True

        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        total_result_count = self._resolve_marketplace_result_count(session, keyword_id)
        top_gigs = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= candidate_window)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        top_gigs = [gig for gig in top_gigs if _eligible(gig)][:top_n_for_scoring]
        rsv = get_result_set_validation(keyword_id, session)
        if rsv is not None and rsv.result_set_relevance_score is not None and rsv.result_set_relevance_score < 0.80:
            relevance_filtered = [gig for gig in top_gigs if gig.relevance_flag is True]
            filtered_count = len(top_gigs) - len(relevance_filtered)
            if len(top_gigs) > 0 and (filtered_count / len(top_gigs)) > 0.20:
                log.warning("competition: >20%% gigs relevance-filtered kw=%s", keyword_id)
            if not relevance_filtered:
                log.warning("competition: all gigs filtered by relevance; full-set fallback kw=%s", keyword_id)
            else:
                top_gigs = relevance_filtered
                log.debug("competition: relevance_filtered_gigs=%s kw=%s", filtered_count, keyword_id)
        top_sellers = [gig.seller for gig in top_gigs if gig.seller is not None]
        review_counts = [float(gig.review_count) for gig in top_gigs if gig.review_count is not None]
        starting_prices = [float(gig.starting_price) for gig in top_gigs if gig.starting_price is not None]
        price_outliers_excluded: int | None = None
        if _coerce_bool(scoring_cfg.get("exclude_price_outliers"), False):
            starting_prices, price_outliers_excluded = _exclude_price_outliers_iqr(starting_prices)
        seller_level_values = [self._seller_level_value(seller.level) for seller in top_sellers]
        normalized_levels = [value for value in seller_level_values if value is not None]
        pro_verified_flags = [self._is_pro_verified(seller) for seller in top_sellers]
        keyword_meta = keyword.metadata_json if keyword and isinstance(keyword.metadata_json, dict) else {}
        signals: dict[str, Any] = {
            "total_result_count": total_result_count,
            "avg_review_count_top10": (sum(review_counts) / len(review_counts)) if review_counts else None,
            "avg_seller_level_top10": (sum(normalized_levels) / len(normalized_levels)) if normalized_levels else None,
            "proportion_with_100_plus_reviews": (
                sum(1 for count in review_counts if count >= 100.0) / len(review_counts)
                if review_counts
                else None
            ),
            "pro_verified_presence_ratio": (
                sum(1 for is_verified in pro_verified_flags if is_verified) / len(pro_verified_flags)
                if pro_verified_flags
                else None
            ),
            "avg_starting_price_top10": (sum(starting_prices) / len(starting_prices)) if starting_prices else None,
            "llm_competitor_strength_rating": self._as_float(keyword_meta.get("llm_competitor_strength_rating")),
        }
        if price_outliers_excluded is not None:
            signals["_price_outliers_excluded"] = price_outliers_excluded

        use_profile = _coerce_bool(_competition_config(config).get("use_competitor_profile"), True)
        if not use_profile:
            return signals

        niche_slug: str | None = None
        if keyword is not None and keyword.niche_id is not None:
            niche = session.query(Niche).filter(Niche.id == keyword.niche_id).first()
            if niche is not None and isinstance(niche.slug, str) and niche.slug.strip():
                niche_slug = niche.slug.strip()

        run_id: str | None = None
        try:
            latest_search_row = (
                session.query(SearchResult.run_id)
                .filter(SearchResult.keyword_id == keyword_id)
                .order_by(SearchResult.collected_at.desc(), SearchResult.id.desc())
                .first()
            )
        except Exception:
            latest_search_row = None
        if latest_search_row and isinstance(latest_search_row[0], str) and latest_search_row[0].strip():
            run_id = latest_search_row[0].strip()
        if run_id is None:
            for gig in top_gigs:
                if isinstance(gig.run_id, str) and gig.run_id.strip():
                    run_id = gig.run_id.strip()
                    break

        if niche_slug is None or run_id is None:
            return signals

        profile_inputs = get_competitor_profile_inputs(niche_slug, run_id, session)
        if not profile_inputs:
            return signals
        selected_profile: dict[str, Any] = dict(profile_inputs)
        selected_source = "per_niche"
        if _coerce_bool(competition_cfg.get("use_per_keyword_profile"), False):
            per_keyword_raw = keyword_meta.get("competitor_profile_per_keyword")
            per_keyword_profile = dict(per_keyword_raw) if isinstance(per_keyword_raw, Mapping) else None
            selected_profile_candidate, selected_source = _select_competitor_profile(
                per_keyword_profile,
                profile_inputs,
            )
            selected_profile = selected_profile_candidate or {}
        if _coerce_bool(competition_cfg.get("exclude_contaminated"), False):
            contaminated_ids: set[int] = set()
            raw_ids = keyword_meta.get("contaminated_keyword_ids")
            if isinstance(raw_ids, list):
                for raw_id in raw_ids:
                    try:
                        contaminated_ids.add(int(raw_id))
                    except (TypeError, ValueError):
                        continue
            selected_profile = _exclude_contaminated_competitors(selected_profile, contaminated_ids) or {}

        merged = self._merge_competitor_profile_signals(signals, selected_profile)
        merged["_profile_niche_id"] = niche_slug
        merged["_profile_run_id"] = run_id
        merged["_competitor_profile_source"] = selected_source
        return merged

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _has_value(value: Any) -> bool:
        return value is not None

    @staticmethod
    def _resolve_marketplace_result_count(session: Session, keyword_id: int) -> float | None:
        max_total_result_count = (
            session.query(SearchResult.total_result_count)
            .filter(
                SearchResult.keyword_id == keyword_id,
                SearchResult.total_result_count.isnot(None),
            )
            .order_by(SearchResult.total_result_count.desc())
            .first()
        )
        if max_total_result_count is not None and max_total_result_count[0] is not None:
            return float(max_total_result_count[0])

        # Only use row-count as a coarse fallback when top-10 coverage is complete.
        # Sparse partial rows can materially understate competition pressure.
        fallback_count = (
            session.query(SearchResult)
            .filter(
                SearchResult.keyword_id == keyword_id,
                SearchResult.rank.isnot(None),
                SearchResult.rank <= 10,
            )
            .count()
        )
        if fallback_count >= 10:
            return float(fallback_count)
        return None

    def _seller_level_value(self, level: str | None) -> float | None:
        if not level:
            return None
        return self._normalize_seller_level(level)

    def _merge_competitor_profile_signals(
        self,
        signals: dict[str, Any],
        profile_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(signals)
        profile_used = False

        mean_reviews = self._as_float(profile_inputs.get("mean_reviews"))
        if mean_reviews is not None:
            merged["avg_review_count_top10"] = mean_reviews
            merged["_profile_used_for_reviews"] = True
            profile_used = True

        seller_level_distribution = profile_inputs.get("seller_level_distribution")
        if isinstance(seller_level_distribution, Mapping):
            distribution = {
                str(level): _coerce_float(share, 0.0)
                for level, share in seller_level_distribution.items()
                if isinstance(level, str)
            }
            if distribution:
                merged["seller_level_distribution"] = distribution
                merged["avg_seller_level_top10"] = compute_seller_level_competition_signal(distribution)
                merged["_profile_used_for_seller_level"] = True
                profile_used = True

        median_price = self._as_float(profile_inputs.get("median_price"))
        if median_price is None:
            median_price = self._as_float(profile_inputs.get("mean_price"))
        if median_price is not None:
            merged["avg_starting_price_top10"] = median_price
            merged["_profile_used_for_price"] = True
            profile_used = True

        llm_rating, adjustment_note = self._derive_profile_llm_rating(
            profile_inputs=profile_inputs,
            existing_rating=self._as_float(merged.get("llm_competitor_strength_rating")),
        )
        if llm_rating is not None:
            merged["llm_competitor_strength_rating"] = llm_rating
            merged["_profile_used_for_llm"] = True
            profile_used = True
        if adjustment_note:
            merged["_llm_adjustment_note"] = adjustment_note

        profile_gap_flags = _extract_profile_gap_flags(profile_inputs)
        if profile_gap_flags:
            merged["_profile_gap_flags"] = profile_gap_flags

        merged["_profile_used"] = profile_used
        return merged

    def _derive_profile_llm_rating(
        self,
        *,
        profile_inputs: Mapping[str, Any],
        existing_rating: float | None,
    ) -> tuple[float | None, str]:
        rating = existing_rating
        adjustment_note = ""

        if rating is None:
            distribution = profile_inputs.get("seller_level_distribution")
            if isinstance(distribution, Mapping):
                normalized_distribution = {
                    str(level): _coerce_float(share, 0.0)
                    for level, share in distribution.items()
                    if isinstance(level, str)
                }
                if normalized_distribution:
                    rating = compute_seller_level_competition_signal(normalized_distribution) / 10.0

            mean_reviews = self._as_float(profile_inputs.get("mean_reviews"))
            if rating is not None and mean_reviews is not None and mean_reviews > 0:
                review_boost = min(2.0, math.log10(mean_reviews + 1.0))
                rating = min(10.0, rating + (review_boost * 0.35))

        if rating is None:
            return None, adjustment_note

        profile_gap_flags = _extract_profile_gap_flags(profile_inputs)
        if _GAP_FLAG_LOW_VIDEO_PRESENCE in profile_gap_flags:
            rating = max(0.0, rating - 1.0)
            adjustment_note = (
                "LOW_VIDEO_PRESENCE gap flag reduced LLM competitor-strength component "
                "to reflect additional new-seller opportunity."
            )

        return max(0.0, min(10.0, rating)), adjustment_note

    @staticmethod
    def _is_pro_verified(seller: Seller) -> bool:
        metadata = seller.metadata_json if isinstance(seller.metadata_json, dict) else {}
        for key in ("is_pro", "pro_verified", "fiverr_pro"):
            value = metadata.get(key)
            if isinstance(value, bool):
                return value
        return False
