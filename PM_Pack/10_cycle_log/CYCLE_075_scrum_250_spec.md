# CYCLE 075 EXECUTABLE SPEC - SCRUM-250

## Objective
SCRUM-250 governs hydration header alignment for Cycle 077 so every agent starts from a single, current state. The objective is to add a scoped Cycle 077 section that explicitly lists in-scope Jira keys, planning assumptions, and blockers discovered during governance pass. This prevents stale context propagation across parallel agents and establishes a deterministic "read-first" control point.

## Component Boundaries
- In scope: `PM_Pack/07_hydration/HYDRATION_HEADER.md` Cycle 077 governance section and related references.
- In scope: references to cycle logs and epic status tracker for cross-checking.
- Out of scope: historical cycle rewrites except minimal non-destructive additions.
- Out of scope: source code, tests, pipeline commands, and DB artifacts.

## Data Flow
1. Read active hydration state and current blocker section.
2. Compile Cycle 077 Jira set: SCRUM-246, 250, 252, 253, 254, 256, 258, 280, 281, 282, 283, 284, 286, 439, 440, 441, 446, 450, 451, 452.
3. Produce Cycle 077 scope block with objective, ownership, and blocker snapshot.
4. Link scope block to cycle log and epic tracker entries for consistency.
5. Validate no contradictory status statement remains for the same Jira keys.

## Error Handling
- Duplicate key listing in hydration section: preserve first canonical list, remove duplicates in new section.
- Missing blocker evidence: mark as "no hard blockers observed" plus open assumptions.
- Contradictory cycle identifiers: fail update and add correction note before merge.
- Invalid markdown table format: fallback to bullet list with stable key ordering.

## API Contract (Governance Interfaces)
```python
def generate_hydration_cycle_scope(cycle_label: str, jira_keys: list[str]) -> str: ...
def append_blocker_snapshot(doc: str, blockers: list[str]) -> str: ...
def assert_hydration_key_consistency(doc: str, expected: set[str]) -> list[str]: ...
def link_hydration_to_cycle_log(doc: str, cycle_log_path: str) -> str: ...
```

## Validation Strategy
- Key completeness check: hydration section must include all 20 Jira keys.
- Order stability check: keys are listed in ascending numeric order for quick scanning.
- Blocker declaration check: explicitly states blockers or explicit "none" statement.
- Cross-document check: key set equals cycle log and epic tracker key set.

## Required Tests
1. `test_scrum_250_hydration_contains_all_cycle_077_keys`
2. `test_scrum_250_hydration_declares_blockers_or_none`
3. `test_scrum_250_hydration_cycle_reference_matches_tracker`
4. `test_scrum_250_hydration_order_is_stable`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Cycle 077 scope visible in hydration | New section added | Updated hydration file |
| AC-2: Jira key set complete | 20 keys present | Key list comparison output |
| AC-3: Blockers documented | Blocker subsection present | "Blockers discovered" entry |
| AC-4: Alignment with trackers | No mismatched keys | Cross-doc review checklist |

## Architecture Decision and Tradeoff Notes
Decision: represent Cycle 077 scope as a dedicated hydration subsection instead of replacing older blocks. Tradeoff: document grows longer but preserves audit history. Decision: keep blocker capture lightweight (bullets) rather than adding a separate schema file. Tradeoff: easier maintenance versus less strict machine validation. Decision: maintain ordered Jira keys as a governance invariant. Tradeoff: slight manual overhead but reduces review mistakes when matching against PR templates and tracker tables.
