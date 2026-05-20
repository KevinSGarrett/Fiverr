# Saturation Model
# Fiverr Research System — Wave 5

**Document Status:** Complete
**Wave:** 5 — Analysis and Competitor Model
**Purpose:** Niche-level saturation score formula, saturation signals, title duplication algorithm, price compression detection, LLM saturation classification, and the distinction between Saturation and Competition scores.

---

## Saturation vs. Competition — Key Distinction

These are two different scores measuring two different things:

| | Competition Score | Saturation Score |
|---|---|---|
| **Measures** | How strong the existing sellers are | How commoditized / undifferentiated the offerings are |
| **High score means** | Top sellers have many reviews, are Top Rated / Pro, hard to beat | Many similar gigs with identical titles, price compression, little differentiation |
| **Possible combinations** | High Competition + Low Saturation = Few strong, differentiated sellers (niche market) | Low Competition + High Saturation = Many weak, undifferentiated sellers (commoditized market) |
| **Entry implication** | High competition = need proof and positioning to beat established sellers | High saturation = need differentiation to stand out from a sea of similar gigs |
| **Primary data source** | Seller profiles, review counts, seller levels | Gig titles, pricing patterns, result counts, seller overlap |

---

## Saturation Score Formula (0–100)

The saturation score is calculated at the keyword level and rolled up to the niche level.

```python
# src/analysis/saturation_model.py

def calculate_saturation_score(
    keyword_id: int,
    niche_id: str,
    db,
    niche_context: dict,
) -> float:
    """
    Calculates the Saturation Score for a keyword (0–100).
    Higher = more saturated = harder to stand out.

    Used as Score 7 (inverted) in the Final Recommendation Score.
    """

    search_result = get_latest_search_result(keyword_id, db)
    gig_cards = search_result.gig_cards or []
    top_30_gigs = gig_cards[:30]

    # Component 1: Total gig count (25%)
    total_count = search_result.total_result_count or len(gig_cards)
    niche_median_count = niche_context.get("median_result_count", 500)
    count_score = min(100.0, (total_count / max(1, niche_median_count)) * 50)
    # At 2× median → score 100; at median → score 50; below median → proportionally lower

    # Component 2: Title duplication rate (25%)
    title_dup_rate = calculate_title_duplication_rate(top_30_gigs)
    title_dup_score = title_dup_rate * 100  # 0.0–1.0 → 0–100

    # Component 3: Price compression (20%)
    price_compression = calculate_price_compression(gig_cards, niche_context)
    price_score = price_compression * 100

    # Component 4: Seller portfolio overlap (15%)
    overlap_score = calculate_seller_overlap(keyword_id, niche_id, db) * 100

    # Component 5: LLM saturation classification (15%)
    llm_class_score = get_llm_saturation_score(keyword_id, db)

    saturation_score = (
        count_score      * 0.25 +
        title_dup_score  * 0.25 +
        price_score      * 0.20 +
        overlap_score    * 0.15 +
        llm_class_score  * 0.15
    )
    return round(min(100.0, max(0.0, saturation_score)), 2)
```

---

## Title Duplication Algorithm

Detects near-identical gig titles without requiring LLM — uses token overlap (Jaccard similarity).

```python
import re
from itertools import combinations

# Stop words that should be ignored in title comparison
TITLE_STOP_WORDS = {
    "i", "will", "you", "your", "the", "a", "an", "for", "and",
    "or", "to", "in", "of", "with", "that", "this", "my", "our",
    "create", "make", "build", "write", "provide", "give", "help",
    "professional", "high", "quality", "best", "great", "amazing",
    "excellent", "perfect", "top",
}

def tokenize_title(title: str) -> set[str]:
    """Tokenizes a gig title into a set of meaningful words."""
    words = re.findall(r"\b[a-z]+\b", title.lower())
    return {w for w in words if w not in TITLE_STOP_WORDS and len(w) > 2}

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculates Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union

def calculate_title_duplication_rate(gig_cards: list[dict],
                                      similarity_threshold: float = 0.65) -> float:
    """
    Calculates the proportion of gig titles that are near-duplicates.

    Returns a float 0.0–1.0:
        0.0 = all titles are unique (low saturation)
        1.0 = all titles are near-identical (high saturation)

    Uses pairwise Jaccard similarity — two titles with similarity >= threshold
    are considered near-duplicates.
    """
    if len(gig_cards) < 2:
        return 0.0

    titles = [card.get("gig_title", "") for card in gig_cards if card.get("gig_title")]
    tokenized = [tokenize_title(t) for t in titles]

    duplicate_pairs = set()
    for i, j in combinations(range(len(tokenized)), 2):
        sim = jaccard_similarity(tokenized[i], tokenized[j])
        if sim >= similarity_threshold:
            duplicate_pairs.add(i)
            duplicate_pairs.add(j)

    return len(duplicate_pairs) / max(1, len(titles))
```

**Interpretation:**
- Duplication rate < 0.20 → titles are diverse (differentiated landscape)
- Duplication rate 0.20–0.50 → moderate duplication (some saturation)
- Duplication rate > 0.50 → heavy duplication (commoditized landscape)

---

## Price Compression Detection

Price compression occurs when sellers race to the bottom, compressing the market toward the lowest possible price.

```python
import numpy as np

def calculate_price_compression(gig_cards: list[dict], niche_context: dict) -> float:
    """
    Detects price compression in the search results.
    Returns a float 0.0–1.0 (0 = healthy pricing, 1 = severely compressed).

    Compression signals:
    1. Standard deviation of prices is very low (everyone charges the same)
    2. Median price is declining vs. the niche historical median
    3. Large proportion of gigs are clustered at the absolute lowest price tier
    """
    prices = [
        card.get("starting_price", 0)
        for card in gig_cards
        if card.get("starting_price", 0) > 0
    ]
    if len(prices) < 5:
        return 0.3  # Not enough data — return moderate default

    prices_arr = np.array(prices, dtype=float)
    current_median = float(np.median(prices_arr))
    current_std = float(np.std(prices_arr))

    # Signal 1: Low price diversity (coefficient of variation < 0.3)
    cv = current_std / max(1, current_median)
    low_diversity_score = max(0.0, 1.0 - (cv / 0.5))  # CV of 0.5 → no compression signal

    # Signal 2: Price decline vs. historical niche median
    historical_median = niche_context.get("historical_median_price", current_median)
    if historical_median > 0:
        price_decline_ratio = max(0.0, (historical_median - current_median) / historical_median)
        decline_score = min(1.0, price_decline_ratio * 3)  # 33% decline → score 1.0
    else:
        decline_score = 0.0

    # Signal 3: Proportion of gigs at bottom 25% of price range
    price_min = float(np.min(prices_arr))
    bottom_quartile = np.percentile(prices_arr, 25)
    bottom_clustered = float(np.mean(prices_arr <= bottom_quartile * 1.1))
    bottom_cluster_score = min(1.0, bottom_clustered * 2)

    return float(
        low_diversity_score * 0.40 +
        decline_score       * 0.35 +
        bottom_cluster_score * 0.25
    )
```

---

## Seller Portfolio Overlap

Detects when the same sellers dominate across multiple keywords in the niche, reducing the effective number of independent competitors.

```python
def calculate_seller_overlap(keyword_id: int, niche_id: str, db) -> float:
    """
    Calculates how much seller overlap exists across keywords in this niche.
    High overlap = a small group of sellers dominates the entire niche.
    Returns 0.0–1.0 (0 = all different sellers per keyword, 1 = same sellers everywhere).
    """
    # Get all keywords in this niche
    all_keywords = db.query(Keyword.id).filter(
        Keyword.niche_id == niche_id,
        Keyword.is_active == True
    ).all()
    all_keyword_ids = [k.id for k in all_keywords]

    if len(all_keyword_ids) < 2:
        return 0.0

    # Get top-5 seller sets per keyword
    keyword_seller_sets = {}
    for kid in all_keyword_ids:
        sr = get_latest_search_result(kid, db)
        if sr and sr.gig_cards:
            top5 = [card.get("seller_username", "") for card in sr.gig_cards[:5]]
            keyword_seller_sets[kid] = set(filter(None, top5))

    if len(keyword_seller_sets) < 2:
        return 0.0

    # Calculate pairwise Jaccard overlap between seller sets
    sets = list(keyword_seller_sets.values())
    overlaps = []
    for i, j in combinations(range(len(sets)), 2):
        sim = jaccard_similarity(sets[i], sets[j])
        overlaps.append(sim)

    return float(np.mean(overlaps)) if overlaps else 0.0
```

---

## LLM Saturation Classification (gpt-4o-mini)

The LLM adds qualitative context that the rule-based signals cannot capture.

```
Prompt template: src/llm/prompts/stage09_clustering/saturation_narrative.j2

---
You are analyzing the saturation level of a Fiverr keyword market.

Keyword: {{ keyword_text }}
Niche: {{ niche_name }}
Total search results: {{ total_result_count }}
Title duplication rate: {{ title_dup_rate | round(2) }} (0=unique, 1=identical)
Price compression score: {{ price_compression | round(2) }} (0=healthy, 1=compressed)

Top 10 gig titles:
{% for title in top_10_titles %}
- {{ title }}
{% endfor %}

Classify this market's saturation level and explain why in one sentence.

Return JSON:
{
  "saturation_class": "HIGHLY_DIFFERENTIATED|MODERATELY_DIFFERENTIATED|SATURATED|COMMODITIZED",
  "saturation_score": 0-100,
  "one_sentence_narrative": "string"
}

Scoring guide:
HIGHLY_DIFFERENTIATED (0–25): Titles and approaches vary significantly
MODERATELY_DIFFERENTIATED (26–50): Some differentiation but patterns emerging
SATURATED (51–75): Many similar offerings, price competition visible
COMMODITIZED (76–100): Near-identical titles, extreme price compression, no differentiation
---

Score mapping for saturation_score component:
HIGHLY_DIFFERENTIATED → 10.0
MODERATELY_DIFFERENTIATED → 35.0
SATURATED → 65.0
COMMODITIZED → 90.0

Stored in: keyword_scores.saturation_narrative (one_sentence_narrative)
Model: gpt-4o-mini
Cache: Yes
```

---

## Niche-Level Saturation Rollup

The keyword-level saturation scores are rolled up to a niche-level saturation indicator:

```python
def calculate_niche_saturation(niche_id: str, db) -> dict:
    """
    Aggregates keyword-level saturation scores to produce a niche-level
    saturation summary.
    """
    scores = db.query(KeywordScore.saturation_score).filter(
        KeywordScore.niche_id == niche_id,
        KeywordScore.saturation_score.isnot(None),
    ).all()

    if not scores:
        return {"niche_saturation_score": None, "label": "UNKNOWN"}

    values = [s.saturation_score for s in scores]
    avg = float(np.mean(values))
    p75 = float(np.percentile(values, 75))  # 75th percentile — how saturated is the saturated end

    if avg < 30:    label = "LOW SATURATION"
    elif avg < 55:  label = "MODERATE SATURATION"
    elif avg < 75:  label = "HIGH SATURATION"
    else:           label = "EXTREMELY SATURATED"

    return {
        "niche_saturation_score": round(avg, 1),
        "p75_saturation": round(p75, 1),
        "label": label,
        "keyword_count": len(values),
        "low_saturation_keywords": sum(1 for v in values if v < 30),
        "high_saturation_keywords": sum(1 for v in values if v >= 70),
    }
```

---

## Saturation Score Interpretation for Dashboard

| Saturation Score | Dashboard Label | Strategic Meaning |
|---|---|---|
| 0–25 | LOW | Differentiated market — buyers are seeing varied offerings, good for specialists |
| 26–50 | MODERATE | Some commoditization emerging — strong positioning can still stand out |
| 51–75 | HIGH | Crowded with similar gigs — needs sharp differentiation to get noticed |
| 76–100 | EXTREME | Race to the bottom — compete only with exceptional proof or unique sub-niche |
