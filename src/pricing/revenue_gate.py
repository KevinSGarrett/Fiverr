"""Wave 9 Phase 3 revenue gate tracking utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.pricing.ladder_tracker import get_recommended_prices_at_milestone

REVENUE_GATE_MILESTONES = [5, 10, 25, 50, 100]
MONTHLY_ORDERS_ESTIMATE = 4

if TYPE_CHECKING:
    from src.models.revenue_gate_record import RevenueGateRecord


def check_revenue_gates(
    keyword_id: int, db: Session, actual_review_count: int = 0
) -> list[RevenueGateRecord]:
    """Create revenue gate records for milestone checks."""
    from src.models.revenue_gate_record import RevenueGateRecord

    entry_prices = get_recommended_prices_at_milestone(keyword_id, REVENUE_GATE_MILESTONES[0], db)
    entry_basic = float(entry_prices.get("basic") or 0.0)
    records: list[RevenueGateRecord] = []

    for milestone in REVENUE_GATE_MILESTONES:
        gate_triggered = actual_review_count >= milestone
        recommended = get_recommended_prices_at_milestone(keyword_id, milestone, db)
        rec_price = float(recommended.get("basic") or 0.0)
        revenue_delta = (rec_price - entry_basic) * MONTHLY_ORDERS_ESTIMATE
        alert_text = None
        if gate_triggered and rec_price > 0:
            alert_text = f"At {milestone} reviews: consider updating your basic price to ${rec_price:.0f}"

        record = RevenueGateRecord(
            keyword_id=keyword_id,
            milestone_reviews=milestone,
            gate_triggered=gate_triggered,
            recommended_price_at_gate=rec_price,
            actual_price_at_gate=None,
            revenue_delta_usd=revenue_delta,
            monthly_orders_estimate=MONTHLY_ORDERS_ESTIMATE,
            gate_alert_text=alert_text,
        )
        db.add(record)
        records.append(record)

    db.flush()
    return records


def fire_revenue_gate_alert(keyword_id: int, milestone_reviews: int, db: Session) -> str | None:
    """Return gate alert text when a recommended milestone price exists."""
    recommended = get_recommended_prices_at_milestone(keyword_id, milestone_reviews, db)
    basic_price = recommended.get("basic")
    if not basic_price:
        return None
    return (
        f"Milestone {milestone_reviews} reviews reached. Recommended new basic price: "
        f"${basic_price:.0f}/gig (~${basic_price * MONTHLY_ORDERS_ESTIMATE:.0f}/mo)."
    )
