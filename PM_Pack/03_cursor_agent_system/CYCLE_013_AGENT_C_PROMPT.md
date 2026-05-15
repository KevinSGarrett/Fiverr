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
