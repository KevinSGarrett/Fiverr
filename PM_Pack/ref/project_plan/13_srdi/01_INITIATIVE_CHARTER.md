# 01 — SRDI Initiative Charter
# Search Relevance & Data Integrity ("Bulletproof")
# Fiverr Research System

**Status:** Active — All epics specified + Jira implementation complete  
**Owner:** PM / Agent A  
**Created:** 2026-05-29 (Cycle 049)  
**Source:** WAVE_A + waves B–L  

---

## 1. EXECUTIVE SUMMARY

The Fiverr Research System collects Fiverr search results, computes seven scoring components
(demand, competition, opportunity, feasibility, profitability, intent, weakness), folds them into
a Final Score with a Confidence Modifier, and emits GO/PASS recommendations.

Every scoring formula rests on one unverified assumption:

> `SearchResult(keyword_id=K)` → gigs that **genuinely compete** for keyword K.

The problem catalog (WAVE_A) documents **20 distinct ways this assumption fails** — from semantic
broadening and cross-category contamination, to ghost markets, zombie gigs, sponsored placements,
and a discovery feedback loop that can amplify a single bad signal into a portfolio of phantom-market
recommendations. When the assumption fails, all seven scores can be corrupted **simultaneously**.
The system has **no layer today** that verifies whether gigs are actually relevant to the keyword.

This initiative installs that missing layer — at collection (category-constrained search), after
collection (rule-based Stage 3.5 validation), inside every scoring calculator (qualified inputs),
at the LLM boundary (conditional Stage 7.5 relevance gate), around autonomous discovery (4 gates),
and across external signals. Every signal is surfaced to the operator and the first recommendation
is gated behind a strict quality check.

**The single highest-leverage change** is the category filter in the Stage 3 search URL (Story 2.8.2
in `COLLECTION_WORKFLOWS.md`, never implemented). It removes the majority of contamination at source.

---

## 2. PROBLEM STATEMENT

Recommendations can be confidently wrong. "fiverr gig seo" can return thousands of Google-SEO gigs,
score as accessible, earn a CONDITIONAL_GO, and send a seller into a market that does not exist.
The data was real — but described the **wrong market** — and nothing in the pipeline noticed.

**Why now:** The system is at Cycle 049 with no live recommendation yet acted on. This is the last
moment to install integrity controls before the first recommendation is generated.

**Opportunity:** The same controls unlock emerging niche discovery. Today the demand calculator
penalizes emerging keywords for being absent from autocomplete (Issue 10). The relevance framework
distinguishes "no market" from "new market," enabling first-mover opportunities.

---

## 3. GOALS, NON-GOALS, SUCCESS CRITERIA

### 3.1 Goals
1. No recommendation generated from a ghost-market or critically-contaminated result set (hard block).
2. Every score knows input quality and qualifies output and confidence accordingly.
3. Discovery feedback loop never learns from invalid (ghost) or contaminated outcomes.
4. Every integrity signal visible to operator at decision time (badges, score breakdown, alerts, run summary).
5. Emerging/new niches no longer systematically under-scored for being new.
6. All changes are additive, toggle-guarded, backward compatible, 120+ tests + 18 permanent regressions.

### 3.2 Non-Goals
- Not re-architecting scoring weights or recommendation tiers (only inputs/qualifiers change).
- Not removing or renaming any existing field, table, or behavior (purely additive).
- Not building a general-purpose relevance ML model (rule-based first, LLM only for ambiguous band).
- Not scraping competitor images/faces or bypassing Fiverr bot-protection.
- Not changing the 9 production niches (framework must make adding a 10th safe).

### 3.3 Success Criteria (monthly KPIs)

| Metric | Target |
|---|---|
| Ghost-market rate per niche | < 8% |
| Avg result-set relevance | > 0.78 |
| Sponsored exclusion rate | 5–25% (expected band) |
| Zombie exclusion rate | < 20% |
| Category-filter fallback rate | < 10% |
| Discovery rejection rate | 20–40% (healthy gate) |
| Discovery feedback validity | > 80% valid outcomes |
| First recommendation | Passes strict quality gate + operator review |

---

## 4. SCOPE

### 4.1 In scope
- **Stage 3:** category-constrained URLs, fallback hierarchy, sponsored/organic counts, strictness recorded
- **Stage 3.5 (NEW):** rule-based result-set validation, per-gig relevance flags, ghost-market detection
- **Stage 4 / 4.5:** sponsored-flag propagation to `Gig`, zombie detection, pagination normalization
- **Stage 5:** category specialization + last-active signals
- **Scoring (all 7 + confidence + opportunity):** qualified TRC, reliability, sponsored/zombie/relevance filters
- **Stage 7.5 (NEW, conditional):** LLM relevance classification for ambiguous band; synthesis pre-filter
- **Discovery (Stage 16):** four gates (hypothesis specificity, pre-collection dry-run, outcomes, feedback)
- **External signals:** Trends qualifier, Reddit buyer-intent ratio, YouTube legitimacy gate, autocomplete emerging
- **Schema:** 2 new models + additive columns on 6 tables; 6 migrations + indexes
- **Dashboard:** badges, integrity tab, 6 new alert types, run-summary relevance block, opportunities filters
- **Edge cases / maintenance:** monitors, versioning, monthly audit, new-niche onboarding checklist
- **Testing:** full unit/integration/regression suite + fixtures (120+ tests, 18 permanent regressions)

### 4.2 Out of scope
- Per-keyword competitor profiles for all keywords (high-contamination path only; full = V1.1)
- Cross-platform (Google) keyword validation (V1.5)
- TRC benchmarking database (V1.3), buyer-persona intent matching (V1.4)
- Migration off SQLite, React dashboard, Celery (existing v2 roadmap; unaffected)

---

## 5. HIGH-LEVEL TIMELINE

| Phase | Tier | Epics | Gate |
|---|---|---|---|
| Phase 1 (weeks 1–4) | Tier 0 | R8 → R1 → R3 → R2 | First-recommendation quality gate armed |
| Phase 2 (weeks 5–10) | Tier 1 | R4, R6, R9 | Discovery cleared for activation |
| Phase 3 (weeks 11–16) | Tier 2 | R5, R7 | LLM relevance live; signals qualified |
| Phase 4 (weeks 17–22) | Tier 3/4 | R10, R11 | Dashboard + maintenance live |

---

## 6. GUIDING PRINCIPLES

1. **Non-destructive.** Add fields/signals; never remove. Every filter has config toggle. NULL = include.
2. **Cost-proportional.** Rules before LLM. LLM only for 0.35–0.75 relevance band.
3. **Transparent degradation.** CM deduction + dashboard badge + plain-language explanation.
4. **False-positive tolerance.** Flag and down-weight; hard blocks only for ghost markets.
5. **Architecture extensibility.** Versioned configs; new-niche checklist.
6. **Traceability.** Every change: issue → wave → epic → story → task → test → AC → surface → gate.

---

## 7. DEFINITION OF INITIATIVE COMPLETE

1. All 11 epics meet their DOD/AC (`04_DOD_AND_ACCEPTANCE.md`).
2. All 6 migrations applied + idempotent; backward compat proven on legacy rows.
3. 120+ tests pass; 18 permanent regressions (REG-13…REG-30) green every cycle.
4. Re-collection run shows ≥ 90% category-constrained searches; ghost markets surfaced + blocked.
5. First-recommendation quality gate passes for at least one keyword + operator review.
6. Zero unresolved CRITICAL open questions in registers.

---

## 8. JIRA IMPLEMENTATION STATUS

| Epic | Jira Stories | Subtasks | Labels |
|---|---|---|---|
| R1 Search URL | SCRUM-591–597 (7) | ~30 | `srdi,wave-B,tier-0,r1,collection` |
| R2 Stage 3.5 | SCRUM-605–612 (8) | ~36 | `srdi,wave-C,tier-0,r2,analysis` |
| R3 Sponsored/Zombie | SCRUM-598–604 (7) | ~28 | `srdi,wave-D,tier-0,r3,collection` |
| R4 Scoring Integrity | SCRUM-613–619, 813 (8) | ~29 | `srdi,wave-E,tier-1,r4,scoring` |
| R5 LLM Stage 7.5 | SCRUM-624–625, 816, 823, 830, 835, 841 (7) | ~32 | `srdi,wave-F,tier-2,r5,llm` |
| R6 Discovery Gates | SCRUM-626–629, 864, 868, 873, 877 (8) | ~31 | `srdi,wave-G,tier-1,r6,discovery` |
| R7 External Signals | SCRUM-620–623, 847, 851, 854, 858 (8) | ~26 | `srdi,wave-H,tier-2,r7,external-signals` |
| R8 Schema | SCRUM-583–590 (8) | ~31 | `srdi,wave-I,tier-0,r8,schema` |
| R9 Testing | SCRUM-630–633, 880, 883, 886, 893 (8) | ~26 | `srdi,wave-J,tier-1,r9,testing` |
| R10 Dashboard | SCRUM-634–640, 897 (8) | ~24 | `srdi,wave-K,tier-3,r10,dashboard` |
| R11 Edge Cases | SCRUM-641–646, 901, 906 (8) | ~27 | `srdi,wave-L,tier-4,r11,edge-cases` |

**Totals:** 85 stories, 322+ subtasks, 35 Blocks links, 410 items labeled.  
**Jira project:** SCRUM @ kevinsgarrett.atlassian.net  
**Blocking chain:** SCRUM-589 (R8) → SCRUM-591 (R1), SCRUM-598 (R3), SCRUM-605 (R2) → etc.

---

*Cross-references: `02_ARCHITECTURE_IMPACT.md`, `07_SEQUENCING_ROADMAP.md`, `03_EPIC_BREAKDOWN_MASTER.md`*
