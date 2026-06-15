Cycle 078 — Agent F Prompt

## Canonical Secrets Reference
- Master .env: C:\Fiverr\Fiverr\.env
- Runner secrets: C:\AI_Runner\secrets\runner.env
- Required keys: OPENAI_API_KEY, SCRAPFLY_API_KEY, JIRA_API_TOKEN, JIRA_EMAIL, JIRA_BASE_URL, GH_AUTOMATION_TOKEN
- ANTHROPIC_API_KEY must be ABSENT

## Exact Directory Map
- Repo root: C:\Fiverr\Fiverr
- Automation modules: C:\Fiverr\Fiverr\automation\
- Tests: C:\Fiverr\Fiverr\tests\unit\
- PM_Pack root: C:\Fiverr\Fiverr\PM_Pack\
- PM_Pack automation configs: C:\Fiverr\Fiverr\PM_Pack\automation\
- PM_Pack instructions: C:\Fiverr\Fiverr\PM_Pack\01_pm_instructions\
- PM_Pack current state: C:\Fiverr\Fiverr\PM_Pack\02_current_state\
- PM_Pack Cursor agent system: C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\
- PM_Pack cycle log: C:\Fiverr\Fiverr\PM_Pack\10_cycle_log\
- Docs/cycle_reports: C:\Fiverr\Fiverr\docs\cycle_reports\
- Docs/architecture: C:\Fiverr\Fiverr\docs\architecture\
- Docs/runbooks: C:\Fiverr\Fiverr\docs\runbooks\
- Runner root: C:\AI_Runner\
- Runner config: C:\AI_Runner\config\
- Runner state: C:\AI_Runner\state\
- Runner secrets: C:\AI_Runner\secrets\
- Runner logs: C:\AI_Runner\logs\
- Runner reports: C:\AI_Runner\reports\
- Runner scripts: C:\AI_Runner\scripts\
- Runner runs: C:\AI_Runner\runs\
- Runner queue: C:\AI_Runner\queue\
- Runner artifacts: C:\AI_Runner\artifacts\
- GitHub Actions runner: C:\actions-runner\

## PM_Pack Structure
- Post-cycle review prompt: C:\Fiverr\Fiverr\PM_Pack\01_pm_instructions\POST_CYCLE_PM_REVIEW_v4.md
- PM_Pack/ref project plans: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\
- PM_Pack/ref DoD: C:\Fiverr\Fiverr\PM_Pack\ref\dod\
- PM_Pack/ref TODO: C:\Fiverr\Fiverr\PM_Pack\ref\todo\

## Model Verification
- Verify C:\AI_Runner\state\cursor_model_state.json is VERIFIED and unexpired before dispatch.

## Agent Identity and Lane
You are Agent F for Cycle 078 on branch cycle/078/integration.
Lane description: Test coverage gaps, regression tests, coverage enforcement
Your lane owns:
- tests/**
You MUST NOT touch:
- (none explicitly declared)

## Model Policy (MANDATORY)
- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED

## Autonomy rule
- Proceed autonomously through all tasks without pausing for confirmation.
- If blocked, document blocker and continue with next executable task.
- Do not include git add/commit/push instructions in this prompt.

## Jira Scope
- SCRUM-230: [DASHBOARD] S9.16 Pricing Dashboard Widgets
  - AC: Story Implement S9.16 — Pricing Dashboard Widgets. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-
  - DoD: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- SCRUM-255: [CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff
  - AC: Created by Cycle 012 Agent D during final integration board audit. Missing AC/DoD coverage discovered: Expected artifact docs/cycle_reports/CYCLE_012_AGENT_A.md is absent from branch evidence. Governa
  - DoD: 
- SCRUM-261: [CYCLE 017] Enforce repo-root branch/worktree controls and continue product inte
  - AC: Purpose Cycle 017 continues product-forward development while permanently hardening PM Pack and Cursor prompt rules against the branch, GitHub, shell, worktree, and directory issues observed during Cy
  - DoD: 
- SCRUM-281: [MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline
  - AC: Medium Gap — M11\n\nCI pipeline runs Ruff (lint), Mypy (types), Pytest (tests), Codecov. Missing security scanning steps:\n\n- Bandit — Python security linter (finds SQL injection, hardcoded secrets, 
  - DoD: 
- SCRUM-439: [CYCLE 019] Merge PR #15 and advance validation closure while fixing PM Pack art
  - AC: Purpose Cycle 019 continues from uploaded Fiverr_018(1).zip and PM_Pack_018(1).zip . PM reviewed the local repository archive, local PM Pack, live GitHub PR #15, Codex review state, CI/Codecov state, 
  - DoD: 
- SCRUM-445: [W19][1.1.3] Create requirements.txt with pinned versions
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.3
Task: Create requirements.txt with pinned versions

This sub-task makes the E01 task-level work tr
  - DoD: 
- SCRUM-451: [W19][1.2.2] Create ConfigLoader class
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.2
Task: Create ConfigLoader class

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-457: [W19][1.3.1] Create database engine setup
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.1
Task: Create database engine setup

This sub-task makes the E01 task-level work trackable in Jira
  - DoD: 
- SCRUM-463: [W19][1.3.7] Create Seller model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.7
Task: Create Seller model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-469: [W19][1.3.13] Create ClusterAnalysis model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.13
Task: Create ClusterAnalysis model

This sub-task makes the E01 task-level work trackable in Jir
  - DoD: 
- SCRUM-475: [W19][1.3.19] Create RunLog model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.19
Task: Create RunLog model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-481: [W19][1.3.25] Create DiscoveryCycleLog model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.25
Task: Create DiscoveryCycleLog model

This sub-task makes the E01 task-level work trackable in J
  - DoD: 
- SCRUM-487: [W19][1.4.1] Create run.py CLI
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.1
Task: Create run.py CLI

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-493: [W19][1.4.7] Create CLI unit tests
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.7
Task: Create CLI unit tests

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-499: [W19][1.5.6] Create Jinja2 template renderer
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.6
Task: Create Jinja2 template renderer

This sub-task makes the E01 task-level work trackable in J
  - DoD: 
- SCRUM-505: [W19][1.7.1] Create seed keyword YAML files
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-140
Task ID: 1.7.1
Task: Create seed keyword YAML files

This sub-task makes the E01 task-level work trackable in Ji
  - DoD: 

## Tasks
### TASK 01 — Agent F setup/verify for SCRUM-230: [DASHBOARD] S9.16 Pricing Dashboard Widgets
- Story: SCRUM-230
- AC Focus: Story Implement S9.16 — Pricing Dashboard Widgets. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.16.1–9.16.4 covering pricing widgets, price ladder display, distribution charts, and tests. Acceptance Criteria Pricing widgets display price analysis, ladders, market positioning, and related confidence context. Widgets handle sparse or missing pricing data gracefully. Child tasks are created in later native task import waves or formally waived. Dashboard smoke tests validate pricing widget rendering and data access. DoD Complete when pricing widgets satisfy source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-16-pricing-widgets
PR: feat(dashboard): S9.16 Pricing Dashboard Widgets Suggested Metadata Labels: wave-19, story, dashboard, pricing-widgets, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- DoD Catalog Context: EPIC_09: [ ] Design tokens defined (colours, typography, spacing)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 02 — Agent F read project plan for SCRUM-255: [CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff
- Story: SCRUM-255
- AC Focus: Created by Cycle 012 Agent D during final integration board audit. Missing AC/DoD coverage discovered: Expected artifact docs/cycle_reports/CYCLE_012_AGENT_A.md is absent from branch evidence. Governance issue SCRUM-254 cannot be closed until missing Agent A report evidence is either delivered or formally dispositioned. Product stories in the Cycle 012 touched set remain In Progress/In Review without full source DoD closure evidence. Required follow-up: Deliver or disposition missing Agent A report. Re-run board-wide AC/DoD closure review for touched keys. Transition only issues with full source DoD evidence; keep others non-Done. Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with closure decisions and evidence links.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 03 — Agent F implement AC for SCRUM-261: [CYCLE 017] Enforce repo-root branch/worktree controls and continue pr
- Story: SCRUM-261
- AC Focus: Purpose Cycle 017 continues product-forward development while permanently hardening PM Pack and Cursor prompt rules against the branch, GitHub, shell, worktree, and directory issues observed during Cycle 016. The operator specifically requested prevention of agents creating or using random directories instead of the canonical repo root C:\Fiverr\Fiverr . Required Guardrail Updates Add a canonical execution-root lock: every Cursor agent must work from C:\Fiverr\Fiverr by default. Require start-of-run preflight commands: Get-Location , git rev-parse --show-toplevel , git branch --show-current , git status --short --branch , and git worktree list . Abort if the Git top-level is not exactly C:\Fiverr\Fiverr unless the operator explicitly authorizes an alternate worktree in the current cycle. Ban default worktree creation and use. Worktrees require explicit operator approval, documented reason, exact path, branch binding, and cleanup/restore plan. Standardize all Windows runbook commands to PowerShell syntax; do not use Bash-only && , heredocs, or unquoted stash@{0} patterns. Before branch switching, require dirty-tree, untracked-collision, and worktree-binding checks. Require a final evidence freeze after the last push: final head SHA, PR URL, mergeability, exact check names/statuses, Codex thread status, Jira update status, and no-main confirmation must be synchronized in reports, ledger, and PR body. Product Focus After Guardrails After the short PR #13 merge gate, Cycle 017 should create cycle/017/integration from updated develop and continue actual Fiverr product development. Priority product scope: SCRUM-231, SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-237, SCRUM-239, SCRUM-240, SCRUM-241, and related dashboard/runtime closure stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228. Acceptance Criteria PM Pack contains permanent execution-root, worktree, branch safety, PowerShell, and final-evidence-freeze protocols. Cycle 017 prompts include these guardrails in the first instructions block for every agent. Prompt quality audit passes: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PR #13 is merged only if still green, mergeable, and Codex-resolved. Product work advances runtime dashboard/integration validation rather than becoming a process-only cycle. All touched Jira stories receive AC/DoD progress comments and remain non-Done unless full source DoD is satisfied.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 04 — Agent F validation for SCRUM-281: [MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline
- Story: SCRUM-281
- AC Focus: Medium Gap — M11\n\nCI pipeline runs Ruff (lint), Mypy (types), Pytest (tests), Codecov. Missing security scanning steps:\n\n- Bandit — Python security linter (finds SQL injection, hardcoded secrets, etc.)\n- Safety / pip-audit — CVE checker for installed Python packages\n- Secret scanning — TruffleHog or GitLeaks to prevent credential commits\n\nSCRUM-75 (security controls) implies these should exist.\n\n## Acceptance Criteria\n\n- [ ] Bandit added to CI with bandit -r src/ -ll (low-level threshold)\n- [ ] pip-audit or safety check added to CI\n- [ ] Secret scanning step added (TruffleHog or GitLeaks action)\n- [ ] CI fails if any HIGH severity Bandit finding exists\n- [ ] CI fails if any known CVE in current deps\n- [ ] Steps added to .github/workflows/ci.yml \n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M11\n* Related: SCRUM-75 (Credential/secrets/incident-response controls)
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 05 — Agent F cleanup for SCRUM-439: [CYCLE 019] Merge PR #15 and advance validation closure while fixing P
- Story: SCRUM-439
- AC Focus: Purpose Cycle 019 continues from uploaded Fiverr_018(1).zip and PM_Pack_018(1).zip . PM reviewed the local repository archive, local PM Pack, live GitHub PR #15, Codex review state, CI/Codecov state, and active Jira board scope. Cycle 019 should begin with a short PR #15 merge gate, then continue product-forward integration validation and closure work while fixing the PM Pack artifact-hygiene gaps found in the uploaded repo/pack. Local Repository Findings Active branch in uploaded repo: cycle/018/integration . Git status is clean for tracked source files but includes untracked PM_Pack/ cycle files in the repo archive. .env exists in the uploaded repo archive. It must never be read, printed, committed, copied into artifacts, or exposed. Cycle 018 branch contains 14 commits over origin/develop and 27 changed files. Cycle 018 changed areas include analysis closure readiness, dashboard runtime acceptance, dashboard query contracts, report reconciliation helpers, preflight/root guardrails, Jira ledgers, and PR template/freeze controls. Agent reports are present for Agent A, B, C, and D under docs/cycle_reports/ . PM Pack Findings Uploaded PM Pack contains PM_CORRECTIVE_RULES_CYCLE_018.md , board audit files, and Cycle 018 prompt files. Uploaded PM Pack is missing several protocol files that should be permanent after the prior root/worktree failures: 02_cycle_protocol/RUN_PREFLIGHT_POWERSHELL.md 05_github_protocol/EXECUTION_ROOT_AND_WORKTREE_LOCK.md 05_github_protocol/POWERSHELL_ONLY_COMMAND_POLICY.md 06_review_and_qa/FINAL_EVIDENCE_FREEZE_PROTOCOL.md 06_review_and_qa/GENERATED_PROMPT_QUALITY_AUDIT.md Agent A Cycle 018 prompt in the uploaded PM Pack is below the 6,000-word floor and must not be used as the Cycle 019 quality baseline. Live GitHub Findings PR #15: cycle018: finalize agent d board reconciliation and freeze controls . Source branch: cycle/018/integration . Target branch: develop . Status at PM review time: open, mergeable, not draft. Head SHA at review time: 4ba703210b619ca6c28165e77321341b1f7fcb66 . Codex review threads: two findings existed; both are replied to and resolved. CI workflow status: successful. Visible workflow jobs: Lint, Typecheck, Tests, and Gates and codecov/project , both successful. PR body mentions codecov/patch , but the visible workflow job list did not show a separate codecov/patch job; Cycle 019 steward must verify whether patch coverage is an external Codecov status, missing from the workflow job list, or needs restoration. Jira Board Findings Analysis stories SCRUM-157 through SCRUM-164 are In Review and need closure evidence before any Done transitions. Dashboard/runtime stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, SCRUM-228, and SCRUM-231 are In Review and should remain non-Done until full runtime/production acceptance evidence exists. SCRUM-213 remains In Progress. SCRUM-216, SCRUM-218, SCRUM-220, and SCRUM-223 remain To Do and should not be silently treated as completed by adjacent dashboard work. Integration stories SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-239, SCRUM-240, SCRUM-241, and SCRUM-242 remain To Do unless Cycle 019 agents touch them and add AC/DoD progress evidence. SCRUM-250 remains In Review; SCRUM-254 remains In Progress; SCRUM-257 remains To Do; SCRUM-262 remains In Progress pending PR #15 merge. Cycle 019 Product Focus After PR #15 is merged into develop , create cycle/019/integration from updated develop and advance product work from Jira AC/DoD stories. Priority scope: SCRUM-232 — Data Integrity Validation SCRUM-233 — Performance Testing SCRUM-234 — Resilience Testing SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-239 — First Run Validation SCRUM-240 — Full 9-Niche Validation Run readiness SCRUM-241 — Security and Data Hygiene SCRUM-242 — Launch Readiness Checklist preparation SCRUM-157 through SCRUM-164 — Analysis closure evidence SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228, SCRUM-231 — Dashboard/runtime and integration closure evidence SCRUM-257 — Duplicate/premature Done-risk audit for SCRUM-217, SCRUM-221, and SCRUM-222, without derailing product work Required Guardrails Work only from C:\Fiverr\Fiverr unless Kevin explicitly authorizes an alternate path in-thread. No random directories, copied repos, or unapproved worktrees. PowerShell-only operational commands. Do not read, print, stage, commit, or expose .env . Same-cycle Codex review handling is mandatory. Final evidence freeze after the last push/checks settle is mandatory. Cursor prompt quality audit must pass before PM handoff: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PM Pack permanent protocol files must be restored into the generated PM Pack artifact. Acceptance Criteria PR #15 is merged only if still green, mergeable, and Codex-resolved. Cycle 019 branch starts from updated develop after PR #15 merge, or branch creation is blocked with evidence. Product work advances integration validation/runtime closure rather than process-only cleanup. PM Pack artifact hygiene is corrected and untracked repo PM Pack files are either committed intentionally or removed from the working tree before PR handoff. .env remains untouched and excluded from artifacts/repo changes. Touched Jira stories receive AC/DoD progress comments and are not marked Done unless full source DoD is satisfied. Codecov project and patch expectations are verified or restored. Prompt quality audit passes for all agents. Updated PM Pack zip, PM response, and prompt-only backup are generated and verified.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 06 — Agent F setup/verify for SCRUM-445: [W19][1.1.3] Create requirements.txt with pinned versions
- Story: SCRUM-445
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.3
Task: Create requirements.txt with pinned versions

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 07 — Agent F read project plan for SCRUM-451: [W19][1.2.2] Create ConfigLoader class
- Story: SCRUM-451
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.2
Task: Create ConfigLoader class

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 08 — Agent F implement AC for SCRUM-457: [W19][1.3.1] Create database engine setup
- Story: SCRUM-457
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.1
Task: Create database engine setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 09 — Agent F validation for SCRUM-463: [W19][1.3.7] Create Seller model
- Story: SCRUM-463
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.7
Task: Create Seller model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 10 — Agent F cleanup for SCRUM-469: [W19][1.3.13] Create ClusterAnalysis model
- Story: SCRUM-469
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.13
Task: Create ClusterAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 11 — Agent F setup/verify for SCRUM-475: [W19][1.3.19] Create RunLog model
- Story: SCRUM-475
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.19
Task: Create RunLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 12 — Agent F read project plan for SCRUM-481: [W19][1.3.25] Create DiscoveryCycleLog model
- Story: SCRUM-481
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.25
Task: Create DiscoveryCycleLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 13 — Agent F implement AC for SCRUM-487: [W19][1.4.1] Create run.py CLI
- Story: SCRUM-487
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.1
Task: Create run.py CLI

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 14 — Agent F validation for SCRUM-493: [W19][1.4.7] Create CLI unit tests
- Story: SCRUM-493
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.7
Task: Create CLI unit tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 15 — Agent F cleanup for SCRUM-499: [W19][1.5.6] Create Jinja2 template renderer
- Story: SCRUM-499
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.6
Task: Create Jinja2 template renderer

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 16 — Agent F setup/verify for SCRUM-505: [W19][1.7.1] Create seed keyword YAML files
- Story: SCRUM-505
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-140
Task ID: 1.7.1
Task: Create seed keyword YAML files

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 17 — Agent F read project plan for SCRUM-230: [DASHBOARD] S9.16 Pricing Dashboard Widgets
- Story: SCRUM-230
- AC Focus: Story Implement S9.16 — Pricing Dashboard Widgets. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.16.1–9.16.4 covering pricing widgets, price ladder display, distribution charts, and tests. Acceptance Criteria Pricing widgets display price analysis, ladders, market positioning, and related confidence context. Widgets handle sparse or missing pricing data gracefully. Child tasks are created in later native task import waves or formally waived. Dashboard smoke tests validate pricing widget rendering and data access. DoD Complete when pricing widgets satisfy source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-16-pricing-widgets
PR: feat(dashboard): S9.16 Pricing Dashboard Widgets Suggested Metadata Labels: wave-19, story, dashboard, pricing-widgets, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- DoD Catalog Context: EPIC_09: [ ] Design tokens defined (colours, typography, spacing)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 18 — Agent F implement AC for SCRUM-255: [CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff
- Story: SCRUM-255
- AC Focus: Created by Cycle 012 Agent D during final integration board audit. Missing AC/DoD coverage discovered: Expected artifact docs/cycle_reports/CYCLE_012_AGENT_A.md is absent from branch evidence. Governance issue SCRUM-254 cannot be closed until missing Agent A report evidence is either delivered or formally dispositioned. Product stories in the Cycle 012 touched set remain In Progress/In Review without full source DoD closure evidence. Required follow-up: Deliver or disposition missing Agent A report. Re-run board-wide AC/DoD closure review for touched keys. Transition only issues with full source DoD evidence; keep others non-Done. Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with closure decisions and evidence links.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 19 — Agent F validation for SCRUM-261: [CYCLE 017] Enforce repo-root branch/worktree controls and continue pr
- Story: SCRUM-261
- AC Focus: Purpose Cycle 017 continues product-forward development while permanently hardening PM Pack and Cursor prompt rules against the branch, GitHub, shell, worktree, and directory issues observed during Cycle 016. The operator specifically requested prevention of agents creating or using random directories instead of the canonical repo root C:\Fiverr\Fiverr . Required Guardrail Updates Add a canonical execution-root lock: every Cursor agent must work from C:\Fiverr\Fiverr by default. Require start-of-run preflight commands: Get-Location , git rev-parse --show-toplevel , git branch --show-current , git status --short --branch , and git worktree list . Abort if the Git top-level is not exactly C:\Fiverr\Fiverr unless the operator explicitly authorizes an alternate worktree in the current cycle. Ban default worktree creation and use. Worktrees require explicit operator approval, documented reason, exact path, branch binding, and cleanup/restore plan. Standardize all Windows runbook commands to PowerShell syntax; do not use Bash-only && , heredocs, or unquoted stash@{0} patterns. Before branch switching, require dirty-tree, untracked-collision, and worktree-binding checks. Require a final evidence freeze after the last push: final head SHA, PR URL, mergeability, exact check names/statuses, Codex thread status, Jira update status, and no-main confirmation must be synchronized in reports, ledger, and PR body. Product Focus After Guardrails After the short PR #13 merge gate, Cycle 017 should create cycle/017/integration from updated develop and continue actual Fiverr product development. Priority product scope: SCRUM-231, SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-237, SCRUM-239, SCRUM-240, SCRUM-241, and related dashboard/runtime closure stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228. Acceptance Criteria PM Pack contains permanent execution-root, worktree, branch safety, PowerShell, and final-evidence-freeze protocols. Cycle 017 prompts include these guardrails in the first instructions block for every agent. Prompt quality audit passes: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PR #13 is merged only if still green, mergeable, and Codex-resolved. Product work advances runtime dashboard/integration validation rather than becoming a process-only cycle. All touched Jira stories receive AC/DoD progress comments and remain non-Done unless full source DoD is satisfied.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 20 — Agent F cleanup for SCRUM-281: [MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline
- Story: SCRUM-281
- AC Focus: Medium Gap — M11\n\nCI pipeline runs Ruff (lint), Mypy (types), Pytest (tests), Codecov. Missing security scanning steps:\n\n- Bandit — Python security linter (finds SQL injection, hardcoded secrets, etc.)\n- Safety / pip-audit — CVE checker for installed Python packages\n- Secret scanning — TruffleHog or GitLeaks to prevent credential commits\n\nSCRUM-75 (security controls) implies these should exist.\n\n## Acceptance Criteria\n\n- [ ] Bandit added to CI with bandit -r src/ -ll (low-level threshold)\n- [ ] pip-audit or safety check added to CI\n- [ ] Secret scanning step added (TruffleHog or GitLeaks action)\n- [ ] CI fails if any HIGH severity Bandit finding exists\n- [ ] CI fails if any known CVE in current deps\n- [ ] Steps added to .github/workflows/ci.yml \n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M11\n* Related: SCRUM-75 (Credential/secrets/incident-response controls)
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 21 — Agent F setup/verify for SCRUM-439: [CYCLE 019] Merge PR #15 and advance validation closure while fixing P
- Story: SCRUM-439
- AC Focus: Purpose Cycle 019 continues from uploaded Fiverr_018(1).zip and PM_Pack_018(1).zip . PM reviewed the local repository archive, local PM Pack, live GitHub PR #15, Codex review state, CI/Codecov state, and active Jira board scope. Cycle 019 should begin with a short PR #15 merge gate, then continue product-forward integration validation and closure work while fixing the PM Pack artifact-hygiene gaps found in the uploaded repo/pack. Local Repository Findings Active branch in uploaded repo: cycle/018/integration . Git status is clean for tracked source files but includes untracked PM_Pack/ cycle files in the repo archive. .env exists in the uploaded repo archive. It must never be read, printed, committed, copied into artifacts, or exposed. Cycle 018 branch contains 14 commits over origin/develop and 27 changed files. Cycle 018 changed areas include analysis closure readiness, dashboard runtime acceptance, dashboard query contracts, report reconciliation helpers, preflight/root guardrails, Jira ledgers, and PR template/freeze controls. Agent reports are present for Agent A, B, C, and D under docs/cycle_reports/ . PM Pack Findings Uploaded PM Pack contains PM_CORRECTIVE_RULES_CYCLE_018.md , board audit files, and Cycle 018 prompt files. Uploaded PM Pack is missing several protocol files that should be permanent after the prior root/worktree failures: 02_cycle_protocol/RUN_PREFLIGHT_POWERSHELL.md 05_github_protocol/EXECUTION_ROOT_AND_WORKTREE_LOCK.md 05_github_protocol/POWERSHELL_ONLY_COMMAND_POLICY.md 06_review_and_qa/FINAL_EVIDENCE_FREEZE_PROTOCOL.md 06_review_and_qa/GENERATED_PROMPT_QUALITY_AUDIT.md Agent A Cycle 018 prompt in the uploaded PM Pack is below the 6,000-word floor and must not be used as the Cycle 019 quality baseline. Live GitHub Findings PR #15: cycle018: finalize agent d board reconciliation and freeze controls . Source branch: cycle/018/integration . Target branch: develop . Status at PM review time: open, mergeable, not draft. Head SHA at review time: 4ba703210b619ca6c28165e77321341b1f7fcb66 . Codex review threads: two findings existed; both are replied to and resolved. CI workflow status: successful. Visible workflow jobs: Lint, Typecheck, Tests, and Gates and codecov/project , both successful. PR body mentions codecov/patch , but the visible workflow job list did not show a separate codecov/patch job; Cycle 019 steward must verify whether patch coverage is an external Codecov status, missing from the workflow job list, or needs restoration. Jira Board Findings Analysis stories SCRUM-157 through SCRUM-164 are In Review and need closure evidence before any Done transitions. Dashboard/runtime stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, SCRUM-228, and SCRUM-231 are In Review and should remain non-Done until full runtime/production acceptance evidence exists. SCRUM-213 remains In Progress. SCRUM-216, SCRUM-218, SCRUM-220, and SCRUM-223 remain To Do and should not be silently treated as completed by adjacent dashboard work. Integration stories SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-239, SCRUM-240, SCRUM-241, and SCRUM-242 remain To Do unless Cycle 019 agents touch them and add AC/DoD progress evidence. SCRUM-250 remains In Review; SCRUM-254 remains In Progress; SCRUM-257 remains To Do; SCRUM-262 remains In Progress pending PR #15 merge. Cycle 019 Product Focus After PR #15 is merged into develop , create cycle/019/integration from updated develop and advance product work from Jira AC/DoD stories. Priority scope: SCRUM-232 — Data Integrity Validation SCRUM-233 — Performance Testing SCRUM-234 — Resilience Testing SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-239 — First Run Validation SCRUM-240 — Full 9-Niche Validation Run readiness SCRUM-241 — Security and Data Hygiene SCRUM-242 — Launch Readiness Checklist preparation SCRUM-157 through SCRUM-164 — Analysis closure evidence SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228, SCRUM-231 — Dashboard/runtime and integration closure evidence SCRUM-257 — Duplicate/premature Done-risk audit for SCRUM-217, SCRUM-221, and SCRUM-222, without derailing product work Required Guardrails Work only from C:\Fiverr\Fiverr unless Kevin explicitly authorizes an alternate path in-thread. No random directories, copied repos, or unapproved worktrees. PowerShell-only operational commands. Do not read, print, stage, commit, or expose .env . Same-cycle Codex review handling is mandatory. Final evidence freeze after the last push/checks settle is mandatory. Cursor prompt quality audit must pass before PM handoff: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PM Pack permanent protocol files must be restored into the generated PM Pack artifact. Acceptance Criteria PR #15 is merged only if still green, mergeable, and Codex-resolved. Cycle 019 branch starts from updated develop after PR #15 merge, or branch creation is blocked with evidence. Product work advances integration validation/runtime closure rather than process-only cleanup. PM Pack artifact hygiene is corrected and untracked repo PM Pack files are either committed intentionally or removed from the working tree before PR handoff. .env remains untouched and excluded from artifacts/repo changes. Touched Jira stories receive AC/DoD progress comments and are not marked Done unless full source DoD is satisfied. Codecov project and patch expectations are verified or restored. Prompt quality audit passes for all agents. Updated PM Pack zip, PM response, and prompt-only backup are generated and verified.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 22 — Agent F read project plan for SCRUM-445: [W19][1.1.3] Create requirements.txt with pinned versions
- Story: SCRUM-445
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.3
Task: Create requirements.txt with pinned versions

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 23 — Agent F implement AC for SCRUM-451: [W19][1.2.2] Create ConfigLoader class
- Story: SCRUM-451
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.2
Task: Create ConfigLoader class

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 24 — Agent F validation for SCRUM-457: [W19][1.3.1] Create database engine setup
- Story: SCRUM-457
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.1
Task: Create database engine setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 25 — Agent F cleanup for SCRUM-463: [W19][1.3.7] Create Seller model
- Story: SCRUM-463
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.7
Task: Create Seller model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 26 — Agent F setup/verify for SCRUM-469: [W19][1.3.13] Create ClusterAnalysis model
- Story: SCRUM-469
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.13
Task: Create ClusterAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 27 — Agent F read project plan for SCRUM-475: [W19][1.3.19] Create RunLog model
- Story: SCRUM-475
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.19
Task: Create RunLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 28 — Agent F implement AC for SCRUM-481: [W19][1.3.25] Create DiscoveryCycleLog model
- Story: SCRUM-481
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.25
Task: Create DiscoveryCycleLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 29 — Agent F validation for SCRUM-487: [W19][1.4.1] Create run.py CLI
- Story: SCRUM-487
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.1
Task: Create run.py CLI

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 30 — Agent F cleanup for SCRUM-493: [W19][1.4.7] Create CLI unit tests
- Story: SCRUM-493
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.7
Task: Create CLI unit tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 31 — Agent F setup/verify for SCRUM-499: [W19][1.5.6] Create Jinja2 template renderer
- Story: SCRUM-499
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.6
Task: Create Jinja2 template renderer

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 32 — Agent F read project plan for SCRUM-505: [W19][1.7.1] Create seed keyword YAML files
- Story: SCRUM-505
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-140
Task ID: 1.7.1
Task: Create seed keyword YAML files

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 33 — Agent F implement AC for SCRUM-230: [DASHBOARD] S9.16 Pricing Dashboard Widgets
- Story: SCRUM-230
- AC Focus: Story Implement S9.16 — Pricing Dashboard Widgets. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.16.1–9.16.4 covering pricing widgets, price ladder display, distribution charts, and tests. Acceptance Criteria Pricing widgets display price analysis, ladders, market positioning, and related confidence context. Widgets handle sparse or missing pricing data gracefully. Child tasks are created in later native task import waves or formally waived. Dashboard smoke tests validate pricing widget rendering and data access. DoD Complete when pricing widgets satisfy source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-16-pricing-widgets
PR: feat(dashboard): S9.16 Pricing Dashboard Widgets Suggested Metadata Labels: wave-19, story, dashboard, pricing-widgets, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- DoD Catalog Context: EPIC_09: [ ] Design tokens defined (colours, typography, spacing)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 34 — Agent F validation for SCRUM-255: [CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff
- Story: SCRUM-255
- AC Focus: Created by Cycle 012 Agent D during final integration board audit. Missing AC/DoD coverage discovered: Expected artifact docs/cycle_reports/CYCLE_012_AGENT_A.md is absent from branch evidence. Governance issue SCRUM-254 cannot be closed until missing Agent A report evidence is either delivered or formally dispositioned. Product stories in the Cycle 012 touched set remain In Progress/In Review without full source DoD closure evidence. Required follow-up: Deliver or disposition missing Agent A report. Re-run board-wide AC/DoD closure review for touched keys. Transition only issues with full source DoD evidence; keep others non-Done. Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with closure decisions and evidence links.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 35 — Agent F cleanup for SCRUM-261: [CYCLE 017] Enforce repo-root branch/worktree controls and continue pr
- Story: SCRUM-261
- AC Focus: Purpose Cycle 017 continues product-forward development while permanently hardening PM Pack and Cursor prompt rules against the branch, GitHub, shell, worktree, and directory issues observed during Cycle 016. The operator specifically requested prevention of agents creating or using random directories instead of the canonical repo root C:\Fiverr\Fiverr . Required Guardrail Updates Add a canonical execution-root lock: every Cursor agent must work from C:\Fiverr\Fiverr by default. Require start-of-run preflight commands: Get-Location , git rev-parse --show-toplevel , git branch --show-current , git status --short --branch , and git worktree list . Abort if the Git top-level is not exactly C:\Fiverr\Fiverr unless the operator explicitly authorizes an alternate worktree in the current cycle. Ban default worktree creation and use. Worktrees require explicit operator approval, documented reason, exact path, branch binding, and cleanup/restore plan. Standardize all Windows runbook commands to PowerShell syntax; do not use Bash-only && , heredocs, or unquoted stash@{0} patterns. Before branch switching, require dirty-tree, untracked-collision, and worktree-binding checks. Require a final evidence freeze after the last push: final head SHA, PR URL, mergeability, exact check names/statuses, Codex thread status, Jira update status, and no-main confirmation must be synchronized in reports, ledger, and PR body. Product Focus After Guardrails After the short PR #13 merge gate, Cycle 017 should create cycle/017/integration from updated develop and continue actual Fiverr product development. Priority product scope: SCRUM-231, SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-237, SCRUM-239, SCRUM-240, SCRUM-241, and related dashboard/runtime closure stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228. Acceptance Criteria PM Pack contains permanent execution-root, worktree, branch safety, PowerShell, and final-evidence-freeze protocols. Cycle 017 prompts include these guardrails in the first instructions block for every agent. Prompt quality audit passes: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PR #13 is merged only if still green, mergeable, and Codex-resolved. Product work advances runtime dashboard/integration validation rather than becoming a process-only cycle. All touched Jira stories receive AC/DoD progress comments and remain non-Done unless full source DoD is satisfied.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 36 — Agent F setup/verify for SCRUM-281: [MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline
- Story: SCRUM-281
- AC Focus: Medium Gap — M11\n\nCI pipeline runs Ruff (lint), Mypy (types), Pytest (tests), Codecov. Missing security scanning steps:\n\n- Bandit — Python security linter (finds SQL injection, hardcoded secrets, etc.)\n- Safety / pip-audit — CVE checker for installed Python packages\n- Secret scanning — TruffleHog or GitLeaks to prevent credential commits\n\nSCRUM-75 (security controls) implies these should exist.\n\n## Acceptance Criteria\n\n- [ ] Bandit added to CI with bandit -r src/ -ll (low-level threshold)\n- [ ] pip-audit or safety check added to CI\n- [ ] Secret scanning step added (TruffleHog or GitLeaks action)\n- [ ] CI fails if any HIGH severity Bandit finding exists\n- [ ] CI fails if any known CVE in current deps\n- [ ] Steps added to .github/workflows/ci.yml \n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M11\n* Related: SCRUM-75 (Credential/secrets/incident-response controls)
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 37 — Agent F read project plan for SCRUM-439: [CYCLE 019] Merge PR #15 and advance validation closure while fixing P
- Story: SCRUM-439
- AC Focus: Purpose Cycle 019 continues from uploaded Fiverr_018(1).zip and PM_Pack_018(1).zip . PM reviewed the local repository archive, local PM Pack, live GitHub PR #15, Codex review state, CI/Codecov state, and active Jira board scope. Cycle 019 should begin with a short PR #15 merge gate, then continue product-forward integration validation and closure work while fixing the PM Pack artifact-hygiene gaps found in the uploaded repo/pack. Local Repository Findings Active branch in uploaded repo: cycle/018/integration . Git status is clean for tracked source files but includes untracked PM_Pack/ cycle files in the repo archive. .env exists in the uploaded repo archive. It must never be read, printed, committed, copied into artifacts, or exposed. Cycle 018 branch contains 14 commits over origin/develop and 27 changed files. Cycle 018 changed areas include analysis closure readiness, dashboard runtime acceptance, dashboard query contracts, report reconciliation helpers, preflight/root guardrails, Jira ledgers, and PR template/freeze controls. Agent reports are present for Agent A, B, C, and D under docs/cycle_reports/ . PM Pack Findings Uploaded PM Pack contains PM_CORRECTIVE_RULES_CYCLE_018.md , board audit files, and Cycle 018 prompt files. Uploaded PM Pack is missing several protocol files that should be permanent after the prior root/worktree failures: 02_cycle_protocol/RUN_PREFLIGHT_POWERSHELL.md 05_github_protocol/EXECUTION_ROOT_AND_WORKTREE_LOCK.md 05_github_protocol/POWERSHELL_ONLY_COMMAND_POLICY.md 06_review_and_qa/FINAL_EVIDENCE_FREEZE_PROTOCOL.md 06_review_and_qa/GENERATED_PROMPT_QUALITY_AUDIT.md Agent A Cycle 018 prompt in the uploaded PM Pack is below the 6,000-word floor and must not be used as the Cycle 019 quality baseline. Live GitHub Findings PR #15: cycle018: finalize agent d board reconciliation and freeze controls . Source branch: cycle/018/integration . Target branch: develop . Status at PM review time: open, mergeable, not draft. Head SHA at review time: 4ba703210b619ca6c28165e77321341b1f7fcb66 . Codex review threads: two findings existed; both are replied to and resolved. CI workflow status: successful. Visible workflow jobs: Lint, Typecheck, Tests, and Gates and codecov/project , both successful. PR body mentions codecov/patch , but the visible workflow job list did not show a separate codecov/patch job; Cycle 019 steward must verify whether patch coverage is an external Codecov status, missing from the workflow job list, or needs restoration. Jira Board Findings Analysis stories SCRUM-157 through SCRUM-164 are In Review and need closure evidence before any Done transitions. Dashboard/runtime stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, SCRUM-228, and SCRUM-231 are In Review and should remain non-Done until full runtime/production acceptance evidence exists. SCRUM-213 remains In Progress. SCRUM-216, SCRUM-218, SCRUM-220, and SCRUM-223 remain To Do and should not be silently treated as completed by adjacent dashboard work. Integration stories SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-239, SCRUM-240, SCRUM-241, and SCRUM-242 remain To Do unless Cycle 019 agents touch them and add AC/DoD progress evidence. SCRUM-250 remains In Review; SCRUM-254 remains In Progress; SCRUM-257 remains To Do; SCRUM-262 remains In Progress pending PR #15 merge. Cycle 019 Product Focus After PR #15 is merged into develop , create cycle/019/integration from updated develop and advance product work from Jira AC/DoD stories. Priority scope: SCRUM-232 — Data Integrity Validation SCRUM-233 — Performance Testing SCRUM-234 — Resilience Testing SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-239 — First Run Validation SCRUM-240 — Full 9-Niche Validation Run readiness SCRUM-241 — Security and Data Hygiene SCRUM-242 — Launch Readiness Checklist preparation SCRUM-157 through SCRUM-164 — Analysis closure evidence SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228, SCRUM-231 — Dashboard/runtime and integration closure evidence SCRUM-257 — Duplicate/premature Done-risk audit for SCRUM-217, SCRUM-221, and SCRUM-222, without derailing product work Required Guardrails Work only from C:\Fiverr\Fiverr unless Kevin explicitly authorizes an alternate path in-thread. No random directories, copied repos, or unapproved worktrees. PowerShell-only operational commands. Do not read, print, stage, commit, or expose .env . Same-cycle Codex review handling is mandatory. Final evidence freeze after the last push/checks settle is mandatory. Cursor prompt quality audit must pass before PM handoff: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PM Pack permanent protocol files must be restored into the generated PM Pack artifact. Acceptance Criteria PR #15 is merged only if still green, mergeable, and Codex-resolved. Cycle 019 branch starts from updated develop after PR #15 merge, or branch creation is blocked with evidence. Product work advances integration validation/runtime closure rather than process-only cleanup. PM Pack artifact hygiene is corrected and untracked repo PM Pack files are either committed intentionally or removed from the working tree before PR handoff. .env remains untouched and excluded from artifacts/repo changes. Touched Jira stories receive AC/DoD progress comments and are not marked Done unless full source DoD is satisfied. Codecov project and patch expectations are verified or restored. Prompt quality audit passes for all agents. Updated PM Pack zip, PM response, and prompt-only backup are generated and verified.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 38 — Agent F implement AC for SCRUM-445: [W19][1.1.3] Create requirements.txt with pinned versions
- Story: SCRUM-445
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.3
Task: Create requirements.txt with pinned versions

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 39 — Agent F validation for SCRUM-451: [W19][1.2.2] Create ConfigLoader class
- Story: SCRUM-451
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.2
Task: Create ConfigLoader class

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 40 — Agent F cleanup for SCRUM-457: [W19][1.3.1] Create database engine setup
- Story: SCRUM-457
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.1
Task: Create database engine setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 41 — Agent F setup/verify for SCRUM-463: [W19][1.3.7] Create Seller model
- Story: SCRUM-463
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.7
Task: Create Seller model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 42 — Agent F read project plan for SCRUM-469: [W19][1.3.13] Create ClusterAnalysis model
- Story: SCRUM-469
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.13
Task: Create ClusterAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 43 — Agent F implement AC for SCRUM-475: [W19][1.3.19] Create RunLog model
- Story: SCRUM-475
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.19
Task: Create RunLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 44 — Agent F validation for SCRUM-481: [W19][1.3.25] Create DiscoveryCycleLog model
- Story: SCRUM-481
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.25
Task: Create DiscoveryCycleLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 45 — Agent F cleanup for SCRUM-487: [W19][1.4.1] Create run.py CLI
- Story: SCRUM-487
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.1
Task: Create run.py CLI

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 46 — Agent F setup/verify for SCRUM-493: [W19][1.4.7] Create CLI unit tests
- Story: SCRUM-493
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.7
Task: Create CLI unit tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 47 — Agent F read project plan for SCRUM-499: [W19][1.5.6] Create Jinja2 template renderer
- Story: SCRUM-499
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.6
Task: Create Jinja2 template renderer

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 48 — Agent F implement AC for SCRUM-505: [W19][1.7.1] Create seed keyword YAML files
- Story: SCRUM-505
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-140
Task ID: 1.7.1
Task: Create seed keyword YAML files

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 49 — Agent F validation for SCRUM-230: [DASHBOARD] S9.16 Pricing Dashboard Widgets
- Story: SCRUM-230
- AC Focus: Story Implement S9.16 — Pricing Dashboard Widgets. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.16.1–9.16.4 covering pricing widgets, price ladder display, distribution charts, and tests. Acceptance Criteria Pricing widgets display price analysis, ladders, market positioning, and related confidence context. Widgets handle sparse or missing pricing data gracefully. Child tasks are created in later native task import waves or formally waived. Dashboard smoke tests validate pricing widget rendering and data access. DoD Complete when pricing widgets satisfy source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-16-pricing-widgets
PR: feat(dashboard): S9.16 Pricing Dashboard Widgets Suggested Metadata Labels: wave-19, story, dashboard, pricing-widgets, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- DoD Catalog Context: EPIC_09: [ ] Design tokens defined (colours, typography, spacing)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 50 — Agent F cleanup for SCRUM-255: [CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff
- Story: SCRUM-255
- AC Focus: Created by Cycle 012 Agent D during final integration board audit. Missing AC/DoD coverage discovered: Expected artifact docs/cycle_reports/CYCLE_012_AGENT_A.md is absent from branch evidence. Governance issue SCRUM-254 cannot be closed until missing Agent A report evidence is either delivered or formally dispositioned. Product stories in the Cycle 012 touched set remain In Progress/In Review without full source DoD closure evidence. Required follow-up: Deliver or disposition missing Agent A report. Re-run board-wide AC/DoD closure review for touched keys. Transition only issues with full source DoD evidence; keep others non-Done. Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with closure decisions and evidence links.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 51 — Agent F setup/verify for SCRUM-261: [CYCLE 017] Enforce repo-root branch/worktree controls and continue pr
- Story: SCRUM-261
- AC Focus: Purpose Cycle 017 continues product-forward development while permanently hardening PM Pack and Cursor prompt rules against the branch, GitHub, shell, worktree, and directory issues observed during Cycle 016. The operator specifically requested prevention of agents creating or using random directories instead of the canonical repo root C:\Fiverr\Fiverr . Required Guardrail Updates Add a canonical execution-root lock: every Cursor agent must work from C:\Fiverr\Fiverr by default. Require start-of-run preflight commands: Get-Location , git rev-parse --show-toplevel , git branch --show-current , git status --short --branch , and git worktree list . Abort if the Git top-level is not exactly C:\Fiverr\Fiverr unless the operator explicitly authorizes an alternate worktree in the current cycle. Ban default worktree creation and use. Worktrees require explicit operator approval, documented reason, exact path, branch binding, and cleanup/restore plan. Standardize all Windows runbook commands to PowerShell syntax; do not use Bash-only && , heredocs, or unquoted stash@{0} patterns. Before branch switching, require dirty-tree, untracked-collision, and worktree-binding checks. Require a final evidence freeze after the last push: final head SHA, PR URL, mergeability, exact check names/statuses, Codex thread status, Jira update status, and no-main confirmation must be synchronized in reports, ledger, and PR body. Product Focus After Guardrails After the short PR #13 merge gate, Cycle 017 should create cycle/017/integration from updated develop and continue actual Fiverr product development. Priority product scope: SCRUM-231, SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-237, SCRUM-239, SCRUM-240, SCRUM-241, and related dashboard/runtime closure stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228. Acceptance Criteria PM Pack contains permanent execution-root, worktree, branch safety, PowerShell, and final-evidence-freeze protocols. Cycle 017 prompts include these guardrails in the first instructions block for every agent. Prompt quality audit passes: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PR #13 is merged only if still green, mergeable, and Codex-resolved. Product work advances runtime dashboard/integration validation rather than becoming a process-only cycle. All touched Jira stories receive AC/DoD progress comments and remain non-Done unless full source DoD is satisfied.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 52 — Agent F read project plan for SCRUM-281: [MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline
- Story: SCRUM-281
- AC Focus: Medium Gap — M11\n\nCI pipeline runs Ruff (lint), Mypy (types), Pytest (tests), Codecov. Missing security scanning steps:\n\n- Bandit — Python security linter (finds SQL injection, hardcoded secrets, etc.)\n- Safety / pip-audit — CVE checker for installed Python packages\n- Secret scanning — TruffleHog or GitLeaks to prevent credential commits\n\nSCRUM-75 (security controls) implies these should exist.\n\n## Acceptance Criteria\n\n- [ ] Bandit added to CI with bandit -r src/ -ll (low-level threshold)\n- [ ] pip-audit or safety check added to CI\n- [ ] Secret scanning step added (TruffleHog or GitLeaks action)\n- [ ] CI fails if any HIGH severity Bandit finding exists\n- [ ] CI fails if any known CVE in current deps\n- [ ] Steps added to .github/workflows/ci.yml \n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M11\n* Related: SCRUM-75 (Credential/secrets/incident-response controls)
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 53 — Agent F implement AC for SCRUM-439: [CYCLE 019] Merge PR #15 and advance validation closure while fixing P
- Story: SCRUM-439
- AC Focus: Purpose Cycle 019 continues from uploaded Fiverr_018(1).zip and PM_Pack_018(1).zip . PM reviewed the local repository archive, local PM Pack, live GitHub PR #15, Codex review state, CI/Codecov state, and active Jira board scope. Cycle 019 should begin with a short PR #15 merge gate, then continue product-forward integration validation and closure work while fixing the PM Pack artifact-hygiene gaps found in the uploaded repo/pack. Local Repository Findings Active branch in uploaded repo: cycle/018/integration . Git status is clean for tracked source files but includes untracked PM_Pack/ cycle files in the repo archive. .env exists in the uploaded repo archive. It must never be read, printed, committed, copied into artifacts, or exposed. Cycle 018 branch contains 14 commits over origin/develop and 27 changed files. Cycle 018 changed areas include analysis closure readiness, dashboard runtime acceptance, dashboard query contracts, report reconciliation helpers, preflight/root guardrails, Jira ledgers, and PR template/freeze controls. Agent reports are present for Agent A, B, C, and D under docs/cycle_reports/ . PM Pack Findings Uploaded PM Pack contains PM_CORRECTIVE_RULES_CYCLE_018.md , board audit files, and Cycle 018 prompt files. Uploaded PM Pack is missing several protocol files that should be permanent after the prior root/worktree failures: 02_cycle_protocol/RUN_PREFLIGHT_POWERSHELL.md 05_github_protocol/EXECUTION_ROOT_AND_WORKTREE_LOCK.md 05_github_protocol/POWERSHELL_ONLY_COMMAND_POLICY.md 06_review_and_qa/FINAL_EVIDENCE_FREEZE_PROTOCOL.md 06_review_and_qa/GENERATED_PROMPT_QUALITY_AUDIT.md Agent A Cycle 018 prompt in the uploaded PM Pack is below the 6,000-word floor and must not be used as the Cycle 019 quality baseline. Live GitHub Findings PR #15: cycle018: finalize agent d board reconciliation and freeze controls . Source branch: cycle/018/integration . Target branch: develop . Status at PM review time: open, mergeable, not draft. Head SHA at review time: 4ba703210b619ca6c28165e77321341b1f7fcb66 . Codex review threads: two findings existed; both are replied to and resolved. CI workflow status: successful. Visible workflow jobs: Lint, Typecheck, Tests, and Gates and codecov/project , both successful. PR body mentions codecov/patch , but the visible workflow job list did not show a separate codecov/patch job; Cycle 019 steward must verify whether patch coverage is an external Codecov status, missing from the workflow job list, or needs restoration. Jira Board Findings Analysis stories SCRUM-157 through SCRUM-164 are In Review and need closure evidence before any Done transitions. Dashboard/runtime stories SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, SCRUM-228, and SCRUM-231 are In Review and should remain non-Done until full runtime/production acceptance evidence exists. SCRUM-213 remains In Progress. SCRUM-216, SCRUM-218, SCRUM-220, and SCRUM-223 remain To Do and should not be silently treated as completed by adjacent dashboard work. Integration stories SCRUM-232, SCRUM-233, SCRUM-234, SCRUM-236, SCRUM-239, SCRUM-240, SCRUM-241, and SCRUM-242 remain To Do unless Cycle 019 agents touch them and add AC/DoD progress evidence. SCRUM-250 remains In Review; SCRUM-254 remains In Progress; SCRUM-257 remains To Do; SCRUM-262 remains In Progress pending PR #15 merge. Cycle 019 Product Focus After PR #15 is merged into develop , create cycle/019/integration from updated develop and advance product work from Jira AC/DoD stories. Priority scope: SCRUM-232 — Data Integrity Validation SCRUM-233 — Performance Testing SCRUM-234 — Resilience Testing SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-239 — First Run Validation SCRUM-240 — Full 9-Niche Validation Run readiness SCRUM-241 — Security and Data Hygiene SCRUM-242 — Launch Readiness Checklist preparation SCRUM-157 through SCRUM-164 — Analysis closure evidence SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-228, SCRUM-231 — Dashboard/runtime and integration closure evidence SCRUM-257 — Duplicate/premature Done-risk audit for SCRUM-217, SCRUM-221, and SCRUM-222, without derailing product work Required Guardrails Work only from C:\Fiverr\Fiverr unless Kevin explicitly authorizes an alternate path in-thread. No random directories, copied repos, or unapproved worktrees. PowerShell-only operational commands. Do not read, print, stage, commit, or expose .env . Same-cycle Codex review handling is mandatory. Final evidence freeze after the last push/checks settle is mandatory. Cursor prompt quality audit must pass before PM handoff: 20+ substantive tasks and 6,000+ words per agent unless formally waived. PM Pack permanent protocol files must be restored into the generated PM Pack artifact. Acceptance Criteria PR #15 is merged only if still green, mergeable, and Codex-resolved. Cycle 019 branch starts from updated develop after PR #15 merge, or branch creation is blocked with evidence. Product work advances integration validation/runtime closure rather than process-only cleanup. PM Pack artifact hygiene is corrected and untracked repo PM Pack files are either committed intentionally or removed from the working tree before PR handoff. .env remains untouched and excluded from artifacts/repo changes. Touched Jira stories receive AC/DoD progress comments and are not marked Done unless full source DoD is satisfied. Codecov project and patch expectations are verified or restored. Prompt quality audit passes for all agents. Updated PM Pack zip, PM response, and prompt-only backup are generated and verified.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 54 — Agent F validation for SCRUM-445: [W19][1.1.3] Create requirements.txt with pinned versions
- Story: SCRUM-445
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.3
Task: Create requirements.txt with pinned versions

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 55 — Agent F cleanup for SCRUM-451: [W19][1.2.2] Create ConfigLoader class
- Story: SCRUM-451
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.2
Task: Create ConfigLoader class

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.


## Validation Commands
- ruff check automation/ src/ tests/
- mypy src/ automation/ --ignore-missing-imports
- pytest tests/unit/ --timeout=30 --tb=no -q
- python automation/ai_cycle_controller.py brain-check
- python automation/ai_cycle_controller.py pm-pack-audit --check-only

## Report
- Write: docs/cycle_reports/CYCLE_078_AGENT_F.md
- Final line must be: AGENT_COMPLETE

Generated at: 2026-06-14T01:01:30.387568+00:00

---

END OF PROMPT
