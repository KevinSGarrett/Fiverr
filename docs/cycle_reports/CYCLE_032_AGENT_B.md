# CYCLE 032 — Agent B Report

## Scope

Cycle 032 Agent B implemented E03 -> E04 scoring integration for:
- Score 2 (Competition): `CompetitorProfile` benchmarks as first-class inputs.
- Score 3 (Opportunity): verified downstream propagation from updated Score 2 output.
- Score 4 (Feasibility): `CompetitorProfile.new_seller_gap` feasibility boost wiring.

Branch target: `cycle/032/integration`.

## Spec Extraction Summary

Reviewed source specs:
- `PM_Pack/ref/project_plan/05_scoring/COMPETITION_SCORE.md`
- `PM_Pack/ref/project_plan/05_scoring/SCORING_DIRECTION.md`
- `PM_Pack/ref/project_plan/05_scoring/NEW_SELLER_FEASIBILITY.md`

Applied Score 2 matrix (default weight inside score):
1. Total Fiverr search result count — 20%
2. Average review count of top 10 gigs — 25%
3. Average seller level of top 10 gigs — 20%
4. Proportion of top 10 with 100+ reviews — 15%
5. Pro-verified seller presence in top 10 — 10%
6. Average starting price top 10 — 5%
7. LLM competitor strength rating (cluster synthesis) — 5%

Score 3 formula validated:
- `normalize_0_100((Demand * 1.2) - (Competition * 0.8))`

Score 4 Stage-8 signal extraction applied:
- `LOW_VIDEO_PRESENCE`, `LOW_PORTFOLIO_PRESENCE`, `HIGH_PRICE_VARIANCE` from competitor profile gap flags.

## Implementation Summary

### Score 2: CompetitorProfile Integration

- Added `get_competitor_profile_inputs(niche_id, run_id, db)` in `src/scoring/competition.py`.
- Added `compute_seller_level_competition_signal(distribution)` helper (0-100 mapping).
- Integrated profile-aware merge path inside `CompetitionScoreCalculator`:
  - Uses `mean_reviews` for review-density component.
  - Uses `seller_level_distribution` for seller-strength component.
  - Uses `median_price` for pricing establishment component.
  - Supports config guard `scoring.competition.use_competitor_profile` (default `true`).
- Preserved fallback behavior:
  - If profile is absent or guard disabled, Score 2 uses existing Stage 3/4 logic.
- Added LLM signal adjustment path:
  - If profile gap flags include `LOW_VIDEO_PRESENCE`, slight reduction is applied to LLM competitor-strength subcomponent as opportunity signal.

### Score 4: Feasibility Gap Boost

- Added `get_feasibility_gap_signal(niche_id, run_id, db, config)` in `src/scoring/feasibility.py`.
- Added config-driven boost controls:
  - `scoring.feasibility.gap_boost_per_flag`
  - `scoring.feasibility.max_gap_boost`
- Integrated bounded boost into feasibility final score:
  - +10 for each supported gap flag.
  - Capped to configured max (default 30).
- Added source evidence and score component traceability for profile gap boosts.

### Data Model and Persistence

- Extended `CompetitorProfile` model in `src/models/market.py` with:
  - `new_seller_gap` JSON payload.
- Updated `write_competitor_profile(...)` to persist `new_seller_gap`.
- Updated Stage 10 profiler write path (`src/analysis/competitor_profiler.py`) to persist computed gap analysis.
- Added SQLite compatibility backfill in `src/models/database.py`:
  - `competitor_profiles.new_seller_gap` column ensure helper.

### Config Surface

- Extended typed config schema in `src/config/models.py`:
  - `scoring.competition.use_competitor_profile`
  - `scoring.feasibility.gap_boost_per_flag`
  - `scoring.feasibility.max_gap_boost`
- Added keys to `config.yaml.example`.

## Opportunity Flow Verification

- Verified Score 3 code path remains formula-stable and consumes updated Score 2 output through pipeline wiring.
- Added tests proving opportunity decreases when profile-informed competition rises, and remains unchanged when profile data is absent.

## Run-ID Resolution Verification

- Verified profile-only run-id resolution fix from Cycle 031 remains active.
- Added explicit regression tests to ensure profile-only mode reuses existing run IDs and does not mint fresh UUIDs when a run exists.

## Validation Evidence (R-092 v2 style, no `--cov`)

- `pytest -q tests/unit/test_competition_score.py --no-header` -> `20 passed`
- `pytest -q tests/unit/test_demand_score.py --no-header` -> `12 passed`
- `pytest -q tests/unit/test_scoring_pipeline.py --no-header` -> `42 passed`
- `pytest -q tests/integration/test_scoring_integration.py --no-header` -> `2 passed`
- `python -m ruff check src/scoring/ tests/unit/test_competition_score.py` -> clean
- `python -m mypy src/scoring/competition.py` -> clean
- `python run.py phase2-smoke` -> pass
- `python run.py recommendations-only` -> pass
- `python run.py collect-only` -> pass
- `python run.py profile-only` -> pass
- `python run.py config-check` -> pass

## Jira Evidence

- E04 competition story planning + implementation evidence comment posted on `SCRUM-166` (`11361`).
- Epic `SCRUM-19` status update comment posted (`11362`).
- `docs/jira/ACTIVE_STORY_DOD_LEDGER.md` updated with Cycle 032 Agent B rows.

## Final SHA

- Pending scoped commit in Task 18.

## Handoff Notes for Agent C

- `CompetitorProfile` now feeds Score 2 and Score 4 with config-gated fallbacks.
- Score 3 consumes updated Score 2 automatically; no standalone formula rewrite required.
- Continue Cycle 032 planned scope on Saturation model (Stage 3.5 / Score 7) while preserving Score 2+4 backward compatibility behavior.
