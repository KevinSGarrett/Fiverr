"""Result-set validation model for SRDI R8 integrity metrics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin, utc_now

if TYPE_CHECKING:
    from src.models.market import Keyword


class ResultSetValidation(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Per keyword/run relevance validation snapshot."""

    __tablename__ = "result_set_validations"
    __table_args__ = (
        UniqueConstraint("keyword_id", "run_id", name="uq_result_set_validations_keyword_run"),
        Index("ix_result_set_validations_keyword_id", "keyword_id"),
        Index("ix_result_set_validations_run_id", "run_id"),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relevant_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sponsored_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_set_relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ghost_market_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ghost_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validation_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    search_strictness_used: Mapped[str | None] = mapped_column(String(32), nullable=True)
    per_gig_relevance: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    relevance_deduction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    keyword_ref: Mapped[Keyword] = relationship("Keyword", back_populates="result_set_validations")
