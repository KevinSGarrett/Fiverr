# CYCLE 064 — AGENT B HANDOFF

Date: 2026-06-04  
Branch: `cycle/064/integration`  
Base SHA: `fec8d9d`

## Scope

Wave 9 Phase 3 implementation for:

- 9E Price Ladder Tracker
- 9F Revenue Gate Tracker
- `llm_usage_logs.task_type` observability column fix
- Tier-A stale docstring fix in `src/recommendations/executor.py` ("11 tasks" -> "12 tasks")

## Required Files

### Create

- `src/pricing/ladder_tracker.py` (9E: PriceLadderSnapshot ORM + tracking functions)
- `src/pricing/revenue_gate.py` (9F: RevenueGateRecord ORM + gate functions)
- `src/models/price_ladder_snapshot.py` (ORM model)
- `src/models/revenue_gate_record.py` (ORM model)
- `src/migrations/srdi_r8/migration_13_ladder_revenue_llm_observability.py`
- `tests/unit/test_ladder_tracker.py` (>=20 tests)
- `tests/unit/test_revenue_gate.py` (>=15 tests)

### Modify

- `src/pricing/__init__.py` (add exports)
- `src/models/__init__.py` (add exports)
- `src/recommendations/executor.py` (docstring fix: 11 -> 12 tasks)
- `src/analysis/orchestrator.py` (optional Stage 10.6 call wiring, additive only)

## Function Signatures (Implement Exactly)

- `track_price_ladder(keyword_id: int, actual_basic: float, actual_standard: float, actual_premium: float, db) -> PriceLadderSnapshot`
- `get_ladder_progress(keyword_id: int, db) -> list[dict]`
- `is_pricing_on_track(keyword_id: int, db, tolerance: float = 0.15) -> bool`
- `check_revenue_gates(keyword_id: int, db) -> list[RevenueGateRecord]`
- `fire_revenue_gate_alert(keyword_id: int, milestone_reviews: int, db) -> str | None`

## 9E Model Design — PriceLadderSnapshot

Recommended columns:

- `id` PK
- `keyword_id` FK
- `niche_id`
- `run_id`
- `recorded_at`
- `reviews_at_snapshot` (int)
- `actual_basic_price` (float)
- `actual_standard_price` (float)
- `actual_premium_price` (float)
- `recommended_basic_price` (float)
- `recommended_standard_price` (float)
- `recommended_premium_price` (float)
- `ladder_milestone` (int; nearest of 5, 10, 25, 50, 100)
- `price_delta_pct` (float)
- `on_track` (bool; within tolerance, default 15%)

Expected source data:

- Recommended milestone pricing from `pricing_snapshots.price_ladder` JSON (present in DB).
- Keyword relationship key from `pricing_snapshots.keyword_id` (present in DB).
- Review signal source should use `gigs.review_count`/`gigs.review_count_exact` path (Keyword model has no direct review field).

## 9F Model Design — RevenueGateRecord

Recommended columns:

- `id` PK
- `keyword_id` FK
- `niche_id`
- `run_id`
- `recorded_at`
- `milestone_reviews` (int; 5, 10, 25, 50, 100)
- `gate_triggered` (bool)
- `recommended_price_at_gate` (float)
- `actual_price_at_gate` (float)
- `revenue_delta_usd` (float)
- `gate_alert_text` (str | None)

Gate logic should remain additive only (tracking/alerting), with no scoring mutations.

## Migration 13 Scope (Single Combined Migration Recommended)

Create one combined migration (`migration_13_ladder_revenue_llm_observability.py`) with:

1. `CREATE TABLE price_ladder_snapshots (...)`
2. `CREATE TABLE revenue_gate_records (...)`
3. `ALTER TABLE llm_usage_logs ADD COLUMN task_type VARCHAR(64) DEFAULT NULL`

Notes:

- Current latest migration is `migration_12_price_analysis_tables.py`.
- `llm_usage_logs.task_type` is currently missing in `data/foundation_gate_ci.db`.
- Preserve legacy `price_analyses` table (advisory carry-forward only); do not drop or rename in C064.

## Verified Baseline Facts for Implementation

- Golden parity baseline unchanged: kw=110 is `62.7 / 1.0 / CONDITIONAL_GO`.
- C064 is tracking/alerting only; do not alter scoring pipeline outputs.
- Pricing tables currently present:
  - `price_analysis` (53 columns)
  - `price_analyses` (25 columns; legacy advisory)
  - `pricing_snapshots` (21 columns with `keyword_id` + `price_ladder`)
- Recommendations table does **not** have `pricing_strategy` or `output_json` columns; strategy payload pattern is stored in `raw_json`.

## Optional Stage 10.6 Wiring Guidance

`src/orchestrator.py` currently runs Stage 10.5 via `run_pricing_stage(...)` and logs completion.  
If wiring Stage 10.6:

- call tracker after Stage 10.5 outputs are available,
- skip gracefully when review_count is unavailable/zero,
- keep behavior non-blocking and additive,
- no scoring gate/output changes.
