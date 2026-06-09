# CYCLE 073 - AGENT B HANDOFF

## Scope

Implement S7.9 Discovery Dashboard Widgets data layer in:

- UPDATE: `src/dashboard/pages/discovery.py`
- CREATE: `tests/unit/test_discovery_dashboard.py` (target >=30 tests)

No migration is authorized in C073.

## Required Public API

```python
def get_discovery_stats(db) -> dict: ...
def get_gold_discoveries(db, limit=50) -> list[dict]: ...
def get_mode_performance(db) -> dict[str, dict]: ...
def render_discovery_page() -> None: ...
```

## Import Structure Contract

Top-level imports in `discovery.py` should remain lightweight:

- `from __future__ import annotations`
- `from typing import Any`
- `from src.dashboard.db_helpers import get_db_session`

Lazy imports inside helper functions:

- `from src.models import DiscoveryCycleLog, Keyword`
- `from sqlalchemy import func`

No top-level SQLAlchemy import that would fail in DB-sparse contexts.

## `get_discovery_stats(db)` Contract

Required query behavior:

- aggregate from `DiscoveryCycleLog`:
  - count rows
  - sum accepted
  - sum gated
  - max cycle timestamp
- fetch latest row for `last_run_id`

Required return keys:

- `total_runs`
- `total_inserted`
- `total_gated`
- `last_run_at`
- `last_run_id`

Implementation rules:

- `int()` cast count/sum outputs
- coalesce nullable aggregation values safely
- full function wrapped in:

```python
try:
    ...
except Exception:  # noqa: BLE001
    return {
        "total_runs": 0,
        "total_inserted": 0,
        "total_gated": 0,
        "last_run_at": None,
        "last_run_id": None,
    }
```

## `get_gold_discoveries(db, limit=50)` Contract

Filter behavior:

- `Keyword.is_discovery == True`
- score threshold `>= 0.70`
- order descending by score
- limit to `limit` rows

Returned dict fields:

- `keyword_text`
- `niche_id`
- `discovery_mode`
- `specificity_score`
- `discovered_in_run`

Implementation rules:

- use `getattr()` for optional model fields
- cast `niche_id` with `str(...)`
- wrap entire function in `try/except Exception` and return `[]` on error

Threshold clarifier:

- S7.9 threshold `0.70` is discovery quality pre-score threshold
- S7.6 `GOLD_THRESHOLD=85.0` is post-score outcome threshold
- both are valid and should not be conflated

## `get_mode_performance(db)` Contract

Behavior:

- filter discovery rows only
- group by `discovery_mode`
- compute:
  - row count per mode
  - average score per mode

Normalization:

- map `None` discovery mode to `"unknown"`
- round averages to 3 decimals

Error handling:

- wrap full function in `try/except Exception`
- return `{}` on error

## `render_discovery_page()` Contract

Required rendering behavior:

- call all 3 helper functions inside one `get_db_session()` context
- show top metrics with `st.columns(3)`:
  - total runs
  - total inserted
  - total gated
- show `st.caption` for `last_run_id` when present
- gold section:
  - `st.dataframe(...)` when data exists
  - `st.info(...)` when empty
- mode section:
  - `st.dataframe(...)` when data exists
  - `st.info(...)` when empty
- no crash in empty/sparse DB

## Error-Handling Pattern (Mandatory)

Each new helper follows:

```python
def helper(db):
    try:
        ...
        return payload
    except Exception:  # noqa: BLE001
        return empty_safe_payload
```

This explicit BLE001 pattern is accepted for dashboard stability in sparse environments.

## Non-Functional Gates

- no migration file add/update
- `src/discovery/stage16.py` unchanged
- golden parity unchanged (`kw=110 -> 62.7/1.0/CONDITIONAL_GO`)
- preserve `__main__` guard in discovery page
