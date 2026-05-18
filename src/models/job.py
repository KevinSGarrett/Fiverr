"""Queue job persistence model for collection orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin

PRIORITY_VALUES = ("CRITICAL", "HIGH", "STANDARD", "LOW", "BACKGROUND")
STATUS_VALUES = ("QUEUED", "RUNNING", "COMPLETE", "FAILED", "DEAD_LETTER", "SKIPPED")


class Job(IntegerPrimaryKeyMixin, Base):
    """Queued collection task with retry and dead-letter metadata."""

    __tablename__ = "jobs"
    tablename = __tablename__
    __table_args__ = (
        CheckConstraint(
            "priority IN ('CRITICAL','HIGH','STANDARD','LOW','BACKGROUND')",
            name="priority_values",
        ),
        CheckConstraint(
            "status IN ('QUEUED','RUNNING','COMPLETE','FAILED','DEAD_LETTER','SKIPPED')",
            name="status_values",
        ),
        Index("ix_jobs_run_status", "run_id", "status"),
        Index("ix_jobs_priority_stage", "priority", "stage"),
        Index("ix_jobs_niche_status", "niche_id", "status"),
        Index("ix_jobs_type_status", "job_type", "status"),
    )

    job_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("run_logs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    stage: Mapped[int] = mapped_column(Integer, nullable=False)
    niche_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("niche_configs.niche_id"),
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="QUEUED")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_log: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    checkpoint_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    def mark_running(self) -> None:
        self.status = "RUNNING"
        self.started_at = datetime.now(UTC)

    def mark_complete(self) -> None:
        self.status = "COMPLETE"
        self.completed_at = datetime.now(UTC)
        self.duration_seconds = (
            (self.completed_at - self.started_at).total_seconds() if self.started_at else None
        )

    def mark_failed(self, error: str) -> None:
        self.retry_count += 1
        self.error_log = (self.error_log or []) + [error]
        self.status = "FAILED" if self.retry_count < self.max_retries else "DEAD_LETTER"

    def should_dead_letter(self) -> bool:
        return str(self.status) == "DEAD_LETTER"
