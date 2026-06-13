# CYCLE 075 EXECUTABLE SPEC - SCRUM-252

## Objective
SCRUM-252 defines the Cycle 077 planning log contract in `CYCLE_075.md`. The objective is to create or update a canonical planning ledger that records agent assignments, Jira status alignment, governance decisions, and sequencing assumptions for this cycle. The document must support both human review and deterministic compliance checks without requiring interpretation.

## Component Boundaries
- In scope: `PM_Pack/10_cycle_log/CYCLE_075.md` creation/update.
- In scope: assignment matrix for Agent A/B/C/D/E/F and Jira alignment snapshot.
- Out of scope: implementation details inside `src/**` or test execution details.
- Out of scope: modifying historical C074/C073 cycle reports beyond references.

## Data Flow
1. Collect current branch context and known governance-only constraints.
2. Build Cycle 077 planning entries by workstream (governance, implementation, validation).
3. Map each Jira key to owner role and expected artifact.
4. Record status snapshot values (To Do / In Progress / Blocked / Done).
5. Store assumptions and dependencies that affect sequencing.
6. Publish in `CYCLE_075.md` with a date-stamped planning section.

## Error Handling
- Missing cycle log file: create with bootstrap header and planning baseline.
- Ambiguous ownership: assign provisional owner and mark "requires PM confirmation."
- Jira status mismatch with epic tracker: set cycle log as pending reconciliation and flag item.
- Duplicate assignment rows: keep latest timestamp and archive older row under notes.

## API Contract (Governance Interfaces)
```python
def create_cycle_log_if_missing(path: str, cycle_id: str) -> None: ...
def write_cycle_planning_section(path: str, planning_payload: dict) -> None: ...
def validate_assignment_matrix(payload: dict) -> list[str]: ...
def reconcile_jira_status_with_tracker(cycle_log: dict, tracker: dict) -> dict: ...
```

## Validation Strategy
- Structural check: planning section must include assignments, Jira statuses, blockers, and next actions.
- Completeness check: all 20 Cycle 077 Jira keys represented exactly once.
- Ownership check: each key has one primary owner and optional support owner.
- Alignment check: cycle log status terminology matches epic tracker terminology.

## Required Tests
1. `test_scrum_252_cycle_log_created_when_missing`
2. `test_scrum_252_assignment_matrix_has_single_primary_owner`
3. `test_scrum_252_all_jira_keys_present_once`
4. `test_scrum_252_status_alignment_with_tracker_terms`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: `CYCLE_075.md` available | File exists | Repository file tree |
| AC-2: Planning log captures agent roles | Assignment table present | Cycle log section |
| AC-3: Jira status alignment documented | Status table present | Matching labels with tracker |
| AC-4: Dependencies and blockers captured | Blocker list and assumptions | Planning notes subsection |

## Architecture Decision and Tradeoff Notes
Decision: keep the planning ledger in a single cycle markdown file instead of splitting by agent. Tradeoff: centralized clarity versus larger document size. Decision: enforce one primary owner per Jira key to prevent accountability gaps. Tradeoff: lower flexibility for shared tasks but cleaner execution governance. Decision: preserve status as snapshot values instead of live links to Jira API. Tradeoff: manual refresh burden, but avoids introducing API credentials and automation complexity in governance-only scope.
