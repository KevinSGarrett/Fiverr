"""Wave 9 new-seller pricing model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy.orm import Session

from src.config import ConfigLoader
from src.models import Keyword, Niche


@dataclass
class PricingRecommendation:
    """Complete pricing recommendation for a new seller."""

    keyword_id: int
    keyword_text: str
    niche_id: str
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
    """Calculate optimal pricing for a new seller entering a keyword."""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first() if isinstance(db, Session) else None
    keyword_text = _keyword_text(keyword)
    niche_id = _keyword_niche_id(keyword, db)

    starter_prices = niche_config.get("starter_prices", {}) if isinstance(niche_config, dict) else {}
    ref_basic = _to_positive(getattr(price_analysis, "basic_median", None), starter_prices.get("basic", 75.0))
    ref_standard = _to_positive(getattr(price_analysis, "standard_median", None), starter_prices.get("standard", 175.0))
    ref_premium = _to_positive(getattr(price_analysis, "premium_median", None), starter_prices.get("premium", 325.0))

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
    acquisition_standard = max(_apply_discount(entry_standard, 0.10), _get_floor_price("standard", niche_config))
    acquisition_premium = max(_apply_discount(entry_premium, 0.05), _get_floor_price("premium", niche_config))

    target_basic = max(ref_basic, entry_basic)
    target_standard = max(ref_standard, entry_standard)
    target_premium = max(ref_premium * 1.05, entry_premium)

    price_ladder = _build_price_ladder(
        entry_basic, entry_standard, entry_premium, target_basic, target_standard, target_premium
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
        market_type=str(getattr(price_analysis, "market_type", "UNKNOWN") or "UNKNOWN"),
        confidence=confidence,
    )


def get_niche_config(keyword_id: int, db: Any) -> dict[str, Any]:
    """Return niche config dictionary for keyword's niche."""
    config = ConfigLoader("config.yaml").load().model_dump()
    if not isinstance(db, Session):
        return {}
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if keyword is None:
        return {}
    niche = db.query(Niche).filter(Niche.id == keyword.niche_id).first()
    candidates = config.get("niches", [])
    if not isinstance(candidates, list):
        return {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("niche_id", ""))
        if niche is not None and candidate_id == str(niche.slug):
            return candidate
        if candidate_id == str(keyword.niche_id):
            return candidate
    return {}


def _calculate_undercut(price_analysis: Any) -> float:
    """Base undercut % by market type, sample density, and skewness."""
    market_type = getattr(price_analysis, "market_type", None)
    base_undercut = {
        "COMMODITY": 0.10,
        "MODERATE_SPREAD": 0.20,
        "WIDE_SPREAD": 0.25,
        "FRAGMENTED": 0.20,
    }.get(str(market_type), 0.20)

    basic_n = int(getattr(price_analysis, "basic_n", 0) or 0)
    if basic_n > 15:
        base_undercut += 0.05
    elif 0 < basic_n < 5:
        base_undercut -= 0.05

    skewness = float(getattr(price_analysis, "basic_skewness", 0.0) or 0.0)
    if skewness > 0.5:
        base_undercut -= 0.05
    elif skewness < -0.3:
        base_undercut += 0.05
    return max(0.05, min(0.40, base_undercut))


def _calculate_moat_adjustment(price_analysis: Any) -> float:
    """Return extra discount % for strong moat markets."""
    moat = str(getattr(price_analysis, "moat_strength", "LOW") or "LOW")
    if moat == "HIGH":
        return 0.10
    if moat == "MEDIUM":
        return 0.05
    return 0.0


def _find_gap_opportunity(price_analysis: Any) -> tuple[float | None, bool]:
    """Pick best lower-half basic-tier price gap candidate."""
    gaps = getattr(price_analysis, "basic_gaps", None) or []
    if not isinstance(gaps, list):
        return None, False
    basic_median = float(getattr(price_analysis, "basic_median", 0.0) or 0.0)
    best_gap: dict[str, Any] | None = None
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        gap_mid = float(gap.get("gap_midpoint", 0.0) or 0.0)
        pct = float(gap.get("pct_of_range", 0.0) or 0.0)
        if gap_mid < basic_median and pct > 15.0:
            if best_gap is None or float(gap.get("gap_width", 0.0)) > float(best_gap.get("gap_width", 0.0)):
                best_gap = gap
    if best_gap is None:
        return None, False
    return float(best_gap.get("gap_midpoint", 0.0)), True


def _apply_discount(price: float, discount: float) -> float:
    """Apply percentage discount and clamp to non-negative output."""
    bounded_discount = max(0.0, min(discount, 0.95))
    return max(0.0, price * (1.0 - bounded_discount))


def _get_floor_price(tier: str, niche_config: dict[str, Any]) -> float:
    """Return floor from niche starter_prices with dignity/fiverr minimums."""
    starter_prices = niche_config.get("starter_prices", {}) if isinstance(niche_config, dict) else {}
    starter_floor = _to_positive(starter_prices.get(tier), 0.0)
    dignity = {"basic": 15.0, "standard": 30.0, "premium": 50.0}
    return max(5.0, dignity.get(tier, 10.0), starter_floor)


def _build_price_ladder(
    entry_basic: float,
    entry_standard: float,
    entry_premium: float,
    ref_basic: float,
    ref_standard: float,
    ref_premium: float,
) -> list[dict[str, Any]]:
    """Build exactly five review milestones with ordered tier prices."""
    milestones = [5, 10, 25, 50, 100]
    ladder: list[dict[str, Any]] = []
    for milestone in milestones:
        pct = milestone / 100.0
        basic = round(entry_basic + (ref_basic - entry_basic) * pct, 0)
        standard = round(entry_standard + (ref_standard - entry_standard) * pct, 0)
        premium = round(entry_premium + (ref_premium - entry_premium) * pct, 0)
        standard = max(standard, basic * 1.4)
        premium = max(premium, standard * 1.3)
        ladder.append(
            {
                "milestone": milestone,
                "basic": float(basic),
                "standard": float(standard),
                "premium": float(premium),
            }
        )
    return ladder


def _assess_pricing_confidence(price_analysis: Any) -> str:
    """Assess confidence by number of observed gigs."""
    n = int(getattr(price_analysis, "basic_n", 0) or 0)
    if n >= 10:
        return "HIGH"
    if n >= 5:
        return "MEDIUM"
    return "LOW"


def generate_pricing_strategy_text(pricing: PricingRecommendation, niche_config: dict[str, Any] | None = None) -> str:
    """Generate deterministic plain-language strategy text."""
    del niche_config
    ladder = " -> ".join(f"{step['milestone']}r:${step['basic']:.0f}" for step in pricing.price_ladder)
    return (
        f"Enter at ${pricing.entry_basic:.0f}/${pricing.entry_standard:.0f}/${pricing.entry_premium:.0f} "
        f"with {pricing.undercut_pct:.1f}% undercut. Ladder {ladder}. "
        f"Target ${pricing.target_basic:.0f}/${pricing.target_standard:.0f}/${pricing.target_premium:.0f}. "
        f"Confidence={pricing.confidence}."
    )


def project_revenue_at_entry_pricing(pricing: PricingRecommendation, niche_config: dict[str, Any]) -> dict[str, Any]:
    """Compatibility helper retained for recommendation pipeline."""
    del niche_config
    entry_aov = pricing.entry_basic * 0.6 + pricing.entry_standard * 0.3 + pricing.entry_premium * 0.1
    return {"entry_aov": round(entry_aov, 2)}


def _keyword_text(keyword: Any) -> str:
    if keyword is None:
        return ""
    return str(getattr(keyword, "keyword_text", None) or getattr(keyword, "keyword", ""))


def _keyword_niche_id(keyword: Any, db: Any) -> str:
    if keyword is None:
        return "unknown"
    niche_fk = getattr(keyword, "niche_id", None)
    if not isinstance(db, Session) or niche_fk is None:
        return str(niche_fk) if niche_fk is not None else "unknown"
    niche = db.query(Niche).filter(Niche.id == niche_fk).first()
    if niche is not None and niche.slug:
        return str(niche.slug)
    return str(niche_fk)


def _to_positive(value: Any, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if numeric > 0 else default


def to_dict(pricing: PricingRecommendation) -> dict[str, Any]:
    """Dataclass serialization convenience for JSON storage."""
    return asdict(pricing)


def _lerp(start: float, end: float, progress: float) -> float:
    """Backward-compatible interpolation helper."""
    return start + (end - start) * progress


def _resolve_starter_prices(niche_config: dict[str, Any]) -> tuple[float, float, float]:
    """Backward-compatible starter price resolver."""
    starter_prices = niche_config.get("starter_prices", {}) if isinstance(niche_config, dict) else {}
    return (
        _to_positive(starter_prices.get("basic"), 75.0),
        _to_positive(starter_prices.get("standard"), 175.0),
        _to_positive(starter_prices.get("premium"), 325.0),
    )


def _coerce_positive(value: Any, fallback: float) -> float:
    """Backward-compatible numeric coercion."""
    return _to_positive(value, fallback)
