# Agent Execution Strategy

Canonical reference for multi-agent cycle execution, regression packs, and handoff contracts.

---

## Section 7: Permanent Regression Pack

Accumulated regression selectors (15-name pack) plus cycle-specific permanent regressions.

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
