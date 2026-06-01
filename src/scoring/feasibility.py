"""S4.4 New Seller Feasibility Score calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any
from urllib.parse import unquote, urlsplit

from sqlalchemy.orm import Session

from src.models import CompetitorProfile, Gig, Keyword, Niche, SearchResult
from src.scoring.contracts import FeasibilityScoreResult, ScoreComponent

_SUPPORTED_GAP_FLAGS = {"LOW_VIDEO_PRESENCE", "LOW_PORTFOLIO_PRESENCE", "HIGH_PRICE_VARIANCE"}
_DEFAULT_GAP_BOOST_PER_FLAG = 10.0
_DEFAULT_MAX_GAP_BOOST = 30.0


def _coerce_float(value: Any, default: float) -> float:
    if value is None or isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _feasibility_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    scoring_cfg = config.get("scoring")
    if not isinstance(scoring_cfg, Mapping):
        return {}
    feasibility_cfg = scoring_cfg.get("feasibility")
    if not isinstance(feasibility_cfg, Mapping):
        return {}
    return dict(feasibility_cfg)


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


def _clean_gig_set(gigs: list[Gig]) -> list[Gig]:
    """Return relevant non-sponsored non-zombie gigs."""
    cleaned: list[Gig] = []
    for gig in gigs:
        is_relevant = bool(getattr(gig, "is_relevant", getattr(gig, "relevance_flag", False)))
        if is_relevant and not bool(getattr(gig, "is_sponsored", False)) and not bool(getattr(gig, "is_zombie", False)):
            cleaned.append(gig)
    return cleaned


def _normalize_gap_flags(raw_flags: Any) -> list[str]:
    if not isinstance(raw_flags, list):
        return []
    normalized: list[str] = []
    for raw_flag in raw_flags:
        if not isinstance(raw_flag, str):
            continue
        cleaned = raw_flag.strip().upper().replace("-", "_").replace(" ", "_")
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _extract_gap_flags_from_profile(profile_payload: Mapping[str, Any]) -> list[str]:
    gap_payload = profile_payload.get("new_seller_gap")
    raw_flags: Any = None
    if isinstance(gap_payload, Mapping):
        raw_flags = gap_payload.get("gap_flags")
    if raw_flags is None:
        raw_flags = profile_payload.get("gap_flags")
    return _normalize_gap_flags(raw_flags)


def _get_feasibility_gap_signal_details(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any] | None = None,
) -> tuple[float, list[str]]:
    if not niche_id.strip() or not run_id.strip():
        return 0.0, []

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
            return 0.0, []
        profile_payload: Mapping[str, Any] = (
            profile.new_seller_gap if isinstance(profile.new_seller_gap, Mapping) else {}
        )
        normalized_flags = _extract_gap_flags_from_profile({"new_seller_gap": profile_payload})
    elif hasattr(db, "get_competitor_profile_inputs"):
        loaded = db.get_competitor_profile_inputs(niche_id, run_id)
        normalized_flags = _extract_gap_flags_from_profile(dict(loaded or {}))
    else:
        normalized_flags = []

    matched_flags = sorted({flag for flag in normalized_flags if flag in _SUPPORTED_GAP_FLAGS})
    if not matched_flags:
        return 0.0, []

    feasibility_cfg = _feasibility_config(config)
    gap_boost_per_flag = max(
        0.0,
        _coerce_float(feasibility_cfg.get("gap_boost_per_flag"), _DEFAULT_GAP_BOOST_PER_FLAG),
    )
    max_gap_boost = max(
        0.0,
        _coerce_float(feasibility_cfg.get("max_gap_boost"), _DEFAULT_MAX_GAP_BOOST),
    )
    boost_value = min(max_gap_boost, gap_boost_per_flag * len(matched_flags))
    return round(max(0.0, boost_value), 2), matched_flags


def get_feasibility_gap_signal(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any] | None = None,
) -> float:
    """Return 0.0–30.0 feasibility boost from CompetitorProfile gap flags."""
    boost, _ = _get_feasibility_gap_signal_details(
        niche_id=niche_id,
        run_id=run_id,
        db=db,
        config=config,
    )
    return boost


class NewSellerFeasibilityCalculator:
    """Calculate how feasible a keyword is for a brand-new seller."""

    DEFAULT_WEIGHT = 0.15
    _LEVEL1_RATIO_WEIGHT = 0.30
    _LOWEST_REVIEW_WEIGHT = 0.25
    _PRICE_DIVERSITY_WEIGHT = 0.15
    _LLM_WEAKNESS_WEIGHT = 0.20
    _LLM_ENTRY_GAP_WEIGHT = 0.10

    _TIER2_KEYWORD_MARKERS = ("python", "ai tool", "ai agent", "workflow", "scraping")

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> FeasibilityScoreResult:
        """Calculate a feasibility score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db, config=config)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0
        clean_gig_count = self._as_int(signals.get("clean_gig_count"))

        level1_ratio = self._resolve_level1_ratio(signals)
        if level1_ratio is not None:
            level1_score = max(0.0, min(100.0, level1_ratio * 100.0))
            score_components["level1_or_new_ratio"] = ScoreComponent(
                value=level1_score,
                weight=self._LEVEL1_RATIO_WEIGHT,
                raw=level1_ratio,
            )
            weighted_sum += level1_score * self._LEVEL1_RATIO_WEIGHT
            total_weight_available += self._LEVEL1_RATIO_WEIGHT
            source_evidence.append("seller_profiles.level1_or_new_ratio_top10")
        else:
            missing_data_warnings.append("Missing Level 1 / no-level seller ratio in top 10.")

        lowest_review_count = self._as_float(signals.get("lowest_ranked_review_count_page1"))
        if lowest_review_count is not None:
            lowest_review_score = self._normalize_entry_review_barrier(lowest_review_count)
            score_components["lowest_ranked_review_barrier"] = ScoreComponent(
                value=lowest_review_score,
                weight=self._LOWEST_REVIEW_WEIGHT,
                raw=lowest_review_count,
            )
            weighted_sum += lowest_review_score * self._LOWEST_REVIEW_WEIGHT
            total_weight_available += self._LOWEST_REVIEW_WEIGHT
            source_evidence.append("gig_details.lowest_ranked_review_count_page1")
        else:
            missing_data_warnings.append("Missing review count of lowest-ranking gig on page 1.")

        price_diversity_signal = self._resolve_price_diversity_score(signals)
        if price_diversity_signal is not None:
            score_components["price_diversity"] = ScoreComponent(
                value=price_diversity_signal,
                weight=self._PRICE_DIVERSITY_WEIGHT,
                raw=signals.get("price_diversity_top10"),
            )
            weighted_sum += price_diversity_signal * self._PRICE_DIVERSITY_WEIGHT
            total_weight_available += self._PRICE_DIVERSITY_WEIGHT
            source_evidence.append("gig_details.price_diversity_top10")
        else:
            missing_data_warnings.append("Missing top-result price diversity signal.")

        llm_weakness_avg = self._as_float(signals.get("llm_gig_quality_weakness_avg_top10"))
        if llm_weakness_avg is not None:
            weakness_score = self._normalize_llm_score(llm_weakness_avg)
            score_components["llm_gig_weakness"] = ScoreComponent(
                value=weakness_score,
                weight=self._LLM_WEAKNESS_WEIGHT,
                raw=llm_weakness_avg,
            )
            weighted_sum += weakness_score * self._LLM_WEAKNESS_WEIGHT
            total_weight_available += self._LLM_WEAKNESS_WEIGHT
            source_evidence.append("llm.gig_quality_weakness_avg_top10")
        else:
            confidence_breakdown["missing_llm_gig_weakness"] = -0.10
            missing_data_warnings.append("llm_not_implemented: missing LLM gig weakness assessment.")

        llm_entry_gap_assessment = self._resolve_llm_entry_gap_assessment(signals)
        if llm_entry_gap_assessment is not None:
            llm_entry_score = self._normalize_llm_score(llm_entry_gap_assessment)
            score_components["llm_entry_gap"] = ScoreComponent(
                value=llm_entry_score,
                weight=self._LLM_ENTRY_GAP_WEIGHT,
                raw=llm_entry_gap_assessment,
            )
            weighted_sum += llm_entry_score * self._LLM_ENTRY_GAP_WEIGHT
            total_weight_available += self._LLM_ENTRY_GAP_WEIGHT
            source_evidence.append("llm.entry_gap_assessment")
        else:
            confidence_breakdown["missing_llm_entry_gap"] = -0.10
            missing_data_warnings.append("llm_not_implemented: missing LLM entry gap assessment.")

        profile_gap_boost, profile_gap_flags = self._resolve_gap_signal(
            signals=signals,
            db=db,
            config=config,
        )
        if profile_gap_boost > 0.0:
            score_components["profile_gap_boost"] = ScoreComponent(
                value=profile_gap_boost,
                weight=0.0,
                raw=profile_gap_flags,
                note=(
                    "CompetitorProfile new_seller_gap flags boosted feasibility "
                    "for exploitable market weaknesses."
                ),
            )
            source_evidence.append("competitor_profiles.new_seller_gap.gap_flags")

        niche_tier = self._resolve_niche_tier(signals)
        if total_weight_available < 0.30:
            return FeasibilityScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient feasibility signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate a new seller feasibility explanation.",
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
                niche_tier=niche_tier,
                clean_gig_count=clean_gig_count,
            )

        baseline_score = weighted_sum / total_weight_available
        feasibility_score = round(min(100.0, max(0.0, baseline_score + profile_gap_boost)), 2)
        tier_note = (
            "Tier 2 context: this signal is emphasized for new-seller entry decisions."
            if niche_tier == "tier2_standard"
            else "Tier 1 context: feasibility is informative but not dominant."
        )
        gap_note = (
            " CompetitorProfile gap flags contributed an entry-opportunity boost."
            if profile_gap_boost > 0.0
            else ""
        )
        return FeasibilityScoreResult(
            keyword_id=keyword_id,
            score_value=feasibility_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Feasibility calculated from marketplace entry signals with confidence deductions"
                " when LLM assessments are unavailable."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Feasibility reflects entry accessibility for a new seller by combining level mix,"
                f" review barrier, price diversity, and LLM weakness/gap signals. {tier_note}{gap_note}"
            ),
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
            niche_tier=niche_tier,
            clean_gig_count=clean_gig_count,
        )

    def _resolve_level1_ratio(self, signals: dict[str, Any]) -> float | None:
        explicit_ratio = self._as_float(signals.get("level1_or_new_ratio_top10"))
        if explicit_ratio is not None:
            return max(0.0, min(1.0, explicit_ratio))

        seller_levels = signals.get("top10_seller_levels")
        if not isinstance(seller_levels, list) or not seller_levels:
            return None

        accessible_count = 0
        for raw_level in seller_levels:
            level = str(raw_level or "").strip().lower()
            if level in {
                "",
                "none",
                "no_level",
                "new",
                "new seller",
                "level 1",
                "level1",
                "level_1",
                "1",
            }:
                accessible_count += 1
        return accessible_count / len(seller_levels)

    def _resolve_price_diversity_score(self, signals: dict[str, Any]) -> float | None:
        ratio = self._as_float(signals.get("price_diversity_top10"))
        if ratio is not None:
            if ratio <= 1.0:
                return max(0.0, min(100.0, ratio * 100.0))
            return max(0.0, min(100.0, ratio))

        prices = signals.get("top10_prices")
        if not isinstance(prices, list):
            return None
        valid_prices = [float(price) for price in prices if self._as_float(price) is not None]
        if len(valid_prices) < 2:
            return None
        avg_price = sum(valid_prices) / len(valid_prices)
        if avg_price <= 0:
            return 0.0
        variance = sum((price - avg_price) ** 2 for price in valid_prices) / len(valid_prices)
        coefficient_of_variation = math.sqrt(variance) / avg_price
        return max(0.0, min(100.0, coefficient_of_variation * 200.0))

    def _resolve_llm_entry_gap_assessment(self, signals: dict[str, Any]) -> float | None:
        value = self._as_float(signals.get("llm_entry_gap_assessment"))
        if value is not None:
            return value
        return self._llm_entry_gap_assessment_stub()

    @staticmethod
    def _llm_entry_gap_assessment_stub() -> float | None:
        return None

    def _resolve_niche_tier(self, signals: dict[str, Any]) -> str:
        explicit_tier = signals.get("niche_tier")
        if isinstance(explicit_tier, str) and explicit_tier.strip():
            return explicit_tier.strip()

        niche_name = str(signals.get("niche_name", "")).strip().lower()
        if any(marker in niche_name for marker in self._TIER2_KEYWORD_MARKERS):
            return "tier2_standard"
        return "tier1_full"

    @staticmethod
    def _normalize_entry_review_barrier(lowest_review_count: float) -> float:
        if lowest_review_count <= 0:
            return 100.0
        return max(0.0, min(100.0, 100.0 - (math.log10(lowest_review_count + 1.0) / 3.0) * 100.0))

    @staticmethod
    def _normalize_llm_score(raw_score: float) -> float:
        if raw_score <= 10.0:
            return max(0.0, min(100.0, raw_score * 10.0))
        return max(0.0, min(100.0, raw_score))

    def _load_signals(
        self,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db, config=config)
        loaded: dict[str, Any] = {}
        if hasattr(db, "get_feasibility_inputs"):
            loaded = db.get_feasibility_inputs(keyword_id)
            if isinstance(loaded, Mapping):
                loaded = dict(loaded)
        elif isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                loaded = dict(loaded)

        if not loaded:
            return {}

        inline_profile = loaded.get("competitor_profile")
        if isinstance(inline_profile, Mapping):
            inline_flags = _extract_gap_flags_from_profile(dict(inline_profile))
            if inline_flags:
                feasibility_cfg = _feasibility_config(config)
                gap_boost_per_flag = max(
                    0.0,
                    _coerce_float(
                        feasibility_cfg.get("gap_boost_per_flag"),
                        _DEFAULT_GAP_BOOST_PER_FLAG,
                    ),
                )
                max_gap_boost = max(
                    0.0,
                    _coerce_float(feasibility_cfg.get("max_gap_boost"), _DEFAULT_MAX_GAP_BOOST),
                )
                loaded["feasibility_gap_signal"] = min(
                    max_gap_boost,
                    gap_boost_per_flag * len({flag for flag in inline_flags if flag in _SUPPORTED_GAP_FLAGS}),
                )
                loaded["feasibility_gap_flags"] = inline_flags
        return loaded

    def _load_signals_from_db(
        self,
        keyword_id: int,
        session: Session,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        relevance_cfg = _relevance_config(config)
        feasibility_cfg = _feasibility_config(config)
        use_clean_gig_set = bool(feasibility_cfg.get("use_clean_gig_set", False))
        top_n_for_scoring = int(relevance_cfg["top_n_for_scoring"])
        candidate_window = max(top_n_for_scoring, 10) * 3

        def _eligible(gig: Gig) -> bool:
            if relevance_cfg["enable_sponsored_exclusion"] and getattr(gig, "is_sponsored", None) is True:
                return False
            if relevance_cfg["enable_zombie_filter"] and bool(getattr(gig, "is_zombie", False)):
                return False
            return True

        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        top_results = (
            session.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= candidate_window)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        active_run_id = next(
            (
                result.run_id.strip()
                for result in top_results
                if isinstance(result.run_id, str) and result.run_id.strip()
            ),
            None,
        )
        if active_run_id is not None:
            scoped_results = [
                result
                for result in top_results
                if isinstance(result.run_id, str) and result.run_id.strip() == active_run_id
            ]
            if scoped_results:
                top_results = scoped_results
        top_card_urls = self._extract_top_card_urls(top_results, limit=candidate_window)
        top_card_url_identities = {
            identity
            for identity in (
                self._normalize_gig_url_identity(candidate_url) for candidate_url in top_card_urls
            )
            if identity is not None
        }
        top_gigs = [result.gig for result in top_results if result.gig is not None]
        if top_card_urls:
            top_gigs_by_url_query = session.query(Gig).filter(Gig.gig_url.in_(top_card_urls))
            if active_run_id is not None:
                top_gigs_by_url_query = top_gigs_by_url_query.filter(Gig.run_id == active_run_id)
            top_gigs_by_url = top_gigs_by_url_query.all()
            seen_ids = {gig.id for gig in top_gigs if gig.id is not None}
            for gig in top_gigs_by_url:
                if gig.id in seen_ids:
                    continue
                top_gigs.append(gig)
                if gig.id is not None:
                    seen_ids.add(gig.id)
            matched_identities = {
                identity
                for identity in (
                    self._normalize_gig_url_identity(getattr(gig, "gig_url", None)) for gig in top_gigs
                )
                if identity is not None
            }
            missing_identities = top_card_url_identities - matched_identities
            if missing_identities:
                top_gigs_candidates_query = session.query(Gig).filter(
                    Gig.keyword_id == keyword_id,
                    Gig.gig_url.isnot(None),
                )
                if active_run_id is not None:
                    top_gigs_candidates_query = top_gigs_candidates_query.filter(Gig.run_id == active_run_id)
                for gig in top_gigs_candidates_query.all():
                    gig_identity = self._normalize_gig_url_identity(getattr(gig, "gig_url", None))
                    if gig_identity not in missing_identities:
                        continue
                    if gig.id in seen_ids:
                        continue
                    top_gigs.append(gig)
                    if gig.id is not None:
                        seen_ids.add(gig.id)

            ranked_identity_order = {
                identity: index
                for index, identity in enumerate(
                    (
                        self._normalize_gig_url_identity(candidate_url) for candidate_url in top_card_urls
                    ),
                    start=1,
                )
                if identity is not None
            }

            def _rank_key(gig: Gig) -> tuple[int, int, int]:
                identity = self._normalize_gig_url_identity(getattr(gig, "gig_url", None))
                card_rank = ranked_identity_order.get(identity, 10_000) if identity is not None else 10_000
                position = gig.position if isinstance(gig.position, int) else 10_000
                gig_id = gig.id if isinstance(gig.id, int) else 10_000
                return (card_rank, position, gig_id)

            top_gigs.sort(key=_rank_key)
            top_gigs = top_gigs[:candidate_window]
        if not top_gigs:
            fallback_query = session.query(Gig).filter(Gig.keyword_id == keyword_id)
            if active_run_id is not None:
                fallback_query = fallback_query.filter(Gig.run_id == active_run_id)
            top_gigs = (
                fallback_query
                .order_by(Gig.position.asc().nullslast(), Gig.id.asc())
                .limit(candidate_window)
                .all()
            )
            # Some latest search runs contain unlinked rows; use any keyword gigs
            # when active-run scoped fallback cannot resolve top listings.
            if not top_gigs and active_run_id is not None:
                top_gigs = (
                    session.query(Gig)
                    .filter(Gig.keyword_id == keyword_id)
                    .order_by(Gig.position.asc().nullslast(), Gig.id.asc())
                    .limit(candidate_window)
                    .all()
                )
        top_gigs = [gig for gig in top_gigs if _eligible(gig)][:top_n_for_scoring]
        basis_gigs = top_gigs
        clean_gig_count: int | None = None
        if use_clean_gig_set:
            basis_gigs = _clean_gig_set(top_gigs) or top_gigs
            clean_gig_count = len(basis_gigs)
        seller_levels = [str(gig.seller.level) for gig in basis_gigs if gig.seller and gig.seller.level]
        accessible_levels = {
            "",
            "none",
            "no_level",
            "new",
            "new seller",
            "level 1",
            "level1",
            "level_1",
            "1",
        }
        accessible_count = sum(1 for level in seller_levels if level.strip().lower() in accessible_levels)
        review_candidates: list[float] = []
        for gig in basis_gigs:
            review_count = gig.review_count
            if review_count is None:
                review_count = gig.review_count_exact
            if review_count is not None:
                review_candidates.append(float(review_count))
        prices = [float(gig.starting_price) for gig in basis_gigs if gig.starting_price is not None]
        price_diversity = self._compute_price_diversity(prices)
        payload: dict[str, Any] = {
            "level1_or_new_ratio_top10": (
                (accessible_count / len(seller_levels)) if seller_levels else None
            ),
            "top10_seller_levels": seller_levels or None,
            "lowest_ranked_review_count_page1": min(review_candidates) if review_candidates else None,
            "price_diversity_top10": price_diversity,
            "top10_prices": prices or None,
            "llm_gig_quality_weakness_avg_top10": None,
        }
        if clean_gig_count is not None:
            payload["clean_gig_count"] = clean_gig_count

        profile_niche_id: str | None = None
        if keyword is not None:
            niche = session.query(Niche).filter(Niche.id == keyword.niche_id).first()
            if niche is not None and isinstance(niche.slug, str) and niche.slug.strip():
                profile_niche_id = niche.slug.strip()

        profile_run_id = active_run_id
        if profile_run_id is None:
            profile_run_id = next(
                (
                    gig.run_id.strip()
                    for gig in top_gigs
                    if isinstance(gig.run_id, str) and gig.run_id.strip()
                ),
                None,
            )
        if profile_niche_id is not None and profile_run_id is not None:
            payload["_profile_niche_id"] = profile_niche_id
            payload["_profile_run_id"] = profile_run_id
            gap_boost, gap_flags = _get_feasibility_gap_signal_details(
                niche_id=profile_niche_id,
                run_id=profile_run_id,
                db=session,
                config=config,
            )
            if gap_boost > 0.0:
                payload["feasibility_gap_signal"] = gap_boost
                payload["feasibility_gap_flags"] = gap_flags

        return payload

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_top_card_urls(top_results: list[SearchResult], limit: int) -> list[str]:
        ranked_urls: list[tuple[int, str]] = []
        for result in top_results:
            cards = result.gig_cards if isinstance(result.gig_cards, list) else []
            for card in cards:
                if not isinstance(card, dict):
                    continue
                raw_url = card.get("gig_url")
                if not isinstance(raw_url, str):
                    continue
                normalized_url = raw_url.strip()
                if not normalized_url:
                    continue
                raw_position = card.get("position")
                if isinstance(raw_position, int) and raw_position > 0:
                    position = raw_position
                elif isinstance(raw_position, str) and raw_position.strip().isdigit():
                    position = int(raw_position.strip())
                else:
                    position = 10_000
                ranked_urls.append((position, normalized_url))

        ranked_urls.sort(key=lambda value: value[0])
        deduped: list[str] = []
        seen: set[str] = set()
        for _, normalized_url in ranked_urls:
            if normalized_url in seen:
                continue
            seen.add(normalized_url)
            deduped.append(normalized_url)
            if len(deduped) >= limit:
                break
        return deduped

    @staticmethod
    def _normalize_gig_url_identity(raw_url: Any) -> str | None:
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

    @staticmethod
    def _compute_price_diversity(prices: list[float]) -> float | None:
        if len(prices) < 2:
            return None
        avg_price = sum(prices) / len(prices)
        if avg_price <= 0:
            return 0.0
        variance = sum((price - avg_price) ** 2 for price in prices) / len(prices)
        std_dev = math.sqrt(variance)
        return max(0.0, min(1.0, std_dev / avg_price))

    def _resolve_gap_signal(
        self,
        *,
        signals: dict[str, Any],
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> tuple[float, list[str]]:
        explicit_boost = self._as_float(signals.get("feasibility_gap_signal"))
        explicit_flags = _normalize_gap_flags(signals.get("feasibility_gap_flags"))
        feasibility_cfg = _feasibility_config(config)
        max_gap_boost = max(
            0.0,
            _coerce_float(feasibility_cfg.get("max_gap_boost"), _DEFAULT_MAX_GAP_BOOST),
        )
        if explicit_boost is not None:
            return min(max_gap_boost, max(0.0, explicit_boost)), explicit_flags

        niche_id = signals.get("_profile_niche_id")
        run_id = signals.get("_profile_run_id")
        if not isinstance(niche_id, str) or not isinstance(run_id, str):
            return 0.0, []
        return _get_feasibility_gap_signal_details(
            niche_id=niche_id,
            run_id=run_id,
            db=db,
            config=config,
        )
