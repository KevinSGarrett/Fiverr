# CYCLE 071 - AGENT B HANDOFF

## Scope

Implement S7.7 Discovery Keyword Integration (INSERT stage) in:

- CREATE: `src/discovery/integration.py`
- CREATE: `tests/unit/test_discovery_integration.py` (>=30 tests)

Do not edit `PM_Pack/` from B. Keep C071 as no-migration story.

## Required Public API

```python
def insert_discovery_keyword(hypothesis, run_id, db, niche_id=None) -> int | None: ...
def queue_discovery_collection(keyword_id, run_id, db) -> bool: ...
def process_accepted_hypotheses(hypotheses, run_id, db) -> dict: ...
def get_pending_discovery_keywords(db) -> list: ...
def check_discovery_keyword_exists(keyword_text, niche_id, db) -> int | None: ...
```

## Dedup Contract (Hard Requirement)

- Dedup by case-insensitive normalized keyword text + niche.
- Apply against both discovery and non-discovery keyword rows.
- On duplicate: return `None` (no exception), DEBUG log only.
- Same keyword text in different niche is allowed.

Repository schema note:

- DB/ORM column is `Keyword.keyword` (not `keyword_text`).
- Map prompt contract semantics to repository naming without changing behavior.

## Lineage Contract (Set Atomically on Insert)

Populate all seven fields in the same insert transaction:

1. `is_discovery = True`
2. `discovery_mode = <hypothesis mode>`
3. `hypothesis_confidence = <specificity/confidence>`
4. `hypothesis_rationale = <reason>`
5. `discovered_in_run = run_id`
6. `discovery_evaluated = False`
7. `is_retired = False`

## Batch Return Contract

`process_accepted_hypotheses()` must always return:

```python
{
  "inserted": int,
  "skipped": int,
  "run_id": str,
  "keyword_ids": list,
}
```

All four keys are mandatory even for empty input.

## Query Contract

`get_pending_discovery_keywords()` returns only:

- `is_discovery == True`
- `discovery_evaluated == False`
- `is_retired == False`

## run_id Guidance

Use existing repository conventions (`uuid4` and timestamp-style IDs both exist). Reuse orchestrator-compatible run_id format; do not invent incompatible IDs.

## S7.7 vs S7.6 Clarifier

- S7.6 (C070): evaluate/feedback stage (`feedback.py`), writes outcomes/logs.
- S7.7 (C071): insert stage (`integration.py`), writes new `Keyword` rows only.
- C071 requires **no migration**; migration_14 already includes needed columns.
