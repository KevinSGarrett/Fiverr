====================================================================
AGENT B — CYCLE 021 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/021/integration
- Python 3.11+ | SQLAlchemy 2.0 | Alembic | Pydantic v2
- Jira: https://kevinsgarrett.atlassian.net | Project: SCRUM

## YOUR ROLE
Agent B owns the single most critical remaining gap from Cycle 020: the KeywordScore
ORM model. The write_keyword_score() function in pipeline.py currently falls back to
a JSON sidecar because no KeywordScore DB table exists. Your job is to create the model,
register it in Base.metadata, ensure init_db creates the table, update write_keyword_score()
to use the real ORM path, and add tests verifying the full write path.

## GIT INSTRUCTIONS
1. Ensure on: cycle/021/integration. Pull latest: git pull origin cycle/021/integration
2. Read Agent A handoff before coding
3. All work on cycle/021/integration — no other branches
4. Commit: feat(models): KeywordScore ORM model and write_keyword_score DB path [Agent B Cycle 021]
5. Do NOT push — human operator pushes after all agents complete

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py
Pass: branch = cycle/021/integration, Agent A tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + inspect existing models
Read docs/cycle_reports/CYCLE_021_AGENT_A.md.
Read src/models/ directory fully. Note which models exist and which Base they inherit from.
Read src/scripts/init_db.py to understand how tables are created.
Read src/scoring/pipeline.py → find write_keyword_score() and understand sidecar path.
Read SCORING_DIRECTION.md "Explanation Field Standard" section for all required fields.
Document: current state and plan in your report before writing any code.

### Task 2: Read E04 Jira stories SCRUM-165, 166, 167 AC/DoD before coding
Query SCRUM-19 children → read SCRUM-165, SCRUM-166, SCRUM-167 full descriptions.
Identify: which AC bullets mention persistence, DB storage, or keyword_scores table.
Post planning comment on SCRUM-165, 166, 167 with your KeywordScore implementation scope.

### Task 3: Create src/models/keyword_score.py — KeywordScore ORM model
Required fields (from SCORING_DIRECTION.md Explanation Field Standard + scoring spec):

class KeywordScore(Base):
  __tablename__ = "keyword_scores"
  id: int (primary key, autoincrement)
  keyword_id: int (ForeignKey to keywords.id, indexed)
  scoring_profile: str (e.g. "default", "aggressive_new_seller")
  score_depth: str (e.g. "standard", "full", "feasibility", "keyword_only")
  scored_at: datetime (UTC, default now)
  data_as_of: datetime (nullable, UTC — oldest data record feeding this score)
  demand_score: float (nullable)
  competition_score: float (nullable)
  opportunity_score: float (nullable)
  feasibility_score: float (nullable)
  profitability_score: float (nullable)
  intent_score: float (nullable)
  saturation_score: float (nullable)
  weakness_score: float (nullable)
  trend_score: float (nullable)
  final_score: float (nullable)
  confidence_modifier: float (nullable)
  tag: str (nullable, e.g. "STRONG_GO", "CONDITIONAL_GO")
  score_components: JSON (nullable)
  confidence_breakdown: JSON (nullable)
  explanation_text: str (nullable)
  red_flags: JSON (nullable)
  missing_data_warnings: JSON (nullable)
  source_evidence: JSON (nullable)
  llm_inputs_used: JSON (nullable)
  niche_tier: str (nullable)

Add UniqueConstraint on (keyword_id, scoring_profile, scored_at) to prevent exact duplicates.
Add Index on (keyword_id, scored_at.desc()) for "latest score" queries.
Import Base from existing src/models/__init__.py or whichever module defines it.

Definition of Done:
  - [ ] Model class created with all 25+ fields
  - [ ] Imports Base from correct location
  - [ ] UniqueConstraint defined
  - [ ] Index on (keyword_id, scored_at) defined
  - [ ] All JSON fields use SQLAlchemy JSON type with nullable=True

### Task 4: Register KeywordScore in src/models/__init__.py
Add import: from src.models.keyword_score import KeywordScore
Add to __all__ list (if it exists).
Verify: python -c "from src.models import KeywordScore; print(KeywordScore.__tablename__)" → "keyword_scores"

### Task 5: Verify init_db creates keyword_scores table
Read src/scripts/init_db.py.
Confirm it imports Base and calls Base.metadata.create_all().
If it imports models selectively, add KeywordScore to the import list.
Test: python run.py init-db → must create keyword_scores table.
Verify: python -c "from src.models import Base; print([t for t in Base.metadata.tables])" includes "keyword_scores"

### Task 6: Update write_keyword_score() in src/scoring/pipeline.py to use ORM path
Current write_keyword_score() tries ORM first, falls back to JSON sidecar.
The ORM path was failing because KeywordScore didn't exist.
Now that KeywordScore exists, update the ORM path:
  from src.models.keyword_score import KeywordScore
  from sqlalchemy.orm import Session
  if isinstance(db, Session):
    row = KeywordScore(
      keyword_id=keyword_id,
      scoring_profile=scoring_profile,
      score_depth=score_depth,
      scored_at=datetime.now(UTC),
      demand_score=scores.get("demand_score"),
      competition_score=scores.get("competition_score"),
      opportunity_score=scores.get("opportunity_score"),
      feasibility_score=scores.get("feasibility_score"),
      profitability_score=scores.get("profitability_score"),
      intent_score=scores.get("intent_score"),
      saturation_score=scores.get("saturation_score"),
      weakness_score=scores.get("weakness_score"),
      trend_score=scores.get("trend_score"),
      final_score=final_score,
      confidence_modifier=confidence_modifier,
      tag=tag,
      score_components=score_components,
      confidence_breakdown=confidence_breakdown,
      explanation_text=explanation_text,
      red_flags=red_flags,
      missing_data_warnings=[...from scores dict],
      source_evidence=[],
      llm_inputs_used={},
      niche_tier="standard",
    )
    db.merge(row)  # UPSERT behavior via merge
    db.commit()
    return True
Keep JSON sidecar as fallback for dict-based db path.

### Task 7: Add get_latest_keyword_score() query helper to src/models/keyword_score.py
def get_latest_keyword_score(keyword_id: int, db) -> "KeywordScore | None":
  """Returns most recent KeywordScore row for keyword_id, or None."""
  if not isinstance(db, Session): return None
  return (db.query(KeywordScore)
    .filter(KeywordScore.keyword_id == keyword_id)
    .order_by(KeywordScore.scored_at.desc())
    .first())

### Task 8: Write tests for KeywordScore ORM model (tests/unit/test_keyword_score.py)
Create: tests/unit/test_keyword_score.py
Use in-memory SQLite session (same pattern as test_scoring_db_integration.py).
Required tests (minimum 14):
- test_keyword_score_table_name — __tablename__ == "keyword_scores"
- test_keyword_score_create_all — init_db creates keyword_scores table
- test_keyword_score_insert_minimal — insert row with only required fields, query back
- test_keyword_score_insert_full — insert row with all 25 fields, no exception
- test_keyword_score_nullable_json_fields — score_components/red_flags can be None
- test_keyword_score_upsert_via_merge — db.merge with same keyword_id → updates row
- test_write_keyword_score_orm_path — write_keyword_score() with Session → returns True
- test_write_keyword_score_orm_persists — row queryable after write
- test_write_keyword_score_sidecar_fallback — write_keyword_score() with dict → sidecar file
- test_get_latest_keyword_score_returns_newest — two rows, gets most recent
- test_get_latest_keyword_score_none_for_missing — unknown keyword_id → None
- test_keyword_score_index_exists — (keyword_id, scored_at) index registered
- test_keyword_score_unique_constraint — duplicate (keyword_id, profile, scored_at) fails
- test_keyword_score_all_score_fields_nullable — all 11 score fields can be None

### Task 9: Run targeted tests
python -m pytest -q tests/unit/test_keyword_score.py
All 14+ tests must pass. Record count.

### Task 10: Run full scoring suite to confirm no regression
python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py tests/unit/test_scoring_db_integration.py
All must pass.

### Task 11: Run ruff + mypy on changed files
python -m ruff check src/models/keyword_score.py src/scoring/pipeline.py tests/unit/test_keyword_score.py
python -m mypy src/models/ src/scoring/pipeline.py
Both must pass. Fix type errors.

### Task 12: Run full validation block
All 6 commands. Total tests >= 965 (951 + 14 new). Coverage >= 90%.

### Task 13: Post Jira evidence for SCRUM-165, 166, 167 (E04 AC/DoD)
For each key: "Cycle 021 Agent B: KeywordScore ORM model created in src/models/keyword_score.py.
  write_keyword_score() now uses ORM UPSERT path when SQLAlchemy Session is passed.
  JSON sidecar preserved as fallback. 14 targeted tests passing. Full validation block pass.
  AC advanced: keyword scoring results can now persist to keyword_scores table.
  DoD remaining: full pipeline run with real collection data, integrated E2E test."

### Task 14: Post Jira evidence for SCRUM-177 (S4.13 Score Orchestration)
Comment: "Cycle 021 Agent B: Orchestrator now has a real DB write path for scoring results.
  KeywordScore ORM model and write helpers are production-ready. End-to-end scoring
  persistence is functional. Remaining gap: controlled full pipeline execution evidence."

### Task 15: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md
Add Cycle 021 Agent B rows for SCRUM-165, 166, 167, 177.

### Task 16: Verify Base.metadata includes keyword_scores
python -c "from src.models import Base; tables = list(Base.metadata.tables.keys()); print(sorted(tables))"
Confirm 'keyword_scores' appears in the list. Record output in report.

### Task 17: Add KeywordScore to DOD_EPIC_01.md table count (if needed)
Read: PM_Pack/ref/dod/DOD_EPIC_01.md (or local copy).
The DOD says AC-1.3.1 requires "at least 28 tables". Count current tables including keyword_scores.
If count increases to 31+, update DOD comment noting intentional additions beyond original spec.
Post note in your report: "keyword_scores table added. Current table count: [N]."

### Task 18: No-main / artifact hygiene / worktree check
git worktree list → canonical root only. No main changes.
git status --short → no .env, coverage.xml, *.db staged.
Commit only: src/models/keyword_score.py, src/models/__init__.py (if modified),
src/scoring/pipeline.py, tests/unit/test_keyword_score.py, ledger, report.

### Task 19: Record SHA and handoff to Agent C
git rev-parse HEAD → record. Test count at handoff.
Handoff: "KeywordScore ORM created. write_keyword_score() has real DB path.
Agent C: build E06 PriceAnalysis model and new_seller_pricing.py calculator."

### Task 20: Create Agent B report at docs/cycle_reports/CYCLE_021_AGENT_B.md
Sections: Preflight, existing models found, KeywordScore design, fields list,
write_keyword_score update, test count (14+), validation block, Jira comments,
table count note, handoff to C.

### Task 21: Commit scoped changes
Message: feat(models): KeywordScore ORM model and write_keyword_score DB path [Agent B Cycle 021]

### Task 22: E04 DoD self-check — what remains for E04 to be Done?
List the remaining AC/DoD items for SCRUM-165-177 that are NOT yet satisfied:
1. Full integrated scoring pipeline run with real collected data
2. score_keyword() integrated into the main run.py --mode full pipeline
3. Explanation text generation (gpt-4o Stage 14) not yet implemented
4. E04 epic-level test: all 13 stories verified Done
Document this list in your report and in a comment on SCRUM-19 (E04 epic).

### Task 23: Read SCRUM-21 children (E06) to prepare Agent C handoff
Query Jira for SCRUM-21 children. Read the first 2 story descriptions.
In your handoff note to Agent C: state the exact Jira story keys for S6.1 and S6.2.

### Task 24: Final state confirmation before handoff
python run.py phase2-smoke → must pass.
python run.py config-check → must pass.
python run.py recommendations-only → must pass (from Agent A's work).
Document all three in your report.

## FILES CREATED THIS CYCLE (Agent B)
| Action | File |
|---|---|
| CREATE | src/models/keyword_score.py |
| MODIFY | src/models/__init__.py |
| MODIFY | src/scoring/pipeline.py |
| CREATE | tests/unit/test_keyword_score.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_021_AGENT_B.md |

## COMMIT INSTRUCTIONS
git add src/models/keyword_score.py src/models/__init__.py src/scoring/pipeline.py
git add tests/unit/test_keyword_score.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_021_AGENT_B.md
git commit -m "feat(models): KeywordScore ORM model and write_keyword_score DB path [Agent B Cycle 021]"
====================================================================
END OF AGENT B PROMPT
====================================================================
