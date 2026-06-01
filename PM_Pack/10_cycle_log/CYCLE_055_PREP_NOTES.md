# CYCLE 055 PREP NOTES — SRDI R6 Discovery Engine Relevance Gates

## 1) Preflight + Branch Anchor

- Repo root confirmed: `C:\Fiverr\Fiverr`
- R4 merge on `origin/develop` confirmed: `acff870 feat(scoring): R4 quality-aware scoring toggles + integrity fields (#63)`
- Develop preflight checks: PASS
  - `py -3.12 -m ruff check .`
  - `py -3.12 -m mypy src`
  - `py -3.12 run.py config-check`
- Base develop SHA (parity anchor): `acff870e8ef32d8e92bc2ebad4ff14e0675fdbc7`
- Integration branch: `cycle/055/integration` (pushed, upstream set)

## 2) Jira Scaffold

- Parent epic (R6 discovery epic): `SCRUM-22` (`Epic 07: Discovery Engine`)
- Cycle control task: `SCRUM-1009` (`Cycle 055: SRDI R6 Discovery Engine Relevance Gates (6-Agent)`)

### R6 story status capture (pre-cycle)

- `SCRUM-626` — To Do
- `SCRUM-864` — To Do
- `SCRUM-627` — To Do
- `SCRUM-868` — To Do
- `SCRUM-628` — To Do
- `SCRUM-873` — To Do
- `SCRUM-877` — To Do
- `SCRUM-629` — To Do

Kickoff comment posted to all 8 stories:

`Cycle 055 active — R6 Discovery Engine Relevance Gates; implementation by Agent B; toggle ships OFF; discovery activation deferred to Tier-1 gate.`

No story was transitioned to Done.

## 3) Config/Module Contract (Agent B copy-paste source of truth)

### Toggle contract

- Required R6 toggle key: `discovery.enable_relevance_gates`
- Required default: `false`
- Exact YAML path: `config.yaml -> discovery.enable_relevance_gates`
- Model location (target): `src/config/models.py` -> `DiscoveryConfig.enable_relevance_gates: bool = False`

Observed current state:

- `config.yaml` has `discovery:` block, but no `enable_relevance_gates` key yet.
- `src/config/models.py` has `DiscoveryConfig`, but no `enable_relevance_gates` field yet.

Cycle config gate statement:

- Only this one new toggle is relaxed for this cycle.
- `collection.scrapfly.enabled` remains `false` in committed `config.yaml`.
- No other committed config key changes are authorized.

### New module + reuse contract

- New module path for Cycle 055 implementation: `src/analysis/pre_validator.py`
- New class: `DiscoveryPreValidator`
- Reuse contract (must not reimplement relevance):
  - `src/analysis/result_set_validator.py::validate_result_set`
  - `src/analysis/result_set_validator.py::compute_gig_relevance`
  - `src/analysis/result_set_validator.py::NICHE_VALIDATION_CONFIG`
  - import path to use:
    - `from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG, compute_gig_relevance, validate_result_set`

Path discrepancy to resolve in implementation notes:

- SRDI reference docs also still mention `src/discovery/pre_validator.py`.
- Cycle 055 prompt contract is authoritative for this cycle; implementer must keep imports/call sites consistent with final chosen path and avoid duplicate modules.

## 4) Schema Columns R6 Must Populate (R8 baseline check)

### DiscoveryOutcome extension touchpoints

- Migration file: `src/migrations/srdi_r8/migration_06_discovery_outcomes_srdi_columns.py`
- Present in migration:
  - `is_invalid`
  - `is_contaminated`
  - `relevance_score`
  - `contamination_reason`

Spec mismatch to flag to Agent B:

- SRDI schema spec (`05_DATA_SCHEMA_MIGRATION.md`) expects:
  - `invalid_reason` (not `contamination_reason`)
  - `pre_validation_passed` (missing)
- ORM model class for `discovery_outcomes` is not currently present in `src/models/` and must be accounted for in B's implementation plan.

### Keyword discovery columns

- Migration file: `src/migrations/srdi_r8/migration_05_keywords_srdi_columns.py`
- Present in migration:
  - `ghost_market_flag`
  - `discovery_needs_recollection`
  - `last_relevance_validated_at`

Spec mismatch to flag to Agent B:

- SRDI schema spec expects `pre_validation_data` and `specificity_confidence` columns for keywords; these are not present in `migration_05`.
- ORM model `src/models/market.py::Keyword` currently has `is_discovery`, `discovery_mode`, and `hypothesis_confidence`; it does not yet map `discovery_needs_recollection`, `ghost_market_flag`, `last_relevance_validated_at`, `pre_validation_data`, or `specificity_confidence`.

### ResultSetValidation relationship (R2/R8 reuse context)

- Model file: `src/models/result_set_validation.py`
- Core fields used by R6 pre-validation reuse:
  - `result_set_relevance_score`
  - `ghost_market_flag`
  - `category_contamination_flag`
  - `used_fallback_strictness`

## 5) Discovery Entrypoint File Paths (Gate Attach Map)

- Gate 1 (hypothesis generation): `src/discovery/hypothesis.py` (`generate_niche_hypotheses`)
- Gate 2 (orchestration / insert decision): `src/discovery/orchestrator.py` (`promote_keywords`, `run_cycle`)
- Gate 3 (outcome recording): `src/discovery/orchestrator.py` (`run_cycle` outcome-persistence branch for discovery outcomes)
- Gate 4 (feedback/learning aggregation): `src/discovery/orchestrator.py` (`run_cycle` feedback aggregation branch)
- SRDI reference delta recorded: planning docs mention `src/discovery/feedback.py`, but current repository discovery package entrypoint is `src/discovery/orchestrator.py`.

## 6) Permanent Regression Pack (26 names, verbatim)

Carried from prior cycles (23):

- `test_extract_price_text_from_payload_uses_nested_price_amount`
- `test_parse_gig_detail_from_html_keeps_zero_review_count`
- `test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration`
- `test_seller_profile_fetcher_maps_parser_fields_for_persistence`
- `test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields`
- `test_seller_profile_live_markup_drift_regression_spec`
- `test_scoring_fallback_queries_scope_to_active_run_id`
- `test_scoring_fallback_queries_recover_when_latest_run_unlinked`
- `test_demand_uses_search_result_total_result_count_when_available`
- `test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch`
- `test_scoring_uses_card_urls_with_querystrings_for_sparse_links`
- `test_confidence_modifier_uses_current_run_context_not_none`
- `test_weakness_multi_row_fallback_does_not_produce_extreme_value`
- `test_fiverr_search_url_always_includes_category_filter_for_production_niches (REG-13)`
- `test_unconstrained_search_result_applies_demand_confidence_deduction (REG-14)`
- `test_eligibility_ghost_hard_block_even_when_forced (REG-15)`
- `test_demand_qualified_trc_when_rsv_below_080 (REG-16)`
- `test_sponsored_gigs_never_included_in_competition_top10 (REG-17)`
- `test_zombie_gigs_never_used_in_feasibility_review_barrier (REG-18)`
- `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent (REG-19)`
- `test_niche_profile_excludes_contaminated_keywords (REG-20)`
- `test_opportunity_qualified_by_relevance (REG-21)`
- `test_price_outlier_excluded_from_competition_and_profitability (REG-22)`

NEW this cycle (R6):

- `test_ghost_discovery_recorded_as_invalid_not_miss (REG-25)`
- `test_feedback_excludes_contaminated_outcomes (REG-26)`
- `test_low_specificity_hypothesis_rejected (REG-27)`

Plus two demand guards to keep green:

- `test_demand_pairs_strictness_with_selected_total_result_count_row`
- `test_demand_ignores_legacy_migration_default_none_strictness`

## 7) Prompt Sizing Gate (Cycle 055)

| Agent | Floor | Lines | Tasks | OK? |
|-------|-------|-------|-------|-----|
| A     | 810   | 817   | 55    | y   |
| B     | 945   | 946   | 110   | y   |
| E     | 810   | 813   | 55    | y   |
| C     | 675   | 677   | 82    | y   |
| F     | 810   | 811   | 81    | y   |
| D     | 945   | 947   | 80    | y   |
| TOTAL | 4995  | 5011  |       | y   |

## 8) Final governance outcome (Agent D)

- Governance run date: `2026-06-01`
- PR: `#64` (`cycle/055/integration -> develop`)
- Gating SHA: `96576228f411671fd0463b1ab19aaeccc59fd84e`
- Decision: **BLOCK (not merged)**

Blocking gates:

- `G7` migration footprint: `DiscoveryOutcome` now persists `run_id/niche_id/keyword_text`, but existing `discovery_outcomes` migration/base table does not contain these columns on migrated DBs.
- `G9` Codex: unresolved review thread present at pre-merge check #2 (0 unresolved required).

Actions explicitly not taken because of BLOCK:

- No squash merge to `develop`
- No Jira story/control-task Done transitions
- No branch deletion
- No R6 DONE tracker/registry closeout updates

Handback:

- Agent B fix list issued in `docs/cycle_reports/CYCLE_055_AGENT_D.md` (D-1, D-2).
- Re-gate required on next pushed SHA after B resolves migration gap + Codex thread.
