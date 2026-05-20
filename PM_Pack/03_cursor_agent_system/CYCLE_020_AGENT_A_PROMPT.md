====================================================================
AGENT A — CYCLE 020 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch (to create): cycle/020/integration (from develop after merging PR #23)
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit
- Jira: https://kevinsgarrett.atlassian.net | Project: SCRUM
- Prior cycle branch: cycle/019/integration | PR #23 ready to merge

## YOUR ROLE
Agent A is the PR gate owner, branch creator, and async scoring pipeline implementer.
Your primary product deliverable this cycle is the score_keyword() async end-to-end
function and write_keyword_score() DB write. You implement the full pipeline that runs
all 11 calculators per keyword, applies confidence modifier + final composite, and
persists the result to the keyword_scores table. This is the bridge between the individual
calculator implementations (Cycle 019) and the production scoring pipeline.

## GIT INSTRUCTIONS
1. Verify PR #23 is green and mergeable: gh pr view 23 --json state,mergeable,statusCheckRollup
2. Merge PR #23: gh pr merge 23 --merge (only if green)
3. Switch to develop: git checkout develop && git pull --ff-only origin develop
4. Create branch: git checkout -b cycle/020/integration && git push -u origin cycle/020/integration
5. All work goes on cycle/020/integration — do NOT create other branches
6. Commit format: feat(scoring): description [Agent A Cycle 020]
7. Do NOT push — human operator pushes after all agents complete

## MANDATORY POWERSHELL PREFLIGHT
Execute from C:\Fiverr\Fiverr:
  Get-Location
  git rev-parse --show-toplevel
  git branch --show-current
  git status --short --branch
  git worktree list
  git fetch origin
  gh pr view 23 --json state,mergeable,statusCheckRollup,reviews

Pass condition: root = C:\Fiverr\Fiverr. PR #23 must be mergeable and checks green.
Abort if PR #23 is not mergeable — document blocker and do not proceed.

## TASKS

### Task 1: Run mandatory PowerShell preflight
Execute all 7 preflight commands. Record output. Confirm canonical root lock.
If PR #23 shows any failing check or unresolved Codex thread, stop and document blocker.

### Task 2: Merge PR #23 and create cycle/020/integration
- Verify: gh pr view 23 --json state confirms OPEN + MERGEABLE + all checks SUCCESS
- Verify: gh api graphql -f query=... confirms all review threads isResolved=true
- Merge: gh pr merge 23 --merge (squash if preferred; document choice)
- Pull: git checkout develop && git pull --ff-only origin develop
- Create: git checkout -b cycle/020/integration
- Push: git push -u origin cycle/020/integration
- Verify baseline: python -m pytest -q --cov=src --cov-fail-under=90 (expect 848 tests, 93.30%+)
- Record: git rev-parse HEAD (initial cycle/020/integration SHA after branch creation)
- Jira: Transition SCRUM-508 to Done; add comment with merge SHA and cycle closure evidence.

### Task 3: Create SCRUM-509 Cycle 020 control ticket
- Create Jira Story: Summary "[CYCLE 020] Scoring Pipeline Wiring + E05 Recommendations Foundation"
- Parent: Governance or SCRUM-19 scope parent
- Status: In Progress (transition immediately)
- Comment: branch=cycle/020/integration, agent=A/B/C/D, scope=score_keyword()+LLM wiring+E05

### Task 4: Transition SCRUM-19 (E04 epic) from To Do to In Progress
- Query Jira: get SCRUM-19 current status
- Transition to In Progress
- Comment: "E04 Scoring epic status corrected to In Progress. 13 calculators implemented
  in Cycle 019 (SCRUM-165 through SCRUM-177). Cycle 020 adds DB wiring, LLM integration,
  and the score_keyword() async pipeline."

### Task 5: Read SCORING_SYSTEM.md and existing scoring files before implementing pipeline
- Read: PM_Pack/ref/project_plan/05_scoring/SCORING_SYSTEM.md (full file)
- Read: src/scoring/orchestrator.py (current implementation)
- Read: src/scoring/final.py (final composite logic)
- Read: src/scoring/contracts.py (current types)
- Read: src/models/ directory to understand KeywordScore model (if it exists)
- Read: src/scripts/init_db.py to understand DB initialization pattern
- Document: in your report, what DB models exist for scoring results, and whether
  keyword_scores table / KeywordScore model already exists.

### Task 6: Create src/scoring/pipeline.py — score_keyword() async function
Spec reference: PM_Pack/ref/project_plan/05_scoring/SCORING_SYSTEM.md (score_keyword section)
File to create: src/scoring/pipeline.py

Implement:
- async def score_keyword(keyword_id: int, profile_name: str, db, llm_client, cache) -> dict:
  - Check depth tier from NicheConfig (keyword_only: scores 1-3 only, feasibility: 1-5,
    standard/full: all 11)
  - Call DEPTH_SCORE_AVAILABILITY to determine available scores
  - Run each calculator (call existing calculators; pass db and llm_client/cache if available)
  - Build opportunity_score from demand + competition results
  - Run ConfidenceScoreModifier
  - Run FinalRecommendationScoreCalculator
  - Call assign_tag() for GO/PASS tag
  - Return full result dict matching keyword_scores schema

- def assign_tag(final_score: float, confidence_modifier: float) -> str:
  - Implement OPPORTUNITY_TAGS logic with confidence demotion (< 0.5 → demote one tier)
  - Tags: STRONG_GO (80-100), CONDITIONAL_GO (60-79), MONITOR (40-59),
          CAUTION (20-39), PASS (0-19)
  - Confidence demotion map: STRONG_GO→CONDITIONAL_GO, CONDITIONAL_GO→MONITOR, etc.

- DEPTH_SCORE_AVAILABILITY dict:
  - full: [1,2,3,4,5,6,7,8,9,10,11]
  - standard: [1,2,3,4,5,6,7,8,9,10,11]
  - feasibility: [1,2,3,4,5,11]
  - keyword_only: [1,2,3,11]

- async def score_keyword_batch(keyword_ids: list[int], profile_name: str, db,
    llm_client, cache) -> list[dict]:
  - Runs score_keyword() sequentially with await for each keyword_id
  - Returns list of result dicts; errors are captured per keyword and included in result

Definition of Done:
  - [ ] score_keyword() returns correct dict structure for mocked db input
  - [ ] depth-tier logic correctly gates scores 4-9 for keyword_only depth
  - [ ] assign_tag() returns correct tag for all 5 score ranges
  - [ ] confidence demotion applied when confidence_modifier < 0.5
  - [ ] score_keyword_batch() handles empty list without crash

### Task 7: Create write_keyword_score() function in src/scoring/pipeline.py
Add to src/scoring/pipeline.py:

- def write_keyword_score(keyword_id, scores, weighted_composite, confidence_modifier,
    final_score, tag, score_components, confidence_breakdown, explanation_text,
    red_flags, scoring_profile, score_depth, db) -> bool:
  - Writes or upserts a row in the keyword_scores table (if KeywordScore model exists)
  - If KeywordScore model does not exist yet, store result as a JSON sidecar file in
    data/scoring_results/{keyword_id}.json (deterministic path, safe fallback)
  - Returns True on success, False on DB/IO failure (non-crashing)
  - Document which path was taken in function docstring

- def detect_red_flags_from_scores(scores: dict, components: dict, keyword_id: int,
    db) -> list[dict]:
  - Returns list of red flag dicts: {"flag": str, "severity": "HIGH"|"MEDIUM"|"LOW",
    "source": str}
  - Rules: competition > 75 → HIGH "High competition barrier",
    confidence_modifier < 0.4 → HIGH "Low confidence — insufficient data",
    demand < 20 → MEDIUM "Low demand signal",
    trend_score < 25 → MEDIUM "Declining trend detected"
  - Returns empty list if no red flags triggered

Definition of Done:
  - [ ] write_keyword_score() does not raise on valid inputs
  - [ ] write_keyword_score() returns True on success
  - [ ] JSON sidecar file is created in data/scoring_results/ when DB model unavailable
  - [ ] detect_red_flags_from_scores() returns correct flags for boundary cases

### Task 8: Add SCORING_PROFILES dict to src/scoring/pipeline.py
Import or replicate SCORING_PROFILES from SCORING_SYSTEM.md spec:
- default, aggressive_new_seller, profitability_focus, trend_chaser
- validate_scoring_profile() function: raises ValueError if weights don't sum to 1.0 ± 0.001
- calculate_weighted_composite() from SCORING_SYSTEM.md:
  - Handles missing scores by redistributing weight proportionally
  - Returns (composite_score, score_components_dict)
- calculate_final_score() with confidence_floor=0.20:
  - effective_modifier = max(confidence_modifier, confidence_floor)
  - final = composite * effective_modifier, clamped 0-100

Definition of Done:
  - [ ] All 4 profiles have weights summing to 1.0 ± 0.001
  - [ ] validate_scoring_profile() raises ValueError for invalid weights
  - [ ] calculate_weighted_composite() redistributes missing-score weights
  - [ ] calculate_final_score() applies confidence_floor of 0.20

### Task 9: Add tests for pipeline.py (tests/unit/test_scoring_pipeline.py)
Create new test file: tests/unit/test_scoring_pipeline.py

Required tests (minimum 14):
- test_assign_tag_strong_go — score 80+ → STRONG_GO
- test_assign_tag_pass — score 0-19 → PASS
- test_assign_tag_confidence_demotion — score 75 + confidence 0.4 → CONDITIONAL_GO (demoted)
- test_assign_tag_no_demotion_above_threshold — confidence 0.6 → no demotion
- test_depth_keyword_only_limits_scores — keyword_only depth allows only scores 1-3
- test_depth_standard_allows_all — standard depth allows all 11 scores
- test_calculate_weighted_composite_all_present — correct weighted sum
- test_calculate_weighted_composite_missing_component — weight redistributed
- test_calculate_weighted_composite_competition_inverted — competition inverted correctly
- test_calculate_final_score_confidence_floor — low confidence (0.0) still gets floor (0.20)
- test_validate_scoring_profile_valid — default profile sums to 1.0
- test_validate_scoring_profile_invalid — invalid profile raises ValueError
- test_detect_red_flags_high_competition — competition > 75 → HIGH flag
- test_detect_red_flags_low_confidence — confidence < 0.4 → HIGH flag
- test_write_keyword_score_returns_true — basic write success
- test_red_flags_empty_for_good_scores — no red flags on clean data

### Task 10: Add pipeline.py to src/scoring/__init__.py exports
Open src/scoring/__init__.py and add imports for:
- score_keyword, score_keyword_batch, write_keyword_score
- detect_red_flags_from_scores, assign_tag
- SCORING_PROFILES, calculate_weighted_composite, calculate_final_score
Verify: python -c "from src.scoring.pipeline import score_keyword; print('OK')" passes.

### Task 11: Run targeted tests for pipeline module
Command: python -m pytest -q tests/unit/test_scoring_pipeline.py
Expected: All 14+ tests PASS. Record test count.

### Task 12: Run ruff and mypy on scoring module
Commands:
  python -m ruff check src/scoring/ tests/unit/test_scoring_pipeline.py
  python -m mypy src/scoring/
Both must pass. Fix all issues before full block.

### Task 13: Run full validation block
All 6 commands from Required Validation Block section above.
Total tests must be >= 862 (848 + 14 new pipeline tests).
Coverage must remain >= 90%. Record exact count and % in report.

### Task 14: Verify data/scoring_results/ directory exists or create it
Run: if not (Test-Path "data/scoring_results") { New-Item -ItemType Directory -Path "data/scoring_results" }
Verify it is listed in .gitignore (or add it). DB result sidecars are local artifacts.

### Task 15: Read E05 RECOMMENDATION_ENGINE.md spec and post planning notes
Read: PM_Pack/ref/project_plan/06_analysis/RECOMMENDATION_ENGINE.md
Note: RecommendationContext Pydantic model fields, async gather pattern, gating logic.
In your report handoff, document: "Agent C will implement E05 — here are the key design
constraints from the spec: [list 5 key design decisions from the spec]."

### Task 16: Post Jira comment on SCRUM-175 (S4.11 Final Composite)
Comment: "Cycle 020 Agent A: score_keyword() async pipeline implemented in
src/scoring/pipeline.py. calculate_weighted_composite() and calculate_final_score()
implement the exact formulas from SCORING_SYSTEM.md spec. SCORING_PROFILES dict with all
4 named profiles validated. assign_tag() with confidence demotion implemented.
Pipeline tests: [count] passing. Full validation: [count] tests, [%] coverage."

### Task 17: Post Jira comment on SCRUM-177 (S4.13 Score Orchestration)
Comment: "Cycle 020 Agent A: score_keyword_batch() wrappers and write_keyword_score()
persistence helpers added in src/scoring/pipeline.py. Orchestrator now has a production
path alongside the existing batch API. JSON sidecar fallback for DB-write included."

### Task 18: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Cycle 020 Agent A rows
Add ledger rows for SCRUM-509, SCRUM-175, SCRUM-177 (and any other touched keys).
Each row: Jira Key, Status (In Progress), Files, AC Advanced, DoD Remaining, Validation.

### Task 19: Confirm .cursorrules compliance for pipeline.py
Read .cursorrules from repo root. Verify:
- src/scoring/pipeline.py uses type annotations on all public functions
- No print() in production code (use logging)
- Line length within configured limit
Document any deviation.

### Task 20: Verify no unauthorized worktrees or random directories
git worktree list → canonical root only.
Get-Location → C:\Fiverr\Fiverr throughout all operations.
Confirm no main branch changes: git log --oneline origin/develop..HEAD shows only cycle/020 commits.

### Task 21: Commit scoped changes with descriptive commit message
Scope: src/scoring/pipeline.py, tests/unit/test_scoring_pipeline.py,
src/scoring/__init__.py, docs/jira/ACTIVE_STORY_DOD_LEDGER.md,
docs/cycle_reports/CYCLE_020_AGENT_A.md
Message: feat(scoring): add score_keyword pipeline, assign_tag, composite and write helpers [Agent A Cycle 020]

### Task 22: Record final local SHA and prepare handoff to Agents B/C/D
git rev-parse HEAD → record as Agent A final SHA.
Handoff summary: pipeline.py exports, data/scoring_results/ created,
baseline tests after this commit = [count], coverage = [%].

### Task 23: Create Agent A report at docs/cycle_reports/CYCLE_020_AGENT_A.md
Required sections: Preflight, PR #23 merge evidence, branch creation SHA, Jira actions
(SCRUM-508 Done, SCRUM-509 created, SCRUM-19 In Progress), pipeline.py design summary,
test count, validation block, .cursorrules compliance, artifact hygiene, no-main, handoff.

### Task 24: Hand off clean branch state to Agents B/C/D
Post handoff note in report:
- Branch: cycle/020/integration at SHA [your SHA]
- Files locked: src/scoring/pipeline.py, tests/unit/test_scoring_pipeline.py
- Files for B: all calculator files (add SQLAlchemy query paths)
- Files for C: all 8 stub calculators (add LLM client integration)
- Types available: all types in contracts.py + pipeline.py exports

## FILES CREATED THIS CYCLE (Agent A)
| Action | File Path |
|---|---|
| CREATE | src/scoring/pipeline.py |
| CREATE | tests/unit/test_scoring_pipeline.py |
| CREATE | data/scoring_results/ (directory) |
| MODIFY | src/scoring/__init__.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_020_AGENT_A.md |

## COMMIT INSTRUCTIONS
git add src/scoring/pipeline.py tests/unit/test_scoring_pipeline.py
git add src/scoring/__init__.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_020_AGENT_A.md
git commit -m "feat(scoring): add score_keyword pipeline, assign_tag, composite helpers [Agent A Cycle 020]"

====================================================================
END OF AGENT A PROMPT
====================================================================
