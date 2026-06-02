# CYCLE 057 PLAN — R5 LLM Relevance Classification (Stage 7.5)

## Control Plane
- Cycle branch: `cycle/057/integration`
- Branch base anchor for R5 work: `3617ce4a33ec4e6c2d614d2578de7c90b0cb3cd3` (C056 squash)
- Current `origin/develop`: `c6139a6ff71d0d52b6771e77cdaf852f2f752297` (post-C056 governance commit)
- Jira control task: `SCRUM-1011`
- R5 stories in scope: `SCRUM-624`, `SCRUM-816`, `SCRUM-625`, `SCRUM-823`, `SCRUM-830`, `SCRUM-835`, `SCRUM-841`
- Draft PR: TBD (created after first governance commit)
- C057 squash SHA: TBD (Agent D)

## Hard Gate Contract (Pass-through to All Agents)
- G-001 COVERAGE GATE: ENFORCED = CI "Lint, Typecheck, Tests, and Gates" + `codecov/project`; `codecov/patch` advisory only.
- G-002: Agent D runs Codex GraphQL unresolved-thread query twice; unresolved=0 required.
- G-003: Agent D merge-gate all PASS before squash merge.
- G-004: Exactly one `--cov=src` run, owned by Agent D only.
- G-005 GOLDEN PARITY: toggle-OFF run equals legacy; kw anchors drift <=2; kw110 remains `62.7/1.0/CONDITIONAL_GO`.
- CONFIG GATE: committed `config.yaml` keeps `scrapfly.enabled=false` and `relevance.llm_relevance_enabled=false`.
- §11 PARITY: any `src/models/*.py` edit requires all-YES parity table before commit.
- §12.2 STAGE ORDER: A(solo) -> B+E(parallel) -> C(after B+E) -> F(after C GO) -> D(after all).
- §12.3 D PLAYBOOK: apply `override:large-pr` label when needed; codex x2; patch coverage advisory.

## Preflight Evidence Snapshot
- PF-1: `git rev-parse origin/develop` => `c6139a6ff71d0d52b6771e77cdaf852f2f752297` (note: differs from prompt baseline because a post-merge docs commit landed after C056).
- PF-2: top 5 includes C056 squash commit `3617ce4 feat(testing): R9 testing framework + Tier-1 gate closure (#65)`.
- PF-3: working tree not clean at start (existing PM local changes predated Agent A).
- PF-4: worktree list shows one worktree: `C:/Fiverr/Fiverr`.
- PF-5: `py -3.12 run.py config-check` PASS, niches=9.
- PF-6/PF-7/PF-8: sequencing roadmap, epic breakdown, and strategy §12 read.

## Tier/Gate and C056 Confirmation
- `docs/tier1_gate_ceremony.md` exists and was included in C056 squash commit file list.
- R9 stories `SCRUM-630/631/632/633/880/883/886/893`: all `Done`.
- `SCRUM-22` status: `Done`.
- C056 authoritative squash SHA recorded in `docs/cycle_reports/CYCLE_056_AGENT_D.md`: `3617ce4a33ec4e6c2d614d2578de7c90b0cb3cd3`.

## R5 Specification Extraction (authoritative for C057)
- New module target: `src/analysis/llm_relevance_classifier.py`.
- New toggle key: `relevance.llm_relevance_enabled`.
- Trigger band for Stage 7.5: RSV >= 0.40 and RSV < 0.70.
- Call budget cap: <=50 LLM calls per scoring run.
- Graceful degrade contract:
  - OpenAI unavailable / missing key / API error => log + treat keyword as `RELEVANT`.
  - Call budget exhausted => stop further LLM calls and treat remaining ambiguous keywords as `RELEVANT`.
  - Never crash or block run from LLM failures.
- New permanent regressions for C057:
  - REG-23: `test_llm_relevance_only_triggers_in_ambiguous_band`
  - REG-24: `test_llm_ghost_verdict_blocks_recommendation`

## File-Impact Map
### Create
- `src/analysis/llm_relevance_classifier.py`
- `src/analysis/stage_7_5_orchestrator.py` (or equivalent wiring module)
- `tests/unit/test_llm_relevance.py`
- `docs/cycle_reports/CYCLE_057_AGENT_B.md`
- `docs/cycle_reports/CYCLE_057_AGENT_E.md`
- `docs/cycle_reports/CYCLE_057_AGENT_C.md`
- `docs/cycle_reports/CYCLE_057_AGENT_F.md`
- `docs/cycle_reports/CYCLE_057_AGENT_D.md`

### Modify
- `config.yaml` (toggle key default false)
- `src/config/models.py` (add `LLMRelevanceConfig` + wiring)
- pipeline wiring module between Stage 7 and Stage 8
- strategy §7 after merge (Agent D post-merge)

### Skip / Protected
- `data/cycle037_live.db` (must remain untouched)
- `.env` (never committed)
- committed `config.live.yaml` (must remain untracked)

## OpenAI and Integration Path
- OPENAI_API_KEY status: present (env prefix `sk-`, `.env` also present with `sk-` prefix).
- Existing OpenAI/LLM integration already exists in `src/llm/client.py` and `src/llm/provider.py`; Agent B should reuse this path rather than creating a duplicate raw client layer.
- Reuse preference: wrap Stage 7.5 classifier over existing `LLMClient`/provider abstraction.

## Migration Assessment (§11)
- Existing SRDI migrations present: `migration_01` through `migration_10` in `src/migrations/srdi_r8/`.
- R5 expectation for C057: no mandatory new DB columns if verdict remains runtime annotation or existing structures are reused.
- If Agent B introduces any new persisted column (e.g., verdict storage), B must add migration and include §11.2 parity table; C must enforce §11.3 PRAGMA cross-check.

## Baseline Checkpoint (C057 start)
- `foundation-gate`: PASS
- `phase2-smoke`: PASS (3 checks OK)
- Golden anchor DB probe (`keyword_id=110`): `(62.7, 1.0, 'CONDITIONAL_GO')`
- Config gate check: `relevance.llm_relevance_enabled` currently `NOT SET` (to be added default false by Agent B)

## Toggle Inventory (R5)
- Key: `relevance.llm_relevance_enabled`
- Type: bool
- Default in committed config: false
- Activation path: local `config.live.yaml` only for live runs
- Non-toggle config field: `call_budget_per_run` (integer, default 50)
- Forbidden state in committed branch: `enabled: true`

## Architecture and Stage Order (§12.2 / §23)
- Agent A: Stage 1 (solo)
- Agent B: Stage 2 (parallel with E)
- Agent E: Stage 2 (parallel with B)
- Agent C: Stage 3 (after BOTH B and E, NOT after F)
- Agent F: Stage 4 (after C GO)
- Agent D: Stage 5 (after all 5 agents)

---

## Agent B Handoff (Stage 2, parallel with E)
**PARALLEL EXECUTION NOTICE — YOU ARE RUNNING IN PARALLEL WITH AGENT E.**
Agent E commits only its report file and those commits WILL appear in `git log`. This is expected; do not halt.

### Zone
- Commit ONLY `src/` changes + `docs/cycle_reports/CYCLE_057_AGENT_B.md`.

### Build Contract
- Add `relevance.llm_relevance_enabled` (default false) to config surface.
- Add `LLMRelevanceConfig` dataclass/config model with:
  - `enabled: bool = False`
  - `call_budget_per_run: int = 50`
  - `model: str = "gpt-4o-mini"`
  - `trigger_band_low: float = 0.40`
  - `trigger_band_high: float = 0.70`
- Create `src/analysis/llm_relevance_classifier.py` (`LLMRelevanceClassifier`).
- Create Stage 7.5 orchestrator module (`src/analysis/stage_7_5_orchestrator.py`) or equivalent pipeline wiring between Stage 7 and Stage 8.
- Locate and reuse prompt context constants where `NICHE_EXPECTED_SERVICE_DESCRIPTIONS` belongs; include all 9 niches.
- Reuse existing LLM stack from `src/llm/client.py` + `src/llm/provider.py`.

### Required Function Signatures
```python
def _should_run_llm(rsv_score: float, band_low: float = 0.40, band_high: float = 0.70) -> bool: ...
def classify_gig_relevance(gig_titles: list[str], niche_id: str, client: OpenAI) -> str: ...
def run_stage_7_5(keyword_id: int, engine: Engine, config: LLMRelevanceConfig) -> None: ...
```

### Safety Contract (verbatim)
- Call budget: <=50 LLM API calls per `run_stage_7_5()` invocation.
- Keep a per-run counter; when exhausted, do not call LLM for remaining ambiguous keywords.
- If OpenAI unavailable OR budget exhausted OR any OpenAI API error: log and return `RELEVANT`.
- Parse failures also degrade to `RELEVANT`.
- Never raise through scoring pipeline from classifier path.

### Test Stubs / Regressions
- `test_llm_relevance_only_triggers_in_ambiguous_band` (REG-23)
- `test_llm_ghost_verdict_blocks_recommendation` (REG-24)

### §11.2 parity reminder
- If any `src/models/*.py` is touched, include full all-YES model/migration parity table before commit.

---

## Agent E Handoff (Stage 2, parallel with B)
**PARALLEL EXECUTION NOTICE — YOU ARE RUNNING IN PARALLEL WITH AGENT B.**
Agent B commits `src/` changes and those commits WILL appear in `git log`. This is expected; do not halt.

### Zone
- Commit ONLY `docs/cycle_reports/CYCLE_057_AGENT_E.md`.
- Zone verification command: `git show --name-only <YOUR_OWN_SHA>` (never `git diff origin/develop..HEAD`).

### Validation Scope
- Validate real RSV distribution in throwaway DB to calibrate trigger gate for ambiguous band.
- Do NOT call LLM API (cost control). Report only distribution evidence.
- ScrapFly policy: follow strategy §10.5; use `config.live.yaml` for live enablement; if unavailable mark `[SEED]` fallback.

### Required Query
```bash
py -3.12 -c "
from sqlalchemy import create_engine
e = create_engine('sqlite:///data/cycle057_e2e_validation.db')
r = e.connect().exec_driver_sql('SELECT COUNT(*) total, SUM(CASE WHEN result_set_relevance_score >= 0.40 AND result_set_relevance_score < 0.70 THEN 1 ELSE 0 END) in_band FROM result_set_validations').fetchone()
print(f'Total RSV rows: {r[0]}, In ambiguous band (0.40-0.70): {r[1]}, Rate: {r[1]/r[0]:.3f}' if r[0] else 'No RSV data')
"
```

---

## Agent C Handoff (Stage 3, after B+E)
- Runs AFTER both B and E are complete; does NOT wait for F.
- Verify B parity audit, `ruff`, `mypy`, regressions, golden parity, config gate, and §11.3 PRAGMA if models touched.
- Must verify committed toggle `relevance.llm_relevance_enabled` defaults false.
- Confirm REG-23 and REG-24 are present and passing.
- C does NOT verify F fixture/coverage additions.

---

## Agent F Handoff (Stage 4, after C GO)
- Starts only after Agent C issues GO.
- Scope: add coverage for new R5 modules and uncovered branches from B changes.
- Must run `pytest --collect-only` and verify REG-23/24 are collected.
- Must verify test fixtures/mocks prevent live OpenAI API calls.
- Zone: commit ONLY `tests/` + `docs/cycle_reports/CYCLE_057_AGENT_F.md`.

---

## Agent D Handoff (Stage 5, after all agents)
- Verify full merge gate package G1-G10 plus §12.3 operational playbook.
- For PR >1000 changed lines, apply label:
  - `gh api -X POST repos/KevinSGarrett/Fiverr/issues/<PR>/labels --field "labels[]=override:large-pr"`
- Run Codex unresolved-thread GraphQL query twice and record both runs.
- Treat `codecov/patch` as advisory if project floor passes.
- Post-merge Jira transitions to Done:
  - `SCRUM-624`, `SCRUM-816`, `SCRUM-625`, `SCRUM-823`, `SCRUM-830`, `SCRUM-835`, `SCRUM-841`, `SCRUM-1011`
- Update strategy §7 with REG-23/24 after merge.

### Regression pack expectation after C057 merge
- Permanent names: 28 (previous 26 + REG-23 + REG-24)
- Expected passed count: 36 (26 prior names + 2 new + 8 supersets)

### Full 28-name expression for D
`test_extract_price_text_from_payload_uses_nested_price_amount or test_parse_gig_detail_from_html_keeps_zero_review_count or test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration or test_seller_profile_fetcher_maps_parser_fields_for_persistence or test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields or test_seller_profile_live_markup_drift_regression_spec or test_scoring_fallback_queries_scope_to_active_run_id or test_scoring_fallback_queries_recover_when_latest_run_unlinked or test_demand_uses_search_result_total_result_count_when_available or test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch or test_scoring_uses_card_urls_with_querystrings_for_sparse_links or test_confidence_modifier_uses_current_run_context_not_none or test_weakness_multi_row_fallback_does_not_produce_extreme_value or test_fiverr_search_url_always_includes_category_filter_for_production_niches or test_unconstrained_search_result_applies_demand_confidence_deduction or test_eligibility_ghost_hard_block_even_when_forced or test_demand_qualified_trc_when_rsv_below_080 or test_sponsored_gigs_never_included_in_competition_top10 or test_zombie_gigs_never_used_in_feasibility_review_barrier or test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent or test_niche_profile_excludes_contaminated_keywords or test_opportunity_qualified_by_relevance or test_price_outlier_excluded_from_competition_and_profitability or test_ghost_discovery_recorded_as_invalid_not_miss or test_feedback_excludes_contaminated_outcomes or test_low_specificity_hypothesis_rejected or test_llm_relevance_only_triggers_in_ambiguous_band or test_llm_ghost_verdict_blocks_recommendation`

---

## C057 Completion Checklist
- [x] Branch `cycle/057/integration` created and pushed
- [x] Baseline checks PASS (`foundation-gate`, `phase2-smoke`, kw110 anchor)
- [x] C056 Tier-1 stories verified Done in Jira
- [x] Control task created (`SCRUM-1011`)
- [x] R5 stories verified present and not Done
- [x] OpenAI key status verified (`present`, prefix `sk-`)
- [ ] Draft PR opened (blocked until first commit exists)
- [x] All 6 handoff packages written in this plan
- [ ] Hydration header updated local-only with PR number
- [ ] Governance commit pushed
- [ ] Agent A report committed and pushed
- [ ] Start signal issued: Agent A complete; B+E parallel may begin
