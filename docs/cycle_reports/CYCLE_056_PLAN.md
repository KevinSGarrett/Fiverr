# CYCLE 056 PLAN — R9 Tier-1 Gate Closure

## Branching and Base
- Branch: `cycle/056/integration`
- Base branch: `develop`
- Verified develop/base SHA: `3689b3197992685a4c82c6dcbcfcc816dbab787d`
- C055 merge verification:
  - PR `#64`: merged=`true`, state=`closed`
  - C055 squash commit on develop: `fabdca9 feat(discovery): R6 relevance gates (toggle off) (#64)`
- Current branch HEAD: `3689b3197992685a4c82c6dcbcfcc816dbab787d` (matches develop at branch creation)
- Worktree verification: exactly one worktree (`C:/Fiverr/Fiverr`)

## PR
- PR number: `#65`
- Title: `feat(testing): R9 testing framework + Tier-1 gate closure (toggle N/A)`
- Base/head: `develop <- cycle/056/integration`

## Scope
- Primary cycle scope: SRDI R9 (Testing & Validation Framework)
- Secondary required scope: §11.5 one-time retroactive model-migration parity audit (all 9 model targets)
- Governance scope: Tier-1 gate ceremony preparation and activation decision framework documentation
- Non-goal: no net-new product features; no non-audit `src/` logic expansion

## Baseline Snapshot at C056 Start
- Regression pack file-scoped run: `739 passed`
- Full collection count: `3829 tests collected`
- Smoke checks: `config-check`, `foundation-gate`, `phase2-smoke` all pass
- Config gate:
  - `collection.scrapfly.enabled: false` in committed `config.yaml`
  - `discovery.enable_relevance_gates: false` in committed `config.yaml`
- Golden OFF parity at cycle start: `PASS`
  - `kw=110`: `62.7 / 1.0 / CONDITIONAL_GO`
  - `kw=96`: `35.8 / CAUTION`
  - `kw=3`: `56.66 / MONITOR`
- Baseline DB integrity: `data/cycle037_live.db` kw110 anchor confirmed `(62.7, 1.0, 'CONDITIONAL_GO')`

## R9 Audit Results (Agent A)

### Test-structure gap table for Agent F
| R9 Story | Files Expected | Files Present | Gap? |
|---|---|---|---|
| R9.2 (R1/R2 unit) | `test_search_url_builder.py`, `test_result_set_validator.py` | Both present | No |
| R9.3 (R3 unit) | `test_zombie_gig_detector.py`, `test_sponsored_gig_filtering.py` | `test_zombie_gig_detector.py` present; `test_sponsored_gig_filtering.py` missing | **Yes** |
| R9.4 (R4/R6 unit) | `test_demand_score_extended.py`, `test_opportunity_extended.py`, `test_discovery_relevance_gates.py` (+ others) | Present | No (baseline coverage already present) |
| R9.5 (integration) | `test_discovery_relevance_gates_integration.py`, `test_fiverr_search_r1_wiring.py`, `test_r3_sponsored_zombie_integration.py`, `test_r2_result_set_validation_integration.py`, `test_r4_scoring_integrity_integration.py` | First two present; last three missing | **Yes** |
| R9.6 (fixtures) | `tests/fixtures/relevance_fixtures.py`, `tests/fixtures/contaminated_data_fixtures.py` | Neither present (`tests/fixtures/` exists) | **Yes** |
| R9.8 (guard) | `tests/test_suite_guard.py` | Missing | **Yes** |

### Fixture directory state
- `tests/fixtures/` exists.
- Existing files:
  - `tests/fixtures/__init__.py`
  - `tests/fixtures/analysis/__init__.py`
  - `tests/fixtures/analysis/factories.py`
  - `tests/fixtures/dashboard/__init__.py`
  - `tests/fixtures/dashboard/factories.py`

## Agent B Package (Start in parallel with E; do not wait for E)

### Exact §11.5 parity audit instruction
Audit all 9 model targets against migrations and produce a complete parity table:
1. `src/models/discovery_outcome.py` -> `discovery_outcomes`
2. `src/models/keyword_score.py` -> `keyword_scores`
3. `src/models/keyword.py` (actual class is in `src/models/market.py`) -> `keywords`
4. `src/models/gig.py` -> `gigs`
5. `src/models/search_result.py` -> `search_results`
6. `src/models/external_signal.py` -> `external_signals`
7. `src/models/result_set_validation.py` -> `result_set_validations`
8. `src/models/market.py` -> `markets` (if model exists in current tree)
9. `src/models/competitor_profile.py` (actual class is in `src/models/market.py`) -> `competitor_profiles`

### Precomputed model contract map (for B step-1 speed)
| Requested path | Actual location | Table | Mapped[] count |
|---|---|---|---:|
| `src/models/discovery_outcome.py` | same | `discovery_outcomes` | 8 |
| `src/models/keyword_score.py` | same | `keyword_scores` | 30 |
| `src/models/keyword.py` | `src/models/market.py` (`class Keyword`) | `keywords` | 19 |
| `src/models/gig.py` | same | `gigs` | 44 |
| `src/models/search_result.py` | same | `search_results` | 23 |
| `src/models/external_signal.py` | same | `external_signals` | 12 |
| `src/models/result_set_validation.py` | same | `result_set_validations` | 16 |
| `src/models/market.py` | same | `markets` (verify class/table existence during audit) | n/a |
| `src/models/competitor_profile.py` | `src/models/market.py` (`class CompetitorProfile`) | `competitor_profiles` | 15 |

For each model target:
- Enumerate ORM `Mapped[]` columns with type/nullability/default.
- Map each to table creation or `ALTER TABLE ... ADD COLUMN ...` migration evidence.
- Build parity table: `column | orm type | migration file | DDL evidence | present`.
- Any `present=NO`: author `migration_11+` idempotent column-add migration and register in `run_srdi_r8_migrations.py`.
- Validate with `PRAGMA table_info(<table>)` after applying migrations.

### Migration inventory precomputed for B
| Migration | Table(s) touched | Columns / DDL summary |
|---|---|---|
| `migration_01_result_set_validations` | `result_set_validations` | Table create with base RSV columns (`keyword_id`, `run_id`, `validated_at`, counts, relevance, ghost fields, strictness, `per_gig_relevance`, `relevance_deduction`) |
| `migration_02_gigs_srdi_columns` | `gigs` | `is_sponsored`, `is_zombie`, `relevance_flag`, `relevance_score`, `excluded_from_scoring` |
| `migration_03_search_results_srdi_columns` | `search_results` | `search_strictness_used`, `sponsored_gig_count`, `organic_gig_count`, `organic_trc`, `rsv_id` |
| `migration_04_keyword_scores_srdi_columns` | `keyword_scores` | `relevance_validation_applied`, `scoring_method`, `trc_reliability_qualified` |
| `migration_05_keywords_srdi_columns` | `keywords` | `ghost_market_flag`, `discovery_needs_recollection`, `last_relevance_validated_at` |
| `migration_06_discovery_outcomes_srdi_columns` | `discovery_outcomes` | table create + `is_invalid`, `is_contaminated`, `relevance_score`, `contamination_reason` |
| `migration_07_r3_columns` | `gigs`, `search_results` | `zombie_score`, `zombie_signals`, `last_reviewed_at`; `search_results.pages_collected` |
| `migration_08_r2_columns` | `result_set_validations` | `category_contamination_flag`, `used_fallback_strictness` |
| `migration_09_keyword_score_integrity_cols` | `keyword_scores` | `trc_reliability`, `opportunity_relevance_factor`, `price_outliers_excluded`, `clean_gig_count`, `competitor_profile_source` |
| `migration_10_discovery_outcome_context_cols` | `discovery_outcomes` | `run_id`, `niche_id`, `keyword_text`, `created_at` |

### B output contract
- `docs/cycle_reports/CYCLE_056_AGENT_B.md`
- Any required `src/migrations/srdi_r8/migration_11*.py`+
- Updated `src/migrations/srdi_r8/run_srdi_r8_migrations.py` if new migrations are introduced
- Optional `src/testing_support/*` only if fixture support cannot be delivered in pure tests

## Agent E Package (Start in parallel with B; do not wait for B)

### Live validation mission
- Execute live ScrapFly sampling (local uncommitted config only) and produce gate evidence:
  - Rejection-rate empirical check (target band 20-40%)
  - DL-207 URL shape verification (`&category_id=` vs `&filter=category_id:`)
  - 9-niche RSV spot signals

### Required niche sample sets (A/B/C)
- Set A: `prd_ai_saas`, `support_kb_readiness`, `gumloop_lindy_workflow`
- Set B: `mcp_ai_agent`, `python_automation`, `ai_tool_llm_integration`
- Set C: `ai_agent_development`, `workflow_automation`, `python_web_scraping`

### Mandatory runbook constraints
- `SCRAPFLY_API_KEY` present (do not print)
- `config.yaml` copied to `config.live.yaml`, then `collection.scrapfly.enabled: true` only in local live file
- Dedicated DB target: `data/cycle056_e2e_validation.db`
- Never write to `data/cycle037_live.db`
- If ScrapFly session line absent, record `[SEED — no live signal]` for affected niches
- Deliverable file-only zone: `docs/cycle_reports/CYCLE_056_AGENT_E.md`

## Agent C Package (after B and E both complete)
- Gate battery: `ruff`, `mypy`, file-scoped `pytest`, `config-check`, `foundation-gate`, `phase2-smoke`
- §11.3 parity PRAGMA cross-check for all 9 model targets
- Validate fixture factories by import+call
- Verify suite-guard test is meaningful, not vacuous
- Verify each new integration test has >=3 meaningful assertions
- Re-run 26-name regression expression and golden OFF parity check
- Output: `docs/cycle_reports/CYCLE_056_AGENT_C.md`

## Agent F Package (after C issues GO)

### Fixture API contract (exact signatures)
`tests/fixtures/relevance_fixtures.py`
- `make_mock_result_set_validation(keyword_id: int, relevance_score: float = 0.85, ghost_market_flag: bool = False, category_contamination_flag: bool = False, run_id: int | None = None) -> ResultSetValidation`
- `make_mock_discovery_outcome(run_id: str = "test_run", niche_id: str = "python_automation", keyword_text: str = "python script", is_invalid: bool = False, is_contaminated: bool = False, relevance_score: float | None = None, contamination_reason: str | None = None) -> DiscoveryOutcome`
- `make_ghost_market_rsv(keyword_id: int = 1) -> ResultSetValidation`
- `make_contaminated_rsv(keyword_id: int = 1) -> ResultSetValidation`
- `make_clean_rsv(keyword_id: int = 1) -> ResultSetValidation`

`tests/fixtures/contaminated_data_fixtures.py`
- `make_contaminated_keyword_set(niche_id: str = "python_automation", count: int = 5, rsv_score: float = 0.30) -> list[dict]`
- `make_rejection_band_dataset(total: int = 10, rejected: int = 3, niche_id: str = "python_automation") -> tuple[list, list]`
- `make_niche_validation_input(niche_id: str, ghost: bool = False) -> dict`

### Required F file outputs
- `tests/fixtures/__init__.py` (ensure exists)
- `tests/fixtures/relevance_fixtures.py`
- `tests/fixtures/contaminated_data_fixtures.py`
- `tests/test_suite_guard.py`
- Missing integration tests:
  - `tests/integration/test_r3_sponsored_zombie_integration.py`
  - `tests/integration/test_r2_result_set_validation_integration.py`
  - `tests/integration/test_r4_scoring_integrity_integration.py`
- Missing unit test:
  - `tests/unit/test_sponsored_gig_filtering.py`
- Report: `docs/cycle_reports/CYCLE_056_AGENT_F.md`

## Agent D Package (after A/B/E/C/F complete)
- Merge gate execution (G-001..G-010)
- Codex GraphQL review thread query run twice (pre/post-resolve)
- Single cycle `--cov=src` run ownership
- Golden parity final run
- Tier-1 ceremony artifact:
  - `docs/tier1_gate_ceremony.md`
- Jira closure set:
  - stories `SCRUM-630`, `SCRUM-631`, `SCRUM-632`, `SCRUM-633`, `SCRUM-880`, `SCRUM-883`, `SCRUM-886`, `SCRUM-893`
  - cycle control `SCRUM-1010`
  - epic checkpoint `SCRUM-22`

## Tier-1 Ceremony Checklist Template
- [ ] R4 done (PR `#63`, squash `acff870`)
- [ ] R6 done (PR `#64`, squash `fabdca9`)
- [ ] R9 done (PR `#65`, squash SHA TBD after merge)
- [ ] Suite count floor (`>=3829`) verified
- [ ] REG-13..27 green verified
- [ ] Golden OFF parity pass verified
- [ ] Activation decision recorded: APPROVED or DEFERRED with rationale

## Discovery Activation Decision Framework
- APPROVED if:
  - live rejection band in `[0.20, 0.40]`
  - no REG-13..27 regressions
  - full-suite coverage gate satisfied
- DEFERRED if:
  - rejection band outside `[0.20, 0.40]`, or
  - any Tier-1 regression failure
- Note: committed `config.yaml` remains default-false (`discovery.enable_relevance_gates: false`) regardless of approval outcome.

## Six-Agent Execution Order (binding)
1. Agent A (this plan + governance scaffolding)
2. Agents B and E in parallel
3. Agent C after B+E both complete
4. Agent F after C GO
5. Agent D final gate and merge

## Carry-forward Risks
- §11.5 audit may uncover new migration gaps beyond `discovery_outcomes` (low probability, must be fixed immediately if found)
- Live ScrapFly signal may be unavailable; E must use `[SEED — no live signal]` fallback without fabricating metrics
- Tier-1 activation remains a decision record outcome, not a committed toggle flip
