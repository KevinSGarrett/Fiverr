# CYCLE 059 PLAN — SRDI R10 Dashboard & Alerting Integration

## Cycle Metadata
- Cycle: `059`
- Tier focus: `Tier-3` (R10)
- Branch: `cycle/059/integration`
- Base branch + SHA: `develop @ adc0c046f80ea8437169c04ce53a531ab1adf7e3`
- Control task: `SCRUM-1013` (`Cycle 059 (R10) control`)
- Scope stories: `SCRUM-634`, `SCRUM-635`, `SCRUM-636`, `SCRUM-637`, `SCRUM-638`, `SCRUM-897`, `SCRUM-639`, `SCRUM-640`

## Stage Order (Binding)
- Stage 1: Agent A (solo)
- Stage 2: Agent B + Agent E (parallel, independent)
- Stage 3: Agent C (after BOTH B and E; NOT after F)
- Stage 4: Agent F (after C GO)
- Stage 5: Agent D (after all five prior agents)

## Hard Gates (Verbatim Carry-In)
- G-001: ENFORCED = "Lint, Typecheck, Tests, and Gates" CI + `codecov/project` SUCCESS. `codecov/patch` = ADVISORY; must be surfaced/documented.
- G-002: Codex GraphQL TWICE. Unresolved=0 before merge. WAIT for Codex bot (§15.1).
- G-003: Agent D merge-gate all PASS before squash-merge.
- G-004: EXACTLY ONE `--cov=src` run, by Agent D only.
- G-005: Golden OFF==legacy PASS; kw=110/96/3 drift <=2; kw=110 anchor remains `62.7/1.0/CONDITIONAL_GO`.
- Config gate (committed `config.yaml`): `scrapfly.enabled=false`; `llm_relevance_enabled=false`; `external_signals_enabled=false`.
- §11 parity: if any `src/models/*.py` touched -> Agent B parity table + Agent C PRAGMA checks.
- §12.3 D playbook: large PR label, Codex resolution, codecov advisory handling, mergeable_state handling.
- §14 env/seed protocol: `.env` load before API collection; throwaway DB must be seeded before live collection.
- §15.1 timing: D waits for Codex review submission up to 15 minutes post-CI.
- §15.3 report placement: ALL agent reports in `docs/cycle_reports/`.

## Architecture Confirmation
- Tier-3 gate in roadmap is keyed to **R10 complete**.
- R11 is documented as Tier-4 (future scope); not in C059 scope.
- R10 is display/integration-only for already-computed R1-R9 signals and should avoid scoring logic changes.

## R10 Story Mapping and Implementation Contracts
- `SCRUM-634` — R10.1 Relevance Quality Score panel
- `SCRUM-635` — R10.2 7 keyword integrity badges
- `SCRUM-636` — R10.3 Data Integrity block + tab behavior
- `SCRUM-637` — R10.4 alert catalog (6 types)
- `SCRUM-638` — R10.5 alert generation function
- `SCRUM-897` — R10.6 run-summary relevance block + ghost print
- `SCRUM-639` — R10.7 opportunities ghost filter default
- `SCRUM-640` — R10.8 dashboard test suite

Pinned function signatures for Agent B:

```python
def calculate_niche_relevance_quality_score(niche_id: int, run_id: str, db) -> float:
    """Aggregate relevance quality score for a niche run. AC-R10.1."""

def render_keyword_integrity_badge(keyword_score_row) -> dict:
    """Return badge type + label for a keyword. 7 badge types. AC-R10.1."""

def generate_relevance_alerts_for_run(run_id: str, db) -> list[dict]:
    """Generate 6 alert types for a run. AC-R10.2."""
```

### Badge Types (7)
- `STRONG_GO`: `tag == "STRONG_GO"`
- `CONDITIONAL_GO`: `tag == "CONDITIONAL_GO"`
- `MONITOR`: `tag == "MONITOR"`
- `CAUTION`: `tag == "CAUTION"`
- `GHOST_MARKET`: `ghost_market_flag is True` (overrides tag)
- `EMERGING`: `autocomplete_status == "emerging"`
- `DATA_INTEGRITY_GAP`: `missing_data_flag is True` OR `rsv IS NULL`

### Alert Types (6)
- `ghost_market_detected`
- `relevance_deduction_applied`
- `llm_validation_triggered`
- `external_signal_partial`
- `contamination_flagged`
- `data_integrity_gap`

### Opportunities Filter Contract (AC-R10.3)
- Default behavior: hide `ghost_market_flag=True` opportunities.
- UI-local toggle only: `show_ghost_markets` (display-layer preference).
- No new `config.yaml` toggle for R10 display logic.

### Data Integrity Block Contract (AC-R10.3 / AC-R10.4)
- Must show: RSV applied, LLM used, external signals enabled, confidence-modifier summary.
- Null/missing rows render user-safe text: `N/A — no data collected`.
- No auto-actions: read/display only.

## AC-R10.1 .. AC-R10.4 (Verbatim)
- AC-R10.1: Relevance Quality Score panel + 7 badges render; emerging clearly marked
- AC-R10.2: 6 alert types generated at Stage 3.5 + run end
- AC-R10.3: Ghost markets excluded by default in Opportunities; relevance bars shown
- AC-R10.4: No auto-actions; NULL rows render gracefully

## Baseline + Spec Findings (Agent A)
- Foundation gate: PASS.
- Phase2 smoke: PASS (3 checks).
- Golden anchor (`keyword_id=110`): `(62.7, 1.0, 'CONDITIONAL_GO')`.
- Regression spot checks:
  - 11 selected tests: PASS
  - REG-31/32/33 subset: PASS
- `src/dashboard/` exists with payload/query modules (not empty scaffolding).
- R10 target function names are not currently present in `src/`.
- Existing opportunities payload does not currently apply a ghost-market default exclusion filter.
- `score_components` JSON is populated for kw=110 and can feed Data Integrity display.
- Base dashboard spec path resolved to `PM_Pack/ref/project_plan/07_reporting/DASHBOARD_PLAN.md` (contains SRDI R10 addendum and display architecture).

## File-Impact Map for R10
- New R10 orchestration module(s):
  - `src/analysis/dashboard_integration.py` (new; R10 display integration helpers)
  - `src/dashboard/relevance.py` (recommended new helpers for R10 contracts)
- Existing dashboard/query modules to extend:
  - `src/dashboard/opportunities.py` (ghost default filter wiring)
  - `src/dashboard/queries.py` (filter descriptors and relevance/ghost filters)
  - `src/dashboard/alerts.py` (R10 alert catalog + generation integration)
  - `src/dashboard/app.py` (panel/table integration hooks)
- Existing run summary/pipeline points:
  - `src/analysis/orchestrator.py` (run summary payload wiring)
  - `src/reports/run_summary.py` (display block rendering contract, if selected)
- Tests to add/extend:
  - `tests/unit/test_badge_rendering.py`
  - `tests/unit/test_relevance_alerts.py`
  - `tests/unit/test_relevance_quality_score.py`
  - filter logic test coverage in dashboard/opportunities suite

## Carry-Forward Tier-C (from C058 into C059)
- TC-1 ExternalSignal schema gap:
  - Current model uses `signal_value` (+ `signal_json`) and lacks explicit `raw_value`, `relevance_score`, `trend_direction`, `buyer_intent_posts`, `total_posts`.
  - Rule: if B introduces model columns for R10 display needs -> §11.2 parity table mandatory + migration.
  - If R10 can read existing fields only -> defer TC-1 schema expansion to C060.
- TC-2 dry-run contamination fallback:
  - Pipeline currently can fall back into dry-run placeholders when throwaway DB has no seeded niches.
  - B must replace silent fallback with clear failure (`no niches seeded`) in collection flow.
  - Requires targeted tests + gate pass.

## Migration Expectation (§11)
- R10 itself is display-focused and expected to be migration-free.
- `calculate_niche_relevance_quality_score` should read existing RSV fields (`result_set_validations.result_set_relevance_score`) and existing score payloads.
- Explicit rule for B:
  - If no `src/models/*.py` changes -> no parity requirement.
  - If model edits occur (including ExternalSignal for TC-1) -> §11.2 parity table required and C must run §11.3 PRAGMA verification.

## Ignore/Artifact Hygiene
- Confirmed already ignored:
  - `config.live.yaml`
  - `.db` throwaway artifacts (including `data/cycle059_e2e_validation.db`)
- Added C059 governance ignore:
  - `alert_log.json`
  - `badge_cache*.json`

## Regression Register for C059
- Existing permanent pack baseline remains 34 names (42-pass aggregate expectation).
- C059 adds R10 regressions (REG-34 onward naming by B/D governance update):
  - `test_ghost_market_excluded_from_opportunities_by_default`
  - `test_relevance_quality_score_computed_for_niche_run`
  - plus additional R10 names from B implementation and `test_badge_rendering.py` / `test_relevance_alerts.py`.

## Agent B Handoff (Stage 2 — Parallel with E)
**PARALLEL EXECUTION NOTICE:** You are running in parallel with Agent E on the same branch. E commits docs-only evidence; those commits will appear in `git log` and are expected.

- Scope: implement R10 display integration and TC-2 fallback fix.
- Function contracts (must implement exactly):
  - `calculate_niche_relevance_quality_score(niche_id: int, run_id: str, db) -> float`
  - `render_keyword_integrity_badge(keyword_score_row) -> dict`
  - `generate_relevance_alerts_for_run(run_id: str, db) -> list[dict]`
- Enumerations to pin:
  - 7 badge types (above)
  - 6 alert types (above)
- Ghost filter requirement:
  - opportunities hide ghost markets by default; local preference key `show_ghost_markets`.
- Data Integrity block requirement:
  - render RSV/LLM/external/confidence summary;
  - render nulls as `N/A — no data collected`.
- TC-1/TC-2:
  - decide if ExternalSignal schema extensions are required for R10 display now;
  - implement explicit `no niches seeded` failure path (no silent dry-run fallback).
- §11.2 model parity:
  - REQUIRED if any `src/models/*.py` touched.
- §14.2 note:
  - if any collection operation is executed, load `.env` first per strategy.
- §15.3 report placement:
  - B commits `docs/cycle_reports/CYCLE_059_AGENT_B.md` (NOT repo root).
- Suggested badge skeleton:

```python
BADGE_TYPES = {
    "STRONG_GO": {"color": "green", "icon": "arrow-up"},
    "CONDITIONAL_GO": {"color": "yellow", "icon": "check"},
    "MONITOR": {"color": "orange", "icon": "eye"},
    "CAUTION": {"color": "red", "icon": "warning"},
    "GHOST_MARKET": {"color": "dark", "icon": "ghost"},
    "EMERGING": {"color": "blue", "icon": "rocket"},
    "DATA_INTEGRITY_GAP": {"color": "gray", "icon": "question"},
}

def render_keyword_integrity_badge(keyword_score_row) -> dict:
    if keyword_score_row.ghost_market_flag:
        return BADGE_TYPES["GHOST_MARKET"]
    return BADGE_TYPES.get(keyword_score_row.tag, BADGE_TYPES["DATA_INTEGRITY_GAP"])
```

## Agent E Handoff (Stage 2 — Parallel with B, Docs-Only)
**PARALLEL EXECUTION NOTICE:** You are running in parallel with Agent B on the same branch. B commits `src/` scope while you commit docs-only evidence.

- Scope: validate R10 outputs in live-like context (alerts/badges/run-summary outputs) and report evidence.
- E commit zone: `docs/cycle_reports/CYCLE_059_AGENT_E.md` only.
- §14.2 mandatory env loading:

```powershell
Get-Content 'C:\Fiverr\Fiverr\.env' | ForEach-Object {
  if ($_ -match '^([A-Z0-9_]+)=(.+)$') {
    [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
  }
}
$k=$env:SCRAPFLY_API_KEY
if ($k -and $k.StartsWith('scp-')){"KEY LOADED"}else{"KEY MISSING"}
```

- §14.3 mandatory throwaway DB seeding:

```powershell
py -3.12 run.py foundation-gate --database-url sqlite:///data/cycle059_e2e_validation.db
py -3.12 -c "from sqlalchemy import create_engine; e=create_engine('sqlite:///data/cycle059_e2e_validation.db'); r=e.connect().exec_driver_sql('SELECT COUNT(*) FROM niches').fetchone(); print('niches:', r[0], '- must be 9')"
```

- Validation prompts:
  - verify `generate_relevance_alerts_for_run` emits rows when seeded evidence exists;
  - verify badge rendering and null-safe fallback behavior in dashboard payload output.
- §15.3 report placement is mandatory.

## Agent C Handoff (Stage 3 — After BOTH B and E)
- Prerequisite: both B and E commits landed.
- Verification battery:
  - `ruff`
  - `mypy`
  - 34-name permanent regression pack + new R10 regressions (36+ expected names)
- New C059 gates:
  - all 7 badge types render without crash on null/minimal rows;
  - all 6 alert types generated correctly for seeded run fixtures.
- §11.3:
  - run PRAGMA checks if B touched any `src/models/*.py`.
- Report path:
  - `docs/cycle_reports/CYCLE_059_AGENT_C.md`

## Agent F Handoff (Stage 4 — After C GO)
- Focus: test and coverage expansion for R10 display functions.
- Primary target files:
  - `tests/unit/test_badge_rendering.py`
  - `tests/unit/test_relevance_alerts.py`
  - `tests/unit/test_relevance_quality_score.py`
- Include opportunities ghost-default filter tests and null-safe rendering tests.
- Report path:
  - `docs/cycle_reports/CYCLE_059_AGENT_F.md`

## Agent D Handoff (Stage 5 — Final Merge Gate)
- Runs after A+B+E+C+F complete.
- Must run §12.3 operational playbook:
  - large PR handling (`override:large-pr`),
  - Codex review-thread resolution (query twice),
  - advisory handling for `codecov/patch`,
  - check-run pending behavior,
  - mergeable-state interpretation.
- §15.1 codex timing command (mandatory before merge):

```powershell
Invoke-Exe gh 'api repos/KevinSGarrett/Fiverr/pulls/<PR>/reviews --jq ".[] | {user:.user.login, state, submitted_at}"'
```

- Wait for `chatgpt-codex-connector`; wait up to 15 minutes after CI success if absent.
- Post-merge:
  - update §7 regression register for R10 additions;
  - update Tier-3 status;
  - close 8 R10 stories + control ticket in Jira.
- Report path:
  - `docs/cycle_reports/CYCLE_059_AGENT_D.md`

## Agent A Preflight and Validation Log
- PF-1 `origin/develop`: `adc0c046f80ea8437169c04ce53a531ab1adf7e3` (PASS)
- PF-2 latest commit line matches C058 PM review commit (PASS)
- PF-3 working tree clean at preflight (PASS)
- PF-4 worktree count exactly one (PASS)
- PF-5 config-check: `Config OK: niches=9` (PASS)
- PF-6 all five SRDI/base spec files read (PASS)
- PF-7 dashboard git history inspected (PASS)
- PF-8 `import src.dashboard` check (PASS)

## PR and Governance Tracking
- Governance commit message target:
  - `chore(cycle059): orient + A scaffold + R10 cycle plan`
- Draft PR:
  - title: `feat(dashboard): R10 Dashboard & Alerting Integration (#059)`
  - body: R10 panel/badges/alerts/filter summary + story keys
- PR number and URL:
  - `#68`
  - <https://github.com/KevinSGarrett/Fiverr/pull/68>

