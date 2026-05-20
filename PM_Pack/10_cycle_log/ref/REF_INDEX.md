# REFERENCE INDEX — AI-Optimized Navigation System
# Total: 143 source files + 4 AI optimization files = 147 files in ref/

---

## AI OPTIMIZATION FILES (Read these BEFORE loading any reference file)

| File | Purpose | When to Read |
|---|---|---|
| ref/SECTION_INDEX.md | File sizes + token estimates, load-by-section rules | Before loading any large file |
| ref/TOPIC_MAP.md | "I need info about X" -> load these files | When deciding which files to load |
| ref/CHUNK_GUIDE.md | Token-efficient loading recipes per epic/task type | Every cycle when generating prompts |
| ref/REF_INDEX.md | This file — master index of all reference files | On-demand |

## LOADING RULES
1. Check CHUNK_GUIDE.md first — it tells you exactly what to load for your current task
2. If your topic isn't in CHUNK_GUIDE, use TOPIC_MAP.md to find the right files
3. Before loading any file over 300 lines, check SECTION_INDEX.md for the section you need
4. NEVER load more than ~8,000 tokens of reference files per cycle
5. NEVER load a file "just in case" — only load what you need RIGHT NOW

---

## HOW ref/ IS ORGANIZED

```
ref/
├── REF_INDEX.md          <- You are here (master navigation)
├── SECTION_INDEX.md      <- File sizes + section-level loading guide
├── TOPIC_MAP.md          <- Reverse lookup: topic -> files
├── CHUNK_GUIDE.md        <- Token-efficient loading recipes
├── project_plan/         <- 74 spec files across 13 domain folders
│   ├── 00_meta/          <- Decision logs, change logs, wave schedules
│   ├── 01_vision/        <- Product vision, personas, niche config
│   ├── 02_architecture/  <- System arch, config schema, data flow, APIs
│   ├── 03_data/          <- DB schema (28 tables), field catalog, validation
│   ├── 04_collection/    <- 16-stage workflow, Playwright, pacing, proxy
│   ├── 05_scoring/       <- 11 score formulas + system overview
│   ├── 06_analysis/      <- LLM prompts, clustering, competitor, rubric
│   ├── 07_reporting/     <- Dashboard plan, alerts, exports, run log
│   ├── 08_roadmap/       <- Development roadmap
│   ├── 09_pricing/       <- Pricing model, distribution, LLM pricing
│   ├── 10_discovery/     <- Discovery engine, hypothesis, feedback
│   ├── 11_playbook/      <- Seller playbook, profile opt, visual analysis
│   └── 12_dashboard_ux/  <- Design system, interaction, responsive
├── todo/                 <- 10 epic task files + wave schedule (11 files)
├── dod/                  <- 10 definition-of-done files
└── github/               <- 47 GitHub setup files (30 docs + 16 repo files + schedule)
```

---

## QUICK FILE COUNTS

| Directory | Files | Total Lines | Est. Tokens |
|---|---|---|---|
| ref/project_plan/ | 74 | ~27,000 | ~270,000 |
| ref/todo/ | 11 | ~1,500 | ~15,000 |
| ref/dod/ | 10 | ~1,170 | ~11,700 |
| ref/github/ (markdown) | 31 | ~5,100 | ~51,000 |
| ref/github/ (repo files) | 16 | ~800 | ~8,000 |
| **TOTAL** | **142** | **~35,600** | **~355,000** |

**CRITICAL: You cannot load all 355,000 tokens. Budget is ~8,000 tokens of ref per cycle.**
**Use CHUNK_GUIDE.md recipes to stay within budget.**

---

## DIRECTORY-LEVEL SUMMARIES

### ref/project_plan/00_meta/ (7 files, ~870 lines)
Meta documents about the planning process itself. Rarely needed during development.
- CHANGE_LOG.md — History of changes across planning waves
- DECISION_LOG.md — 158 architectural decisions with rationale
- DECISION_LOG_APPEND.md — Supplemental decisions
- DECISION_LOG_WAVE1.md — Wave 1 specific decisions
- ENHANCEMENT_WAVE_SCHEDULE.md — Enhancement planning
- OPEN_QUESTIONS.md — All questions resolved
- WAVE_SCHEDULE.md — Planning wave schedule

### ref/project_plan/01_vision/ (5 files, ~1,740 lines)
Product vision and design. Load when understanding WHY something exists.
- PRODUCT_VISION.md (137 lines) — Project goals and scope
- PERSONAS.md (112 lines) — User types
- USER_STORIES.md (391 lines) — Requirements as stories
- NICHE_CONFIG_DESIGN.md (897 lines) — 9-niche config design [X-LARGE]
- AUTOMATION_OPERATING_MODEL.md (203 lines) — How automation works

### ref/project_plan/02_architecture/ (7 files, ~3,160 lines)
System design. Load when building infrastructure or understanding connections.
- SYSTEM_ARCHITECTURE.md (341 lines) — Overall architecture
- CONFIG_SCHEMA.md (567 lines) — Config fields and validation [LARGE]
- DATA_FLOW.md (676 lines) — Data movement diagrams [X-LARGE]
- COLLECTION_ARCHITECTURE.md (495 lines) — Collection subsystem
- JOB_ARCHITECTURE.md (363 lines) — Job queue design
- API_SURFACE.md (485 lines) — API endpoints
- ARCHITECTURE_DIRECTION.md (232 lines) — Design decisions

### ref/project_plan/03_data/ (5 files, ~2,350 lines)
Data layer. Load when building models or understanding the database.
- SCHEMA.md (1041 lines) — 28 database tables [X-LARGE, load by table]
- FIELD_CATALOG.md (262 lines) — All fields documented
- FRESHNESS_MODEL.md (298 lines) — Data staleness rules
- SOURCE_CONNECTORS.md (434 lines) — External data sources
- VALIDATION_RULES.md (318 lines) — Input validation

### ref/project_plan/04_collection/ (6 files, ~2,950 lines)
Collection engine. Load when building scraping/browser automation.
- COLLECTION_WORKFLOWS.md (666 lines) — 16-stage workflow [X-LARGE, load by stage]
- PLAYWRIGHT_SESSION_DESIGN.md (435 lines) — Browser sessions
- PACING_MODEL.md (344 lines) — Rate limiting
- PROXY_LAYER.md (515 lines) — Proxy rotation
- QUEUE_DESIGN.md (464 lines) — Job queues
- RETRY_AND_CHECKPOINT.md (527 lines) — Error recovery

### ref/project_plan/05_scoring/ (13 files, ~3,150 lines)
Scoring formulas. Each score has its own file — load only the one you're implementing.
- SCORING_SYSTEM.md (355 lines) — Overview of all 11 scores + 4 weight profiles
- Individual scores (150-290 lines each): DEMAND, COMPETITION, SATURATION, TREND, OPPORTUNITY, PROFITABILITY, CONFIDENCE, CONVERSION_INTENT, GIG_QUALITY_WEAKNESS, NEW_SELLER_FEASIBILITY, FINAL

### ref/project_plan/06_analysis/ (11 files, ~4,100 lines)
Analysis algorithms. Load per-task as needed.
- LLM_PROMPT_TEMPLATES.md (428 lines) — All 14 LLM prompt templates
- KEYWORD_CLUSTERING.md (422 lines) — Clustering algorithm
- RECOMMENDATION_ENGINE.md (440 lines) — Recommendation logic
- Plus: COMPETITOR_PROFILING, GIG_QUALITY_RUBRIC, GIG_SUGGESTION_TEMPLATES, GO_NOGO_LOGIC, RECOMMENDATION_OUTPUT_FORMAT, REVIEW_ANALYSIS, SATURATION_MODEL, SELLER_STRENGTH_MODEL

### ref/project_plan/07_reporting/ (5 files, ~2,110 lines)
Dashboard and reporting. Load when building UI components.
- DASHBOARD_PLAN.md (769 lines) — Full dashboard layout [X-LARGE, load by page]
- ALERT_SYSTEM.md, EXPORT_FORMATS.md, REPORT_TEMPLATES.md, RUN_LOG_DESIGN.md

### ref/project_plan/09_pricing/ (4 files, ~1,980 lines)
Pricing engine. Load when building pricing features.

### ref/project_plan/10_discovery/ (4 files, ~2,035 lines)
Discovery engine. Load when building hypothesis/discovery features.

### ref/project_plan/11_playbook/ (3 files, ~1,570 lines)
Seller guidance. Load when building playbook features.

### ref/project_plan/12_dashboard_ux/ (3 files, ~1,840 lines)
Dashboard UX. Load when building UI.

### ref/todo/ (11 files, ~1,500 lines)
Task lists. Load the epic you're currently working on.

### ref/dod/ (10 files, ~1,170 lines)
Definition of done. Load the DOD matching the epic you're implementing.

### ref/github/ (47 files, ~5,900 lines)
GitHub setup. Load specific policy files as needed. Most are under 200 lines.
