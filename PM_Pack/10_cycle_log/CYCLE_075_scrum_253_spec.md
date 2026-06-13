# CYCLE 075 EXECUTABLE SPEC - SCRUM-253

## Objective
SCRUM-253 specifies Epic tracker synchronization for Cycle 077. The objective is to ensure `EPIC_STATUS_TRACKER.md` reflects the exact Cycle 077 in-scope Jira keys with a consistent status snapshot that matches hydration and cycle log artifacts. This creates a stable governance state for reviewers and prevents cross-document drift during multi-agent execution.

## Component Boundaries
- In scope: `PM_Pack/08_task_queue/EPIC_STATUS_TRACKER.md` updates for cycle scope and status.
- In scope: cycle-level status table, timestamp, and reconciliation notes.
- Out of scope: historical row rewriting unless needed for current-cycle context.
- Out of scope: any non-governance source files or runtime behavior.

## Data Flow
1. Read existing epic tracker wave and Jira sections.
2. Add Cycle 077 scope section with the 20 Jira keys.
3. Capture status snapshot categories (To Do, In Progress, Blocked, Done).
4. Cross-check status labels against cycle log entries.
5. Publish reconciliation note that indicates snapshot timestamp and confidence.

## Error Handling
- Missing tracker section anchor: insert section at end with explicit heading.
- Key duplication between old and new sections: keep latest section as canonical.
- Conflicting status labels: flag "status conflict" and preserve both values with source label.
- Markdown table corruption: fallback to bullet-based format with deterministic ordering.

## API Contract (Governance Interfaces)
```python
def update_epic_tracker_cycle_scope(path: str, cycle_id: str, jira_keys: list[str]) -> None: ...
def snapshot_jira_status(keys: list[str], default_status: str = "To Do") -> dict[str, str]: ...
def compare_tracker_vs_cycle_log(tracker: dict, cycle_log: dict) -> list[str]: ...
def write_reconciliation_note(path: str, conflicts: list[str]) -> None: ...
```

## Validation Strategy
- Presence check: Cycle 077 section exists in epic tracker.
- Key set check: section includes all required keys exactly once.
- Status vocabulary check: only approved labels are used.
- Drift check: no unresolved status conflicts between tracker and cycle log.

## Required Tests
1. `test_scrum_253_tracker_includes_cycle_077_scope_section`
2. `test_scrum_253_tracker_contains_exact_jira_key_set`
3. `test_scrum_253_status_labels_use_allowed_vocabulary`
4. `test_scrum_253_reconciliation_note_written_on_conflict`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Cycle scope captured in tracker | New section exists | Updated tracker file |
| AC-2: Status snapshot visible | Status table populated | Snapshot timestamp row |
| AC-3: Cross-doc alignment | No unresolved key mismatch | Reconciliation note |
| AC-4: Reviewer-ready readability | Deterministic ordering | Ordered key list |

## Architecture Decision and Tradeoff Notes
Decision: maintain a dedicated Cycle 077 section instead of blending into historical tables. Tradeoff: larger document, stronger audit clarity. Decision: store snapshot statuses manually in markdown, not via Jira API sync. Tradeoff: less automation but no dependency on external tokens or flaky integration at governance stage. Decision: reconcile conflicts explicitly in-document. Tradeoff: minor verbosity increase, but immediate reviewer visibility and lower risk of hidden drift.
