====================================================================
AGENT A -- CYCLE 077 PROMPT
====================================================================

## PROJECT CONTEXT

- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch: `cycle/077/integration`
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit
- Cycle: 077 | Run ID: 20260613T025926

## MODEL POLICY (MANDATORY — do not override)

- **Model:** Codex 5.3
- **Effort:** medium
- **Auto model selection:** DISABLED — use only Codex 5.3
- **Fallback model:** DISABLED
- **Billing:** Claude subscription only for PM review; no API key

## YOUR ROLE

**Agent A** — PM planning, architecture, docs, GitHub governance, config
**Role type:** `planner_foundation_integration`

**You own these file paths (you may create/modify only these):**
- `PM_Pack/**`
- `docs/**`
- `.github/**`
- `pyproject.toml`
- `config.yaml`
- `.cursorrules`

**You must NOT modify these paths:**
- `src/**`
- `tests/**`
- `data/**`

## GIT INSTRUCTIONS

1. Confirm you are on branch: `cycle/077/integration`
   ```
   git branch --show-current
   # Expected: cycle/077/integration
   ```
2. Pull latest: `git pull origin cycle/077/integration`
3. ALL work on `cycle/077/integration` only — do NOT create other branches
4. **DO NOT run git add, git commit, git push.** The controller owns all git operations.
5. **DO NOT run gh pr commands.** The controller manages PRs.
6. Complete your tasks, write your report, and exit.

## AUTONOMY RULE

- Proceed autonomously through all tasks without pausing for confirmation.
- If a task cannot be completed due to a missing dependency, document the blocker
  in your report and continue to the next task.
- If a test fails, fix the bug causing the failure. Do NOT use `pytest.mark.skip`
  as a workaround. If you cannot fix it in 3 attempts, document it as a blocker.
- Do NOT commit files. The controller validates and commits after you finish.

## JIRA SCOPE FOR THIS CYCLE

| Jira Key | Summary | Status | Priority |
|---|---|---|---|
| SCRUM-246 | [PM PROCESS] Cycle 001 prompts lacked required depth an | In Review | Medium |
| SCRUM-250 | [PM/JIRA] Correct cycle-to-story Jira mapping and preve | In Review | Medium |
| SCRUM-252 | [PM/CURSOR] Grant Cursor-agent Jira operations authorit | In Review | Medium |
| SCRUM-253 | [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard bl | In Review | Medium |
| SCRUM-254 | [PM/JIRA] Enforce full-board AC/DoD-first planning and  | In Review | Medium |
| SCRUM-256 | [CYCLE 013] Resolve PR #10 Codex blockers and continue  | In Progress | Medium |
| SCRUM-258 | [CYCLE 014] Resume product development and enforce same | In Progress | Medium |
| SCRUM-280 | [MEDIUM M10] Create .github/dependabot.yml — automated  | To Do | Medium |
| SCRUM-281 | [MEDIUM M11] Add Bandit + pip-audit + secret scanning t | To Do | Medium |
| SCRUM-282 | [MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\Fiverr | To Do | Medium |
| SCRUM-283 | [MEDIUM M14/M15] Fix planning doc count inconsistencies | To Do | Medium |
| SCRUM-284 | [MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACK | To Do | Medium |
| SCRUM-286 | [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale l | To Do | Medium |
| SCRUM-439 | [CYCLE 019] Merge PR #15 and advance validation closure | In Progress | Medium |
| SCRUM-440 | ■ AI PM OPERATING PROTOCOL — READ FIRST | To Do | Medium |
| SCRUM-441 | ■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION | To Do | Medium |
| SCRUM-446 | [W19][1.1.4] Create .env.example and environment config | To Do | Medium |
| SCRUM-450 | [W19][1.2.1] Create config.yaml master template | To Do | Medium |
| SCRUM-451 | [W19][1.2.2] Create ConfigLoader class | To Do | Medium |
| SCRUM-452 | [W19][1.2.3] Create NicheConfig Pydantic model | To Do | Medium |

## TASKS FOR THIS CYCLE

> **Floor:** 55 LARGE/XLARGE/XXLARGE tasks (AGENT_TASK_FLOOR_ENFORCEMENT.md hard rule).
> Each task must have: Story/Jira key, Epic, Spec, Files, Implementation details
> (>=100 words), >=3 tests, Definition of Done.


**MANDATORY FLOOR CHECK — Run at the start of your work (AGENT_TASK_FLOOR_ENFORCEMENT.md):**

```python
# cycle_077_floor_check.py
import sys
from pathlib import Path

CYCLE = 77
MIN_TASKS = 55
prompt_dir = Path("PM_Pack/automation/prompts")

total = 0
for agent in ["A", "B", "E", "C", "F", "D"]:
    p = prompt_dir / f"CYCLE_{CYCLE:03d}_AGENT_{agent}_PROMPT.md"
    if p.exists():
        count = len([l for l in p.read_text().splitlines()
                     if l.startswith("### Task ")])
        print(f"Agent {agent}: {count} tasks")
        total += count

print(f"Total: {total}")
if total < MIN_TASKS * 6:
    print(f"FLOOR VIOLATION: {total} < {MIN_TASKS * 6} minimum", file=sys.stderr)
    sys.exit(1)
print("PASS: task floor met")
```

### Task 1: Architecture review and spec for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 — [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **DOD:** See SCRUM-246 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_246_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-246
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 2: GitHub governance and CI gate for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 — [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **DOD:** See SCRUM-246 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-246 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-246 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-246 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 3: Config and dependency validation for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 — [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **DOD:** See SCRUM-246 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-246. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 4: PM_Pack and Jira governance update for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 — [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **DOD:** See SCRUM-246 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-246 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-246. Cross-check that Jira status for SCRUM-246 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-246
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 5: Architecture review and spec for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 — [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **DOD:** See SCRUM-250 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_250_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-250
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 6: GitHub governance and CI gate for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 — [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **DOD:** See SCRUM-250 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-250 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-250 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-250 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 7: Config and dependency validation for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 — [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **DOD:** See SCRUM-250 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-250. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 8: PM_Pack and Jira governance update for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 — [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **DOD:** See SCRUM-250 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-250 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-250. Cross-check that Jira status for SCRUM-250 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-250
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 9: Architecture review and spec for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 — [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **DOD:** See SCRUM-252 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_252_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-252
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 10: GitHub governance and CI gate for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 — [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **DOD:** See SCRUM-252 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-252 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-252 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-252 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 11: Config and dependency validation for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 — [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **DOD:** See SCRUM-252 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-252. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 12: PM_Pack and Jira governance update for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 — [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **DOD:** See SCRUM-252 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-252 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-252. Cross-check that Jira status for SCRUM-252 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-252
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 13: Architecture review and spec for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 — [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **DOD:** See SCRUM-253 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_253_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-253
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 14: GitHub governance and CI gate for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 — [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **DOD:** See SCRUM-253 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-253 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-253 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-253 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 15: Config and dependency validation for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 — [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **DOD:** See SCRUM-253 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-253. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 16: PM_Pack and Jira governance update for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 — [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **DOD:** See SCRUM-253 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-253 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-253. Cross-check that Jira status for SCRUM-253 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-253
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 17: Architecture review and spec for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 — [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **DOD:** See SCRUM-254 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_254_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-254
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 18: GitHub governance and CI gate for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 — [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **DOD:** See SCRUM-254 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-254 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-254 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-254 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 19: Config and dependency validation for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 — [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **DOD:** See SCRUM-254 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-254. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 20: PM_Pack and Jira governance update for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 — [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **DOD:** See SCRUM-254 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-254 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-254. Cross-check that Jira status for SCRUM-254 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-254
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 21: Architecture review and spec for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 — [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **DOD:** See SCRUM-256 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_256_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-256
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 22: GitHub governance and CI gate for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 — [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **DOD:** See SCRUM-256 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-256 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-256 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-256 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 23: Config and dependency validation for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 — [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **DOD:** See SCRUM-256 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-256. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 24: PM_Pack and Jira governance update for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 — [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **DOD:** See SCRUM-256 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-256 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-256. Cross-check that Jira status for SCRUM-256 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-256
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 25: Architecture review and spec for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 — [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **DOD:** See SCRUM-258 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_258_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-258
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 26: GitHub governance and CI gate for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 — [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **DOD:** See SCRUM-258 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-258 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-258 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-258 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 27: Config and dependency validation for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 — [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **DOD:** See SCRUM-258 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-258. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 28: PM_Pack and Jira governance update for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 — [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **DOD:** See SCRUM-258 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-258 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-258. Cross-check that Jira status for SCRUM-258 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-258
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 29: Architecture review and spec for [MEDIUM M10] Create .github/dependa

- **Jira:** SCRUM-280 — [MEDIUM M10] Create .github/dependabot.yml — autom
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-280 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-280 description for referenced spec files)
- **DOD:** See SCRUM-280 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_280_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-280 '[MEDIUM M10] Create .github/dependabot.yml — automated dependency security updates missing'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-280
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-280 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 30: GitHub governance and CI gate for [MEDIUM M10] Create .github/dependa

- **Jira:** SCRUM-280 — [MEDIUM M10] Create .github/dependabot.yml — autom
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-280 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-280 description for referenced spec files)
- **DOD:** See SCRUM-280 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-280 '[MEDIUM M10] Create .github/dependabot.yml — automated dependency security updates missing'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-280 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-280 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-280 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-280 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 31: Config and dependency validation for [MEDIUM M10] Create .github/dependa

- **Jira:** SCRUM-280 — [MEDIUM M10] Create .github/dependabot.yml — autom
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-280 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-280 description for referenced spec files)
- **DOD:** See SCRUM-280 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-280 '[MEDIUM M10] Create .github/dependabot.yml — automated dependency security updates missing' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-280. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-280 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 32: PM_Pack and Jira governance update for [MEDIUM M10] Create .github/dependa

- **Jira:** SCRUM-280 — [MEDIUM M10] Create .github/dependabot.yml — autom
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-280 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-280 description for referenced spec files)
- **DOD:** See SCRUM-280 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-280 '[MEDIUM M10] Create .github/dependabot.yml — automated dependency security updates missing' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-280 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-280. Cross-check that Jira status for SCRUM-280 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-280
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-280 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 33: Architecture review and spec for [MEDIUM M11] Add Bandit + pip-audit

- **Jira:** SCRUM-281 — [MEDIUM M11] Add Bandit + pip-audit + secret scann
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-281 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-281 description for referenced spec files)
- **DOD:** See SCRUM-281 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_281_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-281 '[MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-281
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-281 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 34: GitHub governance and CI gate for [MEDIUM M11] Add Bandit + pip-audit

- **Jira:** SCRUM-281 — [MEDIUM M11] Add Bandit + pip-audit + secret scann
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-281 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-281 description for referenced spec files)
- **DOD:** See SCRUM-281 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-281 '[MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-281 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-281 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-281 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-281 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 35: Config and dependency validation for [MEDIUM M11] Add Bandit + pip-audit

- **Jira:** SCRUM-281 — [MEDIUM M11] Add Bandit + pip-audit + secret scann
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-281 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-281 description for referenced spec files)
- **DOD:** See SCRUM-281 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-281 '[MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-281. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-281 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 36: PM_Pack and Jira governance update for [MEDIUM M11] Add Bandit + pip-audit

- **Jira:** SCRUM-281 — [MEDIUM M11] Add Bandit + pip-audit + secret scann
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-281 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-281 description for referenced spec files)
- **DOD:** See SCRUM-281 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-281 '[MEDIUM M11] Add Bandit + pip-audit + secret scanning to CI pipeline' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-281 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-281. Cross-check that Jira status for SCRUM-281 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-281
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-281 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 37: Architecture review and spec for [MEDIUM M13] Bulk replace C:\\Fiver

- **Jira:** SCRUM-282 — [MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\F
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-282 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-282 description for referenced spec files)
- **DOD:** See SCRUM-282 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_282_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-282 '[MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\Fiverr\\ in 100+ Jira descriptions and plan files'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-282
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-282 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 38: GitHub governance and CI gate for [MEDIUM M13] Bulk replace C:\\Fiver

- **Jira:** SCRUM-282 — [MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\F
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-282 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-282 description for referenced spec files)
- **DOD:** See SCRUM-282 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-282 '[MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\Fiverr\\ in 100+ Jira descriptions and plan files'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-282 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-282 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-282 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-282 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 39: Config and dependency validation for [MEDIUM M13] Bulk replace C:\\Fiver

- **Jira:** SCRUM-282 — [MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\F
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-282 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-282 description for referenced spec files)
- **DOD:** See SCRUM-282 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-282 '[MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\Fiverr\\ in 100+ Jira descriptions and plan files' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-282. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-282 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 40: PM_Pack and Jira governance update for [MEDIUM M13] Bulk replace C:\\Fiver

- **Jira:** SCRUM-282 — [MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\F
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-282 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-282 description for referenced spec files)
- **DOD:** See SCRUM-282 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-282 '[MEDIUM M13] Bulk replace C:\\Fiverr1\\ with C:\\Fiverr\\ in 100+ Jira descriptions and plan files' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-282 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-282. Cross-check that Jira status for SCRUM-282 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-282
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-282 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 41: Architecture review and spec for [MEDIUM M14/M15] Fix planning doc c

- **Jira:** SCRUM-283 — [MEDIUM M14/M15] Fix planning doc count inconsiste
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-283 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-283 description for referenced spec files)
- **DOD:** See SCRUM-283 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_283_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-283 '[MEDIUM M14/M15] Fix planning doc count inconsistencies — WAVE_SCHEDULE claims 568 tasks (actual 600), Epic 01 header claims 22 stories (actual 7)'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-283
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-283 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 42: GitHub governance and CI gate for [MEDIUM M14/M15] Fix planning doc c

- **Jira:** SCRUM-283 — [MEDIUM M14/M15] Fix planning doc count inconsiste
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-283 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-283 description for referenced spec files)
- **DOD:** See SCRUM-283 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-283 '[MEDIUM M14/M15] Fix planning doc count inconsistencies — WAVE_SCHEDULE claims 568 tasks (actual 600), Epic 01 header claims 22 stories (actual 7)'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-283 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-283 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-283 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-283 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 43: Config and dependency validation for [MEDIUM M14/M15] Fix planning doc c

- **Jira:** SCRUM-283 — [MEDIUM M14/M15] Fix planning doc count inconsiste
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-283 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-283 description for referenced spec files)
- **DOD:** See SCRUM-283 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-283 '[MEDIUM M14/M15] Fix planning doc count inconsistencies — WAVE_SCHEDULE claims 568 tasks (actual 600), Epic 01 header claims 22 stories (actual 7)' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-283. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-283 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 44: PM_Pack and Jira governance update for [MEDIUM M14/M15] Fix planning doc c

- **Jira:** SCRUM-283 — [MEDIUM M14/M15] Fix planning doc count inconsiste
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-283 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-283 description for referenced spec files)
- **DOD:** See SCRUM-283 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-283 '[MEDIUM M14/M15] Fix planning doc count inconsistencies — WAVE_SCHEDULE claims 568 tasks (actual 600), Epic 01 header claims 22 stories (actual 7)' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-283 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-283. Cross-check that Jira status for SCRUM-283 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-283
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-283 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 45: Architecture review and spec for [MEDIUM M16/M17] Update stale PM_Pa

- **Jira:** SCRUM-284 — [MEDIUM M16/M17] Update stale PM_Pack files — TASK
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-284 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-284 description for referenced spec files)
- **DOD:** See SCRUM-284 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_284_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-284 '[MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 001 stale, PM_Pack_017.zip out of sync (284 vs 240 files)'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-284
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-284 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 46: GitHub governance and CI gate for [MEDIUM M16/M17] Update stale PM_Pa

- **Jira:** SCRUM-284 — [MEDIUM M16/M17] Update stale PM_Pack files — TASK
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-284 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-284 description for referenced spec files)
- **DOD:** See SCRUM-284 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-284 '[MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 001 stale, PM_Pack_017.zip out of sync (284 vs 240 files)'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-284 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-284 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-284 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-284 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 47: Config and dependency validation for [MEDIUM M16/M17] Update stale PM_Pa

- **Jira:** SCRUM-284 — [MEDIUM M16/M17] Update stale PM_Pack files — TASK
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-284 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-284 description for referenced spec files)
- **DOD:** See SCRUM-284 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-284 '[MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 001 stale, PM_Pack_017.zip out of sync (284 vs 240 files)' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-284. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-284 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 48: PM_Pack and Jira governance update for [MEDIUM M16/M17] Update stale PM_Pa

- **Jira:** SCRUM-284 — [MEDIUM M16/M17] Update stale PM_Pack files — TASK
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-284 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-284 description for referenced spec files)
- **DOD:** See SCRUM-284 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-284 '[MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 001 stale, PM_Pack_017.zip out of sync (284 vs 240 files)' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-284 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-284. Cross-check that Jira status for SCRUM-284 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-284
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-284 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 49: Architecture review and spec for [MEDIUM M23-M26] Fix 4 PM/governanc

- **Jira:** SCRUM-286 — [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — st
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-286 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-286 description for referenced spec files)
- **DOD:** See SCRUM-286 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_286_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-286 '[MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, missing DL entry, AGENT_ROSTER overload, obsolete field standards template'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-286
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-286 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 50: GitHub governance and CI gate for [MEDIUM M23-M26] Fix 4 PM/governanc

- **Jira:** SCRUM-286 — [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — st
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-286 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-286 description for referenced spec files)
- **DOD:** See SCRUM-286 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-286 '[MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, missing DL entry, AGENT_ROSTER overload, obsolete field standards template'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-286 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-286 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-286 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-286 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 51: Config and dependency validation for [MEDIUM M23-M26] Fix 4 PM/governanc

- **Jira:** SCRUM-286 — [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — st
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-286 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-286 description for referenced spec files)
- **DOD:** See SCRUM-286 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-286 '[MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, missing DL entry, AGENT_ROSTER overload, obsolete field standards template' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-286. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-286 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 52: PM_Pack and Jira governance update for [MEDIUM M23-M26] Fix 4 PM/governanc

- **Jira:** SCRUM-286 — [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — st
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-286 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-286 description for referenced spec files)
- **DOD:** See SCRUM-286 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-286 '[MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, missing DL entry, AGENT_ROSTER overload, obsolete field standards template' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-286 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-286. Cross-check that Jira status for SCRUM-286 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-286
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-286 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 53: Architecture review and spec for [CYCLE 019] Merge PR #15 and advanc

- **Jira:** SCRUM-439 — [CYCLE 019] Merge PR #15 and advance validation cl
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-439 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-439 description for referenced spec files)
- **DOD:** See SCRUM-439 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_439_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-439 '[CYCLE 019] Merge PR #15 and advance validation closure while fixing PM Pack artifact hygiene'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-439
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-439 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 54: GitHub governance and CI gate for [CYCLE 019] Merge PR #15 and advanc

- **Jira:** SCRUM-439 — [CYCLE 019] Merge PR #15 and advance validation cl
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-439 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-439 description for referenced spec files)
- **DOD:** See SCRUM-439 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-439 '[CYCLE 019] Merge PR #15 and advance validation closure while fixing PM Pack artifact hygiene'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-439 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-439 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-439 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-439 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 55: Config and dependency validation for [CYCLE 019] Merge PR #15 and advanc

- **Jira:** SCRUM-439 — [CYCLE 019] Merge PR #15 and advance validation cl
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-439 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-439 description for referenced spec files)
- **DOD:** See SCRUM-439 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-439 '[CYCLE 019] Merge PR #15 and advance validation closure while fixing PM Pack artifact hygiene' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-439. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-439 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 56: PM_Pack and Jira governance update for [CYCLE 019] Merge PR #15 and advanc

- **Jira:** SCRUM-439 — [CYCLE 019] Merge PR #15 and advance validation cl
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-439 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-439 description for referenced spec files)
- **DOD:** See SCRUM-439 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-439 '[CYCLE 019] Merge PR #15 and advance validation closure while fixing PM Pack artifact hygiene' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-439 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-439. Cross-check that Jira status for SCRUM-439 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-439
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-439 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 57: Architecture review and spec for ■ AI PM OPERATING PROTOCOL — READ F

- **Jira:** SCRUM-440 — ■ AI PM OPERATING PROTOCOL — READ FIRST
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-440 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-440 description for referenced spec files)
- **DOD:** See SCRUM-440 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_440_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-440 '■ AI PM OPERATING PROTOCOL — READ FIRST'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-440
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-440 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 58: GitHub governance and CI gate for ■ AI PM OPERATING PROTOCOL — READ F

- **Jira:** SCRUM-440 — ■ AI PM OPERATING PROTOCOL — READ FIRST
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-440 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-440 description for referenced spec files)
- **DOD:** See SCRUM-440 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-440 '■ AI PM OPERATING PROTOCOL — READ FIRST'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-440 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-440 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-440 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-440 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 59: Config and dependency validation for ■ AI PM OPERATING PROTOCOL — READ F

- **Jira:** SCRUM-440 — ■ AI PM OPERATING PROTOCOL — READ FIRST
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-440 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-440 description for referenced spec files)
- **DOD:** See SCRUM-440 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-440 '■ AI PM OPERATING PROTOCOL — READ FIRST' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-440. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-440 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 60: PM_Pack and Jira governance update for ■ AI PM OPERATING PROTOCOL — READ F

- **Jira:** SCRUM-440 — ■ AI PM OPERATING PROTOCOL — READ FIRST
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-440 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-440 description for referenced spec files)
- **DOD:** See SCRUM-440 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-440 '■ AI PM OPERATING PROTOCOL — READ FIRST' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-440 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-440. Cross-check that Jira status for SCRUM-440 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-440
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-440 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 61: Architecture review and spec for ■ AI PM STATUS DASHBOARD — UPDATE E

- **Jira:** SCRUM-441 — ■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-441 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-441 description for referenced spec files)
- **DOD:** See SCRUM-441 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_441_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-441 '■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-441
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-441 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 62: GitHub governance and CI gate for ■ AI PM STATUS DASHBOARD — UPDATE E

- **Jira:** SCRUM-441 — ■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-441 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-441 description for referenced spec files)
- **DOD:** See SCRUM-441 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-441 '■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-441 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-441 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-441 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-441 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 63: Config and dependency validation for ■ AI PM STATUS DASHBOARD — UPDATE E

- **Jira:** SCRUM-441 — ■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-441 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-441 description for referenced spec files)
- **DOD:** See SCRUM-441 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-441 '■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-441. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-441 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 64: PM_Pack and Jira governance update for ■ AI PM STATUS DASHBOARD — UPDATE E

- **Jira:** SCRUM-441 — ■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-441 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-441 description for referenced spec files)
- **DOD:** See SCRUM-441 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-441 '■ AI PM STATUS DASHBOARD — UPDATE EACH SESSION' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-441 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-441. Cross-check that Jira status for SCRUM-441 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-441
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-441 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 65: Architecture review and spec for [W19][1.1.4] Create .env.example an

- **Jira:** SCRUM-446 — [W19][1.1.4] Create .env.example and environment c
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-446 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-446 description for referenced spec files)
- **DOD:** See SCRUM-446 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_446_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-446 '[W19][1.1.4] Create .env.example and environment config notes'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-446
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-446 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 66: GitHub governance and CI gate for [W19][1.1.4] Create .env.example an

- **Jira:** SCRUM-446 — [W19][1.1.4] Create .env.example and environment c
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-446 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-446 description for referenced spec files)
- **DOD:** See SCRUM-446 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-446 '[W19][1.1.4] Create .env.example and environment config notes'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-446 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-446 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-446 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-446 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 67: Config and dependency validation for [W19][1.1.4] Create .env.example an

- **Jira:** SCRUM-446 — [W19][1.1.4] Create .env.example and environment c
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-446 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-446 description for referenced spec files)
- **DOD:** See SCRUM-446 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-446 '[W19][1.1.4] Create .env.example and environment config notes' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-446. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-446 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 68: PM_Pack and Jira governance update for [W19][1.1.4] Create .env.example an

- **Jira:** SCRUM-446 — [W19][1.1.4] Create .env.example and environment c
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-446 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-446 description for referenced spec files)
- **DOD:** See SCRUM-446 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-446 '[W19][1.1.4] Create .env.example and environment config notes' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-446 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-446. Cross-check that Jira status for SCRUM-446 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-446
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-446 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 69: Architecture review and spec for [W19][1.2.1] Create config.yaml mas

- **Jira:** SCRUM-450 — [W19][1.2.1] Create config.yaml master template
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-450 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-450 description for referenced spec files)
- **DOD:** See SCRUM-450 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_450_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-450 '[W19][1.2.1] Create config.yaml master template'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-450
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-450 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 70: GitHub governance and CI gate for [W19][1.2.1] Create config.yaml mas

- **Jira:** SCRUM-450 — [W19][1.2.1] Create config.yaml master template
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-450 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-450 description for referenced spec files)
- **DOD:** See SCRUM-450 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-450 '[W19][1.2.1] Create config.yaml master template'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-450 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-450 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-450 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-450 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 71: Config and dependency validation for [W19][1.2.1] Create config.yaml mas

- **Jira:** SCRUM-450 — [W19][1.2.1] Create config.yaml master template
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-450 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-450 description for referenced spec files)
- **DOD:** See SCRUM-450 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-450 '[W19][1.2.1] Create config.yaml master template' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-450. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-450 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 72: PM_Pack and Jira governance update for [W19][1.2.1] Create config.yaml mas

- **Jira:** SCRUM-450 — [W19][1.2.1] Create config.yaml master template
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-450 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-450 description for referenced spec files)
- **DOD:** See SCRUM-450 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-450 '[W19][1.2.1] Create config.yaml master template' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-450 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-450. Cross-check that Jira status for SCRUM-450 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-450
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-450 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 73: Architecture review and spec for [W19][1.2.2] Create ConfigLoader cl

- **Jira:** SCRUM-451 — [W19][1.2.2] Create ConfigLoader class
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-451 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-451 description for referenced spec files)
- **DOD:** See SCRUM-451 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_451_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-451 '[W19][1.2.2] Create ConfigLoader class'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-451
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-451 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 74: GitHub governance and CI gate for [W19][1.2.2] Create ConfigLoader cl

- **Jira:** SCRUM-451 — [W19][1.2.2] Create ConfigLoader class
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-451 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-451 description for referenced spec files)
- **DOD:** See SCRUM-451 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-451 '[W19][1.2.2] Create ConfigLoader class'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-451 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-451 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-451 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-451 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 75: Config and dependency validation for [W19][1.2.2] Create ConfigLoader cl

- **Jira:** SCRUM-451 — [W19][1.2.2] Create ConfigLoader class
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-451 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-451 description for referenced spec files)
- **DOD:** See SCRUM-451 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-451 '[W19][1.2.2] Create ConfigLoader class' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-451. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-451 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 76: PM_Pack and Jira governance update for [W19][1.2.2] Create ConfigLoader cl

- **Jira:** SCRUM-451 — [W19][1.2.2] Create ConfigLoader class
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-451 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-451 description for referenced spec files)
- **DOD:** See SCRUM-451 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-451 '[W19][1.2.2] Create ConfigLoader class' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-451 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-451. Cross-check that Jira status for SCRUM-451 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-451
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-451 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 77: Architecture review and spec for [W19][1.2.3] Create NicheConfig Pyd

- **Jira:** SCRUM-452 — [W19][1.2.3] Create NicheConfig Pydantic model
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-452 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-452 description for referenced spec files)
- **DOD:** See SCRUM-452 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - CREATE: PM_Pack/10_cycle_log/CYCLE_075_scrum_452_spec.md

**Implementation Details:**

Review the current architecture for SCRUM-452 '[W19][1.2.3] Create NicheConfig Pydantic model'. Identify all integration points with the existing pipeline. Document the component boundaries, data flow, error handling strategy, and API contract in the relevant spec file under ref/project_plan/. Ensure the spec names the exact modules to be created or modified, the data models involved, the method signatures for new public APIs, and the validation strategy. Record the review in PM_Pack with a decision log entry explaining any architecture tradeoffs. Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. Output must be a readable spec artifact that Agent B can execute against.

**Required Tests:**
- Read spec and verify all referenced paths exist or are created this cycle
- Confirm no orphaned imports or missing __init__.py entries
- Validate JSON schema for any new data model definition

**Definition of Done:**
- [ ] Spec file exists at exact path referenced in SCRUM-452
- [ ] Spec is >=300 words with API contract, acceptance criteria, test requirements
- [ ] Architecture decision logged in PM_Pack
- [ ] All AC items for SCRUM-452 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 78: GitHub governance and CI gate for [W19][1.2.3] Create NicheConfig Pyd

- **Jira:** SCRUM-452 — [W19][1.2.3] Create NicheConfig Pydantic model
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-452 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-452 description for referenced spec files)
- **DOD:** See SCRUM-452 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: .github/workflows/ci.yml
- - MODIFY: .github/PULL_REQUEST_TEMPLATE.md

**Implementation Details:**

Verify GitHub Actions CI configuration is correctly set up to enforce the quality gates required for SCRUM-452 '[W19][1.2.3] Create NicheConfig Pydantic model'. Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage against the files that will be changed in this story. Update .github/workflows/ if any gate is missing or misconfigured. Confirm branch protection rules for develop are still enforced. Update PR template to include the Jira key SCRUM-452 in the required fields. Document any CI changes in a commit log entry with rationale. Verify the check names in ci.yml match what merge_gate.py expects to find in GitHub status check results.

**Required Tests:**
- CI workflow lint check passes on changed files
- Branch protection still enforced after any config change
- PR template includes SCRUM-452 requirement

**Definition of Done:**
- [ ] CI gate configured for SCRUM-452 scope
- [ ] Branch protection rules unchanged
- [ ] .github/workflows/ changes committed with rationale
- [ ] All AC items for SCRUM-452 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 79: Config and dependency validation for [W19][1.2.3] Create NicheConfig Pyd

- **Jira:** SCRUM-452 — [W19][1.2.3] Create NicheConfig Pydantic model
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-452 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-452 description for referenced spec files)
- **DOD:** See SCRUM-452 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: config.yaml
- - MODIFY: pyproject.toml

**Implementation Details:**

Validate that all configuration entries required for SCRUM-452 '[W19][1.2.3] Create NicheConfig Pydantic model' are present and correct in config.yaml. Run python run.py config-check and confirm it passes. If new configuration keys are required, add them to config.yaml with sensible defaults and update the config schema validation. Verify pyproject.toml has the correct dependency entries for any new libraries referenced by SCRUM-452. Update requirements if needed. Confirm that scrapfly.enabled remains false in committed config.yaml. Document all config changes in the cycle report with before/after values.

**Required Tests:**
- python run.py config-check passes with no errors
- All new config keys have documented defaults
- scrapfly.enabled=false confirmed in config.yaml

**Definition of Done:**
- [ ] config-check PASS
- [ ] No new required env vars without defaults
- [ ] pyproject.toml up to date
- [ ] All AC items for SCRUM-452 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 80: PM_Pack and Jira governance update for [W19][1.2.3] Create NicheConfig Pyd

- **Jira:** SCRUM-452 — [W19][1.2.3] Create NicheConfig Pydantic model
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-452 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-452 description for referenced spec files)
- **DOD:** See SCRUM-452 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md
- - MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md

**Implementation Details:**

Update PM_Pack hydration and state documents to reflect the work planned for SCRUM-452 '[W19][1.2.3] Create NicheConfig Pydantic model' in cycle 077. Update HYDRATION_HEADER.md with the current cycle scope and any new blockers discovered during architecture review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the decision to include SCRUM-452 in this cycle and the expected agent assignments. Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for the epic containing SCRUM-452. Cross-check that Jira status for SCRUM-452 matches the planned AC delivery in this cycle. Record any stale document findings in STALE_DOCUMENT_REGISTER.md.

**Required Tests:**
- HYDRATION_HEADER.md updated with cycle 077 scope
- Cycle log entry created for SCRUM-452
- Jira status matches planned delivery

**Definition of Done:**
- [ ] PM_Pack documents are internally consistent
- [ ] No new stale document warnings
- [ ] Cycle log entry committed
- [ ] All AC items for SCRUM-452 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

## VALIDATION STEPS

Run these commands in order. Fix any failures before writing your report.

```bash
# 1. Ruff lint
python -m ruff check src/ tests/ automation/ --output-format=text

# 2. Mypy type check
python -m mypy src/ --ignore-missing-imports

# 3. Pytest — run tests relevant to your changed files
python -m pytest tests/ -q --no-header --tb=short -x

# 4. Config check
python run.py config-check
```

**Do not mark your report complete if any check fails.**

## FINAL REPORT REQUIREMENTS

Write your report to: `docs/cycle_reports/CYCLE_077_AGENT_A.md`

Your report MUST contain:
- Header: `# CYCLE_077_AGENT_A REPORT`
- Summary of all work completed
- List of all files created or modified (with full paths)
- Validation results (ruff/mypy/pytest command output)
- Jira evidence (which AC/DoD items were addressed and how)
- Blockers encountered (if any, with details)
- `AGENT_COMPLETE` as the final line

**IMPORTANT:** Do NOT run git add, git commit, or git push.
Write your report and exit. The controller handles all commits.

## FILES CREATED/MODIFIED THIS CYCLE (Summary)

Complete after finishing all tasks:

| Action | File Path |
|---|---|
| n/a | n/a |

====================================================================
END OF PROMPT -- AGENT A CYCLE 077
====================================================================

<!-- Generated by prompt_generator.py -->
<!-- Run ID: 20260613T025926 | Generated: 2026-06-13T02:59:27.170153+00:00 -->