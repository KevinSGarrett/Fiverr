# CYCLE 062 — AGENT B HANDOFF

Post-merge placeholder (do not replace until D finalizes squash): `[C062_SQUASH_SHA]`

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

### Exact Files to CREATE (prompt-locked list)

- `src/pricing/init.py`
- `src/pricing/analysis.py`
- `src/pricing/new_seller_pricing.py`
- `src/models/price_analysis.py`
- `alembic/versions/migration_12_price_analysis_tables.py`
- `tests/unit/test_price_distribution.py` (>=20 tests)
- `tests/unit/test_new_seller_pricing.py` (>=20 tests)
- `tests/unit/test_pricing_integration.py` (>=10 tests)

### Files to MODIFY (prompt-locked list)

- `src/models/init.py`
- `src/models/database.py`
- `src/analysis/orchestrator.py` or equivalent
- `alembic/env.py`

### Repository Reality Notes (required for implementation feasibility)

- Repository currently uses `src/models/__init__.py` (not `src/models/init.py`).
- Repository migration framework currently exists under `src/migrations/srdi_r8/` and no active `alembic/versions` directory is present.
- Preserve the prompt-locked target filenames in planning, but implement against actual repository structure unless PM governance updates the migration framework.

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

### Stage caller/signature details for B

- Current stage entry is `src.orchestrator.run_pipeline(mode="price-analysis", config_path, database_url)`.
- `run_pipeline` gathers keyword ids and calls `src.pricing.orchestrator.run_pricing_stage(run_id, keyword_ids, db, config)`.
- B’s Stage 10.5 functions must support this run-scoped contract while retaining spec-level per-keyword analysis signatures.

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

## `src/models/__init__.py` Export Pattern Requirement

Current export style uses explicit import lines plus explicit `__all__` entries.

Add lines in the same style:

- `from src.models.price_analysis import PriceAnalysis, NichePriceAnalysis, PricingSnapshot`
- Add `"PriceAnalysis"`, `"NichePriceAnalysis"`, and `"PricingSnapshot"` in `__all__`.

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
