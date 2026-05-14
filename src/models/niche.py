"""Niche and niche configuration models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
)

if TYPE_CHECKING:
    from src.models.market import Keyword


class Niche(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, MetadataJSONMixin, Base):
    """Canonical niche domain object used across collection and analysis."""

    __tablename__ = "niches"
    __table_args__ = (UniqueConstraint("slug", name="uq_niches_slug"),)

    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category_path: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    keywords: Mapped[list[Keyword]] = relationship(back_populates="niche")


class NicheConfigRecord(
    IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, Base
):
    """Persisted copy of relevant niche config slices for reproducibility."""

    __tablename__ = "niche_configs"

    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    depth: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    category_path: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
