# CYCLE 075 EXECUTABLE SPEC - SCRUM-284

## Objective
SCRUM-284 formalizes agent assignment governance for Cycle 077. The objective is to define role-bound responsibilities, artifact ownership, and status-report cadence across Agent A/B/C/D/E/F so cycle throughput remains predictable and reviewer-ready. The output is a documented assignment model in cycle log format with explicit Jira linkage.

## Component Boundaries
- In scope: assignment matrix in `CYCLE_075.md`.
- In scope: per-agent expected outputs and handoff dependencies.
- Out of scope: changing team/org structure outside cycle scope.
- Out of scope: coding task implementation details.

## Data Flow
1. Identify Cycle 077 scope keys and group by workstream.
2. Assign primary owner agent and support agent per workstream.
3. Define expected outputs, dependencies, and reporting checkpoints.
4. Publish assignment table in cycle log.
5. Update tracker/hydration references for alignment.

## Error Handling
- Unassigned key detected: flag as governance blocker until owner assigned.
- Multiple primary owners: reduce to one and keep others as support.
- Missing handoff dependency: add dependency notes and status risk.
- Assignment conflict with prior cycle commitments: add exception rationale.

## API Contract (Governance Interfaces)
```python
def build_assignment_matrix(jira_keys: list[str], agents: list[str]) -> list[dict]: ...
def validate_single_primary_owner(assignments: list[dict]) -> list[str]: ...
def attach_handoff_dependencies(assignments: list[dict]) -> list[dict]: ...
def render_assignment_table(assignments: list[dict]) -> str: ...
```

## Validation Strategy
- Coverage check: every key has an assignment.
- Ownership check: exactly one primary owner per key.
- Dependency check: downstream dependencies declared where needed.
- Reporting check: cadence and status fields present for each row.

## Required Tests
1. `test_scrum_284_every_key_has_assignment`
2. `test_scrum_284_one_primary_owner_per_key`
3. `test_scrum_284_dependency_fields_present_for_cross_agent_work`
4. `test_scrum_284_assignment_table_render_stable`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Assignment model documented | Matrix added to cycle log | `CYCLE_075.md` section |
| AC-2: Ownership ambiguity removed | Single owner rule enforced | Assignment review |
| AC-3: Handoffs explicit | Dependency notes present | Matrix columns |
| AC-4: Execution tracking supported | Status cadence documented | Planning log |

## Architecture Decision and Tradeoff Notes
Decision: centralize assignments in cycle log rather than separate agent files. Tradeoff: one large table, easier single-point review. Decision: enforce primary/support ownership model. Tradeoff: less flexibility for co-ownership, stronger accountability. Decision: include dependency and cadence columns from start. Tradeoff: slight authoring overhead, better operational predictability and less mid-cycle coordination churn.
