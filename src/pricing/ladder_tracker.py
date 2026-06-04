"""Wave 9 Phase 3 price ladder tracking utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

LADDER_TOLERANCE = 0.15
LADDER_MILESTONES = [5, 10, 25, 50, 100]

if TYPE_CHECKING:
    from src.models.price_ladder_snapshot import PriceLadderSnapshot


def get_nearest_milestone(review_count: int) -> int:
    """Return the nearest milestone less than or equal to the review count."""
    applicable = [milestone for milestone in LADDER_MILESTONES if milestone <= review_count]
    return max(applicable) if applicable else LADDER_MILESTONES[0]


def get_recommended_prices_at_milestone(keyword_id: int, milestone: int, db: Session) -> dict[str, float | None]:
    """Read latest PricingSnapshot.price_ladder and return recommended prices for milestone."""
    from src.models.price_analysis import PricingSnapshot

    snapshot = (
        db.query(PricingSnapshot)
        .filter(PricingSnapshot.keyword_id == keyword_id)
        .order_by(PricingSnapshot.created_at.desc())
        .first()
    )
    if snapshot is None or snapshot.price_ladder is None:
        return {}

    ladder_payload: Any = snapshot.price_ladder
    if isinstance(ladder_payload, str):
        try:
            ladder_payload = json.loads(ladder_payload)
        except json.JSONDecodeError:
            return {}
    if not isinstance(ladder_payload, list):
        return {}

    for entry in ladder_payload:
        if not isinstance(entry, Mapping):
            continue
        if entry.get("milestone") == milestone:
            return {
                "basic": _as_float(entry.get("basic")),
                "standard": _as_float(entry.get("standard")),
                "premium": _as_float(entry.get("premium")),
            }
    return {}


def track_price_ladder(
    keyword_id: int,
    actual_basic: float,
    actual_standard: float,
    actual_premium: float,
    review_count: int,
    db: Session,
) -> PriceLadderSnapshot:
    """Create a ladder snapshot by comparing actual and recommended pricing."""
    from src.models.price_analysis import PricingSnapshot
    from src.models.price_ladder_snapshot import PriceLadderSnapshot

    milestone = get_nearest_milestone(review_count)
    recommended = get_recommended_prices_at_milestone(keyword_id, milestone, db)
    latest_snapshot = (
        db.query(PricingSnapshot)
        .filter(PricingSnapshot.keyword_id == keyword_id)
        .order_by(PricingSnapshot.created_at.desc())
        .first()
    )
    niche_id = latest_snapshot.niche_id if latest_snapshot and latest_snapshot.niche_id else "unknown"
    run_id = latest_snapshot.run_id if latest_snapshot else None
    rec_basic = _coalesce_price(recommended.get("basic"), actual_basic)
    rec_standard = _coalesce_price(recommended.get("standard"), actual_standard)
    rec_premium = _coalesce_price(recommended.get("premium"), actual_premium)

    delta = abs((actual_basic - rec_basic) / rec_basic) if rec_basic else 0.0
    on_track = delta <= LADDER_TOLERANCE

    snap = PriceLadderSnapshot(
        keyword_id=keyword_id,
        niche_id=niche_id,
        run_id=run_id,
        reviews_at_snapshot=review_count,
        ladder_milestone=milestone,
        actual_basic_price=actual_basic,
        actual_standard_price=actual_standard,
        actual_premium_price=actual_premium,
        recommended_basic_price=rec_basic,
        recommended_standard_price=rec_standard,
        recommended_premium_price=rec_premium,
        price_delta_pct=delta,
        on_track=on_track,
        tolerance=LADDER_TOLERANCE,
    )
    db.add(snap)
    db.flush()
    return snap


def get_ladder_progress(keyword_id: int, db: Session) -> list[dict[str, Any]]:
    """Return ladder tracking history newest first."""
    from src.models.price_ladder_snapshot import PriceLadderSnapshot

    snaps = (
        db.query(PriceLadderSnapshot)
        .filter(PriceLadderSnapshot.keyword_id == keyword_id)
        .order_by(PriceLadderSnapshot.recorded_at.desc(), PriceLadderSnapshot.id.desc())
        .all()
    )
    return [
        {
            "milestone": snap.ladder_milestone,
            "delta_pct": snap.price_delta_pct,
            "on_track": snap.on_track,
            "reviews": snap.reviews_at_snapshot,
        }
        for snap in snaps
    ]


def is_pricing_on_track(keyword_id: int, db: Session, tolerance: float = LADDER_TOLERANCE) -> bool:
    """Return True when the latest ladder snapshot is within tolerance."""
    from src.models.price_ladder_snapshot import PriceLadderSnapshot

    latest = (
        db.query(PriceLadderSnapshot)
        .filter(PriceLadderSnapshot.keyword_id == keyword_id)
        .order_by(PriceLadderSnapshot.recorded_at.desc(), PriceLadderSnapshot.id.desc())
        .first()
    )
    if latest is None:
        return True
    if latest.price_delta_pct is None:
        return True
    return float(latest.price_delta_pct) <= float(tolerance)


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coalesce_price(primary: float | None, fallback: float) -> float:
    if primary is None:
        return float(fallback)
    return float(primary)
