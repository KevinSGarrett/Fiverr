Cycle 078 — Agent B Prompt

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
You are Agent B for Cycle 078 on branch cycle/078/integration.
Lane description: Primary src/ and tests/ author — new features, core logic
Your lane owns:
- src/**
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
- SCRUM-288: [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIES.md ID ma
  - AC: Low Gaps — L7+L9+L10\n\nThree minor cleanup/documentation gaps:\n\n L7 : Cycle 016 has duplicate file naming in docs/cycle_reports/ . Both CYCLE_016_AGENT_A.md and CYCLE_016_A.md exist (same for B/C/D
  - DoD: 
- SCRUM-252: [PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task l
  - AC: Purpose Record and enforce a permanent PM Pack update requested by the operator: Cursor agents have full read/write/edit access to the Jira board and may be instructed by the PM to perform Jira operat
  - DoD: 
- SCRUM-258: [CYCLE 014] Resume product development and enforce same-cycle Codex resolution
  - AC: Purpose Cycle 014 moves the Fiverr Research System back to product development after Cycle 013 repaired PR #10 governance blockers. The operator explicitly requested that the project stop spending mul
  - DoD: 
- SCRUM-272: [MEDIUM M22] Raise per-module test coverage to 90%+ for utils/playbook/scripts/e
  - AC: Medium Gap — M22 CI gate is --cov-fail-under=90 overall. The overall passes (93.7%) but 4 modules are below 90% line-rate individually. Adding new code to these without tests could push overall below 
  - DoD: 
- SCRUM-284: [MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 001 stale, P
  - AC: Medium Gap — M16+M17\n\nTwo related PM_Pack stale content issues:\n\n M16 : PM_Pack/08_task_queue/TASK_BACKLOG.md was last updated "Cycle 001". Cycles 002-017 have passed. Its Epic 01 story decomposit
  - DoD: 
- SCRUM-442: Meta / Gap Audit & Operations
  - AC: Meta epic for cross-epic gap-audit, operations, and noncanonical remediation items. Created by Wave 7B audit remediation to prevent completed gap stories from inflating product epic story counts.
  - DoD: 
- SCRUM-448: [W19][1.1.6] Install Playwright browsers / validate browser setup
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.6
Task: Install Playwright browsers / validate browser setup

This sub-task makes the E01 task-level
  - DoD: 
- SCRUM-454: [W19][1.2.5] Create CollectionConfig model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.5
Task: Create CollectionConfig model

This sub-task makes the E01 task-level work trackable in Jir
  - DoD: 
- SCRUM-460: [W19][1.3.4] Create Keyword model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.4
Task: Create Keyword model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-466: [W19][1.3.10] Create KeywordScore model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.10
Task: Create KeywordScore model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-472: [W19][1.3.16] Create SellerScore model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.16
Task: Create SellerScore model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-478: [W19][1.3.22] Create PriceAnalysis model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.22
Task: Create PriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-484: [W19][1.3.28] Create Order model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.28
Task: Create Order model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-490: [W19][1.4.4] Create logging setup
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.4
Task: Create logging setup

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-496: [W19][1.5.3] Create cache key builder
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.3
Task: Create cache key builder

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-502: [W19][1.6.2] Create data validation utilities
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.2
Task: Create data validation utilities

This sub-task makes the E01 task-level work trackable in 
  - DoD: 

## Tasks
### TASK 01 — Agent B setup/verify for SCRUM-288: [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIE
- Story: SCRUM-288
- AC Focus: Low Gaps — L7+L9+L10\n\nThree minor cleanup/documentation gaps:\n\n L7 : Cycle 016 has duplicate file naming in docs/cycle_reports/ . Both CYCLE_016_AGENT_A.md and CYCLE_016_A.md exist (same for B/C/D). One set should be canonicalized and the other deleted or renamed.\n\n L9 : USER_STORIES.md in the project plan uses a US-NNN ID scheme. No Jira issues carry this ID format, making it impossible to cross-reference USER_STORIES.md entries to Jira. Either add US- IDs as labels to stories, or document the mapping from US- IDs to SCRUM- keys.\n\n L10 : CHANGE_LOG.md only documents Waves 0-12, not implementation cycles 1-17. Significant architectural decisions made during cycles 013-017 (score table pivot, dashboard page structure, analysis module organization) are not captured at the change-log level.\n\n## Acceptance Criteria\n\n- [ ] L7: Canonical Cycle 016 files kept, duplicate files deleted or archived\n- [ ] L9: USER_STORIES.md US- IDs mapped to SCRUM- keys in a cross-reference table, or US- ID labels added to stories\n- [ ] L10: CHANGE_LOG.md updated with cycle 013-017 architectural decisions\n\n## Source Reference\n\n* Gap audit Pass-2: Low Gap L7\n* Gap audit Pass-3: Low Gaps L9, L10
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 02 — Agent B read project plan for SCRUM-252: [PM/CURSOR] Grant Cursor-agent Jira operations authority and double ag
- Story: SCRUM-252
- AC Focus: Purpose Record and enforce a permanent PM Pack update requested by the operator: Cursor agents have full read/write/edit access to the Jira board and may be instructed by the PM to perform Jira operations whenever needed. Also double the minimum and maximum task load allowed for each Cursor agent. Requested Rule Changes Cursor agents may read Jira issues, inspect Jira board state, create Jira issues, update Jira issues, comment on Jira issues, transition Jira issues, and maintain Jira mapping evidence when explicitly instructed in their cycle prompt. PM prompts may assign Jira work directly to Cursor agents instead of reserving all Jira updates for PM-only execution. Cursor agents must still follow the PM-defined Jira mapping protocol: changed files must map to exact Jira tickets, product tickets must be updated alongside governance tickets, and Done is only allowed when story-level DOD is met. Agent task limits are doubled from the previous 5-8 substantive tasks to a new minimum of 10 substantive tasks and target/maximum of 16 substantive tasks per agent, unless a documented task-count waiver is included. Future cycle prompts must include 10-16 tasks per agent and may include Jira operations as explicit assigned tasks. Acceptance Criteria PM Pack includes a Cursor-agent Jira operations authority protocol. PM Pack includes updated Cursor task-load limits: minimum 10 substantive tasks per agent, target/maximum 16. Cycle 010 prompts use the new task limits. Cycle 010 prompts explicitly mention Cursor agents can perform Jira operations when assigned. Future PM responses and PM Pack artifacts preserve this rule so it does not need to be repeated.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 03 — Agent B implement AC for SCRUM-258: [CYCLE 014] Resume product development and enforce same-cycle Codex re
- Story: SCRUM-258
- AC Focus: Purpose Cycle 014 moves the Fiverr Research System back to product development after Cycle 013 repaired PR #10 governance blockers. The operator explicitly requested that the project stop spending multiple cycles on PM Pack/Jira/Codex process loops unless there is a true blocker, and that PR-owning Cursor agents must handle Codex review comments inside the same cycle/PR instead of pushing unresolved Codex work into the next PM cycle. Live Review Context PR #10 remains open and mergeable at PM review time. PR #10 Codex threads are resolved. PR #10 CI and Codecov project checks are green at PM review time. PR #10 still needs a short merge gate before Cycle 014 branch creation. Cycle 014 should prioritize actual Fiverr product implementation after the gate passes. Binding Process Change The Cursor agent responsible for PR stewardship must review all Codex review comments on that PR before final handoff. Valid Codex findings must be fixed in the same PR/cycle when feasible. Invalid or non-applicable Codex findings must receive an evidence-backed comment explaining why they are being ignored, then the thread must be resolved. A PR must not be handed off with unresolved Codex threads unless the agent explicitly documents a hard blocker preventing same-cycle resolution. Future PM cycles should not create whole repair cycles for Codex comments that should have been handled by the PR steward in the prior cycle. Product Development Focus After PR #10 is merged into develop, Cycle 014 should create cycle/014/integration and resume actual product work against Jira-selected AC/DoD stories, especially Dashboard & Reporting, Analysis, Integration, Export, and Query Layer work already in progress. Acceptance Criteria PR #10 merge gate is completed or blocked with evidence. Cycle 014 branch starts from updated develop after PR #10 merge if authorized and green. Product work is selected from Jira AC/DoD issues before coding. Cursor prompts include the same-cycle Codex resolution rule. Product stories receive AC/DoD progress comments and are not marked Done unless full DoD is met. PM Pack and cycle response are updated without derailing the cycle into process-only work.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 04 — Agent B validation for SCRUM-272: [MEDIUM M22] Raise per-module test coverage to 90%+ for utils/playbook
- Story: SCRUM-272
- AC Focus: Medium Gap — M22 CI gate is --cov-fail-under=90 overall. The overall passes (93.7%) but 4 modules are below 90% line-rate individually. Adding new code to these without tests could push overall below 90%. Modules Below 90% Line-Rate Module Current line-rate Status src/utils/ 80.2% ❌ Significantly below gate src/playbook/ 87.2% ❌ Below gate src/scripts/ 88.8% ❌ Below gate src/exports/ 88.8% ❌ Below gate Impact When new engines (scoring, pricing, discovery, playbook) are built, they need tests added simultaneously. The weakest modules (utils, playbook, exports) will be hardest to keep above gate as code grows. Recommended Fix Add per-module coverage gates in codecov.yml : coverage:
  status:
    patch:
      default:
        target: 90%
    project:
      src/utils:
        target: 90%
      src/playbook:
        target: 90%
      src/scripts:
        target: 88%
      src/exports:
        target: 90% Then write missing tests to bring each module to 90%+. Acceptance Criteria [ ] src/utils/ coverage raised to ≥ 90% via new unit tests [ ] src/playbook/ coverage raised to ≥ 90% [ ] src/scripts/ coverage raised to ≥ 90% [ ] src/exports/ coverage raised to ≥ 90% (aided by H17 Excel/PDF implementation) [ ] Per-module coverage thresholds added to codecov.yml or pyproject.toml [ ] CI passes with all module-level gates Source Reference C:\Fiverr\Fiverr\coverage.xml — current per-module coverage data C:\Fiverr\Fiverr.github\workflows\ci.yml — current CI gate setup Gap audit Pass-3: Medium Gap M22 Related SCRUM-235 (S10.5 Unit Test Coverage) SCRUM-268 (H17 Excel/PDF exports — will improve exports/ coverage) Suggested Metadata Labels: medium, integration, test-coverage, ci, wave-19  
Priority: Medium
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 05 — Agent B cleanup for SCRUM-284: [MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 00
- Story: SCRUM-284
- AC Focus: Medium Gap — M16+M17\n\nTwo related PM_Pack stale content issues:\n\n M16 : PM_Pack/08_task_queue/TASK_BACKLOG.md was last updated "Cycle 001". Cycles 002-017 have passed. Its Epic 01 story decomposition differs from the canonical TODO breakdown (e.g., Story 1.5 = "Logging" vs canonical "LLM Client and Cache"). Jira sided with the canonical TODO, making TASK_BACKLOG.md incorrect.\n\n M17 : PM_Pack_017.zip (a zip inside the repo) contains 284 files while the live PM_Pack/ directory has 240 files. They are out of sync.\n\n## Acceptance Criteria\n\n- [ ] Decision: delete or update TASK_BACKLOG.md to match canonical TODO breakdown\n- [ ] If delete: file removed, references cleaned\n- [ ] If update: TASK_BACKLOG.md rewritten to match EPIC_ .md files (105 stories, 600 tasks)\n- [ ] PM_Pack_017.zip updated to match current PM_Pack/ directory contents, OR explicitly labeled as historical snapshot\n- [ ] EPIC_STATUS_TRACKER.md updated to current cycle (was last updated Cycle 011)\n\n## Source Reference\n\n Gap audit Pass-2: Medium Gaps M16, M17
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 06 — Agent B setup/verify for SCRUM-442: Meta / Gap Audit & Operations
- Story: SCRUM-442
- AC Focus: Meta epic for cross-epic gap-audit, operations, and noncanonical remediation items. Created by Wave 7B audit remediation to prevent completed gap stories from inflating product epic story counts.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 07 — Agent B read project plan for SCRUM-448: [W19][1.1.6] Install Playwright browsers / validate browser setup
- Story: SCRUM-448
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.6
Task: Install Playwright browsers / validate browser setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 08 — Agent B implement AC for SCRUM-454: [W19][1.2.5] Create CollectionConfig model
- Story: SCRUM-454
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.5
Task: Create CollectionConfig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 09 — Agent B validation for SCRUM-460: [W19][1.3.4] Create Keyword model
- Story: SCRUM-460
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.4
Task: Create Keyword model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 10 — Agent B cleanup for SCRUM-466: [W19][1.3.10] Create KeywordScore model
- Story: SCRUM-466
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.10
Task: Create KeywordScore model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 11 — Agent B setup/verify for SCRUM-472: [W19][1.3.16] Create SellerScore model
- Story: SCRUM-472
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.16
Task: Create SellerScore model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 12 — Agent B read project plan for SCRUM-478: [W19][1.3.22] Create PriceAnalysis model
- Story: SCRUM-478
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.22
Task: Create PriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 13 — Agent B implement AC for SCRUM-484: [W19][1.3.28] Create Order model
- Story: SCRUM-484
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.28
Task: Create Order model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 14 — Agent B validation for SCRUM-490: [W19][1.4.4] Create logging setup
- Story: SCRUM-490
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.4
Task: Create logging setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 15 — Agent B cleanup for SCRUM-496: [W19][1.5.3] Create cache key builder
- Story: SCRUM-496
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.3
Task: Create cache key builder

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 16 — Agent B setup/verify for SCRUM-502: [W19][1.6.2] Create data validation utilities
- Story: SCRUM-502
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.2
Task: Create data validation utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 17 — Agent B read project plan for SCRUM-288: [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIE
- Story: SCRUM-288
- AC Focus: Low Gaps — L7+L9+L10\n\nThree minor cleanup/documentation gaps:\n\n L7 : Cycle 016 has duplicate file naming in docs/cycle_reports/ . Both CYCLE_016_AGENT_A.md and CYCLE_016_A.md exist (same for B/C/D). One set should be canonicalized and the other deleted or renamed.\n\n L9 : USER_STORIES.md in the project plan uses a US-NNN ID scheme. No Jira issues carry this ID format, making it impossible to cross-reference USER_STORIES.md entries to Jira. Either add US- IDs as labels to stories, or document the mapping from US- IDs to SCRUM- keys.\n\n L10 : CHANGE_LOG.md only documents Waves 0-12, not implementation cycles 1-17. Significant architectural decisions made during cycles 013-017 (score table pivot, dashboard page structure, analysis module organization) are not captured at the change-log level.\n\n## Acceptance Criteria\n\n- [ ] L7: Canonical Cycle 016 files kept, duplicate files deleted or archived\n- [ ] L9: USER_STORIES.md US- IDs mapped to SCRUM- keys in a cross-reference table, or US- ID labels added to stories\n- [ ] L10: CHANGE_LOG.md updated with cycle 013-017 architectural decisions\n\n## Source Reference\n\n* Gap audit Pass-2: Low Gap L7\n* Gap audit Pass-3: Low Gaps L9, L10
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 18 — Agent B implement AC for SCRUM-252: [PM/CURSOR] Grant Cursor-agent Jira operations authority and double ag
- Story: SCRUM-252
- AC Focus: Purpose Record and enforce a permanent PM Pack update requested by the operator: Cursor agents have full read/write/edit access to the Jira board and may be instructed by the PM to perform Jira operations whenever needed. Also double the minimum and maximum task load allowed for each Cursor agent. Requested Rule Changes Cursor agents may read Jira issues, inspect Jira board state, create Jira issues, update Jira issues, comment on Jira issues, transition Jira issues, and maintain Jira mapping evidence when explicitly instructed in their cycle prompt. PM prompts may assign Jira work directly to Cursor agents instead of reserving all Jira updates for PM-only execution. Cursor agents must still follow the PM-defined Jira mapping protocol: changed files must map to exact Jira tickets, product tickets must be updated alongside governance tickets, and Done is only allowed when story-level DOD is met. Agent task limits are doubled from the previous 5-8 substantive tasks to a new minimum of 10 substantive tasks and target/maximum of 16 substantive tasks per agent, unless a documented task-count waiver is included. Future cycle prompts must include 10-16 tasks per agent and may include Jira operations as explicit assigned tasks. Acceptance Criteria PM Pack includes a Cursor-agent Jira operations authority protocol. PM Pack includes updated Cursor task-load limits: minimum 10 substantive tasks per agent, target/maximum 16. Cycle 010 prompts use the new task limits. Cycle 010 prompts explicitly mention Cursor agents can perform Jira operations when assigned. Future PM responses and PM Pack artifacts preserve this rule so it does not need to be repeated.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 19 — Agent B validation for SCRUM-258: [CYCLE 014] Resume product development and enforce same-cycle Codex re
- Story: SCRUM-258
- AC Focus: Purpose Cycle 014 moves the Fiverr Research System back to product development after Cycle 013 repaired PR #10 governance blockers. The operator explicitly requested that the project stop spending multiple cycles on PM Pack/Jira/Codex process loops unless there is a true blocker, and that PR-owning Cursor agents must handle Codex review comments inside the same cycle/PR instead of pushing unresolved Codex work into the next PM cycle. Live Review Context PR #10 remains open and mergeable at PM review time. PR #10 Codex threads are resolved. PR #10 CI and Codecov project checks are green at PM review time. PR #10 still needs a short merge gate before Cycle 014 branch creation. Cycle 014 should prioritize actual Fiverr product implementation after the gate passes. Binding Process Change The Cursor agent responsible for PR stewardship must review all Codex review comments on that PR before final handoff. Valid Codex findings must be fixed in the same PR/cycle when feasible. Invalid or non-applicable Codex findings must receive an evidence-backed comment explaining why they are being ignored, then the thread must be resolved. A PR must not be handed off with unresolved Codex threads unless the agent explicitly documents a hard blocker preventing same-cycle resolution. Future PM cycles should not create whole repair cycles for Codex comments that should have been handled by the PR steward in the prior cycle. Product Development Focus After PR #10 is merged into develop, Cycle 014 should create cycle/014/integration and resume actual product work against Jira-selected AC/DoD stories, especially Dashboard & Reporting, Analysis, Integration, Export, and Query Layer work already in progress. Acceptance Criteria PR #10 merge gate is completed or blocked with evidence. Cycle 014 branch starts from updated develop after PR #10 merge if authorized and green. Product work is selected from Jira AC/DoD issues before coding. Cursor prompts include the same-cycle Codex resolution rule. Product stories receive AC/DoD progress comments and are not marked Done unless full DoD is met. PM Pack and cycle response are updated without derailing the cycle into process-only work.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 20 — Agent B cleanup for SCRUM-272: [MEDIUM M22] Raise per-module test coverage to 90%+ for utils/playbook
- Story: SCRUM-272
- AC Focus: Medium Gap — M22 CI gate is --cov-fail-under=90 overall. The overall passes (93.7%) but 4 modules are below 90% line-rate individually. Adding new code to these without tests could push overall below 90%. Modules Below 90% Line-Rate Module Current line-rate Status src/utils/ 80.2% ❌ Significantly below gate src/playbook/ 87.2% ❌ Below gate src/scripts/ 88.8% ❌ Below gate src/exports/ 88.8% ❌ Below gate Impact When new engines (scoring, pricing, discovery, playbook) are built, they need tests added simultaneously. The weakest modules (utils, playbook, exports) will be hardest to keep above gate as code grows. Recommended Fix Add per-module coverage gates in codecov.yml : coverage:
  status:
    patch:
      default:
        target: 90%
    project:
      src/utils:
        target: 90%
      src/playbook:
        target: 90%
      src/scripts:
        target: 88%
      src/exports:
        target: 90% Then write missing tests to bring each module to 90%+. Acceptance Criteria [ ] src/utils/ coverage raised to ≥ 90% via new unit tests [ ] src/playbook/ coverage raised to ≥ 90% [ ] src/scripts/ coverage raised to ≥ 90% [ ] src/exports/ coverage raised to ≥ 90% (aided by H17 Excel/PDF implementation) [ ] Per-module coverage thresholds added to codecov.yml or pyproject.toml [ ] CI passes with all module-level gates Source Reference C:\Fiverr\Fiverr\coverage.xml — current per-module coverage data C:\Fiverr\Fiverr.github\workflows\ci.yml — current CI gate setup Gap audit Pass-3: Medium Gap M22 Related SCRUM-235 (S10.5 Unit Test Coverage) SCRUM-268 (H17 Excel/PDF exports — will improve exports/ coverage) Suggested Metadata Labels: medium, integration, test-coverage, ci, wave-19  
Priority: Medium
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 21 — Agent B setup/verify for SCRUM-284: [MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 00
- Story: SCRUM-284
- AC Focus: Medium Gap — M16+M17\n\nTwo related PM_Pack stale content issues:\n\n M16 : PM_Pack/08_task_queue/TASK_BACKLOG.md was last updated "Cycle 001". Cycles 002-017 have passed. Its Epic 01 story decomposition differs from the canonical TODO breakdown (e.g., Story 1.5 = "Logging" vs canonical "LLM Client and Cache"). Jira sided with the canonical TODO, making TASK_BACKLOG.md incorrect.\n\n M17 : PM_Pack_017.zip (a zip inside the repo) contains 284 files while the live PM_Pack/ directory has 240 files. They are out of sync.\n\n## Acceptance Criteria\n\n- [ ] Decision: delete or update TASK_BACKLOG.md to match canonical TODO breakdown\n- [ ] If delete: file removed, references cleaned\n- [ ] If update: TASK_BACKLOG.md rewritten to match EPIC_ .md files (105 stories, 600 tasks)\n- [ ] PM_Pack_017.zip updated to match current PM_Pack/ directory contents, OR explicitly labeled as historical snapshot\n- [ ] EPIC_STATUS_TRACKER.md updated to current cycle (was last updated Cycle 011)\n\n## Source Reference\n\n Gap audit Pass-2: Medium Gaps M16, M17
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 22 — Agent B read project plan for SCRUM-442: Meta / Gap Audit & Operations
- Story: SCRUM-442
- AC Focus: Meta epic for cross-epic gap-audit, operations, and noncanonical remediation items. Created by Wave 7B audit remediation to prevent completed gap stories from inflating product epic story counts.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 23 — Agent B implement AC for SCRUM-448: [W19][1.1.6] Install Playwright browsers / validate browser setup
- Story: SCRUM-448
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.6
Task: Install Playwright browsers / validate browser setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 24 — Agent B validation for SCRUM-454: [W19][1.2.5] Create CollectionConfig model
- Story: SCRUM-454
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.5
Task: Create CollectionConfig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 25 — Agent B cleanup for SCRUM-460: [W19][1.3.4] Create Keyword model
- Story: SCRUM-460
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.4
Task: Create Keyword model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 26 — Agent B setup/verify for SCRUM-466: [W19][1.3.10] Create KeywordScore model
- Story: SCRUM-466
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.10
Task: Create KeywordScore model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 27 — Agent B read project plan for SCRUM-472: [W19][1.3.16] Create SellerScore model
- Story: SCRUM-472
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.16
Task: Create SellerScore model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 28 — Agent B implement AC for SCRUM-478: [W19][1.3.22] Create PriceAnalysis model
- Story: SCRUM-478
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.22
Task: Create PriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 29 — Agent B validation for SCRUM-484: [W19][1.3.28] Create Order model
- Story: SCRUM-484
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.28
Task: Create Order model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 30 — Agent B cleanup for SCRUM-490: [W19][1.4.4] Create logging setup
- Story: SCRUM-490
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.4
Task: Create logging setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 31 — Agent B setup/verify for SCRUM-496: [W19][1.5.3] Create cache key builder
- Story: SCRUM-496
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.3
Task: Create cache key builder

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 32 — Agent B read project plan for SCRUM-502: [W19][1.6.2] Create data validation utilities
- Story: SCRUM-502
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.2
Task: Create data validation utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 33 — Agent B implement AC for SCRUM-288: [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIE
- Story: SCRUM-288
- AC Focus: Low Gaps — L7+L9+L10\n\nThree minor cleanup/documentation gaps:\n\n L7 : Cycle 016 has duplicate file naming in docs/cycle_reports/ . Both CYCLE_016_AGENT_A.md and CYCLE_016_A.md exist (same for B/C/D). One set should be canonicalized and the other deleted or renamed.\n\n L9 : USER_STORIES.md in the project plan uses a US-NNN ID scheme. No Jira issues carry this ID format, making it impossible to cross-reference USER_STORIES.md entries to Jira. Either add US- IDs as labels to stories, or document the mapping from US- IDs to SCRUM- keys.\n\n L10 : CHANGE_LOG.md only documents Waves 0-12, not implementation cycles 1-17. Significant architectural decisions made during cycles 013-017 (score table pivot, dashboard page structure, analysis module organization) are not captured at the change-log level.\n\n## Acceptance Criteria\n\n- [ ] L7: Canonical Cycle 016 files kept, duplicate files deleted or archived\n- [ ] L9: USER_STORIES.md US- IDs mapped to SCRUM- keys in a cross-reference table, or US- ID labels added to stories\n- [ ] L10: CHANGE_LOG.md updated with cycle 013-017 architectural decisions\n\n## Source Reference\n\n* Gap audit Pass-2: Low Gap L7\n* Gap audit Pass-3: Low Gaps L9, L10
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 34 — Agent B validation for SCRUM-252: [PM/CURSOR] Grant Cursor-agent Jira operations authority and double ag
- Story: SCRUM-252
- AC Focus: Purpose Record and enforce a permanent PM Pack update requested by the operator: Cursor agents have full read/write/edit access to the Jira board and may be instructed by the PM to perform Jira operations whenever needed. Also double the minimum and maximum task load allowed for each Cursor agent. Requested Rule Changes Cursor agents may read Jira issues, inspect Jira board state, create Jira issues, update Jira issues, comment on Jira issues, transition Jira issues, and maintain Jira mapping evidence when explicitly instructed in their cycle prompt. PM prompts may assign Jira work directly to Cursor agents instead of reserving all Jira updates for PM-only execution. Cursor agents must still follow the PM-defined Jira mapping protocol: changed files must map to exact Jira tickets, product tickets must be updated alongside governance tickets, and Done is only allowed when story-level DOD is met. Agent task limits are doubled from the previous 5-8 substantive tasks to a new minimum of 10 substantive tasks and target/maximum of 16 substantive tasks per agent, unless a documented task-count waiver is included. Future cycle prompts must include 10-16 tasks per agent and may include Jira operations as explicit assigned tasks. Acceptance Criteria PM Pack includes a Cursor-agent Jira operations authority protocol. PM Pack includes updated Cursor task-load limits: minimum 10 substantive tasks per agent, target/maximum 16. Cycle 010 prompts use the new task limits. Cycle 010 prompts explicitly mention Cursor agents can perform Jira operations when assigned. Future PM responses and PM Pack artifacts preserve this rule so it does not need to be repeated.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 35 — Agent B cleanup for SCRUM-258: [CYCLE 014] Resume product development and enforce same-cycle Codex re
- Story: SCRUM-258
- AC Focus: Purpose Cycle 014 moves the Fiverr Research System back to product development after Cycle 013 repaired PR #10 governance blockers. The operator explicitly requested that the project stop spending multiple cycles on PM Pack/Jira/Codex process loops unless there is a true blocker, and that PR-owning Cursor agents must handle Codex review comments inside the same cycle/PR instead of pushing unresolved Codex work into the next PM cycle. Live Review Context PR #10 remains open and mergeable at PM review time. PR #10 Codex threads are resolved. PR #10 CI and Codecov project checks are green at PM review time. PR #10 still needs a short merge gate before Cycle 014 branch creation. Cycle 014 should prioritize actual Fiverr product implementation after the gate passes. Binding Process Change The Cursor agent responsible for PR stewardship must review all Codex review comments on that PR before final handoff. Valid Codex findings must be fixed in the same PR/cycle when feasible. Invalid or non-applicable Codex findings must receive an evidence-backed comment explaining why they are being ignored, then the thread must be resolved. A PR must not be handed off with unresolved Codex threads unless the agent explicitly documents a hard blocker preventing same-cycle resolution. Future PM cycles should not create whole repair cycles for Codex comments that should have been handled by the PR steward in the prior cycle. Product Development Focus After PR #10 is merged into develop, Cycle 014 should create cycle/014/integration and resume actual product work against Jira-selected AC/DoD stories, especially Dashboard & Reporting, Analysis, Integration, Export, and Query Layer work already in progress. Acceptance Criteria PR #10 merge gate is completed or blocked with evidence. Cycle 014 branch starts from updated develop after PR #10 merge if authorized and green. Product work is selected from Jira AC/DoD issues before coding. Cursor prompts include the same-cycle Codex resolution rule. Product stories receive AC/DoD progress comments and are not marked Done unless full DoD is met. PM Pack and cycle response are updated without derailing the cycle into process-only work.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 36 — Agent B setup/verify for SCRUM-272: [MEDIUM M22] Raise per-module test coverage to 90%+ for utils/playbook
- Story: SCRUM-272
- AC Focus: Medium Gap — M22 CI gate is --cov-fail-under=90 overall. The overall passes (93.7%) but 4 modules are below 90% line-rate individually. Adding new code to these without tests could push overall below 90%. Modules Below 90% Line-Rate Module Current line-rate Status src/utils/ 80.2% ❌ Significantly below gate src/playbook/ 87.2% ❌ Below gate src/scripts/ 88.8% ❌ Below gate src/exports/ 88.8% ❌ Below gate Impact When new engines (scoring, pricing, discovery, playbook) are built, they need tests added simultaneously. The weakest modules (utils, playbook, exports) will be hardest to keep above gate as code grows. Recommended Fix Add per-module coverage gates in codecov.yml : coverage:
  status:
    patch:
      default:
        target: 90%
    project:
      src/utils:
        target: 90%
      src/playbook:
        target: 90%
      src/scripts:
        target: 88%
      src/exports:
        target: 90% Then write missing tests to bring each module to 90%+. Acceptance Criteria [ ] src/utils/ coverage raised to ≥ 90% via new unit tests [ ] src/playbook/ coverage raised to ≥ 90% [ ] src/scripts/ coverage raised to ≥ 90% [ ] src/exports/ coverage raised to ≥ 90% (aided by H17 Excel/PDF implementation) [ ] Per-module coverage thresholds added to codecov.yml or pyproject.toml [ ] CI passes with all module-level gates Source Reference C:\Fiverr\Fiverr\coverage.xml — current per-module coverage data C:\Fiverr\Fiverr.github\workflows\ci.yml — current CI gate setup Gap audit Pass-3: Medium Gap M22 Related SCRUM-235 (S10.5 Unit Test Coverage) SCRUM-268 (H17 Excel/PDF exports — will improve exports/ coverage) Suggested Metadata Labels: medium, integration, test-coverage, ci, wave-19  
Priority: Medium
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 37 — Agent B read project plan for SCRUM-284: [MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 00
- Story: SCRUM-284
- AC Focus: Medium Gap — M16+M17\n\nTwo related PM_Pack stale content issues:\n\n M16 : PM_Pack/08_task_queue/TASK_BACKLOG.md was last updated "Cycle 001". Cycles 002-017 have passed. Its Epic 01 story decomposition differs from the canonical TODO breakdown (e.g., Story 1.5 = "Logging" vs canonical "LLM Client and Cache"). Jira sided with the canonical TODO, making TASK_BACKLOG.md incorrect.\n\n M17 : PM_Pack_017.zip (a zip inside the repo) contains 284 files while the live PM_Pack/ directory has 240 files. They are out of sync.\n\n## Acceptance Criteria\n\n- [ ] Decision: delete or update TASK_BACKLOG.md to match canonical TODO breakdown\n- [ ] If delete: file removed, references cleaned\n- [ ] If update: TASK_BACKLOG.md rewritten to match EPIC_ .md files (105 stories, 600 tasks)\n- [ ] PM_Pack_017.zip updated to match current PM_Pack/ directory contents, OR explicitly labeled as historical snapshot\n- [ ] EPIC_STATUS_TRACKER.md updated to current cycle (was last updated Cycle 011)\n\n## Source Reference\n\n Gap audit Pass-2: Medium Gaps M16, M17
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 38 — Agent B implement AC for SCRUM-442: Meta / Gap Audit & Operations
- Story: SCRUM-442
- AC Focus: Meta epic for cross-epic gap-audit, operations, and noncanonical remediation items. Created by Wave 7B audit remediation to prevent completed gap stories from inflating product epic story counts.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 39 — Agent B validation for SCRUM-448: [W19][1.1.6] Install Playwright browsers / validate browser setup
- Story: SCRUM-448
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.6
Task: Install Playwright browsers / validate browser setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 40 — Agent B cleanup for SCRUM-454: [W19][1.2.5] Create CollectionConfig model
- Story: SCRUM-454
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.5
Task: Create CollectionConfig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 41 — Agent B setup/verify for SCRUM-460: [W19][1.3.4] Create Keyword model
- Story: SCRUM-460
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.4
Task: Create Keyword model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 42 — Agent B read project plan for SCRUM-466: [W19][1.3.10] Create KeywordScore model
- Story: SCRUM-466
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.10
Task: Create KeywordScore model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 43 — Agent B implement AC for SCRUM-472: [W19][1.3.16] Create SellerScore model
- Story: SCRUM-472
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.16
Task: Create SellerScore model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 44 — Agent B validation for SCRUM-478: [W19][1.3.22] Create PriceAnalysis model
- Story: SCRUM-478
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.22
Task: Create PriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 45 — Agent B cleanup for SCRUM-484: [W19][1.3.28] Create Order model
- Story: SCRUM-484
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.28
Task: Create Order model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 46 — Agent B setup/verify for SCRUM-490: [W19][1.4.4] Create logging setup
- Story: SCRUM-490
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.4
Task: Create logging setup

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 47 — Agent B read project plan for SCRUM-496: [W19][1.5.3] Create cache key builder
- Story: SCRUM-496
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.3
Task: Create cache key builder

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 48 — Agent B implement AC for SCRUM-502: [W19][1.6.2] Create data validation utilities
- Story: SCRUM-502
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.2
Task: Create data validation utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 49 — Agent B validation for SCRUM-288: [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIE
- Story: SCRUM-288
- AC Focus: Low Gaps — L7+L9+L10\n\nThree minor cleanup/documentation gaps:\n\n L7 : Cycle 016 has duplicate file naming in docs/cycle_reports/ . Both CYCLE_016_AGENT_A.md and CYCLE_016_A.md exist (same for B/C/D). One set should be canonicalized and the other deleted or renamed.\n\n L9 : USER_STORIES.md in the project plan uses a US-NNN ID scheme. No Jira issues carry this ID format, making it impossible to cross-reference USER_STORIES.md entries to Jira. Either add US- IDs as labels to stories, or document the mapping from US- IDs to SCRUM- keys.\n\n L10 : CHANGE_LOG.md only documents Waves 0-12, not implementation cycles 1-17. Significant architectural decisions made during cycles 013-017 (score table pivot, dashboard page structure, analysis module organization) are not captured at the change-log level.\n\n## Acceptance Criteria\n\n- [ ] L7: Canonical Cycle 016 files kept, duplicate files deleted or archived\n- [ ] L9: USER_STORIES.md US- IDs mapped to SCRUM- keys in a cross-reference table, or US- ID labels added to stories\n- [ ] L10: CHANGE_LOG.md updated with cycle 013-017 architectural decisions\n\n## Source Reference\n\n* Gap audit Pass-2: Low Gap L7\n* Gap audit Pass-3: Low Gaps L9, L10
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 50 — Agent B cleanup for SCRUM-252: [PM/CURSOR] Grant Cursor-agent Jira operations authority and double ag
- Story: SCRUM-252
- AC Focus: Purpose Record and enforce a permanent PM Pack update requested by the operator: Cursor agents have full read/write/edit access to the Jira board and may be instructed by the PM to perform Jira operations whenever needed. Also double the minimum and maximum task load allowed for each Cursor agent. Requested Rule Changes Cursor agents may read Jira issues, inspect Jira board state, create Jira issues, update Jira issues, comment on Jira issues, transition Jira issues, and maintain Jira mapping evidence when explicitly instructed in their cycle prompt. PM prompts may assign Jira work directly to Cursor agents instead of reserving all Jira updates for PM-only execution. Cursor agents must still follow the PM-defined Jira mapping protocol: changed files must map to exact Jira tickets, product tickets must be updated alongside governance tickets, and Done is only allowed when story-level DOD is met. Agent task limits are doubled from the previous 5-8 substantive tasks to a new minimum of 10 substantive tasks and target/maximum of 16 substantive tasks per agent, unless a documented task-count waiver is included. Future cycle prompts must include 10-16 tasks per agent and may include Jira operations as explicit assigned tasks. Acceptance Criteria PM Pack includes a Cursor-agent Jira operations authority protocol. PM Pack includes updated Cursor task-load limits: minimum 10 substantive tasks per agent, target/maximum 16. Cycle 010 prompts use the new task limits. Cycle 010 prompts explicitly mention Cursor agents can perform Jira operations when assigned. Future PM responses and PM Pack artifacts preserve this rule so it does not need to be repeated.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 51 — Agent B setup/verify for SCRUM-258: [CYCLE 014] Resume product development and enforce same-cycle Codex re
- Story: SCRUM-258
- AC Focus: Purpose Cycle 014 moves the Fiverr Research System back to product development after Cycle 013 repaired PR #10 governance blockers. The operator explicitly requested that the project stop spending multiple cycles on PM Pack/Jira/Codex process loops unless there is a true blocker, and that PR-owning Cursor agents must handle Codex review comments inside the same cycle/PR instead of pushing unresolved Codex work into the next PM cycle. Live Review Context PR #10 remains open and mergeable at PM review time. PR #10 Codex threads are resolved. PR #10 CI and Codecov project checks are green at PM review time. PR #10 still needs a short merge gate before Cycle 014 branch creation. Cycle 014 should prioritize actual Fiverr product implementation after the gate passes. Binding Process Change The Cursor agent responsible for PR stewardship must review all Codex review comments on that PR before final handoff. Valid Codex findings must be fixed in the same PR/cycle when feasible. Invalid or non-applicable Codex findings must receive an evidence-backed comment explaining why they are being ignored, then the thread must be resolved. A PR must not be handed off with unresolved Codex threads unless the agent explicitly documents a hard blocker preventing same-cycle resolution. Future PM cycles should not create whole repair cycles for Codex comments that should have been handled by the PR steward in the prior cycle. Product Development Focus After PR #10 is merged into develop, Cycle 014 should create cycle/014/integration and resume actual product work against Jira-selected AC/DoD stories, especially Dashboard & Reporting, Analysis, Integration, Export, and Query Layer work already in progress. Acceptance Criteria PR #10 merge gate is completed or blocked with evidence. Cycle 014 branch starts from updated develop after PR #10 merge if authorized and green. Product work is selected from Jira AC/DoD issues before coding. Cursor prompts include the same-cycle Codex resolution rule. Product stories receive AC/DoD progress comments and are not marked Done unless full DoD is met. PM Pack and cycle response are updated without derailing the cycle into process-only work.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 52 — Agent B read project plan for SCRUM-272: [MEDIUM M22] Raise per-module test coverage to 90%+ for utils/playbook
- Story: SCRUM-272
- AC Focus: Medium Gap — M22 CI gate is --cov-fail-under=90 overall. The overall passes (93.7%) but 4 modules are below 90% line-rate individually. Adding new code to these without tests could push overall below 90%. Modules Below 90% Line-Rate Module Current line-rate Status src/utils/ 80.2% ❌ Significantly below gate src/playbook/ 87.2% ❌ Below gate src/scripts/ 88.8% ❌ Below gate src/exports/ 88.8% ❌ Below gate Impact When new engines (scoring, pricing, discovery, playbook) are built, they need tests added simultaneously. The weakest modules (utils, playbook, exports) will be hardest to keep above gate as code grows. Recommended Fix Add per-module coverage gates in codecov.yml : coverage:
  status:
    patch:
      default:
        target: 90%
    project:
      src/utils:
        target: 90%
      src/playbook:
        target: 90%
      src/scripts:
        target: 88%
      src/exports:
        target: 90% Then write missing tests to bring each module to 90%+. Acceptance Criteria [ ] src/utils/ coverage raised to ≥ 90% via new unit tests [ ] src/playbook/ coverage raised to ≥ 90% [ ] src/scripts/ coverage raised to ≥ 90% [ ] src/exports/ coverage raised to ≥ 90% (aided by H17 Excel/PDF implementation) [ ] Per-module coverage thresholds added to codecov.yml or pyproject.toml [ ] CI passes with all module-level gates Source Reference C:\Fiverr\Fiverr\coverage.xml — current per-module coverage data C:\Fiverr\Fiverr.github\workflows\ci.yml — current CI gate setup Gap audit Pass-3: Medium Gap M22 Related SCRUM-235 (S10.5 Unit Test Coverage) SCRUM-268 (H17 Excel/PDF exports — will improve exports/ coverage) Suggested Metadata Labels: medium, integration, test-coverage, ci, wave-19  
Priority: Medium
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 53 — Agent B implement AC for SCRUM-284: [MEDIUM M16/M17] Update stale PM_Pack files — TASK_BACKLOG.md Cycle 00
- Story: SCRUM-284
- AC Focus: Medium Gap — M16+M17\n\nTwo related PM_Pack stale content issues:\n\n M16 : PM_Pack/08_task_queue/TASK_BACKLOG.md was last updated "Cycle 001". Cycles 002-017 have passed. Its Epic 01 story decomposition differs from the canonical TODO breakdown (e.g., Story 1.5 = "Logging" vs canonical "LLM Client and Cache"). Jira sided with the canonical TODO, making TASK_BACKLOG.md incorrect.\n\n M17 : PM_Pack_017.zip (a zip inside the repo) contains 284 files while the live PM_Pack/ directory has 240 files. They are out of sync.\n\n## Acceptance Criteria\n\n- [ ] Decision: delete or update TASK_BACKLOG.md to match canonical TODO breakdown\n- [ ] If delete: file removed, references cleaned\n- [ ] If update: TASK_BACKLOG.md rewritten to match EPIC_ .md files (105 stories, 600 tasks)\n- [ ] PM_Pack_017.zip updated to match current PM_Pack/ directory contents, OR explicitly labeled as historical snapshot\n- [ ] EPIC_STATUS_TRACKER.md updated to current cycle (was last updated Cycle 011)\n\n## Source Reference\n\n Gap audit Pass-2: Medium Gaps M16, M17
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 54 — Agent B validation for SCRUM-442: Meta / Gap Audit & Operations
- Story: SCRUM-442
- AC Focus: Meta epic for cross-epic gap-audit, operations, and noncanonical remediation items. Created by Wave 7B audit remediation to prevent completed gap stories from inflating product epic story counts.
- DoD Focus: 
- DoD Catalog Context: PM_Pack/ref/dod (no direct epic mapping)
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 55 — Agent B cleanup for SCRUM-448: [W19][1.1.6] Install Playwright browsers / validate browser setup
- Story: SCRUM-448
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.6
Task: Install Playwright browsers / validate browser setup

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
- Write: docs/cycle_reports/CYCLE_078_AGENT_B.md
- Final line must be: AGENT_COMPLETE

Generated at: 2026-06-14T01:01:30.287056+00:00

---

END OF PROMPT
