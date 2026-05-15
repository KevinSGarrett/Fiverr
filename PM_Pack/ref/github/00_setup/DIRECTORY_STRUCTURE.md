# Directory Structure
# Fiverr Research System — Repository Layout

---

## Complete Directory Tree

```
fiverr-research-system/
│
├── .github/                          # GitHub configuration
│   ├── workflows/                    # CI/CD pipelines
│   │   ├── ci.yml                    # Main CI pipeline (lint, type-check, test)
│   │   ├── pr-checks.yml            # PR-specific checks (title, size, labels)
│   │   ├── security.yml             # Security scanning (secrets, dependencies)
│   │   └── release.yml              # Release tagging and changelog
│   ├── ISSUE_TEMPLATE/              # Issue templates
│   │   ├── bug_report.yml           # Bug report template
│   │   ├── feature_request.yml      # Feature request template
│   │   ├── task.yml                 # Implementation task template
│   │   ├── epic.yml                 # Epic tracking template
│   │   └── spike.yml               # Research/spike template
│   ├── PULL_REQUEST_TEMPLATE.md     # PR template
│   ├── CODEOWNERS                   # Code ownership rules
│   ├── labels.json                  # Label definitions for import
│   └── dependabot.yml               # Dependabot configuration
│
├── src/                              # All source code
│   ├── __init__.py
│   ├── config/                       # Configuration system
│   │   ├── __init__.py
│   │   ├── loader.py                # ConfigLoader class
│   │   └── models.py               # Pydantic config models
│   │
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                  # Declarative base + mixins
│   │   ├── database.py             # Engine, session factory
│   │   ├── keyword.py              # Keyword model
│   │   ├── gig.py                  # Gig model
│   │   ├── seller.py               # Seller model
│   │   ├── scores.py               # KeywordScore model
│   │   ├── ranking.py              # OpportunityRanking model
│   │   ├── recommendation.py       # Recommendation model
│   │   ├── associations.py         # M2M associations
│   │   ├── search_result.py        # SearchResult model
│   │   ├── external_signal.py      # ExternalSignal model
│   │   ├── cluster.py              # ClusterAnalysis model
│   │   ├── competitor.py           # CompetitorAnalysis model
│   │   ├── gig_quality.py          # GigQualityScore model
│   │   ├── seller_score.py         # SellerScore model
│   │   ├── price_analysis.py       # PriceAnalysis + NichePriceAnalysis
│   │   ├── discovery.py            # DiscoveryOutcome + DiscoveryCycleLog
│   │   ├── visual.py               # GigVisualAnalysis model
│   │   ├── llm_usage.py            # LLMUsageLog model
│   │   ├── llm_cache.py            # LLMCache model
│   │   ├── run_log.py              # RunLog model
│   │   ├── job.py                  # Job model
│   │   ├── alert.py                # Alert model
│   │   ├── auto_promotion.py       # AutoPromotionLog model
│   │   ├── order.py                # Order model (revenue tracking)
│   │   ├── niche.py                # NicheConfig model
│   │   └── init_db.py              # Database initialization script
│   │
│   ├── collection/                   # Data collection engine
│   │   ├── __init__.py
│   │   ├── session_manager.py      # Playwright browser management
│   │   ├── selectors.py            # Fiverr CSS selectors
│   │   ├── pacing.py               # PacingManager
│   │   ├── queue.py                # QueueProcessor
│   │   ├── checkpoint.py           # CheckpointManager
│   │   ├── proxy.py                # ProxyLayer (pluggable)
│   │   └── workflows/              # Collection workflows
│   │       ├── __init__.py
│   │       ├── keyword_expansion.py
│   │       ├── fiverr_search.py
│   │       ├── gig_detail.py
│   │       ├── seller_profile.py
│   │       ├── google_trends.py
│   │       ├── reddit_signals.py
│   │       ├── autocomplete.py
│   │       └── auto_promotion.py
│   │
│   ├── analysis/                     # Analysis engine
│   │   ├── __init__.py
│   │   ├── clustering.py           # Keyword clustering
│   │   ├── gig_quality.py          # Gig quality rubric
│   │   ├── competitor_profiling.py # Competitor analysis
│   │   ├── seller_strength.py      # Seller authority model
│   │   ├── saturation.py           # Saturation model
│   │   ├── review_analysis.py      # Review red flag detection
│   │   └── intent_classifier.py    # Keyword intent classification
│   │
│   ├── scoring/                      # Scoring engine
│   │   ├── __init__.py
│   │   ├── demand.py               # Demand score
│   │   ├── competition.py          # Competition score
│   │   ├── opportunity.py          # Opportunity score
│   │   ├── feasibility.py          # New seller feasibility
│   │   ├── profitability.py        # Profitability score
│   │   ├── intent.py               # Conversion intent score
│   │   ├── saturation_score.py     # Saturation score
│   │   ├── weakness.py             # Gig quality weakness
│   │   ├── trend.py                # Trend score
│   │   ├── confidence.py           # Confidence score
│   │   ├── final.py                # Final composite + tags
│   │   └── ranking.py              # Opportunity ranking
│   │
│   ├── llm/                          # LLM client and prompts
│   │   ├── __init__.py
│   │   ├── client.py               # LLMClient wrapper
│   │   ├── cache.py                # LLM cache layer
│   │   ├── template_renderer.py    # Jinja2 prompt renderer
│   │   └── prompts/                # Jinja2 templates
│   │       ├── gig_titles.j2
│   │       ├── tag_sets.j2
│   │       ├── package_structure.j2
│   │       ├── description_outline.j2
│   │       ├── faq_entries.j2
│   │       ├── differentiation_angle.j2
│   │       ├── buyer_persona.j2
│   │       ├── thumbnail_direction.j2
│   │       ├── upsell_structure.j2
│   │       ├── red_flags.j2
│   │       ├── niche_viability.j2
│   │       ├── pricing_strategy.j2
│   │       └── profile_optimization.j2
│   │
│   ├── pricing/                      # Pricing engine
│   │   ├── __init__.py
│   │   ├── distribution.py         # KDE price distribution
│   │   ├── entry_pricing.py        # New seller entry pricing
│   │   ├── ladder_tracker.py       # Price ladder milestone tracker
│   │   └── revenue_gate.py         # Revenue gate tracker
│   │
│   ├── discovery/                    # Discovery engine
│   │   ├── __init__.py
│   │   ├── engine.py               # Discovery loop
│   │   ├── scorer.py               # Discovery scoring + feedback
│   │   └── modes/                  # Hypothesis generators
│   │       ├── __init__.py
│   │       ├── adjacent_keyword.py
│   │       ├── adjacent_niche.py
│   │       ├── gap_exploit.py
│   │       └── trend_chase.py
│   │
│   ├── playbook/                     # Playbook engine
│   │   ├── __init__.py
│   │   ├── visual_analysis.py      # Gig thumbnail classification
│   │   ├── profile_optimizer.py    # Seller profile optimization
│   │   ├── playbook_generator.py   # 5-section playbook
│   │   └── pdf_export.py           # WeasyPrint PDF rendering
│   │
│   ├── dashboard/                    # Streamlit dashboard
│   │   ├── __init__.py
│   │   ├── app.py                  # Main Streamlit entry
│   │   ├── styles.py               # Design system CSS
│   │   ├── components.py           # Reusable UI components
│   │   ├── interactions.py         # Navigation, shortcuts, state
│   │   ├── queries.py              # Pre-built DB queries
│   │   └── pages/                  # Dashboard pages
│   │       ├── __init__.py
│   │       ├── opportunities.py
│   │       ├── keywords.py
│   │       ├── competitors.py
│   │       ├── recommendations.py
│   │       ├── run_history.py
│   │       ├── llm_costs.py
│   │       └── discovery.py
│   │
│   ├── reports/                      # Report generation
│   │   ├── __init__.py
│   │   └── alert_manager.py        # Alert system
│   │
│   ├── exports/                      # Export system
│   │   ├── __init__.py
│   │   └── export_manager.py       # CSV, Excel, JSON, PDF, Markdown
│   │
│   ├── utils/                        # Shared utilities
│   │   ├── __init__.py
│   │   ├── logging.py              # Structured logging
│   │   ├── datetime.py             # Date/time helpers
│   │   ├── validation.py           # Data validation
│   │   ├── export.py               # Export path helpers
│   │   ├── hashing.py              # SHA-256, Jaccard
│   │   └── integrity.py            # Post-run integrity checks
│   │
│   ├── scripts/                      # One-off scripts
│   │   ├── __init__.py
│   │   ├── import_seeds.py         # Seed keyword import
│   │   └── backup_db.py            # Database backup
│   │
│   └── orchestrator.py              # RunOrchestrator — master pipeline
│
├── tests/                            # All tests
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/                        # Unit tests (mirror src/ structure)
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_scoring.py
│   │   ├── test_analysis.py
│   │   ├── test_collection.py
│   │   ├── test_llm.py
│   │   ├── test_pricing.py
│   │   ├── test_discovery.py
│   │   ├── test_playbook.py
│   │   └── test_utils.py
│   ├── integration/                 # Integration tests
│   │   ├── test_pipeline.py
│   │   ├── test_collection_e2e.py
│   │   └── test_dashboard.py
│   ├── performance/                 # Performance benchmarks
│   │   └── benchmark.py
│   └── fixtures/                    # Test data
│       ├── sample_config.yaml
│       ├── sample_keywords.json
│       ├── mock_gigs.json
│       └── mock_llm_responses.json
│
├── data/                             # Runtime data (gitignored)
│   ├── seeds/                       # Seed keyword YAMLs
│   ├── exports/                     # Generated exports
│   ├── screenshots/                 # Gig thumbnails
│   ├── checkpoints/                 # Run checkpoints
│   ├── backups/                     # Database backups
│   └── browser_profile/            # Playwright persistent context
│
├── docs/                             # Project documentation
│   ├── ARCHITECTURE.md              # System architecture overview
│   ├── SETUP.md                     # Installation + first run
│   ├── CONFIG_REFERENCE.md          # Config.yaml field reference
│   ├── TROUBLESHOOTING.md           # Common issues + fixes
│   └── MAINTENANCE.md               # Regular maintenance tasks
│
├── .env.example                      # Environment variable template
├── .gitignore                        # Git ignore rules
├── .cursorrules                      # Cursor agent behavior rules
├── config.yaml                       # Master configuration
├── run.py                            # CLI entry point
├── pyproject.toml                    # Project metadata + dependencies
├── requirements.txt                  # Pinned dependency versions
├── README.md                         # Project overview
├── CONTRIBUTING.md                   # Contribution guidelines
└── CHANGELOG.md                      # Version changelog
```

---

## Directory Ownership by Epic

| Directory | Primary Epic | Agent Assignment |
|---|---|---|
| src/config/, src/models/, src/utils/ | Epic 01 (Foundation) | Agent 1 — Infrastructure |
| src/collection/ | Epic 02 (Collection) | Agent 2 — Collection |
| src/analysis/ | Epic 03 (Analysis) | Agent 3 — Analysis/Scoring |
| src/scoring/ | Epic 04 (Scoring) | Agent 3 — Analysis/Scoring |
| src/llm/ | Epic 01 + 05 (Foundation + Recommendations) | Agent 1 → Agent 3 |
| src/pricing/ | Epic 06 (Pricing) | Agent 3 — Analysis/Scoring |
| src/discovery/ | Epic 07 (Discovery) | Agent 3 — Analysis/Scoring |
| src/playbook/ | Epic 08 (Playbook) | Agent 4 — Dashboard/UX |
| src/dashboard/, src/reports/, src/exports/ | Epic 09 (Dashboard) | Agent 4 — Dashboard/UX |
| tests/ | Epic 10 (Integration) | All agents + Agent 1 lead |
| .github/ | Cross-cutting | Agent 1 — Infrastructure |

---

## Gitignored Paths

These directories contain runtime data and must NEVER be committed:

```
data/
.env
*.pyc
__pycache__/
*.db
*.sqlite3
.playwright/
data/browser_profile/
data/screenshots/
data/checkpoints/
data/backups/
data/exports/
dist/
build/
*.egg-info/
.mypy_cache/
.pytest_cache/
.coverage
htmlcov/
```
