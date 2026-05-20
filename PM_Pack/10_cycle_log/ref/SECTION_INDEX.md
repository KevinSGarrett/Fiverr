# SECTION INDEX — AI-Optimized File & Section Registry
# Purpose: Enable surgical loading of ONLY the sections the PM needs
# Rule: NEVER load a full file when only one section is needed

---

## How to Use This Index

1. Identify what information you need (use TOPIC_MAP.md for reverse lookup)
2. Find the file in this index
3. Note the line range for the section you need
4. Load ONLY that section using line offsets
5. If a file is under 200 lines, load the whole file (it's small enough)
6. If a file is over 200 lines, load only the relevant section

---

## Size Categories (Token Estimates: ~1 token per 4 characters, ~10 tokens per line)

| Category | Lines | Est. Tokens | Load Strategy |
|---|---|---|---|
| SMALL | 1-100 | <1,000 | Load entire file freely |
| MEDIUM | 101-300 | 1,000-3,000 | Load entire file or by section |
| LARGE | 301-600 | 3,000-6,000 | Load by section only |
| X-LARGE | 601+ | 6,000+ | Load by section only, never full |

---

## File Size Registry by Category

### X-LARGE FILES (601+ lines) — ALWAYS load by section
| File | Lines | Tokens Est. |
|---|---|---|
| ref/project_plan/03_data/SCHEMA.md | 1041 | ~10,000 |
| ref/project_plan/01_vision/NICHE_CONFIG_DESIGN.md | 897 | ~9,000 |
| ref/project_plan/07_reporting/DASHBOARD_PLAN.md | 769 | ~7,700 |
| ref/project_plan/10_discovery/DISCOVERY_ENGINE_ARCHITECTURE.md | 760 | ~7,600 |
| ref/project_plan/02_architecture/DATA_FLOW.md | 676 | ~6,800 |
| ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md | 666 | ~6,700 |
| ref/project_plan/12_dashboard_ux/DESIGN_SYSTEM.md | 660 | ~6,600 |
| ref/project_plan/09_pricing/PRICE_DISTRIBUTION_ANALYSIS.md | 635 | ~6,400 |
| ref/project_plan/12_dashboard_ux/RESPONSIVE_AND_PERFORMANCE.md | 592 | ~5,900 |
| ref/project_plan/12_dashboard_ux/INTERACTION_PATTERNS.md | 588 | ~5,900 |
| ref/project_plan/11_playbook/SELLER_SETUP_PLAYBOOK.md | 587 | ~5,900 |
| ref/project_plan/02_architecture/CONFIG_SCHEMA.md | 567 | ~5,700 |
| ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md | 527 | ~5,300 |
| ref/project_plan/04_collection/PROXY_LAYER.md | 515 | ~5,200 |
| ref/project_plan/11_playbook/GIG_VISUAL_ANALYSIS.md | 514 | ~5,100 |
| ref/project_plan/02_architecture/COLLECTION_ARCHITECTURE.md | 495 | ~5,000 |
| ref/project_plan/02_architecture/API_SURFACE.md | 485 | ~4,900 |
| ref/project_plan/09_pricing/PRICING_DASHBOARD_WIDGETS.md | 480 | ~4,800 |
| ref/project_plan/11_playbook/SELLER_PROFILE_OPTIMIZATION.md | 470 | ~4,700 |
| ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md | 466 | ~4,700 |
| ref/project_plan/04_collection/QUEUE_DESIGN.md | 464 | ~4,600 |

### LARGE FILES (301-600 lines) — Load by section preferred
| File | Lines | Tokens Est. |
|---|---|---|
| ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md | 435 | ~4,400 |
| ref/project_plan/03_data/SOURCE_CONNECTORS.md | 434 | ~4,300 |
| ref/project_plan/10_discovery/HYPOTHESIS_GENERATION_PROMPTS.md | 429 | ~4,300 |
| ref/project_plan/06_analysis/LLM_PROMPT_TEMPLATES.md | 428 | ~4,300 |
| ref/project_plan/10_discovery/DISCOVERY_DASHBOARD_WIDGETS.md | 425 | ~4,300 |
| ref/project_plan/06_analysis/KEYWORD_CLUSTERING.md | 422 | ~4,200 |
| ref/project_plan/10_discovery/DISCOVERY_SCORING_AND_FEEDBACK.md | 421 | ~4,200 |
| ref/project_plan/06_analysis/COMPETITOR_PROFILING.md | 414 | ~4,100 |
| ref/project_plan/09_pricing/PRICING_RECOMMENDATIONS_LLM.md | 400 | ~4,000 |
| ref/project_plan/01_vision/USER_STORIES.md | 391 | ~3,900 |
| ref/project_plan/07_reporting/REPORT_TEMPLATES.md | 367 | ~3,700 |
| ref/project_plan/06_analysis/RECOMMENDATION_OUTPUT_FORMAT.md | 365 | ~3,700 |
| ref/project_plan/02_architecture/JOB_ARCHITECTURE.md | 363 | ~3,600 |
| ref/project_plan/06_analysis/GIG_SUGGESTION_TEMPLATES.md | 361 | ~3,600 |
| ref/project_plan/06_analysis/SELLER_STRENGTH_MODEL.md | 357 | ~3,600 |
| ref/project_plan/05_scoring/SCORING_SYSTEM.md | 355 | ~3,600 |
| ref/project_plan/05_scoring/CONFIDENCE_SCORE.md | 353 | ~3,500 |
| ref/project_plan/07_reporting/EXPORT_FORMATS.md | 351 | ~3,500 |
| ref/project_plan/04_collection/PACING_MODEL.md | 344 | ~3,400 |
| ref/project_plan/07_reporting/RUN_LOG_DESIGN.md | 343 | ~3,400 |
| ref/project_plan/02_architecture/SYSTEM_ARCHITECTURE.md | 341 | ~3,400 |
| ref/project_plan/06_analysis/SATURATION_MODEL.md | 341 | ~3,400 |
| ref/project_plan/03_data/VALIDATION_RULES.md | 318 | ~3,200 |
| ref/project_plan/05_scoring/SCORING_DIRECTION.md | 299 | ~3,000 |
| ref/project_plan/03_data/FRESHNESS_MODEL.md | 298 | ~3,000 |
| ref/project_plan/05_scoring/FINAL_SCORE.md | 290 | ~2,900 |
| ref/project_plan/07_reporting/ALERT_SYSTEM.md | 283 | ~2,800 |

### MEDIUM FILES (101-300 lines) — Safe to load entire file
| File | Lines |
|---|---|
| ref/project_plan/00_meta/CHANGE_LOG.md | 275 |
| ref/project_plan/00_meta/ENHANCEMENT_WAVE_SCHEDULE.md | 270 |
| ref/project_plan/03_data/FIELD_CATALOG.md | 262 |
| ref/project_plan/06_analysis/GO_NOGO_LOGIC.md | 252 |
| ref/project_plan/06_analysis/GIG_QUALITY_RUBRIC.md | 267 |
| ref/project_plan/06_analysis/REVIEW_ANALYSIS.md | 447 |
| ref/project_plan/06_analysis/RECOMMENDATION_ENGINE.md | 440 |
| ref/project_plan/02_architecture/ARCHITECTURE_DIRECTION.md | 232 |
| ref/project_plan/05_scoring/COMPETITION_SCORE.md | 232 |
| ref/project_plan/05_scoring/PROFITABILITY_SCORE.md | 226 |
| ref/project_plan/05_scoring/NEW_SELLER_FEASIBILITY.md | 224 |
| ref/project_plan/05_scoring/CONVERSION_INTENT_SCORE.md | 219 |
| ref/project_plan/05_scoring/GIG_QUALITY_WEAKNESS_SCORE.md | 217 |
| ref/project_plan/05_scoring/OPPORTUNITY_SCORE.md | 208 |
| ref/project_plan/00_meta/DECISION_LOG.md | 206 |
| ref/project_plan/05_scoring/TREND_SCORE.md | 204 |
| ref/project_plan/01_vision/AUTOMATION_OPERATING_MODEL.md | 203 |
| ref/project_plan/05_scoring/DEMAND_SCORE.md | 175 |
| ref/project_plan/05_scoring/SATURATION_SCORE.md | 143 |
| ref/project_plan/01_vision/PRODUCT_VISION.md | 137 |
| ref/project_plan/01_vision/PERSONAS.md | 112 |
| ref/todo/EPIC_01_FOUNDATION.md | 133 |
| ref/todo/EPIC_02_COLLECTION.md | 231 |
| ref/todo/EPIC_03_ANALYSIS.md | 124 |
| ref/todo/EPIC_04_SCORING.md | 131 |
| ref/todo/EPIC_09_DASHBOARD.md | 228 |
| ref/todo/EPIC_10_INTEGRATION.md | 169 |
| ref/dod/DOD_EPIC_01.md | 171 |
| ref/dod/DOD_EPIC_02.md | 144 |
| ref/dod/DOD_EPIC_09.md | 173 |
| ref/dod/DOD_EPIC_10.md | 177 |
| ref/github/00_setup/DIRECTORY_STRUCTURE.md | 292 |

### SMALL FILES (1-100 lines) — Load freely, minimal token cost
All remaining files (DOD_EPIC_03-08, most github files, scoring formulas, etc.)
