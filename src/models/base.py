"""SQLAlchemy declarative base and reusable model mixins."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, DateTime, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

naming_convention: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utc_now() -> datetime:
    """Return an explicit UTC timestamp."""
    return datetime.now(UTC)


def safe_json_default(value: Any) -> Any:
    """JSON serializer for common non-JSON-native values."""
    if isinstance(value, (datetime | date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, set):
        return sorted(value)
    return str(value)


class Base(DeclarativeBase):
    """Declarative base with stable naming conventions for migrations."""

    metadata = MetaData(naming_convention=naming_convention)


class IntegerPrimaryKeyMixin:
    """Reusable integer primary key."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TimestampMixin:
    """Created/updated timestamps stored in UTC."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class ExternalSourceMixin:
    """Common source-tracking fields for collected records."""

    external_source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MetadataJSONMixin:
    """Metadata payload field for flexible record enrichment."""

    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class SoftStatusMixin:
    """Simple lifecycle status and optional error details."""

    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)


def dumps_json(value: Any) -> str:
    """Dump JSON consistently using the safe serializer."""
    return json.dumps(value, default=safe_json_default, sort_keys=True)
