# HYDRATION HEADER — Cycle 036
# Updated: 2026-05-24 (post Cycle 035 PM master protocol)

## Cycle 035 Verified Complete
2407 tests | 94.88% coverage | codecov/patch 100% | 2 Codex VALID_FIXED | PR #42 merged
Live run: PARTIAL (keywords=2, search_results=2, gigs=0, sellers=0, external_signals=4)
Root blocker: PerimeterX (PXCR) blocked Stages 3/4/5/8 in Playwright headless mode.
Fix: ScrapFly integration — added in Cycle 036.

## ⚠️ WORKTREE INCIDENT — RESOLVED IN CYCLE 036
Cycle 035 agents worked in C:\Fiverr\Fiverr_cycle035 (a git worktree) instead of
C:\Fiverr\Fiverr. Root cause: uncommitted PM-level ScrapFly files made main repo dirty.
Fix applied: worktree removed by Agent A Cycle 036. Canonical directory enforced.
RULE: ALL future agents MUST work in C:\Fiverr\Fiverr. NO git worktree add permitted.

## Current PR State
- PR #42 (cycle/035/integration): MERGED
- PR #43 (cycle/036/integration): TO BE CREATED by Agent D
- SCRUM-524 (Cycle 035 control): Done
- SCRUM-525 (Cycle 036 control): In Progress

## Cycle 036 Primary Scope: ScrapFly Integration
ScrapFly is the PerimeterX bypass solution. Primary deliverables:
- ScrapFly client, fetcher protocol, search parser: COMMITTED (Agent A)
- Orchestrator wiring: IN PROGRESS (Agent B)
- Documentation: IN PROGRESS (Agent B)
- Jira updates: IN PROGRESS
- .env.example, requirements.txt, config.yaml.example: COMMITTED (Agent A)

## Hard Gate (Permanent)
- codecov/patch >= 90%: HARD BLOCKER
- Codex GraphQL query: MANDATORY every PR
- Agent D merge gate checklist: ALL PASS/YES
- R-090: 18+ tasks minimum
- R-092 v2: A/B/C = file-scoped only. D = ONE --cov=src.
- ⛔ CANONICAL DIRECTORY: C:\Fiverr\Fiverr — NO worktrees permitted

## Test Baseline
Cycle 035 final: 2407 tests | 94.88% | codecov/patch 100%
Cycle 036 target: >= 2450 tests | >= 90% coverage

## Binding Rules
Work only from C:\Fiverr\Fiverr (ENFORCED — see worktree incident above)
All real Playwright/ScrapFly code guarded by dry_run parameter
Tests use AsyncMock/MagicMock — NO real browser or API calls in automated tests
data/sessions/ gitignored — never stage session files
.env gitignored — never stage API keys
