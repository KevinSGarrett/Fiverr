====================================================================
AGENT B — CYCLE 020 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch: cycle/020/integration (created by Agent A)
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | OpenAI | Streamlit
- Jira: https://kevinsgarrett.atlassian.net | Project: SCRUM

## YOUR ROLE
Agent B owns SQLAlchemy DB query integration for all 13 scoring calculators. The
calculators in Cycle 019 accepted a dict-based db proxy. Your job is to add a real
SQLAlchemy session query path to each calculator so that when a live SQLAlchemy
session is passed (instead of a dict), it queries the actual database models for
Keyword, SearchResult, ExternalSignal, GigQuality, SellerProfile, etc. The dict-proxy
path must remain fully intact — no breaking changes. Use dual-path logic: if db is a
dict, use existing proxy; if db is a SQLAlchemy Session, query the ORM models.

## GIT INSTRUCTIONS
1. Ensure you are on branch: cycle/020/integration
2. Pull latest: git pull origin cycle/020/integration
3. Read Agent A handoff notes in docs/cycle_reports/CYCLE_020_AGENT_A.md
4. All work goes on cycle/020/integration — do NOT create other branches
5. Commit format: feat(scoring): add SQLAlchemy db integration [Agent B Cycle 020]
6. Do NOT push — human operator pushes after all agents complete

## MANDATORY POWERSHELL PREFLIGHT
Execute from C:\Fiverr\Fiverr:
  Get-Location
  git rev-parse --show-toplevel
  git branch --show-current
  git status --short --branch
  git worktree list
  git log --oneline -5
  python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py
Pass condition: branch = cycle/020/integration, all Agent A scoring tests pass.

## TASKS

### Task 1: Preflight, read Agent A handoff, inspect DB models
Read docs/cycle_reports/CYCLE_020_AGENT_A.md.
Read src/models/ directory for all relevant models:
  Keyword, SearchResult, ExternalSignal, GigQualityScore, SellerScore,
  KeywordScore (if created by Agent A or existing), NicheConfig (DB model if any).
Document in your report: which DB models exist and which fields map to scoring inputs.
Run: python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py
Expected: All Agent A tests pass. Record count.

### Task 2: Read all 13 scoring calculator files before modifying
Read each file in src/scoring/:
  demand.py, competition.py, opportunity.py, feasibility.py, profitability.py,
  intent.py, saturation_score.py, weakness.py, trend.py, confidence.py,
  final.py, ranking.py, orchestrator.py
Note: current db parameter usage in each calculate() method. Document the signal
fields each calculator reads from the dict proxy. This determines what ORM queries
to add.

### Task 3: Read relevant Jira stories before coding
Query SCRUM-19 children (SCRUM-165 through SCRUM-177). Read AC/DoD for each story.
Identify: which AC bullets specifically mention database integration or SQLAlchemy.
Post planning comment on SCRUM-165, 166, 167, 168, 169, 170, 171 with your DB
integration scope.

### Task 4: Add _load_from_db() helper to src/scoring/demand.py
The existing calculate() uses dict proxy. Add a companion path:
  def _load_signals_from_db(self, keyword_id: int, session) -> dict:
    """Load demand signal fields from SQLAlchemy session."""
    from sqlalchemy.orm import Session
    keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
    search = session.query(SearchResult).filter(SearchResult.keyword_id==keyword_id
             ).order_by(SearchResult.created_at.desc()).first()
    trends = session.query(ExternalSignal).filter(
             ExternalSignal.keyword_id==keyword_id,
             ExternalSignal.signal_type=="google_trends").first()
    reddit = session.query(ExternalSignal).filter(
             ExternalSignal.keyword_id==keyword_id,
             ExternalSignal.signal_type=="reddit_demand").first()
    return {
      "total_result_count": search.total_result_count if search else None,
      "autocomplete_position": keyword.autocomplete_position if keyword else None,
      "trends_12mo_score": trends.trends_12mo_score if trends else None,
      "reddit_demand_intent_score": reddit.reddit_demand_intent_score if reddit else None,
    }
  Modify calculate() to detect: if isinstance(db, Session): load via _load_signals_from_db.
  Else: use existing dict proxy path. Zero breaking changes to existing dict-proxy behavior.

### Task 5: Add SQLAlchemy path to src/scoring/competition.py
Same dual-path pattern as Task 4.
_load_signals_from_db() for competition must load:
  - SearchResult.total_result_count (gig count)
  - Average review_count of top 10 gigs (from GigQuality or Gig models)
  - Average seller_level of top 10 (from Seller model)
  - Proportion of top 10 with 100+ reviews
  - Pro-verified seller proportion
  - Average starting_price of top 10
Map to existing signal dict keys used by competition calculator components.

### Task 6: Add SQLAlchemy path to src/scoring/feasibility.py
_load_signals_from_db() for feasibility:
  - Level 1/no-level seller ratio in top 10 gigs
  - Review count of lowest-ranking page-1 gig
  - Price diversity (range and std dev of starting_price)
  - LLM weakness average → load from GigQualityScore if available, else None

### Task 7: Add SQLAlchemy path to src/scoring/profitability.py
_load_signals_from_db() for profitability:
  - Average starting_price of top 10 gigs
  - Average premium_price of top 10 gigs
  - Average delivery_time_days of top 10 gigs
  - Extras presence rate (proportion with gig_extras populated)

### Task 8: Add SQLAlchemy path to src/scoring/intent.py
_load_signals_from_db() for intent:
  - keyword.keyword_text (for word-count specificity)
  - keyword.autocomplete_position (existing)
  - Average review_count of top 10 gigs
  - keyword.intent_classification if field exists (LLM stub result)

### Task 9: Add SQLAlchemy path to src/scoring/saturation_score.py
_load_signals_from_db() for saturation:
  - SearchResult.total_result_count (total gig count)
  - GigQuality.title_duplication_rate if field exists
  - Price compression: std dev / range of starting_price

### Task 10: Add SQLAlchemy path to src/scoring/weakness.py
_load_signals_from_db() for weakness (collection-based inputs only; LLM inputs remain None):
  - video_absence_rate: proportion of top 10 Gigs with has_video=False
  - portfolio_absence_rate: proportion with has_portfolio=False
  - All LLM-derived inputs: still None (handled by stub path)

### Task 11: Add SQLAlchemy path to src/scoring/trend.py
_load_signals_from_db() for trend:
  - ExternalSignal (google_trends): trends_12mo_score, trends_3mo_score
  - Build slope from trends data if monthly series available
  - Reddit signal: reddit_activity_trend if available

### Task 12: Add SQLAlchemy path to src/scoring/confidence.py
_load_signals_from_db() for confidence:
  - Check if gig_detail was collected: len(GigQuality rows) > 0 for keyword
  - Check if seller profiles collected: len(Seller rows) > 0
  - Check reddit signals available: ExternalSignal count for reddit_demand
  - Data freshness: compare max(created_at) across models vs. TTL 168 hours
  - Check mode: NicheConfig.current_depth if model exists

### Task 13: Update src/scoring/orchestrator.py to support SQLAlchemy session
In run() method, add detection: if isinstance(db, Session), pass session through to
each calculator's calculate() call. The existing dict-proxy path continues to work.
Add: from sqlalchemy.orm import Session at top of file.
No changes to the ScoringRunResult structure.

### Task 14: Write DB integration tests (tests/unit/test_scoring_db_integration.py)
Create new file: tests/unit/test_scoring_db_integration.py
Tests use SQLite in-memory session with fixtures:
  - Create a Keyword, SearchResult, ExternalSignal fixture in an in-memory SQLite DB
  - Verify DemandScoreCalculator.calculate(keyword_id, session) returns a non-None score
  - Verify CompetitionScoreCalculator.calculate(keyword_id, session) returns a non-None score
  - Verify OpportunityScoreCalculator.calculate(keyword_id, session, ...) returns score
  - Verify FeasibilityScoreCalculator.calculate(keyword_id, session) returns non-None
  - Verify orchestrator.run([keyword_id], session) returns ScoringRunResult
  - Verify dict proxy still works after DB changes (no regression)
  - Verify graceful None return when keyword_id not found in DB
Minimum 10 integration tests.

### Task 15: Run targeted tests
Commands:
  python -m pytest -q tests/unit/test_scoring.py
  python -m pytest -q tests/unit/test_scoring_pipeline.py
  python -m pytest -q tests/unit/test_scoring_db_integration.py
All must pass. Record test counts per file.

### Task 16: Run ruff and mypy on scoring module
  python -m ruff check src/scoring/ tests/unit/test_scoring_db_integration.py
  python -m mypy src/scoring/
Both must pass. Fix all type errors.

### Task 17: Run full validation block
All 6 commands. Total tests >= 872 (848 + pipeline tests + DB integration tests).
Coverage >= 90%. Record in report.

### Task 18: Post Jira evidence comments for SCRUM-165, 166, 167, 168, 169, 170, 171
For each key, post: "Cycle 020 Agent B: Added SQLAlchemy dual-path support to [file].py.
Dict proxy preserved for test compatibility. Real ORM query path uses [Model] for [field].
DB integration tests: [count] passing. Full validation: [count] tests, [%] coverage.
Status recommendation: Keep In Progress (LLM stubs still in place; full E04 DoD pending)."

### Task 19: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent B rows
Add rows for SCRUM-165 through SCRUM-171 with AC advanced (SQLAlchemy integration),
DoD remaining (LLM wiring, full pipeline run, production acceptance), validation evidence.

### Task 20: Verify artifact hygiene and commit
git status --short — no .env, *.db, coverage.xml staged.
Commit scope: all calculator .py files (DB path additions), test_scoring_db_integration.py,
ACTIVE_STORY_DOD_LEDGER.md, docs/cycle_reports/CYCLE_020_AGENT_B.md.
Message: feat(scoring): add SQLAlchemy dual-path DB integration for all calculators [Agent B Cycle 020]

### Task 21: No-main / no-random-directory confirmation
git worktree list → canonical root only.
git log --oneline origin/develop..HEAD → no develop changes, only cycle/020 commits.

### Task 22: Record final SHA and prepare handoff to Agent C
git rev-parse HEAD. Record SHA.
Handoff: "Calculator files now have SQLAlchemy paths. Existing dict proxy unchanged.
Agent C: add LLM client integration to the 8 stub calculators using src/llm/client.py."

### Task 23: Create Agent B report at docs/cycle_reports/CYCLE_020_AGENT_B.md
Sections: Preflight, DB models found, design decisions for dual-path approach, test counts,
validation output, AC/DoD per story, artifact hygiene, no-main, SHA, handoff to C.

### Task 24: Commit and record final state
Final commit includes all calculator updates + new test file + ledger + report.
Push is done by the human operator — do NOT push directly.

## FILES CREATED THIS CYCLE (Agent B)
| Action | File Path |
|---|---|
| MODIFY | src/scoring/demand.py |
| MODIFY | src/scoring/competition.py |
| MODIFY | src/scoring/feasibility.py |
| MODIFY | src/scoring/profitability.py |
| MODIFY | src/scoring/intent.py |
| MODIFY | src/scoring/saturation_score.py |
| MODIFY | src/scoring/weakness.py |
| MODIFY | src/scoring/trend.py |
| MODIFY | src/scoring/confidence.py |
| MODIFY | src/scoring/orchestrator.py |
| CREATE | tests/unit/test_scoring_db_integration.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_020_AGENT_B.md |

## COMMIT INSTRUCTIONS
git add src/scoring/ tests/unit/test_scoring_db_integration.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_020_AGENT_B.md
git commit -m "feat(scoring): add SQLAlchemy dual-path DB integration for all calculators [Agent B Cycle 020]"

====================================================================
END OF AGENT B PROMPT
====================================================================
