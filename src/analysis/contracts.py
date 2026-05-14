"""Contracts used by the Cycle 003 local analysis engines."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.llm.validation import redact_sensitive_text


class AnalysisTaskType(StrEnum):
    """Supported analysis task categories for Epic 03 implementations."""

    KEYWORD_CLUSTERING = "keyword_clustering"
    GIG_QUALITY = "gig_quality"
    COMPETITOR_PROFILE = "competitor_profile"


class AnalysisStatus(StrEnum):
    """Execution state for stage-level and run-level analysis objects."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class AnalysisError(BaseModel):
    """Sanitized error payload for analysis-facing boundaries."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_exception(cls, exc: Exception, *, code: str = "analysis_error") -> AnalysisError:
        return cls(code=code, message=redact_sensitive_text(str(exc)))


class AnalysisWarning(BaseModel):
    """Non-fatal warning produced during analysis calculations."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    missing_data_fields: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClusterEntry(BaseModel):
    """Keyword cluster details for deterministic clustering output."""

    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    size: int = Field(ge=1)
    cohesion_score: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)


class KeywordClusterInput(BaseModel):
    """Input contract for local keyword clustering."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    min_cluster_size: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KeywordClusterResult(BaseModel):
    """Output contract for keyword clustering stage."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    clusters: list[ClusterEntry] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)
    missing_data_fields: list[str] = Field(default_factory=list)
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GigQualityInput(BaseModel):
    """Input contract for deterministic gig quality scoring."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    gig_id: str = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    package_count: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    review_count: int | None = Field(default=None, ge=0)
    image_count: int | None = Field(default=None, ge=0)
    has_faq: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GigQualityResult(BaseModel):
    """Output contract for gig quality rubric scoring."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    gig_id: str = Field(min_length=1)
    overall_score: float = Field(ge=0.0, le=100.0)
    component_scores: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)
    missing_data_fields: list[str] = Field(default_factory=list)
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_component_ranges(self) -> GigQualityResult:
        for component_name, score in self.component_scores.items():
            if score < 0.0 or score > 100.0:
                raise ValueError(
                    f"Component score '{component_name}' must be between 0 and 100 inclusive."
                )
        return self


class CompetitorListingInput(BaseModel):
    """Single competitor listing/seller observation."""

    model_config = ConfigDict(extra="forbid")

    seller_id: str = Field(min_length=1)
    seller_level: str | None = None
    starting_price: float | None = Field(default=None, ge=0.0)
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    review_count: int | None = Field(default=None, ge=0)
    active_gig_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompetitorProfileInput(BaseModel):
    """Input contract for competitor profile pre-model analysis."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    competitors: list[CompetitorListingInput] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompetitorProfileResult(BaseModel):
    """Output contract for competitor profile stage."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    competition_intensity_score: float = Field(ge=0.0, le=100.0)
    dominant_seller_levels: dict[str, int] = Field(default_factory=dict)
    pricing_bands: dict[str, int] = Field(default_factory=dict)
    rating_review_concentration: str = Field(min_length=1)
    high_authority_sellers: list[str] = Field(default_factory=list)
    weak_competitors: list[str] = Field(default_factory=list)
    opportunity_signals: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)
    missing_data_fields: list[str] = Field(default_factory=list)
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisStageSummary(BaseModel):
    """Summary for one stage run in an orchestrated dry-run."""

    model_config = ConfigDict(extra="forbid")

    stage: AnalysisTaskType
    status: AnalysisStatus
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    error: AnalysisError | None = None
    result_type: (
        Literal["keyword_clustering", "gig_quality", "competitor_profile", "none"] | None
    ) = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisRunSummary(BaseModel):
    """Dry-run orchestrator result spanning all analysis stages."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    started_at: datetime
    finished_at: datetime
    status: AnalysisStatus
    stages: list[AnalysisStageSummary] = Field(default_factory=list)
    warnings: list[AnalysisWarning] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
