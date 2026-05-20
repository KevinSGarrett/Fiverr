# HYDRATION HEADER — Cycle 029
# Updated: 2026-05-19
# All 3 new operator rules (R-090, R-091, R-092) take effect this cycle.

## Cycle 028 Closed — Verified Outcomes

Workflow 2 partial real (Google Suggest + dedup), Workflow 6 Google Trends REAL pytrends,
weakness.py wired to GigQualityScore (top-10 filtered after Codex fix), Workflow 7 stub.
1608 tests, 95.04% coverage. PR #32 ready to merge. 3 Codex VALID_FIXED. Checklist PASS.

## PM Verification (Master Protocol Parts 1-8 Completed)

- All 4 agent reports read in full
- All 11 claimed files verified on disk (list_directory)
- Live Jira API: 17 keys verified, zero discrepancies vs. agent claims
- Codex raw GraphQL: 3 threads, all isResolved=true confirmed
- PM Pack files updated with verified state

## ⚠️ THREE NEW PERMANENT RULES IN EFFECT THIS CYCLE

### R-090: Task Sizing Standard
Every agent prompt now has 4-8 MEANINGFUL TASKS labeled SMALL / MEDIUM / LARGE.
NOT 16-24 micro-actions. Sub-steps go INSIDE tasks as numbered bullets.
Each prompt has a TIME BUDGET BLOCK at the top.
See: PM_Pack/01_pm_instructions/AGENT_PROMPT_TEMPLATE.md

### R-091: Stale Branch Cleanup
Agent A deletes merged cycle branch from remote + local after every PR merge.
Periodic full cleanup every 5 cycles (030, 035, 040).
See: PM_Pack/05_github_protocol/GITHUB_RULES.md Rule G-005

### R-092: Coverage Audit Consolidation (BIG PERFORMANCE WIN)
- Agents A/B/C: Run ONLY targeted patch coverage on THEIR module (fast, seconds)
- Agent D: Single comprehensive audit (full pytest + per-module coverage) ONCE before PR
- Codecov on PR: The canonical coverage gate (was always the canonical gate)
Expected effect: 50-65% reduction in agent execution time, no safety loss.
See: PM_Pack/05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md

## Current State

- PR gate: #32 (cycle/028/integration → develop) — READY TO MERGE
- Tests: 1608 | Coverage: 95.04% | codecov/patch: 100% | Codex: 3 VALID_FIXED (all resolved)
- Cycle 028 control: SCRUM-517 (In Progress → Done after PR #32 merge)
- Cycle 029 control: SCRUM-518 (to be created by Agent A)

## Hard Gate (Permanent, Every PR)
- codecov/patch >= 90%: HARD BLOCKER
- Codex query + classify + fix + reply + resolve: MANDATORY
- Agent D merge gate checklist: ALL PASS/YES
- (NEW) R-091 branch cleanup performed by Agent A

## Cycle 029 Focus

Three highest-priority gaps remaining (verified from spec + code review):
1. Workflow 5 (Seller Profile) real Playwright implementation — helpers ready
2. Workflow 2 LLM steps (2c/2d/2f) — LLM keyword gen, relevance filter, intent classification
3. Workflow 7 (Reddit) real praw implementation — requires REDDIT credentials

## Binding Rules

- Work only from C:\Fiverr\Fiverr
- All real Playwright code guarded by dry_run parameter (default True)
- Tests use AsyncMock/MagicMock — NO real browser in automated tests
- data/sessions/ gitignored — never stage session files
- (R-092) Agents A/B/C: skip full validation block, run ONLY targeted patch coverage
- (R-091) Agent A: delete cycle/028/integration after merging PR #32
