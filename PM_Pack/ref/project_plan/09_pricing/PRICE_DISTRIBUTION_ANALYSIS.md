# Price Distribution Analysis
# Fiverr Research System — Wave 9

**Document Status:** Complete
**Wave:** 9 — Pricing Strategy Engine
**Purpose:** Competitor price distribution curves, quartile analysis, price clustering, price-to-review correlation, price gap detection, and statistical summary per keyword and niche.

---

## Design Goals

1. Map the complete pricing landscape for every keyword — not just averages, but the full distribution shape
2. Identify natural price clusters where sellers congregate and empty price bands where no one competes
3. Quantify the relationship between price and review count (the "review moat" premium)
4. Give the pricing model (9B) the statistical foundation it needs to recommend optimal entry prices
5. All analysis runs automatically as Stage 10.5 (between scoring and opportunity ranking)

---

## Data Sources

All pricing data comes from fields already collected in Stage 4 (Gig Detail Scrape):

| Field | Source Table | Column |
|---|---|---|
| Basic price | gigs | packages → basic.price |
| Standard price | gigs | packages → standard.price |
| Premium price | gigs | packages → premium.price |
| Gig extras | gigs | gig_extras → [{name, price}] |
| Seller level | sellers | seller_level |
| Review count | gigs | detail_review_count |
| Rating | gigs | rating |
| Orders in queue | gigs | orders_in_queue (optional) |
| Keyword association | keyword_gig_associations | keyword_id → gig_id |

No new collection is required. This is a pure analysis stage.

---

## Stage 10.5 — Price Distribution Analysis

Inserted between Stage 10 (Scoring) and Stage 11 (Opportunity Ranking):

```
Stage 10: Scoring (all 11 scores calculated)
    │
    ▼
Stage 10.5: Price Distribution Analysis (NEW)
    │
    ├── For each keyword with ≥ 3 gigs collected:
    │   ├── Extract all package prices (Basic/Standard/Premium)
    │   ├── Calculate distribution statistics
    │   ├── Detect price clusters (KDE peak finding)
    │   ├── Identify price gaps (empty bands)
    │   ├── Compute price-to-review correlation
    │   └── Store in price_analysis table
    │
    ├── For each niche (aggregate across keywords):
    │   ├── Niche-level price distribution
    │   ├── Cross-keyword price comparison
    │   └── Store in niche_price_analysis table
    │
    ▼
Stage 11: Opportunity Ranking
```

---

## Price Distribution Statistics — Per Keyword

```python
# src/analysis/price_distribution.py

import numpy as np
from scipy import stats as scipy_stats
from dataclasses import dataclass

@dataclass
class PriceDistribution:
    """Statistical summary of prices for one keyword at one tier."""
    tier: str  # "basic", "standard", "premium"
    n_gigs: int
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    mode_price: float
    std_dev: float
    q1: float  # 25th percentile
    q3: float  # 75th percentile
    iqr: float  # Interquartile range
    p10: float  # 10th percentile
    p90: float  # 90th percentile
    skewness: float  # Positive = right-skewed (most sellers price low)
    price_clusters: list[dict]  # [{center, count, pct}]
    price_gaps: list[dict]  # [{gap_start, gap_end, gap_width}]
    coefficient_of_variation: float  # std_dev / mean — measures price dispersion


def analyze_price_distribution(
    keyword_id: int,
    db,
) -> dict[str, PriceDistribution]:
    """
    Computes price distribution statistics for a single keyword across all 3 tiers.
    Returns dict keyed by tier name.
    """
    gigs = get_gigs_for_keyword(keyword_id, db)

    results = {}
    for tier in ["basic", "standard", "premium"]:
        prices = extract_tier_prices(gigs, tier)
        if len(prices) < 3:
            continue  # Need at least 3 data points for meaningful stats

        prices_arr = np.array(prices, dtype=float)

        # Core statistics
        dist = PriceDistribution(
            tier=tier,
            n_gigs=len(prices),
            min_price=float(np.min(prices_arr)),
            max_price=float(np.max(prices_arr)),
            mean_price=float(np.mean(prices_arr)),
            median_price=float(np.median(prices_arr)),
            mode_price=float(scipy_stats.mode(prices_arr, keepdims=False).mode),
            std_dev=float(np.std(prices_arr, ddof=1)),
            q1=float(np.percentile(prices_arr, 25)),
            q3=float(np.percentile(prices_arr, 75)),
            iqr=float(np.percentile(prices_arr, 75) - np.percentile(prices_arr, 25)),
            p10=float(np.percentile(prices_arr, 10)),
            p90=float(np.percentile(prices_arr, 90)),
            skewness=float(scipy_stats.skew(prices_arr)),
            price_clusters=detect_price_clusters(prices_arr),
            price_gaps=detect_price_gaps(prices_arr),
            coefficient_of_variation=(
                float(np.std(prices_arr, ddof=1) / np.mean(prices_arr))
                if np.mean(prices_arr) > 0 else 0.0
            ),
        )
        results[tier] = dist

    return results


def extract_tier_prices(gigs: list, tier: str) -> list[float]:
    """Extracts all prices for a specific tier from gig packages."""
    prices = []
    for gig in gigs:
        if not gig.packages:
            continue
        # packages is stored as JSON — could be list of dicts or dict with tier keys
        if isinstance(gig.packages, dict):
            tier_data = gig.packages.get(tier, {})
            price = tier_data.get("price", 0)
        elif isinstance(gig.packages, list):
            # Ordered: [basic, standard, premium]
            tier_index = {"basic": 0, "standard": 1, "premium": 2}.get(tier, 0)
            if tier_index < len(gig.packages):
                price = gig.packages[tier_index].get("price", 0)
            else:
                price = 0
        else:
            price = 0

        if price and price > 0:
            prices.append(float(price))
    return prices
```

---

## Price Cluster Detection

Natural price points where sellers congregate (e.g., $50, $100, $150, $200, $250):

```python
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde

def detect_price_clusters(prices: np.ndarray, bandwidth_factor: float = 0.15) -> list[dict]:
    """
    Uses Kernel Density Estimation (KDE) to find natural price clusters.
    Returns list of cluster centers with count and percentage.
    """
    if len(prices) < 5:
        # Not enough data for KDE — fall back to simple rounding
        return _simple_cluster_detection(prices)

    # Create KDE
    price_range = prices.max() - prices.min()
    if price_range == 0:
        return [{"center": float(prices[0]), "count": len(prices), "pct": 100.0}]

    bandwidth = price_range * bandwidth_factor
    kde = gaussian_kde(prices, bw_method=bandwidth / prices.std())

    # Evaluate KDE on a fine grid
    grid = np.linspace(prices.min() - 10, prices.max() + 10, 500)
    density = kde(grid)

    # Find peaks in the density
    peaks, properties = find_peaks(density, height=density.max() * 0.1,
                                    distance=int(500 * 0.05))

    clusters = []
    for peak_idx in peaks:
        center = float(grid[peak_idx])
        # Count prices within ±15% of center (or ±$10, whichever is larger)
        radius = max(center * 0.15, 10.0)
        count = int(np.sum((prices >= center - radius) & (prices <= center + radius)))
        pct = round(count / len(prices) * 100, 1)
        clusters.append({
            "center": round(center, 0),
            "count": count,
            "pct": pct,
            "radius": round(radius, 0),
        })

    # Sort by count descending
    clusters.sort(key=lambda c: c["count"], reverse=True)
    return clusters


def _simple_cluster_detection(prices: np.ndarray) -> list[dict]:
    """Fallback for small sample sizes — round to nearest $25 and count."""
    rounded = np.round(prices / 25) * 25
    unique, counts = np.unique(rounded, return_counts=True)
    clusters = []
    for center, count in sorted(zip(unique, counts), key=lambda x: -x[1]):
        clusters.append({
            "center": float(center),
            "count": int(count),
            "pct": round(int(count) / len(prices) * 100, 1),
        })
    return clusters
```

---

## Price Gap Detection

Empty price bands where no sellers are competing — potential positioning opportunities:

```python
def detect_price_gaps(prices: np.ndarray, min_gap_pct: float = 0.20) -> list[dict]:
    """
    Identifies empty price bands between sorted prices.
    A gap is significant if it represents > min_gap_pct of the price range.
    """
    if len(prices) < 3:
        return []

    sorted_prices = np.sort(prices)
    price_range = sorted_prices[-1] - sorted_prices[0]
    if price_range == 0:
        return []

    min_gap_size = price_range * min_gap_pct

    gaps = []
    for i in range(len(sorted_prices) - 1):
        gap_size = sorted_prices[i + 1] - sorted_prices[i]
        if gap_size >= min_gap_size:
            gaps.append({
                "gap_start": float(sorted_prices[i]),
                "gap_end": float(sorted_prices[i + 1]),
                "gap_width": float(gap_size),
                "gap_midpoint": float((sorted_prices[i] + sorted_prices[i + 1]) / 2),
                "pct_of_range": round(gap_size / price_range * 100, 1),
            })

    # Sort by gap width descending
    gaps.sort(key=lambda g: g["gap_width"], reverse=True)
    return gaps
```

---

## Price-to-Review Correlation (The "Review Moat" Premium)

Quantifies how much established sellers can charge MORE because they have reviews:

```python
def calculate_price_review_correlation(
    keyword_id: int,
    db,
) -> dict:
    """
    Calculates the correlation between price and review count.
    High positive correlation = strong review moat (established sellers charge more).
    Low/no correlation = price not tied to reviews (new sellers can compete on price).
    """
    gigs = get_gigs_for_keyword(keyword_id, db)

    data_points = []
    for gig in gigs:
        review_count = gig.detail_review_count or gig.search_review_count or 0
        basic_price = extract_tier_prices([gig], "basic")
        if basic_price:
            data_points.append({"price": basic_price[0], "reviews": review_count})

    if len(data_points) < 5:
        return {"correlation": None, "n": len(data_points), "interpretation": "insufficient_data"}

    prices = np.array([d["price"] for d in data_points])
    reviews = np.array([d["reviews"] for d in data_points])

    # Pearson correlation
    corr, p_value = scipy_stats.pearsonr(prices, reviews)

    # Spearman rank correlation (more robust to outliers)
    spearman_corr, spearman_p = scipy_stats.spearmanr(prices, reviews)

    # Price premium analysis: average price for sellers with >50 reviews vs <10 reviews
    high_review_prices = prices[reviews > 50]
    low_review_prices = prices[reviews < 10]
    review_premium = None
    if len(high_review_prices) > 0 and len(low_review_prices) > 0:
        review_premium = float(np.mean(high_review_prices) - np.mean(low_review_prices))

    # New seller price position analysis
    new_seller_prices = prices[reviews < 5]
    new_seller_avg = float(np.mean(new_seller_prices)) if len(new_seller_prices) > 0 else None
    market_avg = float(np.mean(prices))

    # Interpretation
    if abs(corr) < 0.2:
        interpretation = "weak_correlation"
        moat_strength = "LOW"
        # New sellers can compete at similar prices — reviews don't command a premium
    elif corr > 0.4:
        interpretation = "strong_positive"
        moat_strength = "HIGH"
        # Established sellers charge significantly more — new sellers must undercut
    elif corr > 0.2:
        interpretation = "moderate_positive"
        moat_strength = "MEDIUM"
    else:
        interpretation = "negative_or_mixed"
        moat_strength = "LOW"

    return {
        "pearson_correlation": round(corr, 3),
        "pearson_p_value": round(p_value, 4),
        "spearman_correlation": round(spearman_corr, 3),
        "spearman_p_value": round(spearman_p, 4),
        "n": len(data_points),
        "interpretation": interpretation,
        "moat_strength": moat_strength,
        "review_premium_usd": round(review_premium, 2) if review_premium else None,
        "new_seller_avg_price": round(new_seller_avg, 2) if new_seller_avg else None,
        "market_avg_price": round(market_avg, 2),
        "new_seller_discount_pct": (
            round((1 - new_seller_avg / market_avg) * 100, 1)
            if new_seller_avg and market_avg > 0 else None
        ),
    }
```

---

## Price Dispersion Analysis

How spread out are prices? High dispersion = room for differentiated positioning. Low dispersion = commodity market with tight pricing.

```python
def analyze_price_dispersion(distribution: PriceDistribution) -> dict:
    """
    Classifies the pricing market structure based on statistical dispersion.
    """
    cv = distribution.coefficient_of_variation

    if cv < 0.15:
        market_type = "COMMODITY"
        description = ("Prices are tightly clustered — this is a commodity market. "
                       "Competing on price alone is a race to the bottom. "
                       "Differentiate on deliverables and proof elements instead.")
    elif cv < 0.30:
        market_type = "MODERATE_SPREAD"
        description = ("Moderate price variation — room for differentiated positioning. "
                       "Premium sellers charge 2-3x the lowest price. "
                       "New sellers can enter at the lower end with a clear upgrade path.")
    elif cv < 0.50:
        market_type = "WIDE_SPREAD"
        description = ("Wide price range — the market has distinct price tiers. "
                       "New sellers should identify which tier to target: "
                       "budget (speed/simplicity), mid-market (quality/reliability), "
                       "or premium (expertise/proof).")
    else:
        market_type = "FRAGMENTED"
        description = ("Highly fragmented pricing — sellers range from very cheap to very expensive. "
                       "This usually indicates unclear buyer expectations. "
                       "Opportunity: set clear scope/pricing that anchors buyer expectations.")

    return {
        "market_type": market_type,
        "coefficient_of_variation": round(cv, 3),
        "description": description,
        "price_range_ratio": (
            round(distribution.max_price / distribution.min_price, 1)
            if distribution.min_price > 0 else None
        ),
        "iqr_as_pct_of_median": (
            round(distribution.iqr / distribution.median_price * 100, 1)
            if distribution.median_price > 0 else None
        ),
    }
```

---

## Niche-Level Aggregation

Aggregate price analysis across all keywords in a niche:

```python
def analyze_niche_pricing(niche_id: str, db) -> dict:
    """
    Aggregates price distribution data across all keywords in a niche.
    """
    keywords = get_keywords_for_niche(niche_id, db)
    all_basic_prices = []
    all_standard_prices = []
    all_premium_prices = []
    all_correlations = []

    for keyword in keywords:
        distributions = analyze_price_distribution(keyword.id, db)
        if "basic" in distributions:
            all_basic_prices.extend(
                extract_tier_prices(get_gigs_for_keyword(keyword.id, db), "basic")
            )
        if "standard" in distributions:
            all_standard_prices.extend(
                extract_tier_prices(get_gigs_for_keyword(keyword.id, db), "standard")
            )
        if "premium" in distributions:
            all_premium_prices.extend(
                extract_tier_prices(get_gigs_for_keyword(keyword.id, db), "premium")
            )

        corr = calculate_price_review_correlation(keyword.id, db)
        if corr.get("pearson_correlation") is not None:
            all_correlations.append(corr["pearson_correlation"])

    niche_summary = {
        "niche_id": niche_id,
        "niche_name": get_niche_name(niche_id),
        "keywords_analyzed": len(keywords),
    }

    for tier, prices in [("basic", all_basic_prices), ("standard", all_standard_prices),
                          ("premium", all_premium_prices)]:
        if prices:
            arr = np.array(prices)
            niche_summary[f"{tier}_median"] = float(np.median(arr))
            niche_summary[f"{tier}_mean"] = float(np.mean(arr))
            niche_summary[f"{tier}_p25"] = float(np.percentile(arr, 25))
            niche_summary[f"{tier}_p75"] = float(np.percentile(arr, 75))
            niche_summary[f"{tier}_min"] = float(np.min(arr))
            niche_summary[f"{tier}_max"] = float(np.max(arr))
            niche_summary[f"{tier}_n"] = len(prices)

    if all_correlations:
        niche_summary["avg_price_review_correlation"] = round(
            float(np.mean(all_correlations)), 3
        )
        niche_summary["moat_strength"] = (
            "HIGH" if niche_summary["avg_price_review_correlation"] > 0.4
            else "MEDIUM" if niche_summary["avg_price_review_correlation"] > 0.2
            else "LOW"
        )

    return niche_summary
```

---

## Storage Schema

```python
# Added to SCHEMA.md — new tables

class PriceAnalysis(Base):
    """Per-keyword price distribution analysis."""
    __tablename__ = "price_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)

    # Basic tier stats
    basic_n = Column(Integer)
    basic_median = Column(Float)
    basic_mean = Column(Float)
    basic_mode = Column(Float)
    basic_std = Column(Float)
    basic_q1 = Column(Float)
    basic_q3 = Column(Float)
    basic_p10 = Column(Float)
    basic_p90 = Column(Float)
    basic_skewness = Column(Float)
    basic_cv = Column(Float)
    basic_clusters = Column(JSON)  # [{center, count, pct}]
    basic_gaps = Column(JSON)  # [{gap_start, gap_end, gap_width}]

    # Standard tier stats (same fields)
    standard_n = Column(Integer)
    standard_median = Column(Float)
    standard_mean = Column(Float)
    standard_mode = Column(Float)
    standard_std = Column(Float)
    standard_q1 = Column(Float)
    standard_q3 = Column(Float)
    standard_p10 = Column(Float)
    standard_p90 = Column(Float)
    standard_skewness = Column(Float)
    standard_cv = Column(Float)
    standard_clusters = Column(JSON)
    standard_gaps = Column(JSON)

    # Premium tier stats (same fields)
    premium_n = Column(Integer)
    premium_median = Column(Float)
    premium_mean = Column(Float)
    premium_mode = Column(Float)
    premium_std = Column(Float)
    premium_q1 = Column(Float)
    premium_q3 = Column(Float)
    premium_p10 = Column(Float)
    premium_p90 = Column(Float)
    premium_skewness = Column(Float)
    premium_cv = Column(Float)
    premium_clusters = Column(JSON)
    premium_gaps = Column(JSON)

    # Cross-tier analysis
    price_review_correlation = Column(Float)
    moat_strength = Column(String)  # HIGH, MEDIUM, LOW
    review_premium_usd = Column(Float)
    new_seller_avg_price = Column(Float)
    new_seller_discount_pct = Column(Float)
    market_type = Column(String)  # COMMODITY, MODERATE_SPREAD, WIDE_SPREAD, FRAGMENTED

    # Extras analysis
    avg_extras_count = Column(Float)
    avg_extras_price = Column(Float)
    extras_price_range = Column(JSON)  # {min, max, median}

    analyzed_at = Column(DateTime, default=datetime.utcnow)


class NichePriceAnalysis(Base):
    """Niche-level aggregate price analysis."""
    __tablename__ = "niche_price_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    niche_id = Column(String, nullable=False, index=True, unique=True)
    run_id = Column(String, nullable=False)

    keywords_analyzed = Column(Integer)
    basic_median = Column(Float)
    basic_mean = Column(Float)
    basic_p25 = Column(Float)
    basic_p75 = Column(Float)
    standard_median = Column(Float)
    standard_mean = Column(Float)
    standard_p25 = Column(Float)
    standard_p75 = Column(Float)
    premium_median = Column(Float)
    premium_mean = Column(Float)
    premium_p25 = Column(Float)
    premium_p75 = Column(Float)
    avg_price_review_correlation = Column(Float)
    moat_strength = Column(String)

    analyzed_at = Column(DateTime, default=datetime.utcnow)
```

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Full analysis on top 20 gigs per keyword |
| standard | Full analysis on top 10 gigs per keyword |
| feasibility | Limited analysis on top 5 gigs (wider confidence intervals) |
| keyword_only | NOT AVAILABLE — no gig data collected |

---

## Example Output

**Keyword:** "AI SaaS PRD" (10 gigs analyzed)

```json
{
  "basic": {
    "n_gigs": 10,
    "min_price": 50.0,
    "max_price": 250.0,
    "mean_price": 127.50,
    "median_price": 100.0,
    "mode_price": 100.0,
    "std_dev": 62.34,
    "q1": 75.0,
    "q3": 175.0,
    "iqr": 100.0,
    "skewness": 0.42,
    "coefficient_of_variation": 0.489,
    "price_clusters": [
      {"center": 100, "count": 4, "pct": 40.0},
      {"center": 50, "count": 2, "pct": 20.0},
      {"center": 200, "count": 2, "pct": 20.0}
    ],
    "price_gaps": [
      {"gap_start": 125, "gap_end": 175, "gap_width": 50, "pct_of_range": 25.0}
    ]
  },
  "price_review_correlation": {
    "pearson_correlation": 0.312,
    "moat_strength": "MEDIUM",
    "review_premium_usd": 45.00,
    "new_seller_avg_price": 72.50,
    "market_avg_price": 127.50,
    "new_seller_discount_pct": 43.1
  },
  "market_type": "WIDE_SPREAD"
}
```

Interpretation: The "AI SaaS PRD" market has wide price spread (CV 0.489), with sellers clustering around $100 (40% of sellers). There's a $50 gap between $125–$175 where no sellers compete. New sellers price 43% below market average. The review moat is MEDIUM strength — established sellers charge ~$45 more than new sellers, but it's not insurmountable.
