"""S4.5 Profitability Score calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from src.models import Gig, SearchResult
from src.scoring.contracts import ProfitabilityScoreResult, ScoreComponent


class ProfitabilityScoreCalculator:
    """Calculate long-term keyword profitability potential."""

    DEFAULT_WEIGHT = 0.10
    _STARTING_PRICE_WEIGHT = 0.30
    _PREMIUM_PRICE_WEIGHT = 0.30
    _DELIVERY_TIME_WEIGHT = 0.15
    _EXTRAS_WEIGHT = 0.15
    _LLM_UPSELL_WEIGHT = 0.10

    def calculate(self, keyword_id: int, db: Any) -> ProfitabilityScoreResult:
        """Calculate a profitability score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0

        starting_price = self._as_float(signals.get("avg_starting_price_top10"))
        if starting_price is not None:
            starting_price_score = self._normalize_with_universe(
                starting_price,
                self._as_float(signals.get("keyword_universe_starting_price_min")),
                self._as_float(signals.get("keyword_universe_starting_price_max")),
            )
            score_components["avg_starting_price"] = ScoreComponent(
                value=starting_price_score,
                weight=self._STARTING_PRICE_WEIGHT,
                raw=starting_price,
            )
            weighted_sum += starting_price_score * self._STARTING_PRICE_WEIGHT
            total_weight_available += self._STARTING_PRICE_WEIGHT
            source_evidence.append("gig_details.avg_starting_price_top10")
        else:
            missing_data_warnings.append("Missing average starting price of top 10 gigs.")

        premium_price = self._as_float(signals.get("avg_premium_package_price_top10"))
        if premium_price is not None:
            premium_price_score = self._normalize_with_universe(
                premium_price,
                self._as_float(signals.get("keyword_universe_premium_price_min")),
                self._as_float(signals.get("keyword_universe_premium_price_max")),
            )
            score_components["avg_premium_price"] = ScoreComponent(
                value=premium_price_score,
                weight=self._PREMIUM_PRICE_WEIGHT,
                raw=premium_price,
            )
            weighted_sum += premium_price_score * self._PREMIUM_PRICE_WEIGHT
            total_weight_available += self._PREMIUM_PRICE_WEIGHT
            source_evidence.append("gig_details.avg_premium_package_price_top10")
        else:
            missing_data_warnings.append("Missing average premium package price in top 10.")

        delivery_days = self._as_float(signals.get("typical_delivery_days"))
        if delivery_days is not None:
            delivery_score = self._normalize_delivery_days(delivery_days)
            score_components["delivery_time_efficiency"] = ScoreComponent(
                value=delivery_score,
                weight=self._DELIVERY_TIME_WEIGHT,
                raw=delivery_days,
            )
            weighted_sum += delivery_score * self._DELIVERY_TIME_WEIGHT
            total_weight_available += self._DELIVERY_TIME_WEIGHT
            source_evidence.append("gig_details.typical_delivery_days")
        else:
            missing_data_warnings.append("Missing typical delivery-time signal.")

        extras_score = self._resolve_extras_score(signals)
        if extras_score is not None:
            score_components["gig_extras_upsell"] = ScoreComponent(
                value=extras_score,
                weight=self._EXTRAS_WEIGHT,
                raw={
                    "extras_presence_ratio": signals.get("extras_presence_ratio"),
                    "avg_extras_price": signals.get("avg_extras_price"),
                },
            )
            weighted_sum += extras_score * self._EXTRAS_WEIGHT
            total_weight_available += self._EXTRAS_WEIGHT
            source_evidence.append("gig_details.extras_presence_and_pricing")
        else:
            missing_data_warnings.append("Missing gig-extras presence/pricing signal.")

        llm_upsell_potential = self._resolve_llm_upsell_potential(signals)
        if llm_upsell_potential is not None:
            llm_upsell_score = self._normalize_llm_score(llm_upsell_potential)
            score_components["llm_upsell_potential"] = ScoreComponent(
                value=llm_upsell_score,
                weight=self._LLM_UPSELL_WEIGHT,
                raw=llm_upsell_potential,
            )
            weighted_sum += llm_upsell_score * self._LLM_UPSELL_WEIGHT
            total_weight_available += self._LLM_UPSELL_WEIGHT
            source_evidence.append("llm.upsell_potential_assessment")
        else:
            confidence_breakdown["missing_llm_upsell"] = -0.05
            missing_data_warnings.append("llm_not_implemented: missing LLM upsell potential assessment.")

        if total_weight_available < 0.30:
            return ProfitabilityScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient profitability signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text=(
                    "Insufficient data for profitability. Month 1-3 AOV typically $95-175."
                    " Month 6+ AOV can reach $300+. Score reflects long-term potential,"
                    " not immediate launch reality. Trust-stage context: new sellers need time"
                    " to unlock higher-value buyers."
                ),
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
            )

        profitability_score = round(min(100.0, max(0.0, weighted_sum / total_weight_available)), 2)
        return ProfitabilityScoreResult(
            keyword_id=keyword_id,
            score_value=profitability_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Profitability combines pricing, delivery efficiency, and upsell signals with"
                " confidence deductions when LLM upsell synthesis is unavailable."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Month 1-3 AOV typically $95-175. Month 6+ AOV can reach $300+. "
                "Score reflects long-term potential, not immediate launch reality. "
                "Trust-stage context: early orders may be lower-ticket before review"
                " velocity supports premium conversion."
            ),
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
        )

    def _resolve_extras_score(self, signals: dict[str, Any]) -> float | None:
        extras_presence_ratio = self._as_float(signals.get("extras_presence_ratio"))
        avg_extras_price = self._as_float(signals.get("avg_extras_price"))
        if extras_presence_ratio is None and avg_extras_price is None:
            return None

        presence_signal = 0.0 if extras_presence_ratio is None else max(0.0, min(100.0, extras_presence_ratio * 100.0))
        price_signal = 0.0 if avg_extras_price is None else max(0.0, min(100.0, avg_extras_price))
        return (presence_signal * 0.6) + (price_signal * 0.4)

    def _resolve_llm_upsell_potential(self, signals: dict[str, Any]) -> float | None:
        value = self._as_float(signals.get("llm_upsell_potential_assessment"))
        if value is not None:
            return value
        return self._llm_upsell_potential_stub()

    @staticmethod
    def _llm_upsell_potential_stub() -> float | None:
        return None

    @staticmethod
    def _normalize_with_universe(value: float, universe_min: float | None, universe_max: float | None) -> float:
        min_bound = 20.0 if universe_min is None else universe_min
        max_bound = 300.0 if universe_max is None else universe_max
        if max_bound <= min_bound:
            return max(0.0, min(100.0, value))
        normalized = ((value - min_bound) / (max_bound - min_bound)) * 100.0
        return max(0.0, min(100.0, normalized))

    @staticmethod
    def _normalize_delivery_days(delivery_days: float) -> float:
        if delivery_days <= 0:
            return 100.0
        return max(0.0, min(100.0, 100.0 - ((math.log10(delivery_days + 1.0) / 2.0) * 100.0)))

    @staticmethod
    def _normalize_llm_score(raw_score: float) -> float:
        if raw_score <= 10.0:
            return max(0.0, min(100.0, raw_score * 10.0))
        return max(0.0, min(100.0, raw_score))

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_profitability_inputs"):
            loaded = db.get_profitability_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        top_results = (
            session.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
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
        top_gigs_query = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
        )
        if active_run_id is not None:
            top_gigs_query = top_gigs_query.filter(SearchResult.run_id == active_run_id)
        top_gigs = top_gigs_query.order_by(SearchResult.rank.asc()).all()
        if active_run_id is not None:
            scoped_results = [
                result
                for result in top_results
                if isinstance(result.run_id, str) and result.run_id.strip() == active_run_id
            ]
            if scoped_results:
                top_results = scoped_results

        top_card_urls = self._extract_top_card_urls(top_results, limit=10)
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

        if not top_gigs:
            fallback_query = session.query(Gig).filter(Gig.keyword_id == keyword_id)
            if active_run_id is not None:
                fallback_query = fallback_query.filter(Gig.run_id == active_run_id)
            top_gigs = (
                fallback_query
                .order_by(Gig.position.asc().nullslast(), Gig.id.asc())
                .limit(10)
                .all()
            )
            # Latest run IDs can point to unlinked SearchResult rows.
            # If run-scoped fallback is empty, recover via keyword-scoped gigs.
            if not top_gigs and active_run_id is not None:
                top_gigs = (
                    session.query(Gig)
                    .filter(Gig.keyword_id == keyword_id)
                    .order_by(Gig.position.asc().nullslast(), Gig.id.asc())
                    .limit(10)
                    .all()
                )
        starting_prices = [float(gig.starting_price) for gig in top_gigs if gig.starting_price is not None]
        premium_prices = [
            self._as_float(self._gig_meta_value(gig, "premium_price", "premium_package_price"))
            for gig in top_gigs
        ]
        valid_premium_prices = [price for price in premium_prices if price is not None]
        delivery_days_values = [
            self._as_float(self._gig_meta_value(gig, "delivery_time_days", "typical_delivery_days"))
            for gig in top_gigs
        ]
        valid_delivery_days = [day for day in delivery_days_values if day is not None]
        extras_flags = [self._has_extras(gig) for gig in top_gigs]
        avg_extras_prices = [
            self._as_float(self._gig_meta_value(gig, "avg_extras_price", "extras_price"))
            for gig in top_gigs
        ]
        valid_extras_prices = [price for price in avg_extras_prices if price is not None]
        return {
            "avg_starting_price_top10": (sum(starting_prices) / len(starting_prices)) if starting_prices else None,
            "avg_premium_package_price_top10": (
                (sum(valid_premium_prices) / len(valid_premium_prices)) if valid_premium_prices else None
            ),
            "typical_delivery_days": (sum(valid_delivery_days) / len(valid_delivery_days)) if valid_delivery_days else None,
            "extras_presence_ratio": (
                (sum(1 for flag in extras_flags if flag) / len(extras_flags)) if extras_flags else None
            ),
            "avg_extras_price": (sum(valid_extras_prices) / len(valid_extras_prices)) if valid_extras_prices else None,
        }

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
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _gig_meta_value(gig: Gig, *keys: str) -> Any:
        metadata = gig.metadata_json if isinstance(gig.metadata_json, dict) else {}
        for key in keys:
            if key in metadata:
                return metadata.get(key)
        return None

    def _has_extras(self, gig: Gig) -> bool:
        metadata = gig.metadata_json if isinstance(gig.metadata_json, dict) else {}
        extras = metadata.get("gig_extras")
        if extras is None:
            extras = metadata.get("extras")
        if isinstance(extras, list):
            return len(extras) > 0
        if isinstance(extras, dict):
            return len(extras) > 0
        if isinstance(extras, bool):
            return extras
        return False
