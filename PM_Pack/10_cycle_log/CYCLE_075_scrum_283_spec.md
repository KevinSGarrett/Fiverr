# CYCLE 075 EXECUTABLE SPEC - SCRUM-283

## Objective
SCRUM-283 establishes blocker documentation rules for Cycle 077 governance artifacts. The objective is to enforce explicit blocker capture in hydration and planning logs, including ownership and mitigation path, so execution teams can distinguish hard blockers from advisory risks. This avoids "silent unknowns" during cycle handoff.

## Component Boundaries
- In scope: blocker sections in hydration header and cycle planning log.
- In scope: blocker severity labels and mitigation notes.
- Out of scope: implementing blocker fixes in code.
- Out of scope: Jira workflow automation.

## Data Flow
1. Review existing blocker declarations in hydration.
2. Compare against discovered governance risks during Cycle 077 setup.
3. Classify each item as hard blocker, soft blocker, or advisory.
4. Add scoped blocker snapshot in hydration and cycle log.
5. Include owner and next action for each non-advisory blocker.

## Error Handling
- Missing evidence for blocker claim: downgrade to advisory with evidence request.
- Duplicate blocker in multiple docs: retain one canonical entry and reference it.
- Severity inflation: require impact statement before "hard blocker" label.
- No blockers found: add explicit none statement to prevent ambiguity.

## API Contract (Governance Interfaces)
```python
def classify_blocker(item: dict) -> str: ...
def write_blocker_snapshot(doc_text: str, blockers: list[dict]) -> str: ...
def ensure_blocker_owner_and_next_action(blockers: list[dict]) -> list[str]: ...
def reconcile_blockers_between_docs(hydration: str, cycle_log: str) -> list[str]: ...
```

## Validation Strategy
- Presence check: blocker section exists in both required docs.
- Completeness check: each blocker has severity, owner, and mitigation.
- Consistency check: blocker IDs/phrasing align across docs.
- None-case check: explicit statement present if zero blockers.

## Required Tests
1. `test_scrum_283_blockers_include_owner_and_next_action`
2. `test_scrum_283_supports_explicit_no_blockers_state`
3. `test_scrum_283_severity_requires_impact_statement`
4. `test_scrum_283_hydration_cycle_log_blockers_consistent`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Blockers are explicit | Blocker section present | Updated docs |
| AC-2: Severity is standardized | Label taxonomy used | Blocker table |
| AC-3: Actionability ensured | Owner + mitigation listed | Blocker entries |
| AC-4: Consistency preserved | Cross-doc blocker match | Reconciliation note |

## Architecture Decision and Tradeoff Notes
Decision: represent blockers in markdown tables or bullets with required fields rather than a new schema file. Tradeoff: flexible editing, lower machine strictness. Decision: differentiate hard blockers from advisory risks to prevent unnecessary stop-the-line decisions. Tradeoff: classification requires judgment, but execution clarity improves. Decision: keep blocker reconciliation lightweight and manual in this cycle. Tradeoff: no automated sync, but low operational overhead.
