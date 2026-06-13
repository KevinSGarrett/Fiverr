# CYCLE 075 EXECUTABLE SPEC - SCRUM-440

## Objective
SCRUM-440 specifies governance compatibility between cycle docs and CI branch protection expectations. The objective is to ensure naming and gate references in planning artifacts align with the checks exposed by CI workflow so reviewers can map policy requirements to concrete checks without inference. This strengthens release governance while preserving current pipeline behavior.

## Component Boundaries
- In scope: references to CI gate names in cycle docs and governance notes.
- In scope: mapping table between branch protection expectation and workflow checks.
- Out of scope: branch protection configuration changes in remote repository.
- Out of scope: adding or removing CI jobs.

## Data Flow
1. Read CI workflow check names and required commands.
2. Build governance mapping table for cycle artifacts.
3. Verify referenced names exactly match workflow names.
4. Publish mapping in cycle log/governance section.
5. Use mapping during PR review to confirm gate pass intent.

## Error Handling
- Check name mismatch in docs: update doc references to exact workflow names.
- Missing check in CI file: flag as blocker for governance compliance.
- Multiple aliases for same check: collapse to canonical form only.
- Incomplete mapping table: mark as non-compliant until completed.

## API Contract (Governance Interfaces)
```python
def extract_ci_check_names(ci_yaml: str) -> list[str]: ...
def build_protection_mapping(checks: list[str]) -> list[dict]: ...
def validate_doc_check_name_references(doc_text: str, checks: list[str]) -> list[str]: ...
def render_ci_governance_mapping(mapping: list[dict]) -> str: ...
```

## Validation Strategy
- Exact match check for required check names.
- Presence check for required gate command references.
- Mapping completeness check for all required checks.
- Drift check ensuring no deprecated alias remains.

## Required Tests
1. `test_scrum_440_mapping_includes_all_required_ci_checks`
2. `test_scrum_440_doc_references_use_exact_check_names`
3. `test_scrum_440_detects_missing_ci_job_before_merge`
4. `test_scrum_440_aliases_are_rejected_in_governance_mapping`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: CI mapping documented | Mapping table added | Governance docs |
| AC-2: Names aligned exactly | No alias mismatch | Name validation output |
| AC-3: Review clarity improved | Reviewer checklist references mapping | PR process notes |
| AC-4: Drift detection enabled | Validation method documented | API contract |

## Architecture Decision and Tradeoff Notes
Decision: keep a governance mapping table in markdown instead of introducing policy-as-code tooling for this cycle. Tradeoff: manual upkeep required, low complexity and immediate readability. Decision: enforce exact check-name references to avoid subtle branch protection mismatch. Tradeoff: less flexibility when renaming jobs, significantly lower compliance risk. Decision: treat missing checks as blocker-level governance defects. Tradeoff: stricter gating, improved merge safety.
