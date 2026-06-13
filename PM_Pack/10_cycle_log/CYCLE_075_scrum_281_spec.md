# CYCLE 075 EXECUTABLE SPEC - SCRUM-281

## Objective
SCRUM-281 formalizes pyproject governance annotation for Cycle 077. The objective is to add a minimal, non-functional note in `pyproject.toml` indicating governance pass completion context, without changing dependencies, build behavior, lint rules, or test settings. This creates a durable metadata breadcrumb for auditability.

## Component Boundaries
- In scope: comment-level or innocuous metadata note in `pyproject.toml`.
- In scope: preserving all existing dependency/version constraints.
- Out of scope: dependency churn, tool config changes, build backend changes.
- Out of scope: modifying lint/type/test strictness.

## Data Flow
1. Read current `pyproject.toml` sections and dependency lists.
2. Insert governance note near top-level metadata for discoverability.
3. Confirm no non-comment semantic changes occurred.
4. Link pyproject note to cycle governance artifacts in docs.

## Error Handling
- TOML parser sensitivity concern: use comment lines only.
- Accidental dependency edit: fail governance gate and revert patch.
- Duplicate cycle note: append timestamped extension or replace stale note.
- Invalid comment placement near arrays: move note to safer section header.

## API Contract (Governance Interfaces)
```python
def add_governance_comment_to_pyproject(toml_text: str, cycle_id: str) -> str: ...
def assert_no_dependency_churn(before: str, after: str) -> list[str]: ...
def locate_safe_comment_insertion_point(toml_text: str) -> int: ...
def validate_pyproject_semantic_equivalence(before: str, after: str) -> list[str]: ...
```

## Validation Strategy
- Dependency diff check: list of dependencies unchanged.
- Tooling config check: ruff/mypy/pytest sections unchanged.
- Build-system check: no backend or requires modifications.
- Visibility check: governance note is easy to locate.

## Required Tests
1. `test_scrum_281_adds_comment_without_semantic_changes`
2. `test_scrum_281_dependency_list_unchanged`
3. `test_scrum_281_tool_sections_unchanged`
4. `test_scrum_281_governance_note_contains_cycle_reference`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Governance note added | Comment present | `pyproject.toml` diff |
| AC-2: Dependency neutrality maintained | No changed dependency rows | Diff audit |
| AC-3: Tool config preserved | Section hashes equivalent | Config compare report |
| AC-4: Audit trail improved | Note references cycle 077 | Comment text |

## Architecture Decision and Tradeoff Notes
Decision: use comments only for governance annotation. Tradeoff: comments are not machine-enforced metadata, but they are guaranteed non-breaking in TOML. Decision: place note close to build or project header for visibility. Tradeoff: slight header clutter versus faster reviewer discovery. Decision: avoid introducing a custom tool section for governance metadata in this cycle. Tradeoff: less structure, lower risk of downstream tooling assumptions breaking.
