# Development Roadmap
# Fiverr Research System — Wave 0 Rev 3 + 9-Niche Portfolio

---

## Phase Overview

| Phase | Waves | Focus | Output |
|---|---|---|---|
| Phase 0: Foundation | Wave 0 | Planning infrastructure + niche confirmation + category verification | Project pack, hydration pack |
| Phase 1: Design | Waves 1–3 | Product design, architecture, schema | All planning documents |
| Phase 2: Core Build | Waves 4–5 | Collection engine, analysis engine | Working collection + analysis code |
| Phase 3: Intelligence | Waves 6–7 | Scoring engine, recommendation engine | Full scoring and recommendation code |
| Phase 4: Interface | Wave 8 | Dashboard, reporting, exports | Streamlit dashboard + reports |
| Phase 5: QA | Post-Wave 8 | Testing, validation, acceptance | Tested, stable system |
| Phase 6: v2 Hardening | Future | PostgreSQL, React, Celery, team features | Production-grade system |

---

## Build Timeline (Single Developer, 2–4 hrs/day)

| Week | Focus | Deliverable |
|---|---|---|
| 1–2 | Schema + database setup | SQLite DB, all 9-niche models, llm_cache, llm_usage_logs, niche_configs, Alembic migrations |
| 3 | Playwright session manager + human events | Working authenticated Fiverr session, relogin mode, human_events module |
| 4 | Keyword expander + Fiverr search collector | Working keyword pipeline with LLM expansion for all 9 niches |
| 5–6 | Gig detail + seller collector + niche depth dispatcher | Full Fiverr data collection with tier-based depth per niche |
| 7 | External source connectors (Google Trends, Reddit, YouTube) | External signals pipeline |
| 8 | LLM client, cache, cost monitor, prompt templates | Full LLM infrastructure layer |
| 9 | Analysis modules: gig quality, seller strength, clustering | Analysis engine with LLM integration |
| 10 | Scoring engine (all 11 scores + confidence + tier-aware behavior) | Scores calculated, stored, explained |
| 11 | Recommendation engine + LLM recommendation tasks | Full recommendations for all GO-tier opportunities |
| 12 | Streamlit dashboard (all 6 pages including LLM cost view) | Dashboard live at localhost:8501 |
| 13 | Exports + alerts + QA pass | Production-ready v1 |

---

## 9-Niche Build Notes

- The niche depth dispatcher (Week 5) is a key component: it reads each niche's configured depth from config.yaml and routes collection jobs to the appropriate sub-pipeline (full / standard / keyword_only / feasibility)
- Auto-promotion logic (Week 5): after 3 completed runs, compare Tier 2 Final Recommendation Scores and update niche_depth in niche_configs table accordingly
- All 9 Fiverr category paths are pre-configured from DL-023 — no manual category lookup needed during build

---

## v2 Roadmap (Post-v1)

- Migrate from SQLite to PostgreSQL
- Replace APScheduler with Celery + Redis
- Build React + FastAPI dashboard
- Add proxy rotation layer as pluggable module
- Add multi-niche profile management UI
- Add seller watchlist with time-series tracking (review velocity, price changes)
- Add Notion and Google Sheets export
- Add email/Slack alert integration
- Add team collaboration features
- Add A/B testing for gig titles (track which LLM suggestions perform best)
- Add historical score tracking (how opportunity scores change over time per niche)
- Add competitor alert system (notify when a tracked competitor changes pricing or receives a burst of reviews)


---

## SRDI Initiative -- "Bulletproof" (Search Relevance & Data Integrity)
**Status:** Active -- Cycle 049 (2026-05-29)
**Jira:** SCRUM project -- 85 stories, 322 subtasks (SCRUM-583 to SCRUM-994)

### Why SRDI Precedes v2

The v1 pipeline has no verification layer for gig result relevance. SRDI installs
that layer before the first acted-on recommendation and before discovery activation.

### SRDI Phase Roadmap

Phase 1 (Weeks 1-4) -- Tier 0: Clean Data at the Source
  R8 Schema (migrations M1-M6) -- ships first, behaviorally inert
  R1 Category-Constrained Search (build_search_url + fallback chain)
  R3 Sponsored/Zombie Filtering (Stage 4.5)
  R2 Stage 3.5 Result-Set Validation (ghost detection + RSV)
  TIER-0 GATE: First-recommendation quality gate armed; ghost markets blocked

Phase 2 (Weeks 5-10) -- Tier 1: Scoring Quality-Aware
  R4 Scoring Integrity Extensions (TRC reliability, clean-gig sets, opportunity qualifier)
  R6 Discovery Relevance Gates (4 gates; discovery activation requires this)
  R9 Testing & Validation Framework (120+ tests, REG-13 to REG-30)
  TIER-1 GATE: Discovery cleared for activation; scoring uses filtered inputs

Phase 3 (Weeks 11-16) -- Tier 2: Semantic + External Signal Integrity
  R5 LLM Stage 7.5 (conditional relevance classifier, synthesis pre-filter)
  R7 External Signal Integrity (Trends qualifier, Reddit buyer-intent, YouTube gate)
  TIER-2 GATE: LLM relevance live; external signals qualified

Phase 4 (Weeks 17-22) -- Tier 3/4: Dashboard + Long-Term Hardening
  R10 Dashboard & Alerting (7 badges, 6 alert types, integrity tab, filters)
  R11 Edge Cases & Maintenance (monitors, versioning, monthly audit, first-rec gate)
  TIER-3/4 GATE: Dashboard released; maintenance protocols live

### Epic Summary

R1 Search URL    SCRUM-591-597       New: search_url_builder.py
R2 Stage 3.5     SCRUM-605-612       New: result_set_validator.py, workflow
R3 Spons/Zombie  SCRUM-598-604       New: zombie_gig_detector.py
R4 Scoring       SCRUM-613-619+813   Updates: all 7 scoring calculators
R5 LLM Stage 7.5 SCRUM-624-625+5more New: llm_relevance_classifier.py
R6 Discovery     SCRUM-626-629+4more New: pre_validator.py
R7 Ext Signals   SCRUM-620-623+4more Updates: Trends/Reddit/YouTube/autocomplete
R8 Schema        SCRUM-583-590       New: 2 models, 6 migrations, ~30 columns
R9 Testing       SCRUM-630-633+4more New: 15 test files, 18 permanent regressions
R10 Dashboard    SCRUM-634-640+897   Updates: dashboard components, alert system
R11 Maintenance  SCRUM-641-646+2more New: monitors.py, protocols, first-rec gate

### Permanent Regression Pack (appended to AGENT_EXECUTION_STRATEGY.md section 7)

REG-13/14: R1 (category filter always active; NONE deduction applied)
REG-15/16: R2 (ghost market absolute block; TRC qualified by RSV)
REG-17/18/19: R3 (sponsored/zombie exclusions; organic TRC adjustment)
REG-20/21/22: R4 (niche profile clean; opportunity qualified; price IQR)
REG-23/24: R5 (LLM in-band trigger; synthesis skipped < 40%)
REG-25/26/27: R6 (ghost = invalid not miss; contaminated excluded; hypothesis rejected)
REG-28/29/30: R7 (emerging not zero-penalized; reddit qualified; trends qualified)

v2 Roadmap items remain unchanged. SRDI is a v1.x initiative.
