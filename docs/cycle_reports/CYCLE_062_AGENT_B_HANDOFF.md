# CYCLE 062 — AGENT B HANDOFF

## Scope and Zone

- Zone: `src/` + required migration wiring + B report.
- You own Wave 9 implementation (9A + 9B) for production-grade Stage 10.5.
- Preserve golden parity (`kw=110` remains `62.7 / 1.0 / CONDITIONAL_GO`) by keeping pricing additive after scoring.

## Current State Snapshot (From A Validation)

- `src/pricing/` already exists with scaffolded and partially implemented files:
  - `src/pricing/analysis.py`
  - `src/pricing/new_seller_pricing.py`
  - `src/pricing/orchestrator.py`
  - `src/pricing/contracts.py`
  - `src/pricing/__init__.py`
- Existing implementation is incomplete vs Wave 9 specs:
  - Missing full `scipy` KDE/peak-driven cluster logic from 9A.
  - Uses legacy table names (`price_analyses`) and partial schema.
  - Does not provide the exact Stage 10.5 integration contract required by cycle prompt.
- DB state (`data/foundation_gate_ci.db`):
  - `price_analysis`: absent
  - `niche_price_analysis`: absent
  - `pricing_snapshots`: exists
  - `price_analyses`: exists (legacy table; reconcile during migration planning)

## Required Files — Create or Replace

### New/Target Files (must exist after B)

- `src/pricing/__init__.py` (ensure exports match new modules)
- `src/pricing/analysis.py`
- `src/pricing/new_seller_pricing.py`
- `src/models/price_analysis.py` (new ORM definitions for canonical tables)
- `src/migrations/srdi_r8/migration_12_price_analysis_tables.py`  
  (Repo uses `src/migrations/srdi_r8/`, not Alembic; follow migration_11 pattern.)
- `tests/unit/test_price_distribution.py` (>=20 tests)
- `tests/unit/test_new_seller_pricing.py` (>=20 tests)
- `tests/unit/test_pricing_integration.py` (>=10 tests)

### Existing Files to Modify

- `src/models/__init__.py`
  - Follow existing import/export style.
  - Add explicit exports for `PriceAnalysis`, `NichePriceAnalysis`, and `PricingSnapshot` from your canonical pricing model module.
- `src/models/database.py`
  - Register any new model classes so schema initialization includes them.
- `src/orchestrator.py` and/or pricing execution entry point
  - Wire Stage 10.5 after scoring and before recommendation/opportunity ranking flow.
- `run.py` (if mode hooks/signatures need adjustment for Stage 10.5 contract)
- `src/pricing/orchestrator.py`
  - Replace stub behavior with spec-compliant execution path.

## Required Function Signatures (Spec-Locked)

- `analyze_price_distribution(keyword_id: int, db) -> dict[str, PriceDistribution]`
- `detect_price_clusters(prices: np.ndarray, bandwidth_factor: float = 0.15) -> list[dict]`
- `detect_price_gaps(prices: np.ndarray, min_gap_pct: float = 0.20) -> list[dict]`
- `calculate_price_review_correlation(keyword_id: int, db) -> dict`
- `calculate_new_seller_pricing(keyword_id, price_analysis, niche_config, db) -> PricingRecommendation`

Implement helper functions required by spec:
- `_calculate_undercut`
- `_calculate_moat_adjustment`
- `_find_gap_opportunity`
- `_apply_discount`
- `_get_floor_price`
- `_build_price_ladder`
- `_assess_pricing_confidence`

## Orchestration Calling Convention (Observed)

- `run.py` command `price-analysis` routes to `src.orchestrator.run_pipeline(mode="price-analysis", ...)`.
- In `src/orchestrator.py`, mode `price-analysis` currently calls:
  - `run_pricing_stage(run_id: str, keyword_ids: list[int], db, config)`
- Stage execution uses `run_id` + DB session + config payload, not a pure `(keyword_id, db)` global loop from CLI.
- Preserve this contract or update both caller and callee consistently.

## Migration Pattern Requirement

Repository migration pattern is file-based under `src/migrations/srdi_r8/` with `apply(engine)` functions.

Use `migration_11_external_signal_tc1_cols.py` as template:
- no Alembic revision ids
- idempotent DDL style
- explicit `apply(engine)` entry point

For migration_12:
- create canonical `price_analysis` and `niche_price_analysis` tables
- reconcile legacy `price_analyses` and existing `pricing_snapshots` without destructive data loss
- ensure downgrade/rollback guidance is documented if no formal downgrade hook exists

## Dependencies and Environment

- `requirements.txt` currently includes:
  - `numpy==2.4.0`
  - `scipy==1.17.1`
- Runtime import check passed:
  - `numpy` and `scipy` importable
  - `scipy.signal.find_peaks`, `scipy.stats.gaussian_kde`, `pearsonr`, `spearmanr` importable

## Spec References (Read Before Coding)

- `PM_Pack/ref/project_plan/09_pricing/PRICE_DISTRIBUTION_ANALYSIS.md`
- `PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md`
- `PM_Pack/ref/project_plan/00_meta/ENHANCEMENT_WAVE_SCHEDULE.md`

## Parity and Hard Gates

- Keep OFF==legacy golden parity unchanged.
- Do not modify `config.yaml` toggle defaults.
- Enforce schema parity between ORM and migration-created tables.
- No secrets in committed files.

## B Deliverables Checklist

- [ ] Stage 10.5 implementation complete and wired.
- [ ] Migration 12 created and runnable in repo migration framework.
- [ ] ORM + DB parity validated (`price_analysis`, `niche_price_analysis`, `pricing_snapshots`).
- [ ] Unit and integration tests added (thresholds met).
- [ ] Golden anchor unaffected.
- [ ] B report captures changed files, migration evidence, and coverage for new pricing code.
