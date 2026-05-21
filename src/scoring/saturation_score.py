"""S4.7 Saturation Score calculator."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from src.models import Gig, Keyword, SaturationScore, SearchResult
from src.scoring.contracts import SaturationScoreResult, ScoreComponent


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


def _saturation_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    scoring_cfg = config.get("scoring")
    if not isinstance(scoring_cfg, Mapping):
        return {}
    saturation_cfg = scoring_cfg.get("saturation")
    if not isinstance(saturation_cfg, Mapping):
        return {}
    return dict(saturation_cfg)


def get_saturation_signal(keyword_id: int, run_id: str, db: Any) -> float | None:
    """
    Return Stage 13 saturation score for keyword/run when available.

    Returns `None` when no persisted saturation analysis output exists.
    """
    if isinstance(db, Session):
        normalized_run = run_id.strip()
        if normalized_run:
            row = (
                db.query(SaturationScore)
                .filter(
                    SaturationScore.keyword_id == keyword_id,
                    SaturationScore.run_id == normalized_run,
                )
                .order_by(SaturationScore.computed_at.desc(), SaturationScore.id.desc())
                .first()
            )
            if row is not None and row.saturation_score is not None:
                return float(row.saturation_score)
            return None

        latest_row = (
            db.query(SaturationScore)
            .filter(SaturationScore.keyword_id == keyword_id)
            .order_by(SaturationScore.computed_at.desc(), SaturationScore.id.desc())
            .first()
        )
        if latest_row is not None and latest_row.saturation_score is not None:
            return float(latest_row.saturation_score)
        return None

    if hasattr(db, "get_saturation_signal"):
        loaded = db.get_saturation_signal(keyword_id, run_id)
        try:
            return None if loaded is None else float(loaded)
        except (TypeError, ValueError):
            return None

    if hasattr(db, "get_saturation_inputs"):
        loaded = db.get_saturation_inputs(keyword_id)
        if isinstance(loaded, Mapping):
            raw_value = loaded.get("saturation_score")
            try:
                return None if raw_value is None else float(raw_value)
            except (TypeError, ValueError):
                return None

    if isinstance(db, Mapping):
        loaded = db.get(keyword_id, db)
        if isinstance(loaded, Mapping):
            raw_value = loaded.get("saturation_score")
            try:
                return None if raw_value is None else float(raw_value)
            except (TypeError, ValueError):
                return None

    return None


class SaturationScoreCalculator:
    """Calculate market saturation where higher score means more saturation."""

    DEFAULT_WEIGHT = 0.05
    _TOTAL_GIG_COUNT_WEIGHT = 0.25
    _TITLE_DUPLICATION_WEIGHT = 0.25
    _PRICE_COMPRESSION_WEIGHT = 0.20
    _SELLER_OVERLAP_WEIGHT = 0.15
    _LLM_SATURATION_WEIGHT = 0.15

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        llm_client: Any | None = None,
        cache: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> SaturationScoreResult:
        """Calculate a saturation score payload for the provided keyword."""
        use_analysis_output = _coerce_bool(
            _saturation_config(config).get("use_analysis_output"),
            True,
        )
        if use_analysis_output:
            resolved_run_id = self._resolve_run_id(keyword_id, db) or ""
            analysis_signal = get_saturation_signal(keyword_id, resolved_run_id, db)
            if analysis_signal is not None:
                clamped_signal = round(min(100.0, max(0.0, analysis_signal)), 2)
                analysis_source_evidence = (
                    [f"saturation_scores.saturation_score[{resolved_run_id}]"]
                    if resolved_run_id
                    else ["saturation_scores.saturation_score"]
                )
                return SaturationScoreResult(
                    keyword_id=keyword_id,
                    score_value=clamped_signal,
                    score_components={
                        "analysis_output": ScoreComponent(
                            value=clamped_signal,
                            weight=1.0,
                            raw=analysis_signal,
                            note="Loaded from Stage 13 saturation analysis output.",
                        )
                    },
                    confidence_modifier=1.0,
                    confidence_breakdown={},
                    confidence_reason="Saturation score loaded from persisted Stage 13 analysis output.",
                    missing_data_warnings=[],
                    source_evidence=analysis_source_evidence,
                    explanation_text=(
                        "Higher saturation means lower strategic upside. Composite usage is inverted: "
                        "(100 - saturation_score) * 0.05."
                    ),
                    total_weight_available=1.0,
                    default_weight=self.DEFAULT_WEIGHT,
                    is_inverted=True,
                )

        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0

        if use_analysis_output:
            missing_data_warnings.append(
                "saturation_analysis_output_missing: falling back to rule-based saturation signals."
            )

        total_gig_count = self._as_float(signals.get("total_gig_count"))
        if total_gig_count is not None:
            gig_count_score = self._normalize_total_gig_count(total_gig_count)
            score_components["total_gig_count"] = ScoreComponent(
                value=gig_count_score,
                weight=self._TOTAL_GIG_COUNT_WEIGHT,
                raw=total_gig_count,
            )
            weighted_sum += gig_count_score * self._TOTAL_GIG_COUNT_WEIGHT
            total_weight_available += self._TOTAL_GIG_COUNT_WEIGHT
            source_evidence.append("fiverr_search_results.total_result_count")
        else:
            missing_data_warnings.append("Missing total gig count for keyword.")

        title_duplication_score = self._resolve_title_duplication_score(signals)
        if title_duplication_score is not None:
            score_components["title_duplication"] = ScoreComponent(
                value=title_duplication_score,
                weight=self._TITLE_DUPLICATION_WEIGHT,
                raw=signals.get("title_duplication_rate"),
            )
            weighted_sum += title_duplication_score * self._TITLE_DUPLICATION_WEIGHT
            total_weight_available += self._TITLE_DUPLICATION_WEIGHT
            source_evidence.append("gig_cards.title_duplication_rate_top30")
        else:
            missing_data_warnings.append("Missing title duplication signal.")

        price_compression_score = self._resolve_price_compression_score(signals)
        if price_compression_score is not None:
            score_components["price_compression"] = ScoreComponent(
                value=price_compression_score,
                weight=self._PRICE_COMPRESSION_WEIGHT,
                raw=signals.get("price_compression_signal"),
            )
            weighted_sum += price_compression_score * self._PRICE_COMPRESSION_WEIGHT
            total_weight_available += self._PRICE_COMPRESSION_WEIGHT
            source_evidence.append("gig_cards.price_compression_signal")
        else:
            missing_data_warnings.append("Missing price compression signal.")

        seller_overlap_ratio = self._as_float(signals.get("seller_portfolio_overlap_ratio"))
        if seller_overlap_ratio is not None:
            seller_overlap_score = self._normalize_ratio_or_score(seller_overlap_ratio)
            score_components["seller_overlap"] = ScoreComponent(
                value=seller_overlap_score,
                weight=self._SELLER_OVERLAP_WEIGHT,
                raw=seller_overlap_ratio,
            )
            weighted_sum += seller_overlap_score * self._SELLER_OVERLAP_WEIGHT
            total_weight_available += self._SELLER_OVERLAP_WEIGHT
            source_evidence.append("seller_profiles.portfolio_overlap_ratio")
        else:
            missing_data_warnings.append("Missing seller portfolio overlap signal.")

        llm_saturation_assessment = self._resolve_llm_saturation_assessment(signals)
        if llm_client is not None:
            keyword_text = str(signals.get("keyword") or "").strip()
            gig_count = int(total_gig_count or 0)
            llm_saturation_assessment = self._run_async(
                self._get_llm_saturation(keyword_text, gig_count, llm_client, cache)
            )
            if llm_saturation_assessment is None:
                missing_data_warnings.append("llm_saturation_failed: unable to get LLM saturation score.")
        if llm_saturation_assessment is not None:
            llm_score = self._normalize_ratio_or_score(llm_saturation_assessment)
            score_components["llm_saturation_assessment"] = ScoreComponent(
                value=llm_score,
                weight=self._LLM_SATURATION_WEIGHT,
                raw=llm_saturation_assessment,
            )
            weighted_sum += llm_score * self._LLM_SATURATION_WEIGHT
            total_weight_available += self._LLM_SATURATION_WEIGHT
            source_evidence.append("llm.saturation_assessment")
        else:
            confidence_breakdown["missing_llm_saturation_assessment"] = -0.05
            missing_data_warnings.append("llm_not_implemented: missing LLM saturation assessment.")

        if total_weight_available < 0.30:
            return SaturationScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient saturation signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text=(
                    "Insufficient data to generate saturation explanation. Composite applies"
                    " inversion rule when available: (100 - saturation_score) * 0.05."
                ),
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
                is_inverted=True,
            )

        saturation_score = round(min(100.0, max(0.0, weighted_sum / total_weight_available)), 2)
        return SaturationScoreResult(
            keyword_id=keyword_id,
            score_value=saturation_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Saturation blends result volume, duplication, compression, overlap, and optional"
                " LLM synthesis."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Higher saturation means lower strategic upside. Composite usage is inverted:"
                " (100 - saturation_score) * 0.05."
            ),
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
            is_inverted=True,
        )

    async def _get_llm_saturation(
        self,
        keyword_text: str,
        gig_count: int,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Rate saturation for '{keyword_text}' with {gig_count} gigs. Return a number 0-100 "
            "where 100 = completely saturated. Respond with only the number."
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
        text = self._extract_llm_text(response).strip()
        try:
            value = float(text)
        except ValueError:
            return None
        if value < 0.0 or value > 100.0:
            return None
        return value

    def _resolve_run_id(self, keyword_id: int, db: Any) -> str | None:
        if isinstance(db, Session):
            try:
                row = (
                    db.query(SearchResult.run_id)
                    .filter(SearchResult.keyword_id == keyword_id)
                    .order_by(SearchResult.collected_at.desc(), SearchResult.id.desc())
                    .first()
                )
            except Exception:
                row = None
            if row and isinstance(row[0], str) and row[0].strip():
                return row[0].strip()
            return None

        if hasattr(db, "get_saturation_inputs"):
            loaded = db.get_saturation_inputs(keyword_id)
            if isinstance(loaded, Mapping):
                run_id = loaded.get("run_id")
                if isinstance(run_id, str) and run_id.strip():
                    return run_id.strip()

        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                run_id = loaded.get("run_id")
                if isinstance(run_id, str) and run_id.strip():
                    return run_id.strip()

        return None

    def _resolve_title_duplication_score(self, signals: dict[str, Any]) -> float | None:
        duplication_rate = self._as_float(signals.get("title_duplication_rate"))
        if duplication_rate is not None:
            return self._normalize_ratio_or_score(duplication_rate)

        duplicate_titles = self._as_float(signals.get("duplicate_title_count_top30"))
        if duplicate_titles is None:
            return None
        return max(0.0, min(100.0, (duplicate_titles / 30.0) * 100.0))

    def _resolve_price_compression_score(self, signals: dict[str, Any]) -> float | None:
        compression_signal = self._as_float(signals.get("price_compression_signal"))
        if compression_signal is not None:
            return self._normalize_ratio_or_score(compression_signal)

        diversity_signal = self._as_float(signals.get("price_diversity_top30"))
        if diversity_signal is None:
            return None
        diversity_score = self._normalize_ratio_or_score(diversity_signal)
        return 100.0 - diversity_score

    def _resolve_llm_saturation_assessment(self, signals: dict[str, Any]) -> float | None:
        explicit = self._as_float(signals.get("llm_saturation_assessment"))
        if explicit is not None:
            return explicit
        return self._llm_saturation_assessment_stub()

    @staticmethod
    def _llm_saturation_assessment_stub() -> float | None:
        return None

    @staticmethod
    def _normalize_total_gig_count(total_gig_count: float) -> float:
        if total_gig_count <= 0:
            return 0.0
        return max(0.0, min(100.0, (math.log10(total_gig_count + 1.0) / 4.0) * 100.0))

    @staticmethod
    def _normalize_ratio_or_score(value: float) -> float:
        if value <= 1.0:
            return max(0.0, min(100.0, value * 100.0))
        if value <= 10.0:
            return max(0.0, min(100.0, value * 10.0))
        return max(0.0, min(100.0, value))

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_saturation_inputs"):
            loaded = db.get_saturation_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        total_gig_count = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).count()
        top_gigs = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        normalized_titles = [gig.normalized_title or gig.title for gig in top_gigs if gig.title]
        title_duplication_rate = None
        if normalized_titles:
            unique_title_count = len({title.strip().lower() for title in normalized_titles if title})
            title_duplication_rate = 1.0 - (unique_title_count / len(normalized_titles))
        prices = [float(gig.starting_price) for gig in top_gigs if gig.starting_price is not None]
        price_compression_signal = self._price_compression_ratio(prices)
        return {
            "keyword": keyword.keyword if keyword else "",
            "total_gig_count": float(total_gig_count) if total_gig_count > 0 else None,
            "title_duplication_rate": title_duplication_rate,
            "price_compression_signal": price_compression_signal,
        }

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _price_compression_ratio(prices: list[float]) -> float | None:
        if len(prices) < 2:
            return None
        spread = max(prices) - min(prices)
        if spread <= 0:
            return 1.0
        avg_price = sum(prices) / len(prices)
        variance = sum((price - avg_price) ** 2 for price in prices) / len(prices)
        std_dev = math.sqrt(variance)
        return max(0.0, min(1.0, std_dev / spread))

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
