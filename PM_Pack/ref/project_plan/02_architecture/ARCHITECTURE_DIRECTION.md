# Architecture Direction
# Fiverr Research System — Wave 0 Rev 3

**Version:** 0.3 — Full Authenticated Session + Complete LLM Layer + 9-Niche Portfolio

---

## System Purpose

A local-first, fully automated intelligence platform that collects data from Fiverr via authenticated Playwright sessions at natural human rate across 9 research niches, validates demand using external sources, analyzes competitive dynamics, scores keyword and niche opportunities using 11 quantifiable scores, and produces LLM-powered gig recommendations — running unattended after initial configuration.

---

## Architecture Principles

1. Local-first. No cloud infrastructure required for v1.
2. Automation-first. Every pipeline stage runs unattended after configuration.
3. Authenticated by default. Fiverr collection uses the user's own account.
4. LLM-native. LLM integrated at every stage where it adds value.
5. Multi-niche. All 9 niches processed in a single run with tier-based depth.
6. Database-backed. SQLite v1 → PostgreSQL v2.
7. Modular. Each pipeline stage is a separate module with clean interface.
8. Explainable. Every score and recommendation has logged reasoning and source evidence.
9. Resumable. Checkpoint-based resumption for every collection pipeline.
10. Configurable. All parameters in config.yaml. No hardcoded values in business logic.
11. Cacheable. LLM responses cached by prompt hash.

---

## Full Stack

| Layer | v1 Technology | v2 Upgrade |
|---|---|---|
| Language | Python 3.11+ | Same |
| Browser Automation | Playwright (Python) + playwright-stealth | Same |
| Session Management | Playwright persistent context + storage_state() | Same |
| HTTP Client | httpx (async) | Same |
| HTML Parsing | selectolax (fast) + BeautifulSoup (fallback) | Same |
| Database | SQLite | PostgreSQL |
| ORM | SQLAlchemy 2.0 | Same |
| Migrations | Alembic | Same |
| Schema Validation | Pydantic v2 | Same |
| Data Analysis | Pandas + Polars | Same |
| ML Clustering | scikit-learn (KMeans / DBSCAN) | Same |
| Embeddings | OpenAI text-embedding-3-small | Same |
| LLM Primary | OpenAI API: gpt-4o + gpt-4o-mini | Same |
| LLM Local Alt | Ollama: llama3:8b + llama3:70b | Same |
| LLM Prompts | Jinja2 templates in src/llm/prompts/ | Same |
| LLM Cache | SQLite llm_cache table | Same |
| NLP Support | spaCy | Same |
| Job Scheduling | APScheduler | Celery + Redis |
| API Layer | FastAPI + Uvicorn | Same |
| Dashboard | Streamlit | React + Tailwind |
| Charts | Plotly | Same |
| PDF Export | WeasyPrint | Same |
| Excel/CSV Export | Pandas (openpyxl) | Same |
| Report Templates | Jinja2 | Same |
| Config | PyYAML + python-dotenv | Same |

---

## Verified Fiverr Category Paths (All 9 Niches)

| Slot | Niche | Category Path | Full URL |
|---|---|---|---|
| 1 | PRD / AI SaaS MVP Roadmap | Programming & Tech > AI & Machine Learning > AI Technology Consulting | fiverr.com/categories/programming-tech/ai-coding/AI-Technology-Consulting |
| 1 | PRD (alternative) | Writing & Translation > Technical Writing | fiverr.com/categories/writing-translation/technical-writing |
| 2 | Support-KB Readiness | Writing & Translation > Technical Writing | fiverr.com/categories/writing-translation/technical-writing |
| 3 | Gumloop/Lindy Workflow | Programming & Tech > Software Development > Automations & Workflows | fiverr.com/categories/programming-tech/software-development/automations-workflows |
| 4 | MCP Server / AI-Agent Integration | Programming & Tech > AI & Machine Learning > AI Agents Development | fiverr.com/categories/programming-tech/ai-coding/ai-agents-development |
| 5 | Python Automation Scripts | Programming & Tech > Web Programming > Python | fiverr.com/categories/programming-tech/buy/web-programming-services/python |
| 6 | AI Tool / LLM App Integration | Programming & Tech > AI & Machine Learning > AI Integrations | fiverr.com/categories/programming-tech/ai-coding/ai-integrations |
| 7 | AI Agent Development | Programming & Tech > AI & Machine Learning > AI Agents Development | fiverr.com/categories/programming-tech/ai-coding/ai-agents-development |
| 8 | Workflow Automation (n8n/Make/Zapier) | Programming & Tech > Software Development > Automations & Workflows | fiverr.com/categories/programming-tech/software-development/automations-workflows |
| 9 | Python Web Scraping / Data Scripts | Programming & Tech > Web Programming > Python | fiverr.com/categories/programming-tech/buy/web-programming-services/python |

---

## System Component Map

```
config.yaml + .env
  9 niche profiles, seeds, depth settings, pacing, LLM config, session mode
         |
         v
    Orchestrator (run.py)
    APScheduler, Mode router, Niche depth dispatcher
    Checkpoint manager, Run logger
         |
   ______|_________________________________
   |              |           |           |
Collection     Analysis    Scoring    Reporting
  Layer         Layer       Layer       Layer
(per niche,   (per niche) (per niche) (aggregate +
 by depth)                             per niche)
   |              |           |           |
Playwright     Pandas      11 Python   Streamlit
Auth session   Polars      scoring     PDF/Excel/CSV
httpx          spaCy       functions   Alert system
pytrends       sklearn
Reddit API
         |
    LLM Intelligence Layer (first-class component)
    gpt-4o / gpt-4o-mini / text-embedding-3-small
    Ollama (offline alt)
    Jinja2 prompt templates (src/llm/prompts/)
    LLM cache (SQLite, SHA-256 keyed)
    Token logger + cost monitor (llm_usage_logs table)
         |
         v
      Database (SQLite v1 / PostgreSQL v2)
      Tables: keywords, search_results, gigs, sellers,
      external_signals, gig_quality_scores, seller_scores,
      keyword_clusters, cluster_analysis, keyword_scores,
      confidence_scores, opportunity_rankings, recommendations,
      llm_cache, llm_usage_logs, run_logs, niche_configs
         |
         v
  Dashboard + Exports
  Streamlit localhost:8501 (6 pages including LLM cost view)
  PDF reports, Excel, CSV, Markdown summaries
```

---

## Data Flow (Seed to Recommendation — Per Niche)

```
config.yaml niche profile (seeds + depth setting)
  → Stage 1: Seed intake + optional LLM expansion (gpt-4o-mini)
  → Stage 2: Keyword expansion: autocomplete + LLM variants + embeddings
  → Stage 3: Fiverr search collection (authenticated Playwright session)
  → Stage 4: Gig detail collection (authenticated, depth-configured top N)
  → Stage 5: Competitor seller profile collection (authenticated)
  → Stage 6: External validation: Google Trends + Reddit + YouTube + LLM parse
  → Stage 7: LLM gig quality analysis: title, description, weakness, thumbnail, FAQ
  → Stage 8: LLM seller strength + competitor cluster synthesis
  → Stage 9: Keyword clustering: embeddings + sklearn + LLM labeling + narrative
  → Stage 10: Score calculation (all 11 scores, deterministic Python)
  → Stage 11: Confidence scoring (deterministic)
  → Stage 12: Opportunity ranking (deterministic)
  → Stage 13: LLM recommendation generation (titles, tags, packages, description, etc.)
  → Stage 14: LLM reporting (score explanations, narratives, competitor summaries)
  → Stage 15: LLM run summary + structured run log
```

---

## Application Code Folder Structure

```
C:\Fiverr1\app\                       (Wave 4+ build root)
  .env                                (OPENAI_API_KEY + Fiverr credentials — gitignored)
  .env.example
  .gitignore
  config.yaml                         (all tunable config + 9 niche profiles)
  run.py                              (main entry point + mode router)
  requirements.txt
  alembic\
    versions\
  src\
    core\
      config.py                       (config loading + validation)
      database.py                     (SQLAlchemy session management)
      logging.py
      scheduler.py
    models\                           (SQLAlchemy ORM — one file per table)
    schemas\                          (Pydantic v2 schemas — one per domain)
    collection\
      session_manager.py              (Playwright session: init, restore, refresh)
      human_events.py                 (scroll, hover, dwell, dead-nav simulation)
      keyword_expander.py             (Stage 2)
      fiverr_search.py                (Stage 3)
      gig_detail.py                   (Stage 4)
      seller_profile.py               (Stage 5)
      checkpoint.py
      external\
        google_trends.py
        reddit.py
        youtube.py
    llm\
      client.py                       (OpenAI + Ollama unified wrapper)
      cache.py                        (SQLite cache: get/set/invalidate)
      cost_monitor.py                 (token usage logger + spend tracker)
      structured_output.py            (JSON mode + Pydantic + self-correction)
      prompts\                        (all Jinja2 templates by stage)
    analysis\
      gig_quality_analyzer.py         (Stage 7 orchestrator)
      seller_strength.py              (Stage 8 orchestrator)
      keyword_clusterer.py            (Stage 9 orchestrator)
    scoring\
      demand_score.py
      competition_score.py
      opportunity_score.py
      new_seller_feasibility.py
      profitability_score.py
      conversion_intent.py
      saturation_score.py
      gig_quality_weakness.py
      trend_score.py
      confidence_score.py
      composite_scorer.py
    recommendation\
      go_nogo.py
      gig_suggester.py
    reporting\
      dashboard_data.py
      pdf_report.py
      excel_export.py
      alert_system.py
    scheduler\
      jobs.py
      queues.py
  dashboard\
    app.py
    pages\
      01_opportunities.py
      02_keywords.py
      03_competitors.py
      04_recommendations.py
      05_run_history.py
      06_llm_costs.py
  data\
    db\
    sessions\                         (gitignored)
    checkpoints\
    exports\
    raw\
  tests\
    unit\
    integration\
```
