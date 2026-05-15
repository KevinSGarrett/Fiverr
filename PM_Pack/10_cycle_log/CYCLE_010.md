# CYCLE 010 — PM RESPONSE

Date: 2026-05-14 America/Chicago  
Repository: `KevinSGarrett/Fiverr`  
Base branch: `develop`  
Cycle branch: `cycle/010/integration`  
Primary focus: Cursor-agent Jira authority protocol + doubled task volume + Phase 2 continuation from merged PR #7.

---

## 1. Review of attachments, GitHub, and Jira

### Attachments reviewed

- `Fiverr_009.zip`
- `PM_Pack_Cycle_009_READY(1).zip`

### Repository archive findings

The uploaded `Fiverr_009.zip` shows:

```text
current branch: cycle/009/integration
origin/develop/develop: 657a72d feat(cycle-008): enforce jira story mapping and harden phase 2 contracts (#7)
cycle/009/integration head: 2d23a80 docs(reporting): add cycle 009 steward gate report [Agent D]
working tree: clean
```

The only branch delta over `develop` is:

```text
A docs/cycle_reports/CYCLE_009_AGENT_D.md
```

### Live GitHub findings

Live GitHub confirms PR #7 is closed and merged into `develop`. PR #7 includes the Cycle 009 stewardship addendum, Codex `VALID_FIXED` disposition, successful local validation, CI success, Codecov project/patch success, and a no-main confirmation.

There are currently no open PRs.

### Jira board findings

A broad Jira audit was performed. The key active product areas are:

| Area | Jira keys currently active/relevant |
|---|---|
| Cursor/Jira authority + task volume | SCRUM-252 |
| Jira story-mapping governance | SCRUM-250 |
| Completed Cycle 009 PR #7 gate | SCRUM-251 |
| Collection | SCRUM-149, SCRUM-154, SCRUM-156, with adjacent S2.10-S2.15 tickets available |
| Analysis | SCRUM-163, SCRUM-164, with S3.1-S3.6 tickets still To Do |
| Dashboard/Reporting/Export | SCRUM-212, SCRUM-213, SCRUM-226, SCRUM-228, with S9 page/query/alert tickets still To Do |
| Integration/testing | SCRUM-231, SCRUM-235 and other S10 stories available |

### Rule change requested by operator

The operator confirmed two new permanent PM Pack rules:

1. Cursor agents have full read/write/edit access to Jira when the PM instructs them to use it.
2. Cursor agent task minimum/maximum must be doubled.

This PM Pack update is now tracked by:

```text
SCRUM-252 — [PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits
```

SCRUM-252 was created and moved to In Progress.

---

## 2. Jira updates completed by PM this cycle

| Jira key | Action |
|---|---|
| SCRUM-252 | Created and moved to In Progress. Added Cycle 010 comment documenting Cursor-agent Jira authority and doubled task-volume rule. |
| SCRUM-251 | Moved to Done because PR #7 is merged, Codex thread was resolved, CI/Codecov passed, and the Cycle 009 gate is complete. |
| SCRUM-250 | Left active because the mapping protocol is now permanent and continues to be enforced across cycles. |

---

## 3. PM Pack updates made

The PM Pack now includes/updates:

| File | Change |
|---|---|
| `Project_Manager/04_jira_protocol/CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md` | New standing protocol allowing assigned Cursor agents to perform Jira operations. |
| `Project_Manager/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_010.md` | New cycle rule file for Jira authority and doubled task volume. |
| `Project_Manager/03_cursor_agent_system/TASK_SIZING.md` | Updated to minimum 10, target 12-16, maximum 20 tasks per agent. |
| `Project_Manager/03_cursor_agent_system/PROMPT_RULES.md` | Updated to enforce 10-20 tasks and explicit Jira responsibility in every prompt. |
| `Project_Manager/01_pm_instructions/PM_RULES.md` | Added R-075 through R-078 for Cursor Jira operations and task volume. |
| `Project_Manager/01_pm_instructions/PM_REPLY_CHECKLIST.md` | Updated checklist gates for 10+ tasks, 3,000+ word prompts, and Jira responsibility. |
| `Project_Manager/02_cycle_protocol/CYCLE_WORKFLOW.md` | Updated to load Cursor Jira protocol and allow assigned agent Jira operations. |
| `Project_Manager/03_cursor_agent_system/AGENT_ROSTER.md` | Added Jira access/operations section. |
| `Project_Manager/09_templates/AGENT_PROMPT_*.md` | Updated task range and Jira access section. |

---

## 4. Cycle 010 execution strategy

Cycle 010 should start from merged `develop`.

Agent A should preserve the Cycle 009 steward report if it is not already in `develop`, then create/use `cycle/010/integration`.

Cycle 010 is no longer a narrow repair cycle. It is a high-volume Phase 2 continuation cycle under the new task-sizing standard.

Expected branch flow:

```text
develop -> cycle/010/integration -> PR into develop
```

No direct `main` work is allowed.

---

## 5. Agent prompts

## AGENT A — CYCLE 010 CURSOR PROMPT

### Project context

Project: Fiverr Research System  
Repository: `https://github.com/KevinSGarrett/Fiverr`  
Local repo path: `C:\Fiverr\Fiverr`  
Base branch: `develop`  
Cycle branch: `cycle/010/integration`  
Python: 3.11+  
Current governance: PR #7 is merged into `develop`; Cycle 010 starts clean from `develop`.

### Your role

Infrastructure, integration, branch hygiene, PM/governance protocol support.

Owned area:

`src/config/`, `src/models/`, `src/utils/`, `src/orchestrator.py`, `.github/`, repository governance docs, branch/CI docs.

### Expanded task-volume rule

The PM Pack has been updated in Cycle 010. You must now expect **10-20 substantive tasks per agent** in normal cycles. This prompt assigns 10 substantive tasks. Do not shrink the scope unless you hit a real blocker. If you cannot complete a task, document the exact blocker in your report and continue with non-blocked tasks.

### Jira access and responsibilities

Cursor agents have full read/write/edit access to the connected Jira board when assigned. You may read Jira issues, create issues, add comments, edit issues, and transition statuses **only for the Jira duties explicitly assigned in this prompt**.

This cycle's Jira instruction for you: You must perform Jira audit/comment work for SCRUM-252, SCRUM-250, and any Foundation/Integration tickets directly touched by your files.

Rules:
- Do not mark a broad product story Done unless the full source DOD is satisfied.
- Partial implementation should remain In Progress.
- PR-ready work with checks passing may move to In Review if the prompt assigns that action.
- Every Jira comment must include Cycle 010, your agent name, branch, changed files, validation evidence, and partial/full DOD status.

### Git instructions

1. Start from `develop` unless Agent A has already created `cycle/010/integration`.
2. Work on `cycle/010/integration`.
3. Pull latest before working.
4. Commit only your owned files.
5. Do not push unless you are Agent D and performing final steward duties.
6. Never push or merge to `main`.

### File ownership table

| File path | Owner |
|---|---|
| docs/cycle_reports/CYCLE_009_AGENT_D.md | A |
| docs/cycle_reports/CYCLE_010_AGENT_A.md | A |
| docs/JIRA_CYCLE_STORY_MAPPING.md | A |
| docs/CURSOR_AGENT_JIRA_OPERATIONS.md | A |
| docs/CYCLE_BRANCH_CHECKLIST.md | A |
| docs/PR_CHECKS_AND_CODECOV.md | A |
| docs/BRANCH_PROTECTION_AND_REQUIRED_CHECKS.md | A |
| src/orchestrator.py | A |
| tests/unit/test_orchestrator.py | A |
| src/utils/governance.py | A |
| tests/unit/test_utils.py | A |

### Tasks for this cycle

### Task A1: Start Cycle 010 branch from clean develop and preserve Cycle 009 report evidence

**Jira mapping:** SCRUM-252, SCRUM-250, SCRUM-251

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_009_AGENT_D.md`
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Begin by fetching/pruning origin, checking out `develop`, pulling with `--ff-only`, verifying that PR #7 merge commit is present, and creating or resetting `cycle/010/integration` from `develop`. The uploaded archive shows `cycle/009/integration` contains `docs/cycle_reports/CYCLE_009_AGENT_D.md`; preserve that report in Cycle 010 if it is not already on `develop`. Do not rewrite history. If the report is already present, record that no copy was needed. If the report is missing, copy it into the new branch and include it in Agent A's commit. This task exists because Cycle 009 created a stewardship report after the PR #7 merge gate, and the project must not lose that evidence.

**Validation / tests:**
  - `git status --short --branch`
  - `git log --oneline --decorate -12`
  - `test -f docs/cycle_reports/CYCLE_009_AGENT_D.md`

### Task A2: Update repo-side Jira/Cursor agent authority documentation

**Jira mapping:** SCRUM-252, SCRUM-250

**Files you may create/modify:**
  - `docs/JIRA_CYCLE_STORY_MAPPING.md`
  - `docs/CURSOR_AGENT_JIRA_OPERATIONS.md`
  - `docs/CYCLE_BRANCH_CHECKLIST.md`

**Implementation detail:** Add or update repo documentation that mirrors the PM Pack rule: Cursor agents have read/write/edit Jira access when a prompt assigns Jira duties. Document allowed operations, required guardrails, and status rules. Include exact examples of allowed Jira tasks: reading issue descriptions, posting cycle comments, moving tickets to In Progress/In Review, creating bugs from Codex findings, and maintaining changed-file-to-Jira tables. Also document what is not allowed: marking broad product stories Done for partial scaffold work, closing governance tasks before implementation is merged, or making ambiguous updates without cycle/branch/PR evidence.

**Validation / tests:**
  - `python -m ruff check .`
  - `grep -R "Cursor-agent Jira" -n docs || true`

### Task A3: Update repo-side task-volume documentation to 10-20 tasks per Cursor agent

**Jira mapping:** SCRUM-252

**Files you may create/modify:**
  - `docs/CYCLE_BRANCH_CHECKLIST.md`
  - `docs/PR_CHECKS_AND_CODECOV.md`
  - `docs/BRANCH_PROTECTION_AND_REQUIRED_CHECKS.md`

**Implementation detail:** Document that normal Cursor prompts now contain 10-20 substantive tasks per agent, with 12-16 as the preferred range. This must match the PM Pack and remove any implication that 5-8 tasks is the normal target. Add a note that emergency hotfix or narrow Codex repair cycles may use fewer tasks only with a written `TASK-COUNT WAIVER`. Keep the text practical for agents: this does not mean every task must be huge, but the prompt should provide enough work volume across implementation, tests, docs, Jira, validation, and reporting.

**Validation / tests:**
  - `grep -R "5-8\|3-10\|10-20\|12-16" -n docs | head -50`

### Task A4: Harden integration command documentation for full local parity

**Jira mapping:** SCRUM-231, SCRUM-235, SCRUM-252

**Files you may create/modify:**
  - `docs/CYCLE_BRANCH_CHECKLIST.md`
  - `docs/PR_CHECKS_AND_CODECOV.md`
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Refresh local parity instructions so every cycle explicitly runs Ruff, Mypy, full Pytest with coverage, config-check, foundation-gate, and phase2-smoke. Add the exact commands and note runtime artifacts that must be cleaned after validation. The documentation should align with the existing GitHub Actions check names and Codecov project/patch gates. This is not a code change; it is governance hardening to ensure every agent and steward uses the same validation language.

**Validation / tests:**
  - `python -m ruff check .`
  - `python -m mypy src`
  - `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`

### Task A5: Audit integration and CI Jira tickets and update assigned Jira records directly

**Jira mapping:** SCRUM-231, SCRUM-235, SCRUM-250, SCRUM-252

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Use the connected Jira board directly. Read SCRUM-231, SCRUM-235, SCRUM-250, SCRUM-252 and confirm whether their status reflects current repo reality. Add a concise Cycle 010 Agent A comment to SCRUM-252 confirming the repo-side and PM Pack-side rule update has been implemented in this branch. For SCRUM-231 and SCRUM-235, do not mark Done unless full source DOD is met; if the cycle only improves documentation/validation evidence, leave as To Do or move to In Progress only if implementation starts. Record exact Jira operations in the Agent A report.

**Validation / tests:**
  - `Manual Jira verification through connected Jira`
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md must include Jira operation log`

### Task A6: Add integration smoke metadata contract for phase handoff

**Jira mapping:** SCRUM-231, SCRUM-237

**Files you may create/modify:**
  - `src/orchestrator.py`
  - `tests/unit/test_orchestrator.py`
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** If `src/orchestrator.py` already exposes phase2 smoke/status metadata, extend it minimally to include branch-safe run metadata such as `phase`, `expected_gates`, `jira_mapping_required`, and `codex_disposition_required`. Do not create a large new orchestration framework. This is a small contract layer for future end-to-end pipeline work. If the file structure does not support this cleanly, create a documented placeholder helper rather than forcing an intrusive rewrite. Keep output deterministic and import-safe.

**Validation / tests:**
  - `python -m pytest tests/unit/test_orchestrator.py -q || true`
  - `python run.py phase2-smoke`

### Task A7: Create or update integration evidence helper for Jira-mapped gates

**Jira mapping:** SCRUM-231, SCRUM-250

**Files you may create/modify:**
  - `src/utils/governance.py`
  - `tests/unit/test_utils.py`
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Create a small utility helper only if one does not already exist. The helper should normalize gate evidence dictionaries that include Jira keys, branch, PR number, CI status, Codecov status, Codex status, and DOD status. Keep it generic and reusable by reports/exports without importing dashboard or collection modules. If `src/utils/` already has a better home, use that existing structure. Tests must cover missing Jira keys, invalid status strings, and safe serialization.

**Validation / tests:**
  - `python -m pytest tests/unit/test_utils.py -q || true`
  - `python -m mypy src/utils`

### Task A8: Reconcile Foundation/Integration status without over-closing stories

**Jira mapping:** SCRUM-16, SCRUM-45, SCRUM-135, SCRUM-136, SCRUM-138, SCRUM-139, SCRUM-140

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Use Jira directly to review the Foundation epic and its active stories. Do not bulk transition all Foundation stories. Instead, report which appear still In Progress, which are truly Done, and which need future source-DOD verification. Add comments only to tickets you directly verify or touch. This task is about preventing status drift, not closing work. Include a table in the Agent A report with Jira key, current status, recommended status, and reason.

**Validation / tests:**
  - `Manual Jira audit`
  - `Agent A report contains Foundation/Integration Jira status table`

### Task A9: Prepare branch and PR hygiene instructions for Agent D steward handoff

**Jira mapping:** SCRUM-252, SCRUM-250

**Files you may create/modify:**
  - `docs/CYCLE_BRANCH_CHECKLIST.md`
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Add a small 'Cycle 010 steward handoff' checklist stating that Agent D is expected to run final full validation, verify no overlapping files, verify Jira operations were completed or reported, push `cycle/010/integration`, create/update the PR into `develop`, and handle Codex comments. This should be reusable by future cycles and must not imply direct pushes to `main`. Include the exact no-main policy.

**Validation / tests:**
  - `grep -R "main" -n docs/CYCLE_BRANCH_CHECKLIST.md`
  - `git status --short`

### Task A10: Agent A report and commit

**Jira mapping:** SCRUM-252

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_A.md`

**Implementation detail:** Write a complete report listing every file changed, every Jira issue read/updated/commented, all commands run, validation results, and any blockers. Include a 'Jira Operations Performed' section even if no Jira API changes were possible in the local environment. Commit Agent A work with a clear message. Do not push unless this prompt explicitly grants push responsibility; final push is assigned to Agent D.

**Validation / tests:**
  - `test -f docs/cycle_reports/CYCLE_010_AGENT_A.md`
  - `git diff --check`


### Report requirement

Create or update your Cycle 010 report file under `docs/cycle_reports/`. Include:

- task-by-task completion status,
- Jira operations performed,
- files changed,
- tests/commands run,
- local validation results,
- blockers,
- partial vs full DOD status,
- recommended next Jira/story transitions.

### Commit message

Use:

```bash
git add <your files>
git commit -m "<type>(<scope>): <summary> [Agent A]"
```


## AGENT B — CYCLE 010 CURSOR PROMPT

### Project context

Project: Fiverr Research System  
Repository: `https://github.com/KevinSGarrett/Fiverr`  
Local repo path: `C:\Fiverr\Fiverr`  
Base branch: `develop`  
Cycle branch: `cycle/010/integration`  
Python: 3.11+  
Current governance: PR #7 is merged into `develop`; Cycle 010 starts clean from `develop`.

### Your role

Collection engine engineer.

Owned area:

`src/collection/`, collection tests, collection fixture docs.

### Expanded task-volume rule

The PM Pack has been updated in Cycle 010. You must now expect **10-20 substantive tasks per agent** in normal cycles. This prompt assigns 10 substantive tasks. Do not shrink the scope unless you hit a real blocker. If you cannot complete a task, document the exact blocker in your report and continue with non-blocked tasks.

### Jira access and responsibilities

Cursor agents have full read/write/edit access to the connected Jira board when assigned. You may read Jira issues, create issues, add comments, edit issues, and transition statuses **only for the Jira duties explicitly assigned in this prompt**.

This cycle's Jira instruction for you: You must directly update Collection Jira tickets for code you touch: SCRUM-149 through SCRUM-156 as applicable. Do not mark any broad story Done.

Rules:
- Do not mark a broad product story Done unless the full source DOD is satisfied.
- Partial implementation should remain In Progress.
- PR-ready work with checks passing may move to In Review if the prompt assigns that action.
- Every Jira comment must include Cycle 010, your agent name, branch, changed files, validation evidence, and partial/full DOD status.

### Git instructions

1. Start from `develop` unless Agent A has already created `cycle/010/integration`.
2. Work on `cycle/010/integration`.
3. Pull latest before working.
4. Commit only your owned files.
5. Do not push unless you are Agent D and performing final steward duties.
6. Never push or merge to `main`.

### File ownership table

| File path | Owner |
|---|---|
| src/collection/orchestrator.py | B |
| src/collection/contracts.py | B |
| tests/unit/test_collection.py | B |
| docs/cycle_reports/CYCLE_010_AGENT_B.md | B |
| src/collection/checkpoint.py | B |
| tests/integration/test_collection_e2e.py | B |
| docs/collection_fixture_contract.md | B |
| src/collection/gig_detail.py | B |

### Tasks for this cycle

### Task B1: Advance S2.14 collection stage orchestration beyond invariant scaffolding

**Jira mapping:** SCRUM-154

**Files you may create/modify:**
  - `src/collection/orchestrator.py`
  - `src/collection/contracts.py`
  - `tests/unit/test_collection.py`
  - `docs/cycle_reports/CYCLE_010_AGENT_B.md`

**Implementation detail:** Build on the fixed stage-summary contract from PR #7. Add deterministic orchestration metadata for stage start/end, skipped stages, failed stages, and resumable stage identity. Preserve the rule that `stage_names` is execution order and `stage_counts` is unordered count evidence. Do not introduce live Fiverr access. Fixtures only. The implementation should make it easier to prove stage order without relying on dictionary ordering.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py -q`
  - `python -m mypy src/collection`

### Task B2: Add checkpoint/resume regression coverage for collection dry runs

**Jira mapping:** SCRUM-154, SCRUM-156

**Files you may create/modify:**
  - `src/collection/checkpoint.py`
  - `tests/unit/test_collection.py`
  - `tests/integration/test_collection_e2e.py`

**Implementation detail:** Add tests proving checkpoint save/load retains semantic stage summary validity even if JSON serialization sorts mapping keys. Include tests for a paused dry-run, a resumed dry-run, and a corrupted checkpoint fallback if current abstractions support it. If checkpoint restore is not fully implemented, create tests around the existing checkpoint helper contract and document remaining gaps in Agent B report.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py tests/integration/test_collection_e2e.py -q`

### Task B3: Strengthen fixture-backed end-to-end collection smoke report

**Jira mapping:** SCRUM-156

**Files you may create/modify:**
  - `tests/integration/test_collection_e2e.py`
  - `docs/collection_fixture_contract.md`
  - `docs/cycle_reports/CYCLE_010_AGENT_B.md`

**Implementation detail:** Expand fixture-backed collection smoke assertions so the run validates keyword expansion, search-result fixture ingestion, gig detail fixture boundaries, seller placeholder or skip behavior, and external-signal placeholder or skip behavior. The smoke test should clearly distinguish implemented stages from safe skips. Keep it deterministic and offline.

**Validation / tests:**
  - `python -m pytest tests/integration/test_collection_e2e.py -q`

### Task B4: Harden gig-detail extraction boundary cases

**Jira mapping:** SCRUM-149

**Files you may create/modify:**
  - `src/collection/gig_detail.py`
  - `tests/unit/test_collection.py`

**Implementation detail:** Add targeted extraction tests for nested markup, missing data-testid, repeated data-testid, malformed HTML fragments, whitespace-only text, and safe fallback behavior. Keep extraction deterministic and avoid browser/network dependencies. If the helper is intentionally limited, document the limit in code comments and tests rather than silently over-parsing.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py -q`

### Task B5: Add seller-profile placeholder boundary for Stage 5 readiness

**Jira mapping:** SCRUM-150, SCRUM-154

**Files you may create/modify:**
  - `src/collection/orchestrator.py`
  - `src/collection/contracts.py`
  - `tests/unit/test_collection.py`

**Implementation detail:** Add an explicit stage summary placeholder for seller-profile collection if not already present. It should report implemented/skipped/blocked status, records_seen, records_written, and a warning when fixture data does not include seller profile detail. Do not implement live seller scraping. The goal is clear stage accounting for later S2.10 work.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py -q`

### Task B6: Add external-signal placeholder boundary for Stage 6a/6b readiness

**Jira mapping:** SCRUM-151, SCRUM-152, SCRUM-154

**Files you may create/modify:**
  - `src/collection/orchestrator.py`
  - `src/collection/contracts.py`
  - `tests/unit/test_collection.py`

**Implementation detail:** Add explicit, safe, fixture-only accounting for Google Trends and Reddit/external signal stages. When no fixture source is present, the stage should be skipped with warnings and zero counts rather than pretending success. Preserve data hygiene: no personal data, no live external calls, no uncontrolled request volume.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py -q`

### Task B7: Add autocomplete stage accounting for Stage 2b readiness

**Jira mapping:** SCRUM-153, SCRUM-154

**Files you may create/modify:**
  - `src/collection/orchestrator.py`
  - `src/collection/contracts.py`
  - `tests/unit/test_collection.py`

**Implementation detail:** Add or improve autocomplete collection accounting so the orchestrator can represent suggestions as fixture-backed outputs or safe skips. Validate dedupe metadata when fixture suggestions exist. Do not call live autocomplete APIs. Ensure stage names remain stable and are included in execution order.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py -q`

### Task B8: Add auto-promotion dry-run decision placeholder

**Jira mapping:** SCRUM-155, SCRUM-154

**Files you may create/modify:**
  - `src/collection/orchestrator.py`
  - `src/collection/contracts.py`
  - `tests/unit/test_collection.py`

**Implementation detail:** Create a deterministic placeholder for auto-promotion collection decisions that records criteria evaluated, decision status, and lineage fields when fixture data supports it. This is not full S2.15; it is a readiness contract. The placeholder must make clear whether auto-promotion is implemented, skipped, or blocked.

**Validation / tests:**
  - `python -m pytest tests/unit/test_collection.py -q`

### Task B9: Perform Collection Jira operations directly

**Jira mapping:** SCRUM-149, SCRUM-150, SCRUM-151, SCRUM-152, SCRUM-153, SCRUM-154, SCRUM-155, SCRUM-156

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_B.md`

**Implementation detail:** Use Jira directly. Read each listed Collection ticket, then add a Cycle 010 Agent B comment to the tickets touched by code changes. Move To Do tickets to In Progress only when this branch starts real partial implementation for that story. Do not mark Done. If a ticket is only referenced as future readiness and no code changes directly advance it, record it in the report but do not transition it.

**Validation / tests:**
  - `Manual Jira operations`
  - `Agent B report includes Jira operations log`

### Task B10: Run full collection validation and write Agent B report

**Jira mapping:** SCRUM-154, SCRUM-156

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_B.md`

**Implementation detail:** Run targeted collection tests, then full test/coverage if time allows. Write a report with changed files, Jira operations, test results, limitations, and next recommended Collection stories. Commit with a clear Agent B message. Do not push unless assigned by Agent D.

**Validation / tests:**
  - `python -m ruff check src/collection tests/unit/test_collection.py tests/integration/test_collection_e2e.py`
  - `python -m mypy src/collection`
  - `python -m pytest tests/unit/test_collection.py tests/integration/test_collection_e2e.py -q`


### Report requirement

Create or update your Cycle 010 report file under `docs/cycle_reports/`. Include:

- task-by-task completion status,
- Jira operations performed,
- files changed,
- tests/commands run,
- local validation results,
- blockers,
- partial vs full DOD status,
- recommended next Jira/story transitions.

### Commit message

Use:

```bash
git add <your files>
git commit -m "<type>(<scope>): <summary> [Agent B]"
```


## AGENT C — CYCLE 010 CURSOR PROMPT

### Project context

Project: Fiverr Research System  
Repository: `https://github.com/KevinSGarrett/Fiverr`  
Local repo path: `C:\Fiverr\Fiverr`  
Base branch: `develop`  
Cycle branch: `cycle/010/integration`  
Python: 3.11+  
Current governance: PR #7 is merged into `develop`; Cycle 010 starts clean from `develop`.

### Your role

Analysis, scoring-readiness, recommendation/pricing/discovery interface engineer.

Owned area:

`src/analysis/`, `src/scoring/`, `src/llm/`, `src/pricing/`, `src/discovery/` and their tests.

### Expanded task-volume rule

The PM Pack has been updated in Cycle 010. You must now expect **10-20 substantive tasks per agent** in normal cycles. This prompt assigns 11 substantive tasks. Do not shrink the scope unless you hit a real blocker. If you cannot complete a task, document the exact blocker in your report and continue with non-blocked tasks.

### Jira access and responsibilities

Cursor agents have full read/write/edit access to the connected Jira board when assigned. You may read Jira issues, create issues, add comments, edit issues, and transition statuses **only for the Jira duties explicitly assigned in this prompt**.

This cycle's Jira instruction for you: You must directly update Analysis Jira tickets for code you touch: SCRUM-157 through SCRUM-164 as applicable. Mention scoring tickets only when directly affected.

Rules:
- Do not mark a broad product story Done unless the full source DOD is satisfied.
- Partial implementation should remain In Progress.
- PR-ready work with checks passing may move to In Review if the prompt assigns that action.
- Every Jira comment must include Cycle 010, your agent name, branch, changed files, validation evidence, and partial/full DOD status.

### Git instructions

1. Start from `develop` unless Agent A has already created `cycle/010/integration`.
2. Work on `cycle/010/integration`.
3. Pull latest before working.
4. Commit only your owned files.
5. Do not push unless you are Agent D and performing final steward duties.
6. Never push or merge to `main`.

### File ownership table

| File path | Owner |
|---|---|
| src/analysis/orchestrator.py | C |
| tests/unit/test_analysis.py | C |
| docs/cycle_reports/CYCLE_010_AGENT_C.md | C |

### Tasks for this cycle

### Task C1: Advance analysis stage wiring from readiness contracts toward usable Stage 7-9 summaries

**Jira mapping:** SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`
  - `docs/cycle_reports/CYCLE_010_AGENT_C.md`

**Implementation detail:** Continue S3.8 by refining deterministic stage summaries for gig quality, competitor profiling, and keyword clustering readiness. Keep outputs fixture-safe and local-only. Add metadata for stage status, source availability, warning_count, missing_field_count, and explanation. Do not call live LLMs.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C2: Improve intent classification schema boundaries

**Jira mapping:** SCRUM-163

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Build on existing intent fallback logic by adding a small structured result shape for selected keyword, selection reason, confidence bucket, and missing-input warnings. This is partial S3.7, not full LLM classification. Add tests for valid explicit intent, fallback to keyword_text, fallback to keywords array, fallback to source_id, and missing all fields.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C3: Add keyword clustering placeholder contract

**Jira mapping:** SCRUM-157, SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Create or refine a deterministic placeholder for keyword clustering readiness. The helper should return empty/sparse/ready status without performing embeddings if no clustering engine exists. Include expected future fields such as cluster_id, label, member_count, confidence, and source keywords. Tests should verify sparse inputs degrade safely.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C4: Add gig quality analysis placeholder contract

**Jira mapping:** SCRUM-158, SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Create a deterministic gig quality placeholder that summarizes title/description/package completeness when fixture data is available. Do not implement full rubric scoring if the model is not ready; instead define explicit readiness and warning output. Tests should cover complete, sparse, missing, and malformed gig fixture input.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C5: Add competitor profiling placeholder contract

**Jira mapping:** SCRUM-159, SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Add a competitor profiling readiness helper that can summarize competitor count, missing seller context, and weakness-signal availability. Keep it deterministic and do not generate ungrounded narratives. Tests must ensure no fabricated competitor insights appear when upstream data is missing.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C6: Add seller strength readiness placeholder

**Jira mapping:** SCRUM-160, SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Add a seller strength readiness placeholder that reports whether seller profile fields are available, which fields are missing, and whether downstream seller strength scoring is blocked or ready. This should align with Agent B seller-profile placeholder stage and not import collection code directly.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C7: Add saturation model readiness placeholder

**Jira mapping:** SCRUM-161, SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Add a saturation readiness placeholder that looks at available keyword/gig/competitor count signals and returns blocked/sparse/ready status with explanation. Do not implement final saturation math unless existing code already supports it. Tests must cover no competitors, one competitor, and sufficient competitor fixture counts.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C8: Add review analysis readiness placeholder

**Jira mapping:** SCRUM-162, SCRUM-164

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`

**Implementation detail:** Add a review analysis readiness placeholder that distinguishes missing reviews, sparse snippets, and usable review fixtures. Do not attempt sentiment analysis unless deterministic fixtures already support it. Output should include warning_count and safe explanation fields.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C9: Map analysis readiness to future scoring input contracts

**Jira mapping:** SCRUM-165, SCRUM-166, SCRUM-167, SCRUM-174

**Files you may create/modify:**
  - `src/analysis/orchestrator.py`
  - `tests/unit/test_analysis.py`
  - `docs/cycle_reports/CYCLE_010_AGENT_C.md`

**Implementation detail:** Add documentation or helper output showing which analysis readiness fields will feed demand, competition, opportunity, and confidence scoring later. This must not implement scoring in `src/analysis/`; it should only make the interface explicit enough for future Agent C scoring work.

**Validation / tests:**
  - `python -m pytest tests/unit/test_analysis.py -q`

### Task C10: Perform Analysis/Scoring Jira operations directly

**Jira mapping:** SCRUM-157, SCRUM-158, SCRUM-159, SCRUM-160, SCRUM-161, SCRUM-162, SCRUM-163, SCRUM-164

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_C.md`

**Implementation detail:** Use Jira directly. Read the Analysis tickets listed above. Add Cycle 010 comments and transition to In Progress only for stories advanced by actual code changes. Do not mark Done. Include any future Scoring tickets referenced by interface mapping as noted/not transitioned unless code directly changes scoring.

**Validation / tests:**
  - `Manual Jira operations`
  - `Agent C report includes Jira operations log`

### Task C11: Run validation and write Agent C report

**Jira mapping:** SCRUM-164

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_C.md`

**Implementation detail:** Run targeted analysis tests plus Ruff/Mypy on analysis code. If full coverage is run, report the percentage. The report must include changed files, Jira operations, tests, partial vs full DOD status, and next recommended analysis/scoring sequence. Commit with an Agent C message.

**Validation / tests:**
  - `python -m ruff check src/analysis tests/unit/test_analysis.py`
  - `python -m mypy src/analysis`
  - `python -m pytest tests/unit/test_analysis.py -q`


### Report requirement

Create or update your Cycle 010 report file under `docs/cycle_reports/`. Include:

- task-by-task completion status,
- Jira operations performed,
- files changed,
- tests/commands run,
- local validation results,
- blockers,
- partial vs full DOD status,
- recommended next Jira/story transitions.

### Commit message

Use:

```bash
git add <your files>
git commit -m "<type>(<scope>): <summary> [Agent C]"
```


## AGENT D — CYCLE 010 CURSOR PROMPT

### Project context

Project: Fiverr Research System  
Repository: `https://github.com/KevinSGarrett/Fiverr`  
Local repo path: `C:\Fiverr\Fiverr`  
Base branch: `develop`  
Cycle branch: `cycle/010/integration`  
Python: 3.11+  
Current governance: PR #7 is merged into `develop`; Cycle 010 starts clean from `develop`.

### Your role

Dashboard, reporting, export, playbook, and final GitHub steward.

Owned area:

`src/dashboard/`, `src/reports/`, `src/exports/`, `src/playbook/`, dashboard/report/export tests, final PR stewardship.

### Expanded task-volume rule

The PM Pack has been updated in Cycle 010. You must now expect **10-20 substantive tasks per agent** in normal cycles. This prompt assigns 11 substantive tasks. Do not shrink the scope unless you hit a real blocker. If you cannot complete a task, document the exact blocker in your report and continue with non-blocked tasks.

### Jira access and responsibilities

Cursor agents have full read/write/edit access to the connected Jira board when assigned. You may read Jira issues, create issues, add comments, edit issues, and transition statuses **only for the Jira duties explicitly assigned in this prompt**.

This cycle's Jira instruction for you: You must directly update Dashboard/Reporting/Export Jira tickets for code you touch and perform final PR/Jira steward duties.

Rules:
- Do not mark a broad product story Done unless the full source DOD is satisfied.
- Partial implementation should remain In Progress.
- PR-ready work with checks passing may move to In Review if the prompt assigns that action.
- Every Jira comment must include Cycle 010, your agent name, branch, changed files, validation evidence, and partial/full DOD status.

### Git instructions

1. Start from `develop` unless Agent A has already created `cycle/010/integration`.
2. Work on `cycle/010/integration`.
3. Pull latest before working.
4. Commit only your owned files.
5. Do not push unless you are Agent D and performing final steward duties.
6. Never push or merge to `main`.

### File ownership table

| File path | Owner |
|---|---|
| src/dashboard/app.py | D |
| tests/unit/test_dashboard.py | D |
| docs/cycle_reports/CYCLE_010_AGENT_D.md | D |
| src/reports/placeholders.py | D |
| tests/unit/test_reports.py | D |
| src/exports/manifest.py | D |
| src/exports/placeholders.py | D |

### Tasks for this cycle

### Task D1: Advance Dashboard governance presentation into reusable page-ready state

**Jira mapping:** SCRUM-212, SCRUM-213, SCRUM-228

**Files you may create/modify:**
  - `src/dashboard/app.py`
  - `tests/unit/test_dashboard.py`
  - `docs/cycle_reports/CYCLE_010_AGENT_D.md`

**Implementation detail:** Build on existing governance status helpers by adding page-ready plain-dict structures for Jira mapping, Codex disposition, CI, Codecov, and merge readiness. Keep module import-safe without Streamlit side effects. Add tests for missing categories, warning severities, and deterministic ordering.

**Validation / tests:**
  - `python -m pytest tests/unit/test_dashboard.py -q`

### Task D2: Create dashboard query-layer placeholder for active story data

**Jira mapping:** SCRUM-225, SCRUM-213

**Files you may create/modify:**
  - `src/dashboard/app.py`
  - `src/reports/placeholders.py`
  - `tests/unit/test_dashboard.py`
  - `tests/unit/test_reports.py`

**Implementation detail:** Add a query-layer placeholder that can return active Jira-mapped story groups from fixture/report data. It should not call Jira live; it should consume structured evidence from reports/manifests. This supports future dashboard pages while remaining local and deterministic.

**Validation / tests:**
  - `python -m pytest tests/unit/test_dashboard.py tests/unit/test_reports.py -q`

### Task D3: Improve report Jira mapping table helper

**Jira mapping:** SCRUM-213, SCRUM-228, SCRUM-250, SCRUM-252

**Files you may create/modify:**
  - `src/reports/placeholders.py`
  - `tests/unit/test_reports.py`

**Implementation detail:** Extend the Jira mapping table helper to include agent, cycle, branch, PR, DOD status, and whether Jira was updated by PM or Cursor agent. Validate that each row includes Jira keys or an explicit not-applicable reason. Tests must cover missing keys, duplicate keys, and mixed product/governance mapping.

**Validation / tests:**
  - `python -m pytest tests/unit/test_reports.py -q`

### Task D4: Improve export manifest governance metadata

**Jira mapping:** SCRUM-226, SCRUM-250, SCRUM-252

**Files you may create/modify:**
  - `src/exports/manifest.py`
  - `src/exports/placeholders.py`
  - `tests/unit/test_reports.py`

**Implementation detail:** Extend export manifest metadata to include cursor_jira_operations_performed, agent_task_count, jira_mapping_complete, and task_count_waiver fields. Keep it secret-safe and deterministic. If no manifest module exists, extend the existing placeholder export model. Tests must reject incomplete governance metadata.

**Validation / tests:**
  - `python -m pytest tests/unit/test_reports.py -q`

### Task D5: Add Opportunities page placeholder support

**Jira mapping:** SCRUM-214, SCRUM-213

**Files you may create/modify:**
  - `src/dashboard/app.py`
  - `tests/unit/test_dashboard.py`

**Implementation detail:** Add a safe page descriptor or placeholder model for the Opportunities dashboard page. Do not implement final UI; create plain metadata that supports future top-opportunity cards/tables, score/confidence placeholders, and empty states. Tests should verify descriptor presence and safe missing data behavior.

**Validation / tests:**
  - `python -m pytest tests/unit/test_dashboard.py -q`

### Task D6: Add Keywords page placeholder support

**Jira mapping:** SCRUM-215, SCRUM-213

**Files you may create/modify:**
  - `src/dashboard/app.py`
  - `tests/unit/test_dashboard.py`

**Implementation detail:** Add a safe page descriptor or placeholder model for the Keywords dashboard page with columns for keyword, niche, cluster, score, confidence, and freshness status. Keep it deterministic and import-safe. Tests should verify descriptor presence and default empty state.

**Validation / tests:**
  - `python -m pytest tests/unit/test_dashboard.py -q`

### Task D7: Add Run History page placeholder support

**Jira mapping:** SCRUM-219, SCRUM-213

**Files you may create/modify:**
  - `src/dashboard/app.py`
  - `tests/unit/test_dashboard.py`

**Implementation detail:** Add a safe page descriptor or placeholder model for Run History, including run_id, branch, PR, status, stages, warning_count, duration placeholder, and validation status. Tests should ensure missing data produces empty-state metadata, not exceptions.

**Validation / tests:**
  - `python -m pytest tests/unit/test_dashboard.py -q`

### Task D8: Add alert-system readiness placeholder

**Jira mapping:** SCRUM-227, SCRUM-213

**Files you may create/modify:**
  - `src/dashboard/app.py`
  - `tests/unit/test_dashboard.py`

**Implementation detail:** Add a deterministic alert placeholder contract for warning/error/governance alerts. This is not full S9.13 implementation. It should define alert severity, source, Jira key, message, and resolution status. Tests should cover unknown severity and missing Jira keys.

**Validation / tests:**
  - `python -m pytest tests/unit/test_dashboard.py -q`

### Task D9: Perform Dashboard/Reporting/Export Jira operations directly

**Jira mapping:** SCRUM-212, SCRUM-213, SCRUM-214, SCRUM-215, SCRUM-219, SCRUM-225, SCRUM-226, SCRUM-227, SCRUM-228, SCRUM-250, SCRUM-252

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_D.md`

**Implementation detail:** Use Jira directly. Read the listed Dashboard/Reporting/Export tickets. Add Cycle 010 comments and transition to In Progress only for tickets advanced by actual code changes. Do not mark Done unless full source DOD is satisfied. Record all Jira operations in the report.

**Validation / tests:**
  - `Manual Jira operations`
  - `Agent D report includes Jira operations log`

### Task D10: Final GitHub steward duties

**Jira mapping:** SCRUM-252, SCRUM-250

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_D.md`

**Implementation detail:** After Agents A/B/C complete and commit, run full validation, verify no open Codex issues, verify Codecov project/patch status after push, push `cycle/010/integration`, and create the PR into `develop`. You are the only agent assigned final push/PR duties this cycle. Do not touch main. If Codex comments appear, disposition every thread before merge.

**Validation / tests:**
  - `python -m ruff check .`
  - `python -m mypy src`
  - `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
  - `python run.py config-check`
  - `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle010.db`
  - `python run.py phase2-smoke`

### Task D11: Write final Cycle 010 steward report

**Jira mapping:** SCRUM-252, SCRUM-250

**Files you may create/modify:**
  - `docs/cycle_reports/CYCLE_010_AGENT_D.md`

**Implementation detail:** Write the final report with local validation, GitHub push/PR status, Codex status, Codecov status, Jira operation summary, changed-files-to-Jira table, and no-main confirmation. Include whether SCRUM-252 can move to In Review/Done after the PM Pack and repo documentation changes are merged.

**Validation / tests:**
  - `test -f docs/cycle_reports/CYCLE_010_AGENT_D.md`
  - `git diff --check`


### Report requirement

Create or update your Cycle 010 report file under `docs/cycle_reports/`. Include:

- task-by-task completion status,
- Jira operations performed,
- files changed,
- tests/commands run,
- local validation results,
- blockers,
- partial vs full DOD status,
- recommended next Jira/story transitions.

### Commit message

Use:

```bash
git add <your files>
git commit -m "<type>(<scope>): <summary> [Agent D]"
```


---

## 6. Final GitHub / PR policy for Cycle 010

- Agent D is the final GitHub steward unless explicitly changed.
- Agent D pushes `cycle/010/integration`.
- Agent D opens a PR into `develop`.
- Agent D verifies GitHub Actions, Codecov project, Codecov patch, and Codex threads.
- Every Codex thread must be dispositioned before merge.
- No direct `main` changes.

## 7. State update

Cycle 010 starts after PR #7 merged cleanly. The PM Pack now recognizes Cursor agents as Jira-capable execution agents when explicitly instructed, and the normal work-volume range is now 10-20 tasks per agent.

## 8. Next cycle preview

Cycle 011 should review PR #8 or the Cycle 010 PR, validate Codex/CI/Codecov/Jira mapping, merge if clean, and continue into deeper Collection, Analysis, Dashboard Query Layer, and Export/System integration work.
