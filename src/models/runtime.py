"""Runtime, job, and artifact persistence models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, SoftStatusMixin, TimestampMixin


class RunLog(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "run_logs"

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(2048), nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class JobStatus(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "job_statuses"
    __table_args__ = (UniqueConstraint("job_key", name="uq_job_statuses_job_key"),)

    job_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    progress: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class AlertEvent(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "alert_events"

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(2048), nullable=False)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ExportArtifact(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "export_artifacts"

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    export_format: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LLMUsageLog(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "llm_usage_logs"

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    prompt_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    request_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LLMCacheRecord(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_cache_records"
    __table_args__ = (UniqueConstraint("cache_key", name="uq_llm_cache_records_cache_key"),)

    cache_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    expires_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
