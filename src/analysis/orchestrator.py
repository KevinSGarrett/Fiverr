"""Dry-run analysis stage orchestrator for local integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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


def run_analysis_dry_run(payload: dict[str, Any]) -> AnalysisRunSummary:
    """
    Execute local deterministic analysis stages.

    This orchestrator intentionally performs no network calls and no persistence.
    """
    started_at = datetime.now(UTC)
    run_id = str(payload.get("run_id", "analysis-dry-run"))
    source_id = str(payload.get("source_id", "analysis-dry-run"))

    stages: list[AnalysisStageSummary] = []
    all_warnings: list[AnalysisWarning] = []

    metadata = payload.get("metadata", {})
    seller_strength_scores: list[float] = []
    gig_quality_scores: list[float] = []

    if "keywords" in payload:
        try:
            keyword_input = KeywordClusterInput.model_validate(
                {
                    "source_id": source_id,
                    "keywords": payload.get("keywords", []),
                    "min_cluster_size": payload.get("min_cluster_size", 1),
                    "metadata": metadata,
                }
            )
            keyword_result = cluster_keywords(keyword_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                    status=AnalysisStatus.SUCCESS,
                    warnings=keyword_result.warnings,
                    result_type="keyword_clustering",
                    metadata={
                        "cluster_count": len(keyword_result.clusters),
                        "warning_count": len(keyword_result.warnings),
                        "missing_field_count": len(keyword_result.missing_data_fields),
                    },
                )
            )
            all_warnings.extend(keyword_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="keyword_stage_failed"),
                    result_type="none",
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
                    "metadata": metadata,
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
                    metadata={
                        "strength_count": len(gig_result.strengths),
                        "weakness_count": len(gig_result.weaknesses),
                        "warning_count": len(gig_result.warnings),
                    },
                )
            )
            all_warnings.extend(gig_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.GIG_QUALITY,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="gig_stage_failed"),
                    result_type="none",
                )
            )

    if "competitors" in payload:
        try:
            competitor_input = CompetitorProfileInput.model_validate(
                {
                    "source_id": source_id,
                    "competitors": payload.get("competitors", []),
                    "metadata": metadata,
                }
            )
            competitor_result = profile_competitors(competitor_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.COMPETITOR_PROFILE,
                    status=AnalysisStatus.SUCCESS,
                    warnings=competitor_result.warnings,
                    result_type="competitor_profile",
                    metadata={
                        "competitor_count": len(competitor_input.competitors),
                        "high_authority_count": len(competitor_result.high_authority_sellers),
                        "warning_count": len(competitor_result.warnings),
                    },
                )
            )
            all_warnings.extend(competitor_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.COMPETITOR_PROFILE,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="competitor_stage_failed"),
                    result_type="none",
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
                    "seller_id": seller_source.get("seller_id", "seller-dry-run"),
                    "level": seller_source.get("level"),
                    "rating": seller_source.get("rating"),
                    "review_count": seller_source.get("review_count"),
                    "response_time": seller_source.get("response_time"),
                    "delivery_consistency": seller_source.get("delivery_consistency"),
                    "active_gig_count": seller_source.get("active_gig_count"),
                    "languages": seller_source.get("languages", []),
                    "account_tenure_months": seller_source.get("account_tenure_months"),
                    "metadata": metadata,
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
                                "metadata": metadata,
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
                    metadata={
                        "evaluated_sellers": len(seller_strength_scores),
                        "warning_count": len(seller_result.warnings),
                        "component_count": len(seller_result.components),
                    },
                )
            )
            all_warnings.extend(seller_result.warnings)
        except (ValidationError, ValueError, AttributeError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SELLER_STRENGTH,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="seller_strength_stage_failed"),
                    result_type="none",
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
                    "metadata": metadata,
                }
            )
            saturation_result = analyze_saturation(saturation_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SATURATION,
                    status=AnalysisStatus.SUCCESS,
                    warnings=saturation_result.warnings,
                    result_type="saturation",
                    metadata={
                        "saturation_level": saturation_result.saturation_level.value,
                        "component_count": len(saturation_result.components),
                        "warning_count": len(saturation_result.warnings),
                    },
                )
            )
            all_warnings.extend(saturation_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SATURATION,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="saturation_stage_failed"),
                    result_type="none",
                )
            )

    if "reviews" in payload:
        try:
            review_input = ReviewAnalysisInput.model_validate(
                {
                    "source_id": source_id,
                    "reviews": payload.get("reviews", []),
                    "metadata": metadata,
                }
            )
            review_result = analyze_reviews(review_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.REVIEW_ANALYSIS,
                    status=AnalysisStatus.SUCCESS,
                    warnings=review_result.warnings,
                    result_type="review_analysis",
                    metadata={
                        "theme_count": len(review_result.themes),
                        "complaint_theme_count": len(review_result.complaint_frequency),
                        "warning_count": len(review_result.warnings),
                    },
                )
            )
            all_warnings.extend(review_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.REVIEW_ANALYSIS,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="review_stage_failed"),
                    result_type="none",
                )
            )

    if "intent" in payload or "keyword_text" in payload or "keywords" in payload:
        try:
            intent_section = payload.get("intent", {})
            inferred_keyword = ""
            keywords_section = payload.get("keywords")
            if isinstance(keywords_section, list) and keywords_section:
                inferred_keyword = str(keywords_section[0])
            keyword_text: str
            if isinstance(intent_section, dict):
                if "keyword_text" in intent_section:
                    keyword_text = str(intent_section.get("keyword_text"))
                else:
                    keyword_text = str(payload.get("keyword_text") or inferred_keyword or source_id)
                title_phrases = intent_section.get("title_phrases", [])
            else:
                keyword_text = str(payload.get("keyword_text") or inferred_keyword or source_id)
                title_phrases = payload.get("title_phrases", [])
            intent_input = IntentInput.model_validate(
                {
                    "source_id": source_id,
                    "keyword_text": keyword_text,
                    "title_phrases": title_phrases,
                    "metadata": metadata,
                }
            )
            intent_result = classify_intent(intent_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.INTENT_CLASSIFICATION,
                    status=AnalysisStatus.SUCCESS,
                    warnings=intent_result.warnings,
                    result_type="intent_classification",
                    metadata={
                        "label": intent_result.label.value,
                        "matched_rule_count": len(intent_result.matched_rules),
                        "warning_count": len(intent_result.warnings),
                    },
                )
            )
            all_warnings.extend(intent_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.INTENT_CLASSIFICATION,
                    status=AnalysisStatus.FAILED,
                    error=AnalysisError.from_exception(exc, code="intent_stage_failed"),
                    result_type="none",
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
            **metadata,
        },
    )
