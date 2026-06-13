# Cycle 076 PR Prerequisites

Before Agent D can create and submit the PR for cycle/075/integration -> develop,
ALL of the following must be true:

## Code Quality Gates
- [ ] ruff check automation/ -> All checks passed!
- [ ] mypy automation/ --ignore-missing-imports -> no issues found
- [ ] pytest tests/unit/ --cov=automation --cov=src --cov-report=term -> >=90%
- [ ] merge_gate.py coverage >=90%
- [ ] secret_guard.py coverage >=90%
- [ ] repair_loop.py coverage >=90%

## Git State
- [ ] git status shows: nothing to commit, working tree clean
- [ ] git push origin cycle/075/integration: remote is up to date

## Brain
- [ ] brain-check: PASS
- [ ] pm-pack-audit: PASS

## PR Body
- [ ] PR body document at docs/cycle_reports/CYCLE_076_PR_BODY.md
- [ ] PR body includes Jira story keys, AC/DoD evidence, validation results, billing mode note

## Evidence
- [ ] docs/cycle_reports/CYCLE_076_AGENT_A.md contains AGENT_COMPLETE
- [ ] docs/cycle_reports/CYCLE_076_AGENT_B.md contains AGENT_COMPLETE
- [ ] docs/cycle_reports/CYCLE_076_AGENT_C.md contains AGENT_COMPLETE
- [ ] docs/cycle_reports/CYCLE_076_AGENT_E.md contains AGENT_COMPLETE
- [ ] docs/cycle_reports/CYCLE_076_AGENT_F.md contains AGENT_COMPLETE
