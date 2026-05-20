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
