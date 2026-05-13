"""Type-safe, side-effect-free contracts for collection stages."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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
