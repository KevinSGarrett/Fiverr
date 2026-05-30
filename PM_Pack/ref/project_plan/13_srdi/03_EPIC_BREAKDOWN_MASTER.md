# 03 — SRDI Epic Breakdown Master
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Status:** Complete — 85 stories, 322+ subtasks in Jira  
**Source:** WAVE_A–L + per-epic files in `epics/`

---

## 1. EPIC OVERVIEW

| Epic | Title | Wave | Tier | Stories | Tasks | New Modules | Depends On |
|---|---|---|---|---|---|---|---|
| R1 | Search URL & Category Hardening | B | 0 | 7 | 30 | `search_url_builder.py` | R8 |
| R2 | Result-Set Relevance Validation (Stage 3.5) | C | 0/1 | 8 | 36 | `result_set_validator.py` | R8, R1 |
| R3 | Sponsored & Zombie Gig Filtering | D | 0 | 7 | 28 | `zombie_gig_detector.py` | R8 |
| R4 | Scoring System Integrity Extensions | E | 1 | 8 | 29 | — | R8, R1, R2, R3 |
| R5 | LLM Relevance Classification (Stage 7.5) | F | 2 | 7 | 32 | `llm_relevance_classifier.py` | R8, R2 |
| R6 | Discovery Engine Relevance Gates | G | 1 | 8 | 31 | `pre_validator.py` | R8, R1, R2 |
| R7 | External Signal Integrity | H | 2 | 8 | 26 | — | R8, R2 |
| R8 | Data Schema Extensions & Migrations | I | 0 | 8 | 31 | 2 models + 6 migrations | — (foundation) |
| R9 | Testing & Validation Framework | J | 1 | 8 | 26 | test infra + fixtures | all |
| R10 | Dashboard & Alerting Integration | K | 3 | 8 | 24 | dashboard components | all |
| R11 | Edge Cases, Future-Proofing & Maintenance | L | 4 | 8 | 27 | monitors + protocols | all |
| **Total** | | | | **85** | **320** | | |

---

## 2. DEPENDENCY GRAPH

```
                     ┌──────────────┐
                     │  R8 Schema   │  (foundation — must land first)
                     └──────┬───────┘
          ┌──────────────────┼─────────────────────┐
          ▼                  ▼                     ▼
    ┌──────────┐       ┌──────────┐          ┌──────────┐
    │ R1 URL   │       │ R3 Spon/ │          │ R7 Ext.  │
    │ category │       │ Zombie   │          │ signals  │
    └────┬─────┘       └────┬─────┘          └────┬─────┘
         │                  │                     │
         └────────┬──────────┘                    │
                  ▼                               │
            ┌──────────┐                          │
            │ R2 Stage │◄─────────────────────────┘
            │ 3.5 val  │
            └────┬─────┘
      ┌──────────┼──────────────┐
      ▼          ▼              ▼
 ┌─────────┐ ┌─────────┐  ┌─────────┐
 │ R4 Score│ │ R6 Disc.│  │ R5 LLM  │
 │ integ.  │ │ gates   │  │ 7.5     │
 └────┬────┘ └─────────┘  └─────────┘
      │
      ▼
 ┌─────────┐      ┌─────────┐
 │ R10 Dash│◄─────│ R11 Edge│
 └─────────┘      └─────────┘

R9 (tests): wraps every epic — each epic ships its own tests;
R9 owns suite structure + 18-test permanent regression pack.
```

---

## 3. STORY INDEX (all epics)

### R1 — Search URL & Category Hardening (Wave B)
| # | Story | Jira |
|---|---|---|
| R1.1 | Category map & strictness constants | SCRUM-591 |
| R1.2 | `search_url_builder.build_search_url` | SCRUM-592 |
| R1.3 | Fallback search (`search_with_fallback`) + min-threshold | SCRUM-593 |
| R1.4 | Wire into Stage 3 (`fiverr_search.py`) + record strictness/counts | SCRUM-594 |
| R1.5 | Config schema (`NicheSearchConfig`) + per-niche `config.yaml` | SCRUM-595 |
| R1.6 | Demand confidence deduction for legacy NONE + validation sweep utility | SCRUM-596 |
| R1.7 | Tests (14 unit + 4 integration + REG-13/14) | SCRUM-597 |

### R2 — Result-Set Relevance Validation / Stage 3.5 (Wave C)
| # | Story | Jira |
|---|---|---|
| R2.1 | `compute_gig_relevance` multi-signal scorer | SCRUM-605 |
| R2.2 | `validate_result_set` aggregate + ghost/contamination flags + confidence deduction | SCRUM-606 |
| R2.3 | `NICHE_VALIDATION_CONFIG` (core/exclusion terms, ghost thresholds) for 9 niches | SCRUM-607 |
| R2.4 | Stage 3.5 orchestrator (`result_set_validation_workflow.py`) | SCRUM-608 |
| R2.5 | Scoring integration hooks (CM deduction, competition/feasibility filter, demand TRC) | SCRUM-609 |
| R2.6 | Ghost-market hard block in eligibility + resolution surfacing | SCRUM-610 |
| R2.7 | Per-gig flag propagation to `Gig` + SearchResult aggregate write | SCRUM-611 |
| R2.8 | Tests (14 unit + 8 integration + REG-15/16) | SCRUM-612 |

### R3 — Sponsored & Zombie Gig Filtering (Wave D)
| # | Story | Jira |
|---|---|---|
| R3.1 | Sponsored propagation: `gig_cards` → `Gig.is_sponsored`; counts on `SearchResult` | SCRUM-598 |
| R3.2 | Sponsored exclusion in competition + feasibility; TRC adjustment in demand | SCRUM-599 |
| R3.3 | `zombie_gig_detector` (`compute_zombie_score`, `is_zombie_gig`, date parsers) | SCRUM-600 |
| R3.4 | Stage 4.5 zombie detection wiring + `last_reviewed_at` extraction | SCRUM-601 |
| R3.5 | Zombie exclusion in competition + feasibility + confidence concentration deduction | SCRUM-602 |
| R3.6 | Pagination normalization (`pages_collected`, `TOP_N_FOR_SCORING=10` cap) | SCRUM-603 |
| R3.7 | Tests (8 sponsored + 10 zombie + REG-17/18/19) | SCRUM-604 |

### R4 — Scoring System Integrity Extensions (Wave E)
| # | Story | Jira |
|---|---|---|
| R4.1 | Demand: TRC reliability qualifier (`_compute_trc_reliability`) | SCRUM-613 |
| R4.2 | Demand: autocomplete emerging distinction + trends platform qualifier | SCRUM-614 |
| R4.3 | Competition: per-keyword vs per-niche profile selection | SCRUM-615 |
| R4.4 | Competition: `CompetitorProfile` contamination outlier exclusion | SCRUM-813 |
| R4.5 | Competition + Profitability: price-outlier exclusion (IQR) | SCRUM-616 |
| R4.6 | Feasibility: clean-gig set for level ratio + organic review barrier | SCRUM-617 |
| R4.7 | Intent alignment + Opportunity relevance qualifier + KeywordScore integrity cols | SCRUM-618 |
| R4.8 | Tests (8+12 unit + REG-20/21/22) | SCRUM-619 |

### R5 — LLM Relevance Classification / Stage 7.5 (Wave F)
| # | Story | Jira |
|---|---|---|
| R5.1 | Trigger gate (`_should_run_llm`) | SCRUM-624 |
| R5.2 | `LLMRelevanceClassifier` service class | SCRUM-816 |
| R5.3 | Prompt template + `NICHE_EXPECTED_SERVICE_DESCRIPTIONS` | SCRUM-625 |
| R5.4 | Apply-back to DB (`_apply_classifications`) | SCRUM-823 |
| R5.5 | Stage 7.5 orchestrator + call-budget cap | SCRUM-830 |
| R5.6 | Competitor-synthesis relevance pre-filter | SCRUM-835 |
| R5.7 | Tests (5 unit + REG-23/24) | SCRUM-841 |

### R6 — Discovery Engine Relevance Gates (Wave G)
| # | Story | Jira |
|---|---|---|
| R6.1 | Gate 1: hypothesis prompt anti-contamination | SCRUM-626 |
| R6.2 | Gate 1: `_gate_hypotheses` specificity filter + hypothesis contract | SCRUM-864 |
| R6.3 | Gate 2: `DiscoveryPreValidator` dry-run | SCRUM-627 |
| R6.4 | Gate 2: orchestrator wiring + validated-only insert | SCRUM-868 |
| R6.5 | Gate 3: relevance-gated outcome recording | SCRUM-628 |
| R6.6 | Gate 4: feedback excludes invalid/contaminated | SCRUM-873 |
| R6.7 | Schema population (DiscoveryOutcome + Keyword cols) | SCRUM-877 |
| R6.8 | Tests (5 unit + 1 integration + REG-25/26/27) | SCRUM-629 |

### R7 — External Signal Integrity (Wave H)
| # | Story | Jira |
|---|---|---|
| R7.1 | Google Trends platform qualifier (`_compute_fiverr_relevance_qualifier`) + storage | SCRUM-620 |
| R7.2 | Demand consumes qualified Trends + signal freshness×relevance | SCRUM-847 |
| R7.3 | Signal freshness×relevance quality score | SCRUM-623 |
| R7.4 | Reddit buyer-intent ratio + qualified score | SCRUM-621 |
| R7.5 | Demand consumes qualified Reddit | SCRUM-851 |
| R7.6 | YouTube as category-legitimacy gate (confidence, not demand weight) | SCRUM-622 |
| R7.7 | Autocomplete-absence classifier (`_classify_autocomplete_absence`) | SCRUM-854 |
| R7.8 | Confidence freshness×relevance + tests + REG-28/29/30 | SCRUM-858 |

### R8 — Data Schema Extensions & Migrations (Wave I)
| # | Story | Jira |
|---|---|---|
| R8.1 | `ResultSetValidation` model (NEW table) | SCRUM-583 |
| R8.2 | `DiscoveryOutcome` extension columns | SCRUM-584 |
| R8.3 | `Gig` extension columns + indexes | SCRUM-585 |
| R8.4 | `SearchResult` extension columns + indexes | SCRUM-586 |
| R8.5 | `KeywordScore` + `Keyword` extension columns | SCRUM-587 |
| R8.6 | `ExternalSignal` extension columns | SCRUM-588 |
| R8.7 | Migration scripts M1–M6 + ordering + performance indexes | SCRUM-589 |
| R8.8 | Registration, backward compat helpers, schema regression tests | SCRUM-590 |

### R9 — Testing & Validation Framework (Wave J)
| # | Story | Jira |
|---|---|---|
| R9.1 | Test structure, conventions, baseline count, suite-count guard | SCRUM-630 |
| R9.2 | Wave B/C unit tests (8 URL + 14 validator) | SCRUM-880 |
| R9.3 | Wave D unit tests (10 zombie + 8 sponsored) | SCRUM-883 |
| R9.4 | Wave E/F/G/H unit tests (8+12+10+12+10+8 = ~60) | SCRUM-886 |
| R9.5 | Integration tests (8+6+6) | SCRUM-893 |
| R9.6 | Fixture factories (relevance_fixtures.py + contaminated_data_fixtures.py) | SCRUM-631 |
| R9.7 | Permanent regression pack REG-13…REG-30 | SCRUM-632 |
| R9.8 | Run commands + tier-completion gates | SCRUM-633 |

### R10 — Dashboard & Alerting Integration (Wave K)
| # | Story | Jira |
|---|---|---|
| R10.1 | Relevance Quality Score panel (`calculate_niche_relevance_quality_score`) | SCRUM-634 |
| R10.2 | Keyword badges (7-badge catalog + `render_keyword_integrity_badge`) | SCRUM-635 |
| R10.3 | Score-explanation Data Integrity block + tab | SCRUM-636 |
| R10.4 | Alert catalog (6 types) | SCRUM-637 |
| R10.5 | `generate_relevance_alerts_for_run` | SCRUM-638 |
| R10.6 | Run-summary relevance block + immediate ghost-market print | SCRUM-897 |
| R10.7 | Opportunities page filters (ghost hidden by default) + score-column indicators | SCRUM-639 |
| R10.8 | Dashboard test suite (12 tests) | SCRUM-640 |

### R11 — Edge Cases, Future-Proofing & Maintenance (Wave L)
| # | Story | Jira |
|---|---|---|
| R11.1 | Stealth-sponsored + relevance-cliff monitors | SCRUM-641 |
| R11.2 | Emerging-opportunity bonus + negation-aware exclusion | SCRUM-642 |
| R11.3 | Validator edge cases (negation + multilingual) | SCRUM-901 |
| R11.4 | Category-filter health monitor + legacy tagging | SCRUM-643 |
| R11.5 | Versioning & selector tracking | SCRUM-906 |
| R11.6 | Operational protocols (incident ladder + monthly audit + onboarding checklist) | SCRUM-644 |
| R11.7 | First-recommendation quality gate (5 checks) + 8 KPI hooks | SCRUM-645 |
| R11.8 | Roadmap + tests | SCRUM-646 |

---

## 4. RACI (initiative-level)

| Activity | Agent A (PM) | Agent B (impl) | Agent C (data/DB) | Agent D (QA) | Agent E (validation) |
|---|---|---|---|---|---|
| Schema/migrations (R8) | C | A | **R** | C | I |
| Search URL + Stage 3 (R1) | C | **R** | C | C | A |
| Stage 3.5 validator (R2) | C | **R** | C | C | A |
| Sponsored/zombie (R3) | C | **R** | C | C | I |
| Scoring extensions (R4) | C | **R** | I | C | I |
| LLM 7.5 (R5) | C | **R** | I | C | C |
| Discovery gates (R6) | C | **R** | I | C | C |
| External signals (R7) | C | **R** | C | C | I |
| Tests/regressions (R9) | I | C | I | **R** | I |
| Dashboard/alerts (R10) | C | **R** | I | C | I |
| Edge/maintenance (R11) | **R** | C | C | C | C |

---

*Full per-epic story/task detail in `epics/` directory. DoD/AC in `04_DOD_AND_ACCEPTANCE.md`.*
