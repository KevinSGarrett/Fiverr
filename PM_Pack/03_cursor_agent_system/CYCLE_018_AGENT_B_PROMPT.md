# Cycle 018 — Cursor Agent B Prompt

## Agent B — Runtime Dashboard Closure and User-Facing Acceptance

## Mission

Turn the latest dashboard query and page contracts into stronger runtime acceptance evidence without claiming done prematurely, especially for opportunities, keywords, run history, app entry, and query layer stories. This is a product-forward cycle, not a PM cleanup loop. Use the board audit to choose and protect scope, but keep the work tied to real product behavior, tests, integration validation, and runtime evidence. PR #14 is the first short gate. After it is merged or definitively blocked, work must continue only from the correct branch state and only from `C:\Fiverr\Fiverr`.

## Common Non-Negotiable Rules

Cycle 018 continues from the live state where PR #14 is open, mergeable, Codex-resolved, and green on required checks. The cycle must start with a short PR #14 merge gate and then move product work forward. Every agent must obey the execution-root lock: work only from C:\Fiverr\Fiverr, run the mandatory PowerShell preflight, reject random directories or unapproved worktrees, use PowerShell-safe commands only, and preserve final evidence after the last push. Jira remains the source of truth, but the board audit shows the project has canonical product epics, duplicate/noncanonical historical items, active In Review product stories, and future To Do backlogs that must not be mixed accidentally. Broad stories stay non-Done unless the full source acceptance criteria and Definition of Done are satisfied.

## Mandatory PowerShell Preflight

```powershell
Get-Location
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git worktree list
git fetch origin
```
Pass condition: `git rev-parse --show-toplevel` must resolve to `C:\Fiverr\Fiverr`. Abort instead of inventing a workaround if the root, branch, dirty-tree, worktree, or remote state is unsafe.


## Same-Cycle Codex Rule

If you own the PR, or if your work causes a Codex review comment, you must handle that review in the same PR/cycle whenever technically possible. Valid findings must be fixed, tested, pushed, replied to with evidence, and resolved. Invalid or non-applicable findings must receive an evidence-backed reply and then be resolved. Do not push unresolved Codex comments into a future PM cycle unless a hard blocker is documented with proof.

## Jira and AC/DoD Rule

Primary Jira keys for this agent: SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228, SCRUM-231, SCRUM-235. Read these issues before coding. For every touched issue, identify the acceptance criteria and Definition of Done bullets you are advancing. Comment on the issue with branch, files changed, validation evidence, remaining gaps, and status recommendation. Keep broad stories non-Done unless full source DoD is satisfied.

## File Scope

Primary file scope includes: src/dashboard/opportunities.py, src/dashboard/keywords.py, src/dashboard/run_history.py, src/dashboard/queries.py, src/dashboard/components.py, src/dashboard/app.py, tests/unit/test_dashboard.py, tests/unit/test_dashboard_queries.py. Stay inside this scope unless the codebase requires a small adjacent change. Coordinate by report notes if a change would overlap another agent’s files.

## Required Validation Block

```powershell
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle018.db
python run.py phase2-smoke
```


## Tasks

### Task 1: Read selected dashboard Jira stories and extract AC/DoD bullets

**Jira / AC / DoD mapping:** Primary key `SCRUM-215`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/keywords.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-215` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 2: Add runtime acceptance matrix for dashboard pages

**Jira / AC / DoD mapping:** Primary key `SCRUM-219`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/run_history.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-219` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 3: Harden Opportunities page drill-in contract

**Jira / AC / DoD mapping:** Primary key `SCRUM-225`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-225` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 4: Harden Keywords page detail and cluster context contract

**Jira / AC / DoD mapping:** Primary key `SCRUM-228`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/components.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-228` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 5: Harden Run History evidence-link and warning contract

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/app.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 6: Validate query metadata consistency across page consumers

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 7: Add page-level empty-state and sparse-state tests

**Jira / AC / DoD mapping:** Primary key `SCRUM-214`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard_queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-214` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 8: Add filter/sort/pagination acceptance tests for runtime pages

**Jira / AC / DoD mapping:** Primary key `SCRUM-215`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/opportunities.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-215` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 9: Improve reusable component payload compatibility

**Jira / AC / DoD mapping:** Primary key `SCRUM-219`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/keywords.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-219` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 10: Add app-entry page registration runtime acceptance tests

**Jira / AC / DoD mapping:** Primary key `SCRUM-225`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/run_history.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-225` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 11: Map dashboard warnings to operator-facing severity categories

**Jira / AC / DoD mapping:** Primary key `SCRUM-228`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-228` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 12: Ensure query layer remains UI-to-storage decoupled

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/components.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 13: Validate dashboard pages consume common source/freshness metadata

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/app.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 14: Coordinate with Agent A integration readiness payloads

**Jira / AC / DoD mapping:** Primary key `SCRUM-214`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-214` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 15: Update ledger rows for dashboard stories

**Jira / AC / DoD mapping:** Primary key `SCRUM-215`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard_queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-215` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 16: Post Jira comments for dashboard issues

**Jira / AC / DoD mapping:** Primary key `SCRUM-219`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/opportunities.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-219` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 17: Run targeted dashboard tests

**Jira / AC / DoD mapping:** Primary key `SCRUM-225`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/keywords.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-225` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 18: Run full validation block or record coordinated full-run evidence

**Jira / AC / DoD mapping:** Primary key `SCRUM-228`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/run_history.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-228` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 19: Commit scoped dashboard runtime work

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 20: Create Agent B report

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/components.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 21: Provide Agent D with closure/non-Done recommendations

**Jira / AC / DoD mapping:** Primary key `SCRUM-214`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/app.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-214` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 22: Document remaining runtime UX acceptance gaps

**Jira / AC / DoD mapping:** Primary key `SCRUM-215`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-215` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

## Final Report

Create or update:

```text
docs/cycle_reports/CYCLE_018_AGENT_B.md
```

The report must include preflight output, branch/PR state, final commit SHA, files changed, Jira keys, AC/DoD bullets advanced, validation commands and outcomes, Codex status, artifact hygiene, no-main confirmation, no-random-directory confirmation, no-unapproved-worktree confirmation, risks/blockers, and next-agent handoff.

## Completion Standard

You are complete only when your scoped files are committed on the active Cycle 018 branch, tests are run or explicitly handed to the steward with reason, Jira evidence is updated for touched issues, no generated artifacts or secrets are staged, and your report is present at the required path.
