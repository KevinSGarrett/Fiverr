# Cycle 020 Fiverr PM Response
# Date: 2026-05-17 | PM: Claude AI

## PM Direction

Cycle 020 advances the scoring engine from "calculators built" to "pipeline wired." The
11 scoring calculators exist on cycle/019/integration and PR #23 is ready to merge. This
cycle has two pillars: (1) replace the dict-based db proxy and LLM stubs in the scoring
calculators with real SQLAlchemy queries and feature-flagged live LLM calls, and (2) begin
E05 Recommendations Engine with the context builder and first async LLM task executors.
This is a product-forward cycle — no process cleanup, no governance-only work.

## Cycle 019 Review Summary

All 4 Cycle 019 agents delivered with PASS. PR #23 created and ready to merge.

Agent A (PASS): Branch gate from clean develop. SCRUM-508 control ticket created. demand.py,
competition.py, opportunity.py + 30 scoring tests. 740 tests, 93.75%.

Agent B (PASS): feasibility.py, profitability.py, intent.py, saturation_score.py + 42 tests.
782 tests, 93.32%. All LLM inputs stubbed per design.

Agent C (PASS): weakness.py, trend.py, confidence.py, final.py, ranking.py, orchestrator.py
+ 64 tests. 846 tests, 92.85%. Orchestrator wires all 13 stories.

Agent D (PASS): Jira board reconciliation, PR #23 created, 2 Codex findings fixed in-cycle
(orchestrator ScoringInput wiring, reddit signal availability). 848 tests, 93.30%.
Final SHA: e97267438ceb70bd7cfa3c7dc748279673fd603a.

## Live Repo State at Cycle 020 Start

- cycle/019/integration HEAD: e97267438ceb70bd7cfa3c7dc748279673fd603a
- PR #23: https://github.com/KevinSGarrett/Fiverr/pull/23
- PR status: CI green, Codex clean, ready to merge
- Tests on PR head: 848 | Coverage: 93.30% | Mypy: clean (148 files)
- Local HEAD: cycle/019/integration (Agent D last commit)

## Jira Board Audit

See: PM_Pack/04_jira_protocol/BOARD_AUDIT_CYCLE_020.md

Key actions required:
- Merge PR #23 (Agent A Task 2)
- Create SCRUM-509 (Cycle 020 control)
- Transition SCRUM-508 to Done (after PR #23 merge)
- Transition SCRUM-19 (E04 epic) to In Progress
- Read E05 story keys from SCRUM-20 before coding; transition S5.1-S5.4 to In Progress

## Cycle 020 Product Focus

### Pillar 1: E04 Scoring — DB Integration + LLM Wiring

The calculators work with dict-based db proxy. Real production scoring requires:
- Real SQLAlchemy session queries for Keyword, SearchResult, ExternalSignal, GigQuality, etc.
- Live LLM calls (using existing src/llm/client.py + src/llm/cache.py)
- score_keyword() async function from SCORING_SYSTEM.md
- write_keyword_score() DB write function
- Depth-tier logic (keyword_only → scores 1-3 only, etc.)

### Pillar 2: E05 Recommendations — Foundation Layer

Stories: S5.1 Eligibility + Gating, S5.2 Skip Logic, S5.3 Context Builder, S5.4 LLM Tasks

The existing src/recommendations/ has scaffold only. The Jinja2 templates exist in
src/llm/prompts/ (from audit PR #16). The RecommendationContext Pydantic model needs to
be built, and the first 4 async LLM task executors need implementation.

## Agent Assignment Summary

| Agent | Primary Scope |
|---|---|
| A | PR #23 gate/merge, branch, score_keyword() async pipeline, write_keyword_score() |
| B | SQLAlchemy DB query integration for all 13 calculators |
| C | LLM wiring for 8 stub calculators using src/llm/client.py + src/llm/cache.py |
| D | E05 S5.1-S5.4 + board reconciliation + PR #24 + Codex + final freeze |

## Jira Updates Required This Cycle

Agent A must:
- Merge PR #23 as first action (before creating new branch)
- Create SCRUM-509: Cycle 020 control → In Progress
- Transition SCRUM-508 (Cycle 019 control) → Done
- Transition SCRUM-19 (E04 epic) → In Progress
- Transition SCRUM-175 (S4.10 Final), SCRUM-177 (S4.13 Orchestration) → keep In Progress
  (score_keyword() is new work advancing these stories)

Agent B must:
- Read all SCRUM-165 through SCRUM-177 before coding
- Post evidence comments on touched stories after DB integration work

Agent C must:
- Read SCRUM-20 (E05 epic) children before coding
- Read SCRUM-165 through SCRUM-173 before adding LLM wiring
- Transition S4.6/S4.7/S4.8/S4.9 → keep In Progress with LLM wiring progress comment

Agent D must:
- Read E05 story keys from SCRUM-20 children
- Transition E05 S5.1, S5.2, S5.3, S5.4 → In Progress before coding
- Post board reconciliation including stale epic status corrections

## Cycle 020 Branch Strategy

```
1. Agent A verifies PR #23 is still green and mergeable.
2. Agent A merges PR #23 into develop.
3. Agent A transitions SCRUM-508 to Done; SCRUM-19 to In Progress.
4. Agent A creates cycle/020/integration from updated develop.
5. Agents A/B/C work product on the same branch.
6. Agent D reads all A/B/C reports, implements E05 foundation, opens PR #24.
7. Agent D resolves Codex findings in-cycle.
8. No direct main changes.
```

## Required Validation Block (All Agents)

```powershell
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle020.db
python run.py phase2-smoke
```

## Guardrails

- Work only from C:\Fiverr\Fiverr. No random directories.
- LLM wiring must use feature flags — stub fallback must remain when LLM client is None.
- score_keyword() must be async-aware; use asyncio.gather for parallel LLM calls.
- SQLAlchemy integration must not break existing dict-proxy test patterns.
- E05 stories non-Done until full LLM generation is tested end-to-end.
- Never stage .env, coverage.xml, *.db runtime databases, or PM_Pack archives.
