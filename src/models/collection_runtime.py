"""Collection runtime persistence models.

Covers the 5 collection operational tables required by the Foundation source spec:
- collection_checkpoints
- collection_proxy_events
- collection_queue_items
- collection_selector_audits
- collection_session_events
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, SoftStatusMixin, TimestampMixin


class CollectionCheckpoint(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    """Persisted progress checkpoint for resumable collection runs."""

    __tablename__ = "collection_checkpoints"
    __table_args__ = (
        UniqueConstraint("run_key", "stage", name="uq_collection_checkpoints_run_key_stage"),
    )

    run_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    niche_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    items_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checkpoint_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CollectionProxyEvent(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    """Log entry for proxy usage and health events during collection."""

    __tablename__ = "collection_proxy_events"

    run_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    proxy_address: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CollectionQueueItem(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    """Work-queue item tracking for a collection pipeline run."""

    __tablename__ = "collection_queue_items"

    run_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    niche_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    item_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class CollectionSelectorAudit(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    """Audit record for CSS/XPath selector evaluations during scraping."""

    __tablename__ = "collection_selector_audits"

    run_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    page_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    selector: Mapped[str] = mapped_column(String(512), nullable=False)
    selector_type: Mapped[str] = mapped_column(String(32), nullable=False)
    matched: Mapped[bool] = mapped_column(default=False, nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CollectionSessionEvent(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    """Browser or HTTP session lifecycle event during collection."""

    __tablename__ = "collection_session_events"

    run_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
