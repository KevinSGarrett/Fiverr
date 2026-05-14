"""Interface-only contracts for future analysis workflows."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.llm.validation import redact_sensitive_text


class AnalysisTaskType(StrEnum):
    """Supported analysis task categories for Epic 03 implementations."""

    KEYWORD_CLUSTERING = "keyword_clustering"
    GIG_QUALITY = "gig_quality"
    COMPETITOR_PROFILE = "competitor_profile"
    SELLER_STRENGTH = "seller_strength"
    SATURATION = "saturation"
    REVIEW_ANALYSIS = "review_analysis"
    INTENT_CLASSIFICATION = "intent_classification"


class AnalysisStatus(StrEnum):
    """Execution state for analysis envelopes."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class AnalysisError(BaseModel):
    """Sanitized error payload for analysis-facing boundaries."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_exception(cls, exc: Exception, *, code: str = "analysis_error") -> AnalysisError:
        return cls(code=code, message=redact_sensitive_text(str(exc)))


class AnalysisInput(BaseModel):
    """Input contract consumed by future analysis modules."""

    task_type: AnalysisTaskType
    run_id: str | None = None
    dataset_uri: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisOutput(BaseModel):
    """Output contract produced by future analysis modules."""

    task_type: AnalysisTaskType
    status: AnalysisStatus
    result: dict[str, Any] = Field(default_factory=dict)
    errors: list[AnalysisError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
