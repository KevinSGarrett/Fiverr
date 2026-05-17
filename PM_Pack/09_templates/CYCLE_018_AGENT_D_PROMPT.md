# Cycle 018 — Cursor Agent D Prompt

## Agent D — Final Stewardship, Board Reconciliation, PR, Codex, and Evidence Freeze

## Mission

Act as final steward: verify all agent work, perform targeted board reconciliation, open/update the cycle 018 pr, resolve codex comments in-cycle, wait for checks, and freeze final evidence without creating a process-only loop. This is a product-forward cycle, not a PM cleanup loop. Use the board audit to choose and protect scope, but keep the work tied to real product behavior, tests, integration validation, and runtime evidence. PR #14 is the first short gate. After it is merged or definitively blocked, work must continue only from the correct branch state and only from `C:\Fiverr\Fiverr`.

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

Primary Jira keys for this agent: SCRUM-262, SCRUM-257, SCRUM-250, SCRUM-254, SCRUM-231, SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-235, SCRUM-237, SCRUM-241. Read these issues before coding. For every touched issue, identify the acceptance criteria and Definition of Done bullets you are advancing. Comment on the issue with branch, files changed, validation evidence, remaining gaps, and status recommendation. Keep broad stories non-Done unless full source DoD is satisfied.

## File Scope

Primary file scope includes: docs/jira/ACTIVE_STORY_DOD_LEDGER.md, docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_018.md, docs/cycle_reports/CYCLE_018_AGENT_D.md, .github/pull_request_template.md, src/reports/placeholders.py, tests/unit/test_reports.py. Stay inside this scope unless the codebase requires a small adjacent change. Coordinate by report notes if a change would overlap another agent’s files.

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

### Task 1: Verify all agent reports and branch state

**Jira / AC / DoD mapping:** Primary key `SCRUM-257`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_018.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-257` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 2: Perform final canonical root/worktree preflight

**Jira / AC / DoD mapping:** Primary key `SCRUM-250`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/cycle_reports/CYCLE_018_AGENT_D.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-250` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 3: Audit board status changes against Cycle 018 touched files

**Jira / AC / DoD mapping:** Primary key `SCRUM-254`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `.github/pull_request_template.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-254` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 4: Review SCRUM-217/SCRUM-221/SCRUM-222 duplicate Done risk

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 5: Update SCRUM-257 with evidence-based reconciliation

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_reports.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 6: Validate noncanonical issue exclusions

**Jira / AC / DoD mapping:** Primary key `SCRUM-233`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-233` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 7: Ensure product stories are not marked Done prematurely

**Jira / AC / DoD mapping:** Primary key `SCRUM-234`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_018.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-234` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 8: Build final AC/DoD progress table for PR body

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/cycle_reports/CYCLE_018_AGENT_D.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 9: Run targeted reports/ledger tests if applicable

**Jira / AC / DoD mapping:** Primary key `SCRUM-237`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `.github/pull_request_template.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-237` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 10: Run full validation block after all agent commits

**Jira / AC / DoD mapping:** Primary key `SCRUM-241`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-241` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 11: Push cycle/018/integration to origin

**Jira / AC / DoD mapping:** Primary key `SCRUM-262`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_reports.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-262` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 12: Open or update PR into develop

**Jira / AC / DoD mapping:** Primary key `SCRUM-257`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-257` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 13: Handle all Codex review comments in the same cycle

**Jira / AC / DoD mapping:** Primary key `SCRUM-250`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_018.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-250` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 14: Verify CI, codecov/project, and codecov/patch if emitted

**Jira / AC / DoD mapping:** Primary key `SCRUM-254`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/cycle_reports/CYCLE_018_AGENT_D.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-254` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 15: Perform final evidence freeze after checks settle

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `.github/pull_request_template.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 16: Synchronize final SHA in PR body/report/ledger

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 17: Post Jira comments for all touched issues

**Jira / AC / DoD mapping:** Primary key `SCRUM-233`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_reports.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-233` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 18: Confirm no-main policy

**Jira / AC / DoD mapping:** Primary key `SCRUM-234`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-234` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 19: Remove generated artifacts from staging

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_018.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 20: Create Agent D final report

**Jira / AC / DoD mapping:** Primary key `SCRUM-237`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `docs/cycle_reports/CYCLE_018_AGENT_D.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-237` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 21: Provide merge readiness recommendation

**Jira / AC / DoD mapping:** Primary key `SCRUM-241`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `.github/pull_request_template.md` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-241` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 22: Record any blocked board items without derailing product work

**Jira / AC / DoD mapping:** Primary key `SCRUM-262`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/reports/placeholders.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-262` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

## Final Report

Create or update:

```text
docs/cycle_reports/CYCLE_018_AGENT_D.md
```

The report must include preflight output, branch/PR state, final commit SHA, files changed, Jira keys, AC/DoD bullets advanced, validation commands and outcomes, Codex status, artifact hygiene, no-main confirmation, no-random-directory confirmation, no-unapproved-worktree confirmation, risks/blockers, and next-agent handoff.

## Completion Standard

You are complete only when your scoped files are committed on the active Cycle 018 branch, tests are run or explicitly handed to the steward with reason, Jira evidence is updated for touched issues, no generated artifacts or secrets are staged, and your report is present at the required path.
