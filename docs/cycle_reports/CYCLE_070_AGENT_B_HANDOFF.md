# CYCLE 070 — AGENT B HANDOFF

Date: 2026-06-07  
Cycle scope: S7.6 Discovery Scoring and Feedback

## Scope Boundaries

- S7.6 is **not** an extension of S7.2-S7.5 hypothesis generation.
- S7.2-S7.5: generation-only logic in `src/discovery/hypothesis.py`.
- S7.6: evaluation/feedback with DB writes, schema migration, and new module.
- Explicit requirement: `S7.6 DIFFERS from S7.2-S7.5. S7.2-S7.5 added functions to hypothesis.py with no DB. S7.6 creates a NEW FILE (feedback.py), NEW MODELS (DiscoveryOutcome+DiscoveryCycleLog), and a NEW MIGRATION (keywords 7 columns + 2 new tables). DB writes are required.`

## Required File Actions

- CREATE: `src/discovery/feedback.py`
- MODIFY: model definitions and exports to align S7.6 fields
- CREATE: `src/migrations/migration_14_s76_discovery_feedback.py` (or next migration number)
- CREATE: `tests/unit/test_discovery_feedback.py` (>=30 tests)

## Prohibited Changes

- Do not edit `PM_Pack/`.
- Do not alter runtime behavior in `config.yaml`.
- Do not perform unrelated refactors in discovery generators.

## `feedback.py` Required API

```python
def evaluate_discovery_results(run_id: str, db) -> dict: ...
def build_feedback_summary(db) -> dict: ...
def _generate_pattern_notes(outcomes: list, mode_stats: dict) -> str: ...
def get_discovery_cycle_stats(run_id: str, db) -> dict: ...
```

## Threshold and Classification Contract

- `GOLD_THRESHOLD = 85`
- `HIT_THRESHOLD = 60`
- `MISS_THRESHOLD = 40`
- `AUTO_RETIRE_THRESHOLD = 30`

Classification rules:

- Gold: `actual_final_score >= 85` -> `is_gold=True`, `is_hit=True`, alert once
- Hit: `actual_final_score >= 60` -> `is_hit=True`
- Monitor: `40 <= score < 60` -> neither hit nor miss
- Miss: `actual_final_score < 40` -> `is_miss=True`
- Auto-retire: `score < 30` -> `keyword.is_retired=True`

## Idempotency (Hard Requirement)

- Only process rows where `keyword.discovery_evaluated` is false.
- Set `keyword.discovery_evaluated = True` after evaluation.
- Running evaluation twice must not:
  - duplicate `DiscoveryOutcome` rows
  - double-fire gold alerts

## Score Delta Contract

- `score_delta = actual_final_score - (hypothesis_confidence * 100)`
- Positive delta: hypothesis underestimated keyword quality.
- Negative delta: hypothesis was overconfident.

## `build_feedback_summary()` Return Contract

```python
{
  "total_hypotheses": int,
  "gold_hits": int,
  "hits": int,
  "misses": int,
  "hit_rate_pct": float,
  "avg_actual_score": float,
  "mode_stats": dict,
  "best_mode": str | None,
  "worst_mode": str | None,
  "top_hit_niches": list,
  "top_miss_niches": list,
  "pattern_notes": str,
  "note": str,  # only when total_hypotheses == 0
}
```

Empty-history contract:

```python
{"total_hypotheses": 0, "note": "No discovery history yet — first cycle"}
```

## Migration Contract (Exact Steps)

1. Create `discovery_outcomes` table with FK `keyword_id -> keywords.id`.
2. Create `discovery_cycle_logs` table with run-level feedback storage.
3. Add `keywords.is_discovery` BOOLEAN DEFAULT FALSE.
4. Add `keywords.discovery_mode` VARCHAR NULLABLE.
5. Add `keywords.hypothesis_confidence` FLOAT NULLABLE.
6. Add `keywords.hypothesis_rationale` TEXT NULLABLE.
7. Add `keywords.discovered_in_run` VARCHAR NULLABLE.
8. Add `keywords.discovery_evaluated` BOOLEAN DEFAULT FALSE.
9. Add `keywords.is_retired` BOOLEAN DEFAULT FALSE.
10. Add indexes: `is_discovery`, `discovery_evaluated`, `is_retired`.

Table field requirements:

- `discovery_outcomes` includes `keyword_id` FK and outcome flags: `is_gold`, `is_hit`, `is_miss`.
- `discovery_cycle_logs` includes `run_id` and `feedback_summary` JSON payload.

Migration properties:

- Forward-only safe (no data loss).
- Downgrade path required (reversible schema changes).

## Alert Import Fallback Requirement

Try in order:

1. `from src.monitoring.monitors import create_alert`
2. `from src.alerts import create_alert`
3. If both fail: log warning and continue without crashing.

## Implementation Notes

- `src/discovery/feedback.py` is absent at C070 start and should be newly created.
- Existing DB already contains discovery tables, but keyword schema is incomplete in baseline DB; migration must align all required fields.
