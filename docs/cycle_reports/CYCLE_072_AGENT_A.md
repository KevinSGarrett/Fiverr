# CYCLE 072 - AGENT A PLANNING REPORT

Date: 2026-06-08  
Branch: `cycle/072/integration`  
Cycle control: `SCRUM-1034`  
Story: `SCRUM-203`  
Baseline reference: `2b4e320` (C071 squash on develop history)

## Governance and Policy

- Policy v4.3 posture upheld for Agent A planning/governance deliverables.
- Zone discipline upheld for Agent A artifacts: `PM_Pack/` + `docs/` only.
- S7.8 is treated as orchestration-only: no migration and no orchestrator class edits.

## Branch and Baseline Evidence

- Branch created and pushed: `cycle/072/integration`.
- Local worktree count: one worktree.
- `2b4e320` is present in current history near top and is the C071 squash commit.
- Discovery module baseline aligns with C071 output:
  - `src/discovery/hypothesis.py`: 764 lines
  - `src/discovery/feedback.py`: 265 lines
  - `src/discovery/integration.py`: 226 lines
  - `src/discovery/orchestrator.py`: 300 lines
  - `src/discovery/stage16.py`: absent at cycle start
- `tests/unit/test_discovery_stage16.py`: absent at cycle start.

## Jira Actions Completed

- `SCRUM-1034` transitioned to **In Progress**.
- `SCRUM-1034` received cycle kickoff comment with S7.8 scope and no-migration/no-LLM statement.
- `SCRUM-203` transitioned to **In Progress**.
- `SCRUM-22` remains **In Progress** and received Wave 10 progress update comment.

## Production Readiness Gates

G-A: CLOSED | G-B: CLOSED | G-C: CLOSED | G-D: OPEN (S7.8-S7.9 and Waves 11-12 pending).  
G-B note: C072 S7.8 uses existing C070 migration_14 tables/columns and adds no schema change.

## S7.8 Scope Confirmation

S7.8 = Stage 16 Orchestration. The implementation handoff requires:

- New file target: `src/discovery/stage16.py`
- New function: `run_discovery_cycle(db, run_id, config=None) -> DiscoveryCycleLog`
- New helper: `_select_modes(config, run_number=None) -> list[str]`
- New tests target: `tests/unit/test_discovery_stage16.py` with >=30 tests
- CLI wiring in `run.py` to execute discovery orchestration mode

Important guardrail:

- Do not modify `DiscoveryOrchestrator` class behavior in `src/discovery/orchestrator.py`.
- Existing documented stubs in orchestrator remain:
  - `generate_hypotheses`
  - `score_and_filter`
  - `promote_keywords`

## Baseline Technical Verification Results

### S7.2-S7.7 chain importability

- PASS: hypothesis generation functions import correctly.
- PASS: feedback functions import correctly.
- PASS: integration functions import correctly.
- PASS: models `DiscoveryCycleLog` and `DiscoveryOutcome` import correctly.
- PASS: hypothesis mode enum values:
  - `adjacent_keyword`
  - `adjacent_niche`
  - `gap_exploit`
  - `trend_chase`

### DiscoveryCycleLog schema readiness

- PASS: required columns present:
  - `run_id`
  - `modes_run`
  - `hypotheses_generated`
  - `hypotheses_gated`
  - `hypotheses_accepted`
  - `total_cost_usd`
  - `feedback_summary`
  - `cycle_at`
- PASS: model instantiation with S7.8 payload shape works.
- PASS: `discovery_cycle_logs` table exists in gate DB.
- PASS: `discovery_outcomes` table exists in gate DB.
- PASS: keywords table includes `is_discovery`, `discovery_mode`, `discovered_in_run`, `discovery_evaluated`.

Conclusion: no migration is required for S7.8.

### Stage16 baseline checks

- PASS: `src/discovery/stage16.py` absent at C072 start (to be created by B).
- PASS: `tests/unit/test_discovery_stage16.py` absent at C072 start (to be created by B/F).
- PASS: `src/discovery/integration.py` remains 226 lines at baseline.
- PASS: `src/discovery/orchestrator.py` remains 300 lines at baseline.

### Discovery ecosystem checks

- PASS: `ADJACENT_NICHE_RELATIONSHIPS` count = 9.
- PASS: `NICHE_VALIDATION_CONFIG` count = 9 and IDs match expected list.
- PASS: discovery cycle logs table has 0 records in seed baseline DB state.
- PASS: DB table count unchanged for this cycle baseline (54 tables).
- PASS: `src/discovery/candidates.py` exists and is not required for S7.8 orchestration wiring.
- PASS: wave 9 pricing imports still succeed.

### .env inventory check

- PASS: 19 configured keys detected.
- Key presence confirmed without exposing values.

### Baseline DB integrity

- PASS: `data/cycle037_live.db` mtime remains `1780553758` (unchanged baseline sentinel).

## 5 Gap Checks

1. Demo data builders in dashboard pages: `[]` (PASS)
2. Config toggles: external signals `true`, llm relevance `false`, scrapfly `false` (PASS)
3. SRDI posture continuity: confirmed as carry-forward requirement (PASS)
4. Niche count: `9` (PASS)
5. Dashboard page count: `9` (PASS)

## Golden and Suite Baseline

- Golden parity command PASS:
  - `kw=110 -> 62.7 / 1.0 / CONDITIONAL_GO`
  - `kw=96 -> 35.8 / 0.8389 / CAUTION`
  - `kw=3 -> 56.66 / 0.95 / MONITOR`
- Unit collection baseline: `5140 tests collected`.
- Existing S7.7 suite anchor: `tests/unit/test_discovery_integration.py` contains 90 tests.

## CLI Framework Survey (`run.py`)

- CLI framework: Click-based command group.
- Existing command set includes scoring/export/dashboard and other commands.
- No existing `discover` command token found in `run.py`.
- S7.8 CLI wiring is a required B change.

## B Handoff (Implementation Contract)

### File and symbols

- Create `src/discovery/stage16.py`.
- Implement:
  - `run_discovery_cycle(db, run_id, config=None) -> DiscoveryCycleLog`
  - `_select_modes(config=None, run_number=None) -> list[str]`

### `_select_modes` required behavior

- Default always-on modes:
  - `adjacent_keyword`
  - `gap_exploit`
  - `trend_chase`
- Add `adjacent_niche` every 3rd run (`run_number % 3 == 0`).
- If `config.discovery.enabled_modes` exists, intersect default schedule with enabled list.
- Expected schedule for tests:
  - run 0: four modes
  - run 1: base three
  - run 2: base three
  - run 3: four modes
  - run None: base three

### `run_discovery_cycle` orchestration sequence

1. `evaluate_discovery_results(run_id, db)`
2. `build_feedback_summary(db)`
3. `get_pending_discovery_keywords(db)`
4. `_select_modes(config, run_number)`
5. Run all active `generate_*_hypotheses()` functions
6. Apply budget gate
7. `process_accepted_hypotheses(filtered, run_id, db)`
8. Build and persist `DiscoveryCycleLog`
9. Commit once and return log

### Niche iteration contract

- Iterate all niche IDs from `NICHE_VALIDATION_CONFIG`.
- Aggregate the full cycle into a single `DiscoveryCycleLog` return object.
- Synchronous orchestration is acceptable (generators are sync functions).

### Budget gate contract (exact pattern)

```python
min_confidence = (config or {}).get("discovery", {}).get("min_hypothesis_confidence", 0.50)
max_hypotheses = (config or {}).get("discovery", {}).get("max_hypotheses_per_run", 15)

confident = [
    h
    for h in all_hypotheses
    if getattr(h, "accepted", False)
    and (getattr(h, "specificity_score", 0.0) or 0.0) >= min_confidence
]
accepted = confident[:max_hypotheses]
hypotheses_gated = len(all_hypotheses) - len(confident)
```

### DiscoveryCycleLog serialization contract

- Store `modes_run` with `json.dumps(list_value)`.
- Store `feedback_summary` with `json.dumps(dict_value)`.
- Set `total_cost_usd = 0.0` for S7.8 (no LLM calls).

### Generator input shaping guidance

- `adjacent_keyword`: existing seed keywords per niche
- `gap_exploit`: scored keyword signal rows
- `trend_chase`: trend-focused scored signals
- `adjacent_niche`: existing niche slugs / relationships

## C Handoff (Verification Gates)

- `stage16.py` importable and exports `run_discovery_cycle` + `_select_modes`.
- `run_discovery_cycle` returns `DiscoveryCycleLog`.
- `DiscoveryCycleLog.run_id` equals input run ID.
- `DiscoveryCycleLog.hypotheses_accepted` equals insertion result inserted count.
- `_select_modes` schedule validated (base 3 plus periodic adjacent_niche).
- Empty hypothesis set still writes log with accepted=0.
- Budget cap obeys `max_hypotheses_per_run`.
- No migration introduced.
- Golden parity remains `62.7 / 1.0 / CONDITIONAL_GO` at kw 110.
- Coverage remains >=90 and stage16 test count >=30.

## E Handoff (Audit Scope)

E scope for C072:

- Report-only artifact updates in `docs/` and `PM_Pack/` for governance validation.
- Validate that S7.8 implementation branch includes:
  - importable `stage16.py`
  - `_select_modes` logic contract
  - no LLM usage in stage16 orchestration path
  - `DiscoveryCycleLog` write behavior even with zero accepted hypotheses
- Confirm no regressions in:
  - S7.2-S7.7 modules
  - wave 9 pricing
  - golden parity
  - 9 niches and 9 dashboard pages
  - demo builders absent
  - scrapfly disabled

## F Handoff (Edge-Case Tests)

F should add/verify tests for:

- mode schedule boundaries (`run_number=0,1,2,3,6`)
- all hypotheses below confidence threshold -> 0 inserted with log still created
- `max_hypotheses_per_run` cap enforcement (default 15)
- single commit per cycle
- multi-niche iteration coverage
- `config=None` defaults (`0.50` / `15`)
- `total_cost_usd` hard-set to `0.0`
- non-fatal fallback handling for evaluate/feedback failures where specified

## D Handoff (Merge and Closeout)

- Merge gate includes CI pass, attribution checks, and S7.8 functional gates.
- Post-merge transitions:
  - `SCRUM-1034 -> Done`
  - `SCRUM-203 -> Done`
  - `SCRUM-22` remains In Progress with Wave 10 update comment
- Create next control issue:
  - `SCRUM-1035` for C073 S7.9 Discovery Dashboard Widgets
- Note: G-B is not re-verified in C072 (no migration).

## S7.9 Preview (C073)

Planned scope target:

- Extend `src/dashboard/pages/discovery.py` data layer
- Add:
  - `get_discovery_stats()`
  - `get_gold_discoveries()`
  - `get_mode_performance()`
- Use existing `DiscoveryOutcome` + `DiscoveryCycleLog` data
- No new migration expected

## Wave 10 Scorecard

| Story | Cycle | Status |
| --- | --- | --- |
| S7.1 scaffold | SRDI | DONE |
| S7.2 adjacent keyword | C066 | DONE |
| S7.3 adjacent niche | C067 | DONE |
| S7.4 gap exploit | C068 | DONE |
| S7.5 trend chase | C069 | DONE |
| S7.6 scoring/feedback | C070 | DONE |
| S7.7 keyword integration | C071 | DONE |
| S7.8 stage16 orchestration | C072 | IN PROGRESS |
| S7.9 dashboard widgets | C073 | TO DO |

Wave status:

| Wave | Stories | Status |
| --- | --- | --- |
| 0-9 | done | COMPLETE |
| 10 | 8/9 target after C072 | IN PROGRESS |
| 11 | 0 | NOT STARTED |
| 12 | 0 | NOT STARTED |

## 14-Track Review (Part 5.7 v4.4)

| Track | % (C072 target) | Evidence |
| --- | ---: | --- |
| 01 Foundation | 93% | branch/worktree/CLI baseline checks |
| 02 Data/models | 92% | migration_14 already covers S7.8 fields |
| 03 Collection | 55% | TierD-2 pending, SEED posture |
| 04 Scoring | 90% | golden parity PASS |
| 05 Analysis | 78% | ext on, llm relevance off |
| 06 LLM recs | 70% | not fully live |
| 07 Dashboard | 72% | 9 pages live, discovery page pending depth |
| 08 Pricing | 88% | wave 9 imports intact |
| 09 Discovery | 62% | orchestration stage delivered in C072 scope |
| 10 Playbook | 8% | wave 11 unstarted |
| 11 Dashboard UX | 10% | wave 12 unstarted |
| 12 SRDI | 90% | prior closure retained |

Weighted completion estimate using provided weights: `~64.5%` (rounded project headline `~65%`).

## Part 5.7 Box (v4.4)

```text
╔══════════════════════════════════════════════════════════════╗
║  PROJECT COMPLETION: ~65% production-ready (C072 target)    ║
║  Delta from C071: +1% (S7.8 done; Track 09: 54%→62%)        ║
║  Biggest lever: TierD-2 ScrapFly → +7-8% immediately        ║
║  Next milestone: ~66% after C073 (S7.9 Dashboard Widgets)   ║
╚══════════════════════════════════════════════════════════════╝
```

## Regression Pack v2.5 (45 names, verbatim)

REG-01: test_ghost_market_excluded_from_go_tag  
REG-02: test_conditional_go_threshold_boundary  
REG-03: test_no_go_below_caution_threshold  
REG-04: test_demand_score_keyword_only_depth  
REG-05: test_competition_score_uses_search_result_count  
REG-06: test_feasibility_score_zero_review_seller_eligible  
REG-07: test_profitability_score_package_data_required  
REG-08: test_confidence_score_freshness_decay  
REG-09: test_trc_reliability_single_multiplier_no_stack  
REG-10: test_null_means_include_backward_compat  
REG-11: test_ghost_market_hard_block_only  
REG-12: test_trends_qualifier_threshold_0_65  
REG-13: test_rsv_live_band_threshold  
REG-14: test_rsv_seed_fallback_behavior  
REG-15: test_result_set_validator_min_gigs  
REG-16: test_sponsored_filter_removes_promoted  
REG-17: test_zombie_filter_removes_stale  
REG-18: test_llm_relevance_disabled_passes_all  
REG-19: test_llm_relevance_flags_below_threshold  
REG-20: test_external_signal_integrity_check  
REG-21: test_scoring_profile_weights_sum_to_one  
REG-22: test_final_score_bounded_0_100  
REG-23: test_golden_anchor_kw110_62_7  
REG-24: test_golden_anchor_kw96_35_8  
REG-25: test_golden_anchor_kw3_56_66  
REG-26: test_discovery_core_loop_budget_gate  
REG-27: test_discovery_hypothesis_confidence_threshold  
REG-28: test_alert_new_strong_go_triggered  
REG-29: test_alert_stale_data_warning  
REG-30: test_export_csv_includes_score_components  
REG-31: test_export_excel_valid_workbook  
REG-32: test_cli_config_check_passes  
REG-33: test_cli_seed_niches_idempotent  
REG-34: test_dry_run_sentinel_prevents_live_writes  
REG-35: test_negation_exclusion_removes_off_topic  
REG-36: test_emerging_bonus_applied_correctly  
REG-37: test_ghost_filter_handles_null_ghost_market_score  
REG-38: test_llm_alert_counts_actual_llm_calls  
REG-39: test_monitors_health_check_returns_status  
REG-40: test_quality_gate_blocks_low_coverage  
REG-41: test_external_signal_raw_value_stored_and_retrieved  
REG-42: test_collection_url_encodes_spaces_correctly  
REG-43: test_collection_url_never_bare_path  
REG-44: test_dashboard_opportunities_renders_empty_db_gracefully  
REG-45: test_legacy_unscored_rows_are_ignored

## Handoff Package Index

- `docs/cycle_reports/CYCLE_072_AGENT_B_HANDOFF.md`
- `docs/cycle_reports/CYCLE_072_AGENT_C_HANDOFF.md`
- `docs/cycle_reports/CYCLE_072_AGENT_D_HANDOFF.md`
- `docs/cycle_reports/CYCLE_072_AGENT_E_HANDOFF.md`
- `docs/cycle_reports/CYCLE_072_AGENT_F_HANDOFF.md`

## Authorization Statements

Task 44 statement:

"CYCLE 072 PROMPTS AUTHORIZED FOR RELEASE. Policy v4.3: 55 LARGE-XXLARGE tasks. Floors: A:1000 B:1200 E:950 C:900 F:1000 D:1200. S7.8 Stage 16 Orchestration: run_discovery_cycle() wires S7.2-S7.7. New file: src/discovery/stage16.py only. No LLM calls. No migration. No orchestrator.py modifications. Wave 10: 8/9 stories after C072. Project ~65%. TierD-1: 12 stashes. TierD-2: SEED x15."

Task 73 statement:

"CYCLE 072 PROMPTS AUTHORIZED. Policy v4.3: 55 LARGE-XXLARGE. Floors A:1000 B:1200 E:950 C:900 F:1000 D:1200. S7.8: run_discovery_cycle() wires S7.2-S7.7. stage16.py only. No LLM. No migration. orchestrator.py untouched. Wave 10: 8/9 after C072. Project ~65%. TierD-1: 12 stashes. TierD-2: SEED x15."

Compliance lines:

- TASK 100: wave 10 8/9 -- PASS
- TASK 101: S7.8 orchestration -- PASS
- TASK 102: no migration -- PASS
