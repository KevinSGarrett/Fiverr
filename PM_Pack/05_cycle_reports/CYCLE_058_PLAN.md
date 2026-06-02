# CYCLE 058 PLAN — R7 External Signal Integrity (Wave H)

## Control Plane
- Cycle branch: `cycle/058/integration`
- Branch base anchor: `6366cba75e7ab03d2dc338ec3535fe3ed394bcc1`
- Current `origin/develop`: `6366cba75e7ab03d2dc338ec3535fe3ed394bcc1`
- Jira control task: `SCRUM-1012`
- R7 stories: `SCRUM-620`, `SCRUM-847`, `SCRUM-623`, `SCRUM-621`, `SCRUM-851`, `SCRUM-622`, `SCRUM-854`, `SCRUM-858`
- Draft PR: `TBD (open after first governance commit lands)`
- C058 squash SHA: `TBD (Agent D)`

## Hard Gate Contract (Pass-through)
- G-001: ENFORCED = CI `Lint, Typecheck, Tests, and Gates` + `codecov/project`; `codecov/patch` advisory only (must be surfaced/documented).
- G-002: Codex unresolved query TWICE; unresolved=0 with real fixes.
- G-003: Agent D merge-gate all PASS before squash merge.
- G-004: Exactly one `--cov=src` run, owned by Agent D only.
- G-005: toggle-OFF parity equals legacy; kw110 ~= `62.7/1.0/CONDITIONAL_GO`; baseline `data/cycle037_live.db` untouched.
- Config gate in committed `config.yaml`: `scrapfly.enabled=false`, `llm_relevance_enabled=false`, `external_signals_enabled=false`.
- §11 parity: any `src/models/*.py` edit requires B parity table + C PRAGMA cross-check.
- Stage order (§12.2): A(solo) -> B+E(parallel) -> C(after B+E only) -> F(after C GO) -> D(after all).

## Preflight and Baseline Evidence
- PF-1 PASS: `git rev-parse origin/develop` = `6366cba75e7ab03d2dc338ec3535fe3ed394bcc1`.
- PF-2 PASS: top commit = `docs(governance): C057 PM review + ...`.
- PF-3 PARTIAL: branch had one externally locked untracked scratch file `PM_Pack/counts_out.txt` that could not be deleted due active process lock.
- PF-4 PASS: exactly one worktree (`C:/Fiverr/Fiverr`).
- PF-5 PASS: `py -3.12 run.py config-check` -> `Config OK: niches=9`.
- PF-6 PASS: read required SRDI files in order:
  - `PM_Pack/ref/project_plan/13_srdi/03_EPIC_BREAKDOWN_MASTER.md`
  - `PM_Pack/ref/project_plan/13_srdi/04_DOD_AND_ACCEPTANCE.md`
  - `PM_Pack/ref/project_plan/13_srdi/06_TEST_PLAN_REGRESSION.md`
  - `PM_Pack/ref/project_plan/13_srdi/07_SEQUENCING_ROADMAP.md`
  - `PM_Pack/ref/project_plan/06_analysis/`
- PF-7 PASS: `ExternalSignal OK` import check.
- PF-8 PASS: `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md` §12 read.

## Task 1 — R7 Spec Extraction
### R7 Story Keys, Titles, Owning Modules
- `SCRUM-620` — R7.1 Google Trends platform qualifier + storage
  - Modules: `src/collection/workflows/google_trends.py`, `src/scoring/demand.py`, `src/models/external_signal.py`
- `SCRUM-847` — R7.2 Demand consumes qualified Trends + freshness×relevance
  - Modules: `src/scoring/demand.py`, `src/scoring/confidence.py`
- `SCRUM-623` — R7.3 Signal freshness×relevance quality score
  - Modules: `src/scoring/confidence.py`, `src/scoring/pipeline.py`
- `SCRUM-621` — R7.4 Reddit buyer-intent ratio + qualified score
  - Modules: `src/collection/workflows/reddit_signals.py`, `src/scoring/demand.py`
- `SCRUM-851` — R7.5 Demand consumes qualified Reddit
  - Modules: `src/scoring/demand.py`
- `SCRUM-622` — R7.6 YouTube category-legitimacy gate (confidence, not demand)
  - Modules: `src/collection/workflows/youtube_count.py`, `src/scoring/confidence.py`
- `SCRUM-854` — R7.7 Autocomplete-absence classifier
  - Modules: `src/scoring/demand.py`, `src/collection/workflows/autocomplete.py`
- `SCRUM-858` — R7.8 Confidence freshness×relevance + tests + REG-28/29/30
  - Modules: `src/scoring/confidence.py`, `tests/unit/test_external_signal_integrity.py`

### AC-R7.1..R7.5 (verbatim from DoD file)
- AC-R7.1: `Trends qualifier (0.65 base + modifiers) computed, clamped [0.20,0.95], applied before demand`
- AC-R7.2: `Reddit qualified score = raw×(0.40+0.60×ratio); lower than raw when intent low`
- AC-R7.3: `YouTube weight 0; <10 deducts confidence, ≥500 adds confidence`
- AC-R7.4: `Autocomplete emerging→50 / not_searched→0 / unknown→20 (shared classifier)`
- AC-R7.5: `Freshness×relevance geometric mean; fresh+irrelevant scores low`

### REG and Test-File Contract
- REG-28: `test_autocomplete_emerging_keyword_gets_neutral_not_zero_score`
- REG-29: `test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low`
- REG-30: `test_trends_platform_qualifier_applied_before_demand_score_calculation`
- Target file: `tests/unit/test_external_signal_integrity.py` with 10 tests total in the test plan.

### Tier Gate Confirmation
- `PM_Pack/ref/project_plan/13_srdi/07_SEQUENCING_ROADMAP.md` §3 confirms Tier-2 gate closes only when both R5 and R7 are complete.

### Base Analysis Reference
- Base analysis docs in `PM_Pack/ref/project_plan/06_analysis/` do not define concrete external-signal scoring formulas for R7; implementation authority remains SRDI R7 specs + existing scoring modules.

## Task 2 — Baseline Codebase Checks
- 2a PASS: `py -3.12 run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci.db`
- 2b PASS: `py -3.12 run.py phase2-smoke` (all 3 OK)
- 2c PASS: kw110 probe = `(62.7, 1.0, 'CONDITIONAL_GO')`
- 2d PASS: `ExternalSignal.__table__.columns`:
  - `keyword_id`, `signal_type`, `signal_value`, `signal_json`, `source_url`, `collected_at`, `ttl_hours`, `is_stale`, `run_id`, `collection_method`, `error_message`, `id`, `created_at`, `updated_at`
- 2e PASS: `external_signals_enabled` currently absent in committed `config.yaml` (`False` check result).

## Task 3 — Existing External Signal Handling Map
### Primary existing paths
- `src/scoring/demand.py`
- `src/collection/workflows/google_trends.py`
- `src/collection/workflows/reddit_signals.py`
- `src/collection/workflows/youtube_count.py`
- `src/collection/workflows/autocomplete.py`
- `src/collection/external_signals.py`

### Demand calculator
- File: `src/scoring/demand.py`
- Class/function: `DemandScoreCalculator.calculate(...)`
- Current Trends contribution point: `trends_12mo_score` -> `trends_score = min(100.0, trends_12mo_score * 1.15)` before weighted add.

### Existing autocomplete classifier
- Present in `src/scoring/demand.py`:
  - `_classify_autocomplete_state(...)`
  - `_autocomplete_state_multiplier(...)`
- R7 requires replacing/extending this path with `_classify_autocomplete_absence(...)`.

### File-impact map by signal type (for B)
- Google Trends (AC-R7.1, R7.2): modify `src/scoring/demand.py` (+ optionally `src/collection/workflows/google_trends.py`)
- Reddit (AC-R7.2, R7.5): modify `src/collection/workflows/reddit_signals.py` and `src/scoring/demand.py`
- YouTube (AC-R7.3): modify `src/scoring/confidence.py` (+ read from `src/collection/workflows/youtube_count.py`)
- Autocomplete (AC-R7.4): modify `src/scoring/demand.py` (classifier and scoring path), align with `src/collection/workflows/autocomplete.py`
- Freshness×relevance (AC-R7.5): add/modify quality utility in `src/scoring/confidence.py` (or shared scoring util referenced by confidence).

## Task 4 — Jira Control and Story Confirmation
- Control task created: `SCRUM-1012` (`Cycle 058 (R7) control`)
- All 8 stories verified and not Done (all `To Do`)
- No story found pre-marked as Done.
- All 8 stories linked to `SCRUM-1012` via `Relates`.

## Task 5 — Branch and PR
- Branch created from `origin/develop`: `cycle/058/integration`
- Branch pushed to origin (tracking set).
- PR creation initially blocked by GitHub 422 due no branch diff yet; PR is created after governance commit in this cycle.

## Task 6 — Pinned R7 Implementation Contracts
- Toggle key to add:
  - Key: `external_signals_enabled`
  - Type: bool
  - Default: `false`
  - Live activation: local `config.live.yaml` sets `external_signals_enabled: true`
- Trends formula (AC-R7.1):
  - `trends_qualifier = clamp(0.65 + modifiers, 0.20, 0.95)`
  - Applied BEFORE demand score calculation (not after demand score computed).
- Reddit formula (AC-R7.2):
  - `qualified = raw_score * (0.40 + 0.60 * buyer_intent_ratio)`
  - `buyer_intent_ratio in [0, 1]`
- YouTube behavior (AC-R7.3):
  - Demand weight = `0`
  - `youtube_video_count < 10` => confidence deduction
  - `youtube_video_count >= 500` => confidence boost
- Autocomplete classifier (AC-R7.4):
  - `_classify_autocomplete_absence(keyword, niche) -> {emerging: 50, not_searched: 0, unknown: 20}`

## Task 14 — Migration Expectation (§11)
- Determination: R7 qualifiers are computed at scoring time; no new persistence columns are strictly required for contract completion.
- Therefore: `§11 not required for R7 unless B decides to persist new model columns`.
- If B touches `src/models/*.py`, §11.2 parity table becomes mandatory.
- Migration registry check PASS: `src/migrations/srdi_r8/migration_01` through `migration_10` present.
- Reserved name if needed later: `migration_11_external_signal_qualifiers.py`.

## Task 17 — .gitignore R7 Artifacts
- `*.log` ignored: YES.
- `config.live.yaml` ignored: YES.
- `*.db` ignored: YES (`data/**/*.db` and related patterns).
- Added specific R7 artifact ignore: `external_signal_cache.json`.

## Task 18 — Existing Qualifier Pattern
- Existing patterns found:
  - `src/scoring/demand.py` `_trends_platform_qualifier(...)`
  - `src/scoring/opportunity.py` `_opportunity_relevance_qualifier(...)`
  - `src/scoring/intent.py` opportunity qualifier toggling path
- Implementation pattern to follow for B:
  - Isolated helper function + clamp + additive modifiers + explicit fallback behavior.

## Task 19 — Freshness×Relevance Formula Contract
- Formula pinned:
  - `quality_score = sqrt(freshness_score * relevance_score)`
  - `freshness_score in [0,1]`, `relevance_score in [0,1]`
- Numeric anchors:
  - `sqrt(0.10 * 0.95) ~= 0.308` (fresh + irrelevant => low)
  - `sqrt(0.90 * 0.95) ~= 0.924` (fresh + high relevance => high)
- Freshness decay reference:
  - No dedicated `freshness_decay` in `src/analysis/`.
  - Existing freshness behavior observed in `src/scoring/confidence.py` as linear age decay over TTL; B should implement explicit R7 signal freshness function for AC-R7.5.

## Task 20 — Agent D Regression Pack (31-name expression)
- Base 28-name permanent pack (strategy §7 v2.0), plus:
  - `test_autocomplete_emerging_keyword_gets_neutral_not_zero_score` (REG-28)
  - `test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low` (REG-29)
  - `test_trends_platform_qualifier_applied_before_demand_score_calculation` (REG-30)
- Expected post-C058: 31 names, 39 passed.
- Strategy update target post-merge: §7 `v2.1` (owned by D).

## Task 21 — OpenAI Key Advisory
- R7 itself is rule-based and does not require OpenAI.
- Advisory check result: `OPENAI_API_KEY` present (`R5 key present`).
- No new LLM budget concerns introduced by R7.

## Task 22 — Tier-2 Proximity Note
- R7 is final Tier-2 epic after R5.
- Post-merge expectation: D confirms Tier-2 gate CLOSED and announces transition to Tier-3 (R10 Dashboard).

## Task 23 — Baseline Regression Spot Checks
- Targeted 28-pack smoke (`-k eligibility_ghost_hard_block ...`): PASS (`4 passed`).
- `tests/unit/test_llm_relevance.py`: PASS (`33 passed` in current repo state).
- Recorded baseline state: pre-R7 regressions remain green on develop anchor.

## Architecture and Stage Order (§12.2, Task 24)
- B: Stage 2 (parallel with E)
- E: Stage 2 (parallel with B)
- C: Stage 3 (after BOTH B and E, NOT after F)
- F: Stage 4 (after C GO)
- D: Stage 5 (after all 5)

---

## Agent B Handoff — Stage 2 (parallel with E)
**PARALLEL EXECUTION NOTICE — YOU ARE RUNNING IN PARALLEL WITH AGENT E. E's commits WILL appear in git log. DO NOT halt.**

### Zone
- B commits ONLY `src/` files + `CYCLE_058_AGENT_B.md` + `tests/unit/test_external_signal_integrity.py`.

### Files to MODIFY vs CREATE
- MODIFY:
  - `src/scoring/demand.py`
  - `src/scoring/confidence.py`
  - `src/collection/workflows/google_trends.py` (if signal payload fields needed)
  - `src/collection/workflows/reddit_signals.py`
  - `src/config/models.py` (if config schema requires toggle wiring)
  - `config.yaml` (add `external_signals_enabled: false`)
- CREATE:
  - `tests/unit/test_external_signal_integrity.py` (10 tests including REG-28/29/30)
  - `docs/cycle_reports/CYCLE_058_AGENT_B.md`

### Toggle contract
- Key: `external_signals_enabled`
- Type: `bool`
- Default: `false`
- Config location: analysis/signals section consistent with existing config structure.

### Formula contracts (verbatim)
- Trends: `trends_qualifier = clamp(0.65 + modifiers, 0.20, 0.95)` before demand calculation.
- Reddit: `qualified = raw_score * (0.40 + 0.60 * buyer_intent_ratio)`.
- YouTube: demand weight `0`; `<10` deduction; `>=500` boost in confidence path.
- Autocomplete classifier output:
  - `emerging -> 50`
  - `not_searched -> 0`
  - `unknown -> 20`
- Freshness×relevance: `sqrt(freshness_score * relevance_score)`.

### Required signatures
```python
def _compute_fiverr_relevance_qualifier(
    rsv: float, is_fiverr_relevant: bool, trend_direction: str
) -> float: ...

def _qualify_reddit_score(raw_score: float, buyer_intent_ratio: float) -> float: ...

def _classify_autocomplete_absence(keyword: str, niche: str) -> int: ...

def compute_signal_freshness_quality(signal_age_days: int, relevance_score: float) -> float: ...
```

### Test/REG requirements
- New file `tests/unit/test_external_signal_integrity.py` with 10 tests total.
- Must include exact tests:
  - `test_autocomplete_emerging_keyword_gets_neutral_not_zero_score` (REG-28)
  - `test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low` (REG-29)
  - `test_trends_platform_qualifier_applied_before_demand_score_calculation` (REG-30)

### Migration/parity rule
- If any model file changes (`src/models/*.py`), §11.2 all-YES parity table required before commit.

### Golden/config gate reminders
- G-005 must pass with `external_signals_enabled=false` (toggle OFF parity).
- Committed `config.yaml` must remain default-off for all toggles.

### Implementation pattern to follow
- Follow existing qualifier helpers in `src/scoring/demand.py` and `src/scoring/opportunity.py`:
  - helper function
  - bounded clamp
  - explicit fallback values
  - transparent note fields in score components.

### §11 expectation for R7
- No mandatory migration expected for R7 unless B introduces new persisted columns.

---

## Agent E Handoff — Stage 2 (parallel with B)
**PARALLEL EXECUTION NOTICE — YOU ARE RUNNING IN PARALLEL WITH AGENT B. B's commits WILL appear in git log. DO NOT halt.**

### Zone
- E commits ONLY `CYCLE_058_AGENT_E.md`.
- Zone verification MUST use `git show --name-only <OWN_SHA>` only.
- NEVER use `git diff origin/develop..HEAD` for zone checks.

### Scope (C058)
- PRIMARY: validate whether live pipeline emits `external_signals` rows for Trends/Reddit/YouTube.
- SECONDARY: RSV band calibration.
- E must not call external signal APIs directly; run pipeline and inspect DB outputs.

### ScrapFly runbook (strategy §10.5, verbatim contract)
- ScrapFly is required for live Fiverr fetch.
- Keep committed `config.yaml` scrapfly disabled.
- Use local uncommitted `config.live.yaml` with ScrapFly enabled for live run.
- If live unavailable, report `[SEED]` fallback; do not fabricate data.

### Required diagnostic query
```bash
py -3.12 -c "
from sqlalchemy import create_engine
e=create_engine('sqlite:///data/cycle058_e2e_validation.db')
r=e.connect().exec_driver_sql(
  'SELECT signal_type, COUNT(*) n, AVG(raw_value) avg_val FROM external_signals GROUP BY signal_type'
).fetchall()
for row in r: print(row)
"
```

---

## Agent C Handoff — Stage 3 (after BOTH B and E, NOT after F)
- Verify `ruff`, `mypy`, 31-name regression pack (28+3), golden parity, config gate, and §11.3 PRAGMA if models touched.
- New regression gate: REG-28/29/30 must PASS.
- Verify committed `config.yaml` contains `external_signals_enabled=false`.
- Expected regression math after B:
  - names: 31
  - passed count: 39

---

## Agent F Handoff — Stage 4 (after C GO)
- Focus: fill coverage gaps in `tests/unit/test_external_signal_integrity.py` left by B.
- Verify all 10 test functions in the R7 file are collected and PASS.
- Zone: commit ONLY `tests/` + `CYCLE_058_AGENT_F.md`.

---

## Agent D Handoff — Stage 5 (after all 5 agents)
- Runs full merge gate after A+B+E+C+F completion.
- Includes §12.3 operational playbook:
  - PR size >1000 lines => apply `override:large-pr`
  - Codex unresolved check twice
  - `codecov/patch` advisory handling
  - mergeable_state interpretation
- Confirms:
  - Golden parity with `external_signals_enabled=false`
  - Baseline DB `data/cycle037_live.db` untouched
  - Jira closeout: `SCRUM-620/847/623/621/851/622/854/858` + control `SCRUM-1012` -> Done
- Post-merge:
  - update strategy §7: add REG-28/29/30 -> `v2.1`
  - permanent pack becomes 31 names
  - announce Tier-2 gate CLOSED (R5 + R7 green)
  - note next active tier: Tier-3 (R10 Dashboard)

### Full 31-name expression for D
`test_extract_price_text_from_payload_uses_nested_price_amount or test_parse_gig_detail_from_html_keeps_zero_review_count or test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration or test_seller_profile_fetcher_maps_parser_fields_for_persistence or test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields or test_seller_profile_live_markup_drift_regression_spec or test_scoring_fallback_queries_scope_to_active_run_id or test_scoring_fallback_queries_recover_when_latest_run_unlinked or test_demand_uses_search_result_total_result_count_when_available or test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch or test_scoring_uses_card_urls_with_querystrings_for_sparse_links or test_confidence_modifier_uses_current_run_context_not_none or test_weakness_multi_row_fallback_does_not_produce_extreme_value or test_fiverr_search_url_always_includes_category_filter_for_production_niches or test_unconstrained_search_result_applies_demand_confidence_deduction or test_eligibility_ghost_hard_block_even_when_forced or test_demand_qualified_trc_when_rsv_below_080 or test_sponsored_gigs_never_included_in_competition_top10 or test_zombie_gigs_never_used_in_feasibility_review_barrier or test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent or test_niche_profile_excludes_contaminated_keywords or test_opportunity_qualified_by_relevance or test_price_outlier_excluded_from_competition_and_profitability or test_ghost_discovery_recorded_as_invalid_not_miss or test_feedback_excludes_contaminated_outcomes or test_low_specificity_hypothesis_rejected or test_llm_relevance_only_triggers_in_ambiguous_band or test_llm_ghost_verdict_blocks_recommendation or test_autocomplete_emerging_keyword_gets_neutral_not_zero_score or test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low or test_trends_platform_qualifier_applied_before_demand_score_calculation`

## Post-merge Activation Advisory (operator decision)
- Keep committed `external_signals_enabled=false`.
- First live activation on one niche only (suggest `python_automation`) via local `config.live.yaml`.
- Compare toggle-OFF vs toggle-ON for same niche before broad rollout.

## Completion Checklist (Task 25)
- [x] All 5 SRDI spec files read
- [x] ExternalSignal model import and columns recorded
- [x] Existing signal handler files located and documented
- [x] Baseline checks pass (foundation/smoke/kw110)
- [x] Tier position confirmed (R5 done, R7 current)
- [x] Control task created (`SCRUM-1012`)
- [x] R7 stories confirmed not Done
- [x] Cycle branch created and pushed
- [x] R7 contracts pinned (Trends/Reddit/YouTube/Autocomplete/Freshness)
- [x] Plan includes stage order, formulas, parallel notices, and all handoffs
- [x] Agent A report authored (`docs/cycle_reports/CYCLE_058_AGENT_A.md`)
- [x] Start signal: Agent A complete; B + E may start in parallel (after governance push + PR open)
