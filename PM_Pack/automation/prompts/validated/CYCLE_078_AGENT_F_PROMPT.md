CYCLE 078 — Agent F: Test Coverage and Regression
Generated: 2026-06-15T08:00:00Z
Cycle: 078
Agent: F
Branch: cycle/078/integration
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
- tests/**

BLOCKED PATHS
- PM_Pack/**
- docs/**

JIRA SCOPE
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
Relevant files:
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
Relevant files:
- tests/unit/test_cost_guard.py
- tests/unit/test_provider_health.py
- tests/unit/test_provider_usage_ledger.py


TASKS
### Task 1: Provider router test coverage expansion — spec review
- Jira: SCRUM-266
- Description: Agent F executes spec review for SCRUM-266.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Run targeted checks and record evidence.

### Task 2: Provider router test coverage expansion — implementation
- Jira: SCRUM-266
- Description: Agent F executes implementation for SCRUM-266.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Run targeted checks and record evidence.

### Task 3: Provider router test coverage expansion — acceptance criteria verification
- Jira: SCRUM-266
- Description: Agent F executes acceptance criteria verification for SCRUM-266.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Run targeted checks and record evidence.

### Task 4: Provider router test coverage expansion — unit test writing
- Jira: SCRUM-266
- Description: Agent F executes unit test writing for SCRUM-266.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Run targeted checks and record evidence.

### Task 5: Provider router test coverage expansion — definition of done verification
- Jira: SCRUM-266
- Description: Agent F executes definition of done verification for SCRUM-266.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Run targeted checks and record evidence.

### Task 6: Provider router test coverage expansion — validation command run
- Jira: SCRUM-266
- Description: Agent F executes validation command run for SCRUM-266.
- Files: tests/unit/test_provider_router.py, tests/unit/test_provider_health.py
- Validation: Run targeted checks and record evidence.

### Task 7: Cost guard and provider health regression tests — spec review
- Jira: SCRUM-267
- Description: Agent F executes spec review for SCRUM-267.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Run targeted checks and record evidence.

### Task 8: Cost guard and provider health regression tests — implementation
- Jira: SCRUM-267
- Description: Agent F executes implementation for SCRUM-267.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Run targeted checks and record evidence.

### Task 9: Cost guard and provider health regression tests — acceptance criteria verification
- Jira: SCRUM-267
- Description: Agent F executes acceptance criteria verification for SCRUM-267.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Run targeted checks and record evidence.

### Task 10: Cost guard and provider health regression tests — unit test writing
- Jira: SCRUM-267
- Description: Agent F executes unit test writing for SCRUM-267.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Run targeted checks and record evidence.

### Task 11: Cost guard and provider health regression tests — definition of done verification
- Jira: SCRUM-267
- Description: Agent F executes definition of done verification for SCRUM-267.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Run targeted checks and record evidence.

### Task 12: Cost guard and provider health regression tests — validation command run
- Jira: SCRUM-267
- Description: Agent F executes validation command run for SCRUM-267.
- Files: tests/unit/test_cost_guard.py, tests/unit/test_provider_health.py, tests/unit/test_provider_usage_ledger.py
- Validation: Run targeted checks and record evidence.

### Task 13: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 14: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 15: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 16: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 17: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 18: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 19: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 20: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 21: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 22: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 23: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 24: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 25: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 26: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 27: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 28: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 29: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 30: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 31: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 32: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 33: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 34: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 35: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 36: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 37: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 38: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 39: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 40: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 41: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 42: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 43: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 44: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 45: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 46: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 47: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 48: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 49: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 50: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 51: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 52: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 53: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 54: General validation and reporting
- Jira: SCRUM-267
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

### Task 55: General validation and reporting
- Jira: SCRUM-266
- Description: Run ruff, mypy, pytest, and update cycle report evidence.
- Files: (none)
- Validation: ruff + mypy + pytest + report update

REQUIRED VALIDATION STEPS
- pytest tests/unit/test_provider_router.py --timeout=8 --tb=short -q
- pytest tests/unit/test_cost_guard.py --timeout=8 --tb=short -q
- pytest tests/unit/test_provider_health.py --timeout=8 --tb=short -q
- mypy src/ automation/ --ignore-missing-imports
- ruff check automation/ src/ tests/

FINAL REPORT REQUIREMENT
Write final report to: docs/cycle_reports/CYCLE_078_AGENT_F.md

STOP CONDITIONS
- About to modify blocked-path files
- Import errors in new modules that propagate to existing tests
- About to run git commit or git push

END OF PROMPT
