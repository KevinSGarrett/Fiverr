# Agent Execution Strategy

Canonical reference for multi-agent cycle execution, regression packs, and handoff contracts.

---

## Section 7: Permanent Regression Pack

Accumulated regression selectors (20-name pack) plus cycle-specific permanent regressions.

### Current 20-name accumulated pack (Cycle 053 baseline)

These are the required regressions that must stay green during Cycle 053:

| # | Test name | File |
| --- | --- | --- |
| 1 | `test_extract_price_text_from_payload_uses_nested_price_amount` | `tests/unit/test_gig_detail.py` |
| 2 | `test_parse_gig_detail_from_html_keeps_zero_review_count` | `tests/unit/test_gig_detail.py` |
| 3 | `test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration` | `tests/unit/test_seller_profile.py` |
| 4 | `test_seller_profile_fetcher_maps_parser_fields_for_persistence` | `tests/unit/test_seller_profile.py` |
| 5 | `test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields` | `tests/unit/test_gig_detail.py` |
| 6 | `test_seller_profile_live_markup_drift_regression_spec` | `tests/unit/test_seller_profile.py` |
| 7 | `test_scoring_fallback_queries_scope_to_active_run_id` | `tests/unit/test_scoring_db_integration.py` |
| 8 | `test_scoring_fallback_queries_recover_when_latest_run_unlinked` | `tests/unit/test_scoring_db_integration.py` |
| 9 | `test_demand_uses_search_result_total_result_count_when_available` | `tests/unit/test_scoring_db_integration.py` |
| 10 | `test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch` | `tests/unit/test_competition_score.py` |
| 11 | `test_scoring_uses_card_urls_with_querystrings_for_sparse_links` | `tests/unit/test_scoring_db_integration.py` |
| 12 | `test_confidence_modifier_uses_current_run_context_not_none` | `tests/unit/test_confidence_score.py` |
| 13 | `test_weakness_multi_row_fallback_does_not_produce_extreme_value` | `tests/unit/test_weakness_multi_row_averaging.py` |
| 14 | `test_fiverr_search_url_always_includes_category_filter_for_production_niches` (REG-13) | `tests/unit/test_search_url_builder.py` |
| 15 | `test_unconstrained_search_result_applies_demand_confidence_deduction` (REG-14) | `tests/unit/test_search_url_builder.py` |
| 16 | `test_eligibility_ghost_hard_block_even_when_forced` (REG-15) | `tests/unit/test_recommendation_eligibility.py` |
| 17 | `test_demand_qualified_trc_when_rsv_below_080` (REG-16) | `tests/unit/test_demand_score_extended.py` |
| 18 | `test_sponsored_gigs_never_included_in_competition_top10` (REG-17) | `tests/unit/test_scoring_db_integration.py` |
| 19 | `test_zombie_gigs_never_used_in_feasibility_review_barrier` (REG-18) | `tests/unit/test_feasibility_extended.py` |
| 20 | `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent` (REG-19) | `tests/unit/test_demand_score_extended.py` |

REG-15 and REG-16 are now active in the permanent pack for Cycle 053.

Carry-forward Codex-fix guards that must remain named and green:

| Test name | File | Purpose |
| --- | --- | --- |
| `test_demand_pairs_strictness_with_selected_total_result_count_row` | `tests/unit/test_scoring_db_integration.py` | Strictness/count row pairing guard |
| `test_demand_ignores_legacy_migration_default_none_strictness` | `tests/unit/test_scoring_db_integration.py` | Migration-default `'NONE'` guard in demand path |

### Cycle 049 additions (2026-05-29)

| Test name | File | Purpose |
| --- | --- | --- |
| `test_weakness_multi_row_fallback_does_not_produce_extreme_value` | `tests/unit/test_weakness_multi_row_averaging.py` | kw=96 combined-state weakness must not spike to 100.0 when a single OWS=10.0 penalty row is present alongside moderate rubric rows |
| `test_weakness_extreme_ows_row_does_not_dominate_average` | `tests/unit/test_weakness_multi_row_averaging.py` | OWS aggregation excludes ceiling rows when lower scores exist |
| `test_weakness_kw96_equivalent_consistent_before_after_combined_state` | `tests/unit/test_weakness_multi_row_averaging.py` | Historical fallback rejects transient 100.0 when stable 53.52 exists |
| `test_kw110_conditional_go_passes_all_recommendation_gates_when_analysis_complete` | `tests/unit/test_recommendation_eligibility.py` | Eligibility gate clears when GQS analysis_complete populated |

### Cycle 051 additions (2026-05-30)

| Test name | File | Purpose |
| --- | --- | --- |
| `test_fiverr_search_url_always_includes_category_filter_for_production_niches` | `tests/unit/test_search_url_builder.py` | Guarantees all production niches keep category/subcategory constraints under SUBCATEGORY strictness |
| `test_unconstrained_search_result_applies_demand_confidence_deduction` | `tests/unit/test_search_url_builder.py` | Guards the post-R1 NONE strictness confidence deduction and note attachment |

### Version history

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-05-29 | Cycle 049 Agent B: added weakness multi-row OWS averaging regression + kw=110 eligibility gate regression |
| 1.1 | 2026-05-30 | Cycle 051 Agent B: added R1 search URL category-filter + unconstrained demand-deduction regressions |
| 1.3 | 2026-05-30 | Cycle 052 Agent B: added REG-17/18/19 (sponsored competition exclusion, zombie feasibility barrier exclusion, TRC sponsored-fraction multiplier). |
| 1.4 | 2026-05-31 | Cycle 053 Agent B: activated REG-15/16 (ghost hard block and RSV-qualified TRC demand path) and expanded permanent pack to 20 names. |

### 12-name accumulated pack (reference)

Run with:

```text
python -m pytest -q tests/unit/test_gig_detail.py \
  tests/unit/test_scoring_db_integration.py \
  tests/unit/test_scrapfly_workflow_integration.py \
  tests/unit/test_search_result.py \
  tests/unit/test_competition_score.py \
  tests/unit/test_confidence_score.py \
  -k "nested_price or zero_review or run_scoped or seller_profile_live_markup_drift \
      or rank or gig_id or latest_unlinked or total_result_count or profile_fallback \
      or signals_present or card_urls or current_run_context" \
  -v --no-header
```

Expected: 20 passed (12 named regressions + superset matches).

---

## Section 8: Task & Prompt-Length Standard (effective Cycle 052+)

This section is authoritative for per-agent task counts and prompt length minimums. It
supersedes the older "18+/20+ task" and prior length figures referenced anywhere else.

### 8.1 Task minimum (raised 20 -> 25)

Every cursor-agent prompt MUST contain **at least 25 tasks**, each sized LARGE, XLARGE,
XXLARGE, or **XXXLARGE**. No standalone small/medium tasks.

| Size | Sub-steps | Typical use |
| --- | --- | --- |
| LARGE | 4-6 | a single focused deliverable (one module section, one test group) |
| XLARGE | 6-8 | a multi-part deliverable with verification |
| XXLARGE | 8-12 | a subsystem + its tests + its wiring |
| XXXLARGE | 12+ (or spans >=2 files with cross-checks) | a full feature slice end-to-end, or a migration + model + wiring + tests |

### 8.2 Legitimacy rule (binding)

Every task must be **real, project-advancing work** that moves the system toward end-to-end
completion. Filler, busywork, or padding tasks invented only to reach the count of 25 are a
PM failure and an agent failure. Each task must map to: a spec requirement, an acceptance
criterion, a regression, a gate, a re-collection/validation need, or a concrete integration
step. If a cycle's real scope does not yield 25 substantive tasks for an agent, the PM splits
larger deliverables into legitimately separable verification-bearing steps -- never invents
hollow ones.

### 8.3 Prompt length minimum (raised +35%)

| Agent | Old min | New min (+35%) |
| --- | --- | --- |
| A | 600 | **810** |
| B | 700 | **945** |
| E | 600 | **810** |
| C | 500 | **675** |
| F | 600 | **810** |
| D | 700 | **945** |
| **Total** | 3,700 | **4,995** |

Length is a floor, not a target; it must be filled with substantive content (code skeletons,
test stubs, verbatim queries, deliverable matrices, decision records, trace ledgers, report
templates) -- never filler to hit a line count.

### 8.4 Prompt-sizing enforcement (BLOCKING self-gate on the PM's own work)

Before the PM may declare a cycle's prompt-writing complete -- and before any prompt is handed
to an agent -- the PM MUST verify EVERY agent prompt against BOTH §8.1 (>=25 substantive
LARGE-XXXLARGE tasks) AND §8.3 (per-agent line floor). Verification is mechanical and recorded,
never eyeballed:

1. Run `(Get-Content <prompt_path>).Count` on all six prompts and record the ACTUAL line counts
   next to their floors (A810 / B945 / E810 / C675 / F810 / D945; total 4995).
2. Count the numbered tasks in each prompt; confirm >=25, each genuinely LARGE-XXXLARGE -- not a
   one-line stub masquerading as a task.
3. ANY prompt under its line floor OR under 25 substantive tasks is **NOT DONE**. The PM MUST
   expand it with GENUINE content per §8.3 -- full inline code/dataclass skeletons, full inline
   test-file skeletons with every test-function stub, verbatim command/query/gate blocks,
   per-niche and per-file procedures, deliverable + Definition-of-Done matrices, worked numeric
   examples, and report templates -- then re-verify the count. Padding to hit the number is
   itself a §8.2 legitimacy failure.
4. This gate is HARD and BLOCKING. The v3.0 Post-Cycle PM Review self-audit item "every prompt
   meets minimum line count and task minimum" is BLOCKING, not advisory. The PM may NOT conclude
   cycle prep, and may NOT release prompts to the agents, until all six PASS both checks with
   recorded counts.
5. The recorded count table (actual vs floor, per agent) MUST be included in the cycle's prep
   notes / PM closeout so the check is auditable by the next PM review.

Rationale: Cycle 053 prep initially shipped all six prompts far under floor
(A487 / B271 / E157 / C161 / F156 / D184 vs the 4995 total) even though each held 25 tasks.
Under-length prompts systematically omit the inline skeletons, command blocks, and acceptance
detail the agents need to execute without guesswork. This gate makes that omission impossible
to ship.

### Version history (continued)

| Version | Date | Change |
| --- | --- | --- |
| 1.2 | 2026-05-30 | Post-Cycle-051 PM: task minimum 20 -> 25 (LARGE-XXXLARGE); prompt length minimums +35% (A810/B945/E810/C675/F810/D945; total 4995); added explicit legitimacy rule (no filler tasks). |
| 1.4 | 2026-05-31 | Added §8.4 prompt-sizing enforcement: blocking self-gate requiring `(Get-Content).Count` verification of every prompt against its floor + 25-task minimum, recorded in prep notes, before prompts may be released. Triggered by Cycle 053 under-floor prompts. |
