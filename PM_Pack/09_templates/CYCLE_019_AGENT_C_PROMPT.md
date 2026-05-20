# Cycle 019 — Cursor Agent C Prompt
# Agent C — Scoring Engine S4.8/S4.9/S4.10/S4.11/S4.12/S4.13

## Mission

Complete the Scoring Engine implementation by implementing five scoring calculators (S4.8-S4.12)
and updating the Scoring Orchestrator (S4.13). This cycle completes the full 11-score suite:
Gig Quality Weakness Score (S4.8), Trend Score (S4.9), Final Recommendation Score (S4.10),
Confidence Score Modifier (S4.11), Ranking and Sorting (S4.12), and Scoring Orchestrator
wiring (S4.13). Your work closes out the E04 epic's implementation phase.

## Common Non-Negotiable Rules

Work only from C:\Fiverr\Fiverr on cycle/019/integration. Read Agent A and Agent B handoff
notes before any implementation. Do not modify files committed by Agents A or B. The .cursorrules
file governs architecture — follow it strictly. One calculator class per file. Read all E04
Jira stories before coding. The scoring orchestrator already exists as a stub (src/scoring/
orchestrator.py) from the audit remediation — update it, do not replace it.

## Mandatory PowerShell Preflight

```powershell
Get-Location
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git worktree list
git log --oneline -10
python -m pytest -q tests/unit/test_scoring.py
```

Pass condition: root = C:\Fiverr\Fiverr, branch = cycle/019/integration.
Pre-check: All Agent A + B scoring tests must pass before you start.
Read docs/cycle_reports/CYCLE_019_AGENT_A.md and CYCLE_019_AGENT_B.md before coding.

## Jira and AC/DoD Rule

Primary Jira keys: SCRUM-19 (E04 epic), E04 S4.8-S4.13 story keys.
Read stories from Jira before coding. Move S4.8-S4.13 from To Do to In Progress.
Post planning comments. After implementation, post evidence comments.

## File Scope

Primary: src/scoring/weakness.py, src/scoring/trend.py, src/scoring/final.py,
src/scoring/confidence.py, src/scoring/ranking.py, src/scoring/orchestrator.py (update only),
tests/unit/test_scoring.py (extend), docs/jira/ACTIVE_STORY_DOD_LEDGER.md,
docs/cycle_reports/CYCLE_019_AGENT_C.md.

Read before writing: src/scoring/contracts.py (types from A+B), ref/project_plan/05_scoring/
GIG_QUALITY_WEAKNESS_SCORE.md, TREND_SCORE.md, FINAL_SCORE.md, CONFIDENCE_SCORE.md,
SCORING_SYSTEM.md, SCORING_DIRECTION.md.

## Required Validation Block

```powershell
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle019.db
python run.py phase2-smoke
```

---

## Tasks

### Task 1: Run preflight, confirm Agent A+B state, read spec files

Confirm all Agent A+B scoring tests pass. Read both handoff reports. Read all scoring spec
files in ref/project_plan/05_scoring/ for S4.8-S4.13. Document design decisions before coding.

### Task 2: Read E04 S4.8-S4.13 Jira stories, move to In Progress, post planning comments

Query Jira for children of SCRUM-19. Read AC/DoD for S4.8-S4.13. Move to In Progress.
Record exact story keys in your report.

### Task 3: Implement src/scoring/weakness.py — GigQualityWeaknessScoreCalculator

Jira / AC mapping: E04 S4.8 story.
Implementation per spec (SCORING_DIRECTION.md Score 8 + GIG_QUALITY_WEAKNESS_SCORE.md):
- Class: GigQualityWeaknessScoreCalculator, method calculate(keyword_id, db) -> float | None
- Most LLM-intensive score — most inputs are LLM-derived
- Input 1: Description quality score (inverted) — LLM gpt-4o — stub if LLM not wired
- Input 2: Weakness count per gig — LLM gpt-4o — count of identified weaknesses 0-10+
- Input 3: Video absence rate — collection field (bool → proportion of top 10 without video)
- Input 4: Portfolio absence rate — collection field (bool → proportion without portfolio)
- Input 5: Thumbnail quality (inverted) — LLM gpt-4o-mini — stub acceptable
- Input 6: FAQ completeness (inverted) — LLM gpt-4o-mini — stub acceptable
- Input 7: Package differentiation (inverted) — LLM gpt-4o — stub acceptable
- Input 8: Niche specificity (inverted, generic = more opportunity) — LLM gpt-4o — stub
- Higher score = weaker competitors = more opportunity for a new seller
- Default weight in composite: 10%
- LLM stubs: All LLM inputs should use placeholder functions returning None with
  "llm_not_implemented" warning; score still computes from collection inputs (video/portfolio)

### Task 4: Implement src/scoring/trend.py — TrendScoreCalculator

Jira / AC mapping: E04 S4.9 Trend Score story.
Implementation per spec (SCORING_DIRECTION.md Score 9 + TREND_SCORE.md):
- Class: TrendScoreCalculator, method calculate(keyword_id, db) -> float | None
- Input 1 (40%): Google Trends 12-month slope (positive slope → high score)
  Raw pytrends data → slope calculation (use linear regression or simple diff)
  Normalize: -50+ slope → 0, 0 slope → 50, +50+ slope → 100
- Input 2 (25%): Google Trends 3-month vs 12-month acceleration
  If 3-month avg > 12-month avg → accelerating (score > 50)
  If 3-month avg < 12-month avg → declining (score < 50)
- Input 3 (15%): Reddit activity trend — stub/placeholder (recent post volume vs historical)
- Input 4 (20%): LLM trend classification — stub returning one of:
  STRONGLY_RISING=100, RISING=75, STABLE=50, DECLINING=25, STRONGLY_DECLINING=0
  Default stub: STABLE (50) with "llm_not_implemented" warning
- Default weight in composite: 5%

### Task 5: Implement src/scoring/confidence.py — ConfidenceScoreModifier

Jira / AC mapping: E04 S4.11 Confidence Score story.
Implementation per spec (SCORING_DIRECTION.md Score 11 + CONFIDENCE_SCORE.md):
- Class: ConfidenceScoreModifier, method calculate(keyword_id, run_context, db) -> float
- Formula: (data_completeness_ratio * 0.50 + data_freshness_score * 0.30 +
             source_diversity_score * 0.20) * llm_analysis_completion_ratio
- Clamped 0.0 to 1.0
- Deductions table (must implement all):
  Google Trends unavailable: -0.15
  No gig detail collected (search only): -0.20
  Seller profiles not collected: -0.10
  Reddit signals unavailable: -0.05
  LLM gig quality incomplete: -0.08 per gig (max -0.20)
  LLM competitor synthesis failed: -0.10
  Data older than 2x TTL: -0.15
  Niche in keyword_only or feasibility mode: -0.25
- Returns: float 0.0-1.0 (the modifier applied to Final Recommendation Score)
- confidence_breakdown: dict with each deduction applied and remaining modifier

### Task 6: Implement src/scoring/final.py — FinalRecommendationScoreCalculator

Jira / AC mapping: E04 S4.10 Final Recommendation Score story.
Implementation per spec (SCORING_DIRECTION.md Score 10 + FINAL_SCORE.md):
- Class: FinalRecommendationScoreCalculator, method calculate(keyword_id, profile, db) -> dict
- Formula (from spec):
  final_score = (
    demand_score * weights.demand
    + (100 - competition_score) * weights.competition_inv
    + opportunity_score * weights.opportunity
    + feasibility_score * weights.feasibility
    + profitability_score * weights.profitability
    + intent_score * weights.intent
    + (100 - saturation_score) * weights.saturation_inv
    + weakness_score * weights.weakness
    + trend_score * weights.trend
  ) * confidence_modifier
- Accept profile name (str): "default", "aggressive_new_seller", "profitability_focus",
  "trend_chaser" — each with weights from SCORING_DIRECTION.md
- Handle None score inputs gracefully — if a score is None, skip its weight contribution
  and document in missing_components list
- Thresholds: STRONG_GO (80-100), CONDITIONAL_GO (60-79), MONITOR (40-59),
  CAUTION (20-39), PASS (0-19)
- Return: {"final_score": float, "tag": str, "profile_used": str, "weights_applied": dict,
           "component_scores": dict, "confidence_modifier": float, "missing_components": list,
           "explanation_text": str}

### Task 7: Implement src/scoring/ranking.py — KeywordRanker

Jira / AC mapping: E04 S4.12 Ranking and Sorting story.
Implementation per spec:
- Class: KeywordRanker with method rank(keywords: list[dict], profile: str) -> list[dict]
- Accepts a list of keyword dicts each with a "final_score" field
- Returns list sorted by final_score descending
- Adds rank field (1-indexed)
- Adds percentile field (0-100, relative rank within the keyword universe)
- Adds delta_from_top field (top_score - this_score)
- Groups by tag (STRONG_GO, CONDITIONAL_GO, etc.) — return as both flat list and grouped dict
- Filter methods: filter_by_tag(keywords, tag), filter_by_niche(keywords, niche_id),
  filter_by_min_score(keywords, min_score)
- Ranking is deterministic: ties broken by keyword_id ascending

### Task 8: Update src/scoring/orchestrator.py — Scoring Orchestrator

Jira / AC mapping: E04 S4.13 Scoring Orchestrator story.
The stub orchestrator exists from audit remediation. Update it to:
- Accept a list of keyword_ids and a database session
- For each keyword_id, call all calculators in order:
  1. DemandScoreCalculator
  2. CompetitionScoreCalculator
  3. OpportunityScoreCalculator
  4. FeasibilityScoreCalculator
  5. ProfitabilityScoreCalculator
  6. IntentScoreCalculator (ConversionIntentScoreCalculator)
  7. SaturationScoreCalculator
  8. WeaknessScoreCalculator (GigQualityWeaknessScoreCalculator)
  9. TrendScoreCalculator
  10. ConfidenceScoreModifier
  11. FinalRecommendationScoreCalculator (with all above scores as inputs)
  12. KeywordRanker (across all keywords in the batch)
- Return: ScoringRunResult with per-keyword scores, final scores, ranking, and run metadata
- Include: run_id, started_at, completed_at, keyword_count, profile_used, errors list
- LLM stubs in place — orchestrator must handle None scores gracefully

### Task 9: Add GigQualityWeaknessScoreCalculator tests (min 12 test cases)

Required tests:
- test_weakness_collection_inputs_only — video/portfolio absence rates → score computes
- test_weakness_video_absence — all top-10 gigs missing video → high weakness
- test_weakness_portfolio_absence — all missing portfolio → additional weakness signal
- test_weakness_all_llm_stubs — all LLM inputs None → score from collection inputs only
- test_weakness_high_weakness_count — many identified weaknesses → high score
- test_weakness_description_quality_inverted — high quality → lower weakness contribution
- test_weakness_llm_warning_emission — stub LLM inputs → missing_data_warnings populated
- test_weakness_insufficient_data — < 30% weight → None
- test_weakness_result_fields — score_value, components, confidence, etc.
- test_weakness_score_range — always 0-100 or None
- test_weakness_opportunity_interpretation — high weakness score = high opportunity
- test_weakness_deterministic — same inputs → same output (no randomness)

### Task 10: Add TrendScoreCalculator tests (min 10 test cases)

Required tests:
- test_trend_all_inputs — all 4 components, result 0-100
- test_trend_slope_calculation — positive Google Trends slope → score > 50
- test_trend_negative_slope — declining trend → score < 50
- test_trend_acceleration_positive — 3mo > 12mo avg → accelerating signal
- test_trend_acceleration_negative — 3mo < 12mo avg → decelerating signal
- test_trend_strongly_rising_llm — STRONGLY_RISING stub → contribution = 100
- test_trend_stable_default — LLM stub defaults to STABLE → contribution = 50
- test_trend_insufficient_data — < 30% weight → None
- test_trend_result_fields — structure validation
- test_trend_no_google_trends — Google Trends missing → confidence penalty applied

### Task 11: Add ConfidenceScoreModifier tests (min 12 test cases)

Required tests:
- test_confidence_full_data — all inputs present → confidence close to 1.0
- test_confidence_missing_google_trends — deduction -0.15 applied
- test_confidence_no_gig_detail — deduction -0.20 applied
- test_confidence_no_seller_profiles — deduction -0.10 applied
- test_confidence_no_reddit — deduction -0.05 applied
- test_confidence_llm_gig_quality_incomplete — per-gig penalty, max -0.20
- test_confidence_llm_competitor_failed — deduction -0.10
- test_confidence_stale_data — data older than 2x TTL → -0.15
- test_confidence_keyword_only_mode — -0.25 applied
- test_confidence_clamped_at_zero — many deductions → result never < 0.0
- test_confidence_clamped_at_one — no deductions → result never > 1.0
- test_confidence_breakdown_dict — breakdown field has all applied deductions listed

### Task 12: Add FinalRecommendationScoreCalculator tests (min 12 test cases)

Required tests:
- test_final_score_default_profile — default weights applied correctly
- test_final_score_aggressive_profile — aggressive_new_seller weights applied
- test_final_score_profitability_profile — profitability_focus weights applied
- test_final_score_trend_chaser_profile — trend_chaser weights applied
- test_final_score_weights_sum_to_1 — all 4 profiles have weights summing to 1.0 ± 0.001
- test_final_score_strong_go_threshold — score >= 80 → tag = STRONG_GO
- test_final_score_pass_threshold — score <= 19 → tag = PASS
- test_final_score_confidence_applied — confidence modifier multiplied correctly
- test_final_score_none_components — missing scores handled gracefully (no crash)
- test_final_score_competition_inverted — competition contribution = (100 - comp) * weight
- test_final_score_saturation_inverted — saturation contribution = (100 - sat) * weight
- test_final_score_result_structure — all required return fields present

### Task 13: Add KeywordRanker tests (min 10 test cases)

Required tests:
- test_ranker_sort_descending — highest final_score gets rank=1
- test_ranker_rank_field — all output items have rank field (1-indexed)
- test_ranker_percentile_field — all items have percentile 0-100
- test_ranker_delta_from_top — top item delta=0.0, others = top_score - score
- test_ranker_filter_by_tag — returns only items matching tag
- test_ranker_filter_by_niche — returns only items for niche_id
- test_ranker_filter_by_min_score — returns items with final_score >= min_score
- test_ranker_tie_breaking — ties broken by keyword_id ascending (deterministic)
- test_ranker_empty_input — empty list → empty list (no crash)
- test_ranker_single_item — one keyword → rank=1, percentile=100, delta=0.0

### Task 14: Add ScoringOrchestrator integration tests (min 8 test cases)

Required tests:
- test_orchestrator_runs_all_calculators — all 12 steps called for each keyword
- test_orchestrator_returns_scoring_run_result — correct return structure
- test_orchestrator_handles_none_scores — LLM stubs return None gracefully
- test_orchestrator_applies_profile — profile name passed to FinalScoreCalculator
- test_orchestrator_run_metadata — run_id, started_at, completed_at present
- test_orchestrator_empty_keyword_list — no crash on empty input
- test_orchestrator_ranking_included — final output includes ranked keyword list
- test_orchestrator_error_list — errors from LLM stubs collected in errors list

### Task 15: Run targeted scoring tests

Command: python -m pytest -q tests/unit/test_scoring.py
Expected: All Agent A + B + C tests pass. Zero regressions. Record total test count.

### Task 16: Run Ruff and Mypy on scoring module

Commands:
  python -m ruff check src/scoring/ tests/unit/test_scoring.py
  python -m mypy src/scoring/
Both must pass clean. Fix all issues before full block.

### Task 17: Run full validation block

All 6 commands in Required Validation Block. Total tests >= 840 (710 + A's tests + B's tests +
C's tests). Coverage must remain >= 90%. Record exact test count and coverage % in report.

### Task 18: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent C rows

Add rows for S4.8, S4.9, S4.10, S4.11, S4.12, S4.13 stories. Each row has Jira Key, Status
(In Progress), Files, AC Advanced, DoD Remaining (runtime wiring pending), Validation, Branch.

### Task 19: Post Jira comments for S4.8-S4.13 story keys

For each key: comment = branch, files changed, tests run, AC/DoD bullets advanced,
remaining gaps (LLM fully wired, runtime scoring acceptance, full pipeline run pending),
status recommendation = Keep In Progress (all calculators implemented, LLM stubs in place).

### Task 20: Verify artifact hygiene, confirm no-main policy, commit scoped changes

git status --short — no .env, *.db, coverage.xml, *.zip staged.
Commit only: weakness.py, trend.py, final.py, confidence.py, ranking.py, orchestrator.py (updates),
tests/unit/test_scoring.py (additions), contracts.py (if needed), ledger, report.
Commit message: feat(scoring): complete scoring engine implementation S4.8-S4.13 [Cycle 019 Agent C]

### Task 21: Run full scoring module smoke test via python run.py phase2-smoke

Confirm phase2-smoke still passes with all new scoring imports present.
If orchestrator.py changes caused import issues, fix before handoff to Agent D.

### Task 22: Record final SHA and prepare handoff note for Agent D

Run: git rev-parse HEAD. Record SHA.
Handoff to Agent D: E04 scoring engine is fully implemented (11 calculators + orchestrator).
All LLM inputs are stubbed. All calculators have unit tests. Phase2-smoke passes.
Agent D: create PR, handle any Codex findings, close E09 dashboard stories with final evidence.

### Task 23: Post SCRUM-19 (E04 epic) status comment with full implementation summary

Comment on SCRUM-19: "Cycle 019 Agent C completed: All 13 scoring stories have
implementations. S4.1-S4.13 all In Progress. 11 calculators implemented with unit tests.
LLM inputs stubbed pending full LLM integration. Orchestrator updated. Tests: [count] passing.
Coverage: [%]. Branch: cycle/019/integration at SHA [sha]."

### Task 24: Create Agent C report at docs/cycle_reports/CYCLE_019_AGENT_C.md

Required sections: Preflight output, Jira S4.8-S4.13 keys confirmed, design decisions for
all 6 implementations, LLM stub rationale, test counts per calculator, validation block output,
AC/DoD progress per story, artifact hygiene, no-main confirmation, risks/blockers, handoff to D.
