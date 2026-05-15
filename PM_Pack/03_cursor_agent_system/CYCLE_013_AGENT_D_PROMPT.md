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
