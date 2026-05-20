"""Core market and research entity models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

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
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    search_volume_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Discovery fields — AC-1.3.8
    is_discovery: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discovery_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hypothesis_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    niche: Mapped[Niche] = relationship(back_populates="keywords")
    search_results: Mapped[list[SearchResult]] = relationship(back_populates="keyword_ref")
    gigs: Mapped[list[Gig]] = relationship(back_populates="keyword_ref")
    external_signals: Mapped[list[ExternalSignal]] = relationship("ExternalSignal", back_populates="keyword_ref")


class AutocompleteSuggestion(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Persist Stage-8 Fiverr autocomplete suggestions per keyword/run."""

    __tablename__ = "autocomplete_suggestions"
    tablename = __tablename__
    __table_args__ = (
        UniqueConstraint(
            "keyword_id",
            "suggestion_text",
            "run_id",
            name="uq_autocomplete_suggestion",
        ),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    suggestion_text: Mapped[str] = mapped_column(String(256), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="fiverr_autocomplete")
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )

    keyword_ref: Mapped[Keyword] = relationship("Keyword")


class Review(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, Base):
    __tablename__ = "reviews"

    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_text: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    reviewer_handle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    review_date_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    gig: Mapped[Gig | None] = relationship(back_populates="reviews")


def write_autocomplete_suggestion(
    *,
    keyword_id: int,
    niche_id: str,
    suggestion_text: str,
    position: int,
    run_id: str,
    db: Any,
    source: str = "fiverr_autocomplete",
) -> AutocompleteSuggestion | None:
    """Upsert autocomplete suggestion row by keyword/suggestion/run key."""
    if not isinstance(db, Session):
        return None

    normalized_text = suggestion_text.strip()
    if not normalized_text:
        return None

    row = (
        db.query(AutocompleteSuggestion)
        .filter(
            AutocompleteSuggestion.keyword_id == keyword_id,
            AutocompleteSuggestion.suggestion_text == normalized_text,
            AutocompleteSuggestion.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = AutocompleteSuggestion(
            keyword_id=keyword_id,
            niche_id=niche_id,
            suggestion_text=normalized_text,
            run_id=run_id,
        )

    row.niche_id = niche_id
    row.position = position
    row.source = source
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = (
            db.query(AutocompleteSuggestion)
            .filter(
                AutocompleteSuggestion.keyword_id == keyword_id,
                AutocompleteSuggestion.suggestion_text == normalized_text,
                AutocompleteSuggestion.run_id == run_id,
            )
            .one_or_none()
        )
        if row is None:
            return None
    db.refresh(row)
    return row


