# Data Flow
# Fiverr Research System — Wave 2

**Document Status:** Complete
**Wave:** 2 — Technical Architecture
**Purpose:** End-to-end data flow for a complete run across all 9 niches, with tier-aware branching, LLM integration points, checkpoint locations, and queue involvement shown explicitly.

---

## High-Level Flow Overview

```
config.yaml + niche_configs table
        │
        ▼
[ORCHESTRATOR] Mode router → Niche Depth Dispatcher → Job Queue population
        │
        ├── [STAGE 1–2]  Keyword Expansion (all 9 niches, parallel)
        │         └──→ keywords table (+ embeddings)
        │
        ├── [STAGE 3]    Fiverr Search Collection (priority queue order)
        │         └──→ search_results table
        │
        ├── [STAGE 4]    Gig Detail Collection (depth-gated per niche)
        │         └──→ gigs table
        │
        ├── [STAGE 5]    Seller Profile Collection (depth-gated)
        │         └──→ sellers table
        │
        ├── [STAGE 6]    External Demand Validation (all 9 niches)
        │         └──→ external_signals table
        │
        ├── [STAGE 7]    LLM Gig Quality Analysis (depth-gated)
        │         └──→ gig_quality_scores table
        │
        ├── [STAGE 8]    LLM Seller Strength + Competitor Synthesis (depth-gated)
        │         └──→ seller_scores table + competitor_analysis table
        │
        ├── [STAGE 9]    Keyword Clustering (depth-gated)
        │         └──→ keyword_clusters table + cluster_analysis table
        │
        ├── [STAGE 10]   Score Calculation (all niches, depth-aware)
        │         └──→ keyword_scores table
        │
        ├── [STAGE 11]   Confidence Scoring
        │         └──→ confidence_scores table
        │
        ├── [STAGE 12]   Opportunity Ranking + GO/PASS Tagging
        │         └──→ opportunity_rankings table
        │
        ├── [STAGE 13]   LLM Recommendation Generation (GO-tier only)
        │         └──→ recommendations table
        │
        ├── [STAGE 14]   LLM Reporting + Dashboard Refresh
        │         └──→ dashboard refreshed + exports written
        │
        ├── [STAGE 15]   Run Logging + Auto-Promotion Evaluation
        │         └──→ run_logs table + niche_configs table (depth updates)
        │
        └── [END] Run complete
```

---

## Stage-by-Stage Data Flow Detail

---

### STAGE 1 — Seed Keyword Intake

**Trigger:** Run start for all 9 niches simultaneously.

**Data In:**
```
config.yaml → niches[*].fiverr.seed_keywords
config.yaml → niches[*].id, slot, tier, depth
niche_configs table → current depth per niche (overrides config if different)
```

**Processing:**
1. Config Loader reads all 9 niche profiles from config.yaml
2. Niche Depth Dispatcher reads niche_configs table, merges runtime depth overrides
3. For each niche, validates seed keywords: deduplicates, strips whitespace, checks for blanks
4. Optional: gpt-4o-mini niche expansion brainstorm if config.llm.niche_brainstorm = true

**LLM Call (optional):**
- Model: gpt-4o-mini
- Prompt template: prompts/stage01_intake/niche_expansion.j2
- Input: niche name + seed keywords
- Output: list of adjacent niches and sub-niches to consider
- Result used: displayed in run summary only; user decides whether to add to config

**Data Out:**
```
Validated seed list per niche → in-memory, passed to Stage 2
NicheJobSpec objects per niche → job queue
```

**Checkpoint:** None (fast stage, no checkpoint needed)

---

### STAGE 2 — Keyword Expansion

**Trigger:** Stage 1 complete. All 9 niches run in parallel (keyword expansion is I/O-bound and fast).

**Data In:**
```
Validated seed list per niche (from Stage 1)
config.yaml → fiverr.autocomplete_collect per niche
config.yaml → external_sources.google_trends per niche (for Google suggest)
```

**Processing per keyword per niche:**

**Step 2a — Fiverr Autocomplete Collection (Playwright, authenticated session):**
- Navigate to fiverr.com/search/gigs?query={seed}
- Collect all autocomplete suggestions (positions 1–10)
- Store with source=fiverr_autocomplete, autocomplete_position

**Step 2b — Google Suggest Collection (httpx):**
- GET https://suggestqueries.google.com/complete/search?q={seed}&client=firefox
- Parse JSON response for related search suggestions
- Store with source=google_suggest

**Step 2c — LLM Keyword Generation (gpt-4o-mini):**
- Prompt: given seed keyword + niche context, generate 10–20 related keywords, long-tail variants, buyer-intent modifier combinations
- Parse response into list of keyword strings
- Store with source=llm_expansion

**Step 2d — LLM Relevance Filter (gpt-4o-mini):**
- Prompt: given full expanded keyword list, classify each as RELEVANT or IRRELEVANT to the niche
- Remove IRRELEVANT keywords from the list

**Step 2e — LLM Buyer Intent Classification (gpt-4o-mini):**
- Prompt: classify each keyword as INFORMATIONAL / CONSIDERATION / HIGH_INTENT / TRANSACTIONAL
- Store intent_class in keywords table

**Step 2f — Embedding Generation (text-embedding-3-small):**
- Generate semantic embedding vector for every keyword in the expanded universe
- Store embedding_vector (1536-dimension float array) in keywords table

**LLM Calls:**
| Task | Model | Template | Volume |
|---|---|---|---|
| Keyword generation | gpt-4o-mini | stage02_expansion/synonym_generation.j2 | 1 call per seed per niche |
| Relevance filter | gpt-4o-mini | stage02_expansion/relevance_filter.j2 | 1 call per niche (batch) |
| Intent classification | gpt-4o-mini | stage02_expansion/intent_classification.j2 | 1 call per niche (batch) |
| Embeddings | text-embedding-3-small | N/A | 1 call per keyword |

**Data Out:**
```
keywords table rows:
  - keyword_text, niche_id, source, autocomplete_position,
    intent_class, embedding_vector, collected_at, ttl_hours
```

**Checkpoint:** Written after every 50 keywords per niche to data/checkpoints/{run_id}/stage02_{niche_id}.json

---

### STAGE 3 — Fiverr Search Collection

**Trigger:** Stage 2 complete per niche. Jobs processed in priority queue order: CRITICAL (PRD) → HIGH (Slots 5,6,7) → STANDARD (Slots 8,9) → LOW (Slots 2,3) → BACKGROUND (Slot 4).

**Data In:**
```
keywords table (keyword_text, niche_id, intent_class)
NicheJobSpec (depth setting, priority)
fiverr session (data/sessions/fiverr_session.json)
config.yaml → pacing.fiverr_search
```

**Processing per keyword:**
1. Session Manager loads authenticated Playwright context
2. Navigate to fiverr.com/search/gigs?query={keyword_text}
3. Human Events: read_delay(2–8s), random_scroll
4. Collect from search result cards: gig title, gig URL, seller username, seller level badge, rating visible in card, review count if visible, starting price, delivery time, tags shown in card, sponsored flag, position in results
5. Collect total result count for keyword (visible at top of results page)
6. Collect pagination depth (total pages)
7. Human Events: scroll to page 2 if collecting multiple pages
8. Apply pacing delay before next keyword

**Data Out:**
```
search_results table rows:
  - keyword_id, niche_id, gig_url, gig_title, seller_username, seller_level,
    rating_visible, review_count_visible, starting_price, delivery_time,
    tags_visible, sponsored_flag, position, total_result_count,
    pagination_depth, collected_at, ttl_hours
```

**Checkpoint:** Written every 50 search result pages to data/checkpoints/{run_id}/stage03_{niche_id}.json

---

### STAGE 4 — Gig Detail Collection

**Trigger:** Stage 3 complete per niche. Top N gigs per keyword selected (N from NicheJobSpec).

**Data In:**
```
search_results table (top N gig_urls per keyword, ordered by position)
NicheJobSpec (top_n_gigs: 20/10/5/0)
fiverr session
config.yaml → pacing.fiverr_gig_detail
```

**Processing (skipped for keyword_only depth; minimal for feasibility depth):**
1. Select top N gig_urls per keyword from search_results
2. Deduplicate across keywords within the same niche (a gig ranking for multiple keywords is only visited once per TTL)
3. For each gig_url:
   a. Load page in authenticated Playwright context
   b. Human Events: read_delay, scroll, hover simulation
   c. Collect all gig detail fields (see field catalog in Wave 3)
   d. Pacing delay before next gig

**Data Out:**
```
gigs table rows:
  - gig_url, keyword_id (FK), niche_id, seller_username, gig_title_full,
    description_text, packages (JSON array), gig_extras (JSON array), tags,
    faq_text, video_present, portfolio_count, review_count_exact,
    rating_exact, review_snippets (JSON), collected_at, ttl_hours
```

**Checkpoint:** Written every 50 gig pages to data/checkpoints/{run_id}/stage04_{niche_id}.json

---

### STAGE 5 — Competitor Seller Profile Collection

**Trigger:** Stage 4 complete per niche.

**Data In:**
```
gigs table (seller_username list, unique per niche per TTL window)
NicheJobSpec (top_n_sellers)
fiverr session
config.yaml → pacing.fiverr_seller_profile
```

**Processing (skipped for keyword_only depth):**
1. Build unique seller username list from all gigs collected this run
2. Check sellers table: skip any seller whose collected_at is within ttl_hours
3. For each new/stale seller:
   a. Navigate to fiverr.com/{username}
   b. Human Events: read_delay, scroll
   c. Collect seller profile fields
   d. Pacing delay

**Data Out:**
```
sellers table rows:
  - seller_username, seller_level, member_since, response_time, response_rate,
    languages, bio_text, total_reviews, total_gigs, gig_titles (JSON),
    portfolio_count, badges (JSON), collected_at, ttl_hours
```

**Checkpoint:** Written every 25 seller pages to data/checkpoints/{run_id}/stage05_{niche_id}.json

---

### STAGE 6 — External Demand Validation

**Trigger:** Stage 5 complete per niche. All 9 niches processed.

**Data In:**
```
keywords table (seed keywords per niche, grouped by niche)
config.yaml → external_sources per niche (google_trends, reddit, youtube)
config.yaml → pacing.google_trends, pacing.reddit_api
```

**Processing — Google Trends (pytrends):**
1. Batch seed keywords (up to 5 per request)
2. For each batch: call pytrends TrendReq().interest_over_time()
3. Collect 12-month interest score, 3-month score, slope (positive/flat/negative)
4. Collect related_queries and related_topics for top results
5. On 429: pause 10 minutes, retry with exponential backoff
6. Pacing delay between batches

**Processing — Reddit API (praw):**
1. For each niche seed keyword list, search top 5 relevant subreddits
2. Collect: post count, top post titles and body snippets (last 90 days)
3. LLM demand intent parse (gpt-4o-mini): extract demand intent score (0–10) and representative intent phrases

**Processing — YouTube:**
1. For each niche, collect YouTube search result count for primary seed keywords (httpx GET)

**LLM Calls:**
| Task | Model | Template | Volume |
|---|---|---|---|
| Reddit demand intent parse | gpt-4o-mini | stage06_external/reddit_demand_parse.j2 | 1 call per niche |

**Data Out:**
```
external_signals table rows:
  - keyword_id or niche_id (FK), signal_type, signal_source, signal_value,
    signal_details (JSON), llm_demand_intent_score, llm_intent_phrases (JSON),
    collected_at, ttl_hours
```

**Checkpoint:** Written after each niche's external data completes.

---

### STAGE 7 — LLM Gig Quality Analysis

**Trigger:** Stage 6 complete. Run for niches with depth = full or standard (skipped for keyword_only; limited for feasibility).

**Data In:**
```
gigs table (gig_title_full, description_text, packages, tags, faq_text, video_present, portfolio_count)
NicheJobSpec (depth setting → controls top_n for gpt-4o analysis)
LLM cache (checked before every call)
```

**Processing:**

**Step 7a — Title Quality Scoring (gpt-4o-mini, all collected gigs):**
- Score: keyword targeting, clarity, specificity, professionalism (0–100)
- Model: gpt-4o-mini (high volume)

**Step 7b — Description Quality + Weakness Detection (gpt-4o, top N gigs per keyword):**
- N = 10 for full depth, 5 for standard depth
- Quality score: clarity, benefit language, proof elements, CTA strength, differentiation (0–100)
- Weakness list: structured list of exploitable weaknesses per gig
- Model: gpt-4o (nuanced judgment)

**Step 7c — Thumbnail Assessment (gpt-4o-mini, all collected gigs):**
- Classification: PROFESSIONAL_PHOTO / GRAPHIC_DESIGN / TEXT_HEAVY / STOCK_IMAGE / LOW_QUALITY
- Model: gpt-4o-mini

**Step 7d — FAQ Quality Scoring (gpt-4o-mini, all collected gigs with FAQ):**
- Score: completeness, buyer-relevance, specificity (0–100)
- Model: gpt-4o-mini

**LLM Calls:**
| Task | Model | Template | Depth Gate |
|---|---|---|---|
| Title quality | gpt-4o-mini | stage07_gig_quality/title_quality.j2 | standard + full |
| Description quality | gpt-4o | stage07_gig_quality/description_quality.j2 | standard (top 5) + full (top 10) |
| Weakness detection | gpt-4o | stage07_gig_quality/weakness_detection.j2 | standard (top 5) + full (top 10) |
| Thumbnail assessment | gpt-4o-mini | stage07_gig_quality/thumbnail_assessment.j2 | standard + full |
| FAQ quality | gpt-4o-mini | stage07_gig_quality/faq_quality.j2 | standard + full |

**Data Out:**
```
gig_quality_scores table rows:
  - gig_id (FK), keyword_id, niche_id, title_quality_score,
    description_quality_score, weakness_list (JSON), thumbnail_class,
    faq_quality_score, video_absent_flag, portfolio_absent_flag,
    llm_model_used, analyzed_at, confidence_flags (JSON)
```

**Checkpoint:** Written every 50 gigs analyzed.

---

### STAGE 8 — Seller Strength Analysis + Competitor Synthesis

**Trigger:** Stage 7 complete per niche. Skipped for keyword_only depth.

**Data In:**
```
sellers table (bio_text, seller_level, member_since, total_reviews, gig_titles)
keyword_clusters (if Stage 9 has run previously; otherwise uses keyword groupings)
gig_quality_scores (weakness_list per gig, for synthesis input)
NicheJobSpec (depth setting)
```

**Processing:**

**Step 8a — Seller Bio Authority Parsing (gpt-4o-mini):**
- Extract authority signals from bio_text: years of experience, credentials, specialization, portfolio highlights
- Return authority_score (0–10) and authority_signals list

**Step 8b — Per-Cluster Competitor Synthesis (gpt-4o):**
- Input: top 10 competitor profiles per keyword cluster (seller level, reviews, gig titles, pricing, weakness list)
- Output: strategic narrative — who dominates, why they're winning, what positioning gaps exist, entry feasibility rating (0–10)
- One synthesis per cluster, not per keyword (cost control)

**Step 8c — Per-Seller Weakness Identification (gpt-4o):**
- For each top-3 competitor per niche: specific, actionable weaknesses with severity ratings
- Input: full seller profile + their gig quality scores

**LLM Calls:**
| Task | Model | Template | Volume |
|---|---|---|---|
| Bio authority parse | gpt-4o-mini | stage08_competitor/bio_parse.j2 | 1 per seller |
| Cluster synthesis | gpt-4o | stage08_competitor/cluster_synthesis.j2 | 1 per cluster |
| Seller weakness IDs | gpt-4o | stage08_competitor/weakness_identification.j2 | 1 per top-3 seller per niche |

**Data Out:**
```
seller_scores table rows:
  - seller_id (FK), niche_id, authority_score, authority_signals (JSON), analyzed_at

competitor_analysis table rows:
  - cluster_id (FK), niche_id, dominant_sellers (JSON), positioning_gaps (JSON),
    entry_feasibility_rating, synthesis_narrative, analyzed_at
```

---

### STAGE 9 — Keyword Clustering

**Trigger:** Stage 8 complete per niche. Skipped for keyword_only depth.

**Data In:**
```
keywords table (keyword_text, embedding_vector, niche_id, intent_class)
NicheJobSpec (depth setting)
config.yaml → clustering.algorithm (kmeans | dbscan), clustering.n_clusters
```

**Processing:**

**Step 9a — sklearn Clustering:**
- Load embedding vectors for all keywords in niche into numpy array
- Run KMeans (default) or DBSCAN (if configured)
- Assign cluster_id to each keyword

**Step 9b — Cluster Theme Labeling (gpt-4o-mini):**
- For each cluster: send representative keyword samples to gpt-4o-mini
- Receive human-readable cluster theme label (e.g., "PRD — MVP Scoping", "PRD — Technical Roadmap")

**Step 9c — Cluster Opportunity Narrative (gpt-4o):**
- For each cluster: synthesize demand signals, competition signals, and competitor analysis into a strategic opportunity narrative
- One paragraph per cluster

**LLM Calls:**
| Task | Model | Template | Volume |
|---|---|---|---|
| Cluster labeling | gpt-4o-mini | stage09_clustering/cluster_labeling.j2 | 1 per cluster |
| Opportunity narrative | gpt-4o | stage09_clustering/cluster_opportunity_narrative.j2 | 1 per cluster |

**Data Out:**
```
keyword_clusters table rows:
  - keyword_id (FK), niche_id, cluster_id, cluster_label, assigned_at

cluster_analysis table rows:
  - cluster_id, niche_id, cluster_label, keyword_count, opportunity_narrative,
    representative_keywords (JSON), analyzed_at
```

---

### STAGES 10–12 — Scoring, Confidence, and Ranking

**Trigger:** Stage 9 complete per niche. Deterministic Python — no LLM calls.

**Data In:**
```
All tables: keywords, search_results, gigs, sellers, external_signals,
gig_quality_scores, seller_scores, keyword_clusters, cluster_analysis
NicheJobSpec (score_depth: all_11 / scores_1_to_5 / scores_1_to_3)
config.yaml → scoring.active_profile → weights
```

**Stage 10 — Score Calculation:**
- For each keyword, call all score modules appropriate to the niche's score_depth
- Each module returns ScoreResult with score_value and score_components
- Composite Scorer combines into weighted final score

**Stage 11 — Confidence Scoring:**
- For each keyword score, calculate Confidence Modifier based on:
  - data_completeness_ratio (populated fields / required fields)
  - data_freshness_score (age of oldest contributing record vs. TTL)
  - source_diversity_score (how many distinct source types contributed)
  - llm_analysis_completion_ratio (successful LLM calls / attempted)
- Apply modifier: final_score × confidence_modifier

**Stage 12 — Opportunity Ranking:**
- Sort all keywords per niche by adjusted final_score descending
- Apply GO/PASS tags based on config thresholds
- Write to opportunity_rankings table

**Data Out:**
```
keyword_scores table rows (all 11 score fields + components + explanation_inputs)
confidence_scores table rows (modifier value + breakdown + reason)
opportunity_rankings table rows (keyword_id, niche_id, final_score, tag, rank)
```

---

### STAGE 13 — LLM Recommendation Generation

**Trigger:** Stage 12 complete. Run only for keywords tagged STRONG GO or CONDITIONAL GO, in niches with recommendation_generation: true.

**Data In:**
```
opportunity_rankings (STRONG GO and CONDITIONAL GO keywords)
keyword_scores (all score components for context)
gig_quality_scores (weakness list for differentiation angle)
competitor_analysis (synthesis narrative for context)
cluster_analysis (opportunity narrative for context)
external_signals (demand signals for buyer persona)
config.yaml → metadata per niche (pricing, exclusions)
```

**Processing — 11 LLM tasks per recommended keyword:**

| Task | Model | Template |
|---|---|---|
| 5 gig title variants | gpt-4o | stage13_recommendations/gig_titles.j2 |
| 5 tag sets | gpt-4o-mini | stage13_recommendations/tag_sets.j2 |
| Package tier structure | gpt-4o | stage13_recommendations/package_structure.j2 |
| Full description outline | gpt-4o | stage13_recommendations/description_draft.j2 |
| 5–7 FAQ entries | gpt-4o-mini | stage13_recommendations/faq_entries.j2 |
| Differentiation angle | gpt-4o | stage13_recommendations/differentiation_angle.j2 |
| Buyer persona | gpt-4o-mini | stage13_recommendations/buyer_persona.j2 |
| Thumbnail direction | gpt-4o-mini | stage13_recommendations/thumbnail_direction.j2 |
| Upsell structure | gpt-4o-mini | stage13_recommendations/upsell_structure.j2 |
| Red flags | gpt-4o | stage13_recommendations/red_flags.j2 |
| Niche viability assessment | gpt-4o | stage13_recommendations/niche_viability_assessment.j2 |

**Data Out:**
```
recommendations table rows:
  - keyword_id (FK), niche_id, tag, gig_titles (JSON), tag_sets (JSON),
    package_structure (JSON), description_outline (JSON), faq_entries (JSON),
    differentiation_angle, buyer_persona (JSON), thumbnail_direction,
    upsell_structure (JSON), red_flags (JSON), niche_viability_assessment,
    generated_at, llm_cost_usd
```

---

### STAGE 14 — Reporting and Dashboard Refresh

**Trigger:** Stage 13 complete.

**Processing:**

**Step 14a — Score Explanation Generation (gpt-4o):**
- For every keyword with a final score: generate 2–4 sentence plain-English explanation referencing actual score component values
- Template: stage14_reporting/opportunity_explanation.j2

**Step 14b — Trend Narrative (gpt-4o-mini):**
- Per keyword cluster: 1-paragraph trend narrative from Google Trends slope + classification
- Template: stage14_reporting/trend_narrative.j2

**Step 14c — Saturation Narrative (gpt-4o-mini):**
- Per keyword: 1-sentence saturation context
- Template: stage14_reporting/saturation_narrative.j2

**Step 14d — Competitor Landscape Summary (gpt-4o):**
- Per niche: 1-paragraph competitor landscape summary for dashboard Competitors page
- Template: stage14_reporting/competitor_landscape_summary.j2

**Step 14e — Dashboard Refresh:**
- Streamlit dashboard reads from database on demand (no explicit push needed — reads latest on page load)
- Revenue gate tracker updated with latest order data (user-entered)
- LLM cost view updated from llm_usage_logs

**Step 14f — Export Generation:**
- Pandas: write keyword_scores to CSV and Excel (data/exports/keywords_{timestamp}.csv / .xlsx)
- WeasyPrint: render opportunity report PDF from Jinja2 template (data/exports/opportunity_report_{timestamp}.pdf)
- Markdown: write run summary to data/exports/run_summary_{timestamp}.md

**Data Out:**
```
keyword_scores.explanation_text updated
cluster_analysis.trend_narrative updated
keyword_scores.saturation_narrative updated
competitor_analysis.landscape_summary updated
data/exports/ files written
```

---

### STAGE 15 — Run Logging + Auto-Promotion Evaluation

**Trigger:** Stage 14 complete.

**Processing:**

**Step 15a — LLM Run Summary (gpt-4o-mini):**
- Input: run stats (niches processed, keywords expanded, gigs collected, LLM cost, new STRONG GO keywords, top score mover)
- Output: 200–400 word natural language run summary
- Template: stage15_run_summary/run_summary.j2

**Step 15b — Run Log Write:**
- Write complete run record to run_logs table
- Fields: run_id, start_time, end_time, duration_seconds, mode, niches_processed (JSON), keywords_expanded_count, gigs_collected_count, sellers_collected_count, llm_calls_total, llm_cache_hits, llm_cost_usd, errors (JSON), summary_text, new_strong_go_keywords (JSON), next_recommended_action

**Step 15c — Auto-Promotion Evaluation (if run_count >= 3):**
1. Query avg Final Recommendation Score per Tier 2 niche from last 3 run_ids
2. Apply promotion/demotion algorithm
3. Write depth changes to niche_configs table with reason field
4. Log changes to run_logs.auto_promotion_changes (JSON)
5. Emit dashboard notification (stored in run_logs for dashboard to surface)

**Step 15d — Checkpoint Cleanup:**
- Delete all checkpoint files for this run_id from data/checkpoints/{run_id}/

**Data Out:**
```
run_logs table row (complete run record)
niche_configs table (updated depths if auto-promotion ran)
data/checkpoints/{run_id}/ directory cleaned
```

---

## Tier-Aware Data Flow Branching

The following table shows exactly which stages run and at what depth for each niche:

| Stage | PRD (full) | Support-KB (kw_only) | Gumloop (kw_only) | MCP (feasibility) | Slots 5-9 (standard) |
|---|---|---|---|---|---|
| 1: Seed Intake | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| 2: Keyword Expansion | ✅ Full + all LLM | ✅ Expansion + intent only | ✅ Expansion + intent only | ✅ Expansion + intent only | ✅ Full + all LLM |
| 3: Fiverr Search | ✅ All keywords | ✅ All keywords | ✅ All keywords | ✅ All keywords | ✅ All keywords |
| 4: Gig Detail | ✅ Top 20 | ⛔ Skipped | ⛔ Skipped | ✅ Top 5 | ✅ Top 10 |
| 5: Seller Profiles | ✅ Top 20 sellers | ⛔ Skipped | ⛔ Skipped | ✅ Top 5 sellers | ✅ Top 10 sellers |
| 6: External Validation | ✅ All sources | ✅ G-Trends + Reddit | ✅ G-Trends + Reddit | ✅ G-Trends + Reddit | ✅ All sources |
| 7: Gig Quality LLM | ✅ Top 10 (gpt-4o) | ⛔ Skipped | ⛔ Skipped | ✅ gpt-4o-mini only | ✅ Top 5 (gpt-4o) |
| 8: Competitor Synthesis | ✅ Full | ⛔ Skipped | ⛔ Skipped | ⛔ Skipped | ✅ Full |
| 9: Clustering | ✅ Full | ⛔ Skipped | ⛔ Skipped | ⛔ Skipped | ✅ Full |
| 10: Scoring | ✅ All 11 scores | ✅ Scores 1–3 only | ✅ Scores 1–3 only | ✅ Scores 1–5 | ✅ All 11 scores |
| 11: Confidence | ✅ Full | ✅ Partial (thin data) | ✅ Partial (thin data) | ✅ Partial | ✅ Full |
| 12: Ranking | ✅ Full | ✅ Limited (3 scores) | ✅ Limited (3 scores) | ✅ Limited (5 scores) | ✅ Full |
| 13: Recommendations | ✅ For GO keywords | ⛔ Skipped | ⛔ Skipped | ⛔ Skipped | ✅ For GO keywords |
| 14: Reporting | ✅ Full | ✅ Keyword-level only | ✅ Keyword-level only | ✅ Keyword-level only | ✅ Full |
| 15: Run Log | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## LLM Cache Interaction in the Data Flow

At every LLM call point in the flow:

```
[Any Stage with LLM Call]
        │
        ▼
Build prompt from Jinja2 template + context data
        │
        ▼
Compute cache_key = SHA-256(model + str(temperature) + prompt_text)
        │
        ▼
Query llm_cache table WHERE key = cache_key AND expires_at > NOW()
        │
    ┌───┴───┐
   HIT     MISS
    │       │
    ▼       ▼
Return   Call OpenAI/Ollama API
cached   Store response in llm_cache
response Log to llm_usage_logs (cache_hit=True/False)
    │       │
    └───┬───┘
        │
        ▼
Parse response via structured_output.parse_structured()
        │
    ┌───┴───────────┐
  Success       ValidationError
    │               │
    ▼               ▼
Return Pydantic  Retry with self-correction prompt
instance         │
             ┌───┴───────────┐
           Success        2nd Failure
             │               │
             ▼               ▼
         Return Pydantic  Return None
         instance        Log failure
                         Decrement confidence
```
