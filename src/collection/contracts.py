"""Type-safe, side-effect-free contracts for collection stages."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

REQUIRED_COLLECTION_SUMMARY_STAGES: tuple[str, ...] = (
    "stage_1_keyword_expansion",
    "stage_2b_autocomplete",
    "stage_2_search_plan",
    "stage_4_gig_detail",
    "stage_5_seller_profile",
    "stage_7_checkpoint_metadata",
    "stage_8_pacing_decisions",
)


class CollectionStageStatus(StrEnum):
    """High-level status for a collection stage execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class CollectionError(BaseModel):
    """Structured error payload emitted by collection stages."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CollectionStageInput(BaseModel):
    """Input envelope for future stage implementations."""

    stage_name: str
    checkpoint_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionStageResult(BaseModel):
    """Output contract for future collection orchestration."""

    stage_name: str
    status: CollectionStageStatus
    records_seen: int = 0
    records_written: int = 0
    errors: list[CollectionError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checkpoint_path: Path | None = None
    started_at: datetime
    finished_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def validate_collection_stage_summary(summary: dict[str, Any]) -> None:
    """Validate required dry-run stage representation in one summary payload."""

    stage_counts = summary.get("stage_counts")
    if not isinstance(stage_counts, dict):
        raise ValueError("Collection stage summary requires a 'stage_counts' mapping.")

    missing_stages = [stage for stage in REQUIRED_COLLECTION_SUMMARY_STAGES if stage not in stage_counts]
    if missing_stages:
        raise ValueError(
            "Collection stage summary is missing required stages: "
            + ", ".join(sorted(missing_stages))
            + "."
        )

    invalid_stage_counts = [
        stage_name
        for stage_name, value in stage_counts.items()
        if not isinstance(value, int) or value < 0
    ]
    if invalid_stage_counts:
        raise ValueError(
            "Collection stage summary has invalid stage_counts values for: "
            + ", ".join(sorted(invalid_stage_counts))
            + "."
        )
