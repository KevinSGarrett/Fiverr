"""Gig model and Workflow 4 persistence helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
)

if TYPE_CHECKING:
    from src.models.market import Keyword, Review
    from src.models.search_result import SearchResult
    from src.models.seller import Seller


class Gig(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base):
    """Persist gig cards/detail data keyed by a stable Fiverr gig URL."""

    __tablename__ = "gigs"
    tablename = __tablename__
    __table_args__ = (
        Index("ix_gigs_keyword_detail_collected", "keyword_id", "detail_collected"),
        Index("ix_gigs_run_keyword", "run_id", "keyword_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gig_url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    seller_username: Mapped[str] = mapped_column(String(256), nullable=False, index=True)

    gig_title_full: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    packages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    gig_extras: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    faq_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    portfolio_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_count_exact: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_exact: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_snippets: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    starting_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    orders_in_queue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail_collected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detail_collected_at: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=True)
    ttl_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=168)
    sponsored_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Legacy compatibility fields used by existing scoring/pricing paths.
    external_gig_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("sellers.id"), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    normalized_title: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    keyword_ref: Mapped[Keyword | None] = relationship(back_populates="gigs")
    seller: Mapped[Seller | None] = relationship(back_populates="gigs")
    search_results: Mapped[list[SearchResult]] = relationship(back_populates="gig")
    reviews: Mapped[list[Review]] = relationship(back_populates="gig")

    def __init__(self, **kwargs: Any) -> None:
        # Keep sparse legacy constructor calls valid while enforcing Stage-4 required columns.
        if kwargs.get("seller_username") is None:
            kwargs["seller_username"] = "unknown_seller"
        if kwargs.get("gig_url") is None:
            kwargs["gig_url"] = f"legacy://gig/{uuid4().hex}"

        if kwargs.get("gig_title_full") is None and kwargs.get("title") is not None:
            kwargs["gig_title_full"] = kwargs["title"]
        if kwargs.get("title") is None and kwargs.get("gig_title_full") is not None:
            kwargs["title"] = kwargs["gig_title_full"]
        if kwargs.get("detail_collected") is None:
            kwargs["detail_collected"] = False
        if kwargs.get("sponsored_flag") is None:
            kwargs["sponsored_flag"] = False
        if kwargs.get("ttl_hours") is None:
            kwargs["ttl_hours"] = 168

        super().__init__(**kwargs)

    def is_stale(self) -> bool:
        """Return True when detail data is missing or TTL has expired."""
        detail_collected = bool(self.detail_collected)
        collected_at = self.detail_collected_at
        ttl_hours = int(self.ttl_hours)
        if not detail_collected or collected_at is None:
            return True
        return datetime.now(UTC) > collected_at + timedelta(hours=ttl_hours)


def write_gig_card(
    gig_url: str,
    keyword_id: int,
    run_id: str,
    seller_username: str,
    position: int,
    starting_price: float | None,
    gig_title: str | None,
    sponsored_flag: bool,
    db: object,
) -> Gig | None:
    """
    Upsert a minimal Gig row from search card data.
    Call this from Workflow 3 output. Returns None if db is not a Session.
    """
    if not isinstance(db, Session):
        return None

    row = db.query(Gig).filter(Gig.gig_url == gig_url).one_or_none()
    if row is None:
        row = Gig(gig_url=gig_url, seller_username=seller_username)
        db.add(row)

    row.keyword_id = keyword_id
    row.run_id = run_id
    row.seller_username = seller_username
    row.position = position
    row.starting_price = starting_price
    row.gig_title_full = gig_title
    row.title = gig_title
    row.sponsored_flag = sponsored_flag
    row.detail_collected = False

    db.commit()
    db.refresh(row)
    return row


def get_gigs_for_keyword(keyword_id: int, db: object, limit: int = 20) -> list[Gig]:
    """Returns up to `limit` gigs for a keyword, ordered by position."""
    if not isinstance(db, Session):
        return []
    return (
        db.query(Gig)
        .filter(Gig.keyword_id == keyword_id)
        .order_by(Gig.position.asc().nullslast())
        .limit(limit)
        .all()
    )
