"""S4.8 Gig Quality Weakness Score calculator."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from src.models import Gig, GigVisualAnalysis, Keyword, SearchResult
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

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        llm_client: Any | None = None,
        cache: Any | None = None,
    ) -> WeaknessScoreResult:
        """Calculate weakness score with graceful degradation for missing LLM inputs."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0
        warn_not_implemented = llm_client is None

        if llm_client is not None:
            keyword_text = str(signals.get("keyword", "")).strip()
            llm_values = self._run_async(
                self._collect_llm_values(keyword_text, signals, llm_client, cache)
            )
            for key, value in llm_values.items():
                if value is not None:
                    signals[key] = value
                else:
                    missing_data_warnings.append(f"{key.replace('llm_', '').replace('_score', '')}_failed")

        description_quality = self._resolve_llm_value(
            "llm_description_quality_score",
            signals,
            self._llm_description_quality_stub,
            missing_data_warnings,
            warn_not_implemented=warn_not_implemented,
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
            warn_not_implemented=warn_not_implemented,
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
            warn_not_implemented=warn_not_implemented,
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
            warn_not_implemented=warn_not_implemented,
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
            warn_not_implemented=warn_not_implemented,
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
            warn_not_implemented=warn_not_implemented,
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

    async def _collect_llm_values(
        self,
        keyword_text: str,
        signals: dict[str, Any],
        llm_client: Any,
        cache: Any | None,
    ) -> dict[str, float | None]:
        return {
            "llm_description_quality_score": await self._get_llm_description_quality(
                keyword_text, llm_client, cache
            ),
            "llm_weakness_count_per_gig": await self._get_llm_weakness_count(
                keyword_text, llm_client, cache
            ),
            "llm_thumbnail_quality_score": await self._get_llm_thumbnail_quality(
                keyword_text, llm_client, cache
            ),
            "llm_faq_completeness_score": await self._get_llm_faq_completeness(
                keyword_text, llm_client, cache
            ),
            "llm_package_differentiation_score": await self._get_llm_package_differentiation(
                keyword_text, llm_client, cache
            ),
            "llm_niche_specificity_score": await self._get_llm_niche_specificity(
                keyword_text, llm_client, cache
            ),
        }

    async def _get_llm_description_quality(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Rate top competitor gig description quality for keyword '{keyword_text}' on a 0-10 scale. "
            "Respond with only the number."
        )
        return await self._get_llm_numeric_score(prompt, "gpt-4o", llm_client, cache)

    async def _get_llm_weakness_count(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Estimate average weakness count per top gig for keyword '{keyword_text}' as a 0-10 value. "
            "Respond with only the number."
        )
        return await self._get_llm_numeric_score(prompt, "gpt-4o", llm_client, cache)

    async def _get_llm_thumbnail_quality(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Rate top competitor thumbnail quality for keyword '{keyword_text}' on a 0-10 scale. "
            "Respond with only the number."
        )
        return await self._get_llm_numeric_score(prompt, "gpt-4o-mini", llm_client, cache)

    async def _get_llm_faq_completeness(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Rate FAQ completeness for top gigs in keyword '{keyword_text}' on a 0-10 scale. "
            "Respond with only the number."
        )
        return await self._get_llm_numeric_score(prompt, "gpt-4o-mini", llm_client, cache)

    async def _get_llm_package_differentiation(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Rate package differentiation for top gigs in keyword '{keyword_text}' on a 0-10 scale. "
            "Respond with only the number."
        )
        return await self._get_llm_numeric_score(prompt, "gpt-4o", llm_client, cache)

    async def _get_llm_niche_specificity(
        self,
        keyword_text: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        prompt = (
            f"Rate niche specificity for top gigs in keyword '{keyword_text}' on a 0-10 scale. "
            "Respond with only the number."
        )
        return await self._get_llm_numeric_score(prompt, "gpt-4o", llm_client, cache)

    async def _get_llm_numeric_score(
        self,
        prompt: str,
        model: str,
        llm_client: Any,
        cache: Any | None,
    ) -> float | None:
        try:
            response = await asyncio.to_thread(
                self._complete_with_optional_cache,
                llm_client,
                prompt,
                model,
                cache,
            )
        except Exception:
            return None
        text = self._extract_llm_text(response).strip()
        try:
            return float(text)
        except ValueError:
            return None

    def _resolve_llm_value(
        self,
        key: str,
        signals: dict[str, Any],
        fallback: Callable[[], float | None],
        warnings: list[str],
        *,
        warn_not_implemented: bool = True,
    ) -> float | None:
        explicit = self._as_float(signals.get(key))
        if explicit is not None:
            return explicit
        if warn_not_implemented:
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
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_weakness_inputs"):
            loaded = db.get_weakness_inputs(keyword_id)
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
        gig_ids = [gig.id for gig in top_gigs]
        video_presence_map: dict[int, bool] = {}
        if gig_ids:
            visual_rows = (
                session.query(GigVisualAnalysis)
                .filter(GigVisualAnalysis.gig_id.in_(gig_ids))
                .order_by(GigVisualAnalysis.created_at.desc())
                .all()
            )
            for row in visual_rows:
                if row.gig_id not in video_presence_map and row.has_video is not None:
                    video_presence_map[row.gig_id] = bool(row.has_video)
        top10_has_video = [self._resolve_has_video(gig, video_presence_map.get(gig.id)) for gig in top_gigs]
        top10_has_portfolio = [self._resolve_has_portfolio(gig) for gig in top_gigs]
        signals = {
            "keyword": keyword.keyword if keyword else "",
            "video_absence_rate": self._absence_rate_from_presence(top10_has_video),
            "portfolio_absence_rate": self._absence_rate_from_presence(top10_has_portfolio),
            "top10_has_video": top10_has_video or None,
            "top10_has_portfolio": top10_has_portfolio or None,
        }

        quality_rows_present = False
        # Supplementary: when available, prefer table-backed quality signals.
        try:
            from src.models.gig_quality_score import GigQualityScore, get_gig_quality_scores

            top_gig_urls = {
                gig.gig_url
                for gig in top_gigs
                if isinstance(getattr(gig, "gig_url", None), str) and gig.gig_url
            }
            quality_rows_all: list[GigQualityScore] = get_gig_quality_scores(keyword_id, session)
            quality_rows = [
                row
                for row in quality_rows_all
                if isinstance(getattr(row, "gig_url", None), str) and row.gig_url in top_gig_urls
            ]
            if quality_rows:
                quality_rows_present = True
                video_known = [row.video_present for row in quality_rows if row.video_present is not None]
                if video_known:
                    video_absence = sum(1 for value in video_known if not value) / len(video_known)
                    signals["video_absence_rate"] = video_absence
                    signals["top10_has_video"] = list(video_known)

                portfolio_known = [row.portfolio_count for row in quality_rows if row.portfolio_count is not None]
                if portfolio_known:
                    portfolio_absence = sum(1 for count in portfolio_known if count == 0) / len(portfolio_known)
                    signals["portfolio_absence_rate"] = portfolio_absence

                signals["gig_quality_score_available"] = any(row.analysis_complete for row in quality_rows)
        except Exception:
            pass

        # Stage 11 table fallback when Stage 7 rows are unavailable.
        if not quality_rows_present:
            try:
                from src.models.market import GigQualityAnalysis

                analysis_rows = (
                    session.query(GigQualityAnalysis)
                    .filter(GigQualityAnalysis.gig_url.in_(top_gig_urls))
                    .order_by(GigQualityAnalysis.analyzed_at.desc())
                    .all()
                )
                latest_by_url: dict[str, Any] = {}
                for analysis_row in analysis_rows:
                    gig_url = getattr(analysis_row, "gig_url", None)
                    if isinstance(gig_url, str) and gig_url not in latest_by_url:
                        latest_by_url[gig_url] = analysis_row
                scoped_rows = list(latest_by_url.values())
                if scoped_rows:
                    video_absence = sum(
                        1 for row in scoped_rows if bool(getattr(row, "video_absent", False))
                    ) / len(scoped_rows)
                    portfolio_absence = sum(
                        1 for row in scoped_rows if bool(getattr(row, "portfolio_absent", False))
                    ) / len(scoped_rows)
                    signals["video_absence_rate"] = video_absence
                    signals["portfolio_absence_rate"] = portfolio_absence
                    signals["top10_has_video"] = [not bool(getattr(row, "video_absent", False)) for row in scoped_rows]
                    signals["gig_quality_analysis_available"] = True
            except Exception:
                pass

        return signals

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_has_video(gig: Gig, visual_flag: bool | None) -> bool | None:
        if visual_flag is not None:
            return visual_flag
        metadata = gig.metadata_json if isinstance(gig.metadata_json, dict) else {}
        value = metadata.get("has_video")
        return value if isinstance(value, bool) else None

    @staticmethod
    def _resolve_has_portfolio(gig: Gig) -> bool | None:
        metadata = gig.metadata_json if isinstance(gig.metadata_json, dict) else {}
        value = metadata.get("has_portfolio")
        return value if isinstance(value, bool) else None

    @staticmethod
    def _absence_rate_from_presence(values: list[bool | None]) -> float | None:
        known = [value for value in values if isinstance(value, bool)]
        if not known:
            return None
        return 1.0 - (sum(1 for value in known if value) / len(known))

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
