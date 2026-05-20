====================================================================
AGENT D — CYCLE 021 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/021/integration
- Python 3.11+ | asyncio | SQLAlchemy 2.0

## YOUR ROLE
Agent D owns the final stewardship: (1) build and run an end-to-end integration test
for the E05 recommendations pipeline using the in-memory SQLite test DB, (2) advance
SCRUM-231 (E10 End-to-End Pipeline Integration) with concrete pipeline execution evidence,
(3) perform board reconciliation, (4) create PR #25, resolve all Codex findings in-cycle,
and perform the final evidence freeze.

## GIT INSTRUCTIONS
1. Ensure on: cycle/021/integration. Pull latest.
2. Read ALL A/B/C handoffs before starting.
3. Commit: feat(integration): E05 e2e test and SCRUM-231 pipeline evidence [Agent D Cycle 021]
4. Then: gh pr create --base develop --head cycle/021/integration
   --title "feat(cycle-021): KeywordScore ORM, run_recommendations CLI, E06 pricing foundation"
5. Do NOT push until PR body is complete.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -10; git worktree list
  python -m pytest -q tests/unit/test_scoring.py tests/unit/test_keyword_score.py tests/unit/test_pricing.py tests/unit/test_recommendations.py
Pass: branch = cycle/021/integration, all A/B/C tests pass.

## TASKS

### Task 1: Read all A/B/C handoffs + run full test suite
Read: docs/cycle_reports/CYCLE_021_AGENT_A.md, B.md, C.md
python -m pytest -q --cov=src --cov-fail-under=90
Record: total count, coverage %, any failures. Confirm >= 985 tests pass.

### Task 2: Create tests/integration/test_e05_recommendations_e2e.py
Create an end-to-end integration test that exercises the full E05 pipeline using
in-memory SQLite and mocked LLM client.

Test setup:
- Create in-memory SQLite engine + session
- Create all tables (Base.metadata.create_all())
- Insert a Keyword row (keyword_id=1, keyword_text="AI SaaS PRD", niche_id="prd_ai_saas")
- Insert a KeywordScore row (keyword_id=1, final_score=75.0, tag="CONDITIONAL_GO",
  demand_score=65, competition_score=40, confidence_modifier=0.8, scoring_profile="default")
- Insert an OpportunityRanking row (if model exists) or mock get_eligible_keywords

Tests (minimum 12):
- test_e05_get_eligible_keywords_returns_keyword — eligible_keywords includes keyword_id=1
- test_e05_passes_gates_confidence_ok — keyword with confidence 0.8 passes gate 1
- test_e05_passes_gates_confidence_fail — keyword with confidence 0.3 fails gate 1
- test_e05_should_regenerate_no_existing — no existing recommendation → True
- test_e05_build_context_minimal_db — build_recommendation_context returns RecommendationContext
- test_e05_generate_recommendation_dry_run — dry_run path returns generation_complete=False
- test_e05_run_recommendations_stage_dry_run — run_recommendations_stage(dry_run=True) summary has generated >= 0
- test_e05_write_recommendation_sidecar — write_recommendation writes sidecar JSON file
- test_e05_write_recommendation_orm — write_recommendation with Session → row insertable
- test_e05_full_stage_smoke — run_recommendations_stage completes without exception
- test_e05_skip_low_confidence — keyword with confidence 0.2 → skipped count = 1
- test_e05_generate_recommendation_all_tasks_mock — all 11 tasks mocked, generation_complete=True

### Task 3: Run E05 e2e tests
python -m pytest -q tests/integration/test_e05_recommendations_e2e.py
All 12+ tests must pass. Record count.

### Task 4: Verify tests/integration/__init__.py exists
If not present: echo "" > tests/integration/__init__.py
Ensure the integration test directory is importable.

### Task 5: Run full validation block
All 6 commands. Total tests >= 997 (985 + 12). Coverage >= 90%.

### Task 6: Board reconciliation — audit stale statuses
Query key Jira items:
- SCRUM-509: should be Done (Agent A did this). Confirm.
- SCRUM-19 (E04 epic): should be In Progress. Confirm.
- SCRUM-20 (E05 epic): should be In Progress. Confirm.
- SCRUM-21 (E06 epic): should be In Progress (Agent C transitioned). Confirm.
- SCRUM-165-177 (E04): should be In Progress. Confirm.
- SCRUM-178-186 (E05): should be In Progress. Confirm.
- E06 S6.1, S6.2 story keys: should be In Progress (Agent C transitioned). Confirm.
If any are stale, correct them. Document corrections.

### Task 7: Post SCRUM-231 (E10 End-to-End Pipeline Integration) evidence comment
This is the most important Jira action this cycle.
Comment: "Cycle 021 Agent D: End-to-end pipeline evidence for SCRUM-231.

The following pipeline stages are now callable from CLI:
  1. Score engine: python run.py --mode score-only → runs Stages 10-12
  2. Recommendations: python run.py recommendations-only → runs Stage 13

Integration test evidence (tests/integration/test_e05_recommendations_e2e.py):
  - get_eligible_keywords: confirmed
  - passes_recommendation_gates: confirmed (confidence, demand gates)
  - should_regenerate_recommendation: confirmed
  - build_recommendation_context: confirmed with in-memory SQLite
  - run_recommendations_stage(dry_run=True): confirmed
  - write_recommendation: confirmed (sidecar fallback)
  - Full stage smoke: no exception

12 integration tests passing.

Remaining SCRUM-231 DoD: full collection→analysis→scoring→recommendations pipeline
with real Fiverr data. Staging this story for In Review (partially — integration layer
evidence is now documented; production data run still required)."

Transition SCRUM-231 from In Review → In Review (post comment; if currently In Progress,
transition to In Review with this evidence).

### Task 8: Post Jira summary comment on SCRUM-509 (Cycle 020 control) final closeout
If SCRUM-509 is already Done (Agent A did it), add a confirming steward comment:
"Cycle 021 Agent D steward: SCRUM-509 confirmed Done. PR #24 merged. 935 tests in develop."

### Task 9: Post Jira comment on SCRUM-510 (Cycle 021 control)
Comment: "Cycle 021 steward summary: KeywordScore ORM (Agent B), run_recommendations()
CLI (Agent A), E06 PriceAnalysis + pricing calculator (Agent C), E05 e2e test (Agent D).
Total tests: [count]. Coverage: [%]. PR #25: [URL]. Codex: [count findings]."

### Task 10: Create PR #25
gh pr create --base develop --head cycle/021/integration \
  --title "feat(cycle-021): KeywordScore ORM, run_recommendations CLI, E06 pricing foundation"

PR body must include:
- Summary paragraph covering all 4 agent deliverables
- Jira Keys: SCRUM-510, SCRUM-509 (Done), SCRUM-165-167 (KeywordScore), SCRUM-183-184
  (recommendations CLI), E06 S6.1/S6.2, SCRUM-231 (e2e evidence)
- Changed Files: src/models/keyword_score.py, src/models/pricing.py, src/scoring/pipeline.py,
  src/recommendations/run.py, src/pricing/new_seller_pricing.py, run.py, 4 new test files
- Validation: ruff clean, mypy clean, [count] tests, [%] coverage, all gates pass
- AC/DoD table (per-story rows)
- Guardrail confirmations: no main, no worktrees, no secrets

### Task 11: Monitor PR #25 CI checks
gh pr checks [PR number] — wait for all checks to settle.
Required: Lint/Typecheck/Tests/Gates PASS | codecov/project PASS.
Add override:large-pr label if needed.

### Task 12: Resolve all Codex findings on PR #25 in-cycle
For each finding: fix + test + push + reply + resolve.
Invalid: reply with evidence + resolve.
Zero unresolved threads at handoff.

### Task 13: Post SCRUM-175 (Final Composite) + SCRUM-177 (Orchestration) final E04 comments
State: "After Cycle 021, the following E04 DoD items remain open:
  1. Explanation text generation (gpt-4o Stage 14) not implemented
  2. E04 integration into --mode full pipeline not yet wired
  3. Production data run needed for E04 DoD closure
  These will be addressed in Cycle 022+ when collection stage is activated."

### Task 14: Final SHA freeze
git rev-parse origin/cycle/021/integration → final pushed SHA.
Verify SHA matches PR head.
Post freeze comment to PR #25.

### Task 15: Confirm all 4 agent reports exist
  docs/cycle_reports/CYCLE_021_AGENT_A.md
  docs/cycle_reports/CYCLE_021_AGENT_B.md
  docs/cycle_reports/CYCLE_021_AGENT_C.md
  docs/cycle_reports/CYCLE_021_AGENT_D.md

### Task 16: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent D rows
Add rows for SCRUM-510, SCRUM-231, and E05 S5.5-S5.9 final closure status.

### Task 17: Final artifact hygiene
git status --short — confirm no .env, *.db runtime, coverage.xml, *.zip staged.

### Task 18: Final validation block rerun on final pushed SHA
Run all 6 commands. Record output matching final PR head.
All must PASS with coverage >= 90%.

### Task 19: State merge readiness
"PR #25 is ready to merge when approved." or document any blockers.

### Task 20: Create Agent D report at docs/cycle_reports/CYCLE_021_AGENT_D.md
Sections: Preflight, A/B/C handoff summary, E05 e2e test design (12 tests), SCRUM-231
evidence summary, board reconciliation, PR #25 URL, CI/Codex status, final SHA,
test count, coverage, merge readiness.

### Task 21: Post final PR freeze comment
"Final freeze. SHA: [sha]. Tests: [count]. Coverage: [%]. All gates PASS.
Codex: [resolved]. No main. Ready to merge."

### Task 22: Commit Agent D report and ledger
Message: feat(integration): E05 e2e test and SCRUM-231 pipeline evidence [Agent D Cycle 021]

## FILES CREATED THIS CYCLE (Agent D)
| Action | File |
|---|---|
| CREATE | tests/integration/test_e05_recommendations_e2e.py |
| CREATE | tests/integration/__init__.py (if missing) |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_021_AGENT_D.md |

## COMMIT INSTRUCTIONS
git add tests/integration/ docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_021_AGENT_D.md
git commit -m "feat(integration): E05 e2e test and SCRUM-231 pipeline evidence [Agent D Cycle 021]"
====================================================================
END OF AGENT D PROMPT
====================================================================
