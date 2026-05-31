# CYCLE 053 - AGENT B REPORT

Date: 2026-05-31  
Branch: `cycle/053/integration`  
Role: Agent B (`src/` implementation owner)

## Scope Completed

Implemented the full Stage 3.5 Result-Set Relevance Validation feature slice behind `relevance.enable_stage_3_5`, including validator math/signals, migration + ORM, Stage 3.5 workflow + orchestration insertion, scoring hooks, eligibility ghost hard block + Stage 12 demotion, bounded config additions, and required unit/integration/regression updates.

## Files Created

- `src/analysis/result_set_validator.py`
- `src/collection/workflows/result_set_validation_workflow.py`
- `src/migrations/srdi_r8/migration_08_r2_columns.py`
- `src/scoring/result_set_relevance.py`
- `tests/unit/test_result_set_validator.py`
- `tests/unit/test_migration_08_r2_columns.py`
- `tests/integration/test_stage_3_5_pipeline.py`
- `docs/cycle_reports/CYCLE_053_AGENT_B.md`

## Files Modified

- `src/migrations/srdi_r8/run_srdi_r8_migrations.py`
- `src/models/result_set_validation.py`
- `src/collection/orchestrator.py`
- `src/scoring/confidence.py`
- `src/scoring/competition.py`
- `src/scoring/demand.py`
- `src/recommendations/eligibility.py`
- `src/scoring/pipeline.py`
- `src/config/models.py`
- `config.yaml`
- `tests/unit/test_confidence_score.py`
- `tests/unit/test_competition_score.py`
- `tests/unit/test_demand_score_extended.py`
- `tests/unit/test_recommendation_eligibility.py`
- `tests/unit/test_collection_orchestrator.py`
- `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md`

## Config Gate Evidence

`config.yaml` diff in `relevance` block is exactly:

- `enable_stage_3_5: true`
- `relevance_flag_threshold: 0.35`
- `ghost_market_threshold_default: 0.20`

No other `config.yaml` lines were changed for this gate.

## Schema / Migration Evidence

`ResultSetValidation` now contains both required columns:

- `category_contamination_flag`
- `used_fallback_strictness`

Runtime column print:

```text
['keyword_id', 'run_id', 'validated_at', 'result_count', 'relevant_count', 'sponsored_count', 'result_set_relevance_score', 'ghost_market_flag', 'ghost_evidence', 'validation_method', 'search_strictness_used', 'per_gig_relevance', 'relevance_deduction', 'category_contamination_flag', 'used_fallback_strictness', 'id', 'created_at', 'updated_at']
```

Migration proof (`tests/unit/test_migration_08_r2_columns.py`):

- apply adds both columns
- second apply is idempotent
- rollback drops both columns
- re-apply after rollback succeeds
- defaults on existing rows verified
- registration order after `migration_07` verified

## Test Evidence (file-scoped)

- `python -m pytest -q tests/unit/test_result_set_validator.py` -> **14 passed**
- `python -m pytest -q tests/integration/test_stage_3_5_pipeline.py` -> **8 passed**
- `python -m pytest -q tests/unit/test_migration_08_r2_columns.py` -> **6 passed**
- `python -m pytest -q tests/unit/test_confidence_score.py tests/unit/test_competition_score.py` -> **269 passed**
- `python -m pytest -q tests/unit/test_demand_score_extended.py tests/unit/test_recommendation_eligibility.py` -> **47 passed**
- `python -m pytest -q tests/unit/test_collection_orchestrator.py` -> **33 passed**
- `python -m pytest -q tests/integration/test_r3_pipeline.py` -> **4 passed**
- `python -m pytest -q tests/unit/test_search_url_builder.py::test_fiverr_search_url_always_includes_category_filter_for_production_niches tests/unit/test_search_url_builder.py::test_unconstrained_search_result_applies_demand_confidence_deduction tests/unit/test_scoring_db_integration.py::test_sponsored_gigs_never_included_in_competition_top10 tests/unit/test_feasibility_extended.py::test_zombie_gigs_never_used_in_feasibility_review_barrier tests/unit/test_demand_score_extended.py::test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent tests/unit/test_recommendation_eligibility.py::test_ghost_market_blocks_recommendation_absolutely tests/unit/test_demand_score_extended.py::test_trc_qualified_by_result_set_relevance_in_demand tests/unit/test_scoring_db_integration.py::test_demand_pairs_strictness_with_selected_total_result_count_row tests/unit/test_scoring_db_integration.py::test_demand_ignores_legacy_migration_default_none_strictness` -> **17 passed**
- `python -m pytest -q -k "REG or category_filter or sponsored or zombie or ghost_market or qualified_by_result_set or strictness"` -> **178 passed, 3487 deselected**
- `python run.py config-check --config-path config.yaml` -> **Config OK**

## REG-15 / REG-16 Registration

Updated `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md` Section 7:

- Added REG-15 and REG-16 entries to permanent pack
- Pack count incremented from 18 to 20
- Version history updated to `1.4`
- Existing REG numbering preserved

## Golden Parity (AC-U3)

Repository CLI currently exposes scoring through `run.py run --mode full` (no `run.py score` command).  
Executed parity using isolated DB copies from `data/cycle037_live.db`:

- OFF run:
  - `python run.py run --mode full --config-path tmp/config_stage35_off.yaml --database-url sqlite:///data/parity_off.db`
- ON run:
  - `python run.py run --mode full --config-path tmp/config_stage35_on.yaml --database-url sqlite:///data/parity_on.db`

Anchor extraction (`keyword_scores` latest row per keyword):

- OFF:
  - `kw=110`: final `62.70`, CM `1.0`, tag `CONDITIONAL_GO`
  - `kw=96`: final `35.80`, CM `0.8389`, tag `CAUTION`
  - `kw=3`: final `56.66`, CM `0.95`, tag `MONITOR`
- ON:
  - `kw=110`: final `62.70`, CM `1.0`, tag `CONDITIONAL_GO`
  - `kw=96`: final `35.80`, CM `0.8389`, tag `CAUTION`
  - `kw=3`: final `56.66`, CM `0.95`, tag `MONITOR`

Result: OFF equals legacy anchors exactly and ON keeps `kw=110` as `CONDITIONAL_GO` with zero anchor drift.

## SCRUM-605..612 Self-Review

- `SCRUM-605`: `compute_gig_relevance` returns full dataclass contract with 4-signal weighting and rejection precedence.
- `SCRUM-606`: `validate_result_set` implements denominator rules, ghost/contamination logic, tiers, and zero-card path.
- `SCRUM-607`: 9 production niches use required slug set with per-niche thresholds and DEFAULT fallback.
- `SCRUM-608`: Stage 3.5 workflow UPSERTs RSV, links `SearchResult.rsv_id`, writes per-gig flags, and fail-softs per keyword.
- `SCRUM-609`: shared RSV helper used across confidence/competition/demand; no inline calculator RSV queries.
- `SCRUM-610`: ghost hard block fires even forced, alert persisted, operator resolution surface emitted, tag demotion to `PASS`.
- `SCRUM-611`: tolerant URL matching propagates `Gig.relevance_flag`/`Gig.relevance_score`; strictness transparency persisted.
- `SCRUM-612`: validator/migration/pipeline and scoring-hook tests all green; permanent pack updated to 20 (`v1.4`).

## Constraints Confirmation

- Zero `scrapfly` config changes.
- Zero `reddit/devvit_bridge` config changes.
- Only the 3 allowed additions in `config.yaml` relevance block.
- No `--cov=src` run executed.
- No no-op commits in Agent B stack.

## Commit Ledger

- `37454b0` - `feat(analysis): add Stage 3.5 result set validator`
- `6c52163` - `feat(schema): add migration_08 RSV columns`
- `79fca20` - `feat(collection): wire Stage 3.5 validation workflow`
- `dc58c8a` - `feat(scoring): apply RSV hooks and ghost hard block`
- `474a582` - `feat(config): add Stage 3.5 relevance toggles`
- `0a9e728` - `docs(cycle-053): finalize Agent B evidence and regressions`

Final report commit SHA: `0a9e728`

## Handoff to Agent C

Use these commands for parity re-check:

- OFF: `python run.py run --mode full --config-path tmp/config_stage35_off.yaml --database-url sqlite:///data/parity_off.db`
- ON: `python run.py run --mode full --config-path tmp/config_stage35_on.yaml --database-url sqlite:///data/parity_on.db`

Verify anchors:

- `kw=110` remains `CONDITIONAL_GO` with final `>= 60` and `CM=1.0`
- OFF and ON drift for `kw=110/96/3` remains within acceptance window (observed drift `0.00`)
