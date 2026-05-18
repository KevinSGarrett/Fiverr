"""Price distribution analysis runner for Stage 10.5."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, variance
from typing import Any

from sqlalchemy.orm import Session

from src.models import Gig, PriceAnalysis, SearchResult, Seller


@dataclass
class RawPriceData:
    """Raw per-gig pricing and seller metadata for one keyword/run."""

    keyword_id: int
    run_id: str
    basic_prices: list[float]
    standard_prices: list[float]
    premium_prices: list[float]
    seller_review_counts: list[int]
    seller_levels: list[str]


def run_price_distribution_analysis(raw: RawPriceData, db: Any) -> PriceAnalysis:
    """Analyze collected prices and optionally persist a `PriceAnalysis` row."""

    basic_stats = _compute_tier_stats(raw.basic_prices)
    standard_stats = _compute_tier_stats(raw.standard_prices)
    premium_stats = _compute_tier_stats(raw.premium_prices)
    market_type = _classify_market_type(basic_stats)
    moat_strength = _classify_moat_strength(raw)
    review_premium = _calculate_review_premium(raw)
    basic_gaps = _find_price_gaps(raw.basic_prices) if raw.basic_prices else []

    row = PriceAnalysis(
        keyword_id=raw.keyword_id,
        run_id=raw.run_id,
        basic_n=basic_stats["n"],
        basic_min=basic_stats["min"],
        basic_max=basic_stats["max"],
        basic_median=basic_stats["median"],
        basic_mean=basic_stats["mean"],
        basic_cv=basic_stats["cv"],
        basic_skewness=basic_stats["skewness"],
        basic_gaps=basic_gaps,
        standard_n=standard_stats["n"],
        standard_min=standard_stats["min"],
        standard_max=standard_stats["max"],
        standard_median=standard_stats["median"],
        standard_mean=standard_stats["mean"],
        premium_n=premium_stats["n"],
        premium_min=premium_stats["min"],
        premium_max=premium_stats["max"],
        premium_median=premium_stats["median"],
        premium_mean=premium_stats["mean"],
        market_type=market_type,
        moat_strength=moat_strength,
        review_premium=review_premium,
    )
    if isinstance(db, Session):
        db.merge(row)
        db.commit()
    return row


def _compute_tier_stats(prices: list[float]) -> dict[str, float | int | None]:
    """Compute basic descriptive statistics for a tier."""

    if not prices:
        return {k: None for k in ("n", "min", "max", "median", "mean", "cv", "skewness")}

    n = len(prices)
    med = float(median(prices))
    mn = float(mean(prices))
    var = float(variance(prices)) if n > 1 else 0.0
    sd = var**0.5
    cv = sd / mn if mn > 0 else 0.0
    # Approximate Pearson's second skewness coefficient.
    skew = (mn - med) / sd if sd > 0 else 0.0
    return {
        "n": n,
        "min": min(prices),
        "max": max(prices),
        "median": med,
        "mean": mn,
        "cv": cv,
        "skewness": skew,
    }


def _classify_market_type(basic_stats: dict[str, float | int | None]) -> str:
    """Classify market spread from basic-tier coefficient of variation."""

    cv_raw = basic_stats.get("cv")
    cv = float(cv_raw) if cv_raw is not None else None
    if cv is None:
        return "UNKNOWN"
    if cv < 0.20:
        return "COMMODITY"
    if cv < 0.35:
        return "MODERATE_SPREAD"
    if cv < 0.60:
        return "WIDE_SPREAD"
    return "FRAGMENTED"


def _classify_moat_strength(raw: RawPriceData) -> str:
    """Estimate moat by established-vs-new seller pricing premium."""

    if not raw.basic_prices or not raw.seller_review_counts:
        return "UNKNOWN"

    established_prices = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if r >= 50]
    new_prices = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if r < 5]
    if not established_prices or not new_prices:
        return "LOW"

    new_avg = mean(new_prices)
    if new_avg <= 0:
        return "LOW"
    premium = mean(established_prices) / new_avg - 1.0
    if premium > 0.30:
        return "HIGH"
    if premium > 0.15:
        return "MEDIUM"
    return "LOW"


def _calculate_review_premium(raw: RawPriceData) -> float | None:
    """Absolute USD delta between established and new seller pricing."""

    if not raw.basic_prices or not raw.seller_review_counts:
        return None
    established = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if r >= 50]
    newbie = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if r < 5]
    if not established or not newbie:
        return None
    return round(mean(established) - mean(newbie), 2)


def _find_price_gaps(prices: list[float]) -> list[dict[str, float]]:
    """Find significant empty price bands in sorted data."""

    if len(prices) < 3:
        return []
    sorted_prices = sorted(prices)
    total_range = sorted_prices[-1] - sorted_prices[0]
    if total_range == 0:
        return []

    gaps: list[dict[str, float]] = []
    for idx in range(len(sorted_prices) - 1):
        gap_width = sorted_prices[idx + 1] - sorted_prices[idx]
        pct = (gap_width / total_range) * 100
        if pct > 10:
            gaps.append(
                {
                    "gap_start": sorted_prices[idx],
                    "gap_end": sorted_prices[idx + 1],
                    "gap_width": round(gap_width, 2),
                    "gap_midpoint": round((sorted_prices[idx] + sorted_prices[idx + 1]) / 2, 2),
                    "pct_of_range": round(pct, 1),
                }
            )
    return gaps


def extract_raw_price_data_from_db(keyword_id: int, run_id: str, db: Any) -> RawPriceData | None:
    """Build `RawPriceData` from persisted gigs associated to a keyword."""

    rows = (
        db.query(Gig, Seller)
        .join(SearchResult, SearchResult.gig_id == Gig.id)
        .outerjoin(Seller, Seller.id == Gig.seller_id)
        .filter(SearchResult.keyword_id == keyword_id)
        .all()
    )
    if not rows:
        return None

    basic_prices: list[float] = []
    standard_prices: list[float] = []
    premium_prices: list[float] = []
    seller_review_counts: list[int] = []
    seller_levels: list[str] = []

    for gig, seller in rows:
        basic_price, standard_price, premium_price = _extract_tier_prices(gig)
        review_count = int(gig.review_count or 0)

        if basic_price is not None:
            basic_prices.append(basic_price)
            seller_review_counts.append(review_count)
            seller_levels.append(seller.level if seller and seller.level else "NO_LEVEL")
        if standard_price is not None:
            standard_prices.append(standard_price)
        if premium_price is not None:
            premium_prices.append(premium_price)

    if not basic_prices and not standard_prices and not premium_prices:
        return None

    return RawPriceData(
        keyword_id=keyword_id,
        run_id=run_id,
        basic_prices=basic_prices,
        standard_prices=standard_prices,
        premium_prices=premium_prices,
        seller_review_counts=seller_review_counts,
        seller_levels=seller_levels,
    )


def _extract_tier_prices(gig: Gig) -> tuple[float | None, float | None, float | None]:
    """Extract basic/standard/premium prices from known gig fields."""

    basic = float(gig.starting_price) if gig.starting_price is not None else None
    standard: float | None = None
    premium: float | None = None

    metadata = getattr(gig, "metadata_json", None)
    if isinstance(metadata, dict):
        packages = metadata.get("packages")
        if isinstance(packages, dict):
            standard = _price_from_package(packages.get("standard"))
            premium = _price_from_package(packages.get("premium"))
            basic = _price_from_package(packages.get("basic")) or basic
        elif isinstance(packages, list):
            basic = _price_from_package(packages[0]) or basic if len(packages) > 0 else basic
            standard = _price_from_package(packages[1]) if len(packages) > 1 else None
            premium = _price_from_package(packages[2]) if len(packages) > 2 else None
    return basic, standard, premium


def _price_from_package(pkg: Any) -> float | None:
    """Normalize price from package dict-like payload."""

    if isinstance(pkg, dict):
        value = pkg.get("price")
        if value is None:
            return None
        if not isinstance(value, int | float | str):
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        return numeric if numeric > 0 else None
    return None
