# CYCLE 070 - AGENT A PLANNING REPORT

Date: 2026-06-07  
Branch: `cycle/070/integration`  
Prompt baseline SHA reference: `e880e80`  
Observed `origin/develop` HEAD at branch cut: `6eba290`  
C070 control: `SCRUM-1032` (In Progress)  
C070 story: `SCRUM-201` (In Progress, parent `SCRUM-22`)  
Baseline suite evidence: `4943 tests collected`, golden parity PASS
A report commit SHA: `a4220d8`

## Policy v4.3 Confirmation

- 55 LARGE-XXLARGE tasks minimum per agent.
- Floors: A:1000, B:1200, E:950, C:900, F:1000, D:1200 (total 6250).
- S7.6 treated as a pipeline story (DB + migration + feedback loop), not a hypothesis-only extension.

## Pre-Release and Branch State

- `develop` refreshed and branch created/pushed: `cycle/070/integration`.
- Worktree count: one active entry.
- Golden parity baseline: PASS (`kw=110 => 62.7 / 1.0 / CONDITIONAL_GO`).
- Unit collection baseline: PASS (`4943 tests collected`).
- Prompt placeholder count check: `[C070_SQUASH_SHA]` occurrences = `5` (pre-release state intact).

## S7.6 Spec Read (Mandatory)

Primary source read:

- `PM_Pack/ref/project_plan/10_discovery/DISCOVERY_ENGINE_ARCHITECTURE.md`

S7.6 interpretation carried to handoffs:

- `evaluate_discovery_results(run_id, db)` executes at cycle start.
- `build_feedback_summary(db)` returns LLM-ready evidence.
- Gold/hit/miss/retire thresholds: `85 / 60 / 40 / 30`.
- Discovery feedback is the LEARN/EVALUATE/FEEDBACK stage in the architecture loop.

## Baseline Discovery and Model Survey

- `src/discovery/feedback.py`: **missing at base** (B creates).
- `src/discovery/hypothesis.py`: present, 764 lines, all S7.2-S7.5 generators intact.
- `src/discovery/orchestrator.py`: present; public methods include `run_cycle`, `generate_hypotheses`, `score_and_filter`, `promote_keywords`, `aggregate_feedback`.
- `HypothesisMode` values: `adjacent_keyword`, `adjacent_niche`, `gap_exploit`, `trend_chase`.
- Discovery ORM exports already present in `src/models/__init__.py`: `DiscoveryOutcome`, `DiscoveryCycleLog`.
- Current `foundation_gate_ci.db` has `discovery_outcomes` and `discovery_cycle_logs` tables.

## Keywords Schema Drift (Important for B)

Observed in `foundation_gate_ci.db`:

- Present: `is_discovery`, `discovery_mode`, `hypothesis_confidence`
- Missing: `hypothesis_rationale`, `discovered_in_run`, `discovery_evaluated`, `is_retired`

S7.6 migration target remains mandatory: ensure all 7 columns exist and indexed as contract requires.

## 14-Track Review (2026-06-07)

| Track | % (C070) | Evidence |
| --- | ---: | --- |
| 01 Foundation | 93% | Branch/golden/collection checks green |
| 02 Data/models | 92% | S7.6 migration scope updates schema +2% |
| 03 Collection | 55% | TierD-2 still pending |
| 04 Scoring | 90% | Golden anchors pass |
| 05 Analysis | 78% | External signals posture verified |
| 06 LLM recs | 70% | Existing modules stable |
| 07 Dashboard | 72% | 9 pages, no demo-data refs |
| 08 Pricing | 88% | Pricing import chain intact |
| 09 Discovery | 46% | S7.1-S7.6 planning package complete |
| 10 Playbook | 8% | Wave 11 unstarted |
| 11 Dashboard UX | 10% | Wave 12 unstarted |
| 12 SRDI | 90% | 47/37/33 baseline held |
| 13 SRDI Ops | 90% | Regression guardrails remain active |
| 00 Meta/Governance | 95% | Prompt/Jira governance executed |

Weighted estimate after C070 planning baseline: ~63%.

## 5 Mandatory Gap Checks

- PASS: dashboard demo-data refs = `[]` (0).
- NOTE: toggle posture observed as `external_signals=true`, `scrapfly=false`, `llm_stage_3_5=true` in config; golden run used override with stage 3.5 disabled.
- PASS: SRDI baseline values maintained (`47/37/33` contract retained).
- PASS: niche count = `9` and IDs match expected list.
- PASS: dashboard page count = `9`.

## S7.6 vs S7.2-S7.5 (Hard Distinction)

| Aspect | S7.2-S7.5 | S7.6 |
| --- | --- | --- |
| New DB tables | None | `discovery_outcomes`, `discovery_cycle_logs` |
| Migration | None | Required (migration_14 or next) |
| DB writes | None (pure generation) | Required (evaluation + cycle logs) |
| Module shape | `hypothesis.py` additions | New `feedback.py` module |
| Keywords impact | None | 7 discovery feedback columns |
| Purpose | Generate hypotheses | Evaluate outcomes + feedback loop |

## B Contract (Implementation Handoff)

Files and zone:

- CREATE: `src/discovery/feedback.py`
- MODIFY: model definitions to align S7.6 fields/types
- CREATE: `src/migrations/migration_14_s76_discovery_feedback.py` (or next available number)
- CREATE: `tests/unit/test_discovery_feedback.py` (>=30 tests)
- Commit zone: `src/` + `src/migrations/` + `tests/` + B handoff doc only

Function contract:

- `evaluate_discovery_results(run_id: str, db) -> dict`
- `build_feedback_summary(db) -> dict`
- `_generate_pattern_notes(outcomes: list, mode_stats: dict) -> str`
- `get_discovery_cycle_stats(run_id: str, db) -> dict`

Threshold contract:

- GOLD: `score >= 85` (implies hit, alert)
- HIT: `score >= 60`
- MISS: `score < 40`
- MONITOR: `40 <= score < 60`
- AUTO-RETIRE: `score < 30`

Idempotency contract:

- Use `discovery_evaluated` guard before processing.
- No duplicate `DiscoveryOutcome` rows on re-run.
- No duplicate gold alerts on re-run.

Migration steps contract (verbatim target):

1. Create `discovery_outcomes` with FK `keyword_id -> keywords.id`.
2. Create `discovery_cycle_logs` with run id support.
3. Add `is_discovery` (BOOLEAN default false).
4. Add `discovery_mode` (VARCHAR nullable).
5. Add `hypothesis_confidence` (FLOAT nullable).
6. Add `hypothesis_rationale` (TEXT nullable).
7. Add `discovered_in_run` (VARCHAR nullable).
8. Add `discovery_evaluated` (BOOLEAN default false).
9. Add `is_retired` (BOOLEAN default false).
10. Add indexes on `is_discovery`, `discovery_evaluated`, `is_retired`.

Alert import fallback contract:

- Try `from src.monitoring.monitors import create_alert`
- Fallback `from src.alerts import create_alert`
- If unavailable, log warning and skip alert without crashing.

## C / E / F / D Handoff Index

- `docs/cycle_reports/CYCLE_070_AGENT_B_HANDOFF.md`
- `docs/cycle_reports/CYCLE_070_AGENT_E_HANDOFF.md`
- `docs/cycle_reports/CYCLE_070_AGENT_C_HANDOFF.md`
- `docs/cycle_reports/CYCLE_070_AGENT_F_HANDOFF.md`
- `docs/cycle_reports/CYCLE_070_AGENT_D_HANDOFF.md`

## Jira Actions Completed

- `SCRUM-1032`: transitioned to In Progress; C070 planning comment posted.
- `SCRUM-201`: transitioned to In Progress; S7.6 differentiation comment posted.
- `SCRUM-22`: remains In Progress; Wave 10 progress comment posted.

## Regression Pack v2.5 (44 Names, Verbatim)

REG-01: test_ghost_market_excluded_from_go_tag REG-02: test_conditional_go_threshold_boundary REG-03: test_no_go_below_caution_threshold REG-04: test_demand_score_keyword_only_depth REG-05: test_competition_score_uses_search_result_count REG-06: test_feasibility_score_zero_review_seller_eligible REG-07: test_profitability_score_package_data_required REG-08: test_confidence_score_freshness_decay REG-09: test_trc_reliability_single_multiplier_no_stack REG-10: test_null_means_include_backward_compat REG-11: test_ghost_market_hard_block_only REG-12: test_trends_qualifier_threshold_0_65 REG-13: test_rsv_live_band_threshold REG-14: test_rsv_seed_fallback_behavior REG-15: test_result_set_validator_min_gigs REG-16: test_sponsored_filter_removes_promoted REG-17: test_zombie_filter_removes_stale REG-18: test_llm_relevance_disabled_passes_all REG-19: test_llm_relevance_flags_below_threshold REG-20: test_external_signal_integrity_check REG-21: test_scoring_profile_weights_sum_to_one REG-22: test_final_score_bounded_0_100 REG-23: test_golden_anchor_kw110_62_7 REG-24: test_golden_anchor_kw96_35_8 REG-25: test_golden_anchor_kw3_56_66 REG-26: test_discovery_core_loop_budget_gate REG-27: test_discovery_hypothesis_confidence_threshold REG-28: test_alert_new_strong_go_triggered REG-29: test_alert_stale_data_warning REG-30: test_export_csv_includes_score_components REG-31: test_export_excel_valid_workbook REG-32: test_cli_config_check_passes REG-33: test_cli_seed_niches_idempotent REG-34: test_dry_run_sentinel_prevents_live_writes REG-35: test_negation_exclusion_removes_off_topic REG-36: test_emerging_bonus_applied_correctly REG-37: test_ghost_filter_handles_null_ghost_market_score REG-38: test_llm_alert_counts_actual_llm_calls REG-39: test_monitors_health_check_returns_status REG-40: test_quality_gate_blocks_low_coverage REG-41: test_external_signal_raw_value_stored_and_retrieved REG-42: test_collection_url_encodes_spaces_correctly REG-43: test_collection_url_never_bare_path REG-44: test_dashboard_opportunities_renders_empty_db_gracefully

## Final Authorization Statement

CYCLE 070 PROMPTS AUTHORIZED FOR RELEASE. Policy v4.3: 55 LARGE-XXLARGE tasks, floors A:1000/B:1200/E:950/C:900/F:1000/D:1200. All 14 tracks reviewed (2026-06-07). 5 gap checks executed. Jira clean. SCRUM-1032 In Progress. SCRUM-201 In Progress. SCRUM-22 In Progress. Base reference in prompt: e880e80; observed develop head at execution: 6eba290. Suite baseline: 4943 tests collected; golden parity PASS. S7.6 Discovery Scoring and Feedback: NEW FILE: src/discovery/feedback.py. NEW/MODIFIED MODELS: DiscoveryOutcome + DiscoveryCycleLog + keyword feedback fields. NEW MIGRATION: keywords +7 columns + discovery feedback table alignment. evaluate_discovery_results(): idempotent, gold>=85, hit>=60, miss<40, retire<30. build_feedback_summary(): per-mode stats, LLM-ready context, graceful empty return. DIFFERS FROM S7.2-S7.5: DB writes, migration, and feedback module (not hypothesis.py additions). G-B NOTE: must be re-verified post-merge due schema migration scope. TierD-1: 12 stashes pending. TierD-2: ScrapFly SEED x13 pending.
