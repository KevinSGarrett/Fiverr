# CYCLE 075 EXECUTABLE SPEC - SCRUM-441

## Objective
SCRUM-441 governs traceability links between per-ticket specs and cycle planning artifacts. The objective is to ensure each SCRUM spec can be navigated from the cycle log and each cycle assignment references its corresponding executable spec. This creates bidirectional traceability needed for rapid review, onboarding, and incident retrospectives.

## Component Boundaries
- In scope: links among `CYCLE_075.md`, per-ticket spec files, hydration section, and epic tracker references.
- In scope: stable naming convention for spec files.
- Out of scope: external tooling indexes or generated documentation portals.
- Out of scope: changes to source implementation files.

## Data Flow
1. Generate per-ticket spec files using consistent naming.
2. Build a cycle log table that links Jira key to spec path.
3. Add references from hydration/tracker scope sections to cycle log.
4. Validate all links resolve and no orphan specs remain.
5. Publish traceability status in governance summary.

## Error Handling
- Broken relative path link: replace with repository-root path notation.
- Orphan spec without cycle log row: add row or mark as deferred.
- Jira key in cycle log without spec: mark as non-compliant.
- Duplicate spec for one key: keep canonical file and archive duplicate note.

## API Contract (Governance Interfaces)
```python
def build_traceability_index(jira_keys: list[str], base_path: str) -> dict[str, str]: ...
def validate_traceability_links(index: dict[str, str]) -> list[str]: ...
def attach_traceability_table_to_cycle_log(cycle_log_text: str, index: dict[str, str]) -> str: ...
def detect_orphan_specs(spec_paths: list[str], keys: set[str]) -> list[str]: ...
```

## Validation Strategy
- Completeness check: one spec path per required Jira key.
- Reachability check: every referenced path exists.
- Orphan check: no unlinked spec file in cycle scope.
- Format check: consistent file naming `CYCLE_075_scrum_<id>_spec.md`.

## Required Tests
1. `test_scrum_441_traceability_index_has_one_to_one_key_mapping`
2. `test_scrum_441_all_linked_spec_paths_exist`
3. `test_scrum_441_orphan_spec_detection_flags_unlinked_files`
4. `test_scrum_441_cycle_log_contains_traceability_table`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Bidirectional traceability established | Key-to-spec index published | Cycle log table |
| AC-2: No orphaned specs | Orphan report empty | Validation output |
| AC-3: Naming convention enforced | All files follow format | File list check |
| AC-4: Reviewer navigation improved | Links from top-level docs present | Updated docs |

## Architecture Decision and Tradeoff Notes
Decision: maintain traceability using explicit markdown path tables instead of generated docs tooling. Tradeoff: manual maintenance effort, straightforward and transparent review process. Decision: adopt strict filename convention embedding cycle and scrum id. Tradeoff: verbose names, strong discoverability and scriptability. Decision: keep index in cycle log as canonical source. Tradeoff: larger cycle file, reduced cross-file ambiguity.
