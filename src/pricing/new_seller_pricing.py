"""New-seller pricing recommendation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.models import Keyword

REVENUE_GATES = {4: 1720, 6: 4770, 9: 17795, 10: 25045, 12: 37500}


@dataclass
class PricingRecommendation:
    """Complete pricing recommendation for one keyword."""

    keyword_id: int
    keyword_text: str
    niche_id: int | None
    entry_basic: float
    entry_standard: float
    entry_premium: float
    acquisition_basic: float
    acquisition_standard: float
    acquisition_premium: float
    price_ladder: list[dict[str, Any]]
    target_basic: float
    target_standard: float
    target_premium: float
    undercut_pct: float
    moat_adjustment: float
    gap_pricing_used: bool
    gap_target: float | None
    market_type: str
    confidence: str


def calculate_new_seller_pricing(
    keyword_id: int,
    price_analysis: Any,
    niche_config: dict[str, Any],
    db: Any,
) -> PricingRecommendation:
    """Calculate entry, acquisition, and ladder pricing for a new seller."""

    starter_basic, starter_standard, starter_premium = _resolve_starter_prices(niche_config)
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first() if db is not None else None
    keyword_text = getattr(keyword, "keyword", f"keyword-{keyword_id}")
    niche_id = getattr(keyword, "niche_id", None)

    ref_basic = _coerce_positive(getattr(price_analysis, "basic_median", None), starter_basic)
    ref_standard = _coerce_positive(getattr(price_analysis, "standard_median", None), starter_standard)
    ref_premium = _coerce_positive(getattr(price_analysis, "premium_median", None), starter_premium)

    undercut_pct = _calculate_undercut(price_analysis)
    moat_adj = _calculate_moat_adjustment(price_analysis)
    gap_target, gap_used = _find_gap_opportunity(price_analysis)

    total_discount = undercut_pct + moat_adj
    entry_basic = _apply_discount(ref_basic, total_discount)
    entry_standard = _apply_discount(ref_standard, total_discount)
    entry_premium = _apply_discount(ref_premium, total_discount)

    if gap_used and gap_target is not None and gap_target < entry_basic:
        entry_basic = gap_target

    entry_basic = max(entry_basic, _get_floor_price("basic", niche_config))
    entry_standard = max(entry_standard, _get_floor_price("standard", niche_config))
    entry_premium = max(entry_premium, _get_floor_price("premium", niche_config))

    entry_standard = max(entry_standard, entry_basic * 1.5)
    entry_premium = max(entry_premium, entry_standard * 1.4)

    acquisition_basic = max(_apply_discount(entry_basic, 0.15), _get_floor_price("basic", niche_config))
    acquisition_standard = max(
        _apply_discount(entry_standard, 0.10),
        _get_floor_price("standard", niche_config),
    )
    acquisition_premium = max(
        _apply_discount(entry_premium, 0.05),
        _get_floor_price("premium", niche_config),
    )

    target_basic = ref_basic * 1.0
    target_standard = ref_standard * 1.0
    target_premium = ref_premium * 1.05

    price_ladder = _build_price_ladder(
        entry_basic,
        entry_standard,
        entry_premium,
        target_basic,
        target_standard,
        target_premium,
    )
    confidence = _assess_pricing_confidence(price_analysis)

    return PricingRecommendation(
        keyword_id=keyword_id,
        keyword_text=keyword_text,
        niche_id=niche_id,
        entry_basic=float(round(entry_basic, 0)),
        entry_standard=float(round(entry_standard, 0)),
        entry_premium=float(round(entry_premium, 0)),
        acquisition_basic=float(round(acquisition_basic, 0)),
        acquisition_standard=float(round(acquisition_standard, 0)),
        acquisition_premium=float(round(acquisition_premium, 0)),
        price_ladder=price_ladder,
        target_basic=float(round(target_basic, 0)),
        target_standard=float(round(target_standard, 0)),
        target_premium=float(round(target_premium, 0)),
        undercut_pct=round(total_discount * 100, 1),
        moat_adjustment=round(moat_adj * 100, 1),
        gap_pricing_used=gap_used,
        gap_target=float(round(gap_target, 0)) if gap_target is not None else None,
        market_type=getattr(price_analysis, "market_type", None) or "UNKNOWN",
        confidence=confidence,
    )


def _calculate_undercut(price_analysis: Any) -> float:
    """Return base undercut percentage by market conditions."""

    market_type = getattr(price_analysis, "market_type", None)
    market_key = market_type if isinstance(market_type, str) else ""
    base_undercut = {
        "COMMODITY": 0.10,
        "MODERATE_SPREAD": 0.20,
        "WIDE_SPREAD": 0.25,
        "FRAGMENTED": 0.20,
    }.get(market_key, 0.20)

    basic_n = getattr(price_analysis, "basic_n", None)
    if basic_n is not None and basic_n > 15:
        base_undercut += 0.05
    elif basic_n is not None and basic_n < 5:
        base_undercut -= 0.05

    basic_skewness = getattr(price_analysis, "basic_skewness", None)
    if basic_skewness is not None and basic_skewness > 0.5:
        base_undercut -= 0.05
    elif basic_skewness is not None and basic_skewness < -0.3:
        base_undercut += 0.05

    return max(0.05, min(0.40, base_undercut))


def _calculate_moat_adjustment(price_analysis: Any) -> float:
    """Apply extra discount in moat-heavy markets."""

    moat = getattr(price_analysis, "moat_strength", None)
    if moat == "HIGH":
        return 0.10
    if moat == "MEDIUM":
        return 0.05
    return 0.00


def _find_gap_opportunity(price_analysis: Any) -> tuple[float | None, bool]:
    """Pick the strongest lower-half basic-tier price gap."""

    gaps = getattr(price_analysis, "basic_gaps", None)
    if not gaps:
        return None, False

    basic_median = float(getattr(price_analysis, "basic_median", None) or 0.0)
    best_gap: dict[str, Any] | None = None
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        gap_mid = float(gap.get("gap_midpoint", 0))
        pct = float(gap.get("pct_of_range", 0))
        if gap_mid < basic_median and pct > 15:
            if best_gap is None or float(gap.get("gap_width", 0)) > float(best_gap.get("gap_width", 0)):
                best_gap = gap

    if best_gap is None:
        return None, False
    return float(best_gap.get("gap_midpoint", 0.0)), True


def _get_floor_price(tier: str, niche_config: dict[str, Any]) -> float:
    """Return tier floor price using dignity + optional niche floors."""

    dignity_floors = {"basic": 15.0, "standard": 30.0, "premium": 50.0}
    config_floor = niche_config.get(f"price_floor_{tier}", 0.0)
    return max(5.0, dignity_floors.get(tier, 10.0), float(config_floor))


def _build_price_ladder(
    entry_basic: float,
    entry_standard: float,
    entry_premium: float,
    target_basic: float,
    target_standard: float,
    target_premium: float,
) -> list[dict[str, Any]]:
    """Build six milestone steps from entry to target prices."""

    milestones: tuple[tuple[int, str, float], ...] = (
        (0, "Launch (0 reviews)", 0.00),
        (5, "First proof (5 reviews)", 0.25),
        (10, "Established (10 reviews)", 0.45),
        (25, "Growing (25 reviews)", 0.65),
        (50, "Proven (50 reviews)", 0.85),
        (100, "Authority (100 reviews)", 1.00),
    )
    ladder: list[dict[str, Any]] = []
    for reviews, label, progress in milestones:
        basic_price = _lerp(entry_basic, target_basic, progress)
        standard_price = _lerp(entry_standard, target_standard, progress)
        premium_price = _lerp(entry_premium, target_premium, progress)
        ladder.append(
            {
                "milestone_reviews": reviews,
                "label": label,
                "basic": float(round(basic_price, 0)),
                "standard": float(round(standard_price, 0)),
                "premium": float(round(premium_price, 0)),
                "basic_increase_pct": round(((basic_price / entry_basic) - 1) * 100, 1) if entry_basic > 0 else 0.0,
            }
        )
    return ladder


def _lerp(start: float, end: float, progress: float) -> float:
    """Linear interpolation helper."""

    return start + (end - start) * progress


def _apply_discount(price: float, discount_pct: float) -> float:
    """Apply percentage discount to a price."""

    bounded_discount = max(0.0, min(discount_pct, 0.95))
    return price * (1 - bounded_discount)


def _assess_pricing_confidence(price_analysis: Any) -> str:
    """Confidence by sample size."""

    n = int(getattr(price_analysis, "basic_n", 0) or 0)
    if n >= 10:
        return "HIGH"
    if n >= 5:
        return "MEDIUM"
    return "LOW"


def project_revenue_at_entry_pricing(pricing: PricingRecommendation, niche_config: dict[str, Any]) -> dict[str, Any]:
    """Project order volume needed to hit revenue gates."""

    del niche_config  # Reserved for future niche-specific throughput modeling.
    entry_aov = pricing.entry_basic * 0.60 + pricing.entry_standard * 0.30 + pricing.entry_premium * 0.10
    projections: dict[str, Any] = {}
    for month, target_gross in REVENUE_GATES.items():
        orders_needed = target_gross / entry_aov if entry_aov > 0 else float("inf")
        orders_per_month = orders_needed / month if month > 0 else float("inf")
        orders_per_week = orders_per_month / 4.33
        projections[f"month_{month}"] = {
            "target_gross": target_gross,
            "entry_aov": round(entry_aov, 2),
            "orders_needed": round(orders_needed, 0),
            "orders_per_month": round(orders_per_month, 1),
            "orders_per_week": round(orders_per_week, 1),
            "feasible": orders_per_week <= 10,
        }

    for step in pricing.price_ladder:
        step_aov = step["basic"] * 0.50 + step["standard"] * 0.35 + step["premium"] * 0.15
        step["projected_aov"] = round(step_aov, 2)
        step["month_12_orders_needed"] = round(37500 / step_aov, 0) if step_aov > 0 else None
    return projections


def _resolve_starter_prices(niche_config: dict[str, Any]) -> tuple[float, float, float]:
    """Support both starter_price_* and starter_prices.* styles."""

    basic = niche_config.get("starter_price_basic")
    standard = niche_config.get("starter_price_standard")
    premium = niche_config.get("starter_price_premium")
    starter_prices = niche_config.get("starter_prices")
    if isinstance(starter_prices, dict):
        basic = basic if basic is not None else starter_prices.get("basic")
        standard = standard if standard is not None else starter_prices.get("standard")
        premium = premium if premium is not None else starter_prices.get("premium")

    metadata = niche_config.get("metadata")
    if isinstance(metadata, dict):
        basic = basic if basic is not None else metadata.get("starter_price_basic")
        standard = standard if standard is not None else metadata.get("starter_price_standard")
        premium = premium if premium is not None else metadata.get("starter_price_premium")

    return (
        _coerce_positive(basic, 75.0),
        _coerce_positive(standard, 175.0),
        _coerce_positive(premium, 325.0),
    )


def _coerce_positive(value: Any, fallback: float) -> float:
    """Coerce value to positive float with fallback."""

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    return numeric if numeric > 0 else fallback
