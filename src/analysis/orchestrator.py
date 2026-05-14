"""Dry-run analysis stage orchestrator for Cycle 003 integration."""

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
    KeywordClusterInput,
)
from src.analysis.gig_quality import score_gig_quality


def run_analysis_dry_run(payload: dict[str, Any]) -> AnalysisRunSummary:
    """
    Execute keyword clustering, gig quality, and competitor profiling locally.

    This orchestrator intentionally performs no network calls and no persistence.
    """
    started_at = datetime.now(UTC)
    run_id = str(payload.get("run_id", "analysis-dry-run"))
    source_id = str(payload.get("source_id", "analysis-dry-run"))

    stages: list[AnalysisStageSummary] = []
    all_warnings: list[AnalysisWarning] = []

    # Stage 1: Keyword clustering.
    try:
        keyword_input = KeywordClusterInput.model_validate(
            {
                "source_id": source_id,
                "keywords": payload.get("keywords", []),
                "min_cluster_size": payload.get("min_cluster_size", 1),
                "metadata": payload.get("metadata", {}),
            }
        )
        keyword_result = cluster_keywords(keyword_input)
        stages.append(
            AnalysisStageSummary(
                stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                status=AnalysisStatus.SUCCESS,
                warnings=keyword_result.warnings,
                result_type="keyword_clustering",
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

    # Stage 2: Gig quality scoring.
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
                "metadata": payload.get("metadata", {}),
            }
        )
        gig_result = score_gig_quality(gig_input)
        stages.append(
            AnalysisStageSummary(
                stage=AnalysisTaskType.GIG_QUALITY,
                status=AnalysisStatus.SUCCESS,
                warnings=gig_result.warnings,
                result_type="gig_quality",
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

    # Stage 3: Competitor profile analysis.
    try:
        competitor_input = CompetitorProfileInput.model_validate(
            {
                "source_id": source_id,
                "competitors": payload.get("competitors", []),
                "metadata": payload.get("metadata", {}),
            }
        )
        competitor_result = profile_competitors(competitor_input)
        stages.append(
            AnalysisStageSummary(
                stage=AnalysisTaskType.COMPETITOR_PROFILE,
                status=AnalysisStatus.SUCCESS,
                warnings=competitor_result.warnings,
                result_type="competitor_profile",
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

    statuses = [stage.status for stage in stages]
    if all(status == AnalysisStatus.SUCCESS for status in statuses):
        run_status = AnalysisStatus.SUCCESS
    elif any(status == AnalysisStatus.SUCCESS for status in statuses):
        run_status = AnalysisStatus.RUNNING
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
        metadata=payload.get("metadata", {}),
    )
