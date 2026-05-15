# Cycle 012 Fiverr PM Response

Date: 2026-05-15
Branch context reviewed: `cycle/011/integration` and live PR #9.

## Executive Decision

The operator concern is valid. Jira is being used, but the workflow is still not strict enough for a 250+ item board. The process has improved from governance-only updates to changed-file mapping, but it still remains too PR/change-driven. The next correction is to make Jira the planning source before code begins: issue inventory, AC/DoD review, work selection, file ownership, implementation, validation, and status updates must flow in that order.

## Evidence Reviewed

- Uploaded `Fiverr_011.zip` local repository archive.
- Uploaded `PM_Pack_Cycle_011_READY(1).zip`.
- Live GitHub PR #9.
- Live Jira SCRUM board sample queries and active backlog review.
- Current PM Pack rules for task sizing, prompt rules, and Jira mapping.

## Key Findings

1. **Jira is not being ignored, but it is not fully board-first.** Product story tickets are now receiving updates, but planning still tends to start from implementation deltas and then map backward to Jira.
2. **The board contains many AC/DoD-bearing stories that are not being used as the first planning layer.** Active development must be selected from these issues before code work begins.
3. **Cycle/governance issues are still too prominent.** They are useful, but they cannot substitute for product story progress tracking.
4. **Acceptance Criteria and Definition of Done are not being tracked bullet-by-bullet.** Partial work is correctly not being marked Done, but there is no mandatory ledger that says which AC/DoD bullets are complete or incomplete.
5. **Prompt depth is still too low for the desired standard.** The Cycle 011 pack only enforces 10-20 tasks and 3,000-word minimums. That must be doubled again.
6. **PR #9 has a live/local discrepancy.** Live PR #9 is open and green, but the uploaded archive has uncommitted Agent C analysis work and an untracked Agent C report not represented in PR #9.

## GitHub Status

PR #9 is open, mergeable, and targets `develop`. It currently has no Codex review threads. CI and the `codecov/project` mirror job are green. However, the PR must not merge until the uploaded local archive discrepancy is reconciled.

## Jira Status

Created and activated:

- `SCRUM-254` — `[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again`

## New Binding Rules

### Jira board-first rule

Every cycle begins with Jira board inventory and AC/DoD review before code work is assigned.

### AC/DoD ledger rule

Every active or touched story must have a ledger row with:

- AC bullets advanced;
- AC bullets incomplete;
- DoD bullets advanced;
- DoD bullets incomplete;
- branch/PR evidence;
- tests;
- Codex/CI/Codecov status;
- recommended Jira status.

### Doubled task and prompt-depth rule

Cursor prompt requirements are now:

- minimum 20 substantive tasks per agent;
- preferred 24-32 tasks per agent;
- maximum 40 tasks per agent;
- minimum 6,000 words per agent prompt;
- preferred 8,000-12,000 words per agent prompt;
- shorter prompts require both `TASK-COUNT WAIVER` and `PROMPT-DETAIL WAIVER`.

## Cycle 012 Agent Prompts

## Agent A — Jira Board Inventory and AC/DoD Ledger Steward

### Mission
Perform full-board Jira inventory, create the AC/DoD-first operating ledger, and make Jira the primary planning source for Cycle 012 before more implementation is allowed.

### Branch and repository context
Repository: `KevinSGarrett/Fiverr`. Local root expected by Cursor agents: `C:\Fiverr\Fiverr`. Work from the active cycle branch instructed by the GitHub steward. Do not push to `main`. Cycle branches target `develop` only.

### Jira access
You are allowed to use the connected Jira board when this prompt explicitly assigns Jira work to you. You may read Jira issues, inspect statuses, create issues, update issue fields when appropriate, add comments, transition issues, and maintain Jira mapping evidence. You must follow the PM-defined Jira AC/DoD rules. Do not mark a broad product story Done unless the full source DoD is met. For partial work, use In Progress or In Review as instructed.

### Jira keys in scope
`SCRUM-254`, `SCRUM-250`, `SCRUM-132`, `SCRUM-243`, `SCRUM-246`

### File ownership boundaries
You may touch only your assigned files/scope unless your final report documents a necessary exception and no other agent owns that file.

- `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_012.md`
- `docs/jira/ACTIVE_STORY_DOD_LEDGER.md`
- `docs/jira/JIRA_SELECTION_RULES.md`
- `docs/cycle_reports/CYCLE_012_AGENT_A.md`

### Required substantive task count
This prompt assigns 24 substantive tasks. That satisfies the Cycle 012 rule requiring at least 20 substantive tasks per agent. Do not compress these into fewer tasks in your final report; report each task outcome individually.

### Tasks
### Task 1: Run a broad Jira issue inventory for SCRUM and document issue-type/status counts, including Epics, Stories, Tasks, Bugs, and Subtasks.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 2: Identify all In Progress stories and verify whether each has a current AC/DoD progress comment tied to the latest PR or branch.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 3: Identify all In Review items and verify whether they are blocked by PR status, Codex status, Codecov status, or incomplete DoD.

**Primary Jira reference:** `SCRUM-132`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 4: Identify stale To Do governance/import issues such as SCRUM-132 and SCRUM-243 and recommend whether they should remain open, be moved active, or be superseded.

**Primary Jira reference:** `SCRUM-243`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 5: Create a board-first story selection matrix that groups open work by Epic 01 through Epic 10 and ranks stories by dependency order.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 6: Create the Active Story DoD Ledger with one row per active story currently involved in Collection, Analysis, Dashboard, Reporting, Export, and Integration work.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 7: For SCRUM-254, add a Jira comment summarizing the audit findings and noting the specific process corrections implemented in the PM Pack.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 8: For SCRUM-250, add or update the Jira comment showing how Cycle 012 expands changed-file mapping into board-first planning.

**Primary Jira reference:** `SCRUM-132`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 9: For active Dashboard stories SCRUM-212, SCRUM-213, SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, and SCRUM-228, capture current AC and DoD status in the ledger.

**Primary Jira reference:** `SCRUM-243`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 10: For active Analysis stories SCRUM-157 through SCRUM-164, capture whether progress is genuine implementation, placeholder, fixture-only, or partial scaffold.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 11: For active Collection stories SCRUM-149 through SCRUM-156, capture whether source-required workflows are complete or only deterministic fixture/dry-run scaffolds.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 12: Flag any story currently In Progress that has no evidence comment or no clear link to a branch/PR.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 13: Flag any broad story that appears at risk of being marked Done prematurely.

**Primary Jira reference:** `SCRUM-132`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 14: Document how PR #9 maps to Jira and whether its changed files are sufficient to advance any story status beyond In Progress.

**Primary Jira reference:** `SCRUM-243`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 15: Document the local archive discrepancy: uncommitted analysis files and untracked Agent C report are not represented in PR #9.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 16: Define a cycle-start checklist that future PMs and Cursor agents must complete before writing code.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 17: Define a cycle-end checklist that must be completed before PR merge.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 18: Add exact language that agents may perform Jira operations only when assigned and must not update unrelated tickets.

**Primary Jira reference:** `SCRUM-132`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 19: Ensure the ledger distinguishes governance tickets from product stories.

**Primary Jira reference:** `SCRUM-243`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 20: Ensure every ledger row includes branch, PR, Codex, CI, Codecov, AC status, DoD status, and recommended next status.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 21: Run markdown/link sanity checks on all new docs you create.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 22: Commit only your Jira audit and ledger files, with a message scoped to Jira governance.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 23: Do not touch implementation code.

**Primary Jira reference:** `SCRUM-132`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 24: Write your final report to docs/cycle_reports/CYCLE_012_AGENT_A.md with Jira operations performed and remaining risks.

**Primary Jira reference:** `SCRUM-243`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.


### Required validation commands
Run the applicable subset, and explain any skipped command:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle012.db
python run.py phase2-smoke
git status --short
```

### Final report requirements
Write a final report with:

1. task-by-task outcome for all assigned tasks;
2. Jira actions performed;
3. AC/DoD bullets advanced and not advanced;
4. files changed;
5. tests/validation run;
6. Codex/CI/Codecov status if applicable;
7. branch and PR status;
8. risks and blockers;
9. explicit no-main confirmation.


---

## Agent B — PR #9 Discrepancy and GitHub Steward

### Mission
Resolve the merge-gate discrepancy between uploaded local Cycle 011 archive and live PR #9 before merge, then prepare a clean branch state for Cycle 012 work.

### Branch and repository context
Repository: `KevinSGarrett/Fiverr`. Local root expected by Cursor agents: `C:\Fiverr\Fiverr`. Work from the active cycle branch instructed by the GitHub steward. Do not push to `main`. Cycle branches target `develop` only.

### Jira access
You are allowed to use the connected Jira board when this prompt explicitly assigns Jira work to you. You may read Jira issues, inspect statuses, create issues, update issue fields when appropriate, add comments, transition issues, and maintain Jira mapping evidence. You must follow the PM-defined Jira AC/DoD rules. Do not mark a broad product story Done unless the full source DoD is met. For partial work, use In Progress or In Review as instructed.

### Jira keys in scope
`SCRUM-253`, `SCRUM-254`, `SCRUM-164`, `SCRUM-163`, `SCRUM-212`, `SCRUM-213`, `SCRUM-228`

### File ownership boundaries
You may touch only your assigned files/scope unless your final report documents a necessary exception and no other agent owns that file.

- `src/analysis/orchestrator.py`
- `tests/unit/test_analysis.py`
- `docs/cycle_reports/CYCLE_011_AGENT_C.md`
- `docs/cycle_reports/CYCLE_012_AGENT_B.md`

### Required substantive task count
This prompt assigns 24 substantive tasks. That satisfies the Cycle 012 rule requiring at least 20 substantive tasks per agent. Do not compress these into fewer tasks in your final report; report each task outcome individually.

### Tasks
### Task 1: Fetch the live repository and verify PR #9 head SHA against the local archive state.

**Primary Jira reference:** `SCRUM-253`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 2: Inspect uncommitted local changes in src/analysis/orchestrator.py and determine whether they are intended deliverables or accidental leftovers.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 3: Inspect uncommitted local changes in tests/unit/test_analysis.py and determine whether they contain necessary regression coverage.

**Primary Jira reference:** `SCRUM-164`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 4: Inspect untracked docs/cycle_reports/CYCLE_011_AGENT_C.md and determine whether it must be committed for complete cycle evidence.

**Primary Jira reference:** `SCRUM-163`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 5: Compare local uncommitted changes against PR #9 changed files and list every delta.

**Primary Jira reference:** `SCRUM-212`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 6: If local Agent C work is valid, commit it to cycle/011/integration and push to PR #9 with exact Jira mapping.

**Primary Jira reference:** `SCRUM-213`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 7: If local Agent C work is invalid or out of scope, stash or discard it only after writing an explicit rationale in your final report.

**Primary Jira reference:** `SCRUM-228`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 8: Do not merge PR #9 before this discrepancy is resolved.

**Primary Jira reference:** `SCRUM-253`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 9: Verify PR #9 still has no unresolved Codex threads after any push.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 10: If new Codex comments appear, disposition each one using the required VALID_FIXED / VALID_DEFERRED_BLOCKER / NOT_APPLICABLE_FALSE_POSITIVE / VALID_ALREADY_COVERED categories.

**Primary Jira reference:** `SCRUM-164`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 11: Rerun local validation after any commit: ruff, mypy, pytest coverage fail-under 90, config-check, foundation-gate, and phase2-smoke.

**Primary Jira reference:** `SCRUM-163`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 12: Verify GitHub Actions and codecov/project are green after push.

**Primary Jira reference:** `SCRUM-212`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 13: Verify codecov/patch visibility or document if GitHub only exposes the project mirror.

**Primary Jira reference:** `SCRUM-213`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 14: Update PR #9 body with a local-discrepancy reconciliation section.

**Primary Jira reference:** `SCRUM-228`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 15: Update PR #9 Jira mapping table if Agent C analysis changes are included.

**Primary Jira reference:** `SCRUM-253`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 16: Add a PR comment stating whether local archive discrepancy was committed or intentionally excluded.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 17: Update SCRUM-253 with final PR #8/PR #9 carry-forward state if relevant.

**Primary Jira reference:** `SCRUM-164`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 18: Update SCRUM-254 with the PR discrepancy finding and resolution.

**Primary Jira reference:** `SCRUM-163`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 19: Update product Jira issues impacted by any committed analysis changes, especially SCRUM-163 and SCRUM-164.

**Primary Jira reference:** `SCRUM-212`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 20: If PR #9 is clean, green, and authorized, merge into develop using the approved strategy; otherwise leave it open and document blocker.

**Primary Jira reference:** `SCRUM-213`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 21: After merge, create or verify cycle/012/integration from updated develop.

**Primary Jira reference:** `SCRUM-228`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 22: Do not push to main.

**Primary Jira reference:** `SCRUM-253`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 23: Document every Git command and Jira action in docs/cycle_reports/CYCLE_012_AGENT_B.md.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 24: Stop immediately if branch ancestry is ambiguous or if uncommitted work cannot be safely classified.

**Primary Jira reference:** `SCRUM-164`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.


### Required validation commands
Run the applicable subset, and explain any skipped command:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle012.db
python run.py phase2-smoke
git status --short
```

### Final report requirements
Write a final report with:

1. task-by-task outcome for all assigned tasks;
2. Jira actions performed;
3. AC/DoD bullets advanced and not advanced;
4. files changed;
5. tests/validation run;
6. Codex/CI/Codecov status if applicable;
7. branch and PR status;
8. risks and blockers;
9. explicit no-main confirmation.


---

## Agent C — PM Pack Protocol and Prompt Depth Enforcement

### Mission
Update PM Pack protocols so future cycles cannot use shallow prompts, cannot plan from Git first, and cannot treat Jira as an after-the-fact reporting layer.

### Branch and repository context
Repository: `KevinSGarrett/Fiverr`. Local root expected by Cursor agents: `C:\Fiverr\Fiverr`. Work from the active cycle branch instructed by the GitHub steward. Do not push to `main`. Cycle branches target `develop` only.

### Jira access
You are allowed to use the connected Jira board when this prompt explicitly assigns Jira work to you. You may read Jira issues, inspect statuses, create issues, update issue fields when appropriate, add comments, transition issues, and maintain Jira mapping evidence. You must follow the PM-defined Jira AC/DoD rules. Do not mark a broad product story Done unless the full source DoD is met. For partial work, use In Progress or In Review as instructed.

### Jira keys in scope
`SCRUM-254`, `SCRUM-252`, `SCRUM-250`, `SCRUM-246`

### File ownership boundaries
You may touch only your assigned files/scope unless your final report documents a necessary exception and no other agent owns that file.

- `Project_Manager/03_cursor_agent_system/TASK_SIZING.md`
- `Project_Manager/03_cursor_agent_system/PROMPT_RULES.md`
- `Project_Manager/04_jira_protocol/FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md`
- `Project_Manager/04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md`
- `Project_Manager/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_012.md`
- `docs/cycle_reports/CYCLE_012_AGENT_C.md`

### Required substantive task count
This prompt assigns 24 substantive tasks. That satisfies the Cycle 012 rule requiring at least 20 substantive tasks per agent. Do not compress these into fewer tasks in your final report; report each task outcome individually.

### Tasks
### Task 1: Update TASK_SIZING.md to enforce minimum 20, target 24-32, maximum 40 substantive tasks per agent.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 2: Update TASK_SIZING.md to define what counts as a substantive task and exclude tiny checklist items from task counts.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 3: Update TASK_SIZING.md to define both TASK-COUNT WAIVER and PROMPT-DETAIL WAIVER requirements.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 4: Update PROMPT_RULES.md to require 6,000-word minimum and 8,000-12,000-word preferred prompt length per agent.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 5: Update PROMPT_RULES.md to require AC/DoD bullets embedded in every agent task.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 6: Update PROMPT_RULES.md to reject vague Jira instructions such as update relevant tickets or handle Jira as needed.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 7: Create or update FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md with board inventory, issue selection, and DoD ledger rules.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 8: Append Cycle 012 addendum to JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md clarifying Jira-first planning before code.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 9: Update PM_CORRECTIVE_RULES_CYCLE_012.md with audit findings and binding enforcement rules.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 10: Add a prompt generation checklist that requires every prompt to list exact Jira keys, AC bullets, DoD bullets, files, tests, and final report path.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 11: Add a prompt rejection checklist for shallow prompts.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 12: Add a rule that every PM response must include board audit findings or documented scope limits.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 13: Add a rule that every cycle must check for uncommitted local work not represented in the live PR.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 14: Add a rule that cycle/governance tickets may not replace product-story updates.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 15: Add a rule that Cursor agents assigned Jira work may update Jira directly but must cite exact keys and DOD status.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 16: Update any agent template files in Project_Manager/09_templates if they still use 10-20 tasks.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 17: Search the PM Pack for outdated 10-20 or 3,000-word language and update or annotate it.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 18: Search the PM Pack for old 5-8 task language and update or preserve only as historical context.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 19: Update cycle log or rehydration note so future cycles remember this change.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 20: Verify all new protocol docs are included in the PM Pack index or roadmap if such index exists.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 21: Do not modify product source code.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 22: Commit only PM Pack/protocol/doc changes.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 23: Update SCRUM-254 with the files changed and protocol changes made.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 24: Write final report to docs/cycle_reports/CYCLE_012_AGENT_C.md.

**Primary Jira reference:** `SCRUM-246`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.


### Required validation commands
Run the applicable subset, and explain any skipped command:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle012.db
python run.py phase2-smoke
git status --short
```

### Final report requirements
Write a final report with:

1. task-by-task outcome for all assigned tasks;
2. Jira actions performed;
3. AC/DoD bullets advanced and not advanced;
4. files changed;
5. tests/validation run;
6. Codex/CI/Codecov status if applicable;
7. branch and PR status;
8. risks and blockers;
9. explicit no-main confirmation.


---

## Agent D — Final Integration, Jira/PR Steward, and Cycle 012 Handoff

### Mission
Integrate all Cycle 012 outputs, enforce the PR/Jira gates, update Jira, create or update the PR, and prepare the final handoff without letting shallow prompt or board-drift rules regress.

### Branch and repository context
Repository: `KevinSGarrett/Fiverr`. Local root expected by Cursor agents: `C:\Fiverr\Fiverr`. Work from the active cycle branch instructed by the GitHub steward. Do not push to `main`. Cycle branches target `develop` only.

### Jira access
You are allowed to use the connected Jira board when this prompt explicitly assigns Jira work to you. You may read Jira issues, inspect statuses, create issues, update issue fields when appropriate, add comments, transition issues, and maintain Jira mapping evidence. You must follow the PM-defined Jira AC/DoD rules. Do not mark a broad product story Done unless the full source DoD is met. For partial work, use In Progress or In Review as instructed.

### Jira keys in scope
`SCRUM-254`, `SCRUM-250`, `SCRUM-252`, `SCRUM-253`, `SCRUM-212`, `SCRUM-213`, `SCRUM-214`, `SCRUM-215`, `SCRUM-219`, `SCRUM-225`, `SCRUM-226`, `SCRUM-227`, `SCRUM-228`, `SCRUM-231`, `SCRUM-235`

### File ownership boundaries
You may touch only your assigned files/scope unless your final report documents a necessary exception and no other agent owns that file.

- `docs/cycle_reports/CYCLE_012_AGENT_D.md`
- `docs/jira/ACTIVE_STORY_DOD_LEDGER.md`
- `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_012.md`
- `.github/pull_request_template.md`

### Required substantive task count
This prompt assigns 24 substantive tasks. That satisfies the Cycle 012 rule requiring at least 20 substantive tasks per agent. Do not compress these into fewer tasks in your final report; report each task outcome individually.

### Tasks
### Task 1: Verify Agent A board audit exists and includes issue-type/status summary.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 2: Verify Agent A active story ledger includes all touched Jira keys and AC/DoD status.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 3: Verify Agent B reconciled the PR #9 local archive discrepancy.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 4: Verify Agent C updated PM Pack task sizing, prompt rules, and Jira-first protocols.

**Primary Jira reference:** `SCRUM-253`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 5: Run full local validation on final branch head.

**Primary Jira reference:** `SCRUM-212`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 6: Verify no uncommitted files remain before push.

**Primary Jira reference:** `SCRUM-213`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 7: Verify no untracked cycle report is missing from the PR if it contains relevant evidence.

**Primary Jira reference:** `SCRUM-214`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 8: Verify no direct main changes occurred.

**Primary Jira reference:** `SCRUM-215`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 9: Verify Codex review threads on active PR are all resolved or formally dispositioned.

**Primary Jira reference:** `SCRUM-219`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 10: Verify CI and Codecov gates are green after final push.

**Primary Jira reference:** `SCRUM-225`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 11: Update PR body with Board-first Jira audit summary.

**Primary Jira reference:** `SCRUM-226`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 12: Update PR body with AC/DoD progress table for all touched issues.

**Primary Jira reference:** `SCRUM-227`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 13: Update PR body with local-discrepancy reconciliation result.

**Primary Jira reference:** `SCRUM-228`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 14: Update PR body with validation evidence.

**Primary Jira reference:** `SCRUM-231`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 15: Update PR body with Codex/Codecov status.

**Primary Jira reference:** `SCRUM-235`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 16: Update SCRUM-254 with final implementation status and remaining blockers.

**Primary Jira reference:** `SCRUM-254`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 17: Update SCRUM-250 if the older Jira mapping issue can move to In Review or Done after Cycle 012 rules land.

**Primary Jira reference:** `SCRUM-250`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 18: Update SCRUM-252 if prompt/task/Jira-agent authority rules are superseded or expanded by Cycle 012.

**Primary Jira reference:** `SCRUM-252`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 19: Update product Jira issues that receive actual code/docs progress in this cycle.

**Primary Jira reference:** `SCRUM-253`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 20: Do not mark product stories Done unless full source DOD is satisfied.

**Primary Jira reference:** `SCRUM-212`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 21: Create follow-up Jira items for any missing AC/DoD coverage discovered during the board audit.

**Primary Jira reference:** `SCRUM-213`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 22: If PR #9 can merge, merge only after all gates and authorization; otherwise leave open with explicit blocker comment.

**Primary Jira reference:** `SCRUM-214`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 23: If PR #9 merges, create cycle/012/integration from updated develop for any remaining Cycle 012 docs/protocol work.

**Primary Jira reference:** `SCRUM-215`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.
### Task 24: Write final report to docs/cycle_reports/CYCLE_012_AGENT_D.md with every gate result.

**Primary Jira reference:** `SCRUM-219`.  
**AC/DoD requirement:** Tie this work to the exact acceptance criteria and definition-of-done text from the Jira issue. Do not treat the task as complete unless the final report states which AC/DoD bullets were advanced, which remain incomplete, and which evidence proves the status.  
**Execution detail:** Perform the task in the assigned files or Jira scope only. Avoid overlapping with other agents. If the task requires Jira, use the connected Jira board directly and record the issue key, action, and result. If the task requires source edits, keep the implementation deterministic, typed, tested, and compatible with existing PR gates.  
**Validation expectation:** Add or update tests/docs/ledger evidence as appropriate. Include the validation command or Jira action evidence in your final report.  
**Stop condition:** Stop and report if the required Jira issue cannot be found, if the AC/DoD text conflicts with the code direction, if branch ancestry is unclear, or if another agent owns the file.


### Required validation commands
Run the applicable subset, and explain any skipped command:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle012.db
python run.py phase2-smoke
git status --short
```

### Final report requirements
Write a final report with:

1. task-by-task outcome for all assigned tasks;
2. Jira actions performed;
3. AC/DoD bullets advanced and not advanced;
4. files changed;
5. tests/validation run;
6. Codex/CI/Codecov status if applicable;
7. branch and PR status;
8. risks and blockers;
9. explicit no-main confirmation.


## PM Pack Updates Included

- `Project_Manager/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_012.md`
- `Project_Manager/03_cursor_agent_system/TASK_SIZING.md`
- `Project_Manager/03_cursor_agent_system/PROMPT_RULES.md`
- `Project_Manager/04_jira_protocol/FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md`
- `Project_Manager/04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md` addendum

## Cycle 012 Stop Conditions

- Do not merge PR #9 until local archive discrepancy is reconciled.
- Do not begin broad feature expansion until board-first audit and AC/DoD ledger exist.
- Do not mark product stories Done for partial scaffold or placeholder work.
- Do not push to main.
