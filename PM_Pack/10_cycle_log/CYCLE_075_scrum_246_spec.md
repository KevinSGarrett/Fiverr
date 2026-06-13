# CYCLE 075 EXECUTABLE SPEC - SCRUM-246

## Objective
SCRUM-246 defines the cycle-level governance bootstrap for Cycle 077 planning and execution traceability. The objective is to establish a deterministic planning contract that links Jira state, PM pack artifacts, and CI gate evidence before implementation agents begin code work. This spec is executable in the sense that every section maps to an automatable check or a concrete artifact path. The scope is documentation and governance only, with no production runtime behavior change.

## Component Boundaries
- In scope: `PM_Pack/10_cycle_log/*`, `PM_Pack/07_hydration/*`, `PM_Pack/08_task_queue/*`, `.github/*`, `config.yaml` governance metadata, and `pyproject.toml` governance note.
- Out of scope: `src/**`, `tests/**`, `data/**`, runtime pipeline logic, SQL schema, and CLI behavior.
- Dependency boundary: Jira keys are source-of-truth for status labels; repository docs are source-of-truth for execution evidence links.

## Data Flow
1. Planner reads Cycle 077 in-scope Jira keys and current governance docs.
2. Planner writes per-ticket executable specs under `PM_Pack/10_cycle_log/`.
3. Planner updates hydration and epic trackers with a synchronized status snapshot.
4. CI governance files are validated for required gate names and command presence.
5. Reviewer confirms each Jira key has AC, DoD mapping, and at least three required tests listed.
6. Output is consumed by Agent B/C/E/F implementation planning without ambiguity.

## Error Handling
- Missing source document: create file with "created in cycle 077 governance bootstrap" marker.
- Conflicting Jira status across docs: prefer latest cycle log status, then add a discrepancy note.
- Invalid file path or naming drift: fail planning step and emit corrective action item.
- CI job name mismatch: block merge readiness and document exact mismatch.

## API Contract (Governance Interfaces)
```python
def build_cycle_governance_snapshot(cycle_id: str, jira_keys: list[str]) -> dict: ...
def write_scrum_spec(scrum_key: str, spec_markdown: str) -> str: ...
def validate_ac_dod_completeness(spec_path: str) -> list[str]: ...
def sync_tracker_status(tracker_path: str, snapshot: dict) -> None: ...
```

## Validation Strategy
- Static validation: required headings must exist in each spec.
- Semantic validation: AC items must map to measurable evidence fields.
- Consistency validation: Jira key set in hydration, cycle log, and epic tracker must match exactly.
- CI governance validation: required check names remain unchanged.

## Required Tests
1. `test_scrum_246_requires_all_spec_sections`
2. `test_scrum_246_rejects_missing_ac_dod_mapping`
3. `test_scrum_246_detects_ci_job_name_drift`
4. `test_scrum_246_tracker_key_set_exact_match`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Cycle 077 scope formalized | 20 spec files exist | File list under `PM_Pack/10_cycle_log` |
| AC-2: Governance docs synchronized | Hydration + tracker updated | Matching Jira key table |
| AC-3: CI governance preserved | Check names unchanged | `.github/workflows/ci.yml` diff |
| AC-4: Non-breaking config metadata | Scrapfly toggle unchanged | `config.yaml` review note |

## Architecture Decision and Tradeoff Notes
Decision: keep governance data in markdown-first artifacts rather than introducing a new structured schema file. Tradeoff: markdown is more reviewer-friendly but less strict than JSON. Mitigation: define pseudo-API contracts and explicit validation rules in each spec. Decision: preserve CI check names exactly to avoid branch protection drift. Tradeoff: reduced flexibility in naming, but strong operational stability. Decision: add governance metadata in safe, optional config keys/comments only. Tradeoff: richer metadata without runtime parser risk, while avoiding behavior changes.
