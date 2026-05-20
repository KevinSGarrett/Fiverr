# Review Analysis
# Fiverr Research System — Wave 5

**Document Status:** Complete
**Wave:** 5 — Analysis and Competitor Model
**Purpose:** Review sentiment analysis design, theme extraction for these 9 niches, review velocity proxy formula, red flag review detection, and review insight integration into scoring and recommendations.

---

## Design Goals

1. Extract buyer intelligence from competitor review text — what buyers love, what frustrates them, and what gaps they mention
2. Estimate review velocity as an orders proxy when orders_in_queue is not visible
3. Flag reviews that reveal delivery or quality problems in competitor gigs
4. Feed review themes into the Gig Quality Weakness Score and recommendation differentiation angles

---

## Review Sentiment Classification (gpt-4o-mini)

```
Prompt template: src/llm/prompts/stage07_gig_quality/review_sentiment.j2

---
Classify these Fiverr gig reviews for a {{ niche_name }} service.

Reviews:
{% for r in review_snippets %}
- "{{ r.snippet }}" ({{ r.rating }} stars)
{% endfor %}

For each review, classify sentiment and extract the primary theme.

Return JSON array:
[
  {
    "snippet_index": 0,
    "sentiment": "POSITIVE|NEUTRAL|NEGATIVE",
    "primary_theme": "string",
    "buyer_outcome_mentioned": true|false,
    "red_flag": true|false,
    "red_flag_type": "string or null"
  }
]
---

Model: gpt-4o-mini
Cache: Yes — keyed on review text
Stored in: gig_quality_scores (aggregated theme output)
```

### Sentiment Score Impact

```python
def review_sentiment_to_score(sentiment_results: list[dict]) -> float:
    """
    Converts review sentiment classification into a 0–10 score
    reflecting overall buyer satisfaction.

    10 = overwhelmingly positive reviews
    0  = overwhelmingly negative reviews
    """
    if not sentiment_results:
        return 7.0  # Neutral default when no reviews

    positive = sum(1 for r in sentiment_results if r.get("sentiment") == "POSITIVE")
    neutral  = sum(1 for r in sentiment_results if r.get("sentiment") == "NEUTRAL")
    negative = sum(1 for r in sentiment_results if r.get("sentiment") == "NEGATIVE")
    total    = len(sentiment_results)

    weighted = (positive * 1.0 + neutral * 0.5 + negative * 0.0) / total
    return round(weighted * 10.0, 2)
```

---

## Theme Extraction — Niche-Specific Categories

Review themes are categorized for each niche. These categories are built into the LLM prompt as guidance so the model returns consistent, queryable themes.

### Universal Theme Categories (all niches)

| Theme | Description | Positive Signal | Negative Signal |
|---|---|---|---|
| DELIVERY_SPEED | Comments about how fast work was delivered | "Delivered ahead of schedule" | "Took much longer than promised" |
| COMMUNICATION | Responsiveness and clarity during the project | "Always available and clear" | "Hard to reach, unclear responses" |
| QUALITY | Overall quality of the delivered work | "Exceeded expectations" | "Needed multiple revisions" |
| SCOPE_CLARITY | Whether the buyer got what they expected | "Exactly what I needed" | "Not what I asked for" |
| VALUE_FOR_MONEY | Whether the price felt fair for the work | "Great value" | "Overpriced for what was delivered" |
| REVISIONS | Experience with the revision process | "Fixed issues quickly" | "Refused to revise properly" |
| REPEAT_BUYER | Indication that buyer returned | "Will definitely hire again" | "Won't use again" |

### Niche-Specific Theme Categories

**PRD / AI SaaS MVP Roadmap:**
| Theme | Positive | Negative |
|---|---|---|
| TECHNICAL_DEPTH | "Understood our tech stack perfectly" | "Too superficial, not developer-ready" |
| ACTIONABILITY | "Dev team could implement immediately" | "Too vague to use" |
| STRUCTURE | "Well-organized, clear sections" | "Disorganized, hard to follow" |
| ASSUMPTIONS | "Asked all the right questions" | "Made assumptions without asking" |

**Python Automation / Web Scraping:**
| Theme | Positive | Negative |
|---|---|---|
| CODE_QUALITY | "Clean, well-commented code" | "Messy, no comments" |
| RELIABILITY | "Script runs without errors" | "Kept breaking, bugs everywhere" |
| DOCUMENTATION | "Explained how to use it" | "No instructions included" |
| SCOPE_CREEP | "Stayed within agreed scope" | "Charged extra for basic features" |

**AI Tool / LLM Integration / AI Agent:**
| Theme | Positive | Negative |
|---|---|---|
| INTEGRATION_ACCURACY | "API integrated perfectly" | "Integration didn't work as promised" |
| UNDERSTANDING_REQUIREMENTS | "Grasped the use case immediately" | "Didn't understand what we needed" |
| TESTING | "Thoroughly tested before delivery" | "Delivered untested code" |
| KNOWLEDGE_DEPTH | "Deep LLM/AI knowledge" | "Surface-level understanding" |

---

## Theme Extraction Implementation

```python
def extract_review_themes(review_snippets: list[dict], niche_id: str,
                           llm_client, cache) -> dict:
    """
    Extracts and aggregates themes from review snippets for a single gig.
    Returns aggregated theme counts and the most prominent themes.
    """
    if not review_snippets:
        return {"themes": {}, "top_themes": [], "red_flag_count": 0}

    niche_themes = get_niche_theme_categories(niche_id)

    # Build prompt with niche-specific theme guidance
    prompt = render_theme_extraction_prompt(review_snippets, niche_id, niche_themes)

    # Check cache
    cache_key = compute_cache_key(prompt, "gpt-4o-mini", 0.1)
    cached = cache.get(cache_key)
    if cached:
        return parse_theme_results(cached)

    # Call LLM
    result = llm_client.complete(prompt, model="gpt-4o-mini", temperature=0.1)
    cache.set(cache_key, result, ttl_hours=72)

    return parse_theme_results(result)


def aggregate_themes_across_gigs(gig_theme_results: list[dict]) -> dict:
    """
    Aggregates theme data across multiple gigs for a keyword cluster,
    revealing the most common buyer praise and complaint patterns.
    """
    all_themes = {}
    red_flag_count = 0

    for gig_result in gig_theme_results:
        for theme, data in gig_result.get("themes", {}).items():
            if theme not in all_themes:
                all_themes[theme] = {"positive": 0, "negative": 0, "total": 0}
            all_themes[theme]["positive"] += data.get("positive", 0)
            all_themes[theme]["negative"] += data.get("negative", 0)
            all_themes[theme]["total"] += data.get("total", 0)
        red_flag_count += gig_result.get("red_flag_count", 0)

    # Sort themes by total mentions
    sorted_themes = sorted(
        all_themes.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )

    top_complaint_themes = [
        t for t, d in sorted_themes
        if d["negative"] > d["positive"]
    ][:3]

    top_praise_themes = [
        t for t, d in sorted_themes
        if d["positive"] > d["negative"]
    ][:3]

    return {
        "all_themes": all_themes,
        "top_complaint_themes": top_complaint_themes,
        "top_praise_themes": top_praise_themes,
        "total_red_flags": red_flag_count,
    }
```

---

## Review Velocity Proxy Formula

Review velocity estimates how many orders per month a gig is currently receiving, based on the dates of visible review snippets.

```python
from datetime import datetime, timedelta
import re

def calculate_review_velocity(review_snippets: list[dict]) -> float:
    """
    Estimates reviews received in the last 30 days from visible snippets.

    Fiverr shows 3–10 recent reviews on the gig detail page.
    The dates are shown as relative ("2 days ago", "1 week ago") or
    abbreviated absolute ("Mar 2026").

    Methodology:
    1. Parse all visible review dates
    2. Count how many fall within the last 30 days
    3. If fewer than 5 reviews are visible, use the date distribution to
       estimate the full 30-day rate (sparse data extrapolation)

    Returns: estimated reviews/month (float, >= 0.0)
    """
    if not review_snippets:
        return 0.0

    now = datetime.utcnow()
    cutoff_30d = now - timedelta(days=30)
    cutoff_90d = now - timedelta(days=90)

    parsed_dates = []
    for review in review_snippets:
        date = parse_review_date(review.get("date", ""))
        if date:
            parsed_dates.append(date)

    if not parsed_dates:
        return 0.0

    # Direct count: reviews in last 30 days
    recent_30d = sum(1 for d in parsed_dates if d >= cutoff_30d)

    # If we have at least 3 reviews in 30 days, direct count is reliable
    if recent_30d >= 3:
        return float(recent_30d)

    # Extrapolation: use 90-day window for sparse data
    recent_90d = sum(1 for d in parsed_dates if d >= cutoff_90d)
    if recent_90d > 0:
        # Annualize from 90-day window, then convert to 30-day estimate
        return round((recent_90d / 90.0) * 30.0, 1)

    # Fallback: if we can see any reviews but all are old, velocity is very low
    if parsed_dates:
        most_recent = max(parsed_dates)
        days_since_last = (now - most_recent).days
        if days_since_last > 90:
            return 0.1  # Essentially inactive
        return 0.5  # Low but not zero

    return 0.0
```

**Velocity interpretation for scoring:**
```python
def velocity_to_demand_score_input(velocity: float) -> float:
    """
    Maps review velocity (reviews/month) to a 0–10 demand contribution.
    Used as a proxy when orders_in_queue is not visible.
    """
    if velocity <= 0:     return 0.0
    if velocity <= 1:     return 2.0
    if velocity <= 3:     return 4.0
    if velocity <= 5:     return 6.0
    if velocity <= 10:    return 8.0
    return 10.0
```

---

## Red Flag Review Detection

Red flag reviews indicate delivery problems, quality issues, or scope disputes that a new seller can use to position against.

### Red Flag Types

| Red Flag Type | Detection Pattern | Strategic Value |
|---|---|---|
| LATE_DELIVERY | "late", "overdue", "missed deadline", "took longer" | Offer faster delivery with clear SLA |
| REVISION_DISPUTE | "refused revision", "wouldn't fix", "extra charge for revision" | Offer inclusive revisions with clear policy |
| SCOPE_CREEP | "charged more", "kept adding cost", "bait and switch" | Offer all-inclusive scoped packages |
| QUALITY_MISMATCH | "not what I expected", "nothing like described", "misleading" | Offer pre-work consultation to align expectations |
| COMMUNICATION_FAILURE | "ghosted", "didn't respond", "disappeared" | Offer guaranteed response time |
| REFUND_REQUEST | "requested refund", "had to cancel", "dispute" | Strong buyer requirements upfront |
| GENERIC_DELIVERY | "copy-paste", "generic", "template", "not customized" | Emphasize custom, research-based approach |

```python
RED_FLAG_PATTERNS = {
    "LATE_DELIVERY": [
        "late", "overdue", "missed deadline", "took longer than",
        "waited weeks", "delayed", "not on time"
    ],
    "REVISION_DISPUTE": [
        "refused to revise", "wouldn't fix", "extra charge for revision",
        "charged for changes", "no revisions", "revision issues"
    ],
    "SCOPE_CREEP": [
        "charged more", "added cost", "bait and switch", "not as described",
        "hidden fees", "extra charges", "price went up"
    ],
    "QUALITY_MISMATCH": [
        "not what i expected", "nothing like described", "misleading",
        "poor quality", "unusable", "had to rewrite"
    ],
    "COMMUNICATION_FAILURE": [
        "ghosted", "didn't respond", "no response", "disappeared",
        "hard to reach", "ignored my messages"
    ],
    "GENERIC_DELIVERY": [
        "copy-paste", "generic", "template", "not customized",
        "felt like a template", "could have used chatgpt"
    ],
}

def detect_red_flags(review_snippets: list[dict]) -> list[dict]:
    """
    Rule-based red flag detection on review text.
    Returns list of detected red flags sorted by severity.
    """
    red_flags = []
    all_text = " ".join(
        r.get("snippet", "").lower() for r in review_snippets
    )

    for flag_type, patterns in RED_FLAG_PATTERNS.items():
        matches = [p for p in patterns if p in all_text]
        if matches:
            red_flags.append({
                "flag_type": flag_type,
                "matched_patterns": matches,
                "severity": "HIGH" if flag_type in ("QUALITY_MISMATCH", "REFUND_REQUEST") else "MEDIUM",
                "review_count": sum(
                    1 for r in review_snippets
                    if any(p in r.get("snippet", "").lower() for p in matches)
                )
            })

    return sorted(red_flags, key=lambda x: 0 if x["severity"] == "HIGH" else 1)
```

---

## Review Insight Integration

Review insights feed into two downstream systems:

### 1. Gig Quality Weakness Score Integration

Competitor review red flags amplify the weakness score:

```python
def apply_review_weakness_boost(
    base_weakness_score: float,
    red_flags: list[dict],
) -> float:
    """
    Increases the overall_weakness_score when competitor reviews contain
    red flags. Buyers who had bad experiences are evidence of weakness.
    """
    if not red_flags:
        return base_weakness_score

    boost = 0.0
    for flag in red_flags:
        if flag["severity"] == "HIGH":
            boost += 0.8
        else:
            boost += 0.4

    return min(10.0, base_weakness_score + boost)
```

### 2. Recommendation Engine Integration

The most common complaint themes feed directly into the differentiation angle prompt:

```python
def get_review_insights_for_recommendation(niche_id: str, keyword_id: int, db) -> dict:
    """
    Provides review intelligence to the recommendation engine.
    Used in the differentiation_angle and red_flags LLM prompts.
    """
    gig_quality_scores = get_gig_quality_scores_for_keyword(keyword_id, db)
    aggregated = aggregate_themes_across_gigs([
        json.loads(q.weakness_list or "[]") for q in gig_quality_scores
    ])

    return {
        "top_buyer_complaints": aggregated["top_complaint_themes"],
        "top_buyer_praise": aggregated["top_praise_themes"],
        "red_flag_patterns": get_keyword_red_flags(keyword_id, db),
        "competitor_failure_modes": [
            f"{ft}: mentioned in {count} competitor reviews"
            for ft, count in get_red_flag_frequency(keyword_id, db).items()
        ],
    }
```

**Example use in differentiation angle prompt:**
```
"Top competitor review complaints for this keyword:
 - LATE_DELIVERY: mentioned in 8 competitor reviews
 - GENERIC_DELIVERY: mentioned in 6 competitor reviews
 - COMMUNICATION_FAILURE: mentioned in 4 competitor reviews

Use these patterns to craft a differentiation angle that directly addresses
what buyers are frustrated with when hiring from existing sellers."
```

---

## OQ-007 Resolution — Competitor Tracking Scope

**Decision for v1:** Snapshot-only. Each run collects current seller data. No historical versioning of seller records.

**Implication:** The `detect_competitor_changes()` function in COMPETITOR_PROFILING.md compares the current run's collected data with the previous run's collected data — both stored in the `sellers` table with their `run_id` and `collected_at` fields. This gives run-over-run change detection without a full versioning system.

**v2 Time-Series Upgrade Path:**

When time-series tracking is needed (for review velocity trend, price change history, seller level progression):

1. Add a `seller_history` table:
```sql
CREATE TABLE seller_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_username TEXT NOT NULL,
    run_id          TEXT NOT NULL,
    snapshot_at     TEXT NOT NULL,
    seller_level    TEXT,
    total_reviews   INTEGER,
    response_rate   INTEGER,
    total_gigs      INTEGER,
    starting_price  REAL
);
CREATE INDEX ix_seller_history_username ON seller_history(seller_username, snapshot_at);
```

2. At end of Stage 5, INSERT a snapshot row for every collected seller (keep original `sellers` row as "latest").

3. The `review_velocity_30d` calculation in v2 uses `seller_history` instead of review snippet parsing — compare `total_reviews` between snapshots 30 days apart for exact velocity.

4. Price trend detection in v2: query `seller_history` for starting_price over time.
