Cycle 078 — Agent E Prompt

## Canonical Secrets Reference
- Master .env: C:\Fiverr\Fiverr\.env
- Runner secrets: C:\AI_Runner\secrets\runner.env
- Required keys: OPENAI_API_KEY, SCRAPFLY_API_KEY, JIRA_API_TOKEN, JIRA_EMAIL, JIRA_BASE_URL, GH_AUTOMATION_TOKEN
- ANTHROPIC_API_KEY must be ABSENT

## Exact Directory Map
- Repo root: C:\Fiverr\Fiverr
- Automation modules: C:\Fiverr\Fiverr\automation\
- PM_Pack root: C:\Fiverr\Fiverr\PM_Pack\
- Runner root: C:\AI_Runner\

## PM_Pack Structure
- Post-cycle review prompt: C:\Fiverr\Fiverr\PM_Pack\01_pm_instructions\POST_CYCLE_PM_REVIEW_v4.md
- PM_Pack/ref project plans: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\
- PM_Pack/ref DoD: C:\Fiverr\Fiverr\PM_Pack\ref\dod\
- PM_Pack/ref TODO: C:\Fiverr\Fiverr\PM_Pack\ref\todo\

## Model Verification
- Verify C:\AI_Runner\state\cursor_model_state.json is VERIFIED and unexpired before dispatch.

## Agent Identity and Lane
You are Agent E for Cycle 078 on branch cycle/078/integration.
Lane description: Live data validation, external signal collection, evidence files
Your lane owns:
- docs/cycle_reports/**
- data/evidence/**
- scripts/validation/**
You MUST NOT touch:
- src/**
- tests/**
- config.yaml

## Model Policy (MANDATORY)
- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED

## Autonomy rule
- Proceed autonomously through all tasks without pausing for confirmation.
- If blocked, document blocker and continue with next executable task.
- Do not include git add/commit/push instructions in this prompt.

## Jira Scope
- SCRUM-211: [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
  - AC: Story Implement S8.7 — Playbook Dashboard Data Layer. Parent Epic SCRUM-23 — Epic 08: Playbook Engine Source ToDo_Fiverr(10)/To-Do/EPIC_08_PLAYBOOK.md DOD_Fiverr(7)/DOD/DOD_EPIC_08.md Gate: SCRUM-132 
  - DoD: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_08.md
- SCRUM-253: [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-
  - AC: Purpose Cycle 011 continues from uploaded Cycle 010 repository and PM Pack. Live GitHub review shows PR #8 is open, mergeable, and CI/Codecov mirror checks are successful, but two unresolved Codex P2 
  - DoD: 
- SCRUM-259: [CYCLE 015] Merge PR #11 and advance dashboard query/pages plus analysis integra
  - AC: Purpose Cycle 015 continues product-forward development after Cycle 014 delivered real Export and Alert product increments. The cycle must preserve the corrected high-detail Cursor prompt standard and
  - DoD: 
- SCRUM-279: [MEDIUM M9] Create SECURITY.md at repo root — missing industry-standard vulnerab
  - AC: Medium Gap — M9\n\nThe repository root is missing a SECURITY.md file. This is an industry standard that GitHub surfaces when users report vulnerabilities.\n\n## Required content\n\n- Supported version
  - DoD: 
- SCRUM-285: [MEDIUM M18/M19] Create missing test fixture dirs (7 engines) and test module st
  - AC: Medium Gap — M18+M19\n\nTwo related test infrastructure gaps:\n\n M18 : tests/fixtures/ only covers 3 engines (analysis, collection, dashboard). Missing fixture subdirectories for 7 engines that will 
  - DoD: 
- SCRUM-443: [W19][1.1.1] Create project directory structure
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.1
Task: Create project directory structure

This sub-task makes the E01 task-level work trackable in
  - DoD: 
- SCRUM-449: [W19][1.1.7] Create comprehensive README.md with setup guide
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.7
Task: Create comprehensive README.md with setup guide

This sub-task makes the E01 task-level work
  - DoD: 
- SCRUM-455: [W19][1.2.6] Create DiscoveryConfig model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.6
Task: Create DiscoveryConfig model

This sub-task makes the E01 task-level work trackable in Jira
  - DoD: 
- SCRUM-461: [W19][1.3.5] Create SearchResult model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.5
Task: Create SearchResult model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-467: [W19][1.3.11] Create OpportunityRanking model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.11
Task: Create OpportunityRanking model

This sub-task makes the E01 task-level work trackable in 
  - DoD: 
- SCRUM-473: [W19][1.3.17] Create LLMUsageLog model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.17
Task: Create LLMUsageLog model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-479: [W19][1.3.23] Create NichePriceAnalysis model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.23
Task: Create NichePriceAnalysis model

This sub-task makes the E01 task-level work trackable in 
  - DoD: 
- SCRUM-485: [W19][1.3.29] Create database migration script
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.29
Task: Create database migration script

This sub-task makes the E01 task-level work trackable in
  - DoD: 
- SCRUM-491: [W19][1.4.5] Create --mode resume logic
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.5
Task: Create --mode resume logic

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-497: [W19][1.5.4] Create cost tracking
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.4
Task: Create cost tracking

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-503: [W19][1.6.3] Create export utilities
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.3
Task: Create export utilities

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 

## Tasks
### TASK 01 — Agent E delivery for SCRUM-211: [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- Story: SCRUM-211
- AC Focus: Story Implement S8.7 — Playbook Dashboard Data Layer. Parent Epic SCRUM-23 — Epic 08: Playbook Engine Source ToDo_Fiverr(10)/To-Do/EPIC_08_PLAYBOOK.md DOD_Fiverr(7)/DOD/DOD_EPIC_08.md Gate: SCRUM-132 Scope Source tasks 8.7.1–8.7.3 covering playbook dashboard query/data layer, widget-ready payloads, and tests. Acceptance Criteria Playbook dashboard data is available from persisted playbook outputs. Outputs are dashboard-ready, source-traceable, and safe for sparse/missing playbook cases. Child tasks are created in later native task import waves or formally waived. Tests validate query output, missing data, and payload shape. DoD Complete when playbook dashboard data layer satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/playbook/s8-7-dashboard-data-layer
PR: feat(playbook): S8.7 Playbook Dashboard Data Layer Suggested Metadata Labels: wave-19, story, playbook, dashboard, data-layer, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_08.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 02 — Agent E delivery for SCRUM-253: [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and cont
- Story: SCRUM-253
- AC Focus: Purpose Cycle 011 continues from uploaded Cycle 010 repository and PM Pack. Live GitHub review shows PR #8 is open, mergeable, and CI/Codecov mirror checks are successful, but two unresolved Codex P2 review threads remain and must block merge under the project governance policy. Live PR State PR #8: feat(cycle-010): integrate multi-agent delivery and steward validations Source branch: cycle/010/integration Target branch: develop Status: open and mergeable at PM review time CI: successful codecov/project : successful Main branch: must remain untouched Blocking Codex Threads src/collection/checkpoint.py : load_checkpoint_stage_summary() should guard decoded checkpoint payloads that are valid non-object JSON, such as [] , so fallback behavior does not crash with AttributeError . src/dashboard/app.py : governance page readiness aggregation must include local_parity so a failing local parity signal is counted in category totals and cannot be hidden from the readiness summary. Scope Verify PR #8 live status, Codex review threads, GitHub Actions, Codecov project/patch, and branch policy. Fix both Codex P2 issues or formally disposition them if later proven invalid. Add regression tests for non-object checkpoint JSON fallback behavior. Add regression tests proving local_parity is present in governance page readiness categories and totals. Reply to both Codex threads with evidence-backed dispositions. Resolve Codex threads only after fixes, local validation, push, and passing checks. Merge PR #8 into develop only if authorized and all required gates remain green. Create cycle/011/integration from updated develop after PR #8 merges, or stop with evidence if blocked. Continue Phase 2 work using direct Cursor-agent Jira operations where assigned. Preserve the doubled Cursor task-volume rule: 10-20 substantive tasks per agent, with 12-16 preferred. Acceptance Criteria Both PR #8 Codex P2 findings are fixed or formally dispositioned with evidence. Both Codex review threads are resolved only after validation passes. GitHub Actions, Codecov project, Codecov patch, and local parity commands pass. PR #8 is merged only after all merge gates are satisfied and merge is authorized. Cycle 011 Cursor prompts include 10-20 substantive tasks per agent and direct Jira operations where assigned. Cycle 011 PM Pack is updated and attached in the final PM response.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 03 — Agent E delivery for SCRUM-259: [CYCLE 015] Merge PR #11 and advance dashboard query/pages plus analys
- Story: SCRUM-259
- AC Focus: Purpose Cycle 015 continues product-forward development after Cycle 014 delivered real Export and Alert product increments. The cycle must preserve the corrected high-detail Cursor prompt standard and avoid regressing into bare prompt lists or process-only work. Live GitHub Context PR #11: Cycle 014: export and alert product integration Source: cycle/014/integration Target: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: all active threads resolved in-cycle with evidence Product progress: Export System, Alert System, Integration Evidence, Coverage, Logging/Monitoring, Security/Data Hygiene Cycle 015 Product Focus After PR #11 is merged into develop, create cycle/015/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer SCRUM-214 — Dashboard Opportunities Page SCRUM-215 — Dashboard Keywords Page SCRUM-219 — Dashboard Run History Page SCRUM-228 — Dashboard App Entry Point SCRUM-231 — End-to-End Pipeline Integration SCRUM-235 — Unit Test Coverage SCRUM-157 through SCRUM-164 — Analysis outputs and stage wiring Continue integration with SCRUM-226/SCRUM-227 only where needed to connect export/alert outputs to dashboard/query/integration paths Prompt Quality Rule Cycle 015 must not repeat the Cycle 014 prompt regression. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #11 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 015 branch starts from updated develop after PR #11 merge, or branch creation is blocked with evidence. Product work advances dashboard query/page contracts and analysis integration from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 04 — Agent E delivery for SCRUM-279: [MEDIUM M9] Create SECURITY.md at repo root — missing industry-standar
- Story: SCRUM-279
- AC Focus: Medium Gap — M9\n\nThe repository root is missing a SECURITY.md file. This is an industry standard that GitHub surfaces when users report vulnerabilities.\n\n## Required content\n\n- Supported versions table\n- Vulnerability reporting process (email/form)\n- Response time commitment\n- Safe harbor statement for responsible disclosure\n- What information to include in a report\n\n## Acceptance Criteria\n\n- [ ] SECURITY.md created at repo root\n- [ ] Supported versions table populated\n- [ ] Responsible disclosure email/process documented\n- [ ] GitHub security advisories enabled on repository\n- [ ] Link from README.md to SECURITY.md\n\n## Related\n\n* SCRUM-61 (Repository security policy, secrets management, CODEOWNERS)\n* Gap audit Pass-2: Medium Gap M9
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 05 — Agent E delivery for SCRUM-285: [MEDIUM M18/M19] Create missing test fixture dirs (7 engines) and test
- Story: SCRUM-285
- AC Focus: Medium Gap — M18+M19\n\nTwo related test infrastructure gaps:\n\n M18 : tests/fixtures/ only covers 3 engines (analysis, collection, dashboard). Missing fixture subdirectories for 7 engines that will be built:\n- tests/fixtures/scoring/ \n- tests/fixtures/recommendations/ \n- tests/fixtures/pricing/ \n- tests/fixtures/discovery/ \n- tests/fixtures/playbook/ \n- tests/fixtures/llm/ (prompt template rendering)\n- tests/fixtures/reports/ (business reports)\n- tests/fixtures/exports/ (Excel/PDF exports)\n\n M19 : Missing test module files that will be required when engines are built:\n- tests/unit/test_scoring.py \n- tests/unit/test_recommendations.py \n- tests/unit/test_pricing.py \n- tests/unit/test_discovery.py \n- tests/unit/test_exports.py (Excel/PDF)\n- tests/unit/test_alerts.py \n- tests/unit/test_seed_import.py \n\nWithout these, building the engines will fail CI's 90% coverage gate.\n\n## Acceptance Criteria\n\n- [ ] All 8 missing fixture directories created with factories.py and example payloads\n- [ ] All 7 missing test module files created with at least a placeholder test class\n- [ ] CI still passes after fixture/test creation\n- [ ] Each fixture directory documents expected data format in a README or docstring\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gaps M18, M19\n* Related: SCRUM-235 (S10.5 Unit Test Coverage)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 06 — Agent E delivery for SCRUM-443: [W19][1.1.1] Create project directory structure
- Story: SCRUM-443
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.1
Task: Create project directory structure

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 07 — Agent E delivery for SCRUM-449: [W19][1.1.7] Create comprehensive README.md with setup guide
- Story: SCRUM-449
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.7
Task: Create comprehensive README.md with setup guide

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 08 — Agent E delivery for SCRUM-455: [W19][1.2.6] Create DiscoveryConfig model
- Story: SCRUM-455
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.6
Task: Create DiscoveryConfig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 09 — Agent E delivery for SCRUM-461: [W19][1.3.5] Create SearchResult model
- Story: SCRUM-461
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.5
Task: Create SearchResult model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 10 — Agent E delivery for SCRUM-467: [W19][1.3.11] Create OpportunityRanking model
- Story: SCRUM-467
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.11
Task: Create OpportunityRanking model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 11 — Agent E delivery for SCRUM-473: [W19][1.3.17] Create LLMUsageLog model
- Story: SCRUM-473
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.17
Task: Create LLMUsageLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 12 — Agent E delivery for SCRUM-479: [W19][1.3.23] Create NichePriceAnalysis model
- Story: SCRUM-479
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.23
Task: Create NichePriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 13 — Agent E delivery for SCRUM-485: [W19][1.3.29] Create database migration script
- Story: SCRUM-485
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.29
Task: Create database migration script

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 14 — Agent E delivery for SCRUM-491: [W19][1.4.5] Create --mode resume logic
- Story: SCRUM-491
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.5
Task: Create --mode resume logic

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 15 — Agent E delivery for SCRUM-497: [W19][1.5.4] Create cost tracking
- Story: SCRUM-497
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.4
Task: Create cost tracking

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 16 — Agent E delivery for SCRUM-503: [W19][1.6.3] Create export utilities
- Story: SCRUM-503
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.3
Task: Create export utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 17 — Agent E delivery for SCRUM-211: [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- Story: SCRUM-211
- AC Focus: Story Implement S8.7 — Playbook Dashboard Data Layer. Parent Epic SCRUM-23 — Epic 08: Playbook Engine Source ToDo_Fiverr(10)/To-Do/EPIC_08_PLAYBOOK.md DOD_Fiverr(7)/DOD/DOD_EPIC_08.md Gate: SCRUM-132 Scope Source tasks 8.7.1–8.7.3 covering playbook dashboard query/data layer, widget-ready payloads, and tests. Acceptance Criteria Playbook dashboard data is available from persisted playbook outputs. Outputs are dashboard-ready, source-traceable, and safe for sparse/missing playbook cases. Child tasks are created in later native task import waves or formally waived. Tests validate query output, missing data, and payload shape. DoD Complete when playbook dashboard data layer satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/playbook/s8-7-dashboard-data-layer
PR: feat(playbook): S8.7 Playbook Dashboard Data Layer Suggested Metadata Labels: wave-19, story, playbook, dashboard, data-layer, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_08.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 18 — Agent E delivery for SCRUM-253: [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and cont
- Story: SCRUM-253
- AC Focus: Purpose Cycle 011 continues from uploaded Cycle 010 repository and PM Pack. Live GitHub review shows PR #8 is open, mergeable, and CI/Codecov mirror checks are successful, but two unresolved Codex P2 review threads remain and must block merge under the project governance policy. Live PR State PR #8: feat(cycle-010): integrate multi-agent delivery and steward validations Source branch: cycle/010/integration Target branch: develop Status: open and mergeable at PM review time CI: successful codecov/project : successful Main branch: must remain untouched Blocking Codex Threads src/collection/checkpoint.py : load_checkpoint_stage_summary() should guard decoded checkpoint payloads that are valid non-object JSON, such as [] , so fallback behavior does not crash with AttributeError . src/dashboard/app.py : governance page readiness aggregation must include local_parity so a failing local parity signal is counted in category totals and cannot be hidden from the readiness summary. Scope Verify PR #8 live status, Codex review threads, GitHub Actions, Codecov project/patch, and branch policy. Fix both Codex P2 issues or formally disposition them if later proven invalid. Add regression tests for non-object checkpoint JSON fallback behavior. Add regression tests proving local_parity is present in governance page readiness categories and totals. Reply to both Codex threads with evidence-backed dispositions. Resolve Codex threads only after fixes, local validation, push, and passing checks. Merge PR #8 into develop only if authorized and all required gates remain green. Create cycle/011/integration from updated develop after PR #8 merges, or stop with evidence if blocked. Continue Phase 2 work using direct Cursor-agent Jira operations where assigned. Preserve the doubled Cursor task-volume rule: 10-20 substantive tasks per agent, with 12-16 preferred. Acceptance Criteria Both PR #8 Codex P2 findings are fixed or formally dispositioned with evidence. Both Codex review threads are resolved only after validation passes. GitHub Actions, Codecov project, Codecov patch, and local parity commands pass. PR #8 is merged only after all merge gates are satisfied and merge is authorized. Cycle 011 Cursor prompts include 10-20 substantive tasks per agent and direct Jira operations where assigned. Cycle 011 PM Pack is updated and attached in the final PM response.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 19 — Agent E delivery for SCRUM-259: [CYCLE 015] Merge PR #11 and advance dashboard query/pages plus analys
- Story: SCRUM-259
- AC Focus: Purpose Cycle 015 continues product-forward development after Cycle 014 delivered real Export and Alert product increments. The cycle must preserve the corrected high-detail Cursor prompt standard and avoid regressing into bare prompt lists or process-only work. Live GitHub Context PR #11: Cycle 014: export and alert product integration Source: cycle/014/integration Target: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: all active threads resolved in-cycle with evidence Product progress: Export System, Alert System, Integration Evidence, Coverage, Logging/Monitoring, Security/Data Hygiene Cycle 015 Product Focus After PR #11 is merged into develop, create cycle/015/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer SCRUM-214 — Dashboard Opportunities Page SCRUM-215 — Dashboard Keywords Page SCRUM-219 — Dashboard Run History Page SCRUM-228 — Dashboard App Entry Point SCRUM-231 — End-to-End Pipeline Integration SCRUM-235 — Unit Test Coverage SCRUM-157 through SCRUM-164 — Analysis outputs and stage wiring Continue integration with SCRUM-226/SCRUM-227 only where needed to connect export/alert outputs to dashboard/query/integration paths Prompt Quality Rule Cycle 015 must not repeat the Cycle 014 prompt regression. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #11 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 015 branch starts from updated develop after PR #11 merge, or branch creation is blocked with evidence. Product work advances dashboard query/page contracts and analysis integration from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 20 — Agent E delivery for SCRUM-279: [MEDIUM M9] Create SECURITY.md at repo root — missing industry-standar
- Story: SCRUM-279
- AC Focus: Medium Gap — M9\n\nThe repository root is missing a SECURITY.md file. This is an industry standard that GitHub surfaces when users report vulnerabilities.\n\n## Required content\n\n- Supported versions table\n- Vulnerability reporting process (email/form)\n- Response time commitment\n- Safe harbor statement for responsible disclosure\n- What information to include in a report\n\n## Acceptance Criteria\n\n- [ ] SECURITY.md created at repo root\n- [ ] Supported versions table populated\n- [ ] Responsible disclosure email/process documented\n- [ ] GitHub security advisories enabled on repository\n- [ ] Link from README.md to SECURITY.md\n\n## Related\n\n* SCRUM-61 (Repository security policy, secrets management, CODEOWNERS)\n* Gap audit Pass-2: Medium Gap M9
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 21 — Agent E delivery for SCRUM-285: [MEDIUM M18/M19] Create missing test fixture dirs (7 engines) and test
- Story: SCRUM-285
- AC Focus: Medium Gap — M18+M19\n\nTwo related test infrastructure gaps:\n\n M18 : tests/fixtures/ only covers 3 engines (analysis, collection, dashboard). Missing fixture subdirectories for 7 engines that will be built:\n- tests/fixtures/scoring/ \n- tests/fixtures/recommendations/ \n- tests/fixtures/pricing/ \n- tests/fixtures/discovery/ \n- tests/fixtures/playbook/ \n- tests/fixtures/llm/ (prompt template rendering)\n- tests/fixtures/reports/ (business reports)\n- tests/fixtures/exports/ (Excel/PDF exports)\n\n M19 : Missing test module files that will be required when engines are built:\n- tests/unit/test_scoring.py \n- tests/unit/test_recommendations.py \n- tests/unit/test_pricing.py \n- tests/unit/test_discovery.py \n- tests/unit/test_exports.py (Excel/PDF)\n- tests/unit/test_alerts.py \n- tests/unit/test_seed_import.py \n\nWithout these, building the engines will fail CI's 90% coverage gate.\n\n## Acceptance Criteria\n\n- [ ] All 8 missing fixture directories created with factories.py and example payloads\n- [ ] All 7 missing test module files created with at least a placeholder test class\n- [ ] CI still passes after fixture/test creation\n- [ ] Each fixture directory documents expected data format in a README or docstring\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gaps M18, M19\n* Related: SCRUM-235 (S10.5 Unit Test Coverage)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 22 — Agent E delivery for SCRUM-443: [W19][1.1.1] Create project directory structure
- Story: SCRUM-443
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.1
Task: Create project directory structure

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 23 — Agent E delivery for SCRUM-449: [W19][1.1.7] Create comprehensive README.md with setup guide
- Story: SCRUM-449
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.7
Task: Create comprehensive README.md with setup guide

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 24 — Agent E delivery for SCRUM-455: [W19][1.2.6] Create DiscoveryConfig model
- Story: SCRUM-455
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.6
Task: Create DiscoveryConfig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 25 — Agent E delivery for SCRUM-461: [W19][1.3.5] Create SearchResult model
- Story: SCRUM-461
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.5
Task: Create SearchResult model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 26 — Agent E delivery for SCRUM-467: [W19][1.3.11] Create OpportunityRanking model
- Story: SCRUM-467
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.11
Task: Create OpportunityRanking model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 27 — Agent E delivery for SCRUM-473: [W19][1.3.17] Create LLMUsageLog model
- Story: SCRUM-473
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.17
Task: Create LLMUsageLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 28 — Agent E delivery for SCRUM-479: [W19][1.3.23] Create NichePriceAnalysis model
- Story: SCRUM-479
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.23
Task: Create NichePriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 29 — Agent E delivery for SCRUM-485: [W19][1.3.29] Create database migration script
- Story: SCRUM-485
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.29
Task: Create database migration script

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 30 — Agent E delivery for SCRUM-491: [W19][1.4.5] Create --mode resume logic
- Story: SCRUM-491
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.5
Task: Create --mode resume logic

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 31 — Agent E delivery for SCRUM-497: [W19][1.5.4] Create cost tracking
- Story: SCRUM-497
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.4
Task: Create cost tracking

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 32 — Agent E delivery for SCRUM-503: [W19][1.6.3] Create export utilities
- Story: SCRUM-503
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.3
Task: Create export utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 33 — Agent E delivery for SCRUM-211: [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- Story: SCRUM-211
- AC Focus: Story Implement S8.7 — Playbook Dashboard Data Layer. Parent Epic SCRUM-23 — Epic 08: Playbook Engine Source ToDo_Fiverr(10)/To-Do/EPIC_08_PLAYBOOK.md DOD_Fiverr(7)/DOD/DOD_EPIC_08.md Gate: SCRUM-132 Scope Source tasks 8.7.1–8.7.3 covering playbook dashboard query/data layer, widget-ready payloads, and tests. Acceptance Criteria Playbook dashboard data is available from persisted playbook outputs. Outputs are dashboard-ready, source-traceable, and safe for sparse/missing playbook cases. Child tasks are created in later native task import waves or formally waived. Tests validate query output, missing data, and payload shape. DoD Complete when playbook dashboard data layer satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/playbook/s8-7-dashboard-data-layer
PR: feat(playbook): S8.7 Playbook Dashboard Data Layer Suggested Metadata Labels: wave-19, story, playbook, dashboard, data-layer, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_08.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 34 — Agent E delivery for SCRUM-253: [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and cont
- Story: SCRUM-253
- AC Focus: Purpose Cycle 011 continues from uploaded Cycle 010 repository and PM Pack. Live GitHub review shows PR #8 is open, mergeable, and CI/Codecov mirror checks are successful, but two unresolved Codex P2 review threads remain and must block merge under the project governance policy. Live PR State PR #8: feat(cycle-010): integrate multi-agent delivery and steward validations Source branch: cycle/010/integration Target branch: develop Status: open and mergeable at PM review time CI: successful codecov/project : successful Main branch: must remain untouched Blocking Codex Threads src/collection/checkpoint.py : load_checkpoint_stage_summary() should guard decoded checkpoint payloads that are valid non-object JSON, such as [] , so fallback behavior does not crash with AttributeError . src/dashboard/app.py : governance page readiness aggregation must include local_parity so a failing local parity signal is counted in category totals and cannot be hidden from the readiness summary. Scope Verify PR #8 live status, Codex review threads, GitHub Actions, Codecov project/patch, and branch policy. Fix both Codex P2 issues or formally disposition them if later proven invalid. Add regression tests for non-object checkpoint JSON fallback behavior. Add regression tests proving local_parity is present in governance page readiness categories and totals. Reply to both Codex threads with evidence-backed dispositions. Resolve Codex threads only after fixes, local validation, push, and passing checks. Merge PR #8 into develop only if authorized and all required gates remain green. Create cycle/011/integration from updated develop after PR #8 merges, or stop with evidence if blocked. Continue Phase 2 work using direct Cursor-agent Jira operations where assigned. Preserve the doubled Cursor task-volume rule: 10-20 substantive tasks per agent, with 12-16 preferred. Acceptance Criteria Both PR #8 Codex P2 findings are fixed or formally dispositioned with evidence. Both Codex review threads are resolved only after validation passes. GitHub Actions, Codecov project, Codecov patch, and local parity commands pass. PR #8 is merged only after all merge gates are satisfied and merge is authorized. Cycle 011 Cursor prompts include 10-20 substantive tasks per agent and direct Jira operations where assigned. Cycle 011 PM Pack is updated and attached in the final PM response.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 35 — Agent E delivery for SCRUM-259: [CYCLE 015] Merge PR #11 and advance dashboard query/pages plus analys
- Story: SCRUM-259
- AC Focus: Purpose Cycle 015 continues product-forward development after Cycle 014 delivered real Export and Alert product increments. The cycle must preserve the corrected high-detail Cursor prompt standard and avoid regressing into bare prompt lists or process-only work. Live GitHub Context PR #11: Cycle 014: export and alert product integration Source: cycle/014/integration Target: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: all active threads resolved in-cycle with evidence Product progress: Export System, Alert System, Integration Evidence, Coverage, Logging/Monitoring, Security/Data Hygiene Cycle 015 Product Focus After PR #11 is merged into develop, create cycle/015/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer SCRUM-214 — Dashboard Opportunities Page SCRUM-215 — Dashboard Keywords Page SCRUM-219 — Dashboard Run History Page SCRUM-228 — Dashboard App Entry Point SCRUM-231 — End-to-End Pipeline Integration SCRUM-235 — Unit Test Coverage SCRUM-157 through SCRUM-164 — Analysis outputs and stage wiring Continue integration with SCRUM-226/SCRUM-227 only where needed to connect export/alert outputs to dashboard/query/integration paths Prompt Quality Rule Cycle 015 must not repeat the Cycle 014 prompt regression. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #11 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 015 branch starts from updated develop after PR #11 merge, or branch creation is blocked with evidence. Product work advances dashboard query/page contracts and analysis integration from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 36 — Agent E delivery for SCRUM-279: [MEDIUM M9] Create SECURITY.md at repo root — missing industry-standar
- Story: SCRUM-279
- AC Focus: Medium Gap — M9\n\nThe repository root is missing a SECURITY.md file. This is an industry standard that GitHub surfaces when users report vulnerabilities.\n\n## Required content\n\n- Supported versions table\n- Vulnerability reporting process (email/form)\n- Response time commitment\n- Safe harbor statement for responsible disclosure\n- What information to include in a report\n\n## Acceptance Criteria\n\n- [ ] SECURITY.md created at repo root\n- [ ] Supported versions table populated\n- [ ] Responsible disclosure email/process documented\n- [ ] GitHub security advisories enabled on repository\n- [ ] Link from README.md to SECURITY.md\n\n## Related\n\n* SCRUM-61 (Repository security policy, secrets management, CODEOWNERS)\n* Gap audit Pass-2: Medium Gap M9
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 37 — Agent E delivery for SCRUM-285: [MEDIUM M18/M19] Create missing test fixture dirs (7 engines) and test
- Story: SCRUM-285
- AC Focus: Medium Gap — M18+M19\n\nTwo related test infrastructure gaps:\n\n M18 : tests/fixtures/ only covers 3 engines (analysis, collection, dashboard). Missing fixture subdirectories for 7 engines that will be built:\n- tests/fixtures/scoring/ \n- tests/fixtures/recommendations/ \n- tests/fixtures/pricing/ \n- tests/fixtures/discovery/ \n- tests/fixtures/playbook/ \n- tests/fixtures/llm/ (prompt template rendering)\n- tests/fixtures/reports/ (business reports)\n- tests/fixtures/exports/ (Excel/PDF exports)\n\n M19 : Missing test module files that will be required when engines are built:\n- tests/unit/test_scoring.py \n- tests/unit/test_recommendations.py \n- tests/unit/test_pricing.py \n- tests/unit/test_discovery.py \n- tests/unit/test_exports.py (Excel/PDF)\n- tests/unit/test_alerts.py \n- tests/unit/test_seed_import.py \n\nWithout these, building the engines will fail CI's 90% coverage gate.\n\n## Acceptance Criteria\n\n- [ ] All 8 missing fixture directories created with factories.py and example payloads\n- [ ] All 7 missing test module files created with at least a placeholder test class\n- [ ] CI still passes after fixture/test creation\n- [ ] Each fixture directory documents expected data format in a README or docstring\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gaps M18, M19\n* Related: SCRUM-235 (S10.5 Unit Test Coverage)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 38 — Agent E delivery for SCRUM-443: [W19][1.1.1] Create project directory structure
- Story: SCRUM-443
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.1
Task: Create project directory structure

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 39 — Agent E delivery for SCRUM-449: [W19][1.1.7] Create comprehensive README.md with setup guide
- Story: SCRUM-449
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.7
Task: Create comprehensive README.md with setup guide

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 40 — Agent E delivery for SCRUM-455: [W19][1.2.6] Create DiscoveryConfig model
- Story: SCRUM-455
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.6
Task: Create DiscoveryConfig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 41 — Agent E delivery for SCRUM-461: [W19][1.3.5] Create SearchResult model
- Story: SCRUM-461
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.5
Task: Create SearchResult model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 42 — Agent E delivery for SCRUM-467: [W19][1.3.11] Create OpportunityRanking model
- Story: SCRUM-467
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.11
Task: Create OpportunityRanking model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 43 — Agent E delivery for SCRUM-473: [W19][1.3.17] Create LLMUsageLog model
- Story: SCRUM-473
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.17
Task: Create LLMUsageLog model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 44 — Agent E delivery for SCRUM-479: [W19][1.3.23] Create NichePriceAnalysis model
- Story: SCRUM-479
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.23
Task: Create NichePriceAnalysis model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 45 — Agent E delivery for SCRUM-485: [W19][1.3.29] Create database migration script
- Story: SCRUM-485
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.29
Task: Create database migration script

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 46 — Agent E delivery for SCRUM-491: [W19][1.4.5] Create --mode resume logic
- Story: SCRUM-491
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.5
Task: Create --mode resume logic

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 47 — Agent E delivery for SCRUM-497: [W19][1.5.4] Create cost tracking
- Story: SCRUM-497
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.4
Task: Create cost tracking

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 48 — Agent E delivery for SCRUM-503: [W19][1.6.3] Create export utilities
- Story: SCRUM-503
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.3
Task: Create export utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 49 — Agent E delivery for SCRUM-211: [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- Story: SCRUM-211
- AC Focus: Story Implement S8.7 — Playbook Dashboard Data Layer. Parent Epic SCRUM-23 — Epic 08: Playbook Engine Source ToDo_Fiverr(10)/To-Do/EPIC_08_PLAYBOOK.md DOD_Fiverr(7)/DOD/DOD_EPIC_08.md Gate: SCRUM-132 Scope Source tasks 8.7.1–8.7.3 covering playbook dashboard query/data layer, widget-ready payloads, and tests. Acceptance Criteria Playbook dashboard data is available from persisted playbook outputs. Outputs are dashboard-ready, source-traceable, and safe for sparse/missing playbook cases. Child tasks are created in later native task import waves or formally waived. Tests validate query output, missing data, and payload shape. DoD Complete when playbook dashboard data layer satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/playbook/s8-7-dashboard-data-layer
PR: feat(playbook): S8.7 Playbook Dashboard Data Layer Suggested Metadata Labels: wave-19, story, playbook, dashboard, data-layer, source-todo-pack, source-dod-pack
Priority: High
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_08.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 50 — Agent E delivery for SCRUM-253: [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and cont
- Story: SCRUM-253
- AC Focus: Purpose Cycle 011 continues from uploaded Cycle 010 repository and PM Pack. Live GitHub review shows PR #8 is open, mergeable, and CI/Codecov mirror checks are successful, but two unresolved Codex P2 review threads remain and must block merge under the project governance policy. Live PR State PR #8: feat(cycle-010): integrate multi-agent delivery and steward validations Source branch: cycle/010/integration Target branch: develop Status: open and mergeable at PM review time CI: successful codecov/project : successful Main branch: must remain untouched Blocking Codex Threads src/collection/checkpoint.py : load_checkpoint_stage_summary() should guard decoded checkpoint payloads that are valid non-object JSON, such as [] , so fallback behavior does not crash with AttributeError . src/dashboard/app.py : governance page readiness aggregation must include local_parity so a failing local parity signal is counted in category totals and cannot be hidden from the readiness summary. Scope Verify PR #8 live status, Codex review threads, GitHub Actions, Codecov project/patch, and branch policy. Fix both Codex P2 issues or formally disposition them if later proven invalid. Add regression tests for non-object checkpoint JSON fallback behavior. Add regression tests proving local_parity is present in governance page readiness categories and totals. Reply to both Codex threads with evidence-backed dispositions. Resolve Codex threads only after fixes, local validation, push, and passing checks. Merge PR #8 into develop only if authorized and all required gates remain green. Create cycle/011/integration from updated develop after PR #8 merges, or stop with evidence if blocked. Continue Phase 2 work using direct Cursor-agent Jira operations where assigned. Preserve the doubled Cursor task-volume rule: 10-20 substantive tasks per agent, with 12-16 preferred. Acceptance Criteria Both PR #8 Codex P2 findings are fixed or formally dispositioned with evidence. Both Codex review threads are resolved only after validation passes. GitHub Actions, Codecov project, Codecov patch, and local parity commands pass. PR #8 is merged only after all merge gates are satisfied and merge is authorized. Cycle 011 Cursor prompts include 10-20 substantive tasks per agent and direct Jira operations where assigned. Cycle 011 PM Pack is updated and attached in the final PM response.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 51 — Agent E delivery for SCRUM-259: [CYCLE 015] Merge PR #11 and advance dashboard query/pages plus analys
- Story: SCRUM-259
- AC Focus: Purpose Cycle 015 continues product-forward development after Cycle 014 delivered real Export and Alert product increments. The cycle must preserve the corrected high-detail Cursor prompt standard and avoid regressing into bare prompt lists or process-only work. Live GitHub Context PR #11: Cycle 014: export and alert product integration Source: cycle/014/integration Target: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: all active threads resolved in-cycle with evidence Product progress: Export System, Alert System, Integration Evidence, Coverage, Logging/Monitoring, Security/Data Hygiene Cycle 015 Product Focus After PR #11 is merged into develop, create cycle/015/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer SCRUM-214 — Dashboard Opportunities Page SCRUM-215 — Dashboard Keywords Page SCRUM-219 — Dashboard Run History Page SCRUM-228 — Dashboard App Entry Point SCRUM-231 — End-to-End Pipeline Integration SCRUM-235 — Unit Test Coverage SCRUM-157 through SCRUM-164 — Analysis outputs and stage wiring Continue integration with SCRUM-226/SCRUM-227 only where needed to connect export/alert outputs to dashboard/query/integration paths Prompt Quality Rule Cycle 015 must not repeat the Cycle 014 prompt regression. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #11 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 015 branch starts from updated develop after PR #11 merge, or branch creation is blocked with evidence. Product work advances dashboard query/page contracts and analysis integration from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 52 — Agent E delivery for SCRUM-279: [MEDIUM M9] Create SECURITY.md at repo root — missing industry-standar
- Story: SCRUM-279
- AC Focus: Medium Gap — M9\n\nThe repository root is missing a SECURITY.md file. This is an industry standard that GitHub surfaces when users report vulnerabilities.\n\n## Required content\n\n- Supported versions table\n- Vulnerability reporting process (email/form)\n- Response time commitment\n- Safe harbor statement for responsible disclosure\n- What information to include in a report\n\n## Acceptance Criteria\n\n- [ ] SECURITY.md created at repo root\n- [ ] Supported versions table populated\n- [ ] Responsible disclosure email/process documented\n- [ ] GitHub security advisories enabled on repository\n- [ ] Link from README.md to SECURITY.md\n\n## Related\n\n* SCRUM-61 (Repository security policy, secrets management, CODEOWNERS)\n* Gap audit Pass-2: Medium Gap M9
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 53 — Agent E delivery for SCRUM-285: [MEDIUM M18/M19] Create missing test fixture dirs (7 engines) and test
- Story: SCRUM-285
- AC Focus: Medium Gap — M18+M19\n\nTwo related test infrastructure gaps:\n\n M18 : tests/fixtures/ only covers 3 engines (analysis, collection, dashboard). Missing fixture subdirectories for 7 engines that will be built:\n- tests/fixtures/scoring/ \n- tests/fixtures/recommendations/ \n- tests/fixtures/pricing/ \n- tests/fixtures/discovery/ \n- tests/fixtures/playbook/ \n- tests/fixtures/llm/ (prompt template rendering)\n- tests/fixtures/reports/ (business reports)\n- tests/fixtures/exports/ (Excel/PDF exports)\n\n M19 : Missing test module files that will be required when engines are built:\n- tests/unit/test_scoring.py \n- tests/unit/test_recommendations.py \n- tests/unit/test_pricing.py \n- tests/unit/test_discovery.py \n- tests/unit/test_exports.py (Excel/PDF)\n- tests/unit/test_alerts.py \n- tests/unit/test_seed_import.py \n\nWithout these, building the engines will fail CI's 90% coverage gate.\n\n## Acceptance Criteria\n\n- [ ] All 8 missing fixture directories created with factories.py and example payloads\n- [ ] All 7 missing test module files created with at least a placeholder test class\n- [ ] CI still passes after fixture/test creation\n- [ ] Each fixture directory documents expected data format in a README or docstring\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gaps M18, M19\n* Related: SCRUM-235 (S10.5 Unit Test Coverage)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 54 — Agent E delivery for SCRUM-443: [W19][1.1.1] Create project directory structure
- Story: SCRUM-443
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.1
Task: Create project directory structure

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 55 — Agent E delivery for SCRUM-449: [W19][1.1.7] Create comprehensive README.md with setup guide
- Story: SCRUM-449
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.7
Task: Create comprehensive README.md with setup guide

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.


## Validation Commands
- ruff check automation/ src/ tests/
- mypy src/ automation/ --ignore-missing-imports
- pytest tests/unit/ --timeout=30 --tb=no -q
- python automation/ai_cycle_controller.py brain-check
- python automation/ai_cycle_controller.py pm-pack-audit --check-only

## Report
- Write: docs/cycle_reports/CYCLE_078_AGENT_E.md
- Final line must be: AGENT_COMPLETE

Generated at: 2026-06-14T00:40:54.272445+00:00

---

END OF PROMPT
