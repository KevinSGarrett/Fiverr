# TOPIC MAP — Reverse Lookup Index
# "I need info about X" -> Load these files
# Organized by concept so the PM can find any info in 1 lookup

---

## How to Use
1. Find your topic below
2. Load ONLY the files listed (smallest first)
3. If the topic spans multiple files, start with the PRIMARY file
4. Load SECONDARY files only if the primary doesn't answer your question

---

## DATABASE & SCHEMA

| Topic | Primary File | Secondary Files |
|---|---|---|
| Table definitions (28 tables) | ref/project_plan/03_data/SCHEMA.md (lines 1-200 for core tables) | ref/project_plan/03_data/FIELD_CATALOG.md |
| Field types & constraints | ref/project_plan/03_data/FIELD_CATALOG.md | ref/project_plan/03_data/VALIDATION_RULES.md |
| Data freshness & staleness | ref/project_plan/03_data/FRESHNESS_MODEL.md | — |
| External data sources | ref/project_plan/03_data/SOURCE_CONNECTORS.md | — |
| Validation rules | ref/project_plan/03_data/VALIDATION_RULES.md | — |
| ORM models (implementation) | ref/todo/EPIC_01_FOUNDATION.md (Story S1.3) | ref/dod/DOD_EPIC_01.md |

## CONFIGURATION

| Topic | Primary File | Secondary Files |
|---|---|---|
| Config schema (all fields) | ref/project_plan/02_architecture/CONFIG_SCHEMA.md | — |
| Niche profiles (9 niches) | ref/project_plan/01_vision/NICHE_CONFIG_DESIGN.md | — |
| Scoring weight profiles (4) | ref/project_plan/05_scoring/SCORING_SYSTEM.md | — |
| Collection pacing config | ref/project_plan/04_collection/PACING_MODEL.md | — |

## COLLECTION ENGINE

| Topic | Primary File | Secondary Files |
|---|---|---|
| Collection workflow (16 stages) | ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md | ref/project_plan/02_architecture/COLLECTION_ARCHITECTURE.md |
| Playwright browser sessions | ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md | — |
| Rate limiting & pacing | ref/project_plan/04_collection/PACING_MODEL.md | — |
| Proxy rotation | ref/project_plan/04_collection/PROXY_LAYER.md | — |
| Job queue design | ref/project_plan/04_collection/QUEUE_DESIGN.md | ref/project_plan/02_architecture/JOB_ARCHITECTURE.md |
| Retry logic & checkpoints | ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md | — |
| Collection tasks | ref/todo/EPIC_02_COLLECTION.md | ref/dod/DOD_EPIC_02.md |

## SCORING SYSTEM

| Topic | Primary File | Secondary Files |
|---|---|---|
| Scoring overview (11 scores) | ref/project_plan/05_scoring/SCORING_SYSTEM.md | ref/project_plan/05_scoring/SCORING_DIRECTION.md |
| Demand score formula | ref/project_plan/05_scoring/DEMAND_SCORE.md | — |
| Competition score formula | ref/project_plan/05_scoring/COMPETITION_SCORE.md | — |
| Saturation score formula | ref/project_plan/05_scoring/SATURATION_SCORE.md | — |
| Trend score formula | ref/project_plan/05_scoring/TREND_SCORE.md | — |
| Opportunity score formula | ref/project_plan/05_scoring/OPPORTUNITY_SCORE.md | — |
| Profitability score formula | ref/project_plan/05_scoring/PROFITABILITY_SCORE.md | — |
| Confidence score formula | ref/project_plan/05_scoring/CONFIDENCE_SCORE.md | — |
| Conversion intent formula | ref/project_plan/05_scoring/CONVERSION_INTENT_SCORE.md | — |
| Gig quality weakness formula | ref/project_plan/05_scoring/GIG_QUALITY_WEAKNESS_SCORE.md | — |
| New seller feasibility | ref/project_plan/05_scoring/NEW_SELLER_FEASIBILITY.md | — |
| Final composite score | ref/project_plan/05_scoring/FINAL_SCORE.md | — |
| Scoring tasks | ref/todo/EPIC_04_SCORING.md | ref/dod/DOD_EPIC_04.md |

## ANALYSIS ENGINE

| Topic | Primary File | Secondary Files |
|---|---|---|
| LLM prompt templates (14) | ref/project_plan/06_analysis/LLM_PROMPT_TEMPLATES.md | — |
| Keyword clustering | ref/project_plan/06_analysis/KEYWORD_CLUSTERING.md | — |
| Competitor profiling | ref/project_plan/06_analysis/COMPETITOR_PROFILING.md | — |
| Gig quality rubric (15 criteria) | ref/project_plan/06_analysis/GIG_QUALITY_RUBRIC.md | — |
| Seller strength model | ref/project_plan/06_analysis/SELLER_STRENGTH_MODEL.md | — |
| Review sentiment analysis | ref/project_plan/06_analysis/REVIEW_ANALYSIS.md | — |
| Saturation model | ref/project_plan/06_analysis/SATURATION_MODEL.md | — |
| Go/no-go decision logic | ref/project_plan/06_analysis/GO_NOGO_LOGIC.md | — |
| Analysis tasks | ref/todo/EPIC_03_ANALYSIS.md | ref/dod/DOD_EPIC_03.md |

## RECOMMENDATIONS

| Topic | Primary File | Secondary Files |
|---|---|---|
| Recommendation engine design | ref/project_plan/06_analysis/RECOMMENDATION_ENGINE.md | — |
| Recommendation output format | ref/project_plan/06_analysis/RECOMMENDATION_OUTPUT_FORMAT.md | — |
| Gig suggestion templates | ref/project_plan/06_analysis/GIG_SUGGESTION_TEMPLATES.md | — |
| Recommendation tasks | ref/todo/EPIC_05_RECOMMENDATIONS.md | ref/dod/DOD_EPIC_05.md |

## PRICING ENGINE

| Topic | Primary File | Secondary Files |
|---|---|---|
| New seller pricing model | ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md | — |
| Price distribution analysis | ref/project_plan/09_pricing/PRICE_DISTRIBUTION_ANALYSIS.md | — |
| Pricing LLM recommendations | ref/project_plan/09_pricing/PRICING_RECOMMENDATIONS_LLM.md | — |
| Pricing dashboard widgets | ref/project_plan/09_pricing/PRICING_DASHBOARD_WIDGETS.md | — |
| Pricing tasks | ref/todo/EPIC_06_PRICING.md | ref/dod/DOD_EPIC_06.md |

## DISCOVERY ENGINE

| Topic | Primary File | Secondary Files |
|---|---|---|
| Discovery architecture | ref/project_plan/10_discovery/DISCOVERY_ENGINE_ARCHITECTURE.md | — |
| Hypothesis generation | ref/project_plan/10_discovery/HYPOTHESIS_GENERATION_PROMPTS.md | — |
| Discovery scoring/feedback | ref/project_plan/10_discovery/DISCOVERY_SCORING_AND_FEEDBACK.md | — |
| Discovery widgets | ref/project_plan/10_discovery/DISCOVERY_DASHBOARD_WIDGETS.md | — |
| Discovery tasks | ref/todo/EPIC_07_DISCOVERY.md | ref/dod/DOD_EPIC_07.md |

## PLAYBOOK & SELLER GUIDANCE

| Topic | Primary File | Secondary Files |
|---|---|---|
| Seller setup playbook | ref/project_plan/11_playbook/SELLER_SETUP_PLAYBOOK.md | — |
| Profile optimization | ref/project_plan/11_playbook/SELLER_PROFILE_OPTIMIZATION.md | — |
| Gig visual/thumbnail analysis | ref/project_plan/11_playbook/GIG_VISUAL_ANALYSIS.md | — |
| Playbook tasks | ref/todo/EPIC_08_PLAYBOOK.md | ref/dod/DOD_EPIC_08.md |

## DASHBOARD & REPORTING

| Topic | Primary File | Secondary Files |
|---|---|---|
| Dashboard page plan | ref/project_plan/07_reporting/DASHBOARD_PLAN.md | — |
| Design system tokens | ref/project_plan/12_dashboard_ux/DESIGN_SYSTEM.md | — |
| UX interaction patterns | ref/project_plan/12_dashboard_ux/INTERACTION_PATTERNS.md | — |
| Responsive & performance | ref/project_plan/12_dashboard_ux/RESPONSIVE_AND_PERFORMANCE.md | — |
| Alert system (8 types) | ref/project_plan/07_reporting/ALERT_SYSTEM.md | — |
| Export formats (5 types) | ref/project_plan/07_reporting/EXPORT_FORMATS.md | — |
| Report templates | ref/project_plan/07_reporting/REPORT_TEMPLATES.md | — |
| Run log design | ref/project_plan/07_reporting/RUN_LOG_DESIGN.md | — |
| Dashboard tasks | ref/todo/EPIC_09_DASHBOARD.md | ref/dod/DOD_EPIC_09.md |

## ARCHITECTURE & SYSTEM

| Topic | Primary File | Secondary Files |
|---|---|---|
| System architecture overview | ref/project_plan/02_architecture/SYSTEM_ARCHITECTURE.md | ref/project_plan/02_architecture/ARCHITECTURE_DIRECTION.md |
| API surface & endpoints | ref/project_plan/02_architecture/API_SURFACE.md | — |
| Data flow diagrams | ref/project_plan/02_architecture/DATA_FLOW.md | — |
| Job scheduling architecture | ref/project_plan/02_architecture/JOB_ARCHITECTURE.md | — |
| Product vision & scope | ref/project_plan/01_vision/PRODUCT_VISION.md | — |
| User personas | ref/project_plan/01_vision/PERSONAS.md | — |
| User stories | ref/project_plan/01_vision/USER_STORIES.md | — |
| Automation operating model | ref/project_plan/01_vision/AUTOMATION_OPERATING_MODEL.md | — |
| Development roadmap | ref/project_plan/08_roadmap/DEVELOPMENT_ROADMAP.md | — |

## GITHUB & REPO

| Topic | Primary File | Secondary Files |
|---|---|---|
| Directory structure | ref/github/00_setup/DIRECTORY_STRUCTURE.md | — |
| Branching strategy | ref/github/01_branching/BRANCHING_STRATEGY.md | ref/github/01_branching/BRANCH_NAMING.md |
| PR policy & reviews | ref/github/02_pr_policy/PR_POLICY.md | ref/github/02_pr_policy/PR_REVIEW_PROCESS.md |
| Label system (52 labels) | ref/github/03_labels/LABEL_TAXONOMY.md | ref/github/03_labels/LABEL_AUTOMATION.md |
| CI/CD pipeline | ref/github/04_ci_checks/CI_PIPELINE.md | ref/github/04_ci_checks/PR_CHECKS.md |
| Agent roles & coordination | ref/github/07_ai_workflow/AI_AGENT_ROLES.md | ref/github/07_ai_workflow/AGENT_COORDINATION.md |
| Cursor rules | ref/github/07_ai_workflow/CURSOR_RULES.md | — |
| Risk management | ref/github/06_risk_management/RISK_TIERS.md | ref/github/06_risk_management/RISK_REVIEW_MATRIX.md |
| Security & secrets | ref/github/09_security/SECURITY_POLICY.md | ref/github/09_security/SECRETS_MANAGEMENT.md |

## INTEGRATION & TESTING

| Topic | Primary File | Secondary Files |
|---|---|---|
| Integration tasks | ref/todo/EPIC_10_INTEGRATION.md | ref/dod/DOD_EPIC_10.md |
| Quality gates | ref/github/04_ci_checks/QUALITY_GATES.md | — |
