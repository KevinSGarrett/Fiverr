# Cycle 018 — Cursor Agent C Prompt

## Agent C — Analysis Closure Evidence and Scoring-Readiness Handoff

## Mission

Convert the analysis engine’s current in review state into clearer closure evidence and scoring-readiness handoff without prematurely starting the scoring epic or marking analysis stories done without source dod proof. This is a product-forward cycle, not a PM cleanup loop. Use the board audit to choose and protect scope, but keep the work tied to real product behavior, tests, integration validation, and runtime evidence. PR #14 is the first short gate. After it is merged or definitively blocked, work must continue only from the correct branch state and only from `C:\Fiverr\Fiverr`.

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

Primary Jira keys for this agent: SCRUM-157, SCRUM-158, SCRUM-159, SCRUM-160, SCRUM-161, SCRUM-162, SCRUM-163, SCRUM-164, SCRUM-231, SCRUM-232, SCRUM-235. Read these issues before coding. For every touched issue, identify the acceptance criteria and Definition of Done bullets you are advancing. Comment on the issue with branch, files changed, validation evidence, remaining gaps, and status recommendation. Keep broad stories non-Done unless full source DoD is satisfied.

## File Scope

Primary file scope includes: src/analysis/contracts.py, src/analysis/orchestrator.py, src/analysis/clustering.py, src/analysis/gig_quality.py, src/analysis/competitors.py, src/analysis/seller_strength.py, src/analysis/saturation.py, src/analysis/reviews.py, src/analysis/intent.py, tests/unit/test_analysis.py. Stay inside this scope unless the codebase requires a small adjacent change. Coordinate by report notes if a change would overlap another agent’s files.

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

### Task 1: Read Analysis S3.1 through S3.8 Jira AC/DoD

**Jira / AC / DoD mapping:** Primary key `SCRUM-158`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/orchestrator.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-158` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 2: Build analysis closure evidence matrix

**Jira / AC / DoD mapping:** Primary key `SCRUM-159`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/clustering.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-159` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 3: Define scoring-readiness handoff contract without implementing scoring

**Jira / AC / DoD mapping:** Primary key `SCRUM-160`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/gig_quality.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-160` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 4: Harden keyword clustering output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-161`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/competitors.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-161` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 5: Harden gig quality output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-162`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/seller_strength.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-162` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 6: Harden competitor profiling output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-163`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/saturation.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-163` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 7: Harden seller strength output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-164`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/reviews.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-164` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 8: Harden saturation output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/intent.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 9: Harden review analysis output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_analysis.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 10: Harden intent classification output completeness checks

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/contracts.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 11: Validate analysis stage-order metadata

**Jira / AC / DoD mapping:** Primary key `SCRUM-157`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/orchestrator.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-157` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 12: Add sparse-data and malformed-data analysis contract tests

**Jira / AC / DoD mapping:** Primary key `SCRUM-158`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/clustering.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-158` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 13: Add source/freshness lineage consistency tests

**Jira / AC / DoD mapping:** Primary key `SCRUM-159`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/gig_quality.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-159` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 14: Integrate analysis closure signals into Agent A runtime evidence model

**Jira / AC / DoD mapping:** Primary key `SCRUM-160`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/competitors.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-160` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 15: Create non-Done decision framework for S3 stories

**Jira / AC / DoD mapping:** Primary key `SCRUM-161`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/seller_strength.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-161` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 16: Update AC/DoD ledger for all touched analysis stories

**Jira / AC / DoD mapping:** Primary key `SCRUM-162`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/saturation.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-162` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 17: Post Jira comments for touched analysis issues

**Jira / AC / DoD mapping:** Primary key `SCRUM-163`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/reviews.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-163` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 18: Run targeted analysis tests

**Jira / AC / DoD mapping:** Primary key `SCRUM-164`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/intent.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-164` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 19: Run or coordinate full validation block

**Jira / AC / DoD mapping:** Primary key `SCRUM-231`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `tests/unit/test_analysis.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-231` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 20: Commit scoped analysis closure work

**Jira / AC / DoD mapping:** Primary key `SCRUM-232`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/contracts.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-232` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 21: Create Agent C report

**Jira / AC / DoD mapping:** Primary key `SCRUM-235`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/orchestrator.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-235` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

### Task 22: Hand off scoring-readiness gaps to later Scoring cycle

**Jira / AC / DoD mapping:** Primary key `SCRUM-157`. Before implementing, read the Jira issue text and identify the exact acceptance criteria that this task advances. If the task advances only part of the story, state that explicitly in your report and Jira comment. Do not mark the issue Done unless every source requirement and Definition of Done bullet is satisfied.

**Implementation detail:** Work from `C:\Fiverr\Fiverr` only. Use the current branch selected by the branch gate. Focus on `src/analysis/clustering.py` and adjacent tests or docs only when necessary. The implementation must be deterministic, fixture-safe, network-free, and compatible with existing dashboard/reporting/orchestrator contracts. Prefer small composable helpers, explicit warning codes, source/freshness metadata, and typed or structured outputs over fragile ad hoc dictionaries. Preserve existing public behavior unless the Jira AC requires a change.

**Validation requirement:** Add or update targeted tests whenever behavior changes. For code changes, run the smallest relevant targeted test first, then run the shared validation block before final completion or clearly document why a downstream steward will run the full block. Validation output must be summarized in your report with exact command names and pass/fail status.

**Report and Jira evidence:** Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` if the task materially advances a Jira issue. Post or prepare a Jira comment for `SCRUM-157` with the changed files, tests run, AC/DoD progress, remaining gaps, and status recommendation. In your report, include the branch, final local SHA after your commit, and whether any root/worktree exception occurred.

## Final Report

Create or update:

```text
docs/cycle_reports/CYCLE_018_AGENT_C.md
```

The report must include preflight output, branch/PR state, final commit SHA, files changed, Jira keys, AC/DoD bullets advanced, validation commands and outcomes, Codex status, artifact hygiene, no-main confirmation, no-random-directory confirmation, no-unapproved-worktree confirmation, risks/blockers, and next-agent handoff.

## Completion Standard

You are complete only when your scoped files are committed on the active Cycle 018 branch, tests are run or explicitly handed to the steward with reason, Jira evidence is updated for touched issues, no generated artifacts or secrets are staged, and your report is present at the required path.
