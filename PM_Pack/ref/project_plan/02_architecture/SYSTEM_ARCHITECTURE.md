# System Architecture
# Fiverr Research System — Wave 2

**Document Status:** Complete
**Wave:** 2 — Technical Architecture
**Scope:** Full component map for the 9-niche automated research system with LLM Intelligence Layer, Niche Depth Dispatcher, Auto-Promotion Evaluator, and 5-tier job queue.

---

## Architecture Overview

The system is organized into 7 primary layers, each with defined responsibilities and clean interfaces. Data flows from configuration through collection, analysis, scoring, and recommendation into the database and dashboard. The LLM Intelligence Layer operates as a first-class cross-cutting component that serves every stage that needs it.

```
╔══════════════════════════════════════════════════════════════════╗
║                    CONFIGURATION LAYER                          ║
║   config.yaml  ·  .env  ·  niche_configs table                  ║
╚══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════╗
║                    ORCHESTRATION LAYER                          ║
║  run.py (mode router)  ·  APScheduler (cron/manual trigger)     ║
║  Niche Depth Dispatcher  ·  Auto-Promotion Evaluator            ║
║  Checkpoint Manager  ·  Run Logger                              ║
╚═══════════╦═══════════╦═════════════╦═══════════════════════════╝
            │           │             │
            ▼           ▼             ▼
╔═══════════════╗ ╔═══════════════╗ ╔═══════════════╗ ╔═══════════╗
║  COLLECTION   ║ ║   ANALYSIS    ║ ║   SCORING     ║ ║ REPORTING ║
║    LAYER      ║ ║    LAYER      ║ ║    LAYER      ║ ║   LAYER   ║
║               ║ ║               ║ ║               ║ ║           ║
║ Playwright    ║ ║ Pandas        ║ ║ 11 Python     ║ ║ Streamlit ║
║ Auth Session  ║ ║ Polars        ║ ║ scoring fns   ║ ║ PDF/Excel ║
║ httpx         ║ ║ spaCy         ║ ║ Confidence    ║ ║ CSV/MD    ║
║ pytrends      ║ ║ sklearn       ║ ║ Modifier      ║ ║ Alerts    ║
║ Reddit API    ║ ║               ║ ║               ║ ║ Run Logs  ║
╚═══════════════╝ ╚═══════════════╝ ╚═══════════════╝ ╚═══════════╝
            │           │             │                     │
            └─────────────────────────────────────────────┘
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════╗
║               LLM INTELLIGENCE LAYER (first-class)             ║
║  OpenAI API  ·  gpt-4o  ·  gpt-4o-mini  ·  text-embedding-3s   ║
║  Ollama (offline alt)  ·  Jinja2 Prompt Templates              ║
║  LLM Cache (SQLite, SHA-256)  ·  Token Usage Logger            ║
║  Structured Output Parser (JSON mode + Pydantic + retry)        ║
╚══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════╗
║                      DATABASE LAYER                             ║
║  SQLite (v1)  ·  PostgreSQL (v2)  ·  SQLAlchemy 2.0 ORM        ║
║  Alembic Migrations  ·  Pydantic v2 Schemas                     ║
╚══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔══════════════════════════════════════════════════════════════════╗
║                    DASHBOARD LAYER                              ║
║  Streamlit (v1, localhost:8501)  ·  Plotly charts              ║
║  React + FastAPI (v2)  ·  WeasyPrint PDF  ·  Pandas exports     ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Component Catalog

### Configuration Layer

**config.yaml**
- Responsibilities: All tunable system parameters. 9 niche profiles with seeds, depths, gates, pricing, category paths. Scoring weights and named profiles. Pacing settings per source. LLM provider and model settings. Revenue gate targets.
- Interface: Read by Config Loader on startup. Validated by Pydantic model. Never written by the application (user-managed only).
- Key constraint: Single source of truth. No business logic reads from environment variables directly — all config is mediated through config.yaml + .env.

**.env**
- Responsibilities: Secrets only. OPENAI_API_KEY, Fiverr credentials (email, password for initial login reference), any third-party API keys.
- Interface: Loaded by python-dotenv into environment at startup. Referenced in config.yaml via ${OPENAI_API_KEY} syntax.
- Security: Always in .gitignore. Never logged.

**niche_configs table (database)**
- Responsibilities: Runtime niche state that changes without user editing config.yaml. Stores current depth per niche (updated by Auto-Promotion Evaluator), gate_passed status, run count, last run timestamp, avg scores per niche.
- Interface: Written by Orchestrator and Auto-Promotion Evaluator. Read by Niche Depth Dispatcher. Config.yaml depth setting is the initial value; niche_configs table stores the live value.

---

### Orchestration Layer

**run.py (Mode Router)**
- Responsibilities: Entry point for all runs. Parses --mode flag. Routes to the correct pipeline subset. Initializes the database session, config loader, and job queue. Triggers the scheduler or runs immediately depending on mode.
- Modes handled: full, collect-only, analyze-only, score-only, report-only, keyword-only, resume, relogin, generate-niche-profile.
- Interface: CLI entry point. Returns exit code 0 on success, 1 on failure.

**APScheduler**
- Responsibilities: Cron-style scheduled runs. In-process scheduler (no external broker needed for v1). Reads schedule from config.yaml.
- Configuration: `scheduler.cron: "0 23 * * 0"` (every Sunday at 11pm by default, fully configurable).
- Interface: Triggers run.py --mode full on schedule. Logs scheduled run start/end to run_logs table.

**Niche Depth Dispatcher**
- Responsibilities: At the start of each run, reads the current depth for each niche from the niche_configs table. Assigns each niche's collection, analysis, and scoring jobs the correct depth-tier parameters. Routes jobs to the priority queue with the correct priority tier.
- Decision table:

| Depth | Collection | LLM Analysis | Scoring | Queue Priority |
|---|---|---|---|---|
| full | Top 20 gigs + all sellers | gpt-4o + gpt-4o-mini on top 10 gigs | All 11 scores | By niche slot (Slot 1 = CRITICAL) |
| standard | Top 10 gigs + top sellers | gpt-4o on top 5, gpt-4o-mini on top 10 | All 11 scores | HIGH or STANDARD |
| keyword_only | Search results only | Keyword expansion + intent only | Scores 1–3 | LOW |
| feasibility | Top 5 gig detail only | gpt-4o-mini only | Scores 1–5 | BACKGROUND |

- Interface: Receives niche list + config. Returns annotated job specs for each niche. Does not write to database — only reads depth and returns job routing instructions.

**Auto-Promotion Evaluator**
- Responsibilities: After every completed run (run 3+), evaluates Tier 2 niche scores and adjusts depth in niche_configs table. Logs all changes. Emits dashboard notifications.
- Trigger: Runs automatically at the end of Stage 15 (Run Logging) when run_count >= 3.
- Algorithm:
  1. Query avg Final Recommendation Score per Tier 2 niche from last 3 completed runs
  2. Sort Tier 2 niches by avg score descending
  3. Top 2 niches with avg score >= promote_threshold (default 65.0): set depth = full
  4. Bottom niche with avg score < demote_threshold (default 35.0): set depth = keyword_only
  5. Remaining niches: set depth = standard
  6. Write changes to niche_configs table with reason field
  7. Log changes to run_logs
- Interface: Reads from keyword_scores and niche_configs. Writes to niche_configs. Returns list of changes for dashboard notification.

**Checkpoint Manager**
- Responsibilities: Writes checkpoint files every 50 records during collection. Reads checkpoints on --mode resume to determine where to restart. Cleans up checkpoint files after successful run completion.
- Checkpoint file format: JSON at data/checkpoints/{run_id}/{stage_name}.json
  - Fields: run_id, stage, niche_id, last_keyword_id, last_gig_id, queue_position, collected_count, timestamp
- Interface: Called by Collection Layer modules. Also called by Orchestrator on --mode resume.

**Run Logger**
- Responsibilities: Creates run record at start. Updates run record throughout. Writes final run summary (LLM-generated) at Stage 15. Stores structured run stats.
- Interface: Writes to run_logs table. Called by Orchestrator at start/end and by each stage on completion.

---

### Collection Layer

**Session Manager** (src/collection/session_manager.py)
- Responsibilities: All Playwright browser lifecycle management. Loads saved session from disk. Verifies session validity after load. Triggers headed re-login when session is expired or missing. Saves new session state to disk. Attaches human-event simulation to every page.
- Interface: Returns an active, verified Playwright browser_context ready for use by all collection modules.

**Human Events Module** (src/collection/human_events.py)
- Responsibilities: Attaches to Playwright pages and simulates natural human browsing behavior on all Fiverr sessions.
- 5 behaviors: random_scroll, hover_before_click, read_delay, dead_navigation, random_viewport.
- Interface: `attach_human_events(page)` call made on every new page. Returns page with event handlers attached.

**Keyword Expander** (src/collection/keyword_expander.py)
- Responsibilities: Stage 2. For each niche, runs Fiverr autocomplete collection + Google suggest collection + LLM keyword generation + LLM relevance filter + LLM intent classification + embedding generation.
- Interface: Input: niche config (seeds, depth). Output: expanded keyword list written to keywords table with intent_class and embedding_vector fields.

**Fiverr Search Collector** (src/collection/fiverr_search.py)
- Responsibilities: Stage 3. For each keyword, runs authenticated Fiverr search and collects all search result card data. Respects pacing config. Writes to search_results table.
- Interface: Input: keyword list + niche depth. Output: search_results rows.

**Gig Detail Collector** (src/collection/gig_detail.py)
- Responsibilities: Stage 4. Visits gig detail pages for top N gigs per keyword (N determined by depth from Niche Depth Dispatcher). Collects all detailed gig fields.
- Interface: Input: search_results list + top_n per depth. Output: gigs table rows.

**Seller Profile Collector** (src/collection/seller_profile.py)
- Responsibilities: Stage 5. Visits seller profile pages for all unique sellers across collected gigs. Deduplicates across niches within TTL window.
- Interface: Input: unique seller username list. Output: sellers table rows.

**External Source Connectors** (src/collection/external/)
- google_trends.py: pytrends wrapper with batching (5 seeds/request), rate limit handling, 429 backoff.
- reddit.py: Reddit API wrapper. Subreddit search per keyword. Rate limit respect.
- youtube.py: YouTube search result count collection.
- Interface: Each connector returns rows for external_signals table with signal_type field.

---

### Analysis Layer

**Gig Quality Analyzer** (src/analysis/gig_quality_analyzer.py)
- Responsibilities: Stage 7. Orchestrates all LLM gig quality tasks: title scoring (gpt-4o-mini, all gigs), description quality + weakness detection (gpt-4o, top N), thumbnail assessment (gpt-4o-mini), FAQ scoring (gpt-4o-mini).
- Interface: Input: gigs list + depth setting. Output: gig_quality_scores table rows.

**Seller Strength Analyzer** (src/analysis/seller_strength.py)
- Responsibilities: Stage 8. Bio parsing (gpt-4o-mini) + cluster synthesis (gpt-4o) + per-seller weakness identification (gpt-4o).
- Interface: Input: sellers + keyword clusters. Output: seller_scores + competitor_analysis table rows.

**Keyword Clusterer** (src/analysis/keyword_clusterer.py)
- Responsibilities: Stage 9. Uses pre-computed embeddings + sklearn KMeans/DBSCAN + gpt-4o-mini labeling + gpt-4o opportunity narrative.
- Interface: Input: keywords with embedding_vector. Output: keyword_clusters + cluster_analysis table rows.

---

### Scoring Layer

**Composite Scorer** (src/scoring/composite_scorer.py)
- Responsibilities: Orchestrates Stages 10–12. Calls individual score modules. Applies Confidence Modifier. Applies GO/PASS tags. Writes to keyword_scores, confidence_scores, opportunity_rankings tables.
- Interface: Input: all collected + analyzed data for a keyword. Output: complete score record with all 11 scores and explanation fields.

**Individual Score Modules** (src/scoring/*.py)
- One module per score: demand_score.py, competition_score.py, opportunity_score.py, new_seller_feasibility.py, profitability_score.py, conversion_intent.py, saturation_score.py, gig_quality_weakness.py, trend_score.py, confidence_score.py.
- Interface: Each module receives all relevant data fields and returns a ScoreResult Pydantic model with score_value, score_components, and explanation_inputs.

---

### LLM Intelligence Layer

**LLM Client** (src/llm/client.py)
- Responsibilities: Unified wrapper for OpenAI API and Ollama. Routes model selection based on config tier. Handles API key injection. Manages rate limiting (TPM ceiling). Returns raw API response.
- Interface: `llm_client.complete(prompt, model, temperature, response_format)` → raw response dict.

**LLM Cache** (src/llm/cache.py)
- Responsibilities: Before every LLM call, checks llm_cache table for a matching entry (key = SHA-256 of model + temperature + prompt). On hit: returns cached response without API call. On miss: calls API, stores response.
- Interface: `cache.get(key)` → cached response or None. `cache.set(key, response, ttl)` → stored.

**Structured Output Parser** (src/llm/structured_output.py)
- Responsibilities: Enforces JSON mode on every structured LLM call. Parses raw response into Pydantic model. On ValidationError: appends self-correction prompt and retries once. On second failure: returns None and logs failure for confidence score deduction.
- Interface: `parse_structured(prompt, response_model, model, temperature)` → Pydantic instance or None.

**Cost Monitor** (src/llm/cost_monitor.py)
- Responsibilities: Logs every LLM call to llm_usage_logs table with model, prompt_tokens, completion_tokens, cost_usd (calculated from known pricing), stage, niche_id, run_id, cache_hit flag. Checks daily spend against alert threshold after each call. Triggers alert if threshold exceeded.
- Interface: `cost_monitor.log(call_metadata)` called after every LLM call by the client.

**Prompt Templates** (src/llm/prompts/)
- Responsibilities: Jinja2 template files organized by stage and task. No prompt strings in business logic code.
- Interface: `load_prompt(stage, task, context_dict)` → rendered prompt string.

---

### Database Layer

**SQLAlchemy ORM Models** (src/models/)
- One file per table. All models inherit from Base.
- Key tables: keywords, search_results, gigs, sellers, external_signals, gig_quality_scores, seller_scores, keyword_clusters, cluster_analysis, keyword_scores, confidence_scores, opportunity_rankings, recommendations, llm_cache, llm_usage_logs, run_logs, niche_configs.

**Alembic Migrations** (alembic/versions/)
- All schema changes managed through Alembic. `alembic upgrade head` on first run creates all tables.

**Pydantic v2 Schemas** (src/schemas/)
- Data transfer objects between modules. Validates data at layer boundaries.
- Key schemas: NicheConfig, KeywordRecord, GigRecord, SellerRecord, ScoreResult, RecommendationOutput, RunSummary.

---

### Dashboard Layer

**Streamlit App** (dashboard/app.py + dashboard/pages/)
- 6 pages: Opportunities, Keywords, Competitors, Recommendations, Run History, LLM Costs.
- Reads directly from database via dashboard_data.py query functions.
- Revenue gate tracker on Run History page.
- Auto-Promotion notifications on Opportunities page.

---

## Key Design Contracts

### Niche Depth Dispatcher → Collection Layer

```python
# NicheJobSpec — passed from Dispatcher to each collection module
class NicheJobSpec(BaseModel):
    niche_id: str
    slot: int
    tier: int
    depth: Literal["full", "standard", "keyword_only", "feasibility"]
    top_n_gigs: int              # 20 / 10 / 0 / 5
    top_n_sellers: int           # 20 / 10 / 0 / 5
    priority: Literal["CRITICAL", "HIGH", "STANDARD", "LOW", "BACKGROUND"]
    run_gig_quality_llm: bool    # True for standard+full
    run_competitor_synthesis: bool  # True for standard+full
    run_recommendations: bool    # True for full and configured standard
    score_depth: Literal["all_11", "scores_1_to_5", "scores_1_to_3"]
```

### LLM Client → Structured Output Parser

```python
# All structured LLM calls use this pattern
result = structured_output.parse_structured(
    prompt=load_prompt("stage07", "description_quality", {"gig": gig_data}),
    response_model=GigDescriptionQualityResult,
    model=config.llm.models.tier_high,
    temperature=0.2,
)
# result is GigDescriptionQualityResult or None (on failure)
# None triggers confidence deduction in scoring
```

### Scoring Layer → Database

```python
# ScoreResult written to keyword_scores table
class ScoreResult(BaseModel):
    keyword_id: int
    niche_id: str
    demand_score: float
    competition_score: float
    opportunity_score: float
    feasibility_score: float
    profitability_score: float
    intent_score: float
    saturation_score: float
    weakness_score: float
    trend_score: float
    final_score: float
    confidence_modifier: float
    tag: Literal["STRONG GO", "CONDITIONAL GO", "MONITOR", "CAUTION", "PASS"]
    score_components: dict       # full breakdown per score
    explanation_text: str        # gpt-4o generated
    red_flags: list[dict]
    missing_data_warnings: list[str]
    source_evidence: list[str]
    confidence_reason: str
    niche_tier: str
    scored_at: datetime
    data_as_of: datetime
```

---

## Technology Dependency Map

```
Python 3.11+
├── playwright (+ playwright-stealth)    → Session Manager, all Fiverr collection
├── httpx                                → External source connectors
├── selectolax / BeautifulSoup           → HTML parsing
├── pytrends                             → Google Trends connector
├── praw                                 → Reddit API connector
├── openai                               → LLM Client (primary)
├── ollama                               → LLM Client (offline alt)
├── sqlalchemy 2.0                       → All database access
├── alembic                              → Database migrations
├── pydantic v2                          → All schemas + structured output
├── pandas + polars                      → Tabular analysis
├── spacy                                → Text preprocessing, NER
├── scikit-learn                         → Keyword clustering (KMeans/DBSCAN)
├── jinja2                               → Prompt templates + report templates
├── apscheduler                          → Scheduled runs (v1)
├── fastapi + uvicorn                    → API layer (v2 dashboard)
├── streamlit                            → v1 dashboard
├── plotly                               → Charts (Streamlit + React)
├── weasyprint                           → PDF export
├── openpyxl                             → Excel export
└── pyyaml + python-dotenv               → Config + secrets
```


---

## SRDI ADDENDUM -- New Pipeline Stages and Hardened Components
**Source:** WAVE_A (architecture) + WAVE_B through WAVE_L (per-epic)
**Implemented:** Cycle 049 (2026-05-29)

### Updated Pipeline (Post-SRDI)

New stages marked NEW; hardened stages marked (updated).

```
Stage 3  Fiverr Search (updated)
         + category-constrained URL via search_url_builder.py (R1)
         + search_strictness_used recorded on SearchResult
         + sponsored_gig_count, organic_gig_count stored
         + pages_collected stored

Stage 3.5 Result-Set Validation [NEW -- R2]
         Runs per-niche immediately after Stage 3, before Stage 4.
         - compute_gig_relevance() scores each gig title 0.0-1.0
         - validate_result_set() aggregates to keyword-level RSV score
         - ghost_market_flag when relevance < 0.20 AND total > 5 (or 0 cards)
         - category_contamination_flag when relevance < 0.60 AND total >= 5
         - confidence_deduction tiered 0.0 to -0.50
         - ResultSetValidation row written per (keyword_id, run_id)
         - UNIQUE constraint prevents duplicates; idempotent on re-run
         - Fail-soft: Stage 3.5 error on one keyword does not abort run

Stage 4  Gig Detail (updated)
         + is_sponsored propagated from gig_cards JSON (R3)
         + last_reviewed_at extracted from review snippets (R3)
         + category_path stored (R3)

Stage 4.5 Zombie Detection [NEW -- R3]
         Runs as sub-step of Stage 4, per gig.
         - compute_zombie_score() rates abandonment 0.0-1.0
         - New-seller disambiguation: account < 180 days old = NOT zombie
         - Threshold 0.50 -> Gig.is_zombie = True
         - zombie_score and zombie_signals JSON stored

Stage 5  Seller Profile (updated)
         + specialization fields for R4 competitor profiling
         + last-active signals (feeds zombie detection)

Stage 6  External Signals (updated)
         + fiverr_relevance_qualifier computed and stored (R7)
         + signal_quality_score = sqrt(freshness x relevance) stored (R7)
         + Trends slope modifiers + buying-intent related-query analysis
         + Reddit buyer-intent ratio computed and stored
         + YouTube used for confidence only (weight = 0 in demand)

Stage 7  Gig Quality LLM (unchanged trigger)
         Consumes relevance_flag from Stage 3.5 in R5 rubric pre-check

Stage 7.5 LLM Relevance Gate [NEW -- R5, conditional]
         Only fires when:
           RSV 0.35-0.75 AND final_score >= 45
           OR discovery keyword hypothesis
           OR ghost-market watch list keyword
         Hard cap: 50 calls/run (~$0.06/run at gpt-4o-mini)
         Cache key: relevance_v1:{sha256(prompt)[:16]}
         Verdicts: CLEAN / MIXED / CONTAMINATED / GHOST_MARKET
         GHOST_MARKET verdict overrides RSV ghost flag + triggers alert
         BORDERLINE verdict = non-destructive (keeps rule-based score)

Stage 8  Competitor Profiling (updated)
         + Relevance pre-filter before LLM synthesis (R5)
           < 40% relevant gigs: skip synthesis (return skipped_low_relevance)
           40-80% relevant: trim to relevant-only competitors
           >= 80% relevant: full set passthrough

Stage 10 Scoring -- All 7 calculators + CM (updated)
         demand.py:       qualified_trc = TRC x trc_reliability (R4.1 single multiplier)
         demand.py:       Trends x fiverr_relevance_qualifier x 1.15 (R7)
         demand.py:       Reddit x (0.40 + 0.60 x buyer_intent_ratio) (R7)
         demand.py:       YouTube weight = 0; used for confidence only (R7)
         demand.py:       autocomplete absent + emerging -> score 50 not 0 (R4.2/R7)
         competition.py:  top-10 from clean gigs only (R3/R4)
         competition.py:  per-keyword profile when RSV < 0.80 (R4.3)
         competition.py:  niche profile excludes < 0.40-relevance keywords (R4.4)
         competition.py:  price IQR outlier exclusion (R4.5)
         feasibility.py:  level ratio + review barrier from clean gigs only (R4.6)
         profitability.py: prices from organic + non-zombie + relevant gigs (R4.5)
         opportunity.py:  score x (0.5 + 0.5 x RSV) when RSV < 0.70 (R4.7)
         confidence.py:   RSV deduction -0.05 to -0.50 tiered (R2)
         confidence.py:   zombie concentration deduction -0.05/-0.10 (R3)
         confidence.py:   trc_reliability_low deduction -0.05 when < 0.70 (R4.1)
         confidence.py:   YouTube legitimacy +0.02/-0.03 (R7)
         confidence.py:   freshness x relevance quality contribution (R7)

Stage 12 Tag Assignment (updated)
         + ghost_market_flag -> recommendation demoted / hard blocked (R2)

Stage 16 Discovery Engine (updated -- R6)
         Gate 1: hypothesis specificity >= 0.65 AND confidence >= 0.50
         Gate 2: pre-collection dry-run (page-1 only) via DiscoveryPreValidator
                 ghost / low-relevance / trc-too-low -> reject before full collect
         Gate 3: relevance-gated outcome recording
                 ghost -> is_invalid (NOT is_miss); retire immediately
                 relevance < 0.40 -> is_contaminated; flag recollection
         Gate 4: feedback excludes is_invalid and is_contaminated outcomes
         ACTIVATION GATE: discovery must NOT run in production until Tier-1 gate passes
```

### New Modules Added

| Module | Path | Epic |
|---|---|---|
| search_url_builder.py | src/collection/ | R1 |
| result_set_validator.py | src/analysis/ | R2 |
| result_set_validation_workflow.py | src/analysis/ | R2 |
| zombie_gig_detector.py | src/analysis/ | R3 |
| llm_relevance_classifier.py | src/analysis/ | R5 |
| pre_validator.py | src/discovery/ | R6 |
| monitors.py | src/analysis/ | R11 |
| selector_version_tracker.py | src/collection/ | R11 |

### New Config Keys (config.yaml)

```yaml
niches:
  - niche_id: <id>
    search:
      category_strictness: SUBCATEGORY   # SUBCATEGORY | CATEGORY | NONE
      fallback_on_empty: CATEGORY
      min_results_threshold: 5
    scoring:
      trends_platform_qualifier: 0.65    # 0.40 broad to 0.90 specific
relevance:
  enable_stage_3_5: true
  enable_zombie_filter: true
  enable_sponsored_filter: true
  enable_llm_relevance: true
  llm_relevance_max_calls_per_run: 50
  ghost_market_block_recommendations: true
```

### Backward Compatibility Guarantee

NULL on any new column = "unknown = include". Legacy rows score byte-identically to
pre-SRDI baseline when new reads are disabled (toggle defaults). No retroactive
penalization of legacy NONE-strictness rows.


---

## SRDI ADDENDUM -- New Pipeline Stages and Hardened Components
**Source:** WAVE_A through WAVE_L | **Date:** Cycle 049 (2026-05-29)

### Updated Pipeline (Post-SRDI)

Stage 3  Fiverr Search (updated) -- category-constrained URL (R1); search_strictness_used recorded; sponsored/organic counts; pages_collected

Stage 3.5  Result-Set Validation [NEW -- R2] -- per-gig relevance 0.0-1.0; ghost_market_flag (<0.20 relevance + >5 results); confidence_deduction tiered; ResultSetValidation row per (keyword_id, run_id); fail-soft per keyword

Stage 4  Gig Detail (updated) -- is_sponsored from gig_cards (R3); last_reviewed_at extraction; category_path

Stage 4.5  Zombie Detection [NEW -- R3] -- compute_zombie_score 0.0-1.0; new-seller guard (< 180 days = NOT zombie); threshold 0.50

Stage 5  Seller Profile (updated) -- specialization + last-active signals

Stage 6  External Signals (updated) -- fiverr_relevance_qualifier (R7); signal_quality_score = sqrt(freshness x relevance); Trends/Reddit/YouTube qualified

Stage 7.5  LLM Relevance Gate [NEW -- R5] -- fires when RSV 0.35-0.75 AND final >= 45; cap 50/run; cache relevance_v1:{hash}; verdicts CLEAN/MIXED/CONTAMINATED/GHOST_MARKET

Stage 8  Competitor Profiling (updated) -- relevance pre-filter: <40% skip synthesis; 40-80% trim to relevant-only; >=80% passthrough (R5)

Stage 10  Scoring (updated) -- all 7 calculators + CM use qualified inputs (R4, R7); see per-file SRDI addenda

Stage 12  Tag Assignment (updated) -- ghost_market_flag -> recommendation hard blocked (R2)

Stage 16  Discovery (updated) -- 4 gates (R6): hypothesis specificity; dry-run pre-validator; relevance-gated outcomes; feedback filtering

### New Modules (SRDI)

| Module | Path | Epic |
|---|---|---|
| search_url_builder.py | src/collection/ | R1 |
| result_set_validator.py | src/analysis/ | R2 |
| result_set_validation_workflow.py | src/analysis/ | R2 |
| zombie_gig_detector.py | src/analysis/ | R3 |
| llm_relevance_classifier.py | src/analysis/ | R5 |
| pre_validator.py | src/discovery/ | R6 |
| monitors.py | src/analysis/ | R11 |

### New config.yaml Keys

  niches[].search.category_strictness: SUBCATEGORY | CATEGORY | NONE
  niches[].search.fallback_on_empty: CATEGORY
  niches[].search.min_results_threshold: 5
  niches[].scoring.trends_platform_qualifier: 0.65
  relevance.enable_stage_3_5: true
  relevance.enable_zombie_filter: true
  relevance.enable_sponsored_filter: true
  relevance.enable_llm_relevance: true
  relevance.llm_relevance_max_calls_per_run: 50
  relevance.ghost_market_block_recommendations: true

### Backward Compatibility

NULL on any new column = include (not penalized). Legacy rows score byte-identically
to pre-SRDI baseline when new reads are disabled via toggles.
