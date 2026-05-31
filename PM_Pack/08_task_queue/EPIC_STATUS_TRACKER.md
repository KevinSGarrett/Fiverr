# EPIC STATUS TRACKER
# Updated: 2026-05-31 (post Cycle 052 PM review) | Active: Cycle 053

## Active Cycle: 053 — SRDI Tier-0 R2: Result-Set Relevance Validation (Stage 3.5)
Base: develop @ badb981 | Branch: cycle/053/integration
Spec source: Jira SCRUM-605..612 (full AC/DoD) + 13_srdi/07_SEQUENCING_ROADMAP (C4 + Tier-0 gate)
Mission: Insert a NEW Stage 3.5 between search-collection (Stage 3) and gig_detail (Stage 4) that
validates whether the returned result set is actually relevant to the searched keyword/niche before
anything is scored. Detect ghost markets (Fiverr returns results but <20% are about the keyword) and
category contamination; deduct confidence by relevance tier; and HARD-BLOCK recommendations for ghost
markets (even when forced). Ships behind enable_stage_3_5; legacy parity preserved when OFF (AC-U3).
KPI: ghost-market rate < 8%. R2 CLOSES the Tier-0 gate.

## SRDI Initiative Progress (Tier 0)
| Epic | Title | Tier | Cycle | Status |
| --- | --- | --- | --- | --- |
| R8 | Schema extensions & migrations | 0 | C050 | DONE (migration_01..06 applied + reversible) |
| R1 | Search URL & category hardening | 0 | C051 | DONE (REG-13/14; 9 niches; kw=110 held) |
| R3 | Sponsored & zombie gig filtering | 0 | C052 | DONE (REG-17/18/19; migration_07; kw=110 held; PR #61) |
| R2 | Result-set relevance validation (Stage 3.5) | 0 | **C053 (active)** | IN PROGRESS (REG-15/16) |
| — | **Tier-0 gate** (R8+R1+R3+R2) | 0 | at end of C053 | pending sign-off |
| R4 | Scoring quality-aware (Tier-1 head) | 1 | C054 (next) | TO DO (REG-20/21/22) |

## Score Path Analysis
- Milestone kw=110 CONDITIONAL_GO @ 62.70 was REACHED in C051 and PRESERVED through C052 (R3). Must
  remain CONDITIONAL_GO through C053 (R2).
- R2 changes scoring inputs ONLY through RSV reads (confidence deduction by relevance tier; competition
  top-10 filtered to relevance_flag when RSV<0.80; demand qualified_trc = trc * relevance when RSV<0.80;
  ghost hard-block in eligibility). Expected effect: contaminated/ghost keywords lose confidence and may
  be blocked; clean keywords (RSV>=0.80) are UNCHANGED. kw=110 (support_kb_readiness) is a real,
  relevant niche -> expected RSV high -> kw=110 should be unaffected.
  GUARD: golden-run parity with enable_stage_3_5 OFF must equal legacy exactly (AC-U3); with it ON,
  kw=110 must remain CONDITIONAL_GO (final >= 60, CM 1.0) or any movement explained + approved. No
  anchor (kw=110/96/3) may drift > 2 pts unexplained. Backward-compat: a keyword with NO RSV row scores
  identically to the pre-SRDI baseline.
- support_kb_readiness (kw=110's niche) remains the milestone-safety priority for any re-collection.

## Open Stories With DoD Conditions (Cycle 053)
- Cycle 053 control task (Agent A creates) — Done only after PR merge + all gates PASS.
- Agent B story (R2 implementation) — DoD: result_set_validator.py (compute_gig_relevance +
  validate_result_set + NICHE_VALIDATION_CONFIG 9 niches); Stage 3.5 orchestrator with UPSERT +
  fail-soft + toggle; scoring hooks (confidence/competition/demand) backward-compatible; ghost hard
  block in eligibility (fires even when forced) + tag demotion + alert row + resolution surface;
  per-gig flag propagation; migration_08 (RSV.category_contamination_flag + RSV.used_fallback_strictness)
  applied + reversible; REG-15/16 green; full suite >= 3500; kw=110 CONDITIONAL_GO held; parity OFF==legacy.
- Agent E story (live validation, docs-only) — DoD: live-sample per niche the relevance signal quality
  (gig titles vs keyword; presence of off-topic / cross-category results; observed ghost-market rate);
  recommend per-niche core_terms / exclusion_terms / ghost_market_threshold to seed NICHE_VALIDATION_CONFIG;
  recommend enable_stage_3_5 default; flag corrections to B; report only (zero src/tests/config/data).
  Also revisit DL-207 (R1 URL param shape) if the live window is clean.

## New Jira Tickets To Create (Agent A, Cycle 053)
- Cycle 053 control Task: "Cycle 053: SRDI Tier-0 R2 Result-Set Relevance Validation Stage 3.5 (6-Agent)"
- Agent B Story: "E03/B Cycle 053: result_set_validator + Stage 3.5 orchestrator + scoring hooks + ghost block + migration_08"
- Agent E Story: "E03/E Cycle 053: live result-set relevance / ghost-market signal validation (9 niches)"
- Link all three under Epic SCRUM-18 (E03 Analysis Engine) — R2 lives under Analysis, not Collection.
- R2 roadmap stories already exist in Jira: SCRUM-605..SCRUM-612 (S3.15-S3.22) — Agent A links/comments;
  Agent D transitions the ones whose DoD this cycle fully meets (verify each; do NOT mark Done if DoD
  unmet; do NOT comment-then-leave-To-Do as happened historically with SCRUM-591/597).

## Schema & Config Deltas (Cycle 053)
- migration_08_r2_columns.py (NEW): result_set_validations.category_contamination_flag (BOOLEAN default 0),
  result_set_validations.used_fallback_strictness (BOOLEAN default 0). Idempotent ALTER + reversible
  rollback (R8 pattern) + register in run_srdi_r8_migrations.py + matching ORM Mapped columns on
  ResultSetValidation. EVERYTHING ELSE R2 NEEDS ALREADY EXISTS (verified live):
  - result_set_validations table (R8 migration_01): result_set_relevance_score, ghost_market_flag,
    relevance_deduction, search_strictness_used, per_gig_relevance, ghost_evidence,
    result_count/relevant_count/sponsored_count, unique(keyword_id,run_id).
  - Gig.relevance_flag + Gig.relevance_score (R8 migration_02).
  - SearchResult.rsv_id FK (R8 migration_03).
  Do NOT add denormalized result_set_relevance_score/ghost_market_flag columns to SearchResult; scoring
  reads RSV via rsv_id FK / get_result_set_validation(keyword_id, session).
- config.yaml: ADD to the EXISTING `relevance:` block ONLY: enable_stage_3_5: true,
  relevance_flag_threshold: 0.35, ghost_market_threshold_default: 0.20. Config gate RELAXED for ONLY
  these additions; scrapfly.enabled stays false; reddit devvit_bridge intact; R3 keys unchanged.
  NICHE_VALIDATION_CONFIG stays in CODE (result_set_validator.py), not config.yaml.

## Regression Pack
- Current: 18 (REG-13/14 R1 + REG-17/18/19 R3 + accumulated). Cycle 053 -> 20 (append REG-15/16; do NOT renumber).
  - REG-15 test_ghost_market_blocks_recommendation_absolutely
  - REG-16 test_trc_qualified_by_result_set_relevance_in_demand
- After C053, the SRDI Tier-0 reg set (REG-13..19 + 15/16) is complete; REG-20..30 arrive in Tier-1/2.

## Carry-Forward / Governance (from C052 review — all C051 failures verified CLOSED in C052)
- Keep the proven guardrails: Agent C verify-only / ZERO src (route fixes to B); Agent D attribution
  scan over ALL in-range commits per src/ file (every one must be Agent B; no no-op "attribution
  touch-up" commit); relaxed config gate (only the enable_stage_3_5 + 2 thresholds); single --cov=src;
  all regressions by name; golden-run parity OFF==legacy; Codex GraphQL TWICE with REAL resolution;
  DoD-verified Jira Done transitions (no comment-and-leave-To-Do).
- Cycle-053 base is develop @ badb981 (NOT c2468f5; a steward-docs commit sits above the #61 merge).
- DL-207 lock revisit in next clean live-validation window (Agent E).
- Stale stash set (cycle051/047/043/036/029/012) UNTOUCHED pending explicit PM yes/no (irreversible).
- Commit HYDRATION_HEADER + this tracker + AGENT_EXECUTION_STRATEGY (if Section 7 changes) + the new
  migration on the cycle/053 branch; keep coverage.xml untracked (already git rm --cached in C052).

## Standard (effective C052+) — see AGENT_EXECUTION_STRATEGY §8
- 25 tasks min per agent (LARGE-XXXLARGE), all substantive (no filler).
- Prompt length: A>=810, B>=945, E>=810, C>=675, F>=810, D>=945 (total >= 4995).
- §8.4 BLOCKING self-gate: before releasing prompts, PM runs (Get-Content).Count on all six, records actual-vs-floor + 25-task counts in prep notes; any prompt under floor or under 25 substantive tasks is NOT done and must be expanded with genuine content then re-verified. (Added v1.4 after C053 shipped under-floor.)
