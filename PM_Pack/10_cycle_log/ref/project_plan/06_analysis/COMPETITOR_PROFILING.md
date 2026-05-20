# Competitor Profiling
# Fiverr Research System — Wave 5

**Document Status:** Complete
**Wave:** 5 — Analysis and Competitor Model
**Purpose:** Competitor signal catalog, strength scoring rubric, weakness scoring rubric with 15+ weakness types, cluster synthesis design, per-seller weakness identification, and competitor change detection.

---

## Competitor Signal Catalog

Every signal collected about competitors and its analytical role:

| Signal | Source | Table.Field | Analytical Role | Weight in Strength Score |
|---|---|---|---|---|
| Seller level | Stage 5 (Playwright) | sellers.seller_level | Primary strength proxy — levels are earned through performance | High (20%) |
| Total reviews | Stage 5 | sellers.total_reviews | Authority and market validation signal | High (20%) |
| Review velocity (30d) | Stage 7 (calculated) | gig_quality_scores.review_velocity_30d | Real-time demand proxy — how actively a seller is winning orders | High (15%) |
| Response rate | Stage 5 | sellers.response_rate | Professionalism signal — high rate = reliable seller | Medium (10%) |
| Response time | Stage 5 | sellers.response_time | Professionalism signal — fast response = engaged seller | Medium (5%) |
| Portfolio count | Stage 5 | sellers.portfolio_count | Social proof depth — more samples = more trustworthy | Medium (10%) |
| Member since | Stage 5 | sellers.member_since | Tenure signal — older accounts have more trust | Low (5%) |
| Bio text richness | Stage 8 (LLM) | seller_scores.authority_signals | Expertise communication — vague vs. specific claims | Medium (10%) |
| Active gig count | Stage 5 | sellers.total_gigs | Specialization signal — too many gigs = generalist | Low (5%) |
| Badges | Stage 5 | sellers.badges | Platform recognition — Top Rated, Pro verified | Low-High (varies) |
| Gig title quality | Stage 7 (LLM) | gig_quality_scores.title_quality_score | Positioning effectiveness — how well they capture buyers | Used in Gig Quality model |
| Description quality | Stage 7 (LLM) | gig_quality_scores.description_quality_score | Conversion effectiveness — how well they close buyers | Used in Gig Quality model |
| Package pricing | Stage 4 (Playwright) | gigs.packages | Market rate establishment and value signaling | Used in Profitability model |
| Video presence | Stage 4 | gigs.video_present | Trust signal — gigs with video convert significantly better | Used in Gig Quality model |
| Thumbnail quality | Stage 7 (LLM) | gig_quality_scores.thumbnail_class | Visual trust signal — professional vs. low-quality imagery | Used in Gig Quality model |

---

## Strength Scoring Rubric

The `competitor_strength` score (0–10) is calculated per-seller and used as a 5% input into the Competition Score.

```python
# src/analysis/competitor_profiler.py

SELLER_LEVEL_SCORES = {
    "No Level": 1.0,
    "Level 1": 3.5,
    "Level 2": 6.5,
    "Top Rated": 9.0,
    "Pro": 10.0,
}

def calculate_competitor_strength(seller: Seller, seller_score: SellerScore) -> float:
    """
    Composite competitor strength score (0–10).
    Higher = stronger competitor = harder to displace.
    """
    # Component 1: Seller level (20%)
    level_score = SELLER_LEVEL_SCORES.get(seller.seller_level or "No Level", 1.0)

    # Component 2: Review count (20%) — normalized against niche median
    review_score = min(10.0, (seller.total_reviews or 0) / 50)
    # 50 reviews = score 1.0; 500 reviews = score 10.0

    # Component 3: Review velocity (15%) — proxy for active demand
    velocity = getattr(seller_score, "review_velocity_30d", None) or 0
    velocity_score = min(10.0, velocity * 2)
    # 5 reviews/month = score 10.0

    # Component 4: Response rate (10%)
    rate = seller.response_rate or 0
    response_score = rate / 10.0  # 100% rate = score 10.0

    # Component 5: Portfolio count (10%)
    portfolio = seller.portfolio_count or 0
    portfolio_score = min(10.0, portfolio / 3)
    # 30 portfolio items = score 10.0

    # Component 6: Authority score from LLM bio analysis (10%)
    authority = getattr(seller_score, "authority_score", None) or 5.0

    # Component 7: Member since tenure (5%)
    tenure_years = estimate_tenure_years(seller.member_since)
    tenure_score = min(10.0, tenure_years * 1.5)
    # 7 years = score 10.0

    # Component 8: Badge recognition (5%)
    badge_score = 5.0
    if seller.badges:
        badge_names = [b.get("badge", "") for b in seller.badges]
        if "Top Rated" in badge_names: badge_score = 9.0
        elif any("Pro" in b for b in badge_names): badge_score = 10.0
        elif "Level 2" in badge_names: badge_score = 6.0

    # Component 9: Active gig count — specialization bonus (5%)
    # Sellers with 1–3 gigs are more specialized (higher quality per gig)
    # Sellers with 10+ gigs are generalists (lower quality per gig)
    gig_count = seller.total_gigs or 1
    if gig_count <= 3: specialization_score = 8.0
    elif gig_count <= 7: specialization_score = 5.0
    else: specialization_score = 2.0

    composite = (
        level_score      * 0.20 +
        review_score     * 0.20 +
        velocity_score   * 0.15 +
        response_score   * 0.10 +
        portfolio_score  * 0.10 +
        authority        * 0.10 +
        tenure_score     * 0.05 +
        badge_score      * 0.05 +
        specialization_score * 0.05
    )
    return round(min(10.0, max(0.0, composite)), 2)
```

---

## Weakness Scoring Rubric — 15 Weakness Types

Each weakness type has a detection method, severity rating, and exploitation guidance.

| # | Weakness Type | Detection Method | Severity | Exploitation Angle |
|---|---|---|---|---|
| 1 | Vague promises | LLM: description lacks specific deliverables, uses "I will help you with X" language | HIGH | Write description with concrete, specific deliverables list |
| 2 | No proof elements | LLM: no case studies, no "I've done X for Y clients", no numbers in description | HIGH | Include specific past results, even from non-Fiverr work |
| 3 | Generic copy | LLM: description could apply to any seller in this niche, no differentiation | HIGH | Lead with specific niche expertise and unique process |
| 4 | Weak package differentiation | LLM: Basic/Standard/Premium are vague or overlap significantly | MEDIUM | Create clearly tiered packages with distinct, named deliverables |
| 5 | No video present | Stage 4: gigs.video_present = False | MEDIUM | Add a gig video (even a simple screen recording adds 40%+ conversion) |
| 6 | No portfolio / samples | Stage 4: gigs.portfolio_count = 0 or null | HIGH | Upload 3–5 portfolio samples before publishing |
| 7 | Low-quality / text-heavy thumbnail | LLM: thumbnail_class = TEXT_HEAVY or LOW_QUALITY | MEDIUM | Create a professional image-forward thumbnail |
| 8 | Incomplete FAQ | LLM: faq_quality_score < 50 or faq_entries is empty | MEDIUM | Write 5–7 specific buyer-concern FAQs |
| 9 | Poor CTA strength | LLM: description has no clear call to action at the end | LOW | Add a direct CTA: "Message me with your requirements" |
| 10 | Niche-generic positioning | LLM: desc_niche_specificity < 5 — description is broad not specialist | HIGH | Position as a specialist ("I only do X for Y type of client") |
| 11 | Slow delivery time | Stage 4: gigs.packages[].delivery_days vs. niche median | MEDIUM | Offer faster delivery if feasible — buyers often choose on speed |
| 12 | No gig extras / upsells | Stage 4: gigs.gig_extras is empty | LOW | Add 2–3 extras (express delivery, extra revisions, additional items) |
| 13 | Overpriced Basic tier | Stage 4: Basic price > 150% of niche median Basic | MEDIUM | Anchor Basic at or near niche median to reduce first-click friction |
| 14 | Bio lacks credentials | LLM: authority_signals is empty or low authority_score | MEDIUM | Highlight specific tools, technologies, years of experience in bio |
| 15 | Missing revision policy | LLM: no mention of revisions in description or packages | LOW | State revision policy clearly — "X rounds of revisions included" |

### Weakness Detection in Code

```python
def detect_gig_weaknesses(gig: Gig, gig_quality: GigQualityScore,
                           niche_context: dict) -> list[dict]:
    """
    Combines LLM-detected weaknesses with rule-based weakness detection.
    Returns a list of weakness dicts sorted by severity (HIGH first).
    """
    weaknesses = []

    # Rule-based detections (no LLM needed)
    if not gig.video_present:
        weaknesses.append({
            "weakness": "No gig video",
            "type": "no_video",
            "severity": "MEDIUM",
            "description": "Gig has no video — video gigs convert significantly better",
            "exploitation": "Add a gig video to stand out from this seller"
        })

    if not gig.portfolio_count or gig.portfolio_count == 0:
        weaknesses.append({
            "weakness": "No portfolio samples",
            "type": "no_portfolio",
            "severity": "HIGH",
            "description": "Seller has no portfolio items — buyers cannot evaluate quality",
            "exploitation": "Upload portfolio samples before publishing your gig"
        })

    if gig.gig_extras is None or len(gig.gig_extras) == 0:
        weaknesses.append({
            "weakness": "No gig extras",
            "type": "no_extras",
            "severity": "LOW",
            "description": "No add-on services offered — missed upsell opportunity",
            "exploitation": "Add 2–3 relevant extras to increase average order value"
        })

    # Check delivery time vs. niche median
    niche_median_delivery = niche_context.get("median_delivery_days")
    if niche_median_delivery and gig.packages:
        basic_delivery = min(
            (p.get("delivery_days", 99) for p in gig.packages), default=99
        )
        if basic_delivery > niche_median_delivery * 1.5:
            weaknesses.append({
                "weakness": "Slow delivery vs. niche median",
                "type": "slow_delivery",
                "severity": "MEDIUM",
                "description": f"Basic delivery {basic_delivery}d vs. niche median {niche_median_delivery}d",
                "exploitation": "Offer a faster Basic delivery to capture time-sensitive buyers"
            })

    # Add LLM-detected weaknesses
    if gig_quality and gig_quality.weakness_list:
        weaknesses.extend(gig_quality.weakness_list)

    # Sort by severity
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    weaknesses.sort(key=lambda w: severity_order.get(w.get("severity", "LOW"), 2))

    return weaknesses
```

---

## Cluster Synthesis Design (gpt-4o)

The cluster synthesis runs once per keyword cluster per niche, giving a strategic landscape overview that is more valuable than per-gig analysis alone.

### Input Specification

```python
def build_cluster_synthesis_input(cluster_id: int, niche_id: str, db) -> dict:
    """
    Assembles all data needed for the cluster synthesis LLM call.
    """
    # Get top 10 competitors in this cluster (by review count)
    top_sellers = get_top_sellers_for_cluster(cluster_id, niche_id, db, limit=10)

    return {
        "niche_name": get_niche_name(niche_id),
        "cluster_label": get_cluster_label(cluster_id, niche_id, db),
        "competitor_count": len(top_sellers),
        "competitors": [
            {
                "username": s.seller_username,
                "seller_level": s.seller_level,
                "total_reviews": s.total_reviews,
                "review_velocity_30d": get_review_velocity(s, db),
                "starting_price": get_lowest_package_price(s, db),
                "bio_snippet": (s.bio_text or "")[:200],
                "gig_title": get_top_gig_title(s, db),
                "authority_score": get_authority_score(s, db),
                "top_weaknesses": get_top_weaknesses(s, db, limit=3),
                "has_video": get_has_video(s, db),
                "has_portfolio": get_has_portfolio(s, db),
                "thumbnail_class": get_thumbnail_class(s, db),
            }
            for s in top_sellers
        ],
        "avg_review_count": mean([s.total_reviews or 0 for s in top_sellers]),
        "avg_starting_price": mean([get_lowest_package_price(s, db) for s in top_sellers]),
        "pro_seller_count": sum(1 for s in top_sellers if s.seller_level == "Pro"),
        "level2_plus_count": sum(1 for s in top_sellers
                                  if s.seller_level in ("Level 2", "Top Rated", "Pro")),
    }
```

### Cluster Synthesis Prompt Template

```
Prompt template: src/llm/prompts/stage08_competitor/cluster_synthesis.j2

---
You are a Fiverr competitive intelligence analyst. Analyze this competitor cluster
and provide a strategic synthesis for a new seller deciding whether to enter.

Niche: {{ niche_name }}
Cluster: {{ cluster_label }}
Total competitors analyzed: {{ competitor_count }}

Top competitors:
{% for c in competitors %}
{{ loop.index }}. {{ c.username }} — {{ c.seller_level }}, {{ c.total_reviews }} reviews,
   Starting at ${{ c.starting_price }}, Review velocity: {{ c.review_velocity_30d }}/month
   Gig title: "{{ c.gig_title }}"
   Top weaknesses: {{ c.top_weaknesses | join(", ") }}
   Has video: {{ c.has_video }} | Has portfolio: {{ c.has_portfolio }}
{% endfor %}

Market stats:
- Average reviews among top 10: {{ avg_review_count | round(0) }}
- Average starting price: ${{ avg_starting_price | round(0) }}
- Pro sellers in top 10: {{ pro_seller_count }}
- Level 2+ sellers in top 10: {{ level2_plus_count }}

Provide a strategic synthesis with these four sections:
1. WHO DOMINATES (2 sentences): Which sellers own this cluster and why.
2. WHY THEY WIN (2 sentences): What gives them their competitive advantage.
3. THE GAP (2 sentences): What weakness or underserved need exists that a new seller could exploit.
4. ENTRY VERDICT (1 sentence): Blunt assessment — easy, medium, or hard entry and why.

Be specific. Use seller names and numbers. No generic advice.
---

Output schema:
{
  "who_dominates": "string",
  "why_they_win": "string",
  "the_gap": "string",
  "entry_verdict": "string",
  "entry_feasibility_rating": 0-10  // 10 = very easy to enter, 0 = nearly impossible
}

Stored in: competitor_analysis.synthesis_narrative (assembled from sections)
           competitor_analysis.entry_feasibility_rating
Model: gpt-4o
Cache: Yes — keyed on competitor data (re-runs when seller data refreshes)
```

---

## Per-Seller Weakness Identification (gpt-4o)

For the top 3 competitors per niche (by review count), gpt-4o identifies specific, actionable weaknesses that a new seller can exploit.

```
Prompt template: src/llm/prompts/stage08_competitor/weakness_identification.j2

---
You are analyzing a specific Fiverr competitor to identify exploitable weaknesses
for a new seller entering this niche.

Competitor: {{ seller_username }} ({{ seller_level }}, {{ total_reviews }} reviews)
Niche: {{ niche_name }}

Gig title: "{{ gig_title }}"
Description excerpt: "{{ description_excerpt }}"
Packages: {{ packages_summary }}
Tags: {{ tags | join(", ") }}
Has video: {{ has_video }}
Portfolio items: {{ portfolio_count }}
Thumbnail type: {{ thumbnail_class }}
FAQ quality score: {{ faq_quality_score }}/100

Identify 3–5 specific, exploitable weaknesses. For each:
- What the weakness is (be specific, not generic)
- Why it hurts this seller's conversion
- What a new seller should do differently

Format as JSON array:
[
  {
    "weakness": "specific description",
    "impact": "why this hurts them",
    "counter_strategy": "what you should do instead",
    "severity": "HIGH|MEDIUM|LOW"
  }
]
---

Stored in: competitor_analysis.per_seller_weaknesses
Model: gpt-4o
Cache: Yes — keyed on gig description + quality scores
```

---

## Competitor Change Detection

The system detects significant competitor changes between runs to trigger alerts.

```python
def detect_competitor_changes(niche_id: str, current_run_id: str,
                               previous_run_id: str, db) -> list[dict]:
    """
    Compares competitor data between runs and returns significant changes.
    Called at end of Stage 8.
    """
    changes = []

    current_sellers = get_top_sellers_for_niche(niche_id, current_run_id, db)

    for seller in current_sellers:
        prev_data = get_seller_previous_run_data(seller.seller_username,
                                                  previous_run_id, db)
        if prev_data is None:
            continue  # New competitor — not a change

        # Detect significant review count growth (> 20% increase)
        if prev_data.total_reviews and seller.total_reviews:
            growth = (seller.total_reviews - prev_data.total_reviews) / prev_data.total_reviews
            if growth > 0.20:
                changes.append({
                    "change_type": "REVIEW_SURGE",
                    "seller_username": seller.seller_username,
                    "niche_id": niche_id,
                    "description": (f"{seller.seller_username} gained "
                                    f"{seller.total_reviews - prev_data.total_reviews} reviews "
                                    f"({growth:.0%} growth) since last run"),
                    "severity": "HIGH" if growth > 0.50 else "MEDIUM",
                })

        # Detect level upgrade
        if prev_data.seller_level != seller.seller_level:
            prev_rank = LEVEL_RANK.get(prev_data.seller_level, 0)
            curr_rank = LEVEL_RANK.get(seller.seller_level, 0)
            if curr_rank > prev_rank:
                changes.append({
                    "change_type": "LEVEL_UPGRADE",
                    "seller_username": seller.seller_username,
                    "niche_id": niche_id,
                    "description": (f"{seller.seller_username} upgraded from "
                                    f"{prev_data.seller_level} to {seller.seller_level}"),
                    "severity": "MEDIUM",
                })

    # Detect new entrants in top 10
    current_usernames = {s.seller_username for s in current_sellers}
    prev_usernames = get_top_seller_usernames_previous_run(niche_id, previous_run_id, db)
    new_entrants = current_usernames - prev_usernames
    for username in new_entrants:
        changes.append({
            "change_type": "NEW_TOP_ENTRANT",
            "seller_username": username,
            "niche_id": niche_id,
            "description": f"{username} entered the top 10 for {niche_id} this run",
            "severity": "LOW",
        })

    return changes

LEVEL_RANK = {"No Level": 0, "Level 1": 1, "Level 2": 2, "Top Rated": 3, "Pro": 4}
```

Detected changes are stored in `alerts` table (alert_type=COMPETITOR_CHANGE) and surfaced in the dashboard Competitors page.
