"""Core market and research entity models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
)
from src.models.gig import Gig
from src.models.search_result import SearchResult
from src.models.seller import Seller as Seller  # noqa: F401

if TYPE_CHECKING:
    from src.models.external_signal import ExternalSignal
    from src.models.niche import Niche


class Keyword(
    IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base
):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("niche_id", "keyword", name="uq_keywords_niche_keyword"),)

    niche_id: Mapped[int] = mapped_column(ForeignKey("niches.id"), nullable=False, index=True)
    keyword: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    normalized_keyword: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intent_class: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    search_volume_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Discovery fields — AC-1.3.8
    is_discovery: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discovery_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hypothesis_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    niche: Mapped[Niche] = relationship(back_populates="keywords")
    search_results: Mapped[list[SearchResult]] = relationship(back_populates="keyword_ref")
    gigs: Mapped[list[Gig]] = relationship(back_populates="keyword_ref")
    external_signals: Mapped[list[ExternalSignal]] = relationship("ExternalSignal", back_populates="keyword_ref")


class Review(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, Base):
    __tablename__ = "reviews"

    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_text: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    reviewer_handle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    review_date_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    gig: Mapped[Gig | None] = relationship(back_populates="reviews")


