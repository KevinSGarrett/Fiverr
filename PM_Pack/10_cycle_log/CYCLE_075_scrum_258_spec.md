# CYCLE 075 EXECUTABLE SPEC - SCRUM-258

## Objective
SCRUM-258 governs CI naming and gate integrity for Cycle 077. The objective is to ensure the workflow continues exposing the exact required check names (`CI / lint`, `CI / type-check`, `CI / tests-coverage`, `CI / smoke-gates`) and retains critical gate commands (ruff, mypy, pytest with coverage, config-check, foundation-gate, phase2-smoke). This prevents silent branch-protection breakage and governance drift.

## Component Boundaries
- In scope: `.github/workflows/ci.yml` job names and gate command presence.
- In scope: non-breaking workflow hygiene additions if needed.
- Out of scope: changing gate semantics, thresholds, or command behavior.
- Out of scope: repository settings and required-check policy in GitHub UI.

## Data Flow
1. Read current workflow jobs and names.
2. Validate required job IDs and display names remain exact.
3. Validate command presence in lint/type-check/tests/smoke jobs.
4. Apply minimal patch if naming or command drift exists.
5. Record conformance in cycle governance notes.

## Error Handling
- Missing workflow file: recreate from baseline governance template.
- Job exists with renamed display name: restore exact required name.
- Required command removed: reinsert command in corresponding job step.
- YAML format issue after edit: fail governance check and rollback patch plan.

## API Contract (Governance Interfaces)
```python
def parse_ci_jobs(ci_yaml: str) -> dict: ...
def validate_required_job_names(ci_jobs: dict, expected: dict[str, str]) -> list[str]: ...
def validate_required_gate_commands(ci_yaml: str, commands: list[str]) -> list[str]: ...
def enforce_ci_governance_baseline(ci_yaml: str) -> str: ...
```

## Validation Strategy
- Name equality check: exact string match on four required check names.
- Command presence check: all seven required command markers present.
- Structural check: workflow still triggers on PR/push/workflow_dispatch.
- Safety check: no additional destructive commands introduced.

## Required Tests
1. `test_scrum_258_ci_check_names_are_exact`
2. `test_scrum_258_required_gate_commands_present`
3. `test_scrum_258_workflow_triggers_unchanged`
4. `test_scrum_258_no_gate_regression_after_patch`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Required check names preserved | Name assertions pass | ci.yml inspection |
| AC-2: Required commands preserved | Command assertions pass | Step content review |
| AC-3: Workflow remains runnable | YAML remains valid | CI parse check |
| AC-4: Governance documented | Cycle spec references CI baseline | Spec artifact |

## Architecture Decision and Tradeoff Notes
Decision: enforce exact check names rather than mapping aliases. Tradeoff: stricter governance, reduced flexibility in naming conventions. Decision: validate command presence textually at governance layer. Tradeoff: weaker than execution-time validation, but fast and repository-local. Decision: apply minimal diffs only. Tradeoff: lower cleanup opportunities, but strongly reduces accidental CI behavior changes during doc-focused cycles.
