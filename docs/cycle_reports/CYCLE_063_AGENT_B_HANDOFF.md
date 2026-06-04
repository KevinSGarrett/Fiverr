# CYCLE 063 — AGENT B HANDOFF

## Scope
- Story: `SCRUM-1024`
- Wave scope: 9C Pricing LLM Task + 9D Pricing Dashboard Widgets
- Constraint: pricing changes must be additive and preserve golden anchor parity.

## Files To Create
- `src/pricing/llm_task.py` (Task #12 pricing LLM task; align with existing client/cache/logging pattern)
- `src/llm/templates/stage13_recommendations/pricing_strategy.j2` (template location used by current recommendation stack)
- `tests/unit/test_pricing_llm_task.py` (>=20 tests)
- `tests/unit/test_dashboard_pricing_widgets.py` (>=15 tests)

## Files To Modify
- `src/recommendations/context.py`
  - Ensure 7 pricing fields remain present and correctly populated at build time:
    - `price_distribution`
    - `market_type`
    - `calculated_entry_prices`
    - `calculated_price_ladder`
    - `new_seller_discount_pct`
    - `competitor_price_positions`
    - `price_review_correlation`
- `src/recommendations/schemas.py`
  - Add `pricing_strategy` to `RecommendationOutput` and include in completeness logic.
- `src/recommendations/executor.py`
  - Add pricing task #12 into the `asyncio.gather()` task list and field order.
- `src/recommendations/llm_tasks.py` (or route through `src/pricing/llm_task.py`)
  - Wire pricing task execution to same LLM client invocation and cache behavior.
- `src/dashboard/pages/opportunities.py`
  - Add W-PRICE-1 mini histogram integration path.
- `src/dashboard/pages/keywords.py`
  - Add price summary column + W-PRICE-3 heatmap.
- `src/dashboard/pages/recommendations.py`
  - Add W-PRICE-2 pricing strategy tab/card.
- `src/dashboard/pages/run_history.py`
  - Add W-PRICE-4 revenue projection widget.

## Required Signatures
- `async def pricing_llm_task(keyword_id, context, db, client) -> str | None`
- `def render_price_distribution_chart(keyword_id, db) -> None`
- `def render_pricing_strategy_card(pricing_snapshot, db) -> None`
- `def render_price_heatmap(niche_id, db) -> None`
- `def render_revenue_projection(keyword_id, db) -> None`

## Cache, Skip, and Cost Rules
- Cache key format target:
  - `f"pricing_strategy:{keyword_text}:{price_distribution_hash}:{competitor_hash}"`
- Skip condition:
  - If no `PriceAnalysis` row exists for keyword, return `None` (no crash).
- Use existing cache/client pattern in `src/recommendations/llm_tasks.py`:
  - `_cache_get`, `_cache_set`, and graceful fallback behavior.
- Keep LLM tracking compatible with existing `llm_usage_logs` schema in `src/models/runtime.py`:
  - Existing columns include `model_name` and `total_cost_usd`.
  - No `task_type`, `keyword_id`, or `cost_usd` columns currently exist in DB baseline.

## Existing Insertion Points (Current Code)
- 11-task gather currently lives in `src/recommendations/executor.py` within:
  - `generate_recommendation_async(...)`
  - `_TASK_FIELD_ORDER`
- Template loading currently uses:
  - `src/llm/templates/stage13_recommendations/*.j2` via `load_template(...)` in `src/recommendations/llm_tasks.py`
- Current dashboard page function entry points for 9D:
  - `render_opportunities_page()` in `src/dashboard/pages/opportunities.py`
  - `render_keywords_page()` in `src/dashboard/pages/keywords.py`
  - `render_recommendations_page()` in `src/dashboard/pages/recommendations.py`
  - `render_run_history_page()` in `src/dashboard/pages/run_history.py`

## DB + Migration Notes
- Canonical pricing table used by code is `price_analysis` (`src/models/price_analysis.py`).
- Legacy table `price_analyses` also exists in baseline DB; do not create further duplicates.
- `recommendations` table currently does not include `pricing_strategy`; add migration if persisting column output is required.

## Hard Gate Reminder
- Golden invariant must hold: `kw=110 => 62.7 / 1.0 / CONDITIONAL_GO`.
- Pricing LLM task must be additive and not alter golden mode outcomes.
