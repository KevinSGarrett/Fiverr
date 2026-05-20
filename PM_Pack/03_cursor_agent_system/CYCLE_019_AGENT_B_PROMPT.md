# Cycle 019 — Cursor Agent B Prompt
# Agent B — Scoring Engine S4.4/S4.5/S4.6/S4.7

## Mission

Implement four scoring calculators for Epic E04: New Seller Feasibility (S4.4),
Profitability Score (S4.5), Conversion Intent Score (S4.6), and Saturation Score (S4.7).
These four calculators build on the scoring infrastructure established by Agent A (demand.py,
competition.py, opportunity.py, contracts.py). Your work continues the Scoring Engine
implementation started by Agent A on cycle/019/integration.

## Common Non-Negotiable Rules

Work only from C:\Fiverr\Fiverr. Run the mandatory PowerShell preflight. Confirm you are on
cycle/019/integration (not develop). Reject random directories or unapproved worktrees.
PowerShell-safe commands only. Jira is the source of truth — read E04 S4.4-S4.7 story
descriptions before implementing any calculator. The .cursorrules file is at repo root; follow
it for all architecture decisions. Each scoring calculator must be in its own file. Do not
modify any files committed by Agent A (demand.py, competition.py, opportunity.py).

## Mandatory PowerShell Preflight

```powershell
Get-Location
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git worktree list
git fetch origin
git log --oneline -5
```

Pass condition: root = C:\Fiverr\Fiverr, branch = cycle/019/integration.
Review Agent A handoff notes in docs/cycle_reports/CYCLE_019_AGENT_A.md before coding.
Confirm the types available in src/scoring/contracts.py before adding new types.

## Jira and AC/DoD Rule

Primary Jira keys: SCRUM-19 (E04 epic), E04 S4.4 story key, E04 S4.5 story key,
E04 S4.6 story key, E04 S4.7 story key. Read these before coding. Query Jira:
  curl -u kevinsgarrett@gmail.com:<TOKEN> \
    "https://kevinsgarrett.atlassian.net/rest/api/3/search?jql=project=SCRUM+AND+parent=19"
Move S4.4, S4.5, S4.6, S4.7 from To Do to In Progress. Post planning comment on each.
Report exact Jira story keys in your cycle report. Post evidence comments after implementation.

## File Scope

Primary: src/scoring/feasibility.py, src/scoring/profitability.py, src/scoring/intent.py,
src/scoring/saturation_score.py, tests/unit/test_scoring.py (extend Agent A's file),
docs/jira/ACTIVE_STORY_DOD_LEDGER.md, docs/cycle_reports/CYCLE_019_AGENT_B.md.

Read before writing: src/scoring/contracts.py (Agent A types), src/scoring/demand.py (pattern),
ref/project_plan/05_scoring/NEW_SELLER_FEASIBILITY.md, PROFITABILITY_SCORE.md,
CONVERSION_INTENT_SCORE.md, SATURATION_SCORE.md, SCORING_DIRECTION.md.

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

### Task 1: Run mandatory PowerShell preflight and read Agent A handoff notes

Jira / AC mapping: Cycle 019 control ticket.
Read docs/cycle_reports/CYCLE_019_AGENT_A.md in full. Note: what types exist in contracts.py,
what test file structure was established, and what patterns Agent A used. Do not duplicate
types or tests already created by Agent A.

### Task 2: Read E04 scoring epic and S4.4/S4.5/S4.6/S4.7 Jira stories before coding

Jira / AC mapping: SCRUM-19, S4.4/S4.5/S4.6/S4.7 story keys.
Query Jira for children of SCRUM-19. Read each story description. Record exact story keys.
Move S4.4, S4.5, S4.6, S4.7 from To Do to In Progress. Post planning comment.

### Task 3: Read all four scoring spec files in ref/project_plan/05_scoring/

Read in sequence:
- ref/project_plan/05_scoring/NEW_SELLER_FEASIBILITY.md
- ref/project_plan/05_scoring/PROFITABILITY_SCORE.md
- ref/project_plan/05_scoring/CONVERSION_INTENT_SCORE.md
- ref/project_plan/05_scoring/SATURATION_SCORE.md
Document key design decisions (weights, normalization, LLM inputs) before writing code.

### Task 4: Implement src/scoring/feasibility.py — NewSellerFeasibilityCalculator

Jira / AC mapping: E04 S4.4 New Seller Feasibility story.
Implementation per spec (SCORING_DIRECTION.md Score 4):
- Class: NewSellerFeasibilityCalculator, method calculate(keyword_id, db) -> float | None
- Input 1 (30%): Proportion of top 10 held by Level 1 or No Level sellers
- Input 2 (25%): Review count of lowest-ranking gig on page 1 (lower = easier entry)
- Input 3 (15%): Price diversity in top results (higher diversity = easier to differentiate)
- Input 4 (20%): LLM gig quality weakness avg of top 10 (higher weakness = more opportunity)
- Input 5 (10%): LLM entry gap assessment (stub/placeholder if LLM unavailable)
- Default weight in composite: 15%
- Niche-tier behavior: For Tier 2 niches (Python, AI Tool, AI Agent, Workflow, Scraping),
  this score is particularly important — add a niche_tier context field in result
- Missing data handling: Same pattern as demand.py (< 30% weight → None)
- LLM stubs: If LLM calls are not yet wired, use placeholder functions that return None
  with a "llm_not_implemented" warning in missing_data_warnings

### Task 5: Implement src/scoring/profitability.py — ProfitabilityScoreCalculator

Jira / AC mapping: E04 S4.5 Profitability Score story.
Implementation per spec (SCORING_DIRECTION.md Score 5):
- Class: ProfitabilityScoreCalculator, method calculate(keyword_id, db) -> float | None
- Input 1 (30%): Average starting price of top 10 — normalized against keyword universe
- Input 2 (30%): Average premium package price — normalized (higher premium = more profit)
- Input 3 (15%): Typical delivery time in days (shorter = lower effort cost → higher score)
- Input 4 (15%): Gig extras presence and pricing (upsells present → higher score)
- Input 5 (10%): LLM upsell potential assessment (stub acceptable)
- Default weight in composite: 10%
- Revenue model integration: Include AOV ramp context in explanation field:
  "Month 1-3 AOV typically $95-175. Month 6+ AOV can reach $300+. Score reflects
  long-term potential, not immediate launch reality."
- Explanation field: Include trust-stage context note

### Task 6: Implement src/scoring/intent.py — ConversionIntentScoreCalculator

Jira / AC mapping: E04 S4.6 Conversion Intent Score story.
Implementation per spec (SCORING_DIRECTION.md Score 6):
- Class: ConversionIntentScoreCalculator, method calculate(keyword_id, db) -> float | None
- Input 1 (25%): Keyword specificity — long-tail vs. broad (long-tail = higher score)
  Heuristic: keyword word count. 1 word = 20, 2 words = 50, 3+ words = 80-100
- Input 2 (25%): Commercial modifier presence — LLM classification or regex
  ("hire", "buy", "need", "looking for", "best" = higher score)
- Input 3 (20%): Average review count top gigs (high reviews = proven buying behavior)
- Input 4 (20%): LLM buyer intent classification (stub returning INFORMATIONAL/CONSIDERATION/
  HIGH INTENT/TRANSACTIONAL — map to 10/40/70/100 numeric scores)
- Input 5 (10%): Reddit demand intent signal (reuse from demand.py if available)
- Default weight in composite: 10%
- LLM classification types: INFORMATIONAL=10, CONSIDERATION=40, HIGH_INTENT=70, TRANSACTIONAL=100
- Stub: If LLM not available, classification defaults to CONSIDERATION (40) with warning

### Task 7: Implement src/scoring/saturation_score.py — SaturationScoreCalculator

Jira / AC mapping: E04 S4.7 Saturation Score story.
Implementation per spec (SCORING_DIRECTION.md Score 7):
- Class: SaturationScoreCalculator, method calculate(keyword_id, db) -> float | None
- Input 1 (25%): Total gig count for keyword (higher count = more saturation)
- Input 2 (25%): Gig title duplication rate — near-identical titles in top 30 (LLM/regex)
- Input 3 (20%): Price compression signal — low price diversity → higher saturation
- Input 4 (15%): Seller portfolio overlap — how similar sellers are to each other
- Input 5 (15%): LLM saturation assessment (stub acceptable)
- Default weight in composite: 5% (applied INVERTED in final score)
- IMPORTANT: This score is APPLIED INVERTED — higher saturation = LOWER final contribution
  Document this clearly: result.is_inverted = True
  In the composite: (100 - saturation_score) * 0.05
- Missing data handling: Same missing-data pattern (< 30% weight → None)

### Task 8: Add FeasibilityScoreResult, ProfitabilityScoreResult, IntentScoreResult,
SaturationScoreResult types to src/scoring/contracts.py (or create a separate types update)

Jira / AC mapping: E04 S4.4-S4.7 shared infrastructure.
Follow the same pattern as Agent A's ScoreResult. Each must have:
- score_value, score_components, confidence_modifier, confidence_breakdown
- missing_data_warnings, source_evidence, scored_at, explanation_text
- SaturationScoreResult also needs: is_inverted: bool = True
- FeasibilityScoreResult also needs: niche_tier: str

### Task 9: Add NewSellerFeasibilityCalculator tests (min 12 test cases)

Required tests:
- test_feasibility_all_inputs — all 5 components, result in range 0-100
- test_feasibility_tier2_niche_context — niche_tier field present in result
- test_feasibility_level1_dominance — all level 1 sellers → high feasibility score
- test_feasibility_high_entry_barrier — TRS sellers dominate → low feasibility score
- test_feasibility_low_review_threshold — low review count on p1 gigs → higher score
- test_feasibility_price_diversity — diverse pricing → positive signal
- test_feasibility_llm_stub — LLM unavailable → warning emitted, score still computes
- test_feasibility_insufficient_data — < 30% weight → None
- test_feasibility_result_fields — result structure includes all required fields
- test_feasibility_niche_tier_tier2 — Tier 2 niche behavior documented in result
- test_feasibility_zero_entry_barrier — no entry barrier keywords → perfect score
- test_feasibility_confidence_deductions — LLM inputs missing → confidence reduced

### Task 10: Add ProfitabilityScoreCalculator tests (min 10 test cases)

Required tests:
- test_profitability_all_inputs — all 5 components, result 0-100
- test_profitability_high_price_market — high avg price → high profitability score
- test_profitability_low_price_market — price war → low profitability score
- test_profitability_premium_package — premium package presence boosts score
- test_profitability_aov_context_in_explanation — explanation text contains AOV context
- test_profitability_delivery_time_short — short delivery time → higher score
- test_profitability_extras_present — gig extras present → higher score
- test_profitability_llm_stub — LLM not available → graceful degradation
- test_profitability_insufficient_data — < 30% weight → None
- test_profitability_result_fields — result structure validation

### Task 11: Add ConversionIntentScoreCalculator tests (min 10 test cases)

Required tests:
- test_intent_all_inputs — all 5 components, result 0-100
- test_intent_long_tail_keyword — 3+ word keyword → higher specificity score
- test_intent_broad_keyword — 1 word keyword → lower specificity score
- test_intent_commercial_modifier — "hire" keyword → high commercial modifier score
- test_intent_transactional_llm — LLM returns TRANSACTIONAL → score contribution = 100
- test_intent_informational_llm — LLM returns INFORMATIONAL → score contribution = 10
- test_intent_llm_default_stub — LLM unavailable → defaults to CONSIDERATION (40) + warning
- test_intent_high_review_count — high review avg → high buying-behavior score
- test_intent_insufficient_data — < 30% weight → None
- test_intent_result_fields — result structure validation

### Task 12: Add SaturationScoreCalculator tests (min 10 test cases)

Required tests:
- test_saturation_all_inputs — all 5 components, result 0-100
- test_saturation_is_inverted_flag — result.is_inverted == True
- test_saturation_high_gig_count — many gigs → high saturation score
- test_saturation_low_gig_count — few gigs → low saturation score
- test_saturation_title_duplication — many identical titles → high saturation
- test_saturation_price_compression — narrow price range → high saturation signal
- test_saturation_llm_stub — LLM unavailable → graceful degradation with warning
- test_saturation_insufficient_data — < 30% weight → None
- test_saturation_result_fields — result structure, is_inverted present
- test_saturation_inversion_note — composite usage note documented in result

### Task 13: Run targeted tests for Agent B scoring additions

Command: python -m pytest -q tests/unit/test_scoring.py
Expected: All new tests PASS. No regression on Agent A tests. Record test count.

### Task 14: Run Ruff and Mypy on scoring module

Commands:
  python -m ruff check src/scoring/ tests/unit/test_scoring.py
  python -m mypy src/scoring/
Both must pass clean. Fix all type errors before proceeding.

### Task 15: Run full validation block

All commands in Required Validation Block above. Total test count must be >= 780.
Coverage must remain >= 90%. Record exact coverage % and test count in report.

### Task 16: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent B rows

Add rows for S4.4, S4.5, S4.6, S4.7 stories. Each row: Jira Key, Status (In Progress),
Files, AC Advanced, DoD Remaining (full product acceptance still open), Validation, PR, Next Action.

### Task 17: Post Jira comments for S4.4, S4.5, S4.6, S4.7 stories

For each key: comment = branch, files changed, tests run, AC/DoD bullets advanced,
remaining gaps (LLM integration pending, runtime acceptance pending), status recommendation.
Recommendation: Keep In Progress (calculators implemented but full pipeline not yet wired).

### Task 18: Verify artifact hygiene before commit

git status --short: confirm no .env, *.db, coverage.xml, *.zip, __pycache__ staged.
Commit only: feasibility.py, profitability.py, intent.py, saturation_score.py,
contracts.py (if updated), tests/unit/test_scoring.py (additions only), ledger, report.

### Task 19: Record final local SHA and update handoff for Agent C

Run: git rev-parse HEAD. Record SHA in report. Post handoff note:
- Files locked: demand.py, competition.py, opportunity.py, feasibility.py,
  profitability.py, intent.py, saturation_score.py (Agent A + B files)
- Files for Agent C: weakness.py, trend.py, final.py, confidence.py, ranking.py, orchestrator.py
- Types available: [list all types in contracts.py after your additions]

### Task 20: Confirm no random directories, no main branch changes, no unauthorized worktrees

Run: git worktree list (expect only canonical root).
Run: git log --oneline origin/main..HEAD (expect 0 commits — no main branch work).
Document both checks in your report.

### Task 21: Check for any new Codex review activity on PRs (Agent D gate awareness)

Run: gh pr list --state all | head -20 to see recent PR activity.
If any PR is open that wasn't there at preflight, report immediately in your handoff note.
Do not merge any open PRs — Agent D owns the PR creation and Codex gate.

### Task 22: Create Agent B report at docs/cycle_reports/CYCLE_019_AGENT_B.md

Required sections: Preflight output, Jira story keys confirmed for S4.4-S4.7,
scoring calculator design decisions for all 4 calculators, test counts per calculator,
LLM stub status per calculator, validation block output, AC/DoD progress, artifact hygiene,
no-main/no-random-dir confirmation, risks/blockers, handoff to Agent C.

### Task 23: Commit scoped changes with descriptive commit message

Message format: feat(scoring): add feasibility/profitability/intent/saturation calculators [Cycle 019 Agent B]
Verify all 4 new calculator files are included. Verify no accidental inclusions.

### Task 24: Hand off clean branch state to Agent C

Ensure the branch is pushed to origin/cycle/019/integration.
Post handoff summary in report covering: current SHA, locked files, C's files, type contracts.
