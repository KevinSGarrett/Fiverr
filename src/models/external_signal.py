"""External signal ORM model and write/query helpers."""

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
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin, utc_now

if TYPE_CHECKING:
    from src.models.market import Keyword


class ExternalSignal(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Keyword-level external demand/trend signal record."""

    __tablename__ = "external_signals"
    tablename = __tablename__
    __table_args__ = (
        UniqueConstraint("keyword_id", "signal_type", "run_id", name="uq_external_signals_keyword_type_run"),
        Index(
            "ix_external_signals_keyword_type_collected_desc",
            "keyword_id",
            "signal_type",
            "collected_at",
        ),
        Index("ix_external_signals_run_type", "run_id", "signal_type"),
    )

    SIGNAL_GOOGLE_TRENDS = "google_trends"
    SIGNAL_REDDIT_DEMAND = "reddit_demand"
    SIGNAL_REDDIT_ACTIVITY = "reddit_activity"
    SIGNAL_AUTOCOMPLETE_POSITION = "autocomplete_position"

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signal_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ttl_hours: Mapped[int] = mapped_column(Integer, default=168, nullable=False)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    collection_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    keyword_ref: Mapped[Keyword] = relationship("Keyword", back_populates="external_signals")

    # Backward-compat field aliases used by current scoring code/tests.
    @property
    def raw_value_json(self) -> dict[str, Any]:
        value = self.signal_json
        return value if isinstance(value, dict) else {}

    @raw_value_json.setter
    def raw_value_json(self, value: dict[str, Any] | None) -> None:
        self.signal_json = value

    @property
    def normalized_value(self) -> float | None:
        return self.signal_value

    @normalized_value.setter
    def normalized_value(self, value: float | None) -> None:
        self.signal_value = value

    @property
    def source_name(self) -> str | None:
        return self.collection_method

    @source_name.setter
    def source_name(self, value: str | None) -> None:
        self.collection_method = value

def write_external_signal(
    keyword_id: int,
    signal_type: str,
    signal_value: float | None,
    signal_json: dict[str, Any] | None,
    run_id: str | None,
    collection_method: str | None,
    db: Any,
) -> ExternalSignal | None:
    """Upsert an external signal row for a keyword/type/run key."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(ExternalSignal)
        .filter(
            ExternalSignal.keyword_id == keyword_id,
            ExternalSignal.signal_type == signal_type,
            ExternalSignal.run_id == run_id,
        )
        .first()
    )
    if row is None:
        row = ExternalSignal(
            keyword_id=keyword_id,
            signal_type=signal_type,
            run_id=run_id,
        )
    row.signal_value = signal_value
    row.signal_json = signal_json
    row.collection_method = collection_method
    row.collected_at = utc_now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_signal(keyword_id: int, signal_type: str, db: Any) -> ExternalSignal | None:
    """Return the latest external signal row for the provided type."""
    if not isinstance(db, Session):
        return None
    return (
        db.query(ExternalSignal)
        .filter(
            ExternalSignal.keyword_id == keyword_id,
            ExternalSignal.signal_type == signal_type,
        )
        .order_by(ExternalSignal.collected_at.desc())
        .first()
    )


def get_all_signals(keyword_id: int, db: Any) -> list[ExternalSignal]:
    """Return all keyword signals ordered by signal type."""
    if not isinstance(db, Session):
        return []
    return (
        db.query(ExternalSignal)
        .filter(ExternalSignal.keyword_id == keyword_id)
        .order_by(ExternalSignal.signal_type.asc())
        .all()
    )
