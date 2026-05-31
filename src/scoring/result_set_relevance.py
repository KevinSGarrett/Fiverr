"""Shared helpers for ResultSetValidation reads and adjustments."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from src.models import ResultSetValidation


def get_result_set_validation(keyword_id: int, session: Any) -> ResultSetValidation | None:
    if not isinstance(session, Session):
        return None
    return (
        session.query(ResultSetValidation)
        .filter(ResultSetValidation.keyword_id == keyword_id)
        .order_by(ResultSetValidation.validated_at.desc(), ResultSetValidation.id.desc())
        .first()
    )


def apply_trc_adjustments(
    trc: float,
    rsv: ResultSetValidation | None,
    sponsored_fraction: float | None,
) -> float:
    """DL-209 seam: apply only one conservative multiplier (never stacked)."""
    r2_factor = (
        float(rsv.result_set_relevance_score)
        if rsv is not None and rsv.result_set_relevance_score is not None and rsv.result_set_relevance_score < 0.80
        else 1.0
    )
    r3_factor = (1.0 - float(sponsored_fraction)) if sponsored_fraction is not None and sponsored_fraction > 0.20 else 1.0
    return float(trc) * min(r2_factor, r3_factor)
