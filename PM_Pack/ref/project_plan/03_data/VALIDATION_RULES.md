# Validation Rules
# Fiverr Research System — Wave 3

**Document Status:** Complete
**Wave:** 3 — Data Schema and Source Design
**Purpose:** Per-field validation rules, null handling strategy, outlier detection, data quality scoring per niche, cross-field validation, and reject vs. flag behavior.

---

## Null Handling Strategy

Every field falls into one of three null handling categories:

| Category | Meaning | Effect on Pipeline |
|---|---|---|
| **REQUIRED** | Field must never be null in a valid record. Null = collection failure. | Record rejected and job retried. If max retries exceeded, job → DEAD_LETTER. |
| **OPTIONAL** | Field may be null without affecting pipeline validity. Null is a valid data state. | No action. Field stored as null. No confidence deduction. |
| **DEGRADED** | Field should be present but its absence reduces analytical quality. | Record accepted but Confidence Modifier deducted by the amount specified. |

---

## Field-Level Validation Rules by Table

### keywords table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| keyword_text | REQUIRED | Non-empty string, len 1–512, stripped of leading/trailing whitespace. No special characters that break Fiverr search URL encoding. | Reject if empty or > 512 chars |
| niche_id | REQUIRED | Must exist in niche_configs.niche_id | Reject if niche not found |
| source | REQUIRED | Must be one of: seed, fiverr_autocomplete, google_suggest, llm_expansion | Reject if invalid value |
| autocomplete_position | OPTIONAL | Integer 1–10 if present, null if not from autocomplete | Flag if value < 1 or > 10 |
| intent_class | DEGRADED | Must be one of: INFORMATIONAL, CONSIDERATION, HIGH_INTENT, TRANSACTIONAL if present | Confidence −0.05 if null |
| embedding_vector | DEGRADED | JSON array of exactly 1536 floats, all values between −1.0 and 1.0 | Confidence −0.10 if null; skip clustering for keyword |
| ttl_hours | REQUIRED | Integer 24–720 | Default to 168 if missing |

---

### search_results table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| keyword_id | REQUIRED | Valid FK to keywords.id | Reject if keyword not found |
| total_result_count | DEGRADED | Integer >= 0 if present | Confidence −0.10 if null (primary demand signal) |
| gig_cards | DEGRADED | JSON array, 0 or more items; each item must have gig_url (valid URL), gig_title (non-empty), seller_username (non-empty) | Confidence −0.15 if null or empty array |
| gig_cards[].gig_url | REQUIRED | Must match pattern: https://www.fiverr.com/[username]/[slug] | Reject card if URL invalid |
| gig_cards[].starting_price | OPTIONAL | Float > 0 if present | Flag if value <= 0 |
| gig_cards[].position | REQUIRED | Integer 1–N (N = number of results on page) | Reject card if missing |

---

### gigs table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| gig_url | REQUIRED | Valid Fiverr gig URL pattern | Reject if invalid |
| gig_title | REQUIRED | Non-empty string, len 10–512 | Reject if empty |
| seller_username | REQUIRED | Non-empty string, no spaces | Reject if empty |
| description_text | DEGRADED | Non-empty string if detail_collected=True; null acceptable if detail_collected=False | Confidence −0.08 if detail_collected=True but null |
| packages | DEGRADED | JSON array, 1–3 items if detail_collected=True | Confidence −0.05 if null when detail collected |
| packages[].price | REQUIRED (if present) | Float > 0 | Flag if <= 0 |
| packages[].delivery_days | REQUIRED (if present) | Integer 1–365 | Flag if out of range |
| tags | OPTIONAL | JSON array, 0–5 strings, each 2–30 chars | Flag if any tag > 30 chars |
| review_count_exact | DEGRADED | Integer >= 0 if detail_collected=True | Confidence −0.05 if null when detail collected |
| rating_exact | DEGRADED | Float 1.0–5.0 if present | Flag if outside range |
| video_present | OPTIONAL | Boolean | — |
| orders_in_queue | OPTIONAL | Integer >= 0 if present; null is valid (common) | No penalty for null — see OQ-003 resolution |
| ttl_hours | REQUIRED | Integer 24–336 | Default to 120 if missing |

---

### sellers table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| seller_username | REQUIRED | Non-empty, no spaces, lowercase | Reject if empty |
| seller_level | OPTIONAL | One of: No Level, Level 1, Level 2, Top Rated, Pro | Flag if unexpected value |
| response_rate | OPTIONAL | Integer 0–100 if present | Flag if > 100 |
| total_reviews | OPTIONAL | Integer >= 0 if present | Flag if < 0 |
| bio_text | OPTIONAL | String, may be empty (some sellers have no bio) | — |

---

### external_signals table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| signal_type | REQUIRED | google_trends, reddit_demand, or youtube_count | Reject if invalid |
| trends_12mo_score | DEGRADED | Float 0.0–100.0 if signal_type=google_trends | Confidence −0.15 if null and signal_type=google_trends |
| trends_slope | DEGRADED | One of: RISING, FLAT, DECLINING, STRONGLY_RISING, STRONGLY_DECLINING | Confidence −0.05 if null |
| reddit_demand_intent_score | DEGRADED | Float 0.0–10.0 if signal_type=reddit_demand | Confidence −0.05 if null |
| youtube_result_count | OPTIONAL | Integer >= 0 if signal_type=youtube_count | — |

---

### gig_quality_scores table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| title_quality_score | DEGRADED | Float 0.0–100.0 | Confidence −0.03 per gig if null |
| description_quality_score | DEGRADED | Float 0.0–100.0 | Confidence −0.04 per gig if null |
| weakness_list | DEGRADED | JSON array, 0 or more items; each item has weakness (str), severity (LOW/MEDIUM/HIGH), description (str) | Confidence −0.04 if null |
| thumbnail_class | DEGRADED | PROFESSIONAL_PHOTO, GRAPHIC_DESIGN, TEXT_HEAVY, STOCK_IMAGE, or LOW_QUALITY | Confidence −0.02 if null |
| overall_weakness_score | REQUIRED (computed) | Float 0.0–10.0 | Compute from components if null; reject record if cannot compute |
| analysis_complete | REQUIRED | Boolean | Default False |

---

### keyword_scores table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| demand_score | DEGRADED | Float 0.0–100.0; required at all depth levels | Confidence −0.20 if null |
| competition_score | DEGRADED | Float 0.0–100.0; required at all depth levels | Confidence −0.20 if null |
| opportunity_score | DEGRADED | Float 0.0–100.0; computed from demand and competition | Confidence −0.25 if null (highest weight score) |
| final_score | REQUIRED | Float 0.0–100.0 | Record invalid if null |
| confidence_modifier | REQUIRED | Float 0.0–1.0 | Record invalid if null |
| score_components | REQUIRED | JSON dict with at least demand and competition keys | Flag if missing any score that should be present given score_depth |
| explanation_text | DEGRADED | Non-empty string | Confidence −0.02 if null (cosmetic only) |

---

### recommendations table

| Field | Category | Validation Rule | Reject/Flag |
|---|---|---|---|
| gig_titles | DEGRADED | JSON array of exactly 5 non-empty strings, each 30–120 chars | Confidence −0.05 if null or wrong count |
| tag_sets | DEGRADED | JSON array of 5 arrays; each inner array has 5 strings, each 2–25 chars | Confidence −0.03 if null |
| package_structure | DEGRADED | JSON dict with keys basic, standard, premium; each has price, deliverables, delivery_days | Confidence −0.05 if null |
| differentiation_angle | DEGRADED | Non-empty string, 50–500 chars | Confidence −0.04 if null |
| niche_viability_assessment | DEGRADED | Non-empty string, 100–400 chars | Confidence −0.04 if null |
| generation_complete | REQUIRED | Boolean | Default False |

---

## Outlier Detection Rules

Outlier detection runs after collection and flags records where field values are statistically unusual. Outliers are flagged (not rejected) and surfaced as warnings in the dashboard.

### Price Outliers (gigs table)
```python
def detect_price_outliers(gigs: list[Gig], niche_id: str) -> list[dict]:
    prices = [g.starting_price for g in gigs if g.starting_price is not None]
    if len(prices) < 5:
        return []  # Not enough data to detect outliers

    import numpy as np
    mean_price = np.mean(prices)
    std_price = np.std(prices)

    outliers = []
    for gig in gigs:
        if gig.starting_price is None:
            continue
        z_score = abs(gig.starting_price - mean_price) / std_price if std_price > 0 else 0
        if z_score > 2.5:  # More than 2.5 standard deviations from mean
            outliers.append({
                "gig_url": gig.gig_url,
                "field": "starting_price",
                "value": gig.starting_price,
                "niche_mean": round(mean_price, 2),
                "z_score": round(z_score, 2),
                "warning": f"Price ${gig.starting_price} is {round(z_score, 1)}σ from niche mean ${round(mean_price, 2)}"
            })
    return outliers
```

### Review Count Outliers (gigs table)
- Flag gigs with review_count_exact > 3× the niche median review count
- These "super-sellers" may skew the Competition Score — surfaced as informational warning

### Score Outliers (keyword_scores table)
- Flag keywords with final_score >= 95 — likely indicate a data quality issue (near-perfect scores are rare)
- Flag keywords with final_score = 0.0 — all scores missing, likely a collection failure
- Flag keywords with confidence_modifier < 0.3 — scores are very low confidence; recommend not acting

### Trend Score Outliers (external_signals table)
- Flag keywords with trends_12mo_score = 100 consistently — may indicate event-driven spike rather than sustained demand
- Flag keywords with trends_12mo_score = 0 — keyword may not exist as a Google search term; verify keyword is searched

---

## Cross-Field Validation Rules

Validation rules that check multiple fields in combination:

```python
def cross_validate_gig(gig: Gig) -> list[str]:
    """Returns list of cross-field validation warnings."""
    warnings = []

    # Rule 1: If detail_collected=True, description_text must be present
    if gig.detail_collected and not gig.description_text:
        warnings.append("detail_collected=True but description_text is null — collection likely incomplete")

    # Rule 2: If review_count_exact is present, it must be >= review_count_visible (from search card)
    # (exact count is from detail page and should match or exceed card display)
    if gig.review_count_exact is not None:
        search_card = get_search_card_for_gig(gig)
        if search_card and search_card.review_count_visible is not None:
            if not search_card.review_count_abbreviated and gig.review_count_exact != search_card.review_count_visible:
                warnings.append(f"review_count_exact ({gig.review_count_exact}) != "
                                f"review_count_visible ({search_card.review_count_visible}) "
                                "— possible page change between collection stages")

    # Rule 3: If packages is present, at least one package must have price > 0
    if gig.packages:
        valid_packages = [p for p in gig.packages if p.get("price", 0) > 0]
        if not valid_packages:
            warnings.append("packages present but all prices are 0 or missing — parsing likely failed")

    # Rule 4: rating_exact must be between 1.0 and 5.0 if present
    if gig.rating_exact is not None and not (1.0 <= gig.rating_exact <= 5.0):
        warnings.append(f"rating_exact {gig.rating_exact} outside valid range [1.0–5.0]")

    return warnings


def cross_validate_keyword_score(score: KeywordScore) -> list[str]:
    """Cross-field validation for score records."""
    warnings = []

    # Rule 1: opportunity_score should be consistent with demand and competition
    if all(v is not None for v in [score.demand_score, score.competition_score, score.opportunity_score]):
        expected_opportunity = (score.demand_score * 1.2) - ((100 - score.competition_score) * 0.8)
        if abs(score.opportunity_score - max(0, min(100, expected_opportunity))) > 10:
            warnings.append("opportunity_score deviates significantly from demand/competition inputs")

    # Rule 2: final_score cannot exceed weighted_composite × confidence_modifier
    if all(v is not None for v in [score.final_score, score.weighted_composite, score.confidence_modifier]):
        expected_final = score.weighted_composite * score.confidence_modifier
        if abs(score.final_score - expected_final) > 0.5:
            warnings.append("final_score calculation inconsistency detected")

    # Rule 3: confidence_modifier must be <= 1.0
    if score.confidence_modifier is not None and score.confidence_modifier > 1.0:
        warnings.append(f"confidence_modifier {score.confidence_modifier} exceeds 1.0 — clamping required")

    return warnings
```

---

## Data Quality Score Per Niche

A per-niche data quality score is calculated after each run and displayed in the dashboard. It provides a single number (0–100) representing the overall data health for that niche.

```python
def calculate_niche_data_quality_score(niche_id: str, run_id: str, db) -> float:
    """
    Composite data quality score for a niche after a run.
    Combines: collection completeness, freshness, LLM analysis completion, validation pass rate.
    Returns 0.0–100.0.
    """
    keywords = get_niche_keywords(niche_id, db)
    if not keywords:
        return 0.0

    # Component 1: Collection completeness (30%)
    # What proportion of keywords have both search results AND gig detail?
    keywords_with_search = sum(1 for k in keywords if has_fresh_search_results(k, db))
    keywords_with_detail = sum(1 for k in keywords if has_fresh_gig_detail(k, db))
    collection_score = (
        (keywords_with_search / len(keywords)) * 0.50 +
        (keywords_with_detail / len(keywords)) * 0.50
    ) * 100

    # Component 2: External signal coverage (20%)
    # What proportion of keywords have Google Trends + Reddit data?
    keywords_with_trends = sum(1 for k in keywords if has_trends_data(k, db))
    keywords_with_reddit = sum(1 for k in keywords if has_reddit_data(k, db))
    external_score = (
        (keywords_with_trends / len(keywords)) * 0.60 +
        (keywords_with_reddit / len(keywords)) * 0.40
    ) * 100

    # Component 3: LLM analysis completion (30%)
    # What proportion of gigs have complete LLM quality analysis?
    gigs = get_niche_gigs(niche_id, db)
    gigs_with_complete_analysis = sum(1 for g in gigs
                                       if g.quality_score and g.quality_score.analysis_complete)
    llm_score = (gigs_with_complete_analysis / len(gigs) * 100) if gigs else 100.0

    # Component 4: Data freshness (20%)
    # Average freshness score across all keyword records
    freshness_scores = [calculate_data_freshness_score(k.id, db) for k in keywords]
    freshness_score = (sum(freshness_scores) / len(freshness_scores)) * 100

    # Weighted composite
    quality_score = (
        collection_score   * 0.30 +
        external_score     * 0.20 +
        llm_score          * 0.30 +
        freshness_score    * 0.20
    )

    return round(min(100.0, max(0.0, quality_score)), 1)
```

**Dashboard display:**
```
PRD / AI SaaS MVP Roadmap    Data Quality: 87/100  ████████▌░  GOOD
Python Automation Scripts    Data Quality: 73/100  ███████▎░░  FAIR
AI Agent Development         Data Quality: 41/100  ████░░░░░░  POOR — run collect-only to refresh
```

---

## Reject vs. Flag Behavior Summary

| Scenario | Behavior | User Notification |
|---|---|---|
| REQUIRED field null on collection | Reject record. Retry job up to max_retries. If still failing → DEAD_LETTER. | Alert in dashboard: "Collection failure: [field] missing for [keyword]" |
| REQUIRED field null on scoring | Score record marked invalid. Do not display in rankings. | Warning in run summary |
| DEGRADED field null | Accept record. Apply confidence deduction. Store deduction in confidence_breakdown. | Shown in keyword score card: "Missing: [field] (−X.XX confidence)" |
| OPTIONAL field null | Accept record. No deduction. Store null. | No notification |
| Cross-field validation failure | Accept record. Store warning in score_components.validation_warnings. | Shown in keyword detail view |
| Outlier detected | Accept record. Flag as outlier. Store warning. | Shown as 📊 Outlier badge in keyword card |
| LLM parse failure (2nd attempt) | Accept record. Store null for LLM fields. Apply DEGRADED deductions. | Shown in LLM cost view: "Failed: [task] for [keyword]" |


---

## SRDI ADDENDUM -- Result-Set Relevance Validation Rules
**Source:** WAVE_C; Epic R2 (SCRUM-605 to SCRUM-612)
**New module:** src/analysis/result_set_validator.py

### Per-Gig Relevance Scoring (4 Signals)

Signal 1 Core term match: +0.30 per core_term hit (max 0.60)
Signal 2 Keyword overlap:  +0.25 when keyword words appear in title
Signal 3 Exclusion terms: -0.25 per non-negated exclusion hit
Signal 4 Generic penalty:  -0.15 when 3+ generic phrases AND 0 core terms

Thresholds: relevance_flag = True when score >= 0.35
Clean >= 0.60 | Borderline 0.35-0.60 | Irrelevant < 0.35

Non-English titles: score = 0.50, flag = True (neutral -- include without penalty)
Missing title: score = 0.0, flag = False, reason = "missing_title"
Negation guard: exclusion term preceded by not/avoid/no/without within 15 chars = skip

### NICHE_VALIDATION_CONFIG (9 Niches)

prd_ai_saas:
  core_terms: [PRD, product requirements, product spec, user story, feature specification]
  exclusion_terms: [logo, SEO, social media, content writing, translation, data entry]
  ghost_market_threshold: 0.20

support_kb_readiness:
  core_terms: [knowledge base, help center, documentation, FAQ, support article, KB]
  exclusion_terms: [logo, SEO blog, social media, translation, data entry]
  ghost_market_threshold: 0.20

python_automation:
  core_terms: [Python, automation, script, bot, scraping, Playwright, Selenium, workflow]
  exclusion_terms: [logo, SEO content, social media post, article writing, translation]
  ghost_market_threshold: 0.20

ai_agent_development:
  core_terms: [AI agent, chatbot, LLM, GPT, Claude, automation, intelligent agent]
  exclusion_terms: [logo design, content writing, SEO article, social media management]
  ghost_market_threshold: 0.15  (stricter -- specific niche)

mcp_ai_agent:
  core_terms: [MCP, Model Context Protocol, Claude, AI agent, tool integration, LLM tool]
  exclusion_terms: [logo, writing, SEO, social media, data entry, translation]
  ghost_market_threshold: 0.10  (very strict -- narrow niche)

n8n_automation:
  core_terms: [n8n, workflow, automation, no-code, integration, Zapier, Make, trigger]
  exclusion_terms: [logo, writing, SEO, social media post, translation, data entry]
  ghost_market_threshold: 0.15

gumloop_automation:
  core_terms: [Gumloop, automation, workflow, no-code, AI workflow, integration]
  exclusion_terms: [logo, writing, SEO, social media, translation]
  ghost_market_threshold: 0.10  (very strict -- narrow niche)

workflow_automation:
  core_terms: [workflow, automation, process automation, business automation, Zapier, Make]
  exclusion_terms: [logo, SEO content, social media post, article, translation]
  ghost_market_threshold: 0.20

python_web_scraping:
  core_terms: [scraping, web scraper, data extraction, Python, Beautiful Soup, Playwright]
  exclusion_terms: [logo, content writing, SEO, social media, translation, data entry]
  ghost_market_threshold: 0.20

DEFAULT_VALIDATION_CONFIG: ghost_market_threshold=0.20, relevance_threshold=0.35, no terms
NICHE_VALIDATION_CONFIG_VERSION = "1.0"
_NEXT_REVIEW = "2026-08-29"  (check_relevance_config_review_due() returns True when past this)

### Confidence Deduction Tiers

RSV >= 0.80  -> deduction = 0.0
RSV >= 0.60  -> deduction = -0.05
RSV >= 0.40  -> category_contamination_flag + deduction = -0.15
RSV >= 0.20  -> category_contamination_flag + deduction = -0.30
RSV <  0.20 (total > 5) OR 0 cards -> ghost_market_flag + deduction = -0.50

Ghost market is the ONLY hard block. All other conditions flag and down-weight.
