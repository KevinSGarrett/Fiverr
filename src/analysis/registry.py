"""Analysis output registry for dashboard and integration diagnostics."""

from __future__ import annotations

from typing import Any

from src.analysis.contracts import AnalysisRunSummary, AnalysisTaskType

_ANALYSIS_OUTPUT_REGISTRY: tuple[dict[str, Any], ...] = (
    {
        "stage": AnalysisTaskType.KEYWORD_CLUSTERING.value,
        "output_type": "keyword_clusters",
        "required_fields": ["cluster_id", "label", "keyword_count", "confidence"],
        "optional_fields": ["representative_terms", "warnings", "source_metadata"],
    },
    {
        "stage": AnalysisTaskType.GIG_QUALITY.value,
        "output_type": "gig_quality",
        "required_fields": ["gig_id", "quality_score", "rubric_components", "confidence"],
        "optional_fields": ["strengths", "weaknesses", "source_references", "warnings"],
    },
    {
        "stage": AnalysisTaskType.COMPETITOR_PROFILE.value,
        "output_type": "competitor_profile",
        "required_fields": ["competition_intensity_score", "market_positioning", "confidence"],
        "optional_fields": ["strengths", "weaknesses", "seller_indicators", "warnings"],
    },
    {
        "stage": AnalysisTaskType.SELLER_STRENGTH.value,
        "output_type": "seller_strength",
        "required_fields": ["seller_id", "authority_score", "confidence"],
        "optional_fields": ["reliability_signals", "experience_indicators", "weakness_markers", "warnings"],
    },
    {
        "stage": AnalysisTaskType.SATURATION.value,
        "output_type": "saturation",
        "required_fields": ["saturation_score", "supply_depth", "demand_proxy", "threshold_band"],
        "optional_fields": ["rationale", "warnings", "source_context"],
    },
    {
        "stage": AnalysisTaskType.REVIEW_ANALYSIS.value,
        "output_type": "review_analysis",
        "required_fields": ["sentiment_band", "sample_count", "confidence"],
        "optional_fields": ["theme_list", "weakness_signals", "positive_signals", "warnings"],
    },
    {
        "stage": AnalysisTaskType.INTENT_CLASSIFICATION.value,
        "output_type": "intent",
        "required_fields": ["label", "confidence", "matched_rules"],
        "optional_fields": ["warnings", "explanation", "metadata"],
    },
)


def build_analysis_output_registry(summary: AnalysisRunSummary | None = None) -> list[dict[str, Any]]:
    """Return a deterministic registry with stage readiness for diagnostics."""
    stage_statuses: dict[str, str] = {}
    if summary is not None:
        for stage in summary.stages:
            status = stage.metadata.get("stage_status")
            if isinstance(status, str):
                stage_statuses[stage.stage.value] = status
            else:
                stage_statuses[stage.stage.value] = stage.status.value
    rows: list[dict[str, Any]] = []
    for item in _ANALYSIS_OUTPUT_REGISTRY:
        row = dict(item)
        row["readiness_status"] = stage_statuses.get(item["stage"], "unknown")
        row["is_ready"] = row["readiness_status"] == "ready"
        rows.append(row)
    return rows

