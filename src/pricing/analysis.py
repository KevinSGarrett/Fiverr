"""Wave 9 pricing distribution analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats as scipy_stats  # type: ignore[import-untyped]
from scipy.signal import find_peaks  # type: ignore[import-untyped]
from scipy.stats import gaussian_kde  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from src.models import (
    Keyword,
    Niche,
    NichePriceAnalysis,
    PriceAnalysis,
    PricingSnapshot,
    get_gigs_for_keyword,
)


@dataclass
class PriceDistribution:
    """Statistical summary of prices for one keyword at one tier."""

    n_gigs: int
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    mode_price: float
    std_dev: float
    q1: float
    q3: float
    iqr: float
    p10: float
    p90: float
    skewness: float
    price_clusters: list[dict[str, Any]]
    price_gaps: list[dict[str, Any]]
    coefficient_of_variation: float


@dataclass
class RawPriceData:
    """Compatibility payload used by legacy pricing entrypoint."""

    keyword_id: int
    run_id: str
    basic_prices: list[float]
    standard_prices: list[float]
    premium_prices: list[float]
    seller_review_counts: list[int]
    seller_levels: list[str]


def extract_tier_prices(gigs: list[Any], tier: str) -> list[float]:
    """Extract all prices for a specific tier from gig packages."""
    prices: list[float] = []
    tier_index = {"basic": 0, "standard": 1, "premium": 2}.get(tier, 0)
    for gig in gigs:
        packages = getattr(gig, "packages", None)
        if isinstance(packages, str):
            try:
                packages = json.loads(packages)
            except json.JSONDecodeError:
                packages = None
        if not packages:
            continue

        price: float | None = None
        if isinstance(packages, dict):
            tier_data = packages.get(tier, {})
            if isinstance(tier_data, dict):
                price = _to_positive_float(tier_data.get("price"))
        elif isinstance(packages, list) and tier_index < len(packages):
            row = packages[tier_index]
            if isinstance(row, dict):
                price = _to_positive_float(row.get("price"))

        if price is not None and price > 0:
            prices.append(price)
    return prices


def detect_price_clusters(prices: np.ndarray, bandwidth_factor: float = 0.15) -> list[dict[str, Any]]:
    """Use KDE + peak-finding to identify natural price clusters."""
    if len(prices) < 5:
        return _simple_cluster_detection(prices)
    price_range = float(prices.max() - prices.min())
    if price_range == 0:
        return [{"center": float(prices[0]), "count": int(len(prices)), "pct": 100.0, "radius": 0.0}]
    std = float(np.std(prices))
    if std <= 0:
        return _simple_cluster_detection(prices)

    bandwidth = max(price_range * bandwidth_factor, 1.0)
    kde = gaussian_kde(prices, bw_method=bandwidth / std)
    grid = np.linspace(float(prices.min()) - 10.0, float(prices.max()) + 10.0, 500)
    density = kde(grid)
    peaks, _ = find_peaks(density, height=float(np.max(density)) * 0.1, distance=int(500 * 0.05))

    clusters: list[dict[str, Any]] = []
    for peak_idx in peaks:
        center = float(grid[peak_idx])
        radius = max(center * 0.15, 10.0)
        count = int(np.sum((prices >= center - radius) & (prices <= center + radius)))
        clusters.append(
            {
                "center": round(center, 0),
                "count": count,
                "pct": round(count / len(prices) * 100, 1),
                "radius": round(radius, 0),
            }
        )
    clusters.sort(key=lambda cluster: cluster["count"], reverse=True)
    return clusters


def _simple_cluster_detection(prices: np.ndarray) -> list[dict[str, Any]]:
    """Fallback clustering for sparse samples."""
    if len(prices) == 0:
        return []
    rounded = np.round(prices / 25.0) * 25.0
    unique, counts = np.unique(rounded, return_counts=True)
    clusters = [
        {
            "center": float(center),
            "count": int(count),
            "pct": round(int(count) / len(prices) * 100, 1),
        }
        for center, count in zip(unique, counts, strict=False)
    ]
    clusters.sort(key=lambda cluster: cluster["count"], reverse=True)
    return clusters


def detect_price_gaps(prices: np.ndarray, min_gap_pct: float = 0.20) -> list[dict[str, Any]]:
    """Identify significant empty price bands between sorted prices."""
    if len(prices) < 3:
        return []
    sorted_prices = np.sort(prices)
    price_range = float(sorted_prices[-1] - sorted_prices[0])
    if price_range == 0:
        return []
    min_gap_size = price_range * min_gap_pct
    gaps: list[dict[str, Any]] = []
    for idx in range(len(sorted_prices) - 1):
        gap_size = float(sorted_prices[idx + 1] - sorted_prices[idx])
        if gap_size >= min_gap_size and gap_size > 10.0:
            start = float(sorted_prices[idx])
            end = float(sorted_prices[idx + 1])
            gaps.append(
                {
                    "gap_start": start,
                    "gap_end": end,
                    "gap_width": gap_size,
                    "gap_midpoint": (start + end) / 2.0,
                    "pct_of_range": round(gap_size / price_range * 100, 1),
                }
            )
    gaps.sort(key=lambda gap: gap["gap_width"], reverse=True)
    return gaps


def calculate_price_review_correlation(keyword_id: int, db: Any) -> dict[str, Any]:
    """Calculate relationship between basic-tier price and review count."""
    gigs = get_gigs_for_keyword(keyword_id, db)
    data_points: list[dict[str, float]] = []
    for gig in gigs:
        basic_price = extract_tier_prices([gig], "basic")
        if not basic_price:
            continue
        review_count = float(
            getattr(gig, "review_count_exact", None)
            or getattr(gig, "review_count", None)
            or 0
        )
        data_points.append({"price": basic_price[0], "reviews": review_count})

    if len(data_points) < 5:
        return {"correlation": None, "n": len(data_points), "interpretation": "insufficient_data"}

    prices = np.array([point["price"] for point in data_points], dtype=float)
    reviews = np.array([point["reviews"] for point in data_points], dtype=float)
    corr, p_value = scipy_stats.pearsonr(prices, reviews)
    spearman_corr, spearman_p = scipy_stats.spearmanr(prices, reviews)

    high_review_prices = prices[reviews > 50]
    low_review_prices = prices[reviews < 10]
    review_premium = float(np.mean(high_review_prices) - np.mean(low_review_prices)) if len(high_review_prices) and len(low_review_prices) else None
    new_seller_prices = prices[reviews < 5]
    new_seller_avg = float(np.mean(new_seller_prices)) if len(new_seller_prices) else None
    market_avg = float(np.mean(prices))

    interpretation = "negative_or_mixed"
    moat_strength = "LOW"
    if abs(corr) < 0.2:
        interpretation = "weak_correlation"
    elif corr > 0.4:
        interpretation = "strong_positive"
        moat_strength = "HIGH"
    elif corr > 0.2:
        interpretation = "moderate_positive"
        moat_strength = "MEDIUM"

    return {
        "pearson_correlation": round(float(corr), 3),
        "pearson_p_value": round(float(p_value), 4),
        "spearman_correlation": round(float(spearman_corr), 3),
        "spearman_p_value": round(float(spearman_p), 4),
        "n": len(data_points),
        "interpretation": interpretation,
        "moat_strength": moat_strength,
        "review_premium_usd": round(review_premium, 2) if review_premium is not None else None,
        "new_seller_avg_price": round(new_seller_avg, 2) if new_seller_avg is not None else None,
        "market_avg_price": round(market_avg, 2),
        "new_seller_discount_pct": round((1 - new_seller_avg / market_avg) * 100, 1) if new_seller_avg is not None and market_avg > 0 else None,
    }


def analyze_price_dispersion(distribution: PriceDistribution) -> dict[str, Any]:
    """Classify market structure by coefficient of variation."""
    cv = distribution.coefficient_of_variation
    if cv < 0.15:
        market_type = "COMMODITY"
    elif cv < 0.30:
        market_type = "MODERATE_SPREAD"
    elif cv < 0.50:
        market_type = "WIDE_SPREAD"
    else:
        market_type = "FRAGMENTED"
    return {
        "market_type": market_type,
        "coefficient_of_variation": round(cv, 3),
        "price_range_ratio": round(distribution.max_price / distribution.min_price, 1) if distribution.min_price > 0 else None,
        "iqr_as_pct_of_median": round(distribution.iqr / distribution.median_price * 100, 1) if distribution.median_price > 0 else None,
    }


def extract_extras_pricing(gigs: list[Any]) -> dict[str, Any]:
    """Extract and summarize gig extras pricing distribution."""
    all_extras_prices: list[float] = []
    all_extras_counts: list[int] = []
    for gig in gigs:
        extras = getattr(gig, "gig_extras", None) or []
        if isinstance(extras, str):
            try:
                extras = json.loads(extras)
            except json.JSONDecodeError:
                extras = []
        prices = [
            price
            for price in (
                _to_positive_float(extra.get("price")) if isinstance(extra, dict) else None
                for extra in (extras if isinstance(extras, list) else [])
            )
            if price is not None
        ]
        all_extras_prices.extend(prices)
        all_extras_counts.append(len(prices))
    if not all_extras_prices:
        return {"min": None, "max": None, "median": None, "avg_count": 0.0}
    arr = np.array(all_extras_prices, dtype=float)
    return {
        "min": float(arr.min()),
        "max": float(arr.max()),
        "median": float(np.median(arr)),
        "avg_count": float(np.mean(all_extras_counts)) if all_extras_counts else 0.0,
    }


def analyze_price_distribution(keyword_id: int, db: Any) -> dict[str, PriceDistribution]:
    """Compute per-tier pricing distribution statistics for one keyword."""
    gigs = get_gigs_for_keyword(keyword_id, db)
    results: dict[str, PriceDistribution] = {}
    for tier in ("basic", "standard", "premium"):
        prices = extract_tier_prices(gigs, tier)
        if len(prices) < 3:
            continue
        prices_arr = np.array(prices, dtype=float)
        mode_result = scipy_stats.mode(prices_arr, keepdims=False)
        std_dev = float(np.std(prices_arr, ddof=1))
        mean_price = float(np.mean(prices_arr))
        results[tier] = PriceDistribution(
            n_gigs=len(prices),
            min_price=float(np.min(prices_arr)),
            max_price=float(np.max(prices_arr)),
            mean_price=mean_price,
            median_price=float(np.median(prices_arr)),
            mode_price=float(mode_result.mode),
            std_dev=std_dev,
            q1=float(np.percentile(prices_arr, 25)),
            q3=float(np.percentile(prices_arr, 75)),
            iqr=float(np.percentile(prices_arr, 75) - np.percentile(prices_arr, 25)),
            p10=float(np.percentile(prices_arr, 10)),
            p90=float(np.percentile(prices_arr, 90)),
            skewness=float(scipy_stats.skew(prices_arr)),
            price_clusters=detect_price_clusters(prices_arr),
            price_gaps=detect_price_gaps(prices_arr),
            coefficient_of_variation=float(std_dev / mean_price) if mean_price > 0 else 0.0,
        )
    return results


def analyze_niche_pricing(niche_id: str, db: Any) -> dict[str, Any]:
    """Aggregate pricing distributions across all keywords in a niche."""
    keywords = get_keywords_for_niche(niche_id, db)
    if not keywords:
        return {}

    tier_prices: dict[str, list[float]] = {"basic": [], "standard": [], "premium": []}
    all_correlations: list[float] = []
    for keyword in keywords:
        keyword_gigs = get_gigs_for_keyword(int(keyword.id), db)
        for tier in ("basic", "standard", "premium"):
            tier_prices[tier].extend(extract_tier_prices(keyword_gigs, tier))
        corr = calculate_price_review_correlation(int(keyword.id), db)
        if corr.get("pearson_correlation") is not None:
            all_correlations.append(float(corr["pearson_correlation"]))

    niche_summary: dict[str, Any] = {
        "niche_id": niche_id,
        "niche_name": get_niche_name(niche_id, db),
        "keywords_analyzed": len(keywords),
    }
    for tier, prices in tier_prices.items():
        if not prices:
            continue
        arr = np.array(prices, dtype=float)
        niche_summary[f"{tier}_median"] = float(np.median(arr))
        niche_summary[f"{tier}_mean"] = float(np.mean(arr))
        niche_summary[f"{tier}_p25"] = float(np.percentile(arr, 25))
        niche_summary[f"{tier}_p75"] = float(np.percentile(arr, 75))
        niche_summary[f"{tier}_n"] = len(prices)

    if all_correlations:
        avg_corr = float(np.mean(all_correlations))
        niche_summary["avg_price_review_correlation"] = round(avg_corr, 3)
        niche_summary["moat_strength"] = "HIGH" if avg_corr > 0.4 else "MEDIUM" if avg_corr > 0.2 else "LOW"
    return niche_summary


def run_price_distribution_analysis(raw: RawPriceData, db: Any) -> PriceAnalysis:
    """Compatibility wrapper that persists a `PriceAnalysis` row."""
    basic = _distribution_from_prices(raw.basic_prices)
    standard = _distribution_from_prices(raw.standard_prices)
    premium = _distribution_from_prices(raw.premium_prices)
    moat_strength = _classify_moat_strength(raw)
    review_premium = _calculate_review_premium(raw)
    corr = _legacy_correlation(raw)
    market_type = analyze_price_dispersion(basic)["market_type"] if basic is not None else "UNKNOWN"
    niche_id = _resolve_keyword_niche_id(raw.keyword_id, db)
    row = PriceAnalysis(
        keyword_id=raw.keyword_id,
        niche_id=niche_id,
        run_id=raw.run_id,
        market_type=market_type,
        moat_strength=moat_strength,
        review_premium_usd=review_premium,
        price_review_correlation=corr,
    )
    _apply_distribution_to_row(row, "basic", basic)
    _apply_distribution_to_row(row, "standard", standard)
    _apply_distribution_to_row(row, "premium", premium)
    if isinstance(db, Session):
        db.add(row)
        db.flush()
    return row


def extract_raw_price_data_from_db(keyword_id: int, run_id: str, db: Any) -> RawPriceData | None:
    """Build legacy raw payload from persisted gigs for one keyword."""
    gigs = get_gigs_for_keyword(keyword_id, db)
    if not gigs:
        return None
    basic = extract_tier_prices(gigs, "basic")
    standard = extract_tier_prices(gigs, "standard")
    premium = extract_tier_prices(gigs, "premium")
    if not basic and not standard and not premium:
        return None
    seller_reviews = [
        int(getattr(gig, "review_count_exact", None) or getattr(gig, "review_count", None) or 0)
        for gig in gigs
        if extract_tier_prices([gig], "basic")
    ]
    return RawPriceData(
        keyword_id=keyword_id,
        run_id=run_id,
        basic_prices=basic,
        standard_prices=standard,
        premium_prices=premium,
        seller_review_counts=seller_reviews,
        seller_levels=["UNKNOWN"] * len(seller_reviews),
    )


def persist_keyword_pricing(keyword_id: int, run_id: str, db: Any) -> tuple[PriceAnalysis | None, PricingSnapshot | None]:
    """Persist `PriceAnalysis` row for keyword and return placeholder snapshot slot."""
    distributions = analyze_price_distribution(keyword_id, db)
    if "basic" not in distributions:
        return None, None
    niche_id = _resolve_keyword_niche_id(keyword_id, db)
    corr = calculate_price_review_correlation(keyword_id, db)
    dispersion = analyze_price_dispersion(distributions["basic"])
    extras = extract_extras_pricing(get_gigs_for_keyword(keyword_id, db))
    row = PriceAnalysis(
        keyword_id=keyword_id,
        niche_id=niche_id,
        run_id=run_id,
        price_review_correlation=corr.get("pearson_correlation"),
        moat_strength=corr.get("moat_strength"),
        review_premium_usd=corr.get("review_premium_usd"),
        new_seller_avg_price=corr.get("new_seller_avg_price"),
        new_seller_discount_pct=corr.get("new_seller_discount_pct"),
        market_type=dispersion.get("market_type"),
        avg_extras_count=extras.get("avg_count"),
        avg_extras_price=extras.get("median"),
        extras_price_range=extras,
    )
    for tier_name, distribution in distributions.items():
        _apply_distribution_to_row(row, tier_name, distribution)
    if isinstance(db, Session):
        db.add(row)
        db.flush()
    _persist_niche_aggregate(niche_id=niche_id, run_id=run_id, db=db)
    return row, None


def get_keywords_for_niche(niche_id: str, db: Any) -> list[Keyword]:
    """Return keywords mapped to niche slug or numeric ID."""
    if not isinstance(db, Session):
        return []
    if str(niche_id).isdigit():
        return db.query(Keyword).filter(Keyword.niche_id == int(niche_id)).all()
    niche = db.query(Niche).filter(Niche.slug == niche_id).first()
    if niche is None:
        return []
    return db.query(Keyword).filter(Keyword.niche_id == niche.id).all()


def get_niche_name(niche_id: str, db: Any) -> str:
    """Resolve user-facing niche name."""
    if not isinstance(db, Session):
        return str(niche_id)
    niche = None
    if str(niche_id).isdigit():
        niche = db.query(Niche).filter(Niche.id == int(niche_id)).first()
    else:
        niche = db.query(Niche).filter(Niche.slug == niche_id).first()
    return niche.name if niche is not None else str(niche_id)


def _distribution_from_prices(prices: list[float]) -> PriceDistribution | None:
    if len(prices) < 3:
        return None
    arr = np.array(prices, dtype=float)
    mode_result = scipy_stats.mode(arr, keepdims=False)
    std_dev = float(np.std(arr, ddof=1))
    mean_price = float(np.mean(arr))
    return PriceDistribution(
        n_gigs=len(prices),
        min_price=float(np.min(arr)),
        max_price=float(np.max(arr)),
        mean_price=mean_price,
        median_price=float(np.median(arr)),
        mode_price=float(mode_result.mode),
        std_dev=std_dev,
        q1=float(np.percentile(arr, 25)),
        q3=float(np.percentile(arr, 75)),
        iqr=float(np.percentile(arr, 75) - np.percentile(arr, 25)),
        p10=float(np.percentile(arr, 10)),
        p90=float(np.percentile(arr, 90)),
        skewness=float(scipy_stats.skew(arr)),
        price_clusters=detect_price_clusters(arr),
        price_gaps=detect_price_gaps(arr),
        coefficient_of_variation=float(std_dev / mean_price) if mean_price > 0 else 0.0,
    )


def _apply_distribution_to_row(row: PriceAnalysis, tier: str, distribution: PriceDistribution | None) -> None:
    if distribution is None:
        return
    setattr(row, f"{tier}_n", distribution.n_gigs)
    setattr(row, f"{tier}_min", distribution.min_price)
    setattr(row, f"{tier}_max", distribution.max_price)
    setattr(row, f"{tier}_median", distribution.median_price)
    setattr(row, f"{tier}_mean", distribution.mean_price)
    setattr(row, f"{tier}_mode", distribution.mode_price)
    setattr(row, f"{tier}_std", distribution.std_dev)
    setattr(row, f"{tier}_q1", distribution.q1)
    setattr(row, f"{tier}_q3", distribution.q3)
    setattr(row, f"{tier}_p10", distribution.p10)
    setattr(row, f"{tier}_p90", distribution.p90)
    setattr(row, f"{tier}_skewness", distribution.skewness)
    setattr(row, f"{tier}_cv", distribution.coefficient_of_variation)
    setattr(row, f"{tier}_clusters", distribution.price_clusters)
    setattr(row, f"{tier}_gaps", distribution.price_gaps)


def _persist_niche_aggregate(niche_id: str, run_id: str, db: Any) -> None:
    summary = analyze_niche_pricing(niche_id, db)
    if not summary or not isinstance(db, Session):
        return
    row = db.query(NichePriceAnalysis).filter(NichePriceAnalysis.niche_id == niche_id).first()
    if row is None:
        row = NichePriceAnalysis(niche_id=niche_id, run_id=run_id)
    row.run_id = run_id
    row.keywords_analyzed = summary.get("keywords_analyzed")
    row.basic_median = summary.get("basic_median")
    row.basic_mean = summary.get("basic_mean")
    row.basic_p25 = summary.get("basic_p25")
    row.basic_p75 = summary.get("basic_p75")
    row.standard_median = summary.get("standard_median")
    row.standard_mean = summary.get("standard_mean")
    row.standard_p25 = summary.get("standard_p25")
    row.standard_p75 = summary.get("standard_p75")
    row.premium_median = summary.get("premium_median")
    row.premium_mean = summary.get("premium_mean")
    row.premium_p25 = summary.get("premium_p25")
    row.premium_p75 = summary.get("premium_p75")
    row.avg_price_review_correlation = summary.get("avg_price_review_correlation")
    row.moat_strength = summary.get("moat_strength")
    db.add(row)


def _legacy_correlation(raw: RawPriceData) -> float | None:
    if len(raw.basic_prices) < 5 or len(raw.seller_review_counts) < 5:
        return None
    prices = np.array(raw.basic_prices[: len(raw.seller_review_counts)], dtype=float)
    reviews = np.array(raw.seller_review_counts[: len(prices)], dtype=float)
    corr, _ = scipy_stats.pearsonr(prices, reviews)
    return float(round(corr, 3))


def _classify_moat_strength(raw: RawPriceData) -> str:
    if not raw.basic_prices or not raw.seller_review_counts:
        return "LOW"
    established = [price for price, reviews in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if reviews >= 50]
    newbies = [price for price, reviews in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if reviews < 5]
    if not established or not newbies:
        return "LOW"
    premium = float(np.mean(established) - np.mean(newbies))
    if premium > 50:
        return "HIGH"
    if premium > 20:
        return "MEDIUM"
    return "LOW"


def _calculate_review_premium(raw: RawPriceData) -> float | None:
    if not raw.basic_prices or not raw.seller_review_counts:
        return None
    established = [price for price, reviews in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if reviews >= 50]
    newbies = [price for price, reviews in zip(raw.basic_prices, raw.seller_review_counts, strict=False) if reviews < 5]
    if not established or not newbies:
        return None
    return round(float(np.mean(established) - np.mean(newbies)), 2)


def _resolve_keyword_niche_id(keyword_id: int, db: Any) -> str:
    if not isinstance(db, Session):
        return "unknown"
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if keyword is None:
        return "unknown"
    niche = db.query(Niche).filter(Niche.id == keyword.niche_id).first()
    if niche is not None and niche.slug:
        return str(niche.slug)
    return str(keyword.niche_id)


def _to_positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _compute_tier_stats(prices: list[float]) -> dict[str, float | int | None]:
    """Backward-compatible tier statistics helper."""
    if not prices:
        return {k: None for k in ("n", "min", "max", "median", "mean", "cv", "skewness")}
    distribution = _distribution_from_prices(prices)
    if distribution is None:
        return {k: None for k in ("n", "min", "max", "median", "mean", "cv", "skewness")}
    return {
        "n": distribution.n_gigs,
        "min": distribution.min_price,
        "max": distribution.max_price,
        "median": distribution.median_price,
        "mean": distribution.mean_price,
        "cv": distribution.coefficient_of_variation,
        "skewness": distribution.skewness,
    }


def _find_price_gaps(prices: list[float]) -> list[dict[str, Any]]:
    """Backward-compatible gap detector."""
    return detect_price_gaps(np.array(prices, dtype=float), min_gap_pct=0.20)


def _price_from_package(pkg: Any) -> float | None:
    """Backward-compatible single-package price extraction."""
    if not isinstance(pkg, dict):
        return None
    return _to_positive_float(pkg.get("price"))


def _extract_tier_prices(gig: Any) -> tuple[float | None, float | None, float | None]:
    """Backward-compatible single-gig package extraction."""
    basic = _to_positive_float(getattr(gig, "starting_price", None))
    packages = getattr(gig, "packages", None)
    if packages is None:
        metadata = getattr(gig, "metadata_json", None)
        if isinstance(metadata, dict):
            packages = metadata.get("packages")
    if isinstance(packages, str):
        try:
            packages = json.loads(packages)
        except json.JSONDecodeError:
            packages = None
    if isinstance(packages, dict):
        basic = _price_from_package(packages.get("basic")) or basic
        standard = _price_from_package(packages.get("standard"))
        premium = _price_from_package(packages.get("premium"))
        return basic, standard, premium
    if isinstance(packages, list):
        basic = _price_from_package(packages[0]) or basic if len(packages) > 0 else basic
        standard = _price_from_package(packages[1]) if len(packages) > 1 else None
        premium = _price_from_package(packages[2]) if len(packages) > 2 else None
        return basic, standard, premium
    return basic, None, None
