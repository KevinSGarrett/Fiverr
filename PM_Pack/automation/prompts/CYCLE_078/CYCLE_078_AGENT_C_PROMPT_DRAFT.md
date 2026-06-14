Cycle 078 — Agent C Prompt

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
You are Agent C for Cycle 078 on branch cycle/078/integration.
Lane description: Integration checks, validation run, cycle report
Your lane owns:
- docs/cycle_reports/**
- PM_Pack/10_cycle_log/**
You MUST NOT touch:
- src/**

## Model Policy (MANDATORY)
- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED

## Autonomy rule
- Proceed autonomously through all tasks without pausing for confirmation.
- If blocked, document blocker and continue with next executable task.
- Do not include git add/commit/push instructions in this prompt.

## Jira Scope
- SCRUM-229: [DASHBOARD] S9.15 Mobile Optimization
  - AC: Story Implement S9.15 — Mobile Optimization. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Sc
  - DoD: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- SCRUM-254: [PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt dept
  - AC: Purpose PM audit confirms Jira is being updated, but not yet used as the primary source-of-truth planning and completion system across the full 250+ item board. The operator raised a valid concern tha
  - DoD: 
- SCRUM-260: [CYCLE 016] Merge PR #12 and advance runtime dashboard/integration validation
  - AC: Purpose Cycle 016 continues product-forward development after Cycle 015 advanced dashboard query/page contracts and analysis output/stage wiring. The cycle should begin with a short PR #12 merge gate,
  - DoD: 
- SCRUM-280: [MEDIUM M10] Create .github/dependabot.yml — automated dependency security updat
  - AC: Medium Gap — M10\n\n .github/dependabot.yml is missing from the repository. Dependabot auto-creates PRs when dependencies have security vulnerabilities or newer versions.\n\nWith openpyxl , weasyprint
  - DoD: 
- SCRUM-286: [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, missing DL 
  - AC: Medium Gap — M23+M24+M25+M26\n\nFour PM/governance documentation gaps from Pass-3:\n\n M23 : docs/jira/ACTIVE_STORY_DOD_LEDGER.md header says "Cycle 014" but its body contains Cycle 017 rows. The head
  - DoD: 
- SCRUM-444: [W19][1.1.2] Create pyproject.toml with all dependencies
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.2
Task: Create pyproject.toml with all dependencies

This sub-task makes the E01 task-level work tra
  - DoD: 
- SCRUM-450: [W19][1.2.1] Create config.yaml master template
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.1
Task: Create config.yaml master template

This sub-task makes the E01 task-level work trackable i
  - DoD: 
- SCRUM-456: [W19][1.2.7] Create config validation tests
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.7
Task: Create config validation tests

This sub-task makes the E01 task-level work trackable in Ji
  - DoD: 
- SCRUM-462: [W19][1.3.6] Create Gig model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.6
Task: Create Gig model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-468: [W19][1.3.12] Create Recommendation model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.12
Task: Create Recommendation model

This sub-task makes the E01 task-level work trackable in Jira
  - DoD: 
- SCRUM-474: [W19][1.3.18] Create LLMCache model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.18
Task: Create LLMCache model

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-480: [W19][1.3.24] Create DiscoveryOutcome model
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.24
Task: Create DiscoveryOutcome model

This sub-task makes the E01 task-level work trackable in Ji
  - DoD: 
- SCRUM-486: [W19][1.3.30] Create model unit tests
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.30
Task: Create model unit tests

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 
- SCRUM-492: [W19][1.4.6] Create --mode full pipeline sequence
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.6
Task: Create --mode full pipeline sequence

This sub-task makes the E01 task-level work trackable
  - DoD: 
- SCRUM-498: [W19][1.5.5] Create self-correction retry
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.5
Task: Create self-correction retry

This sub-task makes the E01 task-level work trackable in Jira
  - DoD: 
- SCRUM-504: [W19][1.6.4] Create hash utilities
  - AC: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.4
Task: Create hash utilities

This sub-task makes the E01 task-level work trackable in Jira.
  - DoD: 

## Tasks
### TASK 01 — Agent C delivery for SCRUM-229: [DASHBOARD] S9.15 Mobile Optimization
- Story: SCRUM-229
- AC Focus: Story Implement S9.15 — Mobile Optimization. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.15.1–9.15.3 covering responsive/mobile layout, key page usability on small screens, and tests/review. Acceptance Criteria Dashboard pages remain usable on narrower/mobile layouts where supported. Critical tables/cards/filters degrade gracefully without losing core functionality. Child tasks are created in later native task import waves or formally waived. QA review validates mobile/responsive behavior. DoD Complete when mobile optimization satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-15-mobile-optimization
PR: feat(dashboard): S9.15 Mobile Optimization Suggested Metadata Labels: wave-19, story, dashboard, mobile, responsive, source-todo-pack, source-dod-pack
Priority: Medium
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 02 — Agent C delivery for SCRUM-254: [PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor p
- Story: SCRUM-254
- AC Focus: Purpose PM audit confirms Jira is being updated, but not yet used as the primary source-of-truth planning and completion system across the full 250+ item board. The operator raised a valid concern that cycles appear to add/update a subset of cycle/governance tickets while not exhaustively planning from the existing Jira backlog, acceptance criteria, and definitions of done. Findings Work has often been PR/change-driven and then mapped to Jira afterward, rather than selected from Jira AC/DoD first. Cycle/governance tasks are created regularly, while full board AC/DoD review is not consistently performed before implementation. Story statuses move to In Progress for partial work, but there is no mandatory AC/DoD progress ledger for every active story. Cursor prompts remain too short/detail-light for the desired autonomous execution standard. Uploaded Cycle 011 archive includes uncommitted local work not reflected in live PR #9, showing handoff and merge-gate risk. Rule Changes Every cycle begins with a full Jira board inventory and issue-type/status summary. Active work must be selected from Jira issues before coding. Every agent task must map to exact Jira issue keys and AC/DoD bullets. Every touched Jira issue must receive an AC/DoD progress update. Done is only allowed after full source AC/DoD completion, not partial scaffold completion. Cursor agents may perform Jira operations as assigned. Normal agent task load doubles again: minimum 20, target 24-32, maximum 40 substantive tasks per Cursor agent. Agent prompts must meet minimum 6,000 words per agent prompt, target 8,000-12,000 words, with no hard cap if organized and useful. Any shorter prompt requires both TASK-COUNT WAIVER and PROMPT-DETAIL WAIVER with a clear reason. Acceptance Criteria PM Pack contains full-board AC/DoD-first protocol. PM Pack contains doubled task-volume/prompt-depth protocol. Cycle 012 prompts comply with 20+ substantive tasks and long-form detail. PR #9 gate accounts for uncommitted local archive changes before merge. Future cycles reject shallow prompts or Jira-after-the-fact planning. Status Created by PM during Cycle 012 audit and governance correction.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 03 — Agent C delivery for SCRUM-260: [CYCLE 016] Merge PR #12 and advance runtime dashboard/integration val
- Story: SCRUM-260
- AC Focus: Purpose Cycle 016 continues product-forward development after Cycle 015 advanced dashboard query/page contracts and analysis output/stage wiring. The cycle should begin with a short PR #12 merge gate, then move into runtime dashboard acceptance, end-to-end integration validation, data integrity, and first-run readiness work. Live GitHub Context PR #12: feat(cycle-015): integrate product increments with steward evidence Source branch: cycle/015/integration Target branch: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: one Codex thread was fixed, replied to with evidence, and resolved in-cycle Product progress: dashboard query/page contracts, analysis output contracts, integration evidence compatibility, 449 passing tests, 93.46% coverage Cycle 016 Product Focus After PR #12 is merged into develop, create cycle/016/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer runtime adoption SCRUM-214 — Opportunities Page runtime acceptance SCRUM-215 — Keywords Page runtime acceptance SCRUM-219 — Run History Page runtime acceptance SCRUM-228 — Dashboard App Entry Point runtime startup and diagnostics SCRUM-231 — End-to-End Pipeline Integration evidence SCRUM-232 — Data Integrity Validation SCRUM-235 — Unit Test Coverage SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-237 — Logging and Monitoring SCRUM-239 — First Run Validation SCRUM-241 — Security and Data Hygiene SCRUM-157 through SCRUM-164 — Analysis output/stage wiring closure evidence Prompt Quality Rule Cycle 016 must preserve the corrected high-detail Cursor prompt standard. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #12 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 016 branch starts from updated develop after PR #12 merge, or branch creation is blocked with evidence. Product work advances runtime dashboard acceptance and integration validation from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 04 — Agent C delivery for SCRUM-280: [MEDIUM M10] Create .github/dependabot.yml — automated dependency secu
- Story: SCRUM-280
- AC Focus: Medium Gap — M10\n\n .github/dependabot.yml is missing from the repository. Dependabot auto-creates PRs when dependencies have security vulnerabilities or newer versions.\n\nWith openpyxl , weasyprint , playwright , openai , pydantic , and others in pyproject.toml, automated dependency updates are critical for security.\n\n## Acceptance Criteria\n\n- [ ] .github/dependabot.yml created\n- [ ] pip ecosystem configured with weekly update schedule\n- [ ] GitHub Actions ecosystem configured (for CI workflow deps)\n- [ ] Auto-merge for minor/patch enabled where safe\n- [ ] Dependabot alerts enabled on repository settings\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M10\n* Related: SCRUM-75 (Security controls)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 05 — Agent C delivery for SCRUM-286: [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, m
- Story: SCRUM-286
- AC Focus: Medium Gap — M23+M24+M25+M26\n\nFour PM/governance documentation gaps from Pass-3:\n\n M23 : docs/jira/ACTIVE_STORY_DOD_LEDGER.md header says "Cycle 014" but its body contains Cycle 017 rows. The header is stale by 3 cycles.\n\n M24 : The score-table design pivot (KeywordScore table → ScoreComponent + FinalScore key-value design) was made without a Decision Log entry. No rationale is documented in DECISION_LOG.md for this architectural shift.\n\n M25 : AGENT_ROSTER.md assigns Agent C ownership of src/scoring/ , src/pricing/ , src/discovery/ — three directories that don't exist — plus test_scoring.py , test_pricing.py , test_discovery.py — three test files that don't exist. Cycle allocation is miscalibrated.\n\n M26 : JIRA_FIELD_STANDARDS.md specifies a description template (## Overview / ## Spec Reference / ## Acceptance Criteria / ## Technical Notes / ## Agent Assignment) that doesn't match the actual template in use (## Story / ## Parent Epic / ## Source / ## Acceptance Criteria / ## DoD / ## GitHub Alignment / ## Suggested Metadata). The standard is obsolete.\n\n## Acceptance Criteria\n\n- [ ] M23: ACTIVE_STORY_DOD_LEDGER.md header updated to current cycle\n- [ ] M24: New DL entry added to DECISION_LOG.md documenting KeywordScore → ScoreComponent+FinalScore design pivot\n- [ ] M25: AGENT_ROSTER.md updated to reflect Agent C's actual capacity and the unbuilt engine situation\n- [ ] M26: JIRA_FIELD_STANDARDS.md description template section updated to match actual practice\n\n## Source Reference\n\n* Gap audit Pass-3: Medium Gaps M23, M24, M25, M26
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 06 — Agent C delivery for SCRUM-444: [W19][1.1.2] Create pyproject.toml with all dependencies
- Story: SCRUM-444
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.2
Task: Create pyproject.toml with all dependencies

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 07 — Agent C delivery for SCRUM-450: [W19][1.2.1] Create config.yaml master template
- Story: SCRUM-450
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.1
Task: Create config.yaml master template

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 08 — Agent C delivery for SCRUM-456: [W19][1.2.7] Create config validation tests
- Story: SCRUM-456
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.7
Task: Create config validation tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 09 — Agent C delivery for SCRUM-462: [W19][1.3.6] Create Gig model
- Story: SCRUM-462
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.6
Task: Create Gig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 10 — Agent C delivery for SCRUM-468: [W19][1.3.12] Create Recommendation model
- Story: SCRUM-468
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.12
Task: Create Recommendation model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 11 — Agent C delivery for SCRUM-474: [W19][1.3.18] Create LLMCache model
- Story: SCRUM-474
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.18
Task: Create LLMCache model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 12 — Agent C delivery for SCRUM-480: [W19][1.3.24] Create DiscoveryOutcome model
- Story: SCRUM-480
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.24
Task: Create DiscoveryOutcome model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 13 — Agent C delivery for SCRUM-486: [W19][1.3.30] Create model unit tests
- Story: SCRUM-486
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.30
Task: Create model unit tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 14 — Agent C delivery for SCRUM-492: [W19][1.4.6] Create --mode full pipeline sequence
- Story: SCRUM-492
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.6
Task: Create --mode full pipeline sequence

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 15 — Agent C delivery for SCRUM-498: [W19][1.5.5] Create self-correction retry
- Story: SCRUM-498
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.5
Task: Create self-correction retry

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 16 — Agent C delivery for SCRUM-504: [W19][1.6.4] Create hash utilities
- Story: SCRUM-504
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.4
Task: Create hash utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 17 — Agent C delivery for SCRUM-229: [DASHBOARD] S9.15 Mobile Optimization
- Story: SCRUM-229
- AC Focus: Story Implement S9.15 — Mobile Optimization. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.15.1–9.15.3 covering responsive/mobile layout, key page usability on small screens, and tests/review. Acceptance Criteria Dashboard pages remain usable on narrower/mobile layouts where supported. Critical tables/cards/filters degrade gracefully without losing core functionality. Child tasks are created in later native task import waves or formally waived. QA review validates mobile/responsive behavior. DoD Complete when mobile optimization satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-15-mobile-optimization
PR: feat(dashboard): S9.15 Mobile Optimization Suggested Metadata Labels: wave-19, story, dashboard, mobile, responsive, source-todo-pack, source-dod-pack
Priority: Medium
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 18 — Agent C delivery for SCRUM-254: [PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor p
- Story: SCRUM-254
- AC Focus: Purpose PM audit confirms Jira is being updated, but not yet used as the primary source-of-truth planning and completion system across the full 250+ item board. The operator raised a valid concern that cycles appear to add/update a subset of cycle/governance tickets while not exhaustively planning from the existing Jira backlog, acceptance criteria, and definitions of done. Findings Work has often been PR/change-driven and then mapped to Jira afterward, rather than selected from Jira AC/DoD first. Cycle/governance tasks are created regularly, while full board AC/DoD review is not consistently performed before implementation. Story statuses move to In Progress for partial work, but there is no mandatory AC/DoD progress ledger for every active story. Cursor prompts remain too short/detail-light for the desired autonomous execution standard. Uploaded Cycle 011 archive includes uncommitted local work not reflected in live PR #9, showing handoff and merge-gate risk. Rule Changes Every cycle begins with a full Jira board inventory and issue-type/status summary. Active work must be selected from Jira issues before coding. Every agent task must map to exact Jira issue keys and AC/DoD bullets. Every touched Jira issue must receive an AC/DoD progress update. Done is only allowed after full source AC/DoD completion, not partial scaffold completion. Cursor agents may perform Jira operations as assigned. Normal agent task load doubles again: minimum 20, target 24-32, maximum 40 substantive tasks per Cursor agent. Agent prompts must meet minimum 6,000 words per agent prompt, target 8,000-12,000 words, with no hard cap if organized and useful. Any shorter prompt requires both TASK-COUNT WAIVER and PROMPT-DETAIL WAIVER with a clear reason. Acceptance Criteria PM Pack contains full-board AC/DoD-first protocol. PM Pack contains doubled task-volume/prompt-depth protocol. Cycle 012 prompts comply with 20+ substantive tasks and long-form detail. PR #9 gate accounts for uncommitted local archive changes before merge. Future cycles reject shallow prompts or Jira-after-the-fact planning. Status Created by PM during Cycle 012 audit and governance correction.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 19 — Agent C delivery for SCRUM-260: [CYCLE 016] Merge PR #12 and advance runtime dashboard/integration val
- Story: SCRUM-260
- AC Focus: Purpose Cycle 016 continues product-forward development after Cycle 015 advanced dashboard query/page contracts and analysis output/stage wiring. The cycle should begin with a short PR #12 merge gate, then move into runtime dashboard acceptance, end-to-end integration validation, data integrity, and first-run readiness work. Live GitHub Context PR #12: feat(cycle-015): integrate product increments with steward evidence Source branch: cycle/015/integration Target branch: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: one Codex thread was fixed, replied to with evidence, and resolved in-cycle Product progress: dashboard query/page contracts, analysis output contracts, integration evidence compatibility, 449 passing tests, 93.46% coverage Cycle 016 Product Focus After PR #12 is merged into develop, create cycle/016/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer runtime adoption SCRUM-214 — Opportunities Page runtime acceptance SCRUM-215 — Keywords Page runtime acceptance SCRUM-219 — Run History Page runtime acceptance SCRUM-228 — Dashboard App Entry Point runtime startup and diagnostics SCRUM-231 — End-to-End Pipeline Integration evidence SCRUM-232 — Data Integrity Validation SCRUM-235 — Unit Test Coverage SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-237 — Logging and Monitoring SCRUM-239 — First Run Validation SCRUM-241 — Security and Data Hygiene SCRUM-157 through SCRUM-164 — Analysis output/stage wiring closure evidence Prompt Quality Rule Cycle 016 must preserve the corrected high-detail Cursor prompt standard. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #12 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 016 branch starts from updated develop after PR #12 merge, or branch creation is blocked with evidence. Product work advances runtime dashboard acceptance and integration validation from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 20 — Agent C delivery for SCRUM-280: [MEDIUM M10] Create .github/dependabot.yml — automated dependency secu
- Story: SCRUM-280
- AC Focus: Medium Gap — M10\n\n .github/dependabot.yml is missing from the repository. Dependabot auto-creates PRs when dependencies have security vulnerabilities or newer versions.\n\nWith openpyxl , weasyprint , playwright , openai , pydantic , and others in pyproject.toml, automated dependency updates are critical for security.\n\n## Acceptance Criteria\n\n- [ ] .github/dependabot.yml created\n- [ ] pip ecosystem configured with weekly update schedule\n- [ ] GitHub Actions ecosystem configured (for CI workflow deps)\n- [ ] Auto-merge for minor/patch enabled where safe\n- [ ] Dependabot alerts enabled on repository settings\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M10\n* Related: SCRUM-75 (Security controls)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 21 — Agent C delivery for SCRUM-286: [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, m
- Story: SCRUM-286
- AC Focus: Medium Gap — M23+M24+M25+M26\n\nFour PM/governance documentation gaps from Pass-3:\n\n M23 : docs/jira/ACTIVE_STORY_DOD_LEDGER.md header says "Cycle 014" but its body contains Cycle 017 rows. The header is stale by 3 cycles.\n\n M24 : The score-table design pivot (KeywordScore table → ScoreComponent + FinalScore key-value design) was made without a Decision Log entry. No rationale is documented in DECISION_LOG.md for this architectural shift.\n\n M25 : AGENT_ROSTER.md assigns Agent C ownership of src/scoring/ , src/pricing/ , src/discovery/ — three directories that don't exist — plus test_scoring.py , test_pricing.py , test_discovery.py — three test files that don't exist. Cycle allocation is miscalibrated.\n\n M26 : JIRA_FIELD_STANDARDS.md specifies a description template (## Overview / ## Spec Reference / ## Acceptance Criteria / ## Technical Notes / ## Agent Assignment) that doesn't match the actual template in use (## Story / ## Parent Epic / ## Source / ## Acceptance Criteria / ## DoD / ## GitHub Alignment / ## Suggested Metadata). The standard is obsolete.\n\n## Acceptance Criteria\n\n- [ ] M23: ACTIVE_STORY_DOD_LEDGER.md header updated to current cycle\n- [ ] M24: New DL entry added to DECISION_LOG.md documenting KeywordScore → ScoreComponent+FinalScore design pivot\n- [ ] M25: AGENT_ROSTER.md updated to reflect Agent C's actual capacity and the unbuilt engine situation\n- [ ] M26: JIRA_FIELD_STANDARDS.md description template section updated to match actual practice\n\n## Source Reference\n\n* Gap audit Pass-3: Medium Gaps M23, M24, M25, M26
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 22 — Agent C delivery for SCRUM-444: [W19][1.1.2] Create pyproject.toml with all dependencies
- Story: SCRUM-444
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.2
Task: Create pyproject.toml with all dependencies

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 23 — Agent C delivery for SCRUM-450: [W19][1.2.1] Create config.yaml master template
- Story: SCRUM-450
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.1
Task: Create config.yaml master template

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 24 — Agent C delivery for SCRUM-456: [W19][1.2.7] Create config validation tests
- Story: SCRUM-456
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.7
Task: Create config validation tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 25 — Agent C delivery for SCRUM-462: [W19][1.3.6] Create Gig model
- Story: SCRUM-462
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.6
Task: Create Gig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 26 — Agent C delivery for SCRUM-468: [W19][1.3.12] Create Recommendation model
- Story: SCRUM-468
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.12
Task: Create Recommendation model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 27 — Agent C delivery for SCRUM-474: [W19][1.3.18] Create LLMCache model
- Story: SCRUM-474
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.18
Task: Create LLMCache model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 28 — Agent C delivery for SCRUM-480: [W19][1.3.24] Create DiscoveryOutcome model
- Story: SCRUM-480
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.24
Task: Create DiscoveryOutcome model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 29 — Agent C delivery for SCRUM-486: [W19][1.3.30] Create model unit tests
- Story: SCRUM-486
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.30
Task: Create model unit tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 30 — Agent C delivery for SCRUM-492: [W19][1.4.6] Create --mode full pipeline sequence
- Story: SCRUM-492
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.6
Task: Create --mode full pipeline sequence

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 31 — Agent C delivery for SCRUM-498: [W19][1.5.5] Create self-correction retry
- Story: SCRUM-498
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.5
Task: Create self-correction retry

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 32 — Agent C delivery for SCRUM-504: [W19][1.6.4] Create hash utilities
- Story: SCRUM-504
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.4
Task: Create hash utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 33 — Agent C delivery for SCRUM-229: [DASHBOARD] S9.15 Mobile Optimization
- Story: SCRUM-229
- AC Focus: Story Implement S9.15 — Mobile Optimization. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.15.1–9.15.3 covering responsive/mobile layout, key page usability on small screens, and tests/review. Acceptance Criteria Dashboard pages remain usable on narrower/mobile layouts where supported. Critical tables/cards/filters degrade gracefully without losing core functionality. Child tasks are created in later native task import waves or formally waived. QA review validates mobile/responsive behavior. DoD Complete when mobile optimization satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-15-mobile-optimization
PR: feat(dashboard): S9.15 Mobile Optimization Suggested Metadata Labels: wave-19, story, dashboard, mobile, responsive, source-todo-pack, source-dod-pack
Priority: Medium
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 34 — Agent C delivery for SCRUM-254: [PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor p
- Story: SCRUM-254
- AC Focus: Purpose PM audit confirms Jira is being updated, but not yet used as the primary source-of-truth planning and completion system across the full 250+ item board. The operator raised a valid concern that cycles appear to add/update a subset of cycle/governance tickets while not exhaustively planning from the existing Jira backlog, acceptance criteria, and definitions of done. Findings Work has often been PR/change-driven and then mapped to Jira afterward, rather than selected from Jira AC/DoD first. Cycle/governance tasks are created regularly, while full board AC/DoD review is not consistently performed before implementation. Story statuses move to In Progress for partial work, but there is no mandatory AC/DoD progress ledger for every active story. Cursor prompts remain too short/detail-light for the desired autonomous execution standard. Uploaded Cycle 011 archive includes uncommitted local work not reflected in live PR #9, showing handoff and merge-gate risk. Rule Changes Every cycle begins with a full Jira board inventory and issue-type/status summary. Active work must be selected from Jira issues before coding. Every agent task must map to exact Jira issue keys and AC/DoD bullets. Every touched Jira issue must receive an AC/DoD progress update. Done is only allowed after full source AC/DoD completion, not partial scaffold completion. Cursor agents may perform Jira operations as assigned. Normal agent task load doubles again: minimum 20, target 24-32, maximum 40 substantive tasks per Cursor agent. Agent prompts must meet minimum 6,000 words per agent prompt, target 8,000-12,000 words, with no hard cap if organized and useful. Any shorter prompt requires both TASK-COUNT WAIVER and PROMPT-DETAIL WAIVER with a clear reason. Acceptance Criteria PM Pack contains full-board AC/DoD-first protocol. PM Pack contains doubled task-volume/prompt-depth protocol. Cycle 012 prompts comply with 20+ substantive tasks and long-form detail. PR #9 gate accounts for uncommitted local archive changes before merge. Future cycles reject shallow prompts or Jira-after-the-fact planning. Status Created by PM during Cycle 012 audit and governance correction.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 35 — Agent C delivery for SCRUM-260: [CYCLE 016] Merge PR #12 and advance runtime dashboard/integration val
- Story: SCRUM-260
- AC Focus: Purpose Cycle 016 continues product-forward development after Cycle 015 advanced dashboard query/page contracts and analysis output/stage wiring. The cycle should begin with a short PR #12 merge gate, then move into runtime dashboard acceptance, end-to-end integration validation, data integrity, and first-run readiness work. Live GitHub Context PR #12: feat(cycle-015): integrate product increments with steward evidence Source branch: cycle/015/integration Target branch: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: one Codex thread was fixed, replied to with evidence, and resolved in-cycle Product progress: dashboard query/page contracts, analysis output contracts, integration evidence compatibility, 449 passing tests, 93.46% coverage Cycle 016 Product Focus After PR #12 is merged into develop, create cycle/016/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer runtime adoption SCRUM-214 — Opportunities Page runtime acceptance SCRUM-215 — Keywords Page runtime acceptance SCRUM-219 — Run History Page runtime acceptance SCRUM-228 — Dashboard App Entry Point runtime startup and diagnostics SCRUM-231 — End-to-End Pipeline Integration evidence SCRUM-232 — Data Integrity Validation SCRUM-235 — Unit Test Coverage SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-237 — Logging and Monitoring SCRUM-239 — First Run Validation SCRUM-241 — Security and Data Hygiene SCRUM-157 through SCRUM-164 — Analysis output/stage wiring closure evidence Prompt Quality Rule Cycle 016 must preserve the corrected high-detail Cursor prompt standard. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #12 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 016 branch starts from updated develop after PR #12 merge, or branch creation is blocked with evidence. Product work advances runtime dashboard acceptance and integration validation from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 36 — Agent C delivery for SCRUM-280: [MEDIUM M10] Create .github/dependabot.yml — automated dependency secu
- Story: SCRUM-280
- AC Focus: Medium Gap — M10\n\n .github/dependabot.yml is missing from the repository. Dependabot auto-creates PRs when dependencies have security vulnerabilities or newer versions.\n\nWith openpyxl , weasyprint , playwright , openai , pydantic , and others in pyproject.toml, automated dependency updates are critical for security.\n\n## Acceptance Criteria\n\n- [ ] .github/dependabot.yml created\n- [ ] pip ecosystem configured with weekly update schedule\n- [ ] GitHub Actions ecosystem configured (for CI workflow deps)\n- [ ] Auto-merge for minor/patch enabled where safe\n- [ ] Dependabot alerts enabled on repository settings\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M10\n* Related: SCRUM-75 (Security controls)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 37 — Agent C delivery for SCRUM-286: [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, m
- Story: SCRUM-286
- AC Focus: Medium Gap — M23+M24+M25+M26\n\nFour PM/governance documentation gaps from Pass-3:\n\n M23 : docs/jira/ACTIVE_STORY_DOD_LEDGER.md header says "Cycle 014" but its body contains Cycle 017 rows. The header is stale by 3 cycles.\n\n M24 : The score-table design pivot (KeywordScore table → ScoreComponent + FinalScore key-value design) was made without a Decision Log entry. No rationale is documented in DECISION_LOG.md for this architectural shift.\n\n M25 : AGENT_ROSTER.md assigns Agent C ownership of src/scoring/ , src/pricing/ , src/discovery/ — three directories that don't exist — plus test_scoring.py , test_pricing.py , test_discovery.py — three test files that don't exist. Cycle allocation is miscalibrated.\n\n M26 : JIRA_FIELD_STANDARDS.md specifies a description template (## Overview / ## Spec Reference / ## Acceptance Criteria / ## Technical Notes / ## Agent Assignment) that doesn't match the actual template in use (## Story / ## Parent Epic / ## Source / ## Acceptance Criteria / ## DoD / ## GitHub Alignment / ## Suggested Metadata). The standard is obsolete.\n\n## Acceptance Criteria\n\n- [ ] M23: ACTIVE_STORY_DOD_LEDGER.md header updated to current cycle\n- [ ] M24: New DL entry added to DECISION_LOG.md documenting KeywordScore → ScoreComponent+FinalScore design pivot\n- [ ] M25: AGENT_ROSTER.md updated to reflect Agent C's actual capacity and the unbuilt engine situation\n- [ ] M26: JIRA_FIELD_STANDARDS.md description template section updated to match actual practice\n\n## Source Reference\n\n* Gap audit Pass-3: Medium Gaps M23, M24, M25, M26
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 38 — Agent C delivery for SCRUM-444: [W19][1.1.2] Create pyproject.toml with all dependencies
- Story: SCRUM-444
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.2
Task: Create pyproject.toml with all dependencies

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 39 — Agent C delivery for SCRUM-450: [W19][1.2.1] Create config.yaml master template
- Story: SCRUM-450
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.1
Task: Create config.yaml master template

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 40 — Agent C delivery for SCRUM-456: [W19][1.2.7] Create config validation tests
- Story: SCRUM-456
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.7
Task: Create config validation tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 41 — Agent C delivery for SCRUM-462: [W19][1.3.6] Create Gig model
- Story: SCRUM-462
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.6
Task: Create Gig model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 42 — Agent C delivery for SCRUM-468: [W19][1.3.12] Create Recommendation model
- Story: SCRUM-468
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.12
Task: Create Recommendation model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 43 — Agent C delivery for SCRUM-474: [W19][1.3.18] Create LLMCache model
- Story: SCRUM-474
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.18
Task: Create LLMCache model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 44 — Agent C delivery for SCRUM-480: [W19][1.3.24] Create DiscoveryOutcome model
- Story: SCRUM-480
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.24
Task: Create DiscoveryOutcome model

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 45 — Agent C delivery for SCRUM-486: [W19][1.3.30] Create model unit tests
- Story: SCRUM-486
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-136
Task ID: 1.3.30
Task: Create model unit tests

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 46 — Agent C delivery for SCRUM-492: [W19][1.4.6] Create --mode full pipeline sequence
- Story: SCRUM-492
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-137
Task ID: 1.4.6
Task: Create --mode full pipeline sequence

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 47 — Agent C delivery for SCRUM-498: [W19][1.5.5] Create self-correction retry
- Story: SCRUM-498
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-138
Task ID: 1.5.5
Task: Create self-correction retry

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 48 — Agent C delivery for SCRUM-504: [W19][1.6.4] Create hash utilities
- Story: SCRUM-504
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-139
Task ID: 1.6.4
Task: Create hash utilities

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 49 — Agent C delivery for SCRUM-229: [DASHBOARD] S9.15 Mobile Optimization
- Story: SCRUM-229
- AC Focus: Story Implement S9.15 — Mobile Optimization. Parent Epic SCRUM-24 — Epic 09: Dashboard & Reporting Source ToDo_Fiverr(10)/To-Do/EPIC_09_DASHBOARD.md DOD_Fiverr(7)/DOD/DOD_EPIC_09.md Gate: SCRUM-132 Scope Source tasks 9.15.1–9.15.3 covering responsive/mobile layout, key page usability on small screens, and tests/review. Acceptance Criteria Dashboard pages remain usable on narrower/mobile layouts where supported. Critical tables/cards/filters degrade gracefully without losing core functionality. Child tasks are created in later native task import waves or formally waived. QA review validates mobile/responsive behavior. DoD Complete when mobile optimization satisfies source ToDo and DOD requirements. GitHub Alignment Branch: feat/dashboard/s9-15-mobile-optimization
PR: feat(dashboard): S9.15 Mobile Optimization Suggested Metadata Labels: wave-19, story, dashboard, mobile, responsive, source-todo-pack, source-dod-pack
Priority: Medium
- DoD Focus: See DoD reference: PM_Pack/ref/dod/DOD_EPIC_09.md
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 50 — Agent C delivery for SCRUM-254: [PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor p
- Story: SCRUM-254
- AC Focus: Purpose PM audit confirms Jira is being updated, but not yet used as the primary source-of-truth planning and completion system across the full 250+ item board. The operator raised a valid concern that cycles appear to add/update a subset of cycle/governance tickets while not exhaustively planning from the existing Jira backlog, acceptance criteria, and definitions of done. Findings Work has often been PR/change-driven and then mapped to Jira afterward, rather than selected from Jira AC/DoD first. Cycle/governance tasks are created regularly, while full board AC/DoD review is not consistently performed before implementation. Story statuses move to In Progress for partial work, but there is no mandatory AC/DoD progress ledger for every active story. Cursor prompts remain too short/detail-light for the desired autonomous execution standard. Uploaded Cycle 011 archive includes uncommitted local work not reflected in live PR #9, showing handoff and merge-gate risk. Rule Changes Every cycle begins with a full Jira board inventory and issue-type/status summary. Active work must be selected from Jira issues before coding. Every agent task must map to exact Jira issue keys and AC/DoD bullets. Every touched Jira issue must receive an AC/DoD progress update. Done is only allowed after full source AC/DoD completion, not partial scaffold completion. Cursor agents may perform Jira operations as assigned. Normal agent task load doubles again: minimum 20, target 24-32, maximum 40 substantive tasks per Cursor agent. Agent prompts must meet minimum 6,000 words per agent prompt, target 8,000-12,000 words, with no hard cap if organized and useful. Any shorter prompt requires both TASK-COUNT WAIVER and PROMPT-DETAIL WAIVER with a clear reason. Acceptance Criteria PM Pack contains full-board AC/DoD-first protocol. PM Pack contains doubled task-volume/prompt-depth protocol. Cycle 012 prompts comply with 20+ substantive tasks and long-form detail. PR #9 gate accounts for uncommitted local archive changes before merge. Future cycles reject shallow prompts or Jira-after-the-fact planning. Status Created by PM during Cycle 012 audit and governance correction.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 51 — Agent C delivery for SCRUM-260: [CYCLE 016] Merge PR #12 and advance runtime dashboard/integration val
- Story: SCRUM-260
- AC Focus: Purpose Cycle 016 continues product-forward development after Cycle 015 advanced dashboard query/page contracts and analysis output/stage wiring. The cycle should begin with a short PR #12 merge gate, then move into runtime dashboard acceptance, end-to-end integration validation, data integrity, and first-run readiness work. Live GitHub Context PR #12: feat(cycle-015): integrate product increments with steward evidence Source branch: cycle/015/integration Target branch: develop Status at PM review time: open, mergeable, not draft CI: successful codecov/project : successful Codex/PR review threads: one Codex thread was fixed, replied to with evidence, and resolved in-cycle Product progress: dashboard query/page contracts, analysis output contracts, integration evidence compatibility, 449 passing tests, 93.46% coverage Cycle 016 Product Focus After PR #12 is merged into develop, create cycle/016/integration from updated develop and advance product work from Jira AC/DoD stories instead of process-only corrections. Priority scope: SCRUM-225 — Dashboard Query Layer runtime adoption SCRUM-214 — Opportunities Page runtime acceptance SCRUM-215 — Keywords Page runtime acceptance SCRUM-219 — Run History Page runtime acceptance SCRUM-228 — Dashboard App Entry Point runtime startup and diagnostics SCRUM-231 — End-to-End Pipeline Integration evidence SCRUM-232 — Data Integrity Validation SCRUM-235 — Unit Test Coverage SCRUM-236 — Configuration Validation for All 9 Niches SCRUM-237 — Logging and Monitoring SCRUM-239 — First Run Validation SCRUM-241 — Security and Data Hygiene SCRUM-157 through SCRUM-164 — Analysis output/stage wiring closure evidence Prompt Quality Rule Cycle 016 must preserve the corrected high-detail Cursor prompt standard. Each Cursor agent prompt must include: 20+ substantive tasks 6,000+ words unless a formal waiver is documented high-level architecture context exact Jira keys and AC/DoD per task implementation details, file scope, validation requirements, report instructions, and Jira update requirements same-cycle Codex handling instructions final PR stewardship and no-main policy Same-Cycle Codex Rule The PR-owning Cursor agent must review, fix or formally disposition, comment on, and resolve all Codex review comments in the same PR/cycle whenever technically possible. No unresolved Codex comments should be handed to a future cycle unless a hard blocker is documented with evidence. Acceptance Criteria PR #12 is merged only if checks remain green, Codex threads remain resolved, and merge is authorized. Cycle 016 branch starts from updated develop after PR #12 merge, or branch creation is blocked with evidence. Product work advances runtime dashboard acceptance and integration validation from Jira AC/DoD stories. Prompt quality audit is passed before PM artifacts are handed off. Updated PM Pack zip and prompt-only backup are generated and verified. Product stories receive AC/DoD progress comments and are not marked Done unless the full source DoD is satisfied.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 52 — Agent C delivery for SCRUM-280: [MEDIUM M10] Create .github/dependabot.yml — automated dependency secu
- Story: SCRUM-280
- AC Focus: Medium Gap — M10\n\n .github/dependabot.yml is missing from the repository. Dependabot auto-creates PRs when dependencies have security vulnerabilities or newer versions.\n\nWith openpyxl , weasyprint , playwright , openai , pydantic , and others in pyproject.toml, automated dependency updates are critical for security.\n\n## Acceptance Criteria\n\n- [ ] .github/dependabot.yml created\n- [ ] pip ecosystem configured with weekly update schedule\n- [ ] GitHub Actions ecosystem configured (for CI workflow deps)\n- [ ] Auto-merge for minor/patch enabled where safe\n- [ ] Dependabot alerts enabled on repository settings\n\n## Source Reference\n\n* Gap audit Pass-2: Medium Gap M10\n* Related: SCRUM-75 (Security controls)
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 53 — Agent C delivery for SCRUM-286: [MEDIUM M23-M26] Fix 4 PM/governance doc gaps — stale ledger header, m
- Story: SCRUM-286
- AC Focus: Medium Gap — M23+M24+M25+M26\n\nFour PM/governance documentation gaps from Pass-3:\n\n M23 : docs/jira/ACTIVE_STORY_DOD_LEDGER.md header says "Cycle 014" but its body contains Cycle 017 rows. The header is stale by 3 cycles.\n\n M24 : The score-table design pivot (KeywordScore table → ScoreComponent + FinalScore key-value design) was made without a Decision Log entry. No rationale is documented in DECISION_LOG.md for this architectural shift.\n\n M25 : AGENT_ROSTER.md assigns Agent C ownership of src/scoring/ , src/pricing/ , src/discovery/ — three directories that don't exist — plus test_scoring.py , test_pricing.py , test_discovery.py — three test files that don't exist. Cycle allocation is miscalibrated.\n\n M26 : JIRA_FIELD_STANDARDS.md specifies a description template (## Overview / ## Spec Reference / ## Acceptance Criteria / ## Technical Notes / ## Agent Assignment) that doesn't match the actual template in use (## Story / ## Parent Epic / ## Source / ## Acceptance Criteria / ## DoD / ## GitHub Alignment / ## Suggested Metadata). The standard is obsolete.\n\n## Acceptance Criteria\n\n- [ ] M23: ACTIVE_STORY_DOD_LEDGER.md header updated to current cycle\n- [ ] M24: New DL entry added to DECISION_LOG.md documenting KeywordScore → ScoreComponent+FinalScore design pivot\n- [ ] M25: AGENT_ROSTER.md updated to reflect Agent C's actual capacity and the unbuilt engine situation\n- [ ] M26: JIRA_FIELD_STANDARDS.md description template section updated to match actual practice\n\n## Source Reference\n\n* Gap audit Pass-3: Medium Gaps M23, M24, M25, M26
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 54 — Agent C delivery for SCRUM-444: [W19][1.1.2] Create pyproject.toml with all dependencies
- Story: SCRUM-444
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-45
Task ID: 1.1.2
Task: Create pyproject.toml with all dependencies

This sub-task makes the E01 task-level work trackable in Jira.
- DoD Focus: 
- Project Plan Context: PM_Pack/ref/project_plan (no direct SCRUM mapping)
- Validation: run targeted unit tests and record evidence in cycle report.

### TASK 55 — Agent C delivery for SCRUM-450: [W19][1.2.1] Create config.yaml master template
- Story: SCRUM-450
- AC Focus: Wave 19 source task created by Jira API-only audit remediation M-14.

Parent: SCRUM-135
Task ID: 1.2.1
Task: Create config.yaml master template

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
- Write: docs/cycle_reports/CYCLE_078_AGENT_C.md
- Final line must be: AGENT_COMPLETE

Generated at: 2026-06-14T00:40:54.298434+00:00

---

END OF PROMPT
