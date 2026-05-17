# Cycle 018 — Cursor Agent A Prompt

## Agent A — PR #14 Gate, Cycle Branch Start, Runtime Acceptance Baseline

## Mission

Own the pr #14 merge gate, create cycle/018/integration safely, enforce the root/worktree controls, and build the runtime integration readiness baseline that lets the rest of the agents work from updated develop. This is a product-forward cycle, not a PM cleanup loop. Use the board audit to choose and protect scope, but keep the work tied to real product behavior, tests, integration validation, and runtime evidence. PR #14 is the first short gate. After it is merged or definitively blocked, work must continue only from the correct branch state and only from `C:\Fiverr\Fiverr`.

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

Primary Jira keys for this agent: SCRUM-262, SCRUM-261, SCRUM-260, SCRUM-231, SCRUM-232, SCRUM-236, SCRUM-239, SCRUM-241. Read these issues before coding. For every touched issue, identify the acceptance criteria and Definition of Done bullets you are advancing. Comment on the issue with branch, files changed, validation evidence, remaining gaps, and status recommendation. Keep broad stories non-Done unless full source DoD is satisfied.

## File Scope

Primary file scope includes: scripts/preflight.ps1, src/reports/placeholders.py, src/dashboard/app.py, src/dashboard/queries.py, tests/unit/test_reports.py, tests/unit/test_dashboard.py, docs/jira/ACTIVE_STORY_DOD_LEDGER.md. Stay inside this scope unless the codebase requires a small adjacent change. Coordinate by report notes if a change would overlap another agent’s files.

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

### Task 1: Verify PR #14 live merge gate from the canonical root

**Jira / AC / DoD mapping:** Primary key `SCRUM-261`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-261` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 2: Merge PR #14 only if green and authorized

**Jira / AC / DoD mapping:** Primary key `SCRUM-260`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/app.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-260` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 3: Create cycle/018/integration from updated develop

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 4: Run and record canonical root preflight

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_reports.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 5: Confirm no unauthorized worktrees or random directories

**Jira / AC / DoD mapping:** Primary key `SCRUM-236`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-236` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 6: Normalize final evidence freeze baseline for Cycle 018

**Jira / AC / DoD mapping:** Primary key `SCRUM-239`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-239` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 7: Create integration validation run context model

**Jira / AC / DoD mapping:** Primary key `SCRUM-241`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `scripts/preflight.ps1` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-241` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 8: Build first-run readiness baseline payload

**Jira / AC / DoD mapping:** Primary key `SCRUM-262`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-262` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 9: Surface all-9-niche config validation in runtime evidence

**Jira / AC / DoD mapping:** Primary key `SCRUM-261`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/app.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-261` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 10: Add data-integrity readiness signal for dashboard and reports

**Jira / AC / DoD mapping:** Primary key `SCRUM-260`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-260` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 11: Add root/worktree preflight regression documentation or test hook

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_reports.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 12: Update app-entry diagnostics for integration-readiness state

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 13: Add tests for ready/warning/blocked/unknown runtime states

**Jira / AC / DoD mapping:** Primary key `SCRUM-236`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-236` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 14: Update AC/DoD ledger for touched integration stories

**Jira / AC / DoD mapping:** Primary key `SCRUM-239`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `scripts/preflight.ps1` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-239` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 15: Post Jira comments for touched issues

**Jira / AC / DoD mapping:** Primary key `SCRUM-241`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-241` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 16: Run targeted tests for reports/dashboard/query integrations

**Jira / AC / DoD mapping:** Primary key `SCRUM-262`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/app.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-262` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 17: Run full validation block

**Jira / AC / DoD mapping:** Primary key `SCRUM-261`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/dashboard/queries.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-261` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 18: Commit scoped changes only

**Jira / AC / DoD mapping:** Primary key `SCRUM-260`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_reports.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-260` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 19: Create Agent A report

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_dashboard.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 20: Hand off clean branch state to Agents B/C/D

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

## Final Report

Create or update:

```text
docs/cycle_reports/CYCLE_018_AGENT_A.md
```

The report must include preflight output, branch/PR state, final commit SHA, files changed, Jira keys, AC/DoD bullets advanced, validation commands and outcomes, Codex status, artifact hygiene, no-main confirmation, no-random-directory confirmation, no-unapproved-worktree confirmation, risks/blockers, and next-agent handoff.

## Completion Standard

You are complete only when your scoped files are committed on the active Cycle 018 branch, tests are run or explicitly handed to the steward with reason, Jira evidence is updated for touched issues, no generated artifacts or secrets are staged, and your report is present at the required path.
