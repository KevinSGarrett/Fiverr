# Cycle 013 Fiverr PM Response

## Review conclusion

The Cycle 012 prompts were a major improvement and should be preserved as the new quality floor. After reviewing the attached repo, attached PM Pack, live GitHub PRs, live PR #10 checks, Codex review threads, and the active Jira control issues, the correct next move is not broad new feature expansion. Cycle 013 must first close the PR #10 merge gate.

## Current GitHub state

PR #10 is open, mergeable, and targets `develop` from `cycle/012/integration`. CI is green and the `codecov/project` job is green. However, PR #10 has three unresolved Codex threads, including two P1 blockers. Therefore PR #10 is not merge-ready.

Open PR #10 blockers:

1. P1: `PM_Pack/00_index/MASTER_INDEX.md` references mandatory files that are absent from the committed repo.
2. P1: `PM_Pack/09_templates/AGENT_PROMPT_C.md` references nonexistent paths such as `src/scoring/` and `tests/unit/test_scoring.py`.
3. P2: `PM_Pack/03_cursor_agent_system/PROMPT_TEMPLATE.md` has inconsistent task-detail thresholds.

## Attached repo state

The attached repo is on `cycle/012/integration`. It has uncommitted tracked changes in:

```text
M docs/cycle_reports/CYCLE_012_AGENT_B.md
 M src/dashboard/app.py
 M src/orchestrator.py
 M tests/unit/test_dashboard.py
 M tests/unit/test_orchestrator_helpers.py
?? PM_Pack/00_index/QUICK_NAV.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_002.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_003.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_004.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_006.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_008.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_010.md
?? PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_011.md
?? PM_Pack/01_pm_instructions/PM_ROLE.md
?? PM_Pack/02_cycle_protocol/CYCLE_NAMING.md
?? PM_Pack/02_cycle_protocol/PACK_UPDATE_PROTOCOL.md
?? PM_Pack/02_cycle_protocol/PR_BATCH_STRATEGY.md
?? PM_Pack/03_cursor_agent_system/AGENT_ROSTER.md
?? PM_Pack/04_jira_protocol/CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md
?? PM_Pack/04_jira_protocol/JIRA_COMMENT_PROTOCOL.md
?? PM_Pack/04_jira_protocol/JIRA_FIELD_STANDARDS.md
?? PM_Pack/04_jira_protocol/JIRA_RULES.md
?? PM_Pack/04_jira_protocol/JIRA_UPDATE_CHECKLIST.md
?? PM_Pack/05_github_protocol/
?? PM_Pack/06_review_and_qa/
?? PM_Pack/07_hydration/
?? PM_Pack/08_task_queue/DEPENDENCY_MAP.md
?? PM_Pack/08_task_queue/EPIC_STATUS_TRACKER.md
?? PM_Pack/08_task_queue/TASK_BACKLOG.md
?? PM_Pack/09_templates/CYCLE_REPLY_TEMPLATE.md
?? PM_Pack/09_templates/JIRA_UPDATE_TEMPLATE.md
?? PM_Pack/09_templates/REVIEW_REPORT_TEMPLATE.md
?? PM_Pack/10_cycle_log/CYCLE_000_INIT.md
?? PM_Pack/10_cycle_log/CYCLE_001.md
?? PM_Pack/10_cycle_log/CYCLE_001_CORRECTIVE_REVIEW.md
?? PM_Pack/10_cycle_log/CYCLE_002.md
?? PM_Pack/10_cycle_log/CYCLE_003.md
?? PM_Pack/10_cycle_log/CYCLE_004.md
?? PM_Pack/10_cycle_log/CYCLE_005.md
?? PM_Pack/10_cycle_log/CYCLE_005_FULL_RESPONSE.md
?? PM_Pack/10_cycle_log/CYCLE_006.md
?? PM_Pack/10_cycle_log/CYCLE_006_FULL_RESPONSE.md
?? PM_Pack/10_cycle_log/CYCLE_007.md
?? PM_Pack/10_cycle_log/CYCLE_008.md
?? PM_Pack/10_cycle_log/CYCLE_009.md
?? PM_Pack/10_cycle_log/CYCLE_010.md
?? PM_Pack/10_cycle_log/CYCLE_011.md
?? PM_Pack/10_cycle_log/CYCLE_012_PM_RESPONSE.md
?? PM_Pack/CYCLE_007_PM_RESPONSE.md
?? PM_Pack/CYCLE_008_PM_RESPONSE.md
?? PM_Pack/CYCLE_009_PM_RESPONSE.md
?? PM_Pack/CYCLE_010_PM_RESPONSE.md
?? PM_Pack/CYCLE_011_PM_RESPONSE.md
?? PM_Pack/WAVE_SCHEDULE.md
?? PM_Pack/ref/
?? coverage.xml
```

These changes appear to be legitimate Cycle 012 follow-up work around dashboard app-entry diagnostics and `SCRUM-228`, but they are not represented in the live PR head reviewed in GitHub. Cycle 013 must reconcile them explicitly: commit/push with validation, or document why they are out of scope and safely discarded.

The attached repo zip also contains a local `.env` file. I did not read, print, copy, or include its contents. Treat the zip as sensitive and do not share it publicly.

## Jira state

`SCRUM-256` already exists and is In Progress as the Cycle 013 control ticket. It correctly captures the PR #10 blockers and local-attachment findings. `SCRUM-255` remains open for the missing Cycle 012 Agent A report and the AC/DoD closure gaps from the Cycle 012 handoff.

Product stories should remain conservative. Several dashboard and integration stories are In Progress or In Review, which is appropriate. They should not be marked Done until full source AC/DoD is evidenced.

## Cycle 013 assignment summary

Cycle 013 assigns 96 substantive tasks total across four Cursor agents.

- Agent A: 24 tasks for PM Pack required-file reconciliation and missing Agent A artifact recovery.
- Agent B: 24 tasks for PR #10 stewardship, Codex disposition, CI/Codecov, PR body, and merge gate.
- Agent C: 24 tasks for prompt-template validation path correction and threshold consistency.
- Agent D: 24 tasks for Jira AC/DoD ledger stewardship and local app-entry reconciliation.

## Branch rule

While PR #10 remains open, agents should work on `cycle/012/integration` as a Cycle 013 correction pass. Do not create a new `cycle/013/integration` branch until PR #10 merges into `develop`. Main remains untouched.

## Cycle 013 PM Pack change log (Agent A corrective pass)

- Blocker addressed: Codex P1 required-file consistency mismatch in `PM_Pack/00_index/MASTER_INDEX.md`.
- Files updated:
  - `PM_Pack/00_index/MASTER_INDEX.md` (required-file consistency gate text + Cycle 013 protocol memory note reference)
  - `PM_Pack/00_index/FILE_REGISTRY.md` (Cycle 013 required-file metadata table: role/read priority/owner/update trigger)
  - `PM_Pack/07_hydration/HYDRATION_HEADER.md` (cycle-current rewrite for PR #10 gate context)
  - `PM_Pack/07_hydration/STATE_SNAPSHOT.md` (cycle-current rewrite for branch/Jira/security state)
  - `PM_Pack/10_cycle_log/CYCLE_013_PROTOCOL_MEMORY_NOTE.md` (new protocol memory anchor)
  - `docs/cycle_reports/CYCLE_012_AGENT_A.md` (formal disposition for missing artifact)
  - `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` (SCRUM-255 evidence narrative update)
- Validation recorded:
  - Branch and discrepancy checks (`git branch --show-current`, `git status --short`, `git log --oneline --decorate -n 12`)
  - Required-file presence/track audit (`git ls-files PM_Pack` + PM Pack tree inspection)
  - Path/reference checks (`rg`/`glob` searches for Cycle 012 Agent A and hydration references)
  - Documentation lint feasibility check and report-level command transcript capture

---

# Cycle 013 Cursor Agent A: PM Pack Required-File Reconciliation and Agent A Artifact Recovery

Recommended model: Codex 5.3  
Role: PM Pack Architect / Documentation Steward  
Repository: `KevinSGarrett/Fiverr`  
Local project folder: `C:\Fiverr`  
Current live PR gate: PR #10, `cycle/012/integration` into `develop`  
Primary Jira keys: SCRUM-256, SCRUM-255, SCRUM-254, SCRUM-250, SCRUM-252

## Non-negotiable operating context

You are executing Cycle 013 for the Fiverr Research System. The operator explicitly approved the longer, more detailed Cursor prompt style from Cycle 012, and this cycle must preserve that quality bar. Do not shrink the prompt, do not reduce task detail, and do not treat Jira as an after-the-fact mapping exercise. Planning starts from Jira, acceptance criteria, and Definition of Done. PR #10 is currently open and mergeable, CI is green, and `codecov/project` is green, but three Codex review threads remain unresolved. Those unresolved threads are merge blockers. The attached repo also contains local uncommitted work that must be reconciled rather than silently ignored.

You must not touch `main`. You must not push directly to `main`. While PR #10 remains open, your correction work belongs on `cycle/012/integration` unless the PM explicitly instructs otherwise. A new `cycle/013/integration` branch should only be created after PR #10 is merged into `develop`. Do not mark any product story Done unless full source acceptance criteria and full source Definition of Done are satisfied with evidence. Partial scaffold, placeholder contract, dashboard diagnostics, governance docs, or smoke-only progress can move a story to In Review when supported, but not to Done.

Security rule: the uploaded local repo archive contains a local `.env` file. Do not print, commit, paste, summarize, or expose its contents. Before any push, verify `.env`, `coverage.xml`, local databases, caches, screenshots, and generated runtime artifacts are not staged.

## Mission

Fix the P1 PM Pack missing-file blocker, restore required-file consistency, deliver or formally disposition the missing Cycle 012 Agent A report, and ensure PM Pack index/hydration files are committed rather than stranded as untracked local files.

## Required task list

### A01 — Confirm branch and repo cleanliness before editing

Run `git branch --show-current`, `git status --short`, and `git log --oneline --decorate -n 12`. Confirm you are on `cycle/012/integration` while PR #10 is open. Do not create a new branch unless PR #10 has merged and PM explicitly authorizes the new branch. Record any uncommitted files before editing. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A02 — Inventory PM Pack committed files versus untracked files

Compare `git ls-files PM_Pack` against the attached/local `PM_Pack/` tree. Identify files that MASTER_INDEX requires but Git does not currently track. Produce a table showing required path, present locally, tracked in Git, and required action. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A03 — Fix MASTER_INDEX required-file consistency

Open `PM_Pack/00_index/MASTER_INDEX.md` and every referenced required path. Either add the missing required files into the repo or downgrade/remove the requirement if the file is not actually mandatory. Prefer committing the missing hydration and state files from the PM Pack attachment if they are valid. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A04 — Add missing hydration files from the PM Pack attachment

Ensure `PM_Pack/07_hydration/HYDRATION_HEADER.md`, `PM_Pack/07_hydration/STATE_SNAPSHOT.md`, and any other mandatory hydration files referenced by the index exist in the repository with source-safe, cycle-current content. Do not create empty placeholder files unless they explicitly state their active purpose and minimum content. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A05 — Update FILE_REGISTRY to match reality

Update `PM_Pack/00_index/FILE_REGISTRY.md` so every mandatory file in the master index has a registry entry and every registry entry points to an existing committed file. Include cycle role, read priority, owner, and update trigger for each new file. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A06 — Create Cycle 013 corrective memory note

Create or update `PM_Pack/10_cycle_log/CYCLE_013_PROTOCOL_MEMORY_NOTE.md` to capture the three PR #10 Codex blockers, local uncommitted-change findings, `.env` security note, and the rule that PR #10 must be fixed before broad new work. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A07 — Deliver missing Cycle 012 Agent A report if recoverable

Search the repo, PM Pack, local reports, and attached files for any Agent A Cycle 012 output. If recoverable, create `docs/cycle_reports/CYCLE_012_AGENT_A.md` with exact evidence. If not recoverable, create that file as a formal disposition report explaining that the expected artifact is missing and listing the replacement evidence and required follow-up. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A08 — Update SCRUM-255 evidence narrative in docs

Update local docs, especially `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and any cycle report references, to reflect whether Agent A was delivered or formally dispositioned. Do not mark `SCRUM-255` Done unless all its acceptance criteria are satisfied. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A09 — Preserve no-secret handling for local attachments

Add a note to the appropriate PM Pack security or cycle log file stating that the attached repo zip included `.env`; agents must not print, copy, commit, or upload secrets. Confirm `.gitignore` covers `.env` and related local artifacts. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A10 — Separate required PM Pack files from generated runtime artifacts

Make sure `coverage.xml`, runtime databases, caches, and other generated files are not added to Git when adding PM Pack files. Confirm with `git status --short` before staging. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A11 — Stage only intended PM Pack and report files

Use precise `git add` commands for required PM Pack files and Agent A/report artifacts. Avoid `git add .` unless you first verify `.env`, coverage, data, and runtime artifacts are excluded. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A12 — Run Markdown consistency review for new PM Pack files

Check that added PM Pack files have headings, purpose, source, owner, update trigger, and no broken required-file references. Search for `PM_Pack/07_hydration` and confirm each referenced path exists. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A13 — Cross-check against Codex P1 wording

Re-read the P1 Codex thread about missing mandatory pack files. Confirm your fix directly answers the complaint. Prepare a short evidence statement for Agent B to post to the thread after validation. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A14 — Ensure PM Pack still points to board-first protocol

Verify `PM_Pack/04_jira_protocol/FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md` remains mandatory and referenced from the master index. Ensure no update weakens the Cycle 012 board-first rule. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A15 — Ensure PM Pack still points to task sizing protocol

Verify `PM_Pack/03_cursor_agent_system/TASK_SIZING.md` still says minimum 20, target 24-32, maximum 40 substantive tasks per Cursor agent, and minimum 6,000 words per agent prompt unless waiver. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A16 — Update Cycle 013 PM Pack change log

Append a precise change log entry listing all PM Pack files added or modified, which Codex blocker they address, and what validation was run. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A17 — Coordinate with Agent C on template consistency

Do not independently change Agent C validation commands unless coordinated with Agent C. If you touch shared template files, note the overlap clearly in your report. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A18 — Coordinate with Agent D on Jira ledger language

If you add Agent A or SCRUM-255 evidence, tell Agent D exactly what Jira keys and AC/DoD bullets were advanced so the active story ledger can be updated correctly. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A19 — Run local documentation validation commands

At minimum run `python -m ruff check .` if code was not touched by Agent A, plus any available markdown/path validation command in the repo. If no markdown checker exists, run grep/path checks and document that limitation. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A20 — Prepare commit message for PM Pack consistency

Recommended commit: `docs(pm-pack): restore required file consistency [Agent A]`. Commit only after inspection and validation. If you cannot commit, create a report explaining exact blockers. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A21 — Prepare PR body addendum for Agent B

Write a PR body addendum section summarizing required-file reconciliation, files added, missing Agent A disposition, validation, and Jira keys. Agent B will decide whether to update PR body after all agents finish. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A22 — Write final Agent A cycle report

Create `docs/cycle_reports/CYCLE_013_AGENT_A.md` summarizing tasks completed, files changed, Jira keys, tests run, Codex blocker status, security checks, and unresolved risks. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A23 — Do not resolve Codex threads yourself unless assigned

Unless you are also serving as GitHub Steward, leave final thread reply/resolution to Agent B after all validation is complete. Provide evidence in your report. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### A24 — Final handoff gate

Before final handoff, confirm: required files exist, master index is consistent, missing Agent A report is delivered/dispositioned, `.env` not staged, and SCRUM-255 has evidence ready for Jira update. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

## Required validation block

At the end of your work, report every command you ran and the result. Use the exact command text. If a command cannot run because dependencies are missing locally, say that directly and do not claim success. If you push changes, Agent B must verify live CI and Codecov after the push. Minimum validation expectation for code-affecting work is:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle013.db
python run.py phase2-smoke
```

Documentation-only work should still run the feasible subset and should include path/grep checks proving the Codex complaint is directly resolved.

## Jira update requirements

You may perform Jira operations if assigned and available in your environment. Every Jira update must include: branch, PR number, files changed, validation evidence, AC bullets advanced, DoD bullets remaining, status recommendation, and whether Done is allowed. Do not update only governance tickets if product stories were touched. Product stories touched by this cycle include at least: `SCRUM-212`, `SCRUM-213`, `SCRUM-214`, `SCRUM-215`, `SCRUM-219`, `SCRUM-225`, `SCRUM-226`, `SCRUM-227`, `SCRUM-228`, `SCRUM-231`, and `SCRUM-235`.

## Final response/report requirements

Create your cycle report under `docs/cycle_reports/CYCLE_013_AGENT_A.md`. The report must include: summary, Jira keys, files changed, Codex thread impact, validation commands, local discrepancy handling, no-main confirmation, no-secret confirmation, and unresolved risks. If you did not change code, say so. If you changed docs only, list docs exactly. If you could not complete a task, explain why and identify the blocking issue key.


---

# Cycle 013 Cursor Agent B: GitHub PR #10 Stewardship, Codex Disposition, and Merge Gate

Recommended model: Codex 5.3  
Role: Integration / GitHub Steward  
Repository: `KevinSGarrett/Fiverr`  
Local project folder: `C:\Fiverr`  
Current live PR gate: PR #10, `cycle/012/integration` into `develop`  
Primary Jira keys: SCRUM-256, SCRUM-253, SCRUM-254, SCRUM-250, SCRUM-255

## Non-negotiable operating context

You are executing Cycle 013 for the Fiverr Research System. The operator explicitly approved the longer, more detailed Cursor prompt style from Cycle 012, and this cycle must preserve that quality bar. Do not shrink the prompt, do not reduce task detail, and do not treat Jira as an after-the-fact mapping exercise. Planning starts from Jira, acceptance criteria, and Definition of Done. PR #10 is currently open and mergeable, CI is green, and `codecov/project` is green, but three Codex review threads remain unresolved. Those unresolved threads are merge blockers. The attached repo also contains local uncommitted work that must be reconciled rather than silently ignored.

You must not touch `main`. You must not push directly to `main`. While PR #10 remains open, your correction work belongs on `cycle/012/integration` unless the PM explicitly instructs otherwise. A new `cycle/013/integration` branch should only be created after PR #10 is merged into `develop`. Do not mark any product story Done unless full source acceptance criteria and full source Definition of Done are satisfied with evidence. Partial scaffold, placeholder contract, dashboard diagnostics, governance docs, or smoke-only progress can move a story to In Review when supported, but not to Done.

Security rule: the uploaded local repo archive contains a local `.env` file. Do not print, commit, paste, summarize, or expose its contents. Before any push, verify `.env`, `coverage.xml`, local databases, caches, screenshots, and generated runtime artifacts are not staged.

## Mission

Own PR #10 gate discipline. Do not merge while Codex threads are unresolved. Reconcile branch updates, verify CI/Codecov/local parity, post formal Codex dispositions, update PR body, and preserve no-main policy.

## Required task list

### B01 — Confirm PR #10 live state

Use GitHub to confirm PR #10 state, base branch, head SHA, mergeability, draft status, changed files, review threads, reviews, and latest workflow runs. Record findings in `docs/cycle_reports/CYCLE_013_AGENT_B.md`. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B02 — Verify branch policy before any push

Confirm current branch is `cycle/012/integration` while PR #10 remains open. Do not create `cycle/013/integration` until PR #10 merges into `develop`. Confirm `main` is untouched. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B03 — Read all PR #10 Codex threads

Read each unresolved review thread and classify as `VALID_FIXED`, `VALID_DEFERRED_BLOCKER`, `VALID_ALREADY_COVERED`, or `NOT_APPLICABLE_FALSE_POSITIVE`. Initial expectation: all three current Codex items are valid and should be fixed. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B04 — Do not resolve threads before evidence exists

Keep all Codex review threads unresolved until the relevant file changes are committed, pushed, and validation passes. This is mandatory even if a local fix seems obvious. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B05 — Coordinate Agent A PM Pack required-file fix

Wait for or inspect Agent A changes for the MASTER_INDEX required-file blocker. Confirm the files now exist in Git, not just in local untracked files. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B06 — Coordinate Agent C validation-template fixes

Wait for or inspect Agent C changes for Agent C prompt validation commands and threshold consistency. Confirm they directly address the two prompt/template Codex findings. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B07 — Coordinate Agent D local-code reconciliation

Inspect whether the local `src/dashboard/app.py`, `src/orchestrator.py`, dashboard tests, and Agent B report deltas are committed or intentionally discarded. PR #10 should not merge while these are ambiguous. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B08 — Check `.env` and generated artifact hygiene

Before staging/pushing, run `git status --short` and verify `.env`, `coverage.xml`, runtime databases, caches, screenshots, and data artifacts are not staged. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B09 — Run full local parity after all agent changes

Run `python -m ruff check .`, `python -m mypy src`, `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`, `python run.py config-check`, `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle013.db`, and `python run.py phase2-smoke`. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B10 — Handle missing local dependencies honestly

If your local environment lacks dependencies, do not claim tests passed. Install per project instructions if allowed; otherwise document the environment blocker and rely only on live CI for those gates. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B11 — Push only clean, reviewed commits

After validation, push commits to `cycle/012/integration`. Do not force push unless explicitly authorized and justified. Preserve PR #10 history and the prior Cycle 012 evidence. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B12 — Re-check GitHub Actions after push

After push, fetch the latest commit SHA and workflow run. Verify `Lint, Typecheck, Tests, and Gates` is successful and `codecov/project` is successful. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B13 — Check Codecov patch if present

If `codecov/patch` appears, verify it is successful. If it does not appear, document whether project policy requires it and whether the repo currently exposes only the project mirror job. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B14 — Prepare Codex thread disposition reply for P1 MASTER_INDEX

Reply with a concise formal disposition naming files added or index corrected, commit SHA, validation commands, and Jira keys. Resolve only after confirmation. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B15 — Prepare Codex thread disposition reply for P1 Agent C validation commands

Reply with a concise formal disposition naming the corrected file, the invalid paths removed or guarded, validation evidence, and Jira keys. Resolve only after confirmation. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B16 — Prepare Codex thread disposition reply for P2 threshold consistency

Reply with the final consistent threshold. Expected answer: all substantive tasks require at least 100 words of implementation detail, and the 50-word reference was removed or corrected. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B17 — Resolve Codex threads only after successful CI

Use GitHub thread resolution only after local parity and live CI/Codecov are green. If any thread remains valid but unfixed, leave PR blocked and document exactly why. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B18 — Update PR #10 body

Update the PR body with a Cycle 013 addendum listing resolved Codex threads, local discrepancy reconciliation, Agent A report status, validation evidence, Jira AC/DoD updates, and no-main confirmation. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B19 — Request review or leave merge blocked

If all gates pass, mark PR #10 ready for final review and state it is merge-ready pending PM/operator authorization. If not, leave it open and blocked with precise next actions. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B20 — Do not merge without explicit authorization

Even if mergeable and green, do not merge PR #10 unless PM/operator authorization is explicitly granted in the cycle instructions or conversation. If authorization is not present, stop at merge-ready. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B21 — If merge is authorized, merge to develop only

If authorization is present and all gates pass, merge PR #10 into `develop` using the repo’s approved merge method. Never merge or push directly to `main`. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B22 — After merge, prepare next clean branch only if needed

If PR #10 merges, create `cycle/013/integration` from updated `develop` for follow-on product work. If PR #10 does not merge, do not create a new branch. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B23 — Update Jira comments for stewarded issues

Update `SCRUM-256`, `SCRUM-254`, `SCRUM-255`, and any touched product story keys with branch, PR, commit SHA, files, validation, Codex status, and AC/DoD progress. Do not mark product stories Done without full source DoD evidence. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### B24 — Write final Agent B stewardship report

Create `docs/cycle_reports/CYCLE_013_AGENT_B.md` with GitHub state, Codex disposition table, CI/Codecov status, local parity results, Jira updates, merge decision, and next steps. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

## Required validation block

At the end of your work, report every command you ran and the result. Use the exact command text. If a command cannot run because dependencies are missing locally, say that directly and do not claim success. If you push changes, Agent B must verify live CI and Codecov after the push. Minimum validation expectation for code-affecting work is:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle013.db
python run.py phase2-smoke
```

Documentation-only work should still run the feasible subset and should include path/grep checks proving the Codex complaint is directly resolved.

## Jira update requirements

You may perform Jira operations if assigned and available in your environment. Every Jira update must include: branch, PR number, files changed, validation evidence, AC bullets advanced, DoD bullets remaining, status recommendation, and whether Done is allowed. Do not update only governance tickets if product stories were touched. Product stories touched by this cycle include at least: `SCRUM-212`, `SCRUM-213`, `SCRUM-214`, `SCRUM-215`, `SCRUM-219`, `SCRUM-225`, `SCRUM-226`, `SCRUM-227`, `SCRUM-228`, `SCRUM-231`, and `SCRUM-235`.

## Final response/report requirements

Create your cycle report under `docs/cycle_reports/CYCLE_013_AGENT_B.md`. The report must include: summary, Jira keys, files changed, Codex thread impact, validation commands, local discrepancy handling, no-main confirmation, no-secret confirmation, and unresolved risks. If you did not change code, say so. If you changed docs only, list docs exactly. If you could not complete a task, explain why and identify the blocking issue key.


---

# Cycle 013 Cursor Agent C: Prompt Template, Agent C Validation Path, and PM Pack Consistency Hardening

Recommended model: Codex 5.3  
Role: PM Pack QA / Validation Command Steward  
Repository: `KevinSGarrett/Fiverr`  
Local project folder: `C:\Fiverr`  
Current live PR gate: PR #10, `cycle/012/integration` into `develop`  
Primary Jira keys: SCRUM-256, SCRUM-254, SCRUM-252, SCRUM-246

## Non-negotiable operating context

You are executing Cycle 013 for the Fiverr Research System. The operator explicitly approved the longer, more detailed Cursor prompt style from Cycle 012, and this cycle must preserve that quality bar. Do not shrink the prompt, do not reduce task detail, and do not treat Jira as an after-the-fact mapping exercise. Planning starts from Jira, acceptance criteria, and Definition of Done. PR #10 is currently open and mergeable, CI is green, and `codecov/project` is green, but three Codex review threads remain unresolved. Those unresolved threads are merge blockers. The attached repo also contains local uncommitted work that must be reconciled rather than silently ignored.

You must not touch `main`. You must not push directly to `main`. While PR #10 remains open, your correction work belongs on `cycle/012/integration` unless the PM explicitly instructs otherwise. A new `cycle/013/integration` branch should only be created after PR #10 is merged into `develop`. Do not mark any product story Done unless full source acceptance criteria and full source Definition of Done are satisfied with evidence. Partial scaffold, placeholder contract, dashboard diagnostics, governance docs, or smoke-only progress can move a story to In Review when supported, but not to Done.

Security rule: the uploaded local repo archive contains a local `.env` file. Do not print, commit, paste, summarize, or expose its contents. Before any push, verify `.env`, `coverage.xml`, local databases, caches, screenshots, and generated runtime artifacts are not staged.

## Mission

Fix the Codex P1/P2 prompt-template blockers. Ensure all agent prompt templates use existing repo paths, task-specific validation fallback rules, and one strict implementation-detail threshold.

## Required task list

### C01 — Inspect current repository paths before editing commands

Run `find src -maxdepth 2 -type d | sort` and `find tests -maxdepth 3 -type f | sort | head -200`. Confirm whether `src/scoring/` and `tests/unit/test_scoring.py` exist. They are expected not to exist in the current repo. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C02 — Open Agent C template and identify invalid commands

Review `PM_Pack/09_templates/AGENT_PROMPT_C.md`. Mark every validation command that references nonexistent paths or assumes future scoring modules are already present. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C03 — Replace nonexistent-path commands with task-aware validation guidance

Update Agent C prompt template so default commands target existing files for current analysis work, and future scoring paths are conditional: agents must only run scoring-specific commands after scoring modules exist or after their task creates them. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C04 — Add path-existence preflight to Agent C prompt

Require Agent C to run a path preflight before validation. If a target directory is absent, the agent must explain whether the current task should create it or choose the nearest existing test suite instead of failing blindly. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C05 — Prefer existing current paths for analysis validation

For current repo state, default Agent C validation should reference existing analysis and orchestration files such as `src/analysis`, `src/orchestrator.py`, and existing unit tests. Do not hard-code nonexistent scoring paths as mandatory. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C06 — Open PROMPT_TEMPLATE and find threshold mismatch

Search `PM_Pack/03_cursor_agent_system/PROMPT_TEMPLATE.md` for `50 words`, `100 words`, `implementation detail`, and validation threshold text. Identify every inconsistent mention. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C07 — Set one strict threshold: 100 words per substantive task

Replace lower detail thresholds with one consistent rule: each substantive task must include at least 100 words of implementation detail unless a documented prompt-detail waiver is included. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C08 — Propagate threshold consistency to PROMPT_RULES

Review `PM_Pack/03_cursor_agent_system/PROMPT_RULES.md` and ensure it does not conflict with the 100-word per-task detail minimum and 6,000-word per-agent prompt minimum. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C09 — Propagate threshold consistency to TASK_SIZING

Review `PM_Pack/03_cursor_agent_system/TASK_SIZING.md` and preserve minimum 20, target 24-32, maximum 40 substantive tasks per agent. Confirm no older 5-8 or 10-16 limit remains as the active standard. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C10 — Check AGENT_PROMPT_A-D for old limits

Search `PM_Pack/09_templates/AGENT_PROMPT_A.md` through `AGENT_PROMPT_D.md` for old task-count or word-count rules. Update any outdated limits to the Cycle 013 standard. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C11 — Make validation commands resilient but not vague

Every agent prompt should include exact commands where applicable plus a path-existence fallback. Avoid vague instructions such as “run tests” without commands, but also avoid commands that are guaranteed to fail on current repo layout. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C12 — Update PM Pack corrective rules for PR #10 lessons

Add a Cycle 013 corrective note explaining that prompt templates must be validated against the actual current repository, not the intended future architecture. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C13 — Update master index if prompt files changed

If you add or rename any prompt/validation guidance files, update `PM_Pack/00_index/MASTER_INDEX.md` and `FILE_REGISTRY.md` to keep the pack internally consistent. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C14 — Create a prompt-template self-check section

Add a self-check checklist requiring each generated prompt to prove: task count met, AC/DoD keys listed, files exist or creation is part of task, commands are valid for current repo, and no obsolete path assumptions remain. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C15 — Run grep-based regression checks

Run searches for `src/scoring`, `test_scoring.py`, `50 words`, `5-8`, and `10-16` across PM Pack files. Keep future references only when explicitly labeled historical, superseded, or conditional. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C16 — Review PR template for consistency

If `.github/pull_request_template.md` was changed in PR #10, ensure it requires Codex disposition, CI/Codecov, Jira keys, AC/DoD progress, and no-main confirmation without referencing unavailable artifacts. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C17 — Coordinate with Agent A for required file references

If your prompt-template updates reference hydration or state files, coordinate with Agent A so those files exist and are tracked. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C18 — Coordinate with Agent B on Codex reply evidence

Provide Agent B a bullet list of exact file changes, line/section names, validation commands, and the disposition category for both prompt-related Codex threads. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C19 — Run local validation focused on docs and Python if available

Run `python -m ruff check .` and `python -m mypy src` if dependencies exist. If dependency setup blocks validation, document the exact failure and rely on CI only after push. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C20 — Do not create fake scoring modules just to satisfy commands

The fix is to correct the template, not to add empty `src/scoring` or `tests/unit/test_scoring.py` files unless the current Jira-selected work truly implements scoring. Avoid architectural drift. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C21 — Commit prompt/template changes

Recommended commit: `docs(pm-pack): fix prompt validation paths and detail thresholds [Agent C]`. Stage only PM Pack/template files and any report file. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C22 — Update cycle report evidence

Create `docs/cycle_reports/CYCLE_013_AGENT_C.md` with before/after commands, path preflight result, grep checks, tests run, Jira keys, and remaining risks. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C23 — Prepare formal disposition text

Draft formal Codex replies: one for invalid Agent C paths and one for the threshold mismatch. Include commit SHA placeholder for Agent B to fill after push. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### C24 — Final handoff gate

Before handoff, confirm all active templates use current standards, no invalid mandatory validation path remains, and all lower thresholds are removed or explicitly superseded. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

## Required validation block

At the end of your work, report every command you ran and the result. Use the exact command text. If a command cannot run because dependencies are missing locally, say that directly and do not claim success. If you push changes, Agent B must verify live CI and Codecov after the push. Minimum validation expectation for code-affecting work is:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle013.db
python run.py phase2-smoke
```

Documentation-only work should still run the feasible subset and should include path/grep checks proving the Codex complaint is directly resolved.

## Jira update requirements

You may perform Jira operations if assigned and available in your environment. Every Jira update must include: branch, PR number, files changed, validation evidence, AC bullets advanced, DoD bullets remaining, status recommendation, and whether Done is allowed. Do not update only governance tickets if product stories were touched. Product stories touched by this cycle include at least: `SCRUM-212`, `SCRUM-213`, `SCRUM-214`, `SCRUM-215`, `SCRUM-219`, `SCRUM-225`, `SCRUM-226`, `SCRUM-227`, `SCRUM-228`, `SCRUM-231`, and `SCRUM-235`.

## Final response/report requirements

Create your cycle report under `docs/cycle_reports/CYCLE_013_AGENT_C.md`. The report must include: summary, Jira keys, files changed, Codex thread impact, validation commands, local discrepancy handling, no-main confirmation, no-secret confirmation, and unresolved risks. If you did not change code, say so. If you changed docs only, list docs exactly. If you could not complete a task, explain why and identify the blocking issue key.


---

# Cycle 013 Cursor Agent D: Jira AC/DoD Ledger, Local App-Entry Reconciliation, and Product Story Status Stewardship

Recommended model: Codex 5.3  
Role: QA / Jira Ledger Steward  
Repository: `KevinSGarrett/Fiverr`  
Local project folder: `C:\Fiverr`  
Current live PR gate: PR #10, `cycle/012/integration` into `develop`  
Primary Jira keys: SCRUM-256, SCRUM-255, SCRUM-228, SCRUM-212, SCRUM-213, SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, SCRUM-231, SCRUM-235

## Non-negotiable operating context

You are executing Cycle 013 for the Fiverr Research System. The operator explicitly approved the longer, more detailed Cursor prompt style from Cycle 012, and this cycle must preserve that quality bar. Do not shrink the prompt, do not reduce task detail, and do not treat Jira as an after-the-fact mapping exercise. Planning starts from Jira, acceptance criteria, and Definition of Done. PR #10 is currently open and mergeable, CI is green, and `codecov/project` is green, but three Codex review threads remain unresolved. Those unresolved threads are merge blockers. The attached repo also contains local uncommitted work that must be reconciled rather than silently ignored.

You must not touch `main`. You must not push directly to `main`. While PR #10 remains open, your correction work belongs on `cycle/012/integration` unless the PM explicitly instructs otherwise. A new `cycle/013/integration` branch should only be created after PR #10 is merged into `develop`. Do not mark any product story Done unless full source acceptance criteria and full source Definition of Done are satisfied with evidence. Partial scaffold, placeholder contract, dashboard diagnostics, governance docs, or smoke-only progress can move a story to In Review when supported, but not to Done.

Security rule: the uploaded local repo archive contains a local `.env` file. Do not print, commit, paste, summarize, or expose its contents. Before any push, verify `.env`, `coverage.xml`, local databases, caches, screenshots, and generated runtime artifacts are not staged.

## Mission

Own the board-first AC/DoD ledger and local app-entry follow-up reconciliation. Ensure product stories only advance as far as evidence supports and no Done transitions occur without full source DoD.

## Required task list

### D01 — Open the active Jira ledger before coding

Read `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` and `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_012.md`. Identify all PR #10 touched story keys and their current AC/DoD status. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D02 — Map local uncommitted dashboard changes to exact Jira keys

Map `src/dashboard/app.py`, `src/orchestrator.py`, `tests/unit/test_dashboard.py`, and `tests/unit/test_orchestrator_helpers.py` to exact AC/DoD bullets. Primary key is `SCRUM-228`; related keys include `SCRUM-212`, `SCRUM-213`, `SCRUM-214`, `SCRUM-219`, `SCRUM-225`, `SCRUM-226`, `SCRUM-227`, `SCRUM-231`, and `SCRUM-235`. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D03 — Decide commit versus discard recommendation for local code deltas

Review the uncommitted app-entry diagnostics changes. If they satisfy real `SCRUM-228` AC and tests, recommend committing. If they are incomplete or risky, recommend keeping them out of PR #10 and document why. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D04 — Verify app-entry behavior if committing

If the local code deltas are retained, run targeted tests for dashboard and orchestrator helpers. Expected commands: `python -m pytest -q tests/unit/test_dashboard.py tests/unit/test_orchestrator_helpers.py`, `python -m pytest -q tests/unit/test_cli.py -k dashboard`, `python run.py dashboard --mode local`, and `python run.py phase2-smoke`. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D05 — Handle sandbox dependency failures honestly

If tests cannot run locally due missing dependencies, record the exact error. Do not convert that into a pass. Agent B must rely on live CI after push for final verification. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D06 — Update SCRUM-228 ledger status

For `SCRUM-228`, identify AC bullets advanced by app-entry diagnostics: startup registration, missing config/data safe state, clear diagnostics, and smoke test behavior. Mark remaining DoD bullets clearly. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D07 — Update dashboard story AC/DoD statuses without over-closing

For each dashboard story touched in PR #10, record whether the work is placeholder contract, scaffold, partial implementation, or full source DoD. Most should remain In Progress/In Review, not Done. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D08 — Update integration story ledger entries

For `SCRUM-231` and `SCRUM-235`, record what PR #10 actually advanced: governance/coverage evidence and orchestrator/dashboard stub evidence, not full launch-level pipeline completion. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D09 — Update SCRUM-255 follow-up status

Record whether missing Agent A report was delivered or formally dispositioned by Agent A. If not, keep `SCRUM-255` To Do and block `SCRUM-254` closure. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D10 — Update SCRUM-254 closure criteria

Confirm whether full-board AC/DoD protocol is in PM Pack and committed. If yes, note that governance AC advanced. Do not mark Done if PR #10 Codex blockers or SCRUM-255 remain open. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D11 — Add Jira comments only after evidence exists

Prepare concise Jira comments for touched keys. Each comment must include PR #10, branch, files, validation, AC bullets advanced, AC bullets remaining, and next status recommendation. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D12 — Keep status transitions conservative

Transition a story to In Review only if PR code affecting it is present and validation evidence exists. Do not transition to Done unless all story source AC and DoD are complete. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D13 — Audit Done statuses from recent cycles

Spot-check any recently moved Done issues for signs of premature closure. If a product story is Done based only on duplicate cleanup or placeholder evidence, create a follow-up note or issue. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D14 — Create Cycle 013 board audit addendum

Create `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_013.md` summarizing PR #10 blockers, touched stories, status recommendations, and remaining DoD gaps. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D15 — Update ACTIVE_STORY_DOD_LEDGER

Update `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` with Cycle 013 rows for all touched issues. Include columns for Jira key, status, files, AC advanced, DoD remaining, tests, PR, and next action. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D16 — Check product story completeness against source ToDo

For every touched product story, compare current implementation against source task scope in the Jira description. If child tasks are not created or formally waived, do not close the story. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D17 — Coordinate with Agent A on missing Agent A artifact

Use Agent A’s delivery/disposition of `CYCLE_012_AGENT_A.md` to update SCRUM-255 and the ledger. If Agent A has no evidence, keep the issue open. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D18 — Coordinate with Agent B on PR body Jira table

Give Agent B a final table of Jira status recommendations for the PR body. Include which stories are In Review, which remain In Progress, and why none should be Done unless fully evidenced. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D19 — Coordinate with Agent C on prompt-governance AC

If Agent C fixes prompt validation paths and thresholds, update `SCRUM-254` and `SCRUM-252` evidence as governance AC advanced. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D20 — Verify no-main and no-secret evidence

Confirm the ledger and cycle report state that no `main` push occurred and `.env` was not staged or committed. Include this in Jira comments. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D21 — Commit ledger/report updates if authorized

Recommended commit: `docs(jira): update cycle 013 ac dod ledger [Agent D]`. Stage only docs/jira and Agent D report files unless your task explicitly owns code deltas. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D22 — Create final Agent D report

Create `docs/cycle_reports/CYCLE_013_AGENT_D.md` with board audit results, Jira comments/transitions attempted, files changed, validation, unresolved gaps, and next-cycle recommendations. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D23 — Reject governance-only final response

Ensure final cycle report lists product stories as well as governance keys. If only `SCRUM-256` or `SCRUM-254` is updated, the cycle violates the board-first correction. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

### D24 — Final handoff gate

Before handoff, confirm: active ledger updated, SCRUM-255 status clear, product stories not over-closed, PR #10 blockers represented, and next product work remains selected from Jira AC/DoD. This task must be executed with source traceability. Before changing files, identify the Jira issue keys and acceptance criteria it supports. After changing files, record the exact files touched and the validation performed. If the task reveals a blocker or missing source information, do not guess; write the blocker into the cycle report and coordinate with the responsible agent.

## Required validation block

At the end of your work, report every command you ran and the result. Use the exact command text. If a command cannot run because dependencies are missing locally, say that directly and do not claim success. If you push changes, Agent B must verify live CI and Codecov after the push. Minimum validation expectation for code-affecting work is:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle013.db
python run.py phase2-smoke
```

Documentation-only work should still run the feasible subset and should include path/grep checks proving the Codex complaint is directly resolved.

## Jira update requirements

You may perform Jira operations if assigned and available in your environment. Every Jira update must include: branch, PR number, files changed, validation evidence, AC bullets advanced, DoD bullets remaining, status recommendation, and whether Done is allowed. Do not update only governance tickets if product stories were touched. Product stories touched by this cycle include at least: `SCRUM-212`, `SCRUM-213`, `SCRUM-214`, `SCRUM-215`, `SCRUM-219`, `SCRUM-225`, `SCRUM-226`, `SCRUM-227`, `SCRUM-228`, `SCRUM-231`, and `SCRUM-235`.

## Final response/report requirements

Create your cycle report under `docs/cycle_reports/CYCLE_013_AGENT_D.md`. The report must include: summary, Jira keys, files changed, Codex thread impact, validation commands, local discrepancy handling, no-main confirmation, no-secret confirmation, and unresolved risks. If you did not change code, say so. If you changed docs only, list docs exactly. If you could not complete a task, explain why and identify the blocking issue key.
