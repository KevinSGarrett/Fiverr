# CYCLE 073 - AGENT A PLANNING REPORT

Date: 2026-06-08  
Branch: `cycle/073/integration`  
Cycle control: `SCRUM-1035`  
Story: `SCRUM-204`  
Baseline reference: `243ce1e` (C072 squash on develop history)

## Governance and Policy

- Policy v4.3 posture upheld for Agent A planning/governance work.
- Agent A artifact zone held to docs/governance outputs only.
- S7.9 is treated as dashboard data-layer work only.
- No migration is authorized in C073.

## Branch and Baseline Evidence

- Branch created and pushed: `cycle/073/integration`.
- Worktree check: single worktree on C073 branch.
- Base SHA `243ce1e` confirmed in recent history.
- `src/dashboard/pages/discovery.py` baseline confirmed:
  - 46 lines
  - function inventory: `render_discovery_page` only
  - `__main__` guard present

## Jira Actions Completed

- `SCRUM-1035` transitioned from To Do to **In Progress**.
- `SCRUM-204` transitioned from To Do to **In Progress**.
- Kickoff comment posted on both issues:
  - branch created
  - S7.9 scope confirmed
  - target file `src/dashboard/pages/discovery.py`
  - no migration statement

## Production Readiness Gates

G-A: CLOSED | G-B: CLOSED | G-C: CLOSED | G-D: OPEN (Waves 11-12 pending).  
Wave 10 position at C073 start: 8/9 stories complete; S7.9 is final Wave 10 story.

## Baseline Technical Verification

### Discovery/Page/Data Baseline

- PASS: discovery page exists and is importable.
- PASS: pages count is 9.
- PASS: demo data builders in pages are absent (`[]`).
- PASS: `discovery_cycle_logs` table exists and has 0 rows in seed DB.
- PASS: `discovery_outcomes` table exists and has 0 rows in seed DB.
- PASS: `test_discovery_dashboard.py` not present yet (B/F scope).

### DiscoveryCycleLog and DiscoveryOutcome

- PASS: `DiscoveryCycleLog` contains required fields:
  - `run_id`
  - `hypotheses_accepted`
  - `hypotheses_gated`
  - `cycle_at`
- PASS: `DiscoveryOutcome` model has persisted evaluation/output fields available for dashboard use.

### Keywords Lineage Columns (S7.7 carry-forward)

- PASS: `keywords.is_discovery` present.
- PASS: `keywords.discovery_mode` present.
- PASS: `keywords.discovered_in_run` present.
- NOTE: `keywords.specificity_score` is not present in current gate DB schema and must be treated as optional in S7.9 query logic (safe `getattr` / tolerant projection required).

### S7.2-S7.8 Chain Integrity at C073 Start

- PASS: `run_discovery_cycle` and `_select_modes` import from `src/discovery/stage16.py`.
- PASS: `process_accepted_hypotheses` import from `src/discovery/integration.py`.
- PASS: `build_feedback_summary` and `GOLD_THRESHOLD` import from `src/discovery/feedback.py`.
- PASS: `HypothesisMode` values remain:
  - `adjacent_keyword`
  - `adjacent_niche`
  - `gap_exploit`
  - `trend_chase`
- PASS: `_select_modes` schedule verified for runs 0-5.
- PASS: stage16 call order smoke confirms evaluate first and insert-processing path present.
- PASS: stage16 has no HTTP client imports/calls.
- PASS: stage16 JSON serialization (`json.dumps`) present for persisted run payload fields.

### Baseline Unchanged Module Checks

- `src/discovery/hypothesis.py`: 764 lines (within expected range)
- `src/discovery/integration.py`: 226 lines (within expected range)
- `src/discovery/feedback.py`: 265 lines (within expected range)
- `src/discovery/orchestrator.py`: 300 lines (within expected range)

### Environment and Config Posture

- PASS: `scrapfly=false`.
- PASS: `analysis.external_signals_enabled=true`.
- PASS: `relevance.llm_relevance_enabled=false`.
- PASS: 9 configured niches with expected canonical IDs.
- PASS: `ADJACENT_NICHE_RELATIONSHIPS` count remains 9.
- PASS: `.env` key presence check executed without revealing values (21 keys present).

### Golden and Test Baseline

- PASS: golden parity run:
  - kw110: `62.7 / 1.0 / CONDITIONAL_GO`
  - kw96: `35.8 / 0.8389 / CAUTION`
  - kw3: `56.66 / 0.95 / MONITOR`
- PASS: unit test collection baseline = `5214 tests collected`.
- PASS: fast full-suite gate = `5214 passed`.
- PASS: full suite with coverage = `5214 passed`, coverage `94.01%`, floor `>=90%`.
- PASS: regression selector pack passed (`6 passed`, `5208 deselected`; all required anchors included).

## S7.9 Scope Confirmation (C073)

S7.9 implementation target is constrained to dashboard data-layer extension in:

- `src/dashboard/pages/discovery.py`

No migration or schema change is authorized for C073.

## B Handoff (Implementation Contract)

Implement in `src/dashboard/pages/discovery.py`:

1. `get_discovery_stats(db) -> dict[str, Any]`
2. `get_gold_discoveries(db, limit=50) -> list[dict[str, Any]]`
3. `get_mode_performance(db) -> dict[str, dict[str, Any]]`
4. Extend `render_discovery_page()` to use all three.

### `get_discovery_stats(db)`

- Query `DiscoveryCycleLog` for:
  - run count
  - sum accepted
  - sum gated
  - latest `cycle_at`
- Resolve `last_run_id` from latest log row.
- Return keys:
  - `total_runs`
  - `total_inserted`
  - `total_gated`
  - `last_run_at`
  - `last_run_id`
- Coalesce nullable aggregations and cast integer counters with `int(...)`.
- Entire function wrapped in `try/except Exception` returning empty-safe defaults on error.

### `get_gold_discoveries(db, limit=50)`

- Filter `Keyword.is_discovery == True`.
- Apply specificity gate using the available score field in the current schema path.
- Keep contract threshold `0.70`.
- Sort descending by score, limit rows to `limit`.
- Return dict keys per row:
  - `keyword_text`
  - `niche_id`
  - `discovery_mode`
  - `specificity_score`
  - `discovered_in_run`
- Use `getattr(..., None)` for optional fields and `str(...)` for `niche_id`.
- Entire function wrapped in `try/except Exception`, returning `[]` on error.

### `get_mode_performance(db)`

- Filter discovery rows only (`is_discovery == True`).
- Group by `discovery_mode`.
- Return count + average score for each mode.
- Normalize `None` mode to `"unknown"`.
- Round average to 3 decimals.
- Entire function wrapped in `try/except Exception`, returning `{}` on error.

### Extended `render_discovery_page()`

- Inside `get_db_session()` context:
  - call all three new helper functions
- Render top metrics with `st.columns(3)`:
  - total runs
  - total inserted
  - total gated
- Show `st.caption` for `last_run_id` when present.
- Gold discoveries section:
  - `st.dataframe` when non-empty
  - `st.info` when empty
- Mode performance section:
  - `st.dataframe` when non-empty
  - `st.info` when empty
- Empty DB and query failure paths must never raise.

## C Handoff (Verification Gates)

- Verify importability and type shape for all 3 new helper functions.
- Verify empty-safe behavior for each helper.
- Verify `render_discovery_page()` does not raise on empty DB.
- Verify no migration file added.
- Verify `src/discovery/stage16.py` unchanged.
- Verify golden parity remains PASS.
- Verify coverage remains >=90.
- Verify C073 suite count after B/F is >=5244 target (>=30 new tests added).

## E Handoff (Audit Scope)

E scope for C073 is report-only:

- E edits only `docs/cycle_reports/CYCLE_073_AGENT_E.md`.
- No `src/`, no `tests/`, no `config.yaml`.

E validates:

- all 3 discovery dashboard helper functions import and handle empty data safely
- `render_discovery_page` no-raise empty behavior
- no migration introduced
- `stage16.py` unchanged
- golden parity PASS

## F Handoff (Test Scope)

F scope is strictly:

- `tests/` additions/updates
- `docs/cycle_reports/CYCLE_073_AGENT_F.md`

Minimum tests to include:

- real totals for stats helper
- gold discoveries field mapping
- multi-mode grouped performance
- `None` mode maps to `"unknown"`
- render path uses `st.dataframe` when gold/mode data exists
- robust empty/error cases for all helpers and render flow

## D Handoff (Merge and Closeout)

- Merge gates:
  - CI green
  - attribution checks
  - Codex x2 checks
  - C gates and S7.9 acceptance gates pass
- Merge strategy: squash
- Post-merge transitions:
  - `SCRUM-1035 -> Done`
  - `SCRUM-204 -> Done`
  - `SCRUM-22 -> Done` (Wave 10 9/9 complete)
- Create `SCRUM-1036` for C074 Wave 11 kickoff.

## Wave 10 Scorecard (C073 Start)

| Story | Cycle | Status |
| --- | --- | --- |
| S7.1 scaffold | SRDI | DONE |
| S7.2 adjacent keyword | C066 | DONE |
| S7.3 adjacent niche | C067 | DONE |
| S7.4 gap exploit | C068 | DONE |
| S7.5 trend chase | C069 | DONE |
| S7.6 scoring/feedback | C070 | DONE |
| S7.7 keyword integration | C071 | DONE |
| S7.8 stage16 orchestration | C072 | DONE |
| S7.9 dashboard widgets | C073 | IN PROGRESS |

## 14-Track Review (Part 5.3/5.7)

Using provided weights and C073 target percentages:

- Weighted completion estimate: `66.3%` (computed from supplied weights).
- Wave-10 expected movement after C073 completion:
  - Track 09 Discovery: `70% -> 78%`
  - Track 07 Dashboard: `72% -> 75%`

Part 5.7 box (v4.4 framing):

```text
╔══════════════════════════════════════════════════════════════╗
║  PROJECT COMPLETION: ~65-66% production-ready (C073 target) ║
║  Delta from C072: +1% (S7.9 dashboard data layer)           ║
║  Biggest lever: TierD-2 ScrapFly enablement (+7-8%)         ║
║  Next milestone: C074 Wave 11 Gig Playbook kickoff          ║
╚══════════════════════════════════════════════════════════════╝
```

## Authorization Statement

"CYCLE 073 PROMPTS AUTHORIZED FOR RELEASE. Policy v4.3: 55 LARGE-XXLARGE tasks. Floors: A:1000 B:1200 E:950 C:900 F:1000 D:1200. S7.9 Discovery Dashboard Widgets Data Layer. Modifies: src/dashboard/pages/discovery.py (3 new functions + extended render). New: tests/unit/test_discovery_dashboard.py. No migration. Wave 10 final story. SCRUM-22 closes after merge."

## Task Ledger Finalization

Agent A planning/governance execution completed for C073 including:

- branch/worktree setup on `cycle/073/integration`
- Jira transitions/comment kickoff on `SCRUM-1035` and `SCRUM-204`
- baseline technical verification and golden/suite checks
- B/C/D/E/F handoff specification package authored
- S7.9 no-migration, empty-safe dashboard data-layer contract documented

Status: **Agent A package complete and ready for Agent B implementation start.**

## Addendum - Strict Task Audit Follow-up

- Task 95 completed by adding `PM_Pack/10_cycle_log/CYCLE_073.md` with required template fields:
  - squash SHA placeholder
  - prompt sizing placeholders
  - gate status line
  - Tier-D surfaced items
  - project completion headline
  - Wave 10 completion + SCRUM-22 close target
