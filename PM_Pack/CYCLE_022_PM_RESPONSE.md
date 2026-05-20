# Cycle 022 PM Response — Root Copy
# See PM_Pack/10_cycle_log/ for full details.

## ⚠️ Protocol Corrections This Session

Two PM Pack quality failures corrected and now hard rules:

1. codecov/patch is a HARD MERGE BLOCKER — not optional, not "non-blocking."
   PRs #24 and #25 merged with patch failing. This is prohibited going forward.
   Rule G-001 added to GITHUB_RULES.md.

2. Codex review threads MUST be queried, classified, dispositioned, and resolved.
   Rule G-003 and mandatory Agent D checklist (Rule G-004) added.
   PM_CORRECTIVE_RULES_CYCLE_022.md created with R-085 through R-089.

## Cycle 021 Confirmed Complete
- 1002 tests | 93.00% coverage | Codex: 0 findings on PR #25
- New: KeywordScore ORM, run_recommendations() CLI, PriceAnalysis model,
  new_seller_pricing.py calculator, E05 e2e integration test

## Cycle 022 Scope
- Agent A: Verify codecov/patch on PR #25 before merging. Stage 14 explanation stub.
  score_keyword() into --mode full.
- Agent B: E06 S6.3 — price distribution analysis runner (analysis.py)
- Agent C: E06 S6.4 + S6.5 — pricing pipeline orchestrator + strategy text
- Agent D: Patch coverage audit+gap tests. Board. PR #26 with FULL merge gate checklist.
  Codex query + disposition on PR #26. codecov/patch MUST be PASS before merge.

## Hard Gate for PR #26
codecov/project: PASS ≥90%
codecov/patch: PASS ≥90% (HARD BLOCKER)
Codex query: run, document, classify, fix/reply, resolve ALL threads
Agent D checklist: filled in completely with no FAIL items
