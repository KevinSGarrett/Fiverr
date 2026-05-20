# PM CORRECTIVE RULES — Cycle 029 (FINAL)
# Three permanent process improvements based on operator feedback.

---

## R-090: Task Sizing Standard (PERMANENT — FINAL DEFINITION)

MINIMUM: 15 tasks per agent.
MAXIMUM: 24 tasks per agent.
EVERY task must be LARGE or XLARGE.
EVERY task contains its own sub-tasks as numbered bullets.

LARGE task (30–60 min): meaningful unit of code, tests, or verified state.
XLARGE task (60–120 min): complex multi-step implementation, deep research, or full test suite.

NOTHING counts as a standalone task unless it delivers real value:
  VALID standalone tasks: implement a function, write a test suite, create a template,
    run a coverage audit with gap closure, execute a live Jira reconciliation, do a
    full code quality pass, perform spec research, create a complete cycle report.
  INVALID standalone tasks: "post Jira comment", "run git status", "record SHA",
    "artifact hygiene check", "update ledger", "git commit", "no-main check".
  These MUST be embedded as sub-steps inside the LARGE/XLARGE task they belong to.

Every task heading format:
  ## TASK N [LARGE] — Descriptive title of real deliverable
  or
  ## TASK N [XLARGE] — Descriptive title of real deliverable

---

## R-091: Stale Branch Cleanup (NEW — Permanent)
After each PR merge, Agent A deletes the merged branch remote + local.
Every 5 cycles (030, 035, 040) Agent A does a full sweep of all stale cycle branches.
Never delete: main, develop, backup/archive/release/hotfix branches.
See: PM_Pack/05_github_protocol/GITHUB_RULES.md Rule G-005.

---

## R-092: Coverage Audit Consolidation (NEW — Permanent)
Tier 1 (Agents A/B/C): targeted patch only on their changed module.
Tier 2 (Agent D): single comprehensive audit (full pytest + per-module) before PR.
Tier 3: Codecov on PR is the canonical gate.
See: PM_Pack/05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md.
