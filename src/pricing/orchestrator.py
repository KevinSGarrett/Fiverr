"""Wave 9 pricing orchestration (Stage 10.5)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Gig, Keyword, Niche, PricingSnapshot
from src.pricing.analysis import persist_keyword_pricing
from src.pricing.contracts import (
    EntryPricingRecommendation,
    PriceDistribution,
    PricingInput,
    PricingOutput,
)
from src.pricing.new_seller_pricing import calculate_new_seller_pricing, get_niche_config

logger = logging.getLogger(__name__)


def run_stage_10_5(keyword_id: int, db: Any, run_id: str = "manual") -> dict[str, Any]:
    """Stage 10.5: Price Distribution Analysis. Skips gracefully if no gig data."""
    if not isinstance(db, Session):
        return {"status": "skipped", "reason": "invalid_db_session", "n_gigs": 0}
    gig_count = db.query(func.count(Gig.id)).filter(Gig.keyword_id == keyword_id).scalar() or 0
    if gig_count < 3:
        return {"status": "skipped", "reason": "insufficient_gig_data", "n_gigs": int(gig_count)}

    price_analysis_row, _ = persist_keyword_pricing(keyword_id=keyword_id, run_id=run_id, db=db)
    if price_analysis_row is None:
        return {"status": "skipped", "reason": "empty_distribution", "n_gigs": int(gig_count)}

    niche_config = get_niche_config(keyword_id, db)
    pricing = calculate_new_seller_pricing(keyword_id, price_analysis_row, niche_config, db)
    snapshot = PricingSnapshot(
        keyword_id=keyword_id,
        niche_id=price_analysis_row.niche_id,
        run_id=run_id,
        entry_basic=pricing.entry_basic,
        entry_standard=pricing.entry_standard,
        entry_premium=pricing.entry_premium,
        acquisition_basic=pricing.acquisition_basic,
        acquisition_standard=pricing.acquisition_standard,
        acquisition_premium=pricing.acquisition_premium,
        target_basic=pricing.target_basic,
        target_standard=pricing.target_standard,
        target_premium=pricing.target_premium,
        price_ladder=pricing.price_ladder,
        undercut_pct=pricing.undercut_pct,
        moat_adjustment=pricing.moat_adjustment,
        gap_pricing_used=pricing.gap_pricing_used,
        gap_target=pricing.gap_target,
        market_type=pricing.market_type,
        confidence=pricing.confidence,
    )
    db.add(snapshot)
    db.flush()
    return {"status": "complete", "n_gigs": int(gig_count)}


def run_stage_10_5_for_niche(niche_id: str, db: Any, run_id: str = "manual") -> dict[str, Any]:
    """Run Stage 10.5 for all keywords in one niche."""
    if not isinstance(db, Session):
        return {"niche_id": niche_id, "analyzed": 0, "skipped": 0}
    keywords = get_keywords_for_niche(niche_id=niche_id, db=db)
    n_analyzed = 0
    n_skipped = 0
    for keyword in keywords:
        result = run_stage_10_5(int(keyword.id), db, run_id=run_id)
        if result.get("status") == "complete":
            n_analyzed += 1
        else:
            n_skipped += 1
    logger.info(
        "Stage 10.5 niche complete",
        extra={"niche_id": niche_id, "analyzed": n_analyzed, "skipped": n_skipped},
    )
    return {"niche_id": niche_id, "analyzed": n_analyzed, "skipped": n_skipped}


def run_pricing_stage(
    run_id: str,
    keyword_ids: list[int],
    db: Any,
    config: dict[str, Any] | None,
) -> dict[str, int | str]:
    """Run Stage 10.5 across keyword ids."""
    del config
    summary: dict[str, int | str] = {"analyzed": 0, "priced": 0, "failed": 0, "run_id": run_id}
    for keyword_id in keyword_ids:
        try:
            result = run_stage_10_5(keyword_id=keyword_id, db=db, run_id=run_id)
            if result.get("status") == "complete":
                summary["analyzed"] = int(summary["analyzed"]) + 1
                summary["priced"] = int(summary["priced"]) + 1
            else:
                summary["failed"] = int(summary["failed"]) + 1
        except Exception:  # noqa: BLE001
            logger.exception("Pricing stage failed for keyword_id=%s run_id=%s", keyword_id, run_id)
            summary["failed"] = int(summary["failed"]) + 1
    return summary


def _get_niche_config_for_keyword(keyword_id: int, db: Any, config: dict[str, Any] | None) -> dict[str, Any]:
    """Backward-compatible config resolver used by legacy tests."""
    del config
    return get_niche_config(keyword_id, db)


def get_keywords_for_niche(niche_id: str, db: Any) -> list[Keyword]:
    """Resolve keywords for string slug or numeric niche id."""
    if not isinstance(db, Session):
        return []
    if str(niche_id).isdigit():
        return db.query(Keyword).filter(Keyword.niche_id == int(niche_id)).all()
    niche = db.query(Niche).filter(Niche.slug == niche_id).first()
    if niche is None:
        return []
    return db.query(Keyword).filter(Keyword.niche_id == niche.id).all()


class PricingOrchestrator:
    """Compatibility scaffold class retained for historical tests."""

    def analyze(self, pricing_input: PricingInput) -> PricingOutput:
        return PricingOutput(
            run_id=pricing_input.run_id,
            niche_id=pricing_input.niche_id,
            keyword_id=pricing_input.keyword_id,
        )

    def compute_distribution(self, prices: list[float], niche_id: str, keyword: str) -> PriceDistribution:
        return PriceDistribution(niche_id=niche_id, keyword=keyword, sample_count=len(prices), raw_prices=prices)

    def recommend_entry_pricing(
        self,
        distribution: PriceDistribution,
        starter_basic: float,
        starter_standard: float,
        starter_premium: float,
    ) -> EntryPricingRecommendation:
        return EntryPricingRecommendation(
            niche_id=distribution.niche_id,
            keyword=distribution.keyword,
            basic_price=starter_basic,
            standard_price=starter_standard,
            premium_price=starter_premium,
            confidence=0.0,
            rationale="Compatibility scaffold recommendation.",
        )
