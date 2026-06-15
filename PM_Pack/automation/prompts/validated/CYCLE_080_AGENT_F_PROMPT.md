# CYCLE 080 — Agent F: Test coverage gaps, regression tests, coverage enforcement
Generated: 2026-06-15T15:40:19.510036+00:00
Cycle: 080
Agent: F
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
- tests/**

## BLOCKED PATHS
- (No blocked paths specified in contract)

## JIRA SCOPE
### SCRUM-266: Provider router test coverage expansion
Status: To Do
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Router edge paths are covered by unit tests
- Failure handling and fallback behavior is asserted
Definition of Done:
- test_provider_router passes
- Coverage increase is documented in cycle report
Files or modules:
- tests/unit/test_provider_router.py
- tests/unit/test_provider_health.py

### SCRUM-267: Cost guard and provider health regression tests
Status: To Do
Priority: Medium
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Cost guard budget states are tested for pass/warn/block
- Provider health blocked and degraded states are covered
Definition of Done:
- test_cost_guard and test_provider_health pass
- Regression suite remains green
Files or modules:
- tests/unit/test_cost_guard.py
- tests/unit/test_provider_health.py
- tests/unit/test_provider_usage_ledger.py


## TASKS
### Task 1: Provider router test coverage expansion — Review specification and acceptance requirements
- Jira key: SCRUM-266
- Description: Agent F executes 'Review specification and acceptance requirements' for SCRUM-266, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Record command outputs and state transition evidence.

### Task 2: Provider router test coverage expansion — Implement routing and control logic
- Jira key: SCRUM-266
- Description: Agent F executes 'Implement routing and control logic' for SCRUM-266, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Record command outputs and state transition evidence.

### Task 3: Provider router test coverage expansion — Verify acceptance criteria coverage
- Jira key: SCRUM-266
- Description: Agent F executes 'Verify acceptance criteria coverage' for SCRUM-266, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Record command outputs and state transition evidence.

### Task 4: Provider router test coverage expansion — Write and run focused unit validation checks
- Jira key: SCRUM-266
- Description: Agent F executes 'Write and run focused unit validation checks' for SCRUM-266, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Record command outputs and state transition evidence.

### Task 5: Provider router test coverage expansion — Verify definition-of-done artifacts
- Jira key: SCRUM-266
- Description: Agent F executes 'Verify definition-of-done artifacts' for SCRUM-266, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Record command outputs and state transition evidence.

### Task 6: Provider router test coverage expansion — Run full validation command set
- Jira key: SCRUM-266
- Description: Agent F executes 'Run full validation command set' for SCRUM-266, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Record command outputs and state transition evidence.

### Task 7: Cost guard and provider health regression tests — Review specification and acceptance requirements
- Jira key: SCRUM-267
- Description: Agent F executes 'Review specification and acceptance requirements' for SCRUM-267, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Record command outputs and state transition evidence.

### Task 8: Cost guard and provider health regression tests — Implement routing and control logic
- Jira key: SCRUM-267
- Description: Agent F executes 'Implement routing and control logic' for SCRUM-267, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Record command outputs and state transition evidence.

### Task 9: Cost guard and provider health regression tests — Verify acceptance criteria coverage
- Jira key: SCRUM-267
- Description: Agent F executes 'Verify acceptance criteria coverage' for SCRUM-267, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Record command outputs and state transition evidence.

### Task 10: Cost guard and provider health regression tests — Write and run focused unit validation checks
- Jira key: SCRUM-267
- Description: Agent F executes 'Write and run focused unit validation checks' for SCRUM-267, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Record command outputs and state transition evidence.

### Task 11: Cost guard and provider health regression tests — Verify definition-of-done artifacts
- Jira key: SCRUM-267
- Description: Agent F executes 'Verify definition-of-done artifacts' for SCRUM-267, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Record command outputs and state transition evidence.

### Task 12: Cost guard and provider health regression tests — Run full validation command set
- Jira key: SCRUM-267
- Description: Agent F executes 'Run full validation command set' for SCRUM-267, records evidence, and updates implementation notes for downstream agents.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Record command outputs and state transition evidence.

### Task 13: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 14: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 15: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 16: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 17: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 18: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 19: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 20: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 21: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 22: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 23: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 24: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 25: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 26: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 27: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 28: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 29: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 30: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 31: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 32: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 33: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 34: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 35: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 36: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 37: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 38: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 39: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 40: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 41: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 42: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 43: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 44: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 45: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 46: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 47: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 48: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 49: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 50: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 51: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 52: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 53: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 54: General quality gate execution
- Jira key: SCRUM-267
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 55: General quality gate execution
- Jira key: SCRUM-266
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

## REQUIRED VALIDATION STEPS
- python automation/ai_cycle_controller.py brain-check
- python automation/ai_cycle_controller.py validate-prompts --cycle 080
- mypy src/ automation/ --ignore-missing-imports

## FINAL REPORT REQUIREMENT
Write final report to docs/cycle_reports/CYCLE_080_AGENT_F.md.

## STOP CONDITIONS
- Stop if a blocked path must be modified.
- Stop if a required external prerequisite is missing.
- Stop before executing any forbidden git write operation.

END OF PROMPT
