# CYCLE 075 EXECUTABLE SPEC - SCRUM-282

## Objective
SCRUM-282 defines cross-artifact Jira key integrity rules for Cycle 077. The objective is to guarantee that hydration header, cycle log, epic status tracker, PR template required field, and per-ticket spec files all carry an identical key set. This eliminates partial-scope merges and reduces governance review friction.

## Component Boundaries
- In scope: key set consistency across `PM_Pack` governance files and PR template.
- In scope: deterministic ordering and uniqueness constraints.
- Out of scope: Jira API synchronization and live status polling.
- Out of scope: any implementation logic outside governance artifacts.

## Data Flow
1. Build canonical key set from cycle mandate.
2. Parse each governance artifact for key extraction.
3. Compare sets and ordering against canonical source.
4. Produce discrepancy report and corrective edits.
5. Persist final aligned state across all artifacts.

## Error Handling
- Missing key in any file: append key and annotate fix date.
- Extra non-scope key included: retain if historical, but isolate from Cycle 077 section.
- Key format mismatch (e.g., typo): normalize and record correction.
- Parsing failure for free-text section: fallback manual checklist.

## API Contract (Governance Interfaces)
```python
def canonical_cycle_keys(cycle_id: str) -> list[str]: ...
def extract_jira_keys_from_markdown(doc_text: str) -> set[str]: ...
def compare_key_sets(expected: set[str], observed: set[str]) -> dict[str, set[str]]: ...
def enforce_ordered_unique_key_list(keys: list[str]) -> list[str]: ...
```

## Validation Strategy
- Set equality check across all five governance surfaces.
- Order check for reviewer readability.
- Typo check against `SCRUM-\d+` pattern.
- Residual mismatch check must return empty after patch.

## Required Tests
1. `test_scrum_282_key_set_equal_across_governance_files`
2. `test_scrum_282_keys_are_unique_and_sorted`
3. `test_scrum_282_rejects_nonconforming_key_format`
4. `test_scrum_282_reports_missing_and_extra_keys`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Canonical key set defined | List committed in governance docs | Cycle scope sections |
| AC-2: All artifacts aligned | Set diff empty | Consistency checklist |
| AC-3: Reviewer scan optimized | Ordered keys | Visual inspection |
| AC-4: Drift detection available | Comparison method documented | API contract section |

## Architecture Decision and Tradeoff Notes
Decision: use one canonical key list propagated to all docs. Tradeoff: updates require multi-file edits, but consistency is guaranteed. Decision: prefer deterministic ordering by numeric key suffix. Tradeoff: manual insertion constraints, easier diff review. Decision: keep matching logic lightweight and regex-based. Tradeoff: limited semantic awareness, but sufficient for governance key integrity.
