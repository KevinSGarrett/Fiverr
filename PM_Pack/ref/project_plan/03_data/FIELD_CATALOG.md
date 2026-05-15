# Field Catalog
# Fiverr Research System — Wave 3

**Document Status:** Complete
**Wave:** 3 — Data Schema and Source Design
**Purpose:** Every field across all 21 tables — Python type, SQLAlchemy type, nullable, default, source stage, purpose, validation rule, and notes.

---

## How to Read This Catalog

| Column | Description |
|---|---|
| Field | Column name in the table |
| PY Type | Python type annotation |
| SQL Type | SQLAlchemy column type |
| Nullable | Whether NULL is allowed |
| Default | Default value (if any) |
| Source | Which pipeline stage writes this field |
| Purpose | Why this field exists |
| Validation | Acceptable values or range |
| Notes | Special handling |

---

## TABLE: niche_configs

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| id | int | Integer PK | No | auto | — | Surrogate PK | positive int | — |
| niche_id | str | String(64) | No | — | config.yaml | Unique niche identifier | snake_case, no spaces | Must match config.yaml niches[*].id |
| slot | int | Integer | No | — | config.yaml | Portfolio slot number | 1–9 | — |
| name | str | String(256) | No | — | config.yaml | Human-readable niche name | non-empty string | — |
| tier | int | Integer | No | — | config.yaml | Tier 1 (locked) or Tier 2 (new) | 1 or 2 | — |
| current_depth | str | String(32) | No | keyword_only | Dispatcher / Auto-Promotion | Runtime collection depth | full\|standard\|keyword_only\|feasibility | Initial value from config; updated by Auto-Promotion Evaluator |
| gate_passed | bool | Boolean | No | False | User (manual) | Whether the niche's gate condition is satisfied | true/false | Set manually in config.yaml; synced to DB on run start |
| run_count | int | Integer | No | 0 | Stage 15 | Total completed runs for this niche | >= 0 | Incremented at end of every successful run |
| last_run_at | datetime\|None | DateTime | Yes | None | Stage 15 | When this niche was last processed | valid datetime | — |
| avg_final_score | float\|None | Float | Yes | None | Stage 15 | Rolling avg Final Recommendation Score last 3 runs | 0.0–100.0 | Used by Auto-Promotion Evaluator |
| auto_promotion_eligible | bool | Boolean | No | False | config.yaml | Whether this niche can be auto-promoted | true/false | Tier 2 niches only |
| depth_reason | str\|None | Text | Yes | None | Auto-Promotion | Reason for current depth | free text | e.g., "Auto-promoted run 3: avg score 71.4" |
| updated_at | datetime | DateTime | No | utcnow | ORM onupdate | Last modification timestamp | valid datetime | Auto-updated by SQLAlchemy |

---

## TABLE: run_logs

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| id | int | Integer PK | No | auto | — | Surrogate PK | positive int | — |
| run_id | str | String(36) | No | — | Orchestrator | UUID4 run identifier | UUID4 format | Generated at run start |
| mode | str | String(32) | No | — | Orchestrator | Run mode | full\|collect-only\|analyze-only\|score-only\|report-only\|keyword-only\|resume | — |
| scoring_profile | str\|None | String(64) | Yes | None | Orchestrator | Active scoring profile for this run | must exist in config.scoring.profiles | — |
| started_at | datetime | DateTime | No | — | Orchestrator | Run start timestamp | valid datetime | — |
| completed_at | datetime\|None | DateTime | Yes | None | Stage 15 | Run completion timestamp | valid datetime | Null while run is active |
| duration_seconds | float\|None | Float | Yes | None | Stage 15 | Total run duration | > 0 | — |
| status | str | String(32) | No | RUNNING | Stage 15 | Run status | RUNNING\|COMPLETE\|FAILED\|PARTIAL | — |
| niches_processed | dict\|None | JSON | Yes | None | Orchestrator | Niche IDs and depths used | {"niche_id": "depth"} | — |
| keywords_expanded | int | Integer | No | 0 | Stage 2 | Total keywords in expanded universe | >= 0 | — |
| gigs_collected | int | Integer | No | 0 | Stage 4 | Total gig detail pages collected | >= 0 | — |
| sellers_collected | int | Integer | No | 0 | Stage 5 | Total seller profiles collected | >= 0 | — |
| llm_calls_total | int | Integer | No | 0 | LLM Client | Total LLM API calls made | >= 0 | Includes cache misses only |
| llm_cache_hits | int | Integer | No | 0 | LLM Cache | Total LLM cache hits | >= 0 | — |
| llm_cost_usd | float | Float | No | 0.0 | Cost Monitor | Total LLM API cost for this run | >= 0.0 | — |
| new_strong_go_count | int | Integer | No | 0 | Stage 12 | Keywords newly tagged STRONG GO vs. prior run | >= 0 | — |
| new_strong_go_keywords | list\|None | JSON | Yes | None | Stage 12 | List of new STRONG GO keyword objects | JSON array | — |
| auto_promotion_ran | bool | Boolean | No | False | Stage 15 | Whether auto-promotion evaluated this run | true/false | True only when run_count >= 3 |
| auto_promotion_changes | list\|None | JSON | Yes | None | Stage 15 | Depth changes made by auto-promotion | JSON array | — |
| errors | list\|None | JSON | Yes | None | All stages | Error log from dead-letter jobs | JSON array | — |
| errors_count | int | Integer | No | 0 | All stages | Count of error events | >= 0 | — |
| dead_letter_count | int | Integer | No | 0 | Job Queue | Count of jobs moved to dead-letter | >= 0 | — |
| summary_text | str\|None | Text | Yes | None | Stage 15 LLM | gpt-4o-mini run summary | non-empty string | — |
| next_recommended_action | str\|None | Text | Yes | None | Stage 15 LLM | LLM-suggested next action | non-empty string | — |

---

## TABLE: jobs

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| id | int | Integer PK | No | auto | — | Surrogate PK | positive int | — |
| job_id | str | String(36) | No | — | Orchestrator | UUID4 job identifier | UUID4 | Generated at job creation |
| run_id | str | String(36) FK | No | — | Orchestrator | Parent run reference | valid run_id | CASCADE DELETE |
| job_type | str | String(64) | No | — | Orchestrator | Job type from taxonomy | valid job type string | e.g., GIG_DETAIL, RECOMMEND_TITLES |
| stage | int | Integer | No | — | Orchestrator | Pipeline stage number | 1–15 | — |
| niche_id | str | String(64) FK | No | — | Orchestrator | Target niche | valid niche_id | — |
| priority | str | String(16) | No | — | Dispatcher | Queue priority tier | CRITICAL\|HIGH\|STANDARD\|LOW\|BACKGROUND | — |
| status | str | String(16) | No | QUEUED | Job Queue | Current job status | QUEUED\|RUNNING\|COMPLETE\|FAILED\|DEAD_LETTER\|SKIPPED | — |
| payload | dict\|None | JSON | Yes | None | Orchestrator | Job-specific input data | valid JSON dict | e.g., {"gig_url": "..."} |
| result_ref | str\|None | String(128) | Yes | None | Job executor | Pointer to output record | "table:row_id" format | e.g., "gigs:12345" |
| retry_count | int | Integer | No | 0 | Job Queue | Retry attempts made | 0–max_retries | — |
| max_retries | int | Integer | No | 3 | Job Queue | Max retry attempts | 1–10 | Configurable per job type |
| error_log | list\|None | JSON | Yes | None | Job executor | Error messages per attempt | JSON array of strings | — |
| checkpoint_ref | str\|None | String(256) | Yes | None | Checkpoint Mgr | Checkpoint file path | valid file path | — |
| created_at | datetime | DateTime | No | — | Orchestrator | Job creation timestamp | valid datetime | — |
| started_at | datetime\|None | DateTime | Yes | None | Job executor | When job began executing | valid datetime | — |
| completed_at | datetime\|None | DateTime | Yes | None | Job executor | When job finished | valid datetime | — |
| duration_seconds | float\|None | Float | Yes | None | Job executor | Execution duration | > 0 | — |

---

## TABLE: keywords

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| id | int | Integer PK | No | auto | — | Surrogate PK | positive int | — |
| keyword_text | str | String(512) | No | — | Stage 2 | The keyword string | non-empty, <= 512 chars | Stripped of whitespace |
| niche_id | str | String(64) FK | No | — | Stage 2 | Parent niche | valid niche_id | — |
| source | str | String(32) | No | — | Stage 2 | How keyword was obtained | seed\|fiverr_autocomplete\|google_suggest\|llm_expansion | — |
| autocomplete_position | int\|None | Integer | Yes | None | Stage 2 | Position in Fiverr autocomplete | 1–10 | Null if not from autocomplete |
| intent_class | str\|None | String(32) | Yes | None | Stage 2 LLM | Buyer intent classification | INFORMATIONAL\|CONSIDERATION\|HIGH_INTENT\|TRANSACTIONAL | — |
| intent_model_used | str\|None | String(64) | Yes | None | Stage 2 LLM | Model that classified intent | valid model ID | — |
| cluster_id | int\|None | Integer FK | Yes | None | Stage 9 | Assigned cluster | valid cluster_id | Set after clustering runs |
| embedding_vector | list\|None | JSON | Yes | None | Stage 2 | 1536-dim float array | list of 1536 floats | pgvector in v2 PostgreSQL |
| embedding_model_used | str\|None | String(64) | Yes | None | Stage 2 | Embedding model ID | valid model ID | — |
| is_active | bool | Boolean | No | True | Stage 1 | Whether keyword is still in active seeds | true/false | Set False for retired seeds |
| collected_at | datetime | DateTime | No | — | Stage 2 | When keyword was expanded | valid datetime | — |
| ttl_hours | int | Integer | No | 168 | Stage 2 | Freshness TTL | 24–720 | 168 = 7 days |

---

## TABLE: search_results

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| id | int | Integer PK | No | auto | — | Surrogate PK | positive int | — |
| keyword_id | int FK | Integer | No | — | Stage 3 | Parent keyword | valid keyword id | CASCADE DELETE |
| niche_id | str | String(64) | No | — | Stage 3 | Niche context | valid niche_id | Denormalized for fast queries |
| run_id | str FK | String(36) | No | — | Stage 3 | Parent run | valid run_id | — |
| total_result_count | int\|None | Integer | Yes | None | Stage 3 | Total Fiverr results for keyword | >= 0 | Key Demand Score input |
| pagination_depth | int\|None | Integer | Yes | None | Stage 3 | Number of result pages | >= 1 | — |
| gig_cards | list\|None | JSON | Yes | None | Stage 3 | All gig card data from search results | JSON array | See gig_cards field structure below |
| collected_at | datetime | DateTime | No | — | Stage 3 | When search was run | valid datetime | — |
| ttl_hours | int | Integer | No | 72 | Stage 3 | Freshness TTL | 24–168 | 72 = 3 days |

**gig_cards JSON element structure:**
```json
{
  "gig_url": "https://www.fiverr.com/...",
  "gig_title": "I will write a developer-ready AI SaaS MVP PRD",
  "seller_username": "example_seller",
  "seller_level": "Level 2",
  "rating_visible": 4.9,
  "review_count_visible": 847,
  "review_count_abbreviated": false,
  "starting_price": 95.0,
  "delivery_time": "3 days",
  "tags_visible": ["PRD", "AI SaaS", "MVP"],
  "sponsored_flag": false,
  "orders_in_queue_visible": null,
  "position": 1
}
```

---

## TABLE: gigs (Key Fields Only — Full Definition in SCHEMA.md)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| gig_url | str | String(512) UNIQUE | No | — | Stage 3/4 | Unique gig identifier | valid Fiverr URL | — |
| description_text | str\|None | Text | Yes | None | Stage 4 | Full gig description | non-empty | Null if detail not collected |
| packages | list\|None | JSON | Yes | None | Stage 4 | All package tiers | JSON array of package objects | — |
| tags | list\|None | JSON | Yes | None | Stage 4 | Fiverr gig tags | JSON array of strings, max 5 | — |
| review_count_exact | int\|None | Integer | Yes | None | Stage 4 | Exact review count from detail page | >= 0 | More reliable than search card value |
| orders_in_queue | int\|None | Integer | Yes | None | Stage 4 | Queue depth (OQ-003) | >= 0 | Null when Fiverr does not show this field |
| detail_collected | bool | Boolean | No | False | Stage 4 | Whether full detail was collected | true/false | False = search card data only |
| ttl_hours | int | Integer | No | 120 | Stage 4 | Freshness TTL | 24–336 | 120=5 days; top gigs may use shorter TTL |

---

## TABLE: external_signals (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| signal_type | str | String(32) | No | — | Stage 6 | Type discriminator | google_trends\|reddit_demand\|youtube_count | — |
| trends_12mo_score | float\|None | Float | Yes | None | Stage 6 | Google Trends 12-month score | 0.0–100.0 | Null when Trends unavailable |
| trends_slope | str\|None | String(16) | Yes | None | Stage 6 | Trend direction | RISING\|FLAT\|DECLINING\|STRONGLY_RISING\|STRONGLY_DECLINING | — |
| reddit_demand_intent_score | float\|None | Float | Yes | None | Stage 6 LLM | LLM-scored buyer intent | 0.0–10.0 | gpt-4o-mini |
| ttl_hours | int | Integer | No | 24 | Stage 6 | Freshness TTL | 12–72 | 24h for Trends, 72h for Reddit |

---

## TABLE: gig_quality_scores (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| title_quality_score | float\|None | Float | Yes | None | Stage 7 LLM | Overall title quality | 0.0–100.0 | gpt-4o-mini |
| description_quality_score | float\|None | Float | Yes | None | Stage 7 LLM | Overall description quality | 0.0–100.0 | gpt-4o; only top N gigs |
| weakness_list | list\|None | JSON | Yes | None | Stage 7 LLM | Exploitable weaknesses | JSON array | Each item has weakness, severity, description |
| weakness_count | int\|None | Integer | Yes | None | Stage 7 LLM | Count of identified weaknesses | >= 0 | — |
| thumbnail_class | str\|None | String(32) | Yes | None | Stage 7 LLM | Thumbnail type | PROFESSIONAL_PHOTO\|GRAPHIC_DESIGN\|TEXT_HEAVY\|STOCK_IMAGE\|LOW_QUALITY | gpt-4o-mini |
| faq_quality_score | float\|None | Float | Yes | None | Stage 7 LLM | FAQ completeness/quality | 0.0–100.0 | gpt-4o-mini |
| review_velocity_30d | float\|None | Float | Yes | None | Stage 7 | Estimated reviews/30 days | >= 0.0 | Proxy for orders_in_queue when null |
| overall_weakness_score | float\|None | Float | Yes | None | Stage 7 | Composite weakness score | 0.0–10.0 | Higher = weaker competitor = more opportunity |
| analysis_complete | bool | Boolean | No | False | Stage 7 | All LLM tasks succeeded | true/false | False reduces confidence score |

---

## TABLE: keyword_scores (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| demand_score | float\|None | Float | Yes | None | Stage 10 | Demand score | 0.0–100.0 | Available at all depths |
| competition_score | float\|None | Float | Yes | None | Stage 10 | Competition score | 0.0–100.0 | Available at all depths |
| opportunity_score | float\|None | Float | Yes | None | Stage 10 | Net opportunity | 0.0–100.0 | Available at all depths |
| feasibility_score | float\|None | Float | Yes | None | Stage 10 | New seller feasibility | 0.0–100.0 | Null for keyword_only depth |
| weakness_score | float\|None | Float | Yes | None | Stage 10 | Gig quality weakness | 0.0–100.0 | Null for keyword_only depth |
| final_score | float\|None | Float | Yes | None | Stage 11 | weighted_composite × confidence_modifier | 0.0–100.0 | Primary ranking field |
| confidence_modifier | float\|None | Float | Yes | None | Stage 11 | Data quality multiplier | 0.0–1.0 | — |
| score_components | dict\|None | JSON | Yes | None | Stage 10 | Per-score input breakdown | JSON dict | Full audit trail |
| explanation_text | str\|None | Text | Yes | None | Stage 14 LLM | Human-readable score explanation | non-empty string | gpt-4o |
| red_flags | list\|None | JSON | Yes | None | Stage 14 LLM | Warning signals | JSON array | Each item has flag_type, description, severity |
| scored_at | datetime | DateTime | No | — | Stage 10 | When scoring ran | valid datetime | — |
| data_as_of | datetime\|None | DateTime | Yes | None | Stage 10 | Oldest contributing data record | valid datetime | For freshness display |

---

## TABLE: opportunity_rankings (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| tag | str | String(32) | No | — | Stage 12 | GO/PASS decision label | STRONG GO\|CONDITIONAL GO\|MONITOR\|CAUTION\|PASS | — |
| rank | int | Integer | No | — | Stage 12 | Rank within niche | >= 1 | 1 = highest scoring in niche |
| rank_global | int\|None | Integer | Yes | None | Stage 12 | Rank across all niches | >= 1 | 1 = highest scoring across all 9 niches |

---

## TABLE: recommendations (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| gig_titles | list\|None | JSON | Yes | None | Stage 13 LLM | 5 gig title variants | JSON array of 5 strings | gpt-4o |
| tag_sets | list\|None | JSON | Yes | None | Stage 13 LLM | 5 tag set options | JSON array of 5 arrays | gpt-4o-mini |
| package_structure | dict\|None | JSON | Yes | None | Stage 13 LLM | Starter/standard/premium packages | JSON dict | gpt-4o |
| description_outline | dict\|None | JSON | Yes | None | Stage 13 LLM | Gig description structure | JSON dict with sections | gpt-4o |
| differentiation_angle | str\|None | Text | Yes | None | Stage 13 LLM | Unique positioning statement | non-empty string | gpt-4o |
| niche_viability_assessment | str\|None | Text | Yes | None | Stage 13 LLM | Strategic viability paragraph | 100–300 words | gpt-4o |
| llm_cost_usd | float\|None | Float | Yes | None | Stage 13 | Total LLM cost for all 11 tasks | >= 0.0 | — |
| generation_complete | bool | Boolean | No | False | Stage 13 | All 11 LLM tasks completed | true/false | False if any task failed |

---

## TABLE: llm_cache (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| cache_key | str | String(64) UNIQUE | No | — | LLM Cache | SHA-256 of model+temp+prompt | 64-char hex string | — |
| response_json | str | Text | No | — | LLM Cache | Full API response | valid JSON string | Compressed in v2 for large responses |
| expires_at | datetime | DateTime | No | — | LLM Cache | When cache entry expires | valid datetime | = created_at + ttl_hours |
| cache_hits_count | int | Integer | No | 0 | LLM Cache | How many times this entry was served | >= 0 | Useful for identifying high-value cache entries |
| source_data_hash | str\|None | String(64) | Yes | None | LLM Cache | Hash of contributing source data | 64-char hex string | When source data refreshes, this hash changes → invalidation |

---

## TABLE: orders (Key Fields)

| Field | PY Type | SQL Type | Nullable | Default | Source | Purpose | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| gross_usd | float | Float | No | — | User entry | Order gross value | > 0.0 | Pre-Fiverr-fee amount |
| net_usd | float | Float | No | — | Calculated | Order net value | > 0.0 | = gross_usd × (1 - fiverr_share) |
| trust_stage | str\|None | String(32) | Yes | None | User entry | Trust stage at time of order | 0_reviews\|1_4_orders\|5_plus_orders\|level_1\|10_plus_reviews | Used for revenue model tracking |
