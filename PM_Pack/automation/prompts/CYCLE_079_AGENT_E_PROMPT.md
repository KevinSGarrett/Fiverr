CYCLE 079 — Agent E: Live Validation / External Signals / Prompt Factory
Generated: 2026-06-15T08:00:00Z
Cycle: 079
Agent: E
Branch: cycle/079/integration
Repo Root: C:/Fiverr/Fiverr

MODEL POLICY — MANDATORY
Worker: Cursor CLI
Model: codex-5.3
Effort: medium
Auto model selection: DISABLED
Fallback: DISABLED

GIT RULES — MANDATORY
Do not run git add, git commit, git push, gh pr merge, or git stash.
Controller owns all git operations.

AUTONOMY RULE
Proceed autonomously through all tasks without confirmation prompts.

ALLOWED PATHS
- automation/ref_catalog_builder.py
- PM_Pack/automation/project_plan_catalog.json
- PM_Pack/automation/dod_catalog.json
- PM_Pack/automation/todo_epic_catalog.json
- PM_Pack/automation/github_governance_catalog.json
- PM_Pack/automation/prompt_contracts/
- PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- docs/architecture/PROMPT_FACTORY_CHAIN.md
- PM_Pack/automation/BRAIN_REGISTRY.yml
- src/collection/live_pilot.py

BLOCKED PATHS
- automation/provider_router.py
- automation/adapters/
- automation/prompt_renderer.py
- automation/pm_pack_consistency_audit.py
- tests/**

JIRA SCOPE
### SCRUM-256: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Six contract JSON files are created in PM_Pack/automation/prompt_contracts/
- All contracts validate against prompt_contract.schema.json
Definition of Done:
- Contract generation for A/B/E/C/F/D completes successfully
- Schema validation command exits zero for all contracts
Relevant files:
- PM_Pack/automation/prompt_contracts/
- automation/schemas/prompt_contract.schema.json

### SCRUM-257: PROMPTFACTORY-012 add prompt lineage metadata
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Each contract includes source lineage entries
- Lineage references Jira keys and PM_Pack catalogs
Definition of Done:
- Lineage is present for all six agents
- Lineage report captures source resolution evidence
Relevant files:
- PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json
- PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md

### SCRUM-258: PROMPTFACTORY-015 create Cycle 079 validation report artifact
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Validation report JSON exists in prompts/validated
- Per-agent PASS/FAIL/WARN and gate checks are recorded
Definition of Done:
- validate-prompts evidence is captured into report
- Report includes generation timestamp and summary status
Relevant files:
- PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json

### SCRUM-259: PROMPTFACTORY-030/031 contract README and prompt factory chain docs
Status: In Progress
Priority: Medium
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- prompt_contracts/README.md explains schema and generation flow
- PROMPT_FACTORY_CHAIN.md documents the artifact lifecycle
Definition of Done:
- Both documentation artifacts exist with correct chain details
- Dispatch source of truth in prompts/validated is documented
Relevant files:
- PM_Pack/automation/prompt_contracts/README.md
- docs/architecture/PROMPT_FACTORY_CHAIN.md

### SCRUM-260: REFCAT freshness rebuild and strict verification
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- All four ref catalogs are rebuilt fresh
- verify --strict exits zero and brain-check has no stale warnings
Definition of Done:
- Catalog counts meet strict minimum thresholds
- BRAIN_REGISTRY freshness constraints are confirmed
Relevant files:
- automation/ref_catalog_builder.py
- PM_Pack/automation/project_plan_catalog.json
- PM_Pack/automation/dod_catalog.json
- PM_Pack/automation/todo_epic_catalog.json
- PM_Pack/automation/github_governance_catalog.json
- PM_Pack/automation/BRAIN_REGISTRY.yml


TASKS
### Task 1: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — spec review
- Jira: SCRUM-256
- Description: Agent E executes spec review for SCRUM-256.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Run targeted checks and record evidence.

### Task 2: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — implementation
- Jira: SCRUM-256
- Description: Agent E executes implementation for SCRUM-256.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Run targeted checks and record evidence.

### Task 3: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — acceptance criteria verification
- Jira: SCRUM-256
- Description: Agent E executes acceptance criteria verification for SCRUM-256.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Run targeted checks and record evidence.

### Task 4: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — unit test writing
- Jira: SCRUM-256
- Description: Agent E executes unit test writing for SCRUM-256.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Run targeted checks and record evidence.

### Task 5: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — definition of done verification
- Jira: SCRUM-256
- Description: Agent E executes definition of done verification for SCRUM-256.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Run targeted checks and record evidence.

### Task 6: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — validation command run
- Jira: SCRUM-256
- Description: Agent E executes validation command run for SCRUM-256.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Run targeted checks and record evidence.

### Task 7: PROMPTFACTORY-012 add prompt lineage metadata — spec review
- Jira: SCRUM-257
- Description: Agent E executes spec review for SCRUM-257.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Run targeted checks and record evidence.

### Task 8: PROMPTFACTORY-012 add prompt lineage metadata — implementation
- Jira: SCRUM-257
- Description: Agent E executes implementation for SCRUM-257.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Run targeted checks and record evidence.

### Task 9: PROMPTFACTORY-012 add prompt lineage metadata — acceptance criteria verification
- Jira: SCRUM-257
- Description: Agent E executes acceptance criteria verification for SCRUM-257.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Run targeted checks and record evidence.

### Task 10: PROMPTFACTORY-012 add prompt lineage metadata — unit test writing
- Jira: SCRUM-257
- Description: Agent E executes unit test writing for SCRUM-257.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Run targeted checks and record evidence.

### Task 11: PROMPTFACTORY-012 add prompt lineage metadata — definition of done verification
- Jira: SCRUM-257
- Description: Agent E executes definition of done verification for SCRUM-257.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Run targeted checks and record evidence.

### Task 12: PROMPTFACTORY-012 add prompt lineage metadata — validation command run
- Jira: SCRUM-257
- Description: Agent E executes validation command run for SCRUM-257.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Run targeted checks and record evidence.

### Task 13: PROMPTFACTORY-015 create Cycle 079 validation report artifact — spec review
- Jira: SCRUM-258
- Description: Agent E executes spec review for SCRUM-258.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Run targeted checks and record evidence.

### Task 14: PROMPTFACTORY-015 create Cycle 079 validation report artifact — implementation
- Jira: SCRUM-258
- Description: Agent E executes implementation for SCRUM-258.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Run targeted checks and record evidence.

### Task 15: PROMPTFACTORY-015 create Cycle 079 validation report artifact — acceptance criteria verification
- Jira: SCRUM-258
- Description: Agent E executes acceptance criteria verification for SCRUM-258.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Run targeted checks and record evidence.

### Task 16: PROMPTFACTORY-015 create Cycle 079 validation report artifact — unit test writing
- Jira: SCRUM-258
- Description: Agent E executes unit test writing for SCRUM-258.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Run targeted checks and record evidence.

### Task 17: PROMPTFACTORY-015 create Cycle 079 validation report artifact — definition of done verification
- Jira: SCRUM-258
- Description: Agent E executes definition of done verification for SCRUM-258.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Run targeted checks and record evidence.

### Task 18: PROMPTFACTORY-015 create Cycle 079 validation report artifact — validation command run
- Jira: SCRUM-258
- Description: Agent E executes validation command run for SCRUM-258.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Run targeted checks and record evidence.

### Task 19: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — spec review
- Jira: SCRUM-259
- Description: Agent E executes spec review for SCRUM-259.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Run targeted checks and record evidence.

### Task 20: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — implementation
- Jira: SCRUM-259
- Description: Agent E executes implementation for SCRUM-259.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Run targeted checks and record evidence.

### Task 21: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — acceptance criteria verification
- Jira: SCRUM-259
- Description: Agent E executes acceptance criteria verification for SCRUM-259.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Run targeted checks and record evidence.

### Task 22: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — unit test writing
- Jira: SCRUM-259
- Description: Agent E executes unit test writing for SCRUM-259.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Run targeted checks and record evidence.

### Task 23: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — definition of done verification
- Jira: SCRUM-259
- Description: Agent E executes definition of done verification for SCRUM-259.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Run targeted checks and record evidence.

### Task 24: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — validation command run
- Jira: SCRUM-259
- Description: Agent E executes validation command run for SCRUM-259.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Run targeted checks and record evidence.

### Task 25: REFCAT freshness rebuild and strict verification — spec review
- Jira: SCRUM-260
- Description: Agent E executes spec review for SCRUM-260.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Run targeted checks and record evidence.

### Task 26: REFCAT freshness rebuild and strict verification — implementation
- Jira: SCRUM-260
- Description: Agent E executes implementation for SCRUM-260.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Run targeted checks and record evidence.

### Task 27: REFCAT freshness rebuild and strict verification — acceptance criteria verification
- Jira: SCRUM-260
- Description: Agent E executes acceptance criteria verification for SCRUM-260.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Run targeted checks and record evidence.

### Task 28: REFCAT freshness rebuild and strict verification — unit test writing
- Jira: SCRUM-260
- Description: Agent E executes unit test writing for SCRUM-260.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Run targeted checks and record evidence.

### Task 29: REFCAT freshness rebuild and strict verification — definition of done verification
- Jira: SCRUM-260
- Description: Agent E executes definition of done verification for SCRUM-260.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Run targeted checks and record evidence.

### Task 30: REFCAT freshness rebuild and strict verification — validation command run
- Jira: SCRUM-260
- Description: Agent E executes validation command run for SCRUM-260.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Run targeted checks and record evidence.

### Task 31: General validation and reporting
- Jira: SCRUM-256
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 32: General validation and reporting
- Jira: SCRUM-257
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 33: General validation and reporting
- Jira: SCRUM-258
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 34: General validation and reporting
- Jira: SCRUM-259
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 35: General validation and reporting
- Jira: SCRUM-260
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 36: General validation and reporting
- Jira: SCRUM-256
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 37: General validation and reporting
- Jira: SCRUM-257
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 38: General validation and reporting
- Jira: SCRUM-258
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 39: General validation and reporting
- Jira: SCRUM-259
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 40: General validation and reporting
- Jira: SCRUM-260
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 41: General validation and reporting
- Jira: SCRUM-256
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 42: General validation and reporting
- Jira: SCRUM-257
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 43: General validation and reporting
- Jira: SCRUM-258
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 44: General validation and reporting
- Jira: SCRUM-259
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 45: General validation and reporting
- Jira: SCRUM-260
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 46: General validation and reporting
- Jira: SCRUM-256
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 47: General validation and reporting
- Jira: SCRUM-257
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 48: General validation and reporting
- Jira: SCRUM-258
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 49: General validation and reporting
- Jira: SCRUM-259
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 50: General validation and reporting
- Jira: SCRUM-260
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 51: General validation and reporting
- Jira: SCRUM-256
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 52: General validation and reporting
- Jira: SCRUM-257
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 53: General validation and reporting
- Jira: SCRUM-258
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 54: General validation and reporting
- Jira: SCRUM-259
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 55: General validation and reporting
- Jira: SCRUM-260
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

REQUIRED VALIDATION STEPS
- python automation/ref_catalog_builder.py verify --strict
- python automation/ai_cycle_controller.py validate-prompts --cycle 079
- ruff check automation/ref_catalog_builder.py automation/jira_spec_mapper.py --output-format=concise
- mypy automation/ref_catalog_builder.py automation/jira_spec_mapper.py --ignore-missing-imports --no-error-summary
- mypy src/ automation/ --ignore-missing-imports
- pytest tests/unit/ --timeout=8 --tb=short -q

FINAL REPORT REQUIREMENT
Write final report to: docs/cycle_reports/CYCLE_079_AGENT_E.md

STOP CONDITIONS
- About to modify blocked-path files
- Import errors in new modules that propagate to existing tests
- About to run git commit or git push

END OF PROMPT
