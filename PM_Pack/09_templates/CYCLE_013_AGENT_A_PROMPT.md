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
