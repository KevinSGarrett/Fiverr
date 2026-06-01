# CYCLE 055 PLAN — SRDI R6 Discovery Engine Relevance Gates

## 1) Cycle Scope Narrative

Cycle 055 implements SRDI R6 to prevent discovery-loop contamination by gating hypotheses and candidate keywords before they can pollute persistence and feedback learning.

R6 introduces one pre-validation module and four gate behaviors:

1. Gate 1: anti-contamination hypothesis prompt + deterministic specificity/on-niche rejection
2. Gate 2: pre-validation dry-run against R2 relevance + validated-only insert
3. Gate 3: outcome semantics split (`INVALID` vs real miss)
4. Gate 4: feedback learning excludes invalid/contaminated outcomes

Critical boundary: discovery activation remains OFF after merge; Tier-1 activation is deferred until `R4 + R6 + R9` are all complete and explicitly approved.

Parity anchor (branch base): `acff870e8ef32d8e92bc2ebad4ff14e0675fdbc7`

## 2) Dependency Order + Pipeline Order

- Dependency order: `R8 -> R1 -> R2 -> R6` (R4 is Tier-1 sibling prerequisite and is already merged)
- Agent pipeline order: `A -> [B + E] -> C -> F -> D`

Rationale:

- B consumes A's exact names/contracts
- E builds live-validation matrix in parallel but validates only after B code lands
- C verifies integration independently
- F hardens coverage after integrated behavior exists
- D runs governance/merge gate last (including Codex double-check)

## 3) Config Contract

- Required new toggle: `discovery.enable_relevance_gates`
- Required default: `false`
- Exact YAML path: `config.yaml -> discovery.enable_relevance_gates`
- Required model field location: `src/config/models.py` -> `DiscoveryConfig.enable_relevance_gates`

Config governance:

- Toggle OFF path must preserve legacy behavior exactly.
- This cycle allows only this one new toggle key.
- Committed `collection.scrapfly.enabled` must remain `false`.
- No other committed config behavior changes are in scope.

## 4) Gate-by-Gate File Mapping (B implementation targets)

## Gate 1 — Hypothesis Anti-Contamination + Specificity

- Story keys: `SCRUM-626`, `SCRUM-864`
- Attach path: `src/discovery/hypothesis.py`
- Primary function to evolve: `generate_niche_hypotheses`
- Required additions:
  - niche scope grounding in prompt text
  - buyer + deliverable hypothesis contract fields
  - deterministic `_gate_hypotheses` specificity/on-niche filter (no second LLM call)
  - explicit rejection reason capture

## Gate 2 — Pre-Validator Dry-Run + Validated-Only Insert

- Story keys: `SCRUM-627`, `SCRUM-868`
- Attach path: `src/discovery/orchestrator.py`
- Orchestrator insertion gate target: `promote_keywords` / `run_cycle` decision branch
- New module for cycle implementation: `src/analysis/pre_validator.py` (`DiscoveryPreValidator`)
- Hard reuse contract:
  - `src/analysis/result_set_validator.py::validate_result_set`
  - `src/analysis/result_set_validator.py::compute_gig_relevance`
  - `src/analysis/result_set_validator.py::NICHE_VALIDATION_CONFIG`
  - canonical import statement:
    - `from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG, compute_gig_relevance, validate_result_set`

Dry-run constraint:

- Pre-validator must not trigger live ScrapFly collection itself.
- It must evaluate existing/provisional result-set signals only.

## Gate 3 — Relevance-Gated Outcome Recording

- Story key: `SCRUM-628`
- Existing discovery entrypoint path in current repo: `src/discovery/orchestrator.py`
- Attach location: `DiscoveryOrchestrator.run_cycle` outcome-persistence branch
- Outcome rule:
  - ghost/contaminated discoveries become `INVALID` outcomes (with reason + RSV)
  - genuine but unsuccessful candidates remain misses

## Gate 4 — Feedback Excludes Invalid/Contaminated

- Story key: `SCRUM-873`
- Existing discovery entrypoint path in current repo: `src/discovery/orchestrator.py`
- Attach location: `DiscoveryOrchestrator.run_cycle` feedback-aggregation branch
- Learning rule:
  - exclude invalid/contaminated outcomes from feedback aggregation
  - only valid outcomes (hit or genuine miss) remain training input

SRDI reference-path note:

- Legacy SRDI planning references list `src/discovery/feedback.py`; current repository discovery package exposes `src/discovery/orchestrator.py` as the operative gate-attachment file and this plan is authoritative for Cycle 055 implementation.

## 5) Data Model Touchpoints (R6 population only)

## DiscoveryOutcome

- Migration source: `src/migrations/srdi_r8/migration_06_discovery_outcomes_srdi_columns.py`
- Present columns: `is_invalid`, `is_contaminated`, `relevance_score`, `contamination_reason`
- Spec-required mismatch to resolve in B:
  - expected `invalid_reason` (not `contamination_reason`)
  - expected `pre_validation_passed` (missing)
- ORM note: no `DiscoveryOutcome` model class is currently present under `src/models/`

## Keyword discovery columns

- Migration source: `src/migrations/srdi_r8/migration_05_keywords_srdi_columns.py`
- Present columns: `ghost_market_flag`, `discovery_needs_recollection`, `last_relevance_validated_at`
- Spec-required mismatch to resolve in B:
  - expected `pre_validation_data` (missing)
  - expected `specificity_confidence` (missing)
- ORM note: `src/models/market.py::Keyword` does not yet map these migration columns.

## ResultSetValidation (R2 contract)

- Model: `src/models/result_set_validation.py`
- Relevance fields consumed by R6 gate logic:
  - `result_set_relevance_score`
  - `ghost_market_flag`
  - `category_contamination_flag`
  - `used_fallback_strictness`

## 6) Tier-1 Validation Criterion

With `discovery.enable_relevance_gates=true`, discovery rejection rate must be in the `0.20-0.40` band:

- `< 0.20` means gates are too weak/inert
- `> 0.40` means gates are over-restrictive

This criterion is validated by Agent E with Agent B fixture alignment and enforced by Agent D.

## 7) Governance Non-Negotiables (Agent D Merge Gate)

1. Attribution invariant
   - All `src/` edits are Agent B authored only.
   - No no-op attribution commits.

2. Zone rules
   - A: `PM_Pack/` + `docs/cycle_reports/` + Jira only; zero `src/`/`tests/`
   - B: `src/` + `tests/` + report; only `src/` author
   - C: docs/report only; zero `src/`/`tests/`
   - E: docs/report only; zero `src/`/`tests/`; never commit `config.live.yaml` or `data/*.db`
   - F: `tests/` + report only; zero `src/`
   - D: governance docs/report only; zero `src/`/`tests/`

3. Single coverage authority
   - Command: `python -m pytest -q --cov=src --cov-fail-under=90`
   - No floor lowering or exclusion tricks.

4. Golden parity gate
   - Toggle OFF must match legacy baseline exactly.
   - `kw=110` remains `CONDITIONAL_GO` (final >= 60, CM 1.0).
   - Anchor keywords `110/96/3` must not drift >2 points.
   - Suspect baseline means STOP/escalate (never mask).

5. Codex review checked twice
   - Use GraphQL `reviewThreads(first:100)` unresolved count.
   - Zero unresolved required before merge and rechecked immediately pre-merge.

6. Jira DoD integrity
   - Stories transition to Done only with cited DoD evidence.

7. Regression pack count
   - Permanent pack is now 26 (23 carry + REG-25/26/27).

8. ScrapFly/live safety
   - Committed config keeps `collection.scrapfly.enabled: false`.
   - Any live validation uses local uncommitted `config.live.yaml` + `SCRAPFLY_API_KEY` + explicit `--config-path`.
   - Agent E uses dedicated throwaway DB only (never golden baseline DB).

## 8) Permanent Regression Pack (26 names)

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
- `test_ghost_discovery_recorded_as_invalid_not_miss (REG-25)`
- `test_feedback_excludes_contaminated_outcomes (REG-26)`
- `test_low_specificity_hypothesis_rejected (REG-27)`

Demand guards (must stay green):

- `test_demand_pairs_strictness_with_selected_total_result_count_row`
- `test_demand_ignores_legacy_migration_default_none_strictness`

## 9) Shared Contamination Fixture Matrix (9 niches)

Niche: `prd_ai_saas`  
Expected scope: PRD/MVP roadmap definition for AI SaaS offers.  
ON-NICHE: "draft a SaaS PRD and feature-priority roadmap for an AI support startup"  
DRIFT: "edit a launch promo video for AI startup marketing"  
GHOST/CONTAM: "product strategy"

Niche: `support_kb_readiness`  
Expected scope: support knowledge-base audits, help-center structure, support docs.  
ON-NICHE: "help-center article rewrite for a SaaS support team"  
DRIFT: "design social media banners for a support team brand refresh"  
GHOST/CONTAM: "support"

Niche: `gumloop_lindy_workflow`  
Expected scope: Gumloop/Lindy automation workflow design and implementation.  
ON-NICHE: "build a Gumloop workflow for inbound lead routing"  
DRIFT: "write ad copy for Gumloop affiliate campaign"  
GHOST/CONTAM: "workflow automation"

Niche: `mcp_ai_agent`  
Expected scope: MCP server/tool integration for agent runtime behavior.  
ON-NICHE: "integrate MCP tools into a Claude-based support agent"  
DRIFT: "design a mascot logo for an AI agent product"  
GHOST/CONTAM: "AI agent"

Niche: `python_automation`  
Expected scope: Python scripts and bot automation for repeatable tasks.  
ON-NICHE: "build a Python script to automate CSV reconciliation"  
DRIFT: "create Python tutorial thumbnails for YouTube"  
GHOST/CONTAM: "python services"

Niche: `ai_tool_llm_integration`  
Expected scope: API-level LLM/tool integrations for existing products.  
ON-NICHE: "integrate OpenAI API into an existing internal dashboard"  
DRIFT: "generate AI art prompts for Etsy prints"  
GHOST/CONTAM: "OpenAI help"

Niche: `ai_agent_development`  
Expected scope: production AI-agent behavior, orchestration, and tool usage.  
ON-NICHE: "build a LangChain agent that triages support tickets"  
DRIFT: "manage a Discord community for AI agent enthusiasts"  
GHOST/CONTAM: "agent development"

Niche: `workflow_automation`  
Expected scope: n8n/Make/Zapier workflow automation and integration logic.  
ON-NICHE: "create a Make scenario for Shopify order escalation"  
DRIFT: "design infographic assets for workflow training"  
GHOST/CONTAM: "automation"

Niche: `python_web_scraping`  
Expected scope: Python web scraping/data extraction scripting.  
ON-NICHE: "build a BeautifulSoup scraper for competitor pricing pages"  
DRIFT: "write SEO blog posts about web scraping tools"  
GHOST/CONTAM: "scraping"

## 10) Glossary (Cycle 055 standard)

- Hypothesis: candidate idea (buyer + deliverable + niche) before keyword candidacy.
- Candidate keyword: hypothesis surviving Gate 1 and entering Gate 2 pre-validation.
- VALID/GHOST/CONTAMINATED: Gate 2 verdict classes from R2 relevance signals.
- INVALID outcome: ghost/contaminated discovery outcome (distinct from MISS).
- RSV: result-set relevance score from R2 validator.
- Rejection rate: rejected candidates divided by total candidates, toggle ON.
- Toggle-OFF parity: pre-R6 behavior preserved exactly when gate toggle is false.
- Tier-1 gate: R4 + R6 + R9 complete before discovery activation decision.
