"""Core market and research entity models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, UniqueConstraint
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
    search_volume_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)

    niche: Mapped[Niche] = relationship(back_populates="keywords")
    search_results: Mapped[list[SearchResult]] = relationship(back_populates="keyword_ref")
    external_signals: Mapped[list[ExternalSignal]] = relationship(back_populates="keyword_ref")


class SearchResult(
    IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base
):
    __tablename__ = "search_results"
    __table_args__ = (UniqueConstraint("keyword_id", "rank", name="uq_search_results_keyword_rank"),)

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    result_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    observed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    keyword_ref: Mapped[Keyword] = relationship(back_populates="search_results")
    gig: Mapped[Gig | None] = relationship(back_populates="search_results")


class Seller(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, Base):
    __tablename__ = "sellers"
    __table_args__ = (UniqueConstraint("seller_handle", name="uq_sellers_seller_handle"),)

    seller_handle: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    gigs: Mapped[list[Gig]] = relationship(back_populates="seller")


class Gig(
    IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base
):
    __tablename__ = "gigs"
    __table_args__ = (UniqueConstraint("external_gig_id", name="uq_gigs_external_gig_id"),)

    external_gig_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("sellers.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_title: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    starting_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    seller: Mapped[Seller | None] = relationship(back_populates="gigs")
    search_results: Mapped[list[SearchResult]] = relationship(back_populates="gig")
    reviews: Mapped[list[Review]] = relationship(back_populates="gig")


class Review(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, Base):
    __tablename__ = "reviews"

    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_text: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    reviewer_handle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    review_date_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    gig: Mapped[Gig | None] = relationship(back_populates="reviews")


class ExternalSignal(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "external_signals"

    source_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    raw_value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    normalized_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    collected_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    keyword_ref: Mapped[Keyword | None] = relationship(back_populates="external_signals")
