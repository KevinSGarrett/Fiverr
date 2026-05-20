# Seller Strength Model
# Fiverr Research System — Wave 5

**Document Status:** Complete
**Wave:** 5 — Analysis and Competitor Model
**Purpose:** Authority signal catalog, scoring formula, LLM bio parse design, seller strength vs. gig quality interaction, and new seller detection.

---

## Authority Signal Catalog

Every signal the system collects about a seller and its role in the authority_score (0–10):

| Signal | Source | Field | Role | Weight |
|---|---|---|---|---|
| Seller level | Stage 5 | sellers.seller_level | Primary platform-validated authority signal | 25% |
| Total reviews | Stage 5 | sellers.total_reviews | Volume of validated buyer experiences | 20% |
| Response rate | Stage 5 | sellers.response_rate | Professionalism and reliability indicator | 10% |
| Response time | Stage 5 | sellers.response_time | Engagement and availability signal | 5% |
| Member since tenure | Stage 5 | sellers.member_since | Platform longevity — older = more established | 8% |
| Portfolio count | Stage 5 | sellers.portfolio_count | Demonstrated work depth | 10% |
| Bio text richness | Stage 8 LLM | seller_scores.authority_signals | Self-presented expertise and credibility | 12% |
| Badge recognition | Stage 5 | sellers.badges | Platform-awarded performance recognition | 5% |
| Active gig specialization | Stage 5 | sellers.total_gigs | Niche focus vs. generalist spread | 5% |

---

## Authority Score Formula

```python
# src/analysis/seller_strength.py

def calculate_authority_score(seller: Seller, niche_context: dict) -> float:
    """
    Calculates seller authority score (0–10).
    Higher = more authoritative competitor = harder to displace.

    niche_context provides niche-level benchmarks for normalization.
    """

    # --- Component 1: Seller Level (25%) ---
    LEVEL_SCORES = {
        "No Level": 0.5,
        "Level 1": 3.0,
        "Level 2": 6.5,
        "Top Rated": 9.0,
        "Pro": 10.0,
    }
    level_score = LEVEL_SCORES.get(seller.seller_level or "No Level", 0.5)

    # --- Component 2: Review Count (20%) ---
    # Normalized against niche median review count for context-aware scoring
    niche_median_reviews = niche_context.get("median_review_count", 50)
    reviews = seller.total_reviews or 0
    # Score relative to niche: at 1× median = 5.0; at 3× median = 10.0
    review_score = min(10.0, (reviews / max(1, niche_median_reviews)) * 5.0)

    # --- Component 3: Response Rate (10%) ---
    rate = seller.response_rate or 0
    response_rate_score = rate / 10.0  # 100% → 10.0

    # --- Component 4: Response Time (5%) ---
    response_time_map = {
        "1 hour": 10.0, "a few hours": 8.0, "within a day": 6.0,
        "1 day": 6.0, "2 days": 4.0, "3 days": 2.0,
    }
    response_time_str = (seller.response_time or "").lower()
    response_time_score = 5.0  # Default neutral
    for key, val in response_time_map.items():
        if key in response_time_str:
            response_time_score = val
            break

    # --- Component 5: Tenure (8%) ---
    tenure_years = estimate_tenure_years(seller.member_since)
    # Normalize: 7 years = score 10.0
    tenure_score = min(10.0, tenure_years * (10.0 / 7.0))

    # --- Component 6: Portfolio Count (10%) ---
    portfolio = seller.portfolio_count or 0
    # 30 items = score 10.0
    portfolio_score = min(10.0, portfolio / 3.0)

    # --- Component 7: Bio Richness (12%) ---
    # Set by LLM bio parse (see below); default 5.0 if not yet analyzed
    bio_score = 5.0  # Placeholder — replaced by LLM result

    # --- Component 8: Badge Recognition (5%) ---
    badge_score = 5.0
    if seller.badges:
        badge_names = [b.get("badge", "").lower() for b in seller.badges]
        if any("pro" in b for b in badge_names): badge_score = 10.0
        elif any("top rated" in b for b in badge_names): badge_score = 9.0
        elif any("level 2" in b for b in badge_names): badge_score = 6.0
        elif any("level 1" in b for b in badge_names): badge_score = 3.0

    # --- Component 9: Gig Specialization (5%) ---
    gig_count = seller.total_gigs or 1
    if gig_count <= 2:   specialization_score = 9.0   # Very focused
    elif gig_count <= 5: specialization_score = 6.0   # Moderately focused
    elif gig_count <= 10: specialization_score = 4.0  # Somewhat broad
    else:                specialization_score = 2.0   # Generalist

    # --- Weighted composite ---
    composite = (
        level_score          * 0.25 +
        review_score         * 0.20 +
        response_rate_score  * 0.10 +
        response_time_score  * 0.05 +
        tenure_score         * 0.08 +
        portfolio_score      * 0.10 +
        bio_score            * 0.12 +
        badge_score          * 0.05 +
        specialization_score * 0.05
    )
    return round(min(10.0, max(0.0, composite)), 2)
```

---

## Review Velocity Scoring

Review velocity (`review_velocity_30d`) is estimated from the review snippet dates collected in Stage 4. It is the primary proxy for current demand when `orders_in_queue` is not visible.

```python
from datetime import datetime, timedelta
import re

def estimate_review_velocity(review_snippets: list[dict]) -> float:
    """
    Estimates reviews received in the last 30 days from visible review snippets.

    Fiverr shows recent reviews on the gig detail page. The date is typically
    shown as relative ("2 days ago", "1 week ago") or absolute ("Mar 2026").

    Returns estimated reviews/month (float).
    """
    if not review_snippets:
        return 0.0

    recent_count = 0
    cutoff = datetime.utcnow() - timedelta(days=30)

    for review in review_snippets:
        date_str = review.get("date", "")
        review_date = parse_review_date(date_str)
        if review_date and review_date >= cutoff:
            recent_count += 1

    return float(recent_count)


def parse_review_date(date_str: str) -> datetime | None:
    """
    Parses Fiverr's relative and absolute date strings.
    Examples: "2 days ago", "1 week ago", "about 1 month ago", "Mar 2026"
    """
    if not date_str:
        return None

    now = datetime.utcnow()
    date_str_lower = date_str.lower().strip()

    # Relative dates
    if "day" in date_str_lower:
        match = re.search(r"(\d+)\s*day", date_str_lower)
        days = int(match.group(1)) if match else 1
        return now - timedelta(days=days)
    if "week" in date_str_lower:
        match = re.search(r"(\d+)\s*week", date_str_lower)
        weeks = int(match.group(1)) if match else 1
        return now - timedelta(weeks=weeks)
    if "month" in date_str_lower:
        match = re.search(r"(\d+)\s*month", date_str_lower)
        months = int(match.group(1)) if match else 1
        return now - timedelta(days=months * 30)
    if "hour" in date_str_lower or "minute" in date_str_lower:
        return now - timedelta(hours=12)  # Very recent

    # Absolute dates (e.g., "Mar 2026")
    try:
        return datetime.strptime(date_str.strip(), "%b %Y")
    except ValueError:
        pass

    return None
```

**Velocity score interpretation:**
```
0.0   reviews/month → Score 0.0  (no recent activity — possibly inactive)
1–2   reviews/month → Score 2.0  (low activity)
3–5   reviews/month → Score 5.0  (moderate activity)
5–10  reviews/month → Score 7.5  (active seller)
10+   reviews/month → Score 10.0 (high-demand seller)
```

---

## LLM Bio Parse Design (gpt-4o-mini)

The bio parse extracts authority signals from the seller's bio text and returns a structured assessment.

```
Prompt template: src/llm/prompts/stage08_competitor/bio_parse.j2

---
You are evaluating a Fiverr seller's bio for authority signals relevant to this niche.

Niche: {{ niche_name }}
Seller level: {{ seller_level }}
Bio text:
"{{ bio_text }}"

Extract authority signals and score the overall bio richness (0–10).

Return JSON:
{
  "bio_richness_score": 0-10,
  "authority_signals": [
    // List of specific signals found. Examples:
    // "10+ years of Python development experience"
    // "Former software architect at [company type]"
    // "Specializes in AI/ML workflow automation"
    // "Client portfolio includes SaaS startups"
  ],
  "missing_signals": [
    // What a strong bio in this niche would typically include but doesn't:
    // "No mention of specific tools or frameworks"
    // "No client results or outcomes cited"
  ],
  "bio_weakness": "one sentence description of the bio's main weakness, or null if bio is strong"
}

Scoring guide:
10: Highly specific expertise, named tools/frameworks, quantified results, clear niche focus
7-9: Good credentials, some specificity, clear relevant experience
4-6: Generic credentials, limited specificity, could apply to any tech seller
1-3: Very vague, no credentials, no specific experience mentioned
0: Empty bio or completely irrelevant content
---

Model: gpt-4o-mini
Cache: Yes — keyed on bio_text
Stored in: sellers.authority_score, sellers.authority_signals, seller_scores
```

---

## Seller Strength vs. Gig Quality Interaction

A strong seller with a weak gig is a different threat than a weak seller with a strong gig. The system tracks both independently and their combination affects the New Seller Feasibility Score.

```python
def assess_entry_difficulty(
    seller_strength: float,      # 0–10: How strong is the competitor as a seller?
    gig_weakness_score: float,   # 0–10: How weak is their gig? (higher = more exploitable)
) -> dict:
    """
    Classifies the competitor entry difficulty based on seller strength
    and gig exploitability.

    Returns an assessment dict with difficulty label and strategic note.
    """
    # Quadrant analysis
    strong_seller  = seller_strength >= 6.0
    weak_gig       = gig_weakness_score >= 6.0

    if strong_seller and not weak_gig:
        return {
            "difficulty": "HARD",
            "label": "Strong seller, strong gig",
            "note": "Both the seller and gig are strong. Direct competition is risky. "
                    "Find a sub-niche or wait for market evolution.",
            "feasibility_contribution": 2.0
        }
    elif strong_seller and weak_gig:
        return {
            "difficulty": "MEDIUM",
            "label": "Strong seller, exploitable gig",
            "note": "Seller is established but their gig has clear weaknesses. "
                    "A better-positioned gig can capture buyers who notice the gap.",
            "feasibility_contribution": 6.0
        }
    elif not strong_seller and weak_gig:
        return {
            "difficulty": "EASY",
            "label": "Weak seller, exploitable gig",
            "note": "Both the seller and their gig are weak. Strong entry opportunity "
                    "with good positioning and proof assets.",
            "feasibility_contribution": 9.0
        }
    else:  # not strong_seller, not weak_gig
        return {
            "difficulty": "MEDIUM-LOW",
            "label": "Modest seller, solid gig",
            "note": "Seller is not dominant but has a decent gig. "
                    "Entry is feasible with superior proof and differentiation.",
            "feasibility_contribution": 7.0
        }
```

---

## New Seller Detection

Signals that indicate a competitor is new to Fiverr, making them lower barrier to compete against:

```python
def is_new_seller(seller: Seller) -> bool:
    """
    Returns True if the seller shows signs of being new to Fiverr.
    New sellers are lower barriers to entry — they have not yet built
    the review moat that established sellers have.
    """
    tenure_years = estimate_tenure_years(seller.member_since)
    reviews = seller.total_reviews or 0
    level = seller.seller_level or "No Level"

    # New if: joined within last 12 months AND fewer than 20 reviews
    if tenure_years <= 1.0 and reviews < 20:
        return True

    # New if: still at No Level despite some time on platform
    if level == "No Level" and reviews < 10:
        return True

    return False
```

**New seller signals feed into New Seller Feasibility Score:**
- If top 5 gigs in a keyword include 3+ new sellers → feasibility score gets a significant boost
- New sellers in top positions indicate the niche has not yet been locked up by established sellers
- This is one of the strongest positive signals for a new entrant

---

## Seller Strength Summary Output

The complete seller analysis is assembled into a `SellerStrengthSummary` for use in scoring and recommendations:

```python
from pydantic import BaseModel

class SellerStrengthSummary(BaseModel):
    seller_username: str
    seller_level: str
    authority_score: float              # 0–10
    authority_signals: list[str]        # LLM-extracted
    bio_richness_score: float           # 0–10
    review_velocity_30d: float          # reviews/month
    is_new_seller: bool
    entry_difficulty: str               # EASY/MEDIUM-LOW/MEDIUM/HARD
    feasibility_contribution: float     # 0–10 (input to New Seller Feasibility Score)
    top_weaknesses: list[str]           # From weakness identification
    strategic_note: str                 # One-sentence assessment
```
