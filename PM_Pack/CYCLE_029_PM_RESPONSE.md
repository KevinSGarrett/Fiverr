# Cycle 029 PM Response — Root Copy

## Operator Feedback at Cycle 028 Close → Three Permanent Rules Now In Effect

### R-090: Task Sizing Standard
Every Cycle 029 prompt now has 4-8 MEANINGFUL TASKS labeled SMALL / MEDIUM / LARGE.
NOT 16-24 micro-actions. Sub-steps live INSIDE tasks as numbered bullets.
Each prompt has a TIME BUDGET BLOCK at the top with per-task estimates.
Codified in: `PM_Pack/01_pm_instructions/AGENT_PROMPT_TEMPLATE.md`

### R-091: Stale Branch Cleanup (Agent A every cycle)
Agent A deletes the merged cycle branch from remote + local after PR merge.
Cycle 029 Agent A: delete `cycle/028/integration` after merging PR #32.
Periodic full sweep every 5 cycles (next at 030).
Codified in: `PM_Pack/05_github_protocol/GITHUB_RULES.md` (Rule G-005)

### R-092: Coverage Audit Consolidation (BIG PERFORMANCE WIN)
This was the operator's strongest concern and it was 100% correct.

**Old behavior:** Every agent ran the full pytest suite with --cov on entire src/,
plus the 6-command validation block, plus per-module coverage. 4-5× redundant per cycle.

**New behavior:**
- Agents A/B/C: Run ONLY targeted patch coverage on THEIR module (seconds, not minutes)
- Agent D: Single comprehensive audit (full pytest + per-module) ONCE before PR
- Codecov on PR: The canonical coverage gate (was always the canonical gate)

Expected execution time reduction: 50-65% for Agents A/B/C with zero safety loss.

Codified in: `PM_Pack/05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`

## Cycle 028 Confirmed Complete (PM Master Protocol Verified)

- 1608 tests | 95.04% coverage | codecov/patch 100% | 3 Codex VALID_FIXED
- W2 Step 2b+2e real (Google Suggest + dedup)
- W6 Google Trends REAL pytrends implementation (niche-scoped after Codex fix)
- weakness.py wired to GigQualityScore (top-10 filtered after Codex fix)
- W7 Reddit stub interface complete
- All 11 claimed files verified on disk
- All 17 Jira keys verified live (zero discrepancies)

## Cycle 029 Scope (Applying R-090)

| Agent | Tasks | Tier Mix | Est. Time |
|---|---|---|---|
| A | PR gate + branch cleanup + W5 REAL | 1×MEDIUM + 1×LARGE + 1×MEDIUM | ~2h |
| B | W2 Step 2c + 2d (LLM gen + relevance) | 1×SMALL + 1×LARGE + 2×MEDIUM | ~2h |
| C | W2 Step 2f + auto-recommendation trigger | 1×SMALL + 3×MEDIUM | ~1h 45m |
| D | W7 REAL praw + comprehensive audit + PR | 1×SMALL + 1×LARGE + 3×MEDIUM | ~3h |

## Target: >=1670 tests | >=90% coverage | PR #33
## Hard Gate: codecov/patch PASS | Codex all resolved | Full checklist ALL PASS/YES
## New Hygiene Gate: Agent A reports branch cleanup result in cycle report
