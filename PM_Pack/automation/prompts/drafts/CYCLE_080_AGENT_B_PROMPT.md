# CYCLE 080 — Agent B: Primary src/ and tests/ author — new features, core logic
Generated: 2026-06-15T15:40:19.505770+00:00
Cycle: 080
Agent: B
Branch: cycle/080/integration
Repo Root: C:/Fiverr/Fiverr

## MODEL POLICY — MANDATORY
Worker: Cursor CLI
Model: codex-5.3
Effort: medium
Auto: DISABLED
Fallback: DISABLED

## GIT RULES — MANDATORY
You MUST NOT run staging, committing, pushing, gh pr merge, or any force push command.
Controller owns all git operations.

## AUTONOMY RULE
Complete all assigned tasks autonomously without confirmation prompts unless a hard blocker appears.

## ALLOWED PATHS
- src/**
- tests/**

## BLOCKED PATHS
- (No blocked paths specified in contract)

## JIRA SCOPE
### SCRUM-264: Prompt rendering and contract generation hardening for Cycle 079
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Prompt rendering path supports Cycle 079 contract payloads
- Validation and promotion flow works for all six agents
Definition of Done:
- Rendered prompts pass validate-prompts checks
- No schema regressions in prompt contract payloads
Files or modules:
- automation/prompt_renderer.py
- automation/prompt_contract_builder.py
- automation/schemas/prompt_contract.schema.json


## TASKS
### Task 1: Prompt rendering and contract generation hardening for Cycle 079 — Review specification and acceptance requirements
- Jira key: SCRUM-264
- Description: Agent B executes 'Review specification and acceptance requirements' for SCRUM-264, records evidence, and updates implementation notes for downstream agents.
- Files: automation/prompt_renderer.py, automation/prompt_contract_builder.py, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 2: Prompt rendering and contract generation hardening for Cycle 079 — Implement routing and control logic
- Jira key: SCRUM-264
- Description: Agent B executes 'Implement routing and control logic' for SCRUM-264, records evidence, and updates implementation notes for downstream agents.
- Files: automation/prompt_renderer.py, automation/prompt_contract_builder.py, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 3: Prompt rendering and contract generation hardening for Cycle 079 — Verify acceptance criteria coverage
- Jira key: SCRUM-264
- Description: Agent B executes 'Verify acceptance criteria coverage' for SCRUM-264, records evidence, and updates implementation notes for downstream agents.
- Files: automation/prompt_renderer.py, automation/prompt_contract_builder.py, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 4: Prompt rendering and contract generation hardening for Cycle 079 — Write and run focused unit validation checks
- Jira key: SCRUM-264
- Description: Agent B executes 'Write and run focused unit validation checks' for SCRUM-264, records evidence, and updates implementation notes for downstream agents.
- Files: automation/prompt_renderer.py, automation/prompt_contract_builder.py, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 5: Prompt rendering and contract generation hardening for Cycle 079 — Verify definition-of-done artifacts
- Jira key: SCRUM-264
- Description: Agent B executes 'Verify definition-of-done artifacts' for SCRUM-264, records evidence, and updates implementation notes for downstream agents.
- Files: automation/prompt_renderer.py, automation/prompt_contract_builder.py, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 6: Prompt rendering and contract generation hardening for Cycle 079 — Run full validation command set
- Jira key: SCRUM-264
- Description: Agent B executes 'Run full validation command set' for SCRUM-264, records evidence, and updates implementation notes for downstream agents.
- Files: automation/prompt_renderer.py, automation/prompt_contract_builder.py, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 7: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 8: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 9: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 10: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 11: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 12: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 13: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 14: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 15: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 16: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 17: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 18: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 19: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 20: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 21: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 22: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 23: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 24: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 25: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 26: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 27: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 28: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 29: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 30: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 31: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 32: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 33: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 34: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 35: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 36: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 37: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 38: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 39: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 40: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 41: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 42: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 43: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 44: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 45: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 46: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 47: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 48: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 49: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 50: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 51: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 52: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 53: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 54: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 55: General quality gate execution
- Jira key: SCRUM-264
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

## REQUIRED VALIDATION STEPS
- python automation/ai_cycle_controller.py brain-check
- python automation/ai_cycle_controller.py validate-prompts --cycle 080
- mypy src/ automation/ --ignore-missing-imports

## FINAL REPORT REQUIREMENT
Write final report to docs/cycle_reports/CYCLE_080_AGENT_B.md.

## STOP CONDITIONS
- Stop if a blocked path must be modified.
- Stop if a required external prerequisite is missing.
- Stop before executing any forbidden git write operation.

END OF PROMPT
