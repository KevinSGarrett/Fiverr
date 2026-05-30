# 08 — SRDI Registers
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Status:** Planning-complete · **Sources:** Waves A–L + live codebase  
**Six registers:** Decisions · Assumptions · Risks · Dependencies · Open Questions · Contradictions/Gaps

---

## 1. DECISION REGISTER

### 1.1 Architecture Decisions (AD)

| ID | Decision | Rationale | Status |
|---|---|---|---|
| AD-1 | Stage 3.5 rule-based; LLM is Stage 7.5, conditional | Cost-proportional; rules clear clean/contaminated ends | LOCKED |
| AD-2 | NULL relevance/sponsored/zombie = "include" | Backward compat; legacy rows never penalized | LOCKED |
| AD-3 | Ghost market is the **only HARD block**; everything else flags/down-weights | False-positive tolerance | LOCKED |
| AD-4 | Schema is additive only (ALTER ADD COLUMN + new tables) | No destructive migration; trivially reversible | LOCKED |
| AD-5 | `result_set_relevance_score` qualifies TRC multiplicatively | Preserves log10 normalization untouched | LOCKED |
| AD-6 | Per-keyword competitor profile only when contamination detected | Avoids cost/complexity (full = V1.1) | LOCKED |
| AD-7 | Discovery records `is_invalid` (ghost) distinctly from `is_miss` | Ghost ≠ low score; must not teach LLM to avoid | LOCKED |
| AD-8 | Constrained TRC needs no demand.py formula change | Constrained search yields corrected count directly | LOCKED |

### 1.2 Resolution Decisions (DEC)

| ID | Decision | Resolves | Status |
|---|---|---|---|
| DEC-1 | Trends qualifier base = **0.65** (not 0.70) + slope/intent/breadth modifiers, clamped [0.20,0.95] | WAVE_E vs WAVE_H conflict | LOCKED |
| DEC-2 | Append REG-13…30 to live `AGENT_EXECUTION_STRATEGY.md §7` without renumbering existing entries | Wave 12-name pack vs live extended pack | LOCKED |
| DEC-3 | R3.2.3 sponsored TRC bands active until R4 ships; R4.1 multiplier supersedes; never stack both | WAVE_D vs WAVE_E | LOCKED |
| DEC-4 | Ghost threshold: per-niche config if present, else global 0.20 | Config key vs hardcoded 0.20 | LOCKED |
| DEC-5 | Stage 4 collect all by default; relevance-gated collection is opt-in toggle (OFF) | WAVE_C optional gate vs audit preservation | LOCKED |
| DEC-6 | YouTube weight = 0 in demand blend (informational only) | WAVE_H reframing; re-baseline required | LOCKED |
| DEC-7 | Both NICHE_CATEGORY_MAP URL shapes stored; R1.6.2 sweep selects live one | WAVE_B dual shapes | PROVISIONAL → closes at R1.6.2 sweep |
| DEC-8 | First-recommendation gate is additional one-time stricter pre-check, not replacement | WAVE_L §5.2 interpretation | LOCKED |

---

## 2. ASSUMPTION REGISTER

| ID | Assumption | Used By | Fallback If False |
|---|---|---|---|
| A1 | Fiverr honors a `category_id`-bearing search URL param | R1 | Degrade to NONE + full reliance on R2/R5 |
| A2 | `profitability.py` reads premium price from `metadata_json.premium_price` | R4.5.3 | Read from packages; no logic change |
| A3 | Live async LLM client exists with `complete_async`-style method | R5 | Adapt to live wrapper method name |
| A4 | `collect_search_page_minimal` exists or is trivially buildable | R6 | Implement thin page-1 wrapper |
| A5 | Stage-6 exposes `trends_12mo_score`, `trends_slope`, `trends_related_queries` | R7 | Adapt key/method names in storage loop |
| A6 | `SearchResult` has `collected_at` column | R7 freshness, R8 | Add as additive column (coordinate R8) |
| A7 | `external_signals` has `created_at` and `raw_value_json` | R7, R8 | Add via additive migration |
| A8 | `alert.py` supports or can gain `alert_type`, `severity`, `metadata` | R10 | Add additive columns (coordinate R8) |
| A9 | Dashboard is Streamlit supporting `st.badge` or markdown-chip fallback | R10 | Render markdown chips |
| A10 | Live baseline test count is ≈ 3334 | R9 | Measure; set regression floor to actual |
| A11 | Single recommendation-gate entry point exists to hook first-rec gate | R11 | Wire at recommendation assembly site |
| A12 | Per-niche rolling history (≥3 prior runs) available or definable for monitors | R11 | Add small history table or aggregate query |
| A13 | Migration harness is Alembic/custom runner/raw-SQL-on-startup | R8 | Author M1–M6 in whichever live format |
| A14 | No routine keyword deletion (so RSV delete-orphan cascade is safe) | R8 | Switch RSV to soft-delete |

---

## 3. RISK REGISTER

### Initiative-Level Risks

| ID | Risk | P | I | Mitigation |
|---|---|---|---|---|
| IR-1 | Consuming epic ships before R8 → missing-column crash | M | H | Hard ordering R8 first; CI schema-presence assert |
| IR-2 | Aggregate false-positive rate too high → operator distrust | M | H | Flag don't block (except ghost); KPI bands monitored monthly |
| IR-3 | Score distributions shift after R4/R7 | M | M | Re-baseline on frozen golden run before/after each scoring epic |
| IR-4 | Fiverr changes markup/algorithm mid-initiative → filters degrade silently | M | H | R11 monitors + monthly audit |
| IR-5 | LLM cost/latency creeps as discovery runs grow | L | M | 50-call cap, cache, highest-score-first ordering |
| IR-6 | Scope creep from V1.1+ items | M | M | Roadmap fence; V1.x items explicitly out-of-scope |
| IR-7 | Partial rollout leaves inconsistent state | M | M | `search_strictness_used` recorded per row; staged re-collect plan |

### Key Epic-Level Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1-RISK-1 | Fiverr ignores category params → filter ineffective | R11 `CategoryFilterHealthMonitor` |
| R2-RISK-1 | core/exclusion terms too strict → legitimate kw flagged ghost | Per-gig table surfaced to operator; quarterly review |
| R3-RISK-1 | Zombie filter excludes real new competitor | New-seller disambiguator + "all gigs filtered → fallback" |
| R4-RISK-1 | Stacked TRC multipliers crush demand for clean keywords | Single-multiplier rule (DEC-3) + dedicated regression |
| R5-RISK-1 | LLM over-flags BORDERLINE as IRRELEVANT | BORDERLINE is non-destructive; only RELEVANT/IRRELEVANT mutate |
| R6-RISK-1 | Over-aggressive gating starves discovery (>40% rejection) | KPI band 20–40% monitored; thresholds config-tunable |
| R7-RISK-3 | Demand shift after YouTube→0 | Weights unchanged; re-baseline required (DEC-6) |
| R8-RISK-1 | SQLite `ALTER ADD COLUMN` limits | All adds nullable/simple-default; verified on live engine |
| R11-RISK-3 | First-rec gate too strict → blocks legitimate first rec | Gate lists actionable issues; operator can re-collect to clear |

---

## 4. DEPENDENCY REGISTER

| ID | Dependency | Type | Blocks |
|---|---|---|---|
| DEP-1 | R8 schema present before any R1–R7 read/write of new columns | Hard | R1–R7, R9, R10 |
| DEP-2 | R1 constrained search live before R2/R4 trust the result set | Hard | R2, R4 |
| DEP-3 | R3 sponsored/zombie flags before R4's reliability multiplier | Hard | R4 |
| DEP-4 | R2 `result_set_relevance_score` before R5 trigger band | Hard | R5 |
| DEP-5 | R6 discovery provenance before discovery is reactivated | Hard | Discovery activation |
| DEP-6 | Shared autocomplete classifier used by both R4 and R7 | Soft | R4, R7 |
| DEP-7 | `gpt-4o-mini` availability + pinned model ID | External | R5 |
| DEP-8 | Frozen golden run for before/after re-baseline | Process | R4, R7 |
| DEP-9 | Fiverr site markup/category taxonomy stable enough to parse | External | R1, R3 |
| DEP-10 | Live migration harness identified before M1–M6 authored | Internal | R8 |

---

## 5. OPEN-QUESTION REGISTER

| ID | Question | Default Until Closed |
|---|---|---|
| R1-OQ-1 | Which URL param shape does live Fiverr honor today? | Build both; R1.6.2 sweep decides (DEC-7) |
| R1-OQ-2 | Are the 9 hardcoded `category_id`s still current? | Validate; map is versioned |
| R2-OQ-1 | Stage 4: collect only relevant gigs (WAVE_C §1.1 gate)? | OFF by default (DEC-5) |
| R3-OQ-1 | Are `review_snippets`/`orders_in_queue`/`response_rate` reliably populated? | Detector tolerates missing fields |
| R4-OQ-2 | `profitability.py` premium price source? | `metadata_json.premium_price` (A2) |
| R5-OQ-1 | Exact live LLM client signature? | Adapt to live wrapper (A3) |
| R6-OQ-1 | Does `collect_search_page_minimal` exist? | Build thin page-1 wrapper if absent (A4) |
| R6-OQ-3 | Is the discovery engine currently activated? | If off, R6 precedes activation (DEP-5) |
| R7-OQ-3 | Is YouTube currently weighted in demand? | If weighted, log as scored change + DEC-6 |
| R8-OQ-1 | Migration harness type? | Author M1–M6 in live format (A13) |
| R9-OQ-1 | Live test runner + baseline count (≈3334?) | Measure; set floor (A10) |
| R10-OQ-3 | Where is the run-summary printed? | Locate printer; insert relevance block |
| R11-OQ-1 | Source of historical sponsored/relevance averages for monitors? | Define small history store (A12) |

---

## 6. CONTRADICTION / GAP REGISTER

| ID | Conflict | Resolution |
|---|---|---|
| CG-1 | Regression pack described as 12 names vs live §7 extended pack | Append REG-13…30; no renumber (DEC-2) |
| CG-2 | Trends qualifier base 0.70 vs 0.65 | Standardize on 0.65 + modifiers (DEC-1) |
| CG-3 | Sponsored TRC adjustment appears twice (WAVE_D bands + WAVE_E single multiplier) | R3 bands active until R4; then R4 subsumes; never stack (DEC-3) |
| CG-4 | Ghost threshold: per-niche config vs hardcoded 0.20 | Per-niche if present, else 0.20 (DEC-4) |
| CG-5 | Two Fiverr search-URL param shapes | Store both; sweep selects (DEC-7) |
| CG-7 | YouTube weighted demand input vs informational-only | Set weight 0; re-baseline (DEC-6) |
| CG-10 | GAP: no per-niche rolling history store for R11 monitors | Define history table in developer handoff (A12) |
| CG-11 | GAP: `is_invalid`/`is_contaminated` may not exist on `DiscoveryOutcome` yet | R8 adds via M6; R6 sets them (AD-7) |

---

*Cross-references: `02_ARCHITECTURE_IMPACT.md` (AD details), `07_SEQUENCING_ROADMAP.md` (DEP sequencing), `10_DEVELOPER_HANDOFF.md` (OQ closure)*
