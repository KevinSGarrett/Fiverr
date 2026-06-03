# CYCLE 060 PLAN — SRDI R11 (Agent A Scaffold)

## Cycle Metadata
- Cycle: 060
- Scope: SRDI R11 (Tier-4) + C059 Tier-C carry-forward
- Branch: `cycle/060/integration`
- Control Jira: `SCRUM-1014` ("Cycle 060 (R11) control")
- Stories: `SCRUM-641`, `SCRUM-642`, `SCRUM-901`, `SCRUM-643`, `SCRUM-906`, `SCRUM-644`, `SCRUM-645`, `SCRUM-646`
- Stage order: A (solo) -> B+E (parallel) -> C -> F -> D
- Working directory: `C:\Fiverr\Fiverr`
- Python: `py -3.12`

## Preflight Results (Actual)
- PF-1 `git rev-parse origin/develop`: `d0c7059d1627bfa747d65dbd0ff627afbd9ce042` (drift from expected `b03c077...`)
- PF-2 top log:
  - `d0c7059 docs(governance): C059 PM review addendum -- dashboard stubs + hydration HEAD b03c077`
  - `b03c077 docs(governance): C059 PM review -- §16 known-issues + hydration/tracker/cycle-log`
- PF-3 `git status --short`: NOT clean (pre-existing dashboard worktree changes)
- PF-4 `git worktree list`: exactly one worktree
- PF-5 `py -3.12 run.py config-check`: `Config OK: niches=9`
- PF-6 SRDI spec files read:
  - `PM_Pack/ref/project_plan/13_srdi/03_EPIC_BREAKDOWN_MASTER.md`
  - `PM_Pack/ref/project_plan/13_srdi/04_DOD_AND_ACCEPTANCE.md`
  - `PM_Pack/ref/project_plan/13_srdi/06_TEST_PLAN_REGRESSION.md`
  - `PM_Pack/ref/project_plan/13_srdi/07_SEQUENCING_ROADMAP.md`
- PF-7 Codex threads (PR #68): totalCount=2, both unresolved
- PF-8 monitor module check: no existing `*monitor*` module files in `src/`

## R11 Story Extraction (Task 1)
- `SCRUM-641` — R11.1 Stealth-sponsored + relevance-cliff monitors
- `SCRUM-642` — R11.2 Emerging-opportunity bonus + negation-aware exclusion
- `SCRUM-901` — R11.3 Validator edge cases (negation + multilingual)
- `SCRUM-643` — R11.4 Category-filter health monitor + legacy tagging
- `SCRUM-906` — R11.5 Versioning & selector tracking
- `SCRUM-644` — R11.6 Operational protocols (incident ladder + monthly audit + onboarding checklist)
- `SCRUM-645` — R11.7 First-recommendation quality gate (5 checks) + 8 KPI hooks
- `SCRUM-646` — R11.8 Roadmap + tests

### R11 AC (verbatim from DoD/AC)
- AC-R11.1: Negation-aware exclusion + multilingual neutral handling
- AC-R11.2: Monitors (cliff, filter-health) fire correctly + don't over-fire
- AC-R11.3: Emerging bonus only for high-integrity emerging keywords
- AC-R11.4: First-recommendation quality gate blocks on missing RSV/ghost/<0.70/not-LLM/NONE
- AC-R11.5: Legacy scores tagged; monthly audit + new-niche checklist in place

### R11 Regressions from test plan / roadmap references
- `test_stealth_sponsored_monitor_fires_on_fixture` (R11 candidate)
- `test_first_recommendation_quality_gate_blocks_missing_rsv` (R11 candidate)
- `test_negation_aware_exclusion_handles_not_prefix` (R11 candidate)

## Baseline Checks (Task 3)
- `py -3.12 run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci.db`: PASS
- `py -3.12 run.py phase2-smoke`: all 3 checks OK
- Golden probe for `keyword_id=110`: `(62.7, 1.0, 'CONDITIONAL_GO')`
- No R11 symbols present:
  - `stealth_sponsored_monitor`: none
  - `relevance_cliff_monitor`: none
  - `first_recommendation_quality_gate`: none
- P2 modules import check: PASS

## C059 Codex P2 Issue Details (Task 2 / Task 7)

### P2-1 (`src/dashboard/relevance_dashboard.py` line 86)
Codex thread text summary:
- Current filter only checks `Keyword.ghost_market_flag` in `get_opportunities_for_display`.
- Stage 3.5 writes ghost status to `ResultSetValidation.ghost_market_flag` in `_upsert_rsv`.
- If keyword-level flag is not later copied (for example, no Stage 7.5 propagation), ghost opportunities remain visible incorrectly.

Observed current code at line region:
- file: `src/dashboard/relevance_dashboard.py`
- current default filter:
  - `Keyword.ghost_market_flag.is_(False)` OR `Keyword.ghost_market_flag.is_(None)`

MANDATORY B fix contract:
- Default visibility must exclude rows ghosted at run-level (`ResultSetValidation.ghost_market_flag`) even when keyword-level field is stale or NULL.
- Preserve null-safe behavior for legacy keyword ghost flags.
- Add regression:
  - `test_ghost_filter_handles_null_and_legacy_rows` (REG-37 candidate)

### P2-2 (`src/dashboard/alert_generator.py` line 113)
Codex thread text summary:
- `llm_validation_triggered` query currently counts `ResultSetValidation.validation_method like '%llm%'`.
- Production Stage 7.5 path does not stamp RSV validation_method for LLM executions; query under-counts or returns zero.

Observed current code at line region:
- file: `src/dashboard/alert_generator.py`
- current LLM count query uses:
  - `ResultSetValidation.validation_method.is_not(None)`
  - `lower(ResultSetValidation.validation_method).like("%llm%")`

MANDATORY B fix contract:
- Count actual Stage 7.5 executions based on the real model field(s) used by Stage 7.5.
- Verify actual LLM-related `KeywordScore` field names from model.
- Add regression:
  - `test_llm_alert_counts_actual_stage_7_5_executions` (REG-38 candidate)

## Model/Schema Findings (Tasks 17/18/19)
- `KeywordScore` LLM-related field detected:
  - `llm_inputs_used` (from `src/models/keyword_score.py`)
- `ResultSetValidation.run_id` exists: `True`
- Niche model location:
  - `src/models/niche.py`
  - class `Niche`
  - table: `niches`
  - key field used for config-mapped niche identifiers: `slug`
  - internal PK inherited from `IntegerPrimaryKeyMixin` (`id`)

## TC Carry-Forward Findings (Tasks 8/15/16)

### TC-3 seed-niches command status
- `run.py` currently does NOT define `seed-niches` command.
- Existing related code:
  - `src/scripts/import_seeds.py` imports keywords, assumes niche rows already exist.
  - `src/collection/workflows/keyword_expansion.py` warning still instructs foundation-gate seeding even though strategy §16.1 says foundation-gate does not seed niches.
- Contract for B:
  - add `run.py seed-niches --database-url ...` command that inserts 9 niche rows from config
  - use `src/models/niche.py` (`Niche.slug`) mapping
  - required before E live collection

### TC-4 dry-run sentinel injection site
- Located in:
  - `src/collection/orchestrator.py`
- Sentinel values found:
  - `_dry_run_test_`
  - `https://dry-run-test.invalid/`
- B must patch true runtime injection location in orchestrator path (not keyword_expansion only).

### TC-5 external signal schema follow-up
- Keep as deferred Tier-C carry-forward for B if needed by R11 surfaces.
- Required fields still tracked: `raw_value`, `relevance_score`, `trend_direction`.

## R11 Module Expectations (Task 1e / Task 6)
- `src/monitoring/`:
  - stealth-sponsored monitor
  - relevance-cliff monitor
  - category-filter-health monitor
- `src/analysis/emerging_bonus.py` (or equivalent)
- `src/analysis/quality_gate.py` (or equivalent)

## Pinned R11 Function Contracts (Task 6)

```python
def detect_stealth_sponsored(keyword_score_row, competition_rows) -> dict:
    """Returns {detected: bool, count: int, severity: str}. AC-R11.2."""

def detect_relevance_cliff(keyword_score_row, prev_score) -> dict:
    """Returns {detected: bool, drop_pct: float}. AC-R11.2."""

def check_category_filter_health(niche_id, run_id, db) -> dict:
    """Returns {healthy: bool, fallback_rate: float, none_count: int}. AC-R11.2."""
```

```python
def first_recommendation_quality_gate(keyword_score_row, rsv_row, db) -> dict:
    """5-check gate:
    1. RSV present (not None)
    2. ghost_market_flag is False
    3. relevance_score >= 0.70
    4. llm_validated is True (or llm not required for niche)
    5. search_strictness_used != 'NONE'
    Returns {passed: bool, failing_checks: list[str]}"""
```

```python
def negation_aware_exclusion(text: str, exclusion_terms: list[str]) -> bool:
    """Returns True if text contains an exclusion term WITHOUT a negation prefix.
    Handles: 'not X', 'no X', "don't X", etc.
    Multilingual neutral: non-English terms pass through as True (no exclusion applied)."""
```

```python
def compute_emerging_opportunity_bonus(keyword_score_row, rsv_row) -> float:
    """Bonus only for high-integrity emerging keywords.
    Conditions: autocomplete_status='emerging' AND relevance>=0.70 AND NOT ghost AND NOT contaminated.
    Returns bonus (0.0–5.0) added to final_score."""
```

## Hard Gates / Global Rules (Pass-through)
- G-001: Enforced checks are CI + `codecov/project`; `codecov/patch` advisory only.
- G-002: Codex GraphQL twice; unresolved=0.
- G-003: D merge-gate all PASS before squash merge.
- G-004: exactly one `--cov=src` run, D only.
- G-005: golden parity anchors preserved; `data/cycle037_live.db` untouched.
- Config gate: committed config keeps `scrapfly=false`, `llm=false`, `ext_signals=false`.
- §11 parity: model changes require parity table + PRAGMA.
- §15.3: all cycle reports in `docs/cycle_reports/`.

## §14.2 Mandatory Env Loading Block (for E and all live collection)
```powershell
# Load .env into current PowerShell session (§14.2 — mandatory before any API call)
Get-Content 'C:\Fiverr\Fiverr\.env' | ForEach-Object {
  if ($_ -match '^([A-Z0-9_]+)=(.+)$') {
    [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
  }
}
# Verify the key is now accessible
$k = $env:SCRAPFLY_API_KEY
if ($k -and $k.StartsWith('scp-')) { Write-Output "SCRAPFLY_API_KEY: LOADED (prefix=$($k.Substring(0,6)))" }
else { Write-Output "SCRAPFLY_API_KEY: MISSING OR WRONG PREFIX — CHECK .env" }
```

## §14.3 Corrected Seeding Procedure (for E)
```powershell
py -3.12 run.py foundation-gate --database-url sqlite:///data/cycle060_e2e.db
# Then manually seed niches (OR use run.py seed-niches if TC-3 is done):
py -3.12 -c "
from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker
import yaml; from src.models.niche import Niche
e=create_engine('sqlite:///data/cycle060_e2e.db')
cfg=yaml.safe_load(open('config.yaml')); s=sessionmaker(bind=e)()
for item in cfg['niches']:
    nid = item['niche_id'] if isinstance(item, dict) else item
    s.add(Niche(slug=nid, name=nid.replace('_',' ').title(), category_path='uncategorized'))
s.commit(); print('niches:', s.query(Niche).count())
"
```

## §16.2 Correction (for E diagnostics)
- Do NOT use `KeywordScore.run_id` in Agent E diagnostics.
- Use `ResultSetValidation.run_id` as authoritative run source.

## Agent B Handoff (MANDATORY FIRST)
- PARALLEL NOTICE: B runs in parallel with E.
- Before any R11 code:
  1. Fix P2-1 in `src/dashboard/relevance_dashboard.py` (line 86 region)
     - filter must account for run-level RSV ghost flags
     - maintain null-safe default behavior for legacy rows
  2. Fix P2-2 in `src/dashboard/alert_generator.py` (line 113 region)
     - count real Stage 7.5 executions, not RSV validation_method heuristic
  3. Add regressions and pass:
     - `test_ghost_filter_handles_null_and_legacy_rows` (REG-37)
     - `test_llm_alert_counts_actual_stage_7_5_executions` (REG-38)
- Then complete carry-forward Tier-C:
  - TC-3 add `run.py seed-niches` command (required for E live collection)
  - TC-4 fix sentinel URL injection in `src/collection/orchestrator.py`
  - TC-5 address deferred `ExternalSignal` schema if needed for R11 output
- Then implement R11 additive modules/functions only.
- If touching `src/models/*.py`: parity table mandatory (§11.2).
- Report path: `docs/cycle_reports/CYCLE_060_AGENT_B.md` (not repo root).

## Agent E Handoff
- PARALLEL NOTICE: E runs in parallel with B.
- First action: run §14.2 env loading block exactly.
- Use §14.3 corrected seeding steps (foundation-gate + seed workaround, unless B shipped `run.py seed-niches`).
- Use §16.2 workaround: `ResultSetValidation.run_id`.
- C060 E execution order:
  1. validate B's P2 fixes after B push
  2. validate R11 monitor behavior (if data paths available)
- Report path: `docs/cycle_reports/CYCLE_060_AGENT_E.md`.

## Agent C Handoff
- C starts only after B+E completion.
- Must gate on P2 regressions:
  - REG-37 PASS
  - REG-38 PASS
- Run/import checks for R11 tests:
  - `test_stealth_sponsored_monitor_*`
  - `test_first_recommendation_quality_gate_*`
- Confirm expanded pack and GO before F.
- Report path: `docs/cycle_reports/CYCLE_060_AGENT_C.md`.

## Agent F Handoff
- F starts only after C GO.
- Coverage focus:
  - monitor tests
  - quality gate tests
  - negation/multilingual edge tests
- Report path: `docs/cycle_reports/CYCLE_060_AGENT_F.md`.

## Agent D Handoff
- D starts after all prior agents (B/E/C/F) complete.
- Include §12.3 operational playbook in prompt (mandatory):
  - PR too large (>1000) => add `override:large-pr`
  - Codex unresolved threads => resolve, rerun GraphQL twice
  - `codecov/patch` advisory, not blocker
  - pending CI => wait/requery loop
  - mergeable_state handling (`blocked` vs `unstable` vs `clean` vs `unknown`)

### §15.5 Codex Timing (critical)
```powershell
# Step 1: Ensure CI is green
# Step 2: PR is currently in draft — mark it ready FIRST
Invoke-Exe gh 'pr ready <PR>'
# Step 3: Record the ready_for_review timestamp
Invoke-Exe gh 'api repos/KevinSGarrett/Fiverr/issues/<PR>/events --jq ".[] | {event,created_at,actor:.actor.login}"'
# Step 4: Start 15-min polling window FROM ready_for_review timestamp
# Step 5: Only then: GraphQL thread queries x2
```

- Post-merge: update §7 v2.4+ with REG-37/38 and R11 regressions.
- Jira completion: 8 stories + control -> Done.
- Report path: `docs/cycle_reports/CYCLE_060_AGENT_D.md`.

## Jira Execution Log (Task 4)
- Control task created:
  - `SCRUM-1014` — "Cycle 060 (R11) control"
- Confirmed all 8 R11 stories exist and are not Done (`To Do` at check time).
- Linked control issue to:
  - `SCRUM-641`
  - `SCRUM-642`
  - `SCRUM-901`
  - `SCRUM-643`
  - `SCRUM-906`
  - `SCRUM-644`
  - `SCRUM-645`
  - `SCRUM-646`

## Git / PR Execution Log (Task 5)
- Branch created:
  - `git checkout -b cycle/060/integration origin/develop`
- Branch pushed:
  - `git push -u origin cycle/060/integration`
- Draft PR target (to create once scaffold commit is present):
  - Title: `feat(maintenance): R11 Edge Cases & Maintenance + C059 Codex P2 fixes (#060)`
  - Body scope includes R11 + P2 fixes + REG-37/38 notes

## Regression Pack (37 names from strategy context + C059 close)
1. test_extract_price_text_from_payload_uses_nested_price_amount
2. test_parse_gig_detail_from_html_keeps_zero_review_count
3. test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration
4. test_seller_profile_fetcher_maps_parser_fields_for_persistence
5. test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields
6. test_seller_profile_live_markup_drift_regression_spec
7. test_scoring_fallback_queries_scope_to_active_run_id
8. test_scoring_fallback_queries_recover_when_latest_run_unlinked
9. test_demand_uses_search_result_total_result_count_when_available
10. test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch
11. test_scoring_uses_card_urls_with_querystrings_for_sparse_links
12. test_confidence_modifier_uses_current_run_context_not_none
13. test_weakness_multi_row_fallback_does_not_produce_extreme_value
14. test_fiverr_search_url_always_includes_category_filter_for_production_niches
15. test_unconstrained_search_result_applies_demand_confidence_deduction
16. test_eligibility_ghost_hard_block_even_when_forced
17. test_demand_qualified_trc_when_rsv_below_080
18. test_sponsored_gigs_never_included_in_competition_top10
19. test_zombie_gigs_never_used_in_feasibility_review_barrier
20. test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent
21. test_niche_profile_excludes_contaminated_keywords
22. test_opportunity_qualified_by_relevance
23. test_price_outlier_excluded_from_competition_and_profitability
24. test_ghost_discovery_recorded_as_invalid_not_miss
25. test_feedback_excludes_contaminated_outcomes
26. test_low_specificity_hypothesis_rejected
27. test_llm_relevance_only_triggers_in_ambiguous_band
28. test_llm_ghost_verdict_blocks_recommendation
29. test_autocomplete_emerging_keyword_gets_neutral_not_zero_score
30. test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low
31. test_trends_platform_qualifier_applied_before_demand_score_calculation
32. test_external_signal_quality_not_blended_without_signal_context
33. test_external_signal_quality_blended_when_signal_context_present
34. test_confidence_context_handles_naive_external_signal_timestamp
35. test_ghost_market_excluded_from_opportunities_by_default
36. test_all_non_ghost_tags_render_correctly
37. test_empty_run_returns_no_alerts

### C060 additions pinned
- REG-37: `test_ghost_filter_handles_null_and_legacy_rows`
- REG-38: `test_llm_alert_counts_actual_stage_7_5_executions`
- R11 candidates:
  - `test_stealth_sponsored_monitor_fires_on_fixture`
  - `test_first_recommendation_quality_gate_blocks_missing_rsv`
  - `test_negation_aware_exclusion_handles_not_prefix`

## Completion Checklist (Agent A scope)
- [x] All 4 SRDI spec files read
- [x] R11 AC-R11.1..R11.5 extracted
- [x] Codex P2 threads confirmed still open (2 unresolved)
- [x] P2-1 and P2-2 exact issue details documented from thread + code
- [x] KeywordScore LLM field name found
- [x] Dry-run sentinel URL injection site found
- [x] TC-3 seed-niches status documented
- [x] R11 function signatures pinned (monitor/quality/emerging/negation)
- [x] Baseline checks run and recorded
- [x] 37-pack spot-check PASS (`5 passed`)
- [x] Control task created and 8 R11 stories linked
- [x] Cycle branch created and pushed
- [ ] Draft PR created (after scaffold commit)
- [x] B/E/C/F/D handoff sections written with §15.5 + §14.2 + §14.3 + §16.2
- [ ] Agent A report committed (pending final commit step)

