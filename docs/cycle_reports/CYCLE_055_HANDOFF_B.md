# HANDOFF_B — Cycle 055 R6 implementation

Branch HEAD: `e65b9f9` (pre-commit snapshot)

Toggle:
- `discovery.enable_relevance_gates = false`
- `config.yaml` path: `discovery.enable_relevance_gates`
- model field: `src/config/models.py::DiscoveryConfig.enable_relevance_gates`

New module:
- `src/analysis/pre_validator.py` (`DiscoveryPreValidator`)
- Reused R2 imports exactly:
  - `src.analysis.result_set_validator.NICHE_VALIDATION_CONFIG`
  - `src.analysis.result_set_validator.compute_gig_relevance`
  - `src.analysis.result_set_validator.validate_result_set`

## Gate wiring (file::function, toggle guard, tests)

- G1 prompt hardening: `src/discovery/hypothesis.py::generate_niche_hypotheses`
  - Guard: `enable_relevance_gates` keyword argument; toggle OFF path preserves legacy prompt bytes.
  - Coverage: `tests/unit/test_discovery.py` + gated behavior exercised in new gate tests.
- G1 specificity filter: `src/discovery/hypothesis.py::_gate_hypotheses`
  - Guard: called only when `enable_relevance_gates` is true.
  - Coverage: `test_low_specificity_hypothesis_rejected` (REG-27) + Gate-1 edge tests.
- G2 dry-run pre-validator: `src/analysis/pre_validator.py::DiscoveryPreValidator.evaluate`
  - Reuses R2 validation APIs, no collection side effects.
  - Coverage: `test_pre_validator_maps_valid_ghost_and_contaminated`.
- G2 validated-only insert: `src/discovery/orchestrator.py::DiscoveryOrchestrator.run_cycle`
  - Guard: `if gates_enabled` branch inserts only `DiscoveryVerdict.VALID`.
  - Coverage: gate2 valid/ghost/contaminated insert tests.
- G3 invalid outcome recording: `src/discovery/orchestrator.py::_record_outcome`
  - Guard: invalid path only under `gates_enabled` pre-validation failure.
  - Coverage: `test_ghost_discovery_recorded_as_invalid_not_miss` (REG-25).
- G4 feedback exclusion: `src/discovery/orchestrator.py::aggregate_feedback`
  - Guard: when enabled, query excludes `is_invalid` and `is_contaminated`.
  - Coverage: `test_feedback_excludes_contaminated_outcomes` (REG-26).

## Column population

- DiscoveryOutcome columns populated in Gate-3 write path:
  - `is_invalid`
  - `is_contaminated`
  - `relevance_score`
  - `contamination_reason`
- Keyword discovery columns populated at insert:
  - `ghost_market_flag`
  - `discovery_needs_recollection`
  - `last_relevance_validated_at`

INVALID vs MISS semantics used in code:
- INVALID: `DISCOVERY_STATUS_INVALID` -> `is_invalid=True`
- MISS: `DISCOVERY_STATUS_MISS` -> `is_invalid=False`

Migration added: **No** (existing R8 columns populated).

## Verification evidence (raw command outcomes)

`py -3.12 -m ruff check .`
- `All checks passed!`

`py -3.12 -m mypy src`
- `Success: no issues found in 222 source files`

`py -3.12 -m pytest -q --cov=src --cov-fail-under=90`
- `3816 passed in 446.25s (0:07:26)`
- `Required test coverage of 90% reached. Total coverage: 95.79%`

`py -3.12 run.py config-check`
- `Config OK: niches=9, active_profile=aggressive_new_seller, profiles=[aggressive_new_seller, default, profitability_focus, trend_chaser]`

`py -3.12 run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci.db`
- `[PASS] config_load: Loaded config.yaml`
- `[PASS] database_registry: created=49, registered=38, source_required=30, source_missing=0`
- `[PASS] smoke_imports: Imported 5 key modules.`
- `[PASS] repo_hygiene: No hygiene issues detected.`

`py -3.12 run.py phase2-smoke`
- `Phase2 smoke OK: collection package`
- `Phase2 smoke OK: analysis package`
- `Phase2 smoke OK: phase2 config models`

Golden OFF parity:
- Command: `py -3.12 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override discovery.enable_relevance_gates=false`
- `status: PASS`
- Anchor rows:
  - `110`: `final_score=62.7`, `confidence_modifier=1.0`, `tag=CONDITIONAL_GO`
  - `96`: `final_score=35.8`, `confidence_modifier=0.8389`, `tag=CAUTION`
  - `3`: `final_score=56.66`, `confidence_modifier=0.95`, `tag=MONITOR`

Golden ON sanity:
- Command: `py -3.12 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override discovery.enable_relevance_gates=true`
- `status: PASS`
- Current scorer harness reports the same anchor values under this helper path.

Rejection-rate evidence (toggle ON, Appendix-D style contamination fixture):
- `REJECTION_RATE 3/10=0.30`
- Band check: `0.30` is within target `0.20-0.40`.

Regression pack evidence:
- Full suite command above passed (`3816 passed`) including the permanent regression set.
- Explicit R6 run:
  - `py -3.12 -m pytest -q -k "ghost_discovery_recorded_as_invalid_not_miss or feedback_excludes_contaminated_outcomes or low_specificity_hypothesis_rejected"`
  - Output: `3 passed, 3813 deselected in 3.70s`

## Changed file set

- `config.yaml`
- `src/config/models.py`
- `src/analysis/pre_validator.py`
- `src/discovery/hypothesis.py`
- `src/discovery/orchestrator.py`
- `src/models/discovery_outcome.py`
- `src/models/market.py`
- `src/models/__init__.py`
- `tests/unit/test_discovery_relevance_gates.py`
- `tests/integration/test_discovery_relevance_gates_integration.py`

PM_Pack touched by this implementation: **No** (pre-existing PM_Pack local edits remain unstaged/uncommitted).
