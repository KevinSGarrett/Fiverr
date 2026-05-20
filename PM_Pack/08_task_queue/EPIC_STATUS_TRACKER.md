# Epic Status Tracker — Cycle 028
# Updated: 2026-05-19 | Verified via live Jira API + spec review

## Active Gate

PR #31 (cycle/027/integration → develop): READY TO MERGE.
codecov/patch 100%. Codex 1 VALID_FIXED (resolved). All checklist items PASS/YES.

## Cycle 028 Scope (From Verified Gap Analysis + Spec Read)

| Agent | Scope | Spec Source | Min Tests |
|---|---|---|---|
| A | PR #31 gate + Workflow 2 partial real (autocomplete + Google Suggest) | COLLECTION_WORKFLOWS.md W2 | 12 |
| B | Workflow 6 real (Google Trends via pytrends → external_signals) | COLLECTION_WORKFLOWS.md W6 | 12 |
| C | Wire weakness.py to gig_quality_scores + Workflow 5 real stub | SCORING_DIRECTION.md S4.8 | 12 |
| D | Workflow 7 stub (Reddit Signals) + patch coverage + PR #32 | COLLECTION_WORKFLOWS.md W7 | 12 |

## Test Baseline and Target

| Milestone | Tests | Coverage |
|---|---|---|
| cycle/027/integration (PR #31 head) | 1521 | 94.91% |
| Cycle 028 target | >= 1570 | >= 90% |

## Why Workflow 2 Is Cycle 028 Priority #1 (From Spec)

COLLECTION_WORKFLOWS.md Workflow 2 specifies:
- Step 2a: Fiverr Autocomplete (Playwright, authenticated)
- Step 2b: Google Suggest (httpx, no auth needed)
- Step 2c: LLM Keyword Generation (gpt-4o-mini)
- Step 2d: LLM Relevance Filter
- Step 2e: Deduplication
- Step 2f: LLM Intent Classification
- Step 2g: Embedding Generation

Agent A Cycle 028 scope:
- Implement Step 2b (Google Suggest via httpx — no Playwright needed, easiest start)
- Implement Step 2e (deduplication logic)
- Stub Steps 2c/2d/2f/2g with feature flags
- Step 2a (Fiverr autocomplete) requires authenticated session — defer to after auth

## Why Workflow 6 Is Cycle 028 Priority #2 (From Spec + ORM Ready)

ExternalSignal ORM exists (Cycle 027). COLLECTION_WORKFLOWS.md W6:
- Uses pytrends Python library (no Playwright needed)
- Fetches 12-month and 3-month interest-over-time per keyword
- Writes to external_signals (signal_type="google_trends")
- Demand and Trend scoring calculators read from external_signals
This is a pure Python API call — no browser needed, implementable now.

## weakness.py Wiring (Cycle 028 Agent C Priority)

From Agent C report: weakness.py._load_signals_from_db() does NOT currently
query gig_quality_scores table despite that ORM now existing.
Required wiring (from SCORING_DIRECTION.md S4.8 inputs):
- video_absence_rate: from GigQualityScore.video_present (proportion where False)
- portfolio_absence_rate: from GigQualityScore.portfolio_count (proportion where 0)
- analysis_complete check: GigQualityScore.analysis_complete for LLM stub fallback
Agent C must update weakness.py._load_signals_from_db() to query GigQualityScore.

## Jira Keys for Cycle 028

- SCRUM-516 → Done (after PR #31 merge, Agent A first task)
- SCRUM-517 → Create as Cycle 028 control → In Progress (Agent A)
- SCRUM-143 or W2 story → In Progress (Agent A — keyword expansion partial impl)
- SCRUM-151 → advance (Agent B — Google Trends real impl)
- SCRUM-172 → advance (Agent C — weakness.py wiring)
- SCRUM-150 → advance (Agent C — Workflow 5 real stub)
