# Search Relevance & Data Integrity Initiative — Project Plan
# 13_srdi — SRDI (Bulletproof) Initiative Directory
# Fiverr Research System

**Package ID:** SRDI-IPP  
**Initiative codename:** "Bulletproof"  
**Created:** 2026-05-29 (Cycle 049)  
**Status:** READY FOR EXECUTION — all 11 epics fully specified, Jira implementation complete  
**Source material:** 12 specification waves (WAVE_A … WAVE_L)  

---

## DIRECTORY MAP

```
13_srdi/
├── 00_SRDI_INDEX.md                 ← This file
├── 01_INITIATIVE_CHARTER.md         ← Executive summary, scope, success criteria
├── 02_ARCHITECTURE_IMPACT.md        ← Pipeline changes, new stages, data flow
├── 03_EPIC_BREAKDOWN_MASTER.md      ← All 11 epics: stories/tasks index + dependency graph
├── 04_DOD_AND_ACCEPTANCE.md         ← DoD + AC tables for every epic
├── 05_DATA_SCHEMA_MIGRATION.md      ← 6 migrations: SQL, order, rollback, idempotency
├── 06_TEST_PLAN_REGRESSION.md       ← Test taxonomy, 18 permanent regressions (REG-13…30)
├── 07_SEQUENCING_ROADMAP.md         ← Tiered rollout, cycle-by-cycle plan, agent assignments
├── 08_REGISTERS.md                  ← Decisions, Assumptions, Risks, Open Questions
├── 09_TRACEABILITY_MATRIX.md        ← Issue→wave→epic→story→task→test→AC→surface
├── 10_DEVELOPER_HANDOFF.md          ← Env, branch strategy, PR checks, file change list
├── 11_AI_AGENT_HANDOFF.md           ← Build order, per-task agent prompts, verification gates
├── 12_LAUNCH_READINESS.md           ← Go-live gates, first-recommendation quality gate
├── 13_RISK_COMPLIANCE_COST.md       ← Risk depth, ToS posture, LLM cost, observability
└── epics/
    ├── R1_SEARCH_URL_HARDENING.md
    ├── R2_RELEVANCE_VALIDATION_STAGE_3_5.md
    ├── R3_SPONSORED_ZOMBIE_FILTERING.md
    ├── R4_SCORING_INTEGRITY_EXTENSIONS.md
    ├── R5_LLM_RELEVANCE_STAGE_7_5.md
    ├── R6_DISCOVERY_RELEVANCE_GATES.md
    ├── R7_EXTERNAL_SIGNAL_INTEGRITY.md
    ├── R8_SCHEMA_EXTENSIONS_MIGRATIONS.md
    ├── R9_TESTING_VALIDATION_FRAMEWORK.md
    ├── R10_DASHBOARD_ALERTING.md
    └── R11_EDGE_CASES_MAINTENANCE.md
```

---

## THE 11 EPICS AT A GLANCE

| Epic | Title | Wave | Tier | New Stage? | Jira Stories |
|---|---|---|---|---|---|
| R1 | Search URL & Category Hardening | B | 0 | Stage 3 change | SCRUM-591–597 |
| R2 | Result-Set Relevance Validation | C | 0/1 | **Stage 3.5 (NEW)** | SCRUM-605–612 |
| R3 | Sponsored & Zombie Gig Filtering | D | 0 | Stage 4.5 (new sub-stage) | SCRUM-598–604 |
| R4 | Scoring System Integrity Extensions | E | 1 | 7 calculators changed | SCRUM-613–619, 813 |
| R5 | LLM Relevance Classification | F | 2 | **Stage 7.5 (NEW, conditional)** | SCRUM-624–625, 816, 823, 830, 835, 841 |
| R6 | Discovery Engine Relevance Gates | G | 1 | 4 gates in Stage 16 | SCRUM-626–629, 864, 868, 873, 877 |
| R7 | External Signal Integrity | H | 2 | Trends/Reddit/YT/autocomplete | SCRUM-620–623, 847, 851, 854, 858 |
| R8 | Data Schema Extensions & Migrations | I | 0 | 6 migrations | SCRUM-583–590 |
| R9 | Testing & Validation Framework | J | 1 | Test infra | SCRUM-630–633, 880, 883, 886, 893 |
| R10 | Dashboard & Alerting Integration | K | 3 | Streamlit components | SCRUM-634–640, 897 |
| R11 | Edge Cases, Future-Proofing & Maintenance | L | 4 | Monitors + protocols | SCRUM-641–646, 901, 906 |

**Total:** 85 stories, 322 subtasks, 35 Blocks issue links, 410 items labeled in Jira.

---

## PROBLEM CATALOG (20 issues this initiative fixes)

| # | Issue | Severity | Epic |
|---|---|---|---|
| 1 | Fiverr semantic broadening | CRITICAL | R1, R2 |
| 2 | Gig title keyword stuffing | HIGH | R2 |
| 3 | Sponsored result contamination | HIGH | R3 |
| 4 | Category boundary contamination | CRITICAL | R1 |
| 5 | TRC inflation for broad terms | HIGH | R4 |
| 6 | Ghost market keywords | CRITICAL | R2 |
| 7 | Zombie gig contamination | HIGH | R3 |
| 8 | Review count abbreviation parsing | MEDIUM | R3 |
| 9 | Google Trends platform-intent mismatch | HIGH | R7 |
| 10 | Autocomplete penalizing emerging niches | HIGH | R7 |
| 11 | Niche-level competitor profile contamination | HIGH | R4 |
| 12 | Gig title relevance in weakness scoring | MEDIUM | R5 |
| 13 | Discovery engine feedback-loop amplification | CRITICAL | R6 |
| 14 | Competitor synthesis LLM hallucination | HIGH | R5 |
| 15 | Freshness score masking data quality | MEDIUM | R7 |
| 16 | Price contamination from cross-category results | HIGH | R4 |
| 17 | Seller bio analysis on wrong competitors | MEDIUM | R4 |
| 18 | Conversion intent keyword-only classification | MEDIUM | R4 |
| 19 | Pagination depth inconsistency | LOW-MED | R3 |
| 20 | Collection timing staleness within a run | LOW | R8/R11 |

---

## SUCCESS CRITERIA (monthly KPIs)

| Metric | Target |
|---|---|
| Ghost-market rate per niche | < 8% |
| Avg result-set relevance | > 0.78 |
| Sponsored exclusion rate | 5–25% |
| Zombie exclusion rate | < 20% |
| Category-filter fallback rate | < 10% |
| Discovery hypothesis rejection rate | 20–40% (healthy gate) |
| Discovery feedback validity | > 80% valid outcomes |
| First recommendation | Passes strict quality gate + operator review |

---

## GUIDING PRINCIPLES (binding for every wave)

1. **Non-destructive.** Add fields/signals; never remove. Every filter has a config toggle. NULL = unknown = include.
2. **Cost-proportional.** Rules before LLM. LLM only for ambiguous 0.35–0.75 relevance band.
3. **Transparent degradation.** CM deduction + dashboard badge + plain-language explanation.
4. **False-positive tolerance.** Flag and down-weight; hard blocks only for ghost markets.
5. **Architecture extensibility.** Versioned configs; new-niche checklist.
6. **Traceability.** Every change: issue → wave → epic → story → task → test → AC → surface → gate.

---

*See `01_INITIATIVE_CHARTER.md` for full executive summary and `07_SEQUENCING_ROADMAP.md` for rollout plan.*
