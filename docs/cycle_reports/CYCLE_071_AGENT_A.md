# CYCLE 071 - AGENT A PLANNING REPORT

Date: 2026-06-08  
Branch: `cycle/071/integration`  
Cycle control: `SCRUM-1033`  
Story: `SCRUM-202`  
Develop baseline reference for C071 planning scope: `afbfcf1` (includes hotfix `4234ff6`)

## Governance and Policy

- Policy v4.3 upheld for C071 planning/governance outputs.
- Zone discipline upheld: `PM_Pack/` + `docs/` only for Agent A artifacts.
- S7.7 treated correctly as INSERT-stage bridge (not GENERATE, not EVALUATE).

## Branch and Baseline Evidence

- Branch created and pushed: `cycle/071/integration`.
- Worktree check: single worktree entry.
- Golden parity check: PASS (`kw=110 = 62.7 / 1.0 / CONDITIONAL_GO`).
- Unit collection baseline: `5050 tests collected`.
- C070 hotfix (`4234ff6`) behavior still intact: legacy unscored outcomes excluded from feedback totals.

## Jira Actions Completed

- `SCRUM-1033` transitioned to **In Progress** and commented with C071 S7.7 scope.
- `SCRUM-202` transitioned to **In Progress**.
- `SCRUM-22` remains **In Progress** and updated with Wave 10 progress note.

## Production Readiness Gates Update

G-A: CLOSED | G-B: CLOSED | G-C: CLOSED | G-D: OPEN (S7.7-S7.9 remain; Waves 11-12).  
G-B note: S7.7 adds no new tables/columns and only inserts to existing `keywords`; G-B does not need re-verification after C071 merge when migration_14 is untouched.

## S7.7 Scope Confirmation

S7.7 is the Discovery INSERT stage:

- Input: accepted `HypothesisContract` items from S7.2-S7.5 generators.
- Output: new discovery `Keyword` rows queued for normal collect/score pipeline.
- No migration required in C071 (migration_14 from C070 already provides S7.7 lineage columns).
- New implementation file for B: `src/discovery/integration.py`.
- Test target for B/F: `tests/unit/test_discovery_integration.py` (>=30 tests).

Required S7.7 integration functions:

1. `insert_discovery_keyword()`
2. `queue_discovery_collection()`
3. `process_accepted_hypotheses()`
4. `get_pending_discovery_keywords()`
5. `check_discovery_keyword_exists()`

## Baseline Technical Survey Results

### Discovery module state at C071 start

- `src/discovery/integration.py`: absent at baseline (B creates).
- `src/discovery/feedback.py`: present and importable.
- `src/discovery/hypothesis.py`: present and importable.
- `src/discovery/contracts.py`: present and importable.

### Keywords table/model readiness (S7.7 fields)

All required S7.7 columns are present in DB and ORM:

- `is_discovery`
- `discovery_mode`
- `hypothesis_confidence`
- `hypothesis_rationale`
- `discovered_in_run`
- `discovery_evaluated`
- `is_retired`

Conclusion: **no migration needed for S7.7**.

### Important schema reality for B implementation

- `Keyword` column name is `keyword` (not `keyword_text`).
- `Keyword.niche_id` is currently integer-typed in ORM.
- Dedup contract remains case-insensitive by normalized keyword text plus niche scope; B should map prompt naming (`keyword_text`) to repository column naming (`keyword`).

### Hypothesis contract survey

- Present: `hypothesis_text`, `niche_id`, `specificity_score`, `accepted`, `reason`.
- `HypothesisMode` values confirmed: `adjacent_keyword`, `adjacent_niche`, `gap_exploit`, `trend_chase`.
- `discovery_mode` is not a dataclass field on `HypothesisContract`; B should derive mode from orchestration context or compatible source field.

### 5 mandatory gap checks

- Check 1: dashboard demo data references = `[]` (PASS).
- Check 2: toggles = `external_signals=true`, `scrapfly=false`, `llm_relevance=false` (PASS).
- Check 3: SRDI baseline posture carried (PASS).
- Check 4: niche config count = `9` (PASS).
- Check 5: dashboard pages count = `9` (PASS).

### Additional baseline verifications

- `discovery_outcomes` and `discovery_cycle_logs` tables present.
- Baseline live DB untouched (`data/cycle037_live.db` mtime unchanged).
- Discovery seed-mode counts: `discovery_outcomes=0`, discovery keywords in gate DB `=0`.
- Wave 9 pricing imports are intact.
- `ADJACENT_NICHE_RELATIONSHIPS` count remains `9`.
- Existing keyword insertion/query idioms were surveyed in `src/collection/orchestrator.py`; B should follow current ORM/write patterns and repository field naming.

## Dedup and Lineage Contract for B

### Dedup

- Dedup key: case-insensitive normalized keyword text + niche.
- Applies to both existing discovery and existing seed keywords.
- Duplicate behavior: return `None`, skip silently, log DEBUG.
- Same keyword text across different niches is allowed.

### Lineage (populate atomically on insert)

1. `is_discovery = True`
2. `discovery_mode = <mode>`
3. `hypothesis_confidence = <specificity/confidence>`
4. `hypothesis_rationale = <reason or fallback>`
5. `discovered_in_run = run_id`
6. `discovery_evaluated = False`
7. `is_retired = False`

### Batch contract

`process_accepted_hypotheses()` must always return:

```python
{
  "inserted": int,
  "skipped": int,
  "run_id": str,
  "keyword_ids": list,
}
```

## S7.7 vs Neighbor Stories

- S7.2-S7.5: hypothesis generation only, no keyword inserts.
- S7.6: evaluation/feedback after scoring, already delivered in C070.
- S7.7: inserts accepted hypotheses into keywords for normal collection/scoring.
- S7.8 (C072): orchestration stage wiring.
- S7.9 (C073): dashboard presentation for discovery outcomes.

Wave 10 stage map (documentation requirement):

- GENERATE (S7.2-S7.5) - `hypothesis.py` - DONE
- EVALUATE (S7.6) - `feedback.py` - DONE
- INSERT (S7.7) - `integration.py` - THIS CYCLE
- ORCHESTRATE (S7.8) - `orchestrator.py` - C072
- DISPLAY (S7.9) - `dashboard/pages/` - C073

## Wave 10 Scorecard

| Story | Cycle | Status |
| --- | --- | --- |
| S7.1 scaffold | SRDI | DONE |
| S7.2 adjacent keyword | C066 | DONE |
| S7.3 adjacent niche | C067 | DONE |
| S7.4 gap exploit | C068 | DONE |
| S7.5 trend chase | C069 | DONE |
| S7.6 scoring/feedback | C070 | DONE |
| S7.7 keyword integration | C071 | IN PROGRESS |
| S7.8 stage16 orchestration | C072 | TO DO |
| S7.9 dashboard | C073 | TO DO |

## 14-Track Review (Part 5.7 v4.4)

| Track | % (C071 target) | Evidence |
| --- | ---: | --- |
| 01 Foundation | 93% | CLI and branch/worktree checks green |
| 02 Data/models | 92% | migration_14 already contains S7.7 fields |
| 03 Collection | 55% | TierD-2 PENDING; RSV SEED x15; code 95% done |
| 04 Scoring | 90% | Golden anchor parity pass |
| 05 Analysis | 78% | ext signals enabled, llm relevance disabled |
| 06 LLM recs | 70% | Built but not fully live-run |
| 07 Dashboard | 72% | 9 pages, demo refs 0 |
| 08 Pricing | 88% | Wave 9 pricing intact |
| 09 Discovery | 54% | S7.7 planning contract complete, 7/9 target after C071 |
| 10 Playbook | 8% | Wave 11 unstarted |
| 11 Dashboard UX | 10% | Wave 12 unstarted |
| 12 SRDI | 90% | R1-R11 complete, G-A closed |

Weighted completion estimate:

- `~64.0%` using Part 5.7 weight model.
- Discovery track shift: `46% -> 54%` after S7.7.

## Part 5.7 Final Box (v4.4)

```text
╔══════════════════════════════════════════════════════════════╗
║  PROJECT COMPLETION: ~64% production-ready (C071, 2026-06-08)  ║
║  Delta from C070: +1% (S7.7 INSERT; Track 09: 46%→54%)        ║
║  Biggest lever: TierD-2 ScrapFly → +7-8% immediately          ║
║  Next milestone: ~65% after C072 (S7.8 Stage 16 Orchestration) ║
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

- `docs/cycle_reports/CYCLE_071_AGENT_B_HANDOFF.md`
- `docs/cycle_reports/CYCLE_071_AGENT_C_HANDOFF.md`
- `docs/cycle_reports/CYCLE_071_AGENT_D_HANDOFF.md`
- `docs/cycle_reports/CYCLE_071_AGENT_E_HANDOFF.md`
- `docs/cycle_reports/CYCLE_071_AGENT_F_HANDOFF.md`

## Commercial Value Statement

S7.7 unlocks direct commercial value by converting accepted hypotheses into first-class keywords that flow through collection, scoring, and later feedback. Without INSERT, generation output remains inert. With INSERT, discovery ideas become executable pipeline candidates on the next run.

## run_id Convention Survey and Recommendation

- Existing codebase patterns use both UUID-based and timestamp-based run identifiers.
- B should follow orchestrator-compatible conventions for consistency.
- Fallback recommendation if no helper applies: `discovery-YYYYMMDD-HHMMSS`.

## S7.7 Design Note (Required)

For implementation guidance, `integration.py` should use lazy imports for model access inside function bodies (for example `from src.models import Keyword` within functions) to minimize circular-import risk, consistent with discovery module patterns.

## SCRUM-202 Acceptance Criteria Check (Required)

1. Approved discovery keywords integrate into keyword table with source lineage -> covered by `insert_discovery_keyword()` contract.
2. Duplicates are prevented -> covered by case-insensitive dedup on keyword+niche scope.
3. Promotion confidence preserved -> `hypothesis_confidence` lineage field requirement captured.
4. Tests cover promotion/duplicate/missing-data/rollback behavior -> directed to `tests/unit/test_discovery_integration.py` with >=30 tests.

## Required Authorization Statements

Task 50 authorization statement (verbatim requirement):

"CYCLE 071 PROMPTS AUTHORIZED FOR RELEASE.
Policy v4.3: 55 LARGE-XXLARGE tasks, floors A:1000/B:1200/E:950/C:900/F:1000/D:1200.
14 tracks reviewed. 5 gap checks PASS. Jira clean.
SCRUM-1033 In Progress. SCRUM-202 In Progress. SCRUM-22 In Progress.
Base SHA: afbfcf1 (includes C070 hotfix 4234ff6). Suite: 5050/94.01%.
S7.7 Discovery Keyword Integration:
  NEW FILE: src/discovery/integration.py (INSERT stage)
  Functions: insert_discovery_keyword(), process_accepted_hypotheses(),
             get_pending_discovery_keywords(), check_discovery_keyword_exists(),
             queue_discovery_collection()
  NO NEW MIGRATION (migration_14 from C070 has all required columns)
  Dedup: case-insensitive (keyword_text, niche_id) check
  Lineage: all 7 discovery fields populated on insert
Wave 10: 7/9 stories after C071. Project ~64%.
TierD-1: 12 stashes. TierD-2: SEED x14. Approve TierD-2 before C072."

Task 59 final paragraph format (verbatim requirement):

"CYCLE 071 PROMPTS AUTHORIZED FOR RELEASE.
Policy v4.3 floors: A:1000 B:1200 E:950 C:900 F:1000 D:1200.
S7.7 Discovery Keyword Integration. INSERT stage.
No migration. integration.py only. Wave 10: 7/9 after C071.
Project ~64%."

CYCLE 071 PROMPTS AUTHORIZED FOR RELEASE.  
Policy v4.3: floors A:1000 B:1200 E:950 C:900 F:1000 D:1200.  
S7.7 Discovery Keyword Integration: INSERT stage.  
New file: `src/discovery/integration.py` only.  
No migration. 5 functions. Dedup. Lineage. Batch.  
Wave 10: 7/9 after C071. Project ~64%.  
TierD-1: 12 stashes. TierD-2: SEED x15.

CYCLE 071 PROMPTS AUTHORIZED.  
Policy v4.3: 55 LARGE-XXLARGE tasks. Floors: A:1000 B:1200 E:950 C:900 F:1000 D:1200.  
S7.7 Discovery Keyword Integration.  
New file: `src/discovery/integration.py`.  
No migration. Dedup. Lineage. Batch commit.  
Wave 10: 7/9 stories after C071. Project ~64%.  
TierD-1: 12 stashes. TierD-2: SEED x14. Approve before C072.
