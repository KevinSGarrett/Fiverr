"""S4.6 Conversion Intent Score calculator."""

from __future__ import annotations

import asyncio
import math
import re
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from src.models import ExternalSignal, Gig, Keyword, SearchResult
from src.scoring.contracts import IntentScoreResult, ScoreComponent


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _opportunity_qualifier_enabled(config: dict[str, Any] | None) -> bool:
    if not isinstance(config, Mapping):
        return False
    scoring_cfg = config.get("scoring")
    if not isinstance(scoring_cfg, Mapping):
        return False
    opportunity_cfg = scoring_cfg.get("opportunity")
    if not isinstance(opportunity_cfg, Mapping):
        return False
    return bool(opportunity_cfg.get("qualify_by_relevance", False))


def compute_intent_alignment_factor(query_intent: str | None, service_intent: str | None) -> float:
    if not query_intent or not service_intent:
        return 1.0
    query_key = query_intent.strip().upper()
    service_key = service_intent.strip().upper()
    if not query_key or not service_key:
        return 1.0
    if query_key == service_key:
        return 1.0
    mapping = {
        ("TRANSACTIONAL", "HIGH_INTENT"): 0.9,
        ("HIGH_INTENT", "TRANSACTIONAL"): 0.9,
        ("CONSIDERATION", "HIGH_INTENT"): 0.9,
        ("HIGH_INTENT", "CONSIDERATION"): 0.9,
        ("INFORMATIONAL", "TRANSACTIONAL"): 0.6,
        ("TRANSACTIONAL", "INFORMATIONAL"): 0.6,
        ("INFORMATIONAL", "HIGH_INTENT"): 0.7,
        ("HIGH_INTENT", "INFORMATIONAL"): 0.7,
    }
    return _clamp01(mapping.get((query_key, service_key), 0.8))


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

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        llm_client: Any | None = None,
        cache: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> IntentScoreResult:
        """Calculate a conversion intent score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0
        use_alignment = _opportunity_qualifier_enabled(config)

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
        if llm_client is not None and keyword_text:
            llm_intent_raw = self._run_async(self._get_llm_intent_class(keyword_text, llm_client, cache))
            if llm_intent_raw is None:
                missing_data_warnings.append("llm_intent_failed: unable to classify buyer intent via LLM.")
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

        if use_alignment:
            alignment_factor = compute_intent_alignment_factor(
                query_intent=signals.get("query_intent_class") if isinstance(signals.get("query_intent_class"), str) else None,
                service_intent=signals.get("service_intent_class")
                if isinstance(signals.get("service_intent_class"), str)
                else None,
            )
            weighted_sum *= alignment_factor
            score_components["intent_alignment"] = ScoreComponent(
                value=alignment_factor * 100.0,
                weight=0.0,
                raw={
                    "query_intent_class": signals.get("query_intent_class"),
                    "service_intent_class": signals.get("service_intent_class"),
                },
                note="Intent alignment factor applied under opportunity qualifier toggle.",
            )

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

    async def _get_llm_intent_class(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> str | None:
        prompt = (
            "Classify buyer intent for the Fiverr keyword below. "
            "Return exactly one token from: INFORMATIONAL, CONSIDERATION, HIGH_INTENT, TRANSACTIONAL.\n"
            f"Keyword: {keyword_text}"
        )
        try:
            response = await asyncio.to_thread(
                self._complete_with_optional_cache,
                llm_client,
                prompt,
                "gpt-4o-mini",
                cache,
            )
        except Exception:
            return None
        text = self._extract_llm_text(response).strip().upper()
        return text if text in self._LLM_INTENT_MAP else None

    @staticmethod
    def _complete_with_optional_cache(
        llm_client: Any,
        prompt: str,
        model: str,
        cache: Any | None,
    ) -> Any:
        try:
            return llm_client.complete(prompt=prompt, model=model, cache=cache)
        except TypeError:
            return llm_client.complete(prompt=prompt, model=model)

    @staticmethod
    def _extract_llm_text(response: Any) -> str:
        if isinstance(response, str):
            return response
        text = getattr(response, "text", None)
        return text if isinstance(text, str) else str(response)

    @staticmethod
    def _run_async(coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()

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
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_intent_inputs"):
            loaded = db.get_intent_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        top_gigs = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        review_counts = [float(gig.review_count) for gig in top_gigs if gig.review_count is not None]
        keyword_meta = keyword.metadata_json if keyword else {}
        reddit_demand = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == "reddit_demand",
            )
            .order_by(ExternalSignal.created_at.desc())
            .first()
        )
        reddit_raw = reddit_demand.raw_value_json if reddit_demand and isinstance(reddit_demand.raw_value_json, dict) else {}
        return {
            "keyword": keyword.keyword if keyword else "",
            "autocomplete_position": keyword_meta.get("autocomplete_position"),
            "avg_review_count_top10": (sum(review_counts) / len(review_counts)) if review_counts else None,
            "llm_buyer_intent_classification": keyword_meta.get("intent_classification"),
            "reddit_demand_intent_score": reddit_raw.get("reddit_demand_intent_score"),
        }

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
