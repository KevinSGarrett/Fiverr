# MASTER INDEX
# Fiverr Research System — Project Manager Pack
# READ THIS FILE FIRST ON EVERY CYCLE

---

## How to Use This Pack

1. **Start here** — This file is your navigation hub
2. **Load HYDRATION_HEADER.md** (07_hydration/) — Paste into your context every cycle
3. **Load STATE_SNAPSHOT.md** (07_hydration/) — Know where we are
4. **Load FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md** (04_jira_protocol/) — Perform Jira-first board inventory and AC/DoD selection
5. **Load CYCLE_PLANNER.md** (08_task_queue/) — Allocate selected Jira scope to agents
6. **Generate agent prompts** using PROMPT_TEMPLATE.md (03_cursor_agent_system/)
7. **After agent work** — Follow REVIEW_CHECKLIST.md (06_review_and_qa/)
8. **Update Jira** — Follow JIRA_UPDATE_CHECKLIST.md (04_jira_protocol/)
9. **Update state** — Update STATE_SNAPSHOT.md + CYCLE_LOG

---

## Pack Structure

```
C:\Fiverr1\Project_Manager\
├── WAVE_SCHEDULE.md              ← Build plan for this pack
├── 00_index/                     ← Navigation & file registry
│   ├── MASTER_INDEX.md           ← Start here every cycle
│   ├── FILE_REGISTRY.md          ← Every file with path + description
│   └── QUICK_NAV.md              ← "I need X" → go to Y
├── 01_pm_instructions/           ← PM behavioral rules
│   ├── PM_ROLE.md                ← What the PM is and does
│   ├── PM_RULES.md               ← 74 mandatory rules every cycle
│   ├── PM_REPLY_CHECKLIST.md     ← 34 gate checklist before sending reply
│   └── PM_DECISION_FRAMEWORK.md  ← Priority, sequencing, scope decisions
├── 02_cycle_protocol/            ← How cycles work
│   ├── CYCLE_WORKFLOW.md         ← 8-phase step-by-step cycle flow
│   ├── CYCLE_NAMING.md           ← Naming conventions
│   ├── PACK_UPDATE_PROTOCOL.md   ← Rules for updating pack
│   └── PR_BATCH_STRATEGY.md      ← Batch 4 agents into 1 PR
├── 03_cursor_agent_system/       ← Agent prompts
│   ├── AGENT_ROSTER.md           ← 4 agents: roles, ownership
│   ├── PROMPT_TEMPLATE.md        ← Mandatory prompt template (15 validation rules)
│   ├── PROMPT_RULES.md           ← Rules preventing shallow prompts
│   └── TASK_SIZING.md            ← Work volume per agent per cycle
├── 04_jira_protocol/             ← Jira management
│   ├── JIRA_RULES.md             ← Exhaustive Jira rules
│   ├── JIRA_UPDATE_CHECKLIST.md  ← 15-item checklist for every update
│   ├── JIRA_FIELD_STANDARDS.md   ← Required fields and formats
│   ├── JIRA_COMMENT_PROTOCOL.md  ← 10 comment triggers with templates
│   ├── FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md ← Jira-first board planning + AC/DoD ledger
│   └── JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md ← file/story mapping with Cycle 012 addendum
├── 05_github_protocol/           ← GitHub management
│   ├── GITHUB_RULES.md           ← GitHub rules for PM
│   ├── BRANCH_WORKFLOW.md        ← Branch lifecycle per cycle
│   ├── PR_CYCLE_BATCH.md         ← Batched PR strategy
│   └── MERGE_PROTOCOL.md         ← Merge conditions
├── 06_review_and_qa/             ← PM review system
│   ├── REVIEW_CHECKLIST.md       ← What PM checks
│   ├── QA_GATES.md               ← Pass/fail gates
│   ├── AGENT_REVIEW_PROTOCOL.md  ← Review process per agent
│   └── CONFIDENCE_SCORING.md     ← Confidence scoring system
├── 07_hydration/                 ← Anti-drift system
│   ├── HYDRATION_HEADER.md       ← Compact state block
│   ├── STATE_SNAPSHOT.md         ← Full project state
│   ├── DRIFT_PREVENTION.md       ← Drift detection rules
│   └── REHYDRATION_PROTOCOL.md   ← Context recovery
├── 08_task_queue/                ← Task planning
│   ├── TASK_BACKLOG.md           ← All 601 tasks with status
│   ├── DEPENDENCY_MAP.md         ← Story dependencies
│   ├── CYCLE_PLANNER.md          ← Task selection logic
│   └── EPIC_STATUS_TRACKER.md    ← Completion tracking
├── 09_templates/                 ← Reusable templates
│   ├── CYCLE_REPLY_TEMPLATE.md
│   ├── AGENT_PROMPT_A.md through AGENT_PROMPT_D.md
│   ├── JIRA_UPDATE_TEMPLATE.md
│   └── REVIEW_REPORT_TEMPLATE.md
├── 10_cycle_log/                 ← Cycle history
│   └── CYCLE_000_INIT.md
└── ref/                          ← Source documents (read-only reference)
    ├── REF_INDEX.md
    ├── project_plan/  (74 spec files)
    ├── todo/          (11 files — 10 epics + schedule)
    ├── dod/           (10 DOD files)
    └── github/        (47 GitHub files)
```

---

## Project Vitals

| Key | Value |
|---|---|
| Project | Fiverr Research System |
| GitHub | https://github.com/KevinSGarrett/Fiverr |
| Local | C:\Fiverr |
| PM Pack | C:\Fiverr1\Project_Manager\ |
| Epics | 10 |
| Stories | 105 |
| Tasks | 601 |
| Agents | A=Infrastructure, B=Collection, C=Analysis/Scoring, D=Dashboard |
| PM | ChatGPT |

---

## Critical Files (Load Order)

### Every Cycle (load these always)
1. `07_hydration/HYDRATION_HEADER.md` — Context block
2. `07_hydration/STATE_SNAPSHOT.md` — Current state
3. `08_task_queue/CYCLE_PLANNER.md` — What to build
4. `04_jira_protocol/FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md` — Board-first planning gate
5. `03_cursor_agent_system/PROMPT_TEMPLATE.md` — Generate prompts
6. `01_pm_instructions/PM_REPLY_CHECKLIST.md` — Validate reply

### When Reviewing Agent Work
7. `06_review_and_qa/REVIEW_CHECKLIST.md`
8. `06_review_and_qa/QA_GATES.md`

### When Updating Jira
9. `04_jira_protocol/JIRA_UPDATE_CHECKLIST.md`

### When Referencing Specs (on demand)
10. `ref/REF_INDEX.md` → navigate to specific spec file

## Cycle 005 Governance Additions
- `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md` — permanent rules for reviewing, fixing, ignoring, replying to, and resolving Codex PR comments.
- `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md` — permanent PR checks, GitHub Actions, Codecov >=90%, branch protection, and steward checklist.

- `05_github_protocol/CODEX_PR_GATE_CYCLE_009.md` — Cycle 009 Codex blocker handling for PR #7.

- `04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md` — Mandatory changed-files-to-Jira-story mapping protocol.

- `04_jira_protocol/CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md` — Cursor-agent Jira read/write/edit authority and guardrails.
- `01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_010.md` — Cycle 010 rule changes for Jira authority and doubled task volume.
- `01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_012.md` — Cycle 012 board-first and prompt-depth enforcement.
- `10_cycle_log/CYCLE_011.md` — Cycle 011 PM response and agent prompts.
- `CYCLE_011_PM_RESPONSE.md` — Copy of Cycle 011 PM response.

## Cycle 013 additions

- `PM_Pack/10_cycle_log/CYCLE_013_REVIEW_AND_HANDOFF.md` — Cycle 013 review of attached repo, PM Pack, GitHub PR #10, and Jira gate findings.
- `PM_Pack/05_github_protocol/CODEX_PR10_GATE_CYCLE_013.md` — PR #10 Codex blocker gate and merge-readiness rule.
- `PM_Pack/01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_013.md` — Cycle 013 corrective rule memory.
- `PM_Pack/03_cursor_agent_system/CYCLE_013_AGENT_A_PROMPT.md` through `CYCLE_013_AGENT_D_PROMPT.md` — full next-cycle Cursor prompts.
- `PM_Pack/10_cycle_log/CYCLE_013_PROTOCOL_MEMORY_NOTE.md` — mandatory protocol memory for PR #10 blocker closure, security hygiene, and handoff constraints.

## Required-file consistency gate

All paths listed in this index as mandatory pack files must be present in the repository and tracked in Git on the active integration branch. If a file is optional, historical, or attachment-only, label it explicitly as optional in this index and in `PM_Pack/00_index/FILE_REGISTRY.md`.

Cycle 013 enforcement: `PM_Pack/07_hydration/HYDRATION_HEADER.md` and `PM_Pack/07_hydration/STATE_SNAPSHOT.md` are required and must remain cycle-current.

