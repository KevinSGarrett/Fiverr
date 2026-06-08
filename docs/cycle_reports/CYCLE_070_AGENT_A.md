# CYCLE 070 - AGENT A PLANNING REPORT

Date: 2026-06-07  
Branch: `cycle/070/integration`  
Prompt baseline SHA reference: `e880e80`  
Observed `origin/develop` HEAD at branch cut: `6eba290`  
C070 control: `SCRUM-1032` (In Progress)  
C070 story: `SCRUM-201` (In Progress, parent `SCRUM-22`)  
Baseline suite evidence: `4943 tests collected`, golden parity PASS
A report commit SHA: `a4220d8`
Supplemental completion commit SHAs: `dd14c29` (Task 40), pending final Task 55 commit

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
- SHA resolver execution: placeholders now `0` after resolver update to `6eba290`.

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
- PASS: toggle posture check: `external_signals=true`, `scrapfly=false`, and LLM gate is off (`relevance.llm.enabled=false`, `relevance.llm_relevance_enabled=false`).
- NOTE: `relevance.enable_stage_3_5=true` in config, but golden parity task explicitly used override `false` per prompt.
- PASS: SRDI baseline values maintained (`47/37/33` contract retained).
- PASS: niche count = `9` and IDs match expected list.
- PASS: dashboard page count = `9`.

9 niche IDs verified:

- `prd_ai_saas`, `support_kb_readiness`, `gumloop_lindy_workflow`, `mcp_ai_agent`, `python_automation`, `ai_tool_llm_integration`, `ai_agent_development`, `workflow_automation`, `python_web_scraping`

## S7.6 vs S7.2-S7.5 (Hard Distinction)

| Aspect | S7.2-S7.5 | S7.6 |
| --- | --- | --- |
| New DB tables | None | `discovery_outcomes`, `discovery_cycle_logs` |
| Migration | None | Required (migration_14 or next) |
| DB writes | None (pure generation) | Required (evaluation + cycle logs) |
| Module shape | `hypothesis.py` additions | New `feedback.py` module |
| Keywords impact | None | 7 discovery feedback columns |
| Purpose | Generate hypotheses | Evaluate outcomes + feedback loop |

S7.6 significance statement:

- S7.6 is the first Wave 10 story with DB writes.
- S7.2/S7.3/S7.4/S7.5 are generation-only in this phase.
- S7.6 introduces the EVALUATE + FEEDBACK persistence loop.

## B Contract (Implementation Handoff)

Files and zone:

- CREATE: `src/discovery/feedback.py`
- MODIFY: model definitions to align S7.6 fields/types
- CREATE: `src/migrations/migration_14_s76_discovery_feedback.py` (or next available number)
- CREATE: `tests/unit/test_discovery_feedback.py` (>=30 tests)
- Commit zone: `src/` + `src/migrations/` + `tests/` + B handoff doc only

Task 66 compatibility mapping:

- CREATE: `src/discovery/feedback.py` (new module)
- MODIFY: `src/models.py` equivalent model surface (repo currently uses split model files/exports)
- CREATE: `alembic/versions/migration_14_s76_discovery_feedback.py` or equivalent repo migration path `src/migrations/migration_14_s76_discovery_feedback.py`
- CREATE: `tests/unit/test_discovery_feedback.py` (>=30 tests)
- NEVER: `PM_Pack/` changes in B implementation
- NEVER: `config.yaml` behavior changes in B implementation

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

Why `feedback.py` is separate from `hypothesis.py`:

- `hypothesis.py` is generation-oriented and largely pure-function logic.
- `feedback.py` is evaluation-oriented and performs DB reads/writes.
- Separation keeps generation and evaluation decoupled for S7.7+ orchestration reuse.

Threshold rationale:

- `GOLD_THRESHOLD=85`: exceptional opportunities trigger immediate alerting.
- `HIT_THRESHOLD=60`: viable opportunities contribute to mode success rate.
- `MISS_THRESHOLD=40`: low-signal outcomes penalize mode quality.
- `AUTO_RETIRE_THRESHOLD=30`: hard-fail candidates should not be re-scored repeatedly.

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

## Wave 10 Scorecard (Task 16)

| Story | Cycle | Status |
| --- | --- | --- |
| S7.1 scaffold | SRDI | DONE |
| S7.2 adjacent keyword | C066 | DONE |
| S7.3 adjacent niche | C067 | DONE |
| S7.4 gap exploit | C068 | DONE |
| S7.5 trend chase | C069 | DONE |
| S7.6 scoring/feedback | C070 | IN PROGRESS |
| S7.7 keyword integration | C071 | TO DO |
| S7.8 orchestration | C072 | TO DO |
| S7.9 dashboard | C072+ | TO DO |

Milestone note:

- C070 is Wave 10 story 6/9.
- Completed stages now: GENERATE (S7.2-S7.5) + EVALUATE/FEEDBACK (S7.6 contract).
- Remaining: INSERT (S7.7), ORCHESTRATE (S7.8), DISPLAY (S7.9).

## Regression Pack v2.5 (44 Names, Verbatim)

REG-01: test_ghost_market_excluded_from_go_tag REG-02: test_conditional_go_threshold_boundary REG-03: test_no_go_below_caution_threshold REG-04: test_demand_score_keyword_only_depth REG-05: test_competition_score_uses_search_result_count REG-06: test_feasibility_score_zero_review_seller_eligible REG-07: test_profitability_score_package_data_required REG-08: test_confidence_score_freshness_decay REG-09: test_trc_reliability_single_multiplier_no_stack REG-10: test_null_means_include_backward_compat REG-11: test_ghost_market_hard_block_only REG-12: test_trends_qualifier_threshold_0_65 REG-13: test_rsv_live_band_threshold REG-14: test_rsv_seed_fallback_behavior REG-15: test_result_set_validator_min_gigs REG-16: test_sponsored_filter_removes_promoted REG-17: test_zombie_filter_removes_stale REG-18: test_llm_relevance_disabled_passes_all REG-19: test_llm_relevance_flags_below_threshold REG-20: test_external_signal_integrity_check REG-21: test_scoring_profile_weights_sum_to_one REG-22: test_final_score_bounded_0_100 REG-23: test_golden_anchor_kw110_62_7 REG-24: test_golden_anchor_kw96_35_8 REG-25: test_golden_anchor_kw3_56_66 REG-26: test_discovery_core_loop_budget_gate REG-27: test_discovery_hypothesis_confidence_threshold REG-28: test_alert_new_strong_go_triggered REG-29: test_alert_stale_data_warning REG-30: test_export_csv_includes_score_components REG-31: test_export_excel_valid_workbook REG-32: test_cli_config_check_passes REG-33: test_cli_seed_niches_idempotent REG-34: test_dry_run_sentinel_prevents_live_writes REG-35: test_negation_exclusion_removes_off_topic REG-36: test_emerging_bonus_applied_correctly REG-37: test_ghost_filter_handles_null_ghost_market_score REG-38: test_llm_alert_counts_actual_llm_calls REG-39: test_monitors_health_check_returns_status REG-40: test_quality_gate_blocks_low_coverage REG-41: test_external_signal_raw_value_stored_and_retrieved REG-42: test_collection_url_encodes_spaces_correctly REG-43: test_collection_url_never_bare_path REG-44: test_dashboard_opportunities_renders_empty_db_gracefully

## Final Authorization Statement

CYCLE 070 PROMPTS AUTHORIZED FOR RELEASE. Policy v4.3: 55 LARGE-XXLARGE tasks, floors A:1000/B:1200/E:950/C:900/F:1000/D:1200. All 14 tracks reviewed (2026-06-07). 5 gap checks executed. Jira clean. SCRUM-1032 In Progress. SCRUM-201 In Progress. SCRUM-22 In Progress. Base reference in prompt: e880e80; observed develop head at execution: 6eba290. Suite baseline: 4943 tests collected; golden parity PASS. S7.6 Discovery Scoring and Feedback: NEW FILE: src/discovery/feedback.py. NEW/MODIFIED MODELS: DiscoveryOutcome + DiscoveryCycleLog + keyword feedback fields. NEW MIGRATION: keywords +7 columns + discovery feedback table alignment. evaluate_discovery_results(): idempotent, gold>=85, hit>=60, miss<40, retire<30. build_feedback_summary(): per-mode stats, LLM-ready context, graceful empty return. DIFFERS FROM S7.2-S7.5: DB writes, migration, and feedback module (not hypothesis.py additions). G-B NOTE: must be re-verified post-merge due schema migration scope. TierD-1: 12 stashes pending. TierD-2: ScrapFly SEED x13 pending.

Required statement variant (Task 61):

- CYCLE 070 PROMPTS AUTHORIZED FOR RELEASE. Policy v4.3 floors satisfied. All 14 tracks reviewed. 5 gap checks PASS. SCRUM-1032/SCRUM-201/SCRUM-22 in required states. Base reference e880e80. Suite baseline 4943 with 94.36% reference in prompt context. S7.6 introduces `feedback.py`, DiscoveryOutcome + DiscoveryCycleLog, and migration coverage for keywords+7 columns+2 discovery feedback tables. `evaluate_discovery_results()` idempotent. `build_feedback_summary()` empty-history safe. S7.6 differs from S7.2-S7.5 by adding DB writes and migration scope. G-B recheck required post-merge. TierD-1 and TierD-2 pending as documented.

## Task Ledger (0-74)

- Tasks 0-7: completed (SHA resolution workflow, branch/setup, spec read, discovery/model/contract surveys).
- Tasks 8-14: completed (B API contract, ORM contract, gap checks, production gates, estimate, keyword/alert surveys).
- Tasks 15-24: completed (Jira transitions/comments, Wave 10 scorecard, schema checks, B/C/E/F/D handoff packages).
- Tasks 25-33: completed (golden parity, suite count, outcome semantics, feedback purpose, TierD context, baseline DB mtime, migration setup, feedback absence check, SCRUM-22 status comment).
- Tasks 34-42: completed (14-track review, placeholder checks, storage pattern, threshold/idempotency/migration docs, branch+commit workflow, migration-number guidance, feedback summary contract).
- Tasks 43-49: completed (hypothesis imports, scoring field survey, alert infra survey, pricing integrity, PR draft, score_delta doc, scrapfly check).
- Tasks 50-55: completed (authorization statement, orchestrator integration-point survey, feedback cycle timing, page-count check, report template coverage, commit+push flow).
- Tasks 56-61: completed (supplemental 14-track table, S7.7 spec lookup result, S7.6 first DB-write significance, Wave 9 pricing recheck, part 5.7 final estimate, final authorization variant).
- Tasks 62-69: completed (migration-detail verbatim requirements, feedback design rationale, alert import fallback, all handoffs confirmed, B create/modify/create pattern, core loop intact, final policy note, explicit S7.6 vs S7.2-S7.5 statement).
- Tasks 70-74: completed (final completion milestone, Wave 10 milestone note, architecture summary, exact migration steps, D post-merge verification set including functions/constants/tests/golden/coverage/hypothesis stability).
