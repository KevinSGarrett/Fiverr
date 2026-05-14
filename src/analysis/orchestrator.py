"""Dry-run analysis stage orchestrator for local integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from pydantic import ValidationError

from src.analysis.clustering import cluster_keywords
from src.analysis.competitors import profile_competitors
from src.analysis.contracts import (
    AnalysisError,
    AnalysisRunSummary,
    AnalysisStageSummary,
    AnalysisStatus,
    AnalysisTaskType,
    AnalysisWarning,
    CompetitorProfileInput,
    GigQualityInput,
    IntentInput,
    KeywordClusterInput,
    ReviewAnalysisInput,
    SaturationInput,
    SellerStrengthInput,
)
from src.analysis.gig_quality import score_gig_quality
from src.analysis.intent import classify_intent
from src.analysis.reviews import analyze_reviews
from src.analysis.saturation import analyze_saturation
from src.analysis.seller_strength import score_seller_strength


def _stage_metadata(
    source_id: str,
    *,
    result_count: int = 0,
    warning_count: int = 0,
    missing_field_count: int = 0,
    **extras: Any,
) -> dict[str, Any]:
    """Build stable metadata keys required by dry-run consumers."""
    return {
        "source_id": source_id,
        "result_count": result_count,
        "warning_count": warning_count,
        "missing_field_count": missing_field_count,
        **extras,
    }


def _failed_stage_summary(
    *,
    stage: AnalysisTaskType,
    source_id: str,
    code: str,
    exc: Exception,
) -> AnalysisStageSummary:
    """Create stable failed-stage summaries without dropping error details."""
    error = AnalysisError.from_exception(exc, code=code)
    return AnalysisStageSummary(
        stage=stage,
        status=AnalysisStatus.FAILED,
        error=error,
        result_type="none",
        metadata=_stage_metadata(
            source_id,
            result_count=0,
            warning_count=0,
            missing_field_count=0,
            error_code=error.code,
            failed=True,
        ),
    )


def summarize_scoring_readiness(
    stages: list[AnalysisStageSummary], payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Summarize which analysis outputs are available for downstream scoring."""
    successful_stages = {
        stage.stage for stage in stages if stage.status == AnalysisStatus.SUCCESS
    }
    payload_dict = payload if isinstance(payload, dict) else {}
    demand_inputs = (
        AnalysisTaskType.INTENT_CLASSIFICATION in successful_stages
        or AnalysisTaskType.KEYWORD_CLUSTERING in successful_stages
        or bool(payload_dict.get("keywords"))
    )
    readiness: dict[str, Any] = {
        "demand_inputs": demand_inputs,
        "competition_inputs": AnalysisTaskType.COMPETITOR_PROFILE in successful_stages,
        "saturation_inputs": AnalysisTaskType.SATURATION in successful_stages,
        "review_signals": AnalysisTaskType.REVIEW_ANALYSIS in successful_stages,
        "intent_signals": AnalysisTaskType.INTENT_CLASSIFICATION in successful_stages,
        "seller_strength": AnalysisTaskType.SELLER_STRENGTH in successful_stages,
        "gig_quality": AnalysisTaskType.GIG_QUALITY in successful_stages,
    }
    readiness["available_count"] = sum(1 for value in readiness.values() if bool(value))
    readiness["total_expected"] = 7
    return readiness


def _non_empty_text_or_none(value: Any) -> str | None:
    """Return text only when value is present and not blank."""
    if value is None:
        return None
    text = value if isinstance(value, str) else str(value)
    normalized = text.strip().lower()
    if not normalized:
        return None
    if normalized in {"none", "null"}:
        return None
    return text


def _resolve_intent_keyword_text(payload: dict[str, Any], source_id: str) -> str:
    """Resolve keyword text with explicit null/blank fallback handling."""
    intent_section = payload.get("intent", {})
    if isinstance(intent_section, dict):
        intent_keyword = _non_empty_text_or_none(intent_section.get("keyword_text"))
        if intent_keyword is not None:
            return intent_keyword

    payload_keyword = _non_empty_text_or_none(payload.get("keyword_text"))
    if payload_keyword is not None:
        return payload_keyword

    keywords_section = payload.get("keywords")
    if isinstance(keywords_section, list):
        for keyword in keywords_section:
            candidate = _non_empty_text_or_none(keyword)
            if candidate is not None:
                return candidate

    # Preserve source_id fallback so intent classification still receives a stable key.
    return source_id


def run_analysis_dry_run(payload: dict[str, Any]) -> AnalysisRunSummary:
    """
    Execute local deterministic analysis stages.

    This orchestrator intentionally performs no network calls and no persistence.
    """
    started_at = datetime.now(UTC)
    if not isinstance(payload, dict):
        finished_at = datetime.now(UTC)
        return AnalysisRunSummary(
            run_id="analysis-dry-run",
            source_id="analysis-dry-run",
            started_at=started_at,
            finished_at=finished_at,
            status=AnalysisStatus.FAILED,
            stages=[],
            warnings=[],
            metadata={
                "executed_stage_count": 0,
                "success_stage_count": 0,
                "failed_stage_count": 0,
                "invalid_input": True,
                "invalid_input_type": type(payload).__name__,
                "scoring_readiness": summarize_scoring_readiness([], {}),
            },
        )

    run_id = str(payload.get("run_id", "analysis-dry-run"))
    source_id = _non_empty_text_or_none(payload.get("source_id")) or "analysis-dry-run"

    stages: list[AnalysisStageSummary] = []
    all_warnings: list[AnalysisWarning] = []

    metadata = payload.get("metadata", {})
    metadata_dict = metadata if isinstance(metadata, dict) else {}
    seller_strength_scores: list[float] = []
    gig_quality_scores: list[float] = []

    if "keywords" in payload:
        try:
            keyword_input = KeywordClusterInput.model_validate(
                {
                    "source_id": source_id,
                    "keywords": payload.get("keywords", []),
                    "min_cluster_size": payload.get("min_cluster_size", 1),
                    "metadata": metadata_dict,
                }
            )
            keyword_result = cluster_keywords(keyword_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                    status=AnalysisStatus.SUCCESS,
                    warnings=keyword_result.warnings,
                    result_type="keyword_clustering",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=len(keyword_result.clusters),
                        warning_count=len(keyword_result.warnings),
                        missing_field_count=len(keyword_result.missing_data_fields),
                        cluster_count=len(keyword_result.clusters),
                    ),
                )
            )
            all_warnings.extend(keyword_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                    source_id=source_id,
                    code="keyword_stage_failed",
                    exc=exc,
                )
            )

    if "gig" in payload:
        try:
            gig_input = GigQualityInput.model_validate(
                {
                    "source_id": source_id,
                    "gig_id": payload.get("gig", {}).get("gig_id", "dry-run-gig"),
                    "title": payload.get("gig", {}).get("title"),
                    "description": payload.get("gig", {}).get("description"),
                    "package_count": payload.get("gig", {}).get("package_count"),
                    "rating": payload.get("gig", {}).get("rating"),
                    "review_count": payload.get("gig", {}).get("review_count"),
                    "image_count": payload.get("gig", {}).get("image_count"),
                    "has_faq": payload.get("gig", {}).get("has_faq"),
                    "metadata": metadata_dict,
                }
            )
            gig_result = score_gig_quality(gig_input)
            gig_quality_scores.append(gig_result.overall_score)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.GIG_QUALITY,
                    status=AnalysisStatus.SUCCESS,
                    warnings=gig_result.warnings,
                    result_type="gig_quality",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=1,
                        warning_count=len(gig_result.warnings),
                        missing_field_count=len(gig_result.missing_data_fields),
                        strength_count=len(gig_result.strengths),
                        weakness_count=len(gig_result.weaknesses),
                    ),
                )
            )
            all_warnings.extend(gig_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.GIG_QUALITY,
                    source_id=source_id,
                    code="gig_stage_failed",
                    exc=exc,
                )
            )

    if "competitors" in payload:
        try:
            competitor_input = CompetitorProfileInput.model_validate(
                {
                    "source_id": source_id,
                    "competitors": payload.get("competitors", []),
                    "metadata": metadata_dict,
                }
            )
            competitor_result = profile_competitors(competitor_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.COMPETITOR_PROFILE,
                    status=AnalysisStatus.SUCCESS,
                    warnings=competitor_result.warnings,
                    result_type="competitor_profile",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=len(competitor_input.competitors),
                        warning_count=len(competitor_result.warnings),
                        missing_field_count=len(competitor_result.missing_data_fields),
                        competitor_count=len(competitor_input.competitors),
                        high_authority_count=len(competitor_result.high_authority_sellers),
                    ),
                )
            )
            all_warnings.extend(competitor_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.COMPETITOR_PROFILE,
                    source_id=source_id,
                    code="competitor_stage_failed",
                    exc=exc,
                )
            )

    if "seller" in payload or "sellers" in payload:
        try:
            seller_rows = payload.get("sellers")
            if isinstance(seller_rows, list) and seller_rows:
                seller_source = seller_rows[0]
            else:
                seller_source = payload.get("seller", {})
            seller_input = SellerStrengthInput.model_validate(
                {
                    "source_id": source_id,
                    "seller_id": cast(dict[str, Any], seller_source).get("seller_id", "seller-dry-run"),
                    "level": cast(dict[str, Any], seller_source).get("level"),
                    "rating": cast(dict[str, Any], seller_source).get("rating"),
                    "review_count": cast(dict[str, Any], seller_source).get("review_count"),
                    "response_time": cast(dict[str, Any], seller_source).get("response_time"),
                    "delivery_consistency": cast(dict[str, Any], seller_source).get("delivery_consistency"),
                    "active_gig_count": cast(dict[str, Any], seller_source).get("active_gig_count"),
                    "languages": cast(dict[str, Any], seller_source).get("languages", []),
                    "account_tenure_months": cast(dict[str, Any], seller_source).get("account_tenure_months"),
                    "metadata": metadata_dict,
                }
            )
            seller_result = score_seller_strength(seller_input)
            seller_strength_scores.append(seller_result.score)
            if isinstance(seller_rows, list):
                for entry in seller_rows[1:]:
                    try:
                        additional_input = SellerStrengthInput.model_validate(
                            {
                                "source_id": source_id,
                                "seller_id": entry.get("seller_id", "seller-dry-run"),
                                "level": entry.get("level"),
                                "rating": entry.get("rating"),
                                "review_count": entry.get("review_count"),
                                "response_time": entry.get("response_time"),
                                "delivery_consistency": entry.get("delivery_consistency"),
                                "active_gig_count": entry.get("active_gig_count"),
                                "languages": entry.get("languages", []),
                                "account_tenure_months": entry.get("account_tenure_months"),
                                "metadata": metadata_dict,
                            }
                        )
                        seller_strength_scores.append(score_seller_strength(additional_input).score)
                    except ValidationError:
                        continue
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SELLER_STRENGTH,
                    status=AnalysisStatus.SUCCESS,
                    warnings=seller_result.warnings,
                    result_type="seller_strength",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=len(seller_strength_scores),
                        warning_count=len(seller_result.warnings),
                        missing_field_count=len(seller_result.missing_data_fields),
                        evaluated_sellers=len(seller_strength_scores),
                        component_count=len(seller_result.components),
                    ),
                )
            )
            all_warnings.extend(seller_result.warnings)
        except (ValidationError, ValueError, AttributeError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.SELLER_STRENGTH,
                    source_id=source_id,
                    code="seller_strength_stage_failed",
                    exc=exc,
                )
            )

    saturation_trigger_keys = {
        "keywords",
        "search_result_count",
        "competitors",
        "prices",
        "gig_quality_scores",
        "seller",
        "sellers",
    }
    if any(key in payload for key in saturation_trigger_keys):
        try:
            prices = [float(price) for price in payload.get("prices", []) if isinstance(price, (int | float))]
            if not prices and isinstance(payload.get("competitors"), list):
                prices = [
                    float(entry["starting_price"])
                    for entry in payload.get("competitors", [])
                    if isinstance(entry, dict) and isinstance(entry.get("starting_price"), (int | float))
                ]
            input_quality_scores = payload.get("gig_quality_scores", [])
            if isinstance(input_quality_scores, list):
                gig_quality_scores.extend(
                    [float(score) for score in input_quality_scores if isinstance(score, (int | float))]
                )
            saturation_input = SaturationInput.model_validate(
                {
                    "source_id": source_id,
                    "keyword_count": len(payload.get("keywords", []))
                    if isinstance(payload.get("keywords"), list)
                    else payload.get("keyword_count"),
                    "search_result_count": payload.get("search_result_count"),
                    "competitor_count": len(payload.get("competitors", []))
                    if isinstance(payload.get("competitors"), list)
                    else payload.get("competitor_count"),
                    "seller_strength_scores": seller_strength_scores,
                    "prices": prices,
                    "gig_quality_scores": gig_quality_scores,
                    "metadata": metadata_dict,
                }
            )
            saturation_result = analyze_saturation(saturation_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SATURATION,
                    status=AnalysisStatus.SUCCESS,
                    warnings=saturation_result.warnings,
                    result_type="saturation",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=len(saturation_result.components),
                        warning_count=len(saturation_result.warnings),
                        missing_field_count=len(saturation_result.missing_data_fields),
                        saturation_level=saturation_result.saturation_level.value,
                        component_count=len(saturation_result.components),
                    ),
                )
            )
            all_warnings.extend(saturation_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.SATURATION,
                    source_id=source_id,
                    code="saturation_stage_failed",
                    exc=exc,
                )
            )

    if "reviews" in payload:
        try:
            review_input = ReviewAnalysisInput.model_validate(
                {
                    "source_id": source_id,
                    "reviews": payload.get("reviews", []),
                    "metadata": metadata_dict,
                }
            )
            review_result = analyze_reviews(review_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.REVIEW_ANALYSIS,
                    status=AnalysisStatus.SUCCESS,
                    warnings=review_result.warnings,
                    result_type="review_analysis",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=len(review_result.themes),
                        warning_count=len(review_result.warnings),
                        missing_field_count=len(review_result.missing_data_fields),
                        theme_count=len(review_result.themes),
                        complaint_theme_count=len(review_result.complaint_frequency),
                    ),
                )
            )
            all_warnings.extend(review_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.REVIEW_ANALYSIS,
                    source_id=source_id,
                    code="review_stage_failed",
                    exc=exc,
                )
            )

    if "intent" in payload or "keyword_text" in payload or "keywords" in payload:
        try:
            intent_section = payload.get("intent", {})
            if isinstance(intent_section, dict):
                keyword_text = _resolve_intent_keyword_text(payload, source_id)
                title_phrases = intent_section.get("title_phrases", [])
            else:
                keyword_text = _resolve_intent_keyword_text(payload, source_id)
                title_phrases = payload.get("title_phrases", [])
            intent_input = IntentInput.model_validate(
                {
                    "source_id": source_id,
                    "keyword_text": keyword_text,
                    "title_phrases": title_phrases,
                    "metadata": metadata_dict,
                }
            )
            intent_result = classify_intent(intent_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.INTENT_CLASSIFICATION,
                    status=AnalysisStatus.SUCCESS,
                    warnings=intent_result.warnings,
                    result_type="intent_classification",
                    metadata=_stage_metadata(
                        source_id,
                        result_count=len(intent_result.matched_rules),
                        warning_count=len(intent_result.warnings),
                        missing_field_count=0,
                        label=intent_result.label.value,
                        matched_rule_count=len(intent_result.matched_rules),
                    ),
                )
            )
            all_warnings.extend(intent_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.INTENT_CLASSIFICATION,
                    source_id=source_id,
                    code="intent_stage_failed",
                    exc=exc,
                )
            )

    statuses = [stage.status for stage in stages]
    if statuses and all(status == AnalysisStatus.SUCCESS for status in statuses):
        run_status = AnalysisStatus.SUCCESS
    elif any(status == AnalysisStatus.SUCCESS for status in statuses):
        run_status = AnalysisStatus.PARTIAL
    else:
        run_status = AnalysisStatus.FAILED

    finished_at = datetime.now(UTC)
    return AnalysisRunSummary(
        run_id=run_id,
        source_id=source_id,
        started_at=started_at,
        finished_at=finished_at,
        status=run_status,
        stages=stages,
        warnings=all_warnings,
        metadata={
            "executed_stage_count": len(stages),
            "success_stage_count": sum(1 for stage in stages if stage.status == AnalysisStatus.SUCCESS),
            "failed_stage_count": sum(1 for stage in stages if stage.status == AnalysisStatus.FAILED),
            "scoring_readiness": summarize_scoring_readiness(stages, payload),
            **metadata_dict,
        },
    )
