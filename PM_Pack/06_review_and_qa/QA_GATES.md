# QA GATES — Pass/Fail Gates at Every Level

---

## Gate 1: Task-Level Gate
| Criterion | Pass | Fail |
|---|---|---|
| File exists at specified path | Yes | File missing or wrong path |
| Implementation matches spec | Yes | Deviates from spec |
| Tests exist and pass | Yes | Tests missing or failing |
| Lint clean | Yes | Ruff errors present |
| Type check clean | Yes | Mypy errors present |

## Gate 2: Story-Level Gate
| Criterion | Pass | Fail |
|---|---|---|
| All tasks in story pass Gate 1 | Yes | Any task fails |
| Tasks integrate with each other | Yes | Tasks work in isolation only |
| Story DOD acceptance criteria met | Yes | Any DOD criterion unmet |
| No regressions in related modules | Yes | Broke something nearby |

## Gate 3: Epic-Level Gate
| Criterion | Pass | Fail |
|---|---|---|
| All stories pass Gate 2 | Yes | Any story fails |
| Integration tests pass across stories | Yes | Integration failures |
| Coverage >= 80% for epic modules | Yes | Below threshold |
| No open bugs tagged to this epic | Yes | Open bugs exist |

## Gate 4: Cycle-Level Gate
| Criterion | Pass | Fail |
|---|---|---|
| All 4 agents' work reviewed | Yes | Any agent skipped |
| All confidence scores >= 80 | Yes | Any agent < 80 |
| Jira board updated | Yes | Updates missing |
| PR ready or merged | Yes | PR not created |
| CYCLE_LOG entry created | Yes | Entry missing |
| STATE_SNAPSHOT updated | Yes | Stale state |

## Gate 5: Release Gate (develop -> main)
| Criterion | Pass | Fail |
|---|---|---|
| All targeted epics pass Gate 3 | Yes | Any epic incomplete |
| Full test suite green | Yes | Any failures |
| No P1/P2 bugs open | Yes | Critical bugs exist |
| Human operator approves | Yes | Not approved |

## Gate 6: Regression Gate (every cycle)
| Criterion | Pass | Fail |
|---|---|---|
| Existing tests still pass after new code | Yes | Regressions |
| No new lint warnings in existing code | Yes | New warnings |
| No import errors across the codebase | Yes | Broken imports |

---

## Gate Application Per Cycle
- Gate 1 + Gate 6: Every task every cycle
- Gate 2: When a story completes
- Gate 3: When an epic completes
- Gate 4: End of every cycle
- Gate 5: Release milestones only

## Cycle 005 Addendum — PR Gate

Cycle Gate now requires GitHub Actions checks and Codecov >=90% before merge readiness. Codex review threads must be resolved only after formal disposition. PRs with missing checks are not merge-ready even when local tests pass.
