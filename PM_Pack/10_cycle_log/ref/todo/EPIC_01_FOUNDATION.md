# EPIC 01 — Foundation & Infrastructure
# Fiverr Research System — Implementation To-Do

**Epic Owner:** Backend Engineer
**Source Specs:** Waves 0–3 (00_meta, 01_vision, 02_architecture, 03_data)
**Priority:** P0 — Must complete before all other epics
**Estimated Stories:** 22 | **Estimated Tasks:** 68

---

## Story 1.1 — Project Scaffolding

| ID | Task | Type | Description |
|---|---|---|---|
| 1.1.1 | Create project directory structure | TASK | Create `src/`, `src/config/`, `src/models/`, `src/collection/`, `src/analysis/`, `src/scoring/`, `src/llm/`, `src/dashboard/`, `src/reports/`, `src/exports/`, `src/discovery/`, `src/playbook/`, `src/pricing/`, `data/`, `data/exports/`, `data/screenshots/`, `data/checkpoints/`, `tests/`, `tests/unit/`, `tests/integration/` |
| 1.1.2 | Create pyproject.toml | TASK | Define project metadata, Python 3.11+ requirement, all dependencies: playwright, sqlalchemy[asyncio]==2.0.*, pydantic==2.*, apscheduler, openai, jinja2, numpy, scipy, scikit-learn, pandas, plotly, streamlit, weasyprint, openpyxl, click |
| 1.1.3 | Create requirements.txt | TASK | Pin all dependency versions for reproducible installs |
| 1.1.4 | Create .env.example | TASK | Template for OPENAI_API_KEY, DATABASE_URL, LOG_LEVEL, LLM_CACHE_PATH |
| 1.1.5 | Create .gitignore | TASK | Ignore data/, .env, __pycache__, *.pyc, data/screenshots/, data/checkpoints/ |
| 1.1.6 | Install Playwright browsers | TASK | Script: `playwright install chromium` |
| 1.1.7 | Create README.md | TASK | Project overview, setup instructions, run commands, architecture diagram reference |

---

## Story 1.2 — Configuration System

| ID | Task | Type | Description |
|---|---|---|---|
| 1.2.1 | Create config.yaml master template | TASK | Full config file with all 9 niche profiles, LLM settings, collection pacing, scoring weights (4 profiles), discovery settings, alert thresholds, export settings. Source: CONFIG_SCHEMA.md |
| 1.2.2 | Create ConfigLoader class | TASK | `src/config/loader.py` — loads config.yaml, validates with Pydantic, merges env vars, provides typed access. Methods: `load()`, `get_niche(niche_id)`, `get_scoring_profile()`, `get_collection_config()` |
| 1.2.3 | Create NicheConfig Pydantic model | TASK | `src/config/models.py` — NicheConfig with fields: niche_id, name, depth, category_path, seed_keywords, starter_prices, hard_exclusions, llm settings. Source: NICHE_CONFIG_DESIGN.md |
| 1.2.4 | Create ScoringProfileConfig model | TASK | 4 named weight profiles: default, aggressive_new_seller, profitability_focus, trend_chaser. Source: SCORING_SYSTEM.md |
| 1.2.5 | Create CollectionConfig model | TASK | Pacing delays, retry limits, checkpoint interval, proxy settings. Source: PACING_MODEL.md |
| 1.2.6 | Create DiscoveryConfig model | TASK | enabled, max_hypotheses_per_run, max_cost_per_run, min_confidence, gold_threshold, enabled_modes, skill_profile. Source: DISCOVERY_ENGINE_ARCHITECTURE.md |
| 1.2.7 | Create config validation tests | TASK | Unit tests: valid config loads, invalid config raises, missing required fields detected, niche pricing validates |

---

## Story 1.3 — Database Models (SQLAlchemy ORM)

| ID | Task | Type | Description |
|---|---|---|---|
| 1.3.1 | Create database engine setup | TASK | `src/models/database.py` — SQLAlchemy engine creation, session factory, `get_db()` context manager, SQLite default with PostgreSQL connection string support |
| 1.3.2 | Create Base model | TASK | `src/models/base.py` — SQLAlchemy declarative base with common mixins (created_at, updated_at) |
| 1.3.3 | Create NicheConfig model | TASK | `src/models/niche.py` — Maps to niche_configs table |
| 1.3.4 | Create Keyword model | TASK | `src/models/keyword.py` — All fields from SCHEMA.md including Wave 10 discovery fields (is_discovery, discovery_mode, hypothesis_confidence, etc.) |
| 1.3.5 | Create SearchResult model | TASK | `src/models/search_result.py` — Fiverr search result snapshots |
| 1.3.6 | Create Gig model | TASK | `src/models/gig.py` — Gig detail data with packages (JSON), gig_extras (JSON) |
| 1.3.7 | Create Seller model | TASK | `src/models/seller.py` — All seller fields including Wave 11 profile extensions |
| 1.3.8 | Create KeywordGigAssociation model | TASK | `src/models/associations.py` — Many-to-many keyword↔gig |
| 1.3.9 | Create ExternalSignal model | TASK | `src/models/external_signal.py` — Google Trends, Reddit signals |
| 1.3.10 | Create KeywordScore model | TASK | `src/models/scores.py` — All 11 score fields + score_components (JSON) + explanation_text |
| 1.3.11 | Create OpportunityRanking model | TASK | `src/models/ranking.py` — tag, rank, final_score per keyword per run |
| 1.3.12 | Create Recommendation model | TASK | `src/models/recommendation.py` — All 14 recommendation fields (JSON columns for complex types) |
| 1.3.13 | Create ClusterAnalysis model | TASK | `src/models/cluster.py` — Cluster labels, centroids, keyword assignments |
| 1.3.14 | Create CompetitorAnalysis model | TASK | `src/models/competitor.py` — Synthesis narrative, entry feasibility |
| 1.3.15 | Create GigQualityScore model | TASK | `src/models/gig_quality.py` — 15 quality criteria scores per gig |
| 1.3.16 | Create SellerScore model | TASK | `src/models/seller_score.py` — authority_score, weakness list |
| 1.3.17 | Create LLMUsageLog model | TASK | `src/models/llm_usage.py` — model, tokens, cost, cache_hit, stage |
| 1.3.18 | Create LLMCache model | TASK | `src/models/llm_cache.py` — SHA-256 key, response, source_data_hash, ttl |
| 1.3.19 | Create RunLog model | TASK | `src/models/run_log.py` — run_id, mode, status, stages, duration, cost |
| 1.3.20 | Create Job model | TASK | `src/models/job.py` — Job queue with status, priority, retry count |
| 1.3.21 | Create Alert model | TASK | `src/models/alert.py` — alert_type, severity, message, resolved |
| 1.3.22 | Create PriceAnalysis model | TASK | `src/models/price_analysis.py` — Wave 9 per-keyword price stats |
| 1.3.23 | Create NichePriceAnalysis model | TASK | `src/models/price_analysis.py` — Wave 9 niche aggregate |
| 1.3.24 | Create DiscoveryOutcome model | TASK | `src/models/discovery.py` — Wave 10 hypothesis outcomes |
| 1.3.25 | Create DiscoveryCycleLog model | TASK | `src/models/discovery.py` — Wave 10 cycle tracking |
| 1.3.26 | Create GigVisualAnalysis model | TASK | `src/models/visual.py` — Wave 11 thumbnail classifications |
| 1.3.27 | Create AutoPromotionLog model | TASK | `src/models/auto_promotion.py` — Niche depth change history |
| 1.3.28 | Create Order model | TASK | `src/models/order.py` — Revenue tracking for gate tracker |
| 1.3.29 | Create database migration script | TASK | `src/models/init_db.py` — Creates all tables, handles schema migrations |
| 1.3.30 | Create model unit tests | TASK | Test all model creation, relationships, JSON field serialization, constraint validation |

---

## Story 1.4 — CLI Entry Point

| ID | Task | Type | Description |
|---|---|---|---|
| 1.4.1 | Create run.py CLI | TASK | `run.py` using Click — commands: `run --mode [full|collect-only|score-only|analyze-only|recommendations-only|discovery-only|discovery-collect|resume]`, `init-db`, `export`, `dashboard` |
| 1.4.2 | Create RunOrchestrator | TASK | `src/orchestrator.py` — Master orchestrator: loads config, initializes DB, selects stages based on --mode, executes stages in order, handles errors, writes run_log |
| 1.4.3 | Create run_id generation | TASK | `run_{timestamp}_{mode}` format with collision avoidance |
| 1.4.4 | Create logging setup | TASK | `src/utils/logging.py` — structured logging with run_id context, file + console handlers, log level from config |
| 1.4.5 | Create --mode resume logic | TASK | Read last checkpoint, determine which stage to restart from, resume job queue |
| 1.4.6 | Create --mode full pipeline sequence | TASK | Wire all 16 stages in order: config→keyword_expand→search→gig_detail→seller→external→gig_quality→competitor→cluster→scoring→price_analysis→ranking→tags→recommendations→reporting→export→discovery |
| 1.4.7 | Create CLI unit tests | TASK | Test all --mode flags, invalid mode handling, run_id generation |

---

## Story 1.5 — LLM Client and Cache

| ID | Task | Type | Description |
|---|---|---|---|
| 1.5.1 | Create LLMClient wrapper | TASK | `src/llm/client.py` — Wraps OpenAI SDK. Methods: `complete(prompt, model, temperature, response_format)`, `embed(texts, model)`. Tracks token usage and cost. Supports gpt-4o, gpt-4o-mini, text-embedding-3-small |
| 1.5.2 | Create LLM cache layer | TASK | `src/llm/cache.py` — SQLite-based cache. Key: SHA-256 of (model + temperature + prompt). Methods: `get(key)`, `set(key, value, ttl_hours)`, `invalidate(key)`. TTL enforcement on read |
| 1.5.3 | Create cache key builder | TASK | `build_cache_key(model, temperature, prompt_text)` — deterministic SHA-256 |
| 1.5.4 | Create cost tracking | TASK | Per-call cost calculation based on model pricing. Logs to llm_usage_logs table |
| 1.5.5 | Create self-correction retry | TASK | On Pydantic ValidationError, append error to prompt and retry once. On second failure, return None |
| 1.5.6 | Create Jinja2 template renderer | TASK | `src/llm/template_renderer.py` — Loads .j2 files from `src/llm/prompts/`, renders with context |
| 1.5.7 | Create LLM client unit tests | TASK | Test cache hits/misses, cost calculation, retry behavior, template rendering |

---

## Story 1.6 — Utility Modules

| ID | Task | Type | Description |
|---|---|---|---|
| 1.6.1 | Create date/time utilities | TASK | `src/utils/datetime.py` — format_duration(), date_stamp(), parse_fiverr_date() |
| 1.6.2 | Create data validation utilities | TASK | `src/utils/validation.py` — validate_url(), validate_price(), sanitize_text() |
| 1.6.3 | Create export utilities | TASK | `src/utils/export.py` — ensure_export_dirs(), get_export_path(format, date) |
| 1.6.4 | Create hash utilities | TASK | `src/utils/hashing.py` — sha256_hash(), jaccard_similarity() |

---

## Story 1.7 — Niche Seed Data

| ID | Task | Type | Description |
|---|---|---|---|
| 1.7.1 | Create seed keyword files | TASK | One YAML file per niche in `data/seeds/` with 6-8 seed keywords each. All 9 niches |
| 1.7.2 | Create keyword import script | TASK | `src/scripts/import_seeds.py` — Reads seed YAMLs, inserts into keywords table with source="seed" |
| 1.7.3 | Create Fiverr category path validator | TASK | Script that validates category_path URLs are live (one-time manual check helper) |

---

## Epic 01 Summary

| Metric | Count |
|---|---|
| Stories | 7 |
| Tasks | 68 |
| Source Spec Files | SYSTEM_ARCHITECTURE.md, DATA_FLOW.md, CONFIG_SCHEMA.md, SCHEMA.md, FIELD_CATALOG.md, JOB_ARCHITECTURE.md |
| New Python Files | ~35 |
| New Test Files | ~7 |
