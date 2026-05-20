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
