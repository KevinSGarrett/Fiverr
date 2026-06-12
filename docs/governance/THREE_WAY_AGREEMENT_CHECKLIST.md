# Three-Way Agreement Checklist

Cycle completion requires agreement between PMPack state, Jira state, and GitHub merge state. If any leg disagrees, the cycle is not complete.

## Verification Table

| # | Checkpoint | System | Command / Query | Expected Result |
|---|---|---|---|---|
| 1 | Active cycle in hydration | PMPack | read `PM_Pack/07_hydration/HYDRATION_HEADER.md` | Cycle NNN active |
| 2 | Canonical cycle match | PMPack | read `PM_Pack/CURRENT_STATE_CANONICAL.md` | Same cycle as hydration |
| 3 | Score alignment | PMPack | read score values in scorecard | Score 1 and Score 2 coherent |
| 4 | Wave alignment | PMPack | check epic tracker wave row | Current wave accurate |
| 5 | PM consistency audit | PMPack | `python automation/ai_cycle_controller.py pm-pack-audit` | PASS |
| 6 | Cycle control issue done | Jira | JQL for control issue | Done |
| 7 | Story completion check | Jira | JQL by cycle label | No unresolved required stories |
| 8 | Jira comments posted | Jira | issue activity view | Agent reports linked |
| 9 | PR merged to develop | GitHub | `gh pr view <PR> --json state,mergedAt,baseRefName` | merged, base=develop |
|10| CI checks green | GitHub | `gh pr checks <PR>` | required checks pass |
|11| Codecov checks green | GitHub | check statuses | project and patch pass |
|12| Merge SHA recorded | GitHub/PMPack | compare PR merge SHA vs cycle log | exact match |

## Closure Rule

Do not mark cycle complete until all checkpoints pass. If one leg fails, document blocker in cycle report and keep cycle status IN_PROGRESS.

