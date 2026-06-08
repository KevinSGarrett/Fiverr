# CYCLE 071 - AGENT F HANDOFF

## Required S7.7 Edge-Case Tests

Add focused tests for `src/discovery/integration.py`:

- duplicate keyword returns `None`; count unchanged
- empty hypothesis list returns inserted=0/skipped=0 with all return keys
- case-insensitive dedup (`Python AI` vs `python ai`)
- `accepted=False` hypotheses are skipped
- same keyword text in different niche is allowed
- lineage fields all populated on insert
- retired keywords excluded from pending query

## Additional Behavioral Tests

- queue operation returns false for missing/already-queued rows
- batch collects and returns inserted IDs deterministically
- rationale fallback behavior when reason is missing/None

## Quality Gates

- Add >=30 S7.7 tests.
- Keep overall suite coverage >=90%.
- Keep changes inside `tests/` plus F report doc scope.
