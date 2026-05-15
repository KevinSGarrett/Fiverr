# FILE REGISTRY
# Every file in the PM Pack with path, purpose, and load frequency

---

## 00_index/ — Navigation

| File | Purpose | Load |
|---|---|---|
| 00_index/MASTER_INDEX.md | Entry point, navigation hub, pack structure | always |
| 00_index/FILE_REGISTRY.md | This file — complete file listing | on-demand |
| 00_index/QUICK_NAV.md | "I need X → go to Y" lookup | on-demand |

## 01_pm_instructions/ — PM Rules

| File | Purpose | Load |
|---|---|---|
| 01_pm_instructions/PM_ROLE.md | PM identity, responsibilities, authority | once per session |
| 01_pm_instructions/PM_RULES.md | All 74 mandatory rules across 8 categories | always |
| 01_pm_instructions/PM_REPLY_CHECKLIST.md | 34 gate items before every reply | always |
| 01_pm_instructions/PM_DECISION_FRAMEWORK.md | Priority/scope decision logic | on-demand |

## 02_cycle_protocol/ — Cycle Management

| File | Purpose | Load |
|---|---|---|
| 02_cycle_protocol/CYCLE_WORKFLOW.md | 8-phase step-by-step cycle process | always |
| 02_cycle_protocol/CYCLE_NAMING.md | Naming rules for cycles, zips, branches | on-demand |
| 02_cycle_protocol/PACK_UPDATE_PROTOCOL.md | Which files update every cycle vs when relevant | always |
| 02_cycle_protocol/PR_BATCH_STRATEGY.md | All 4 agents on single integration branch, 1 PR | always |

## 03_cursor_agent_system/ — Agent Prompts

| File | Purpose | Load |
|---|---|---|
| 03_cursor_agent_system/AGENT_ROSTER.md | 4 agents: roles, epic ownership, owned dirs | on-demand |
| 03_cursor_agent_system/PROMPT_TEMPLATE.md | Mandatory template with 15 validation rules | always |
| 03_cursor_agent_system/PROMPT_RULES.md | Prohibited patterns, required specificity | always |
| 03_cursor_agent_system/TASK_SIZING.md | 20-40 tasks/agent/cycle rule, waiver protocol, substantive-task definition | always |

## 04_jira_protocol/ — Jira Management

| File | Purpose | Load |
|---|---|---|
| 04_jira_protocol/JIRA_RULES.md | Exhaustive Jira management rules | when updating Jira |
| 04_jira_protocol/JIRA_UPDATE_CHECKLIST.md | 15-item checklist for every Jira update | when updating Jira |
| 04_jira_protocol/JIRA_FIELD_STANDARDS.md | Summary formats, description template | on-demand |
| 04_jira_protocol/JIRA_COMMENT_PROTOCOL.md | 10 comment triggers with exact templates | on-demand |
| 04_jira_protocol/FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md | Jira-first planning and AC/DoD ledger protocol | always |
| 04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md | Changed-file and Jira-story mapping with board-first addendum | always |

## 05_github_protocol/ — GitHub Management

| File | Purpose | Load |
|---|---|---|
| 05_github_protocol/GITHUB_RULES.md | PM GitHub responsibilities, key rules | when managing repo |
| 05_github_protocol/BRANCH_WORKFLOW.md | Step-by-step branch creation, push, PR, merge | always |
| 05_github_protocol/PR_CYCLE_BATCH.md | PR body template listing all 4 agents | always |
| 05_github_protocol/MERGE_PROTOCOL.md | Merge conditions, CI failure handling | on-demand |

## 06_review_and_qa/ — Review System

| File | Purpose | Load |
|---|---|---|
| 06_review_and_qa/REVIEW_CHECKLIST.md | 25+ items PM checks for each agent | when reviewing |
| 06_review_and_qa/QA_GATES.md | 6 pass/fail gates at multiple levels | when reviewing |
| 06_review_and_qa/AGENT_REVIEW_PROTOCOL.md | Step-by-step review per agent type | when reviewing |
| 06_review_and_qa/CONFIDENCE_SCORING.md | 0-100 scoring rubric, thresholds | when reviewing |

## 07_hydration/ — Anti-Drift

| File | Purpose | Load |
|---|---|---|
| 07_hydration/HYDRATION_HEADER.md | Compact context block — paste every cycle | always (first) |
| 07_hydration/STATE_SNAPSHOT.md | Full project state — updated each cycle | always |
| 07_hydration/DRIFT_PREVENTION.md | 10 drift signals, correction protocol | on-demand |
| 07_hydration/REHYDRATION_PROTOCOL.md | Full context recovery from pack files | on-demand |

## 08_task_queue/ — Planning

| File | Purpose | Load |
|---|---|---|
| 08_task_queue/TASK_BACKLOG.md | All 601 tasks with status tracking | on-demand |
| 08_task_queue/DEPENDENCY_MAP.md | Story-level dependencies across epics | when planning |
| 08_task_queue/CYCLE_PLANNER.md | Logic for selecting tasks each cycle | always |
| 08_task_queue/EPIC_STATUS_TRACKER.md | Epic/story completion percentages | always |

## 09_templates/ — Templates

| File | Purpose | Load |
|---|---|---|
| 09_templates/CYCLE_REPLY_TEMPLATE.md | Full PM reply structure template | always |
| 09_templates/AGENT_PROMPT_A.md | Pre-filled template for Agent A | when generating |
| 09_templates/AGENT_PROMPT_B.md | Pre-filled template for Agent B | when generating |
| 09_templates/AGENT_PROMPT_C.md | Pre-filled template for Agent C | when generating |
| 09_templates/AGENT_PROMPT_D.md | Pre-filled template for Agent D | when generating |
| 09_templates/JIRA_UPDATE_TEMPLATE.md | Jira update block format | when updating Jira |
| 09_templates/REVIEW_REPORT_TEMPLATE.md | Review report format | when reviewing |

## 10_cycle_log/ — History

| File | Purpose | Load |
|---|---|---|
| 10_cycle_log/CYCLE_000_INIT.md | Initial state — cycle 0 | once |

## ref/ — Reference Library (read-only)

| File | Purpose | Load |
|---|---|---|
| ref/REF_INDEX.md | Master index of all reference files with directory summaries | on-demand |
| ref/SECTION_INDEX.md | File sizes, token estimates, load-by-section rules | before loading large files |
| ref/TOPIC_MAP.md | Reverse lookup: "topic X" -> load these files | when deciding what to load |
| ref/CHUNK_GUIDE.md | Token-efficient loading recipes per epic | every cycle (prompt gen) |
| ref/project_plan/**/*.md | 74 project spec documents | on-demand (by spec) |
| ref/todo/*.md | 11 task files (10 epics + schedule) | on-demand (by epic) |
| ref/dod/*.md | 10 DOD files | on-demand (by epic) |
| ref/github/**/*.md | 47 GitHub setup files | on-demand |

## Cycle 005 Governance Additions
- `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md` — permanent rules for reviewing, fixing, ignoring, replying to, and resolving Codex PR comments.
- `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md` — permanent PR checks, GitHub Actions, Codecov >=90%, branch protection, and steward checklist.

- `05_github_protocol/CODEX_PR_GATE_CYCLE_009.md` — Cycle 009 Codex blocker handling for PR #7.

- `04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md` — Mandatory changed-files-to-Jira-story mapping protocol.

- `04_jira_protocol/CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md` — Cursor-agent Jira read/write/edit authority and guardrails.
- `01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_010.md` — Cycle 010 rule changes for Jira authority and doubled task volume.
- `01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_012.md` — Cycle 012 board-first, AC/DoD-first, and prompt-depth enforcement.
- `10_cycle_log/CYCLE_011.md` — Cycle 011 PM response and agent prompts.
- `CYCLE_011_PM_RESPONSE.md` — Copy of Cycle 011 PM response.
