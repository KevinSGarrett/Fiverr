# CYCLE 071 - AGENT C HANDOFF

## S7.7 Gate Checklist

- `src/discovery/integration.py` importable with 5 required functions.
- `insert_discovery_keyword()` inserts new row with all 7 lineage fields populated.
- Duplicate insert path returns `None` (no raise).
- `check_discovery_keyword_exists()` performs case-insensitive match.
- `process_accepted_hypotheses()` processes only `accepted=True`.
- `process_accepted_hypotheses()` return dict includes all keys:
  - `inserted`
  - `skipped`
  - `run_id`
  - `keyword_ids`
- `get_pending_discovery_keywords()` excludes retired rows.
- Cross-seed and cross-discovery dedup both enforced.

## Non-Functional Gates

- Golden parity remains: `kw=110 => 62.7 / 1.0 / CONDITIONAL_GO`.
- Coverage >=90%.
- S7.7 tests >=30 and all green.
- Existing S7.2-S7.6 behavior remains intact.

## Evidence Requirements in C Report

- Schema evidence that C071 required no migration.
- Before/after counts proving dedup behavior.
- At least one positive insert sample with lineage field assertions.
- Empty-list batch contract sample.
