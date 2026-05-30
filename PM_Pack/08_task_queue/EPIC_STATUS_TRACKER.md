# EPIC STATUS TRACKER
# Updated: 2026-05-30 (post Cycle 051 PM review) | Active: Cycle 052

## Active Cycle: 052 — SRDI Tier-0 R3: Sponsored & Zombie Gig Filtering
Base: develop @ 12c3866 | Branch: cycle/052/integration
Spec: PM_Pack/ref/project_plan/04_collection/SPONSORED_ZOMBIE_FILTERING.md
Mission: Stop paid placements and abandoned ("zombie") gigs from contaminating competition,
feasibility, demand, and profitability scoring; fix "10k+" review-count parsing; cap scoring at
top-10 organic gigs. Ships behind config toggles; legacy parity preserved when toggles OFF.

## SRDI Initiative Progress (Tier 0)
| Epic | Title | Tier | Cycle | Status |
| --- | --- | --- | --- | --- |
| R8 | Schema extensions & migrations | 0 | C050 | DONE (6 migrations applied + reversible) |
| R1 | Search URL & category hardening | 0 | C051 | DONE (REG-13/14; 9 niches; kw=110 held) |
| R3 | Sponsored & zombie gig filtering | 0 | **C052 (active)** | IN PROGRESS |
| R2 | Result-set relevance validation (Stage 3.5) | 0/1 | C053 (next) | TO DO (REG-15/16) |
| — | **Tier-0 gate** (R8+R1+R3+R2) | 0 | after C053 | pending |

## Score Path Analysis
- Milestone (kw=110 CONDITIONAL_GO @ 62.70) was REACHED in C051 and must be PRESERVED.
- R3 changes scoring inputs (exclude sponsored/zombie from top-10; TRC sponsored-fraction multiplier;
  zombie confidence deductions). Expected effect: cleaner competition/feasibility for contaminated
  niches; demand may DECREASE where sponsored fraction is high. Risk: kw=110 demand could move.
  GUARD: golden-run parity with toggles OFF (must match legacy exactly, AC-U3); with toggles ON,
  kw=110 must remain CONDITIONAL_GO (final >= 60, CM 1.0) or any movement must be explained and
  approved. No anchor (kw=110/96/3) may drift > 2 pts unexplained.
- support_kb_readiness (kw=110's niche) is the milestone-safety priority for any re-collection.

## Open Stories With DoD Conditions (Cycle 052)
- Cycle control task (Agent A creates) — Done only after PR merge + all gates PASS.
- Agent B story (R3 implementation) — DoD: migration_07 applied+reversible; zombie detector with
  new-seller guard; sponsored flag propagation; parse_review_count fix; Stage 4.5 wiring; scoring
  exclusions in 4 calculators; REG-17/18/19 green; full suite >= 3500; kw=110 CONDITIONAL_GO held.
- Agent E story (live validation, docs-only) — DoD: live-sample sponsored-flag presence in gig_cards
  per niche; observed zombie-signal availability (member_since, last_reviewed_at, response_rate,
  orders_in_queue) per niche; recommended enable_* defaults; corrections flagged to B; report only.

## New Jira Tickets To Create (Agent A, Cycle 052)
- Cycle 052 control Task: "Cycle 052: SRDI Tier-0 R3 Sponsored & Zombie Gig Filtering (6-Agent)"
- Agent B Story: "E02/B Cycle 052: sponsored flag propagation + zombie_gig_detector + scoring exclusions + migration_07"
- Agent E Story: "E02/E Cycle 052: live sponsored/zombie signal availability validation (9 niches)"
- Link all three under Epic SCRUM-17 (E02 Collection).
- R3 roadmap stories already exist in Jira: SCRUM-598..SCRUM-604 — Agent A links/comments; Agent D
  transitions the ones whose DoD this cycle fully meets (verify each before transitioning; do NOT
  mark Done if DoD unmet — and do NOT only comment-then-leave-To-Do as happened with SCRUM-591/597).

## Schema & Config Deltas (Cycle 052)
- migration_07 (NEW): gigs.zombie_score REAL, gigs.zombie_signals TEXT(JSON), gigs.last_reviewed_at
  TIMESTAMP, search_results.pages_collected INTEGER. Idempotent ALTER + rollback + ORM Mapped columns.
  (R8 already supplied gigs.is_sponsored/is_zombie, search_results.sponsored_gig_count/organic_gig_count/organic_trc.)
- config.yaml: ADD `relevance:` block with enable_sponsored_exclusion + enable_zombie_filter (+ any
  thresholds the spec needs). Config gate RELAXED for ONLY these additions; scrapfly.enabled stays
  false; reddit devvit_bridge intact.

## Regression Pack
- Current: 15 (REG-13/14 + accumulated). Cycle 052 -> 18 (append REG-17/18/19; do NOT renumber).
- REG-15/16 reserved for R2 (Cycle 053) — temporary numbering gap is expected and correct.

## Carry-Forward / Governance (from C051 review)
- Agent C must NOT edit src/ (C051 violation c6489b9). D's attribution gate must check ALL in-range
  src/ commits (not just latest); a no-op "attribution touch-up" commit is NOT an acceptable fix.
- Verify/register the two C051 Codex-fix tests (strictness/count pairing; migration-default NONE
  guard) in Section 7 if missing. Preserve the migration-default-NONE guard (interacts with R3).
- Commit HYDRATION_HEADER + this tracker + AGENT_EXECUTION_STRATEGY on the cycle/052 branch; untrack
  coverage.xml (`git rm --cached`) + gitignore it and the PM_Pack scratch files.
- DL-207 lock revisit in next clean live-validation window.

## Standard (effective C052) — see AGENT_EXECUTION_STRATEGY §8
- 25 tasks min per agent (LARGE-XXXLARGE), all substantive (no filler).
- Prompt length: A>=810, B>=945, E>=810, C>=675, F>=810, D>=945 (total >= 4995).
