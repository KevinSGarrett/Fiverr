# Cycle 019 — Cursor Agent A Prompt
# Agent A — Branch Gate, E01 Closure Baseline, Scoring S4.1/S4.2/S4.3

## Mission

Own the branch gate, verify the post-audit develop state, create cycle/019/integration, and
implement the first three scoring calculators for Epic E04: Demand Score (S4.1), Competition
Score (S4.2), and Opportunity Score (S4.3). This is a product-forward cycle. The audit
remediation (PRs #16 and #22) has already scaffolded src/scoring/ with contracts.py and
orchestrator.py stubs. Your job is to read those stubs, read the Jira scoring stories for
S4.1-S4.3, and build real implementations with full test coverage.

## Common Non-Negotiable Rules

Cycle 019 starts from develop (clean, 710 tests, 93.6%+ coverage, 0 open PRs). The audit
session (2026-05-17) merged PRs #15, #16, and #22 into develop. Confirm this before coding.
Work only from C:\Fiverr\Fiverr. Run the mandatory PowerShell preflight. Reject random
directories or unapproved worktrees. Use PowerShell-safe commands only. Preserve final
evidence after the last push. Jira is the source of truth — read E04 scoring stories before
implementing any calculator. Do not implement logic not supported by the Jira AC/DoD spec.
The project's .cursorrules file is now in the repo root; follow it for all architecture
decisions, including one-class-per-file for scoring calculators.

## Mandatory PowerShell Preflight

```powershell
Get-Location
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git worktree list
git fetch origin
gh pr list --state open
```

Pass condition: root resolves to C:\Fiverr\Fiverr, branch is develop (before switch),
worktree list has only canonical root. `gh pr list --state open` must return 0 open PRs
(PRs #15, #16, #22 should all be merged). Abort if any of these conditions are not met.

## Same-Cycle Codex Rule

If your work introduces a PR and receives Codex review comments, handle all findings in-cycle.
Valid findings: fix, test, push, reply with evidence, resolve. Invalid findings: evidence-
backed reply, then resolve. No unresolved Codex threads at handoff to Agent D.

## Jira and AC/DoD Rule

Primary Jira keys for this agent: SCRUM-19 (E04 epic), E04 S4.1 story key, E04 S4.2 story key,
E04 S4.3 story key, SCRUM-140, and the new Cycle 019 control ticket (create as first action).
Read these issues before coding. For every touched issue, identify the acceptance criteria and
Definition of Done bullets you are advancing. Comment on each issue with branch, files changed,
validation evidence, remaining gaps, and status recommendation. Keep broad stories non-Done
unless full source DoD is satisfied.

Read Jira E04 scoring stories using:
  curl -u kevinsgarrett@gmail.com:<API_TOKEN> \
    "https://kevinsgarrett.atlassian.net/rest/api/3/search?jql=project=SCRUM+AND+parent=19+ORDER+BY+summary"
Or via gh CLI jira extension or PowerShell Invoke-RestMethod.

## File Scope

Primary: src/scoring/demand.py, src/scoring/competition.py, src/scoring/opportunity.py,
src/scoring/contracts.py (update if needed), tests/unit/test_scoring.py (create or extend),
docs/jira/ACTIVE_STORY_DOD_LEDGER.md, docs/cycle_reports/CYCLE_019_AGENT_A.md.

Read before writing: src/scoring/contracts.py (existing stubs), src/scoring/orchestrator.py
(existing stubs), ref/project_plan/05_scoring/DEMAND_SCORE.md, COMPETITION_SCORE.md,
OPPORTUNITY_SCORE.md, SCORING_DIRECTION.md.

Stay inside this scope unless a small adjacent change is required. Coordinate via report notes
if a change would overlap another agent's files.

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

### Task 1: Run mandatory PowerShell preflight and verify post-audit develop state

Jira / AC mapping: Cycle 019 control ticket (create as SCRUM-274 or next available).
Implementation: Execute all preflight commands. Verify `gh pr list --state open` returns 0 PRs.
Verify `git log --oneline -5` shows the audit merge commits as the most recent. Verify
`python -m pytest -q --cov=src --cov-fail-under=90` passes with 710 tests. Document the
exact test count, coverage %, and SHA at develop HEAD before creating the cycle branch.
Report: Include output of `git log --oneline -5` and pytest summary in your report.

### Task 2: Create Cycle 019 control ticket in Jira

Jira / AC mapping: Governance. Create SCRUM-274 (or next available after 273) with:
- Summary: [CYCLE 019] Scoring Engine Implementation — E04 S4.1 through S4.13
- Type: Story
- Parent: SCRUM-19 (E04 Scoring Epic) or governance epic
- Status: In Progress (transition immediately after creation)
- Description: Cycle 019 delivers the first full scoring engine implementation across all
  11 scoring calculators and the scoring orchestrator. Branch: cycle/019/integration.
Comment on the new ticket with the cycle branch name and agent assignment plan.

### Task 3: Create cycle/019/integration from updated develop

Jira / AC mapping: Cycle 019 control ticket.
Implementation: After verifying develop is clean, run:
  git checkout develop
  git pull --ff-only origin develop
  git checkout -b cycle/019/integration
  git push -u origin cycle/019/integration
Verify the new branch shows the 710-test, post-audit state. Record the initial branch SHA.

### Task 4: Read E04 scoring epic and all 13 scoring story Jira issues before coding

Jira / AC mapping: SCRUM-19 (E04 Scoring epic), S4.1 story key, S4.2 story key, S4.3 story key.
Implementation: Query Jira for all children of SCRUM-19. Read each story description for
AC and DoD bullets. Do not implement any calculator logic that is not backed by AC/DoD text.
Record the exact Jira story keys for S4.1, S4.2, and S4.3 in your report (e.g., SCRUM-165).
Move S4.1, S4.2, S4.3 from To Do to In Progress. Post a planning comment on each.

### Task 5: Confirm SCRUM-140 (S1.7 Niche Seed Data) status and post evidence comment

Jira / AC mapping: SCRUM-140.
Implementation: Verify SCRUM-140 is In Review. Run:
  python -m pytest -q tests/unit/test_seeds.py (or equivalent seed tests)
Confirm 42/42 seed tests pass. Post a Jira comment on SCRUM-140: "Cycle 019 baseline check:
SCRUM-140 confirmed In Review. Branch: cycle/019/integration. 42/42 seed tests PASS. No new
seed issues found. Status recommendation: Keep In Review until full operator acceptance."

### Task 6: Read existing src/scoring/ stubs before implementing calculators

Jira / AC mapping: E04 S4.1 story.
Implementation: Read src/scoring/contracts.py and src/scoring/orchestrator.py in full.
Map the existing stub types and interfaces. Note what DataclassContracts/TypedDicts already exist.
Determine what new types are needed for demand/competition/opportunity calculators.
Document the interface plan in your report before writing any implementation.

### Task 7: Implement src/scoring/demand.py — DemandScoreCalculator

Jira / AC mapping: E04 S4.1 Demand Score story.
Implementation per ref/project_plan/05_scoring/DEMAND_SCORE.md:
- Class: DemandScoreCalculator with method calculate(keyword_id, db) -> float | None
- Component 1 (50%): Fiverr total result count — log-scaled normalization
  (count=100→~50, count=1000→~75, count=5000+→~100)
- Component 2 (20%): Fiverr autocomplete position (pos=1→100, pos=10→10, absent→0)
- Component 3 (20%): Google Trends 12-month score (boost: score*1.15, capped 100)
- Component 4 (10%): Reddit demand intent score (raw 0-10, scaled to 0-100)
- Missing data: If total_weight_available < 0.30, return None
- Confidence deductions: Google Trends missing → -0.15, Reddit missing → -0.05
- Return: round(min(100.0, max(0.0, demand_score)), 2)
- Score components: return dict with each component's value, weight, raw, and notes
- Handle None inputs gracefully (no AttributeError on null DB records)
- Explanation field: gpt-4o-generated explanation (stub/placeholder acceptable for now)
- Include missing_data_warnings list and source_evidence list in output payload

### Task 8: Implement src/scoring/competition.py — CompetitionScoreCalculator

Jira / AC mapping: E04 S4.2 Competition Score story.
Implementation per ref/project_plan/05_scoring/COMPETITION_SCORE.md (read file first):
- Class: CompetitionScoreCalculator with method calculate(keyword_id, db) -> float | None
- Input 1 (20%): Total Fiverr search result count — log-scaled similar to demand
- Input 2 (25%): Average review count of top 10 gigs — normalized against keyword universe
- Input 3 (20%): Average seller level of top 10 gigs (level 1=20, level 2=60, TRS=100)
- Input 4 (15%): Proportion of top 10 with 100+ reviews (0.0-1.0 → 0-100)
- Input 5 (10%): Pro-verified seller presence in top 10 (bool proportion → 0-100)
- Input 6 (5%): Average starting price of top 10 (market establishment proxy)
- Input 7 (5%): LLM competitor strength rating — stub/placeholder acceptable
- Higher = more competition. Inverted in Opportunity Score.
- Same missing-data and confidence structure as DemandScoreCalculator.

### Task 9: Implement src/scoring/opportunity.py — OpportunityScoreCalculator

Jira / AC mapping: E04 S4.3 Opportunity Score story.
Implementation per ref/project_plan/05_scoring/OPPORTUNITY_SCORE.md (read file first):
- Class: OpportunityScoreCalculator
- Formula: normalize_0_100((Demand_Score * 1.2) - (Competition_Score * 0.8))
- Requires: DemandScoreCalculator and CompetitionScoreCalculator results as inputs
- Default weight: 25% (highest weight in composite) — document this
- Return None if either demand or competition score is None
- Opportunity Score is not independently collected — it is derived
- Include explanation: "Higher demand minus weighted competition = opportunity"

### Task 10: Update src/scoring/contracts.py with new scoring payload types

Jira / AC mapping: E04 S4.1 story (shared infrastructure).
Implementation: Add or update type definitions for:
- ScoreComponent (value: float, weight: float, raw: Any, note: str = "")
- ScoreResult (score_value: float | None, score_components: dict, confidence_modifier: float,
  confidence_breakdown: dict, confidence_reason: str, missing_data_warnings: list,
  source_evidence: list, scored_at: datetime, explanation_text: str = "")
- DemandScoreResult(ScoreResult), CompetitionScoreResult(ScoreResult),
  OpportunityScoreResult(ScoreResult) — each with appropriate extra fields
These types should be used by all three calculators and be importable from src/scoring/.

### Task 11: Add DemandScoreCalculator tests (tests/unit/test_scoring.py)

Jira / AC mapping: E04 S4.1 story AC tests.
Tests required (minimum 12 test cases):
- test_demand_score_all_inputs_present — all 4 components, expected result in range 0-100
- test_demand_score_missing_google_trends — returns score, confidence deducted by 0.15
- test_demand_score_missing_reddit — returns score, confidence deducted by 0.05
- test_demand_score_no_autocomplete — autocomplete_position=None → 0 for that component
- test_demand_score_zero_result_count — count=0 → count_score=0.0
- test_demand_score_high_count — count=10000+ → count_score capped at 100
- test_demand_score_insufficient_data — < 30% weight available → returns None
- test_demand_score_all_missing — all inputs None → returns None
- test_demand_score_result_fields — result has score_components, confidence_modifier, etc.
- test_demand_score_autocomplete_pos_1 — position 1 → position_score = 100.0
- test_demand_score_autocomplete_pos_10 — position 10 → position_score = 10.0
- test_demand_score_log_normalization — verify specific count→score mapping from spec

### Task 12: Add CompetitionScoreCalculator tests

Jira / AC mapping: E04 S4.2 story AC tests.
Tests required (minimum 10 test cases):
- test_competition_score_all_inputs — all 7 components, result in range 0-100
- test_competition_score_no_gig_data — gig detail not collected → confidence penalty
- test_competition_score_level_mapping — level 1/2/TRS seller level normalization
- test_competition_score_review_proportion — 100+ review proportion → 0-100 mapping
- test_competition_score_pro_verified — pro verified proportion handling
- test_competition_score_insufficient_data — < 30% weight → None
- test_competition_score_result_fields — result structure validation
- test_competition_score_high_competition — saturated market → high score (close to 100)
- test_competition_score_low_competition — new niche → low score
- test_competition_score_missing_prices — price missing → graceful degradation

### Task 13: Add OpportunityScoreCalculator tests

Jira / AC mapping: E04 S4.3 story AC tests.
Tests required (minimum 8 test cases):
- test_opportunity_score_formula — verify (demand*1.2 - competition*0.8) then normalize
- test_opportunity_score_normalized — result always 0-100
- test_opportunity_score_demand_none — returns None when demand is None
- test_opportunity_score_competition_none — returns None when competition is None
- test_opportunity_score_both_none — returns None
- test_opportunity_score_high_demand_low_competition — high opportunity (>70)
- test_opportunity_score_low_demand_high_competition — low opportunity (<30)
- test_opportunity_score_result_fields — result structure validation

### Task 14: Run targeted tests for scoring module

Jira / AC mapping: E04 sprint quality gate.
Command: python -m pytest -q tests/unit/test_scoring.py
Expected: All new tests PASS. Zero regressions. Record exact test count.

### Task 15: Run Ruff and Mypy on scoring module

Commands:
  python -m ruff check src/scoring/ tests/unit/test_scoring.py
  python -m mypy src/scoring/
Both must pass. Fix any linting or type errors before proceeding.

### Task 16: Run full validation block

Commands (full block):
  python -m ruff check .
  python -m mypy src
  python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
  python run.py config-check
  python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle019.db
  python run.py phase2-smoke
All must PASS. Total test count must be >= 740 (710 base + new scoring tests).
Coverage must remain >= 90%.

### Task 17: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Cycle 019 Agent A rows

Add rows for SCRUM-274 (control), S4.1, S4.2, S4.3 stories, SCRUM-140.
Each row: Jira Key, Jira Status, Files/Evidence, AC Advanced, DoD Remaining, Validation, PR/Branch.

### Task 18: Post Jira comments for all touched issues

For each touched Jira key (SCRUM-274, S4.1 key, S4.2 key, S4.3 key, SCRUM-140, SCRUM-19):
Comment must include: branch=cycle/019/integration, files changed, tests run,
AC/DoD bullets advanced, remaining gaps, and status recommendation.
Use exact Jira keys found by reading the board — do not guess keys.

### Task 19: Commit scoped changes only — verify artifact hygiene before commit

Check: git status --short to confirm no .env, coverage.xml, *.db, *.zip, __pycache__
are staged. Commit only:
- src/scoring/demand.py
- src/scoring/competition.py
- src/scoring/opportunity.py
- src/scoring/contracts.py (if updated)
- tests/unit/test_scoring.py
- docs/jira/ACTIVE_STORY_DOD_LEDGER.md
- docs/cycle_reports/CYCLE_019_AGENT_A.md

### Task 20: Confirm .cursorrules is in repo root and architecture rules are followed

Read .cursorrules from repo root. Verify your scoring calculator files comply with:
- One class per file (DemandScoreCalculator in demand.py only)
- Type annotations on all public methods
- No print() statements in production code (use logging module)
- Line length per configured limit
Document any deviation with a reason in your report.

### Task 21: Verify no unauthorized worktrees or random directories were used

Run: git worktree list
Expected: Only canonical C:\Fiverr\Fiverr worktree. No other entries.
Run: Get-Location (confirm = C:\Fiverr\Fiverr throughout all operations).

### Task 22: Record final local SHA and prepare handoff to Agents B/C/D

Run: git rev-parse HEAD (local SHA after your commit)
Confirm: cycle/019/integration branch exists and has your changes.
Handoff notes: state which files are locked (demand.py, competition.py, opportunity.py),
what contracts are available in src/scoring/contracts.py for downstream agents,
and what patterns to follow for the remaining 10 calculators.

### Task 23: Create Agent A report at docs/cycle_reports/CYCLE_019_AGENT_A.md

Required sections: Preflight output, branch creation evidence, Jira story keys found for
S4.1/S4.2/S4.3, scoring calculator design decisions, test counts, validation block output,
AC/DoD progress per story, artifact hygiene confirmation, no-main confirmation, risks/blockers,
handoff to Agents B/C/D.

### Task 24: Hand off clean branch state to Agents B/C/D

Post or prepare a handoff note summarizing:
- Branch: cycle/019/integration at SHA <your commit SHA>
- Files locked: src/scoring/demand.py, competition.py, opportunity.py, contracts.py
- Files available for B: src/scoring/feasibility.py, profitability.py, intent.py, saturation_score.py
- Files available for C: src/scoring/weakness.py, trend.py, final.py, confidence.py, ranking.py
- Existing test file: tests/unit/test_scoring.py (extend, do not replace)
- Available types from contracts.py: ScoreResult, ScoreComponent, [other types you created]

## Final Report

Create or update: docs/cycle_reports/CYCLE_019_AGENT_A.md

The report must include: preflight output, post-audit develop verification, branch SHA,
Jira keys for S4.1/S4.2/S4.3, design decisions for all 3 calculators, test counts,
validation commands and outcomes, Codex status (N/A until PR), artifact hygiene confirmation,
no-main confirmation, no-random-directory confirmation, risks, and handoff notes for B/C/D.

## Completion Standard

You are complete only when: demand.py, competition.py, opportunity.py are committed on
cycle/019/integration; all scoring tests pass; full validation block passes; Jira evidence
comments are posted for all touched stories; no generated artifacts are staged; Agent A report
exists at the required path.
