"""SearchResult model and persistence helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
    utc_now,
)

if TYPE_CHECKING:
    from src.models.market import Gig, Keyword


class SearchResult(
    IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base
):
    """Persist collected Fiverr search result payloads for a keyword/run/page."""

    __tablename__ = "search_results"
    tablename = __tablename__
    __table_args__ = (
        UniqueConstraint("keyword_id", "run_id", "page_collected", name="uq_search_results_keyword_run_page"),
        # Legacy compatibility for rank-based callers until downstream workflow updates land.
        UniqueConstraint("keyword_id", "rank", name="uq_search_results_keyword_rank"),
        Index("ix_search_results_run_keyword", "run_id", "keyword_id"),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, default="legacy", index=True)
    total_result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pagination_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gig_cards: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    page_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    collected_at: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    ttl_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=168)
    is_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_html_ref: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Legacy fields preserved for existing scoring/recommendation integrations.
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    result_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    observed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    keyword_ref: Mapped[Keyword] = relationship(back_populates="search_results")
    gig: Mapped[Gig | None] = relationship(back_populates="search_results")

    def __init__(self, **kwargs: Any) -> None:
        # Keep legacy callers working while new workflow callers pass run/page directly.
        rank_value = kwargs.get("rank")
        if kwargs.get("run_id") is None:
            kwargs["run_id"] = "legacy"
        if kwargs.get("page_collected") is None and isinstance(rank_value, int) and rank_value > 0:
            kwargs["page_collected"] = rank_value
        super().__init__(**kwargs)


Index(
    "ix_search_results_keyword_collected_at_desc",
    SearchResult.keyword_id,
    SearchResult.collected_at.desc(),
)


def write_search_result(
    keyword_id: int,
    run_id: str,
    total_result_count: int | None,
    pagination_depth: int | None,
    gig_cards: list[dict[str, Any]],
    page_collected: int,
    db: object,
) -> SearchResult | None:
    """Upsert a SearchResult row by keyword/run/page; return None for non-Session db."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(SearchResult)
        .filter(
            SearchResult.keyword_id == keyword_id,
            SearchResult.run_id == run_id,
            SearchResult.page_collected == page_collected,
        )
        .one_or_none()
    )
    if row is None:
        row = SearchResult(
            keyword_id=keyword_id,
            run_id=run_id,
            page_collected=page_collected,
        )
        db.add(row)

    row.total_result_count = total_result_count
    row.pagination_depth = pagination_depth
    row.gig_cards = gig_cards
    db.commit()
    db.refresh(row)
    return row


def get_latest_search_result(keyword_id: int, db: object) -> SearchResult | None:
    """Return the most recent SearchResult for this keyword."""
    if not isinstance(db, Session):
        return None
    return (
        db.query(SearchResult)
        .filter(SearchResult.keyword_id == keyword_id)
        .order_by(SearchResult.collected_at.desc())
        .first()
    )
