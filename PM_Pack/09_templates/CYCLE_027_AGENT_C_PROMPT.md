====================================================================
AGENT C — CYCLE 027 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/027/integration
- Python 3.11+ | SQLAlchemy 2.0

## ⚠️ HARD GATE REMINDER
codecov/patch >= 90% hard blocker. Run targeted coverage on all new files before handoff.

## YOUR ROLE
Agent C builds the GigQualityScore ORM model. This table is what the LLM quality
analysis pipeline writes to when it evaluates individual gigs for description quality,
weakness count, thumbnail quality, FAQ completeness, etc. The GigQualityWeaknessScore
calculator (weakness.py) reads from this table when real data is available.
Spec: PM_Pack/ref/project_plan/03_data/SCHEMA.md (gig_quality_scores table)
      PM_Pack/ref/project_plan/05_scoring/SCORING_DIRECTION.md (weakness score inputs)

## GIT INSTRUCTIONS
1. Ensure on: cycle/027/integration. Pull latest.
2. Read Agents A + B handoffs.
3. Commit: feat(models): GigQualityScore ORM and write helpers [Agent C Cycle 027]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_external_signal.py tests/unit/test_gig_detail.py
Pass: all A+B tests pass.

## TASKS

### Task 1: Preflight + read all handoffs + read specs
Read: docs/cycle_reports/CYCLE_027_AGENT_A.md, CYCLE_027_AGENT_B.md
Read: PM_Pack/ref/project_plan/03_data/SCHEMA.md (gig_quality_scores table)
Read: src/scoring/weakness.py (_load_signals_from_db method — understand field names)
Read: src/models/ to verify GigQualityScore does not already exist

### Task 2: Read relevant E02/E04 Jira story before coding
Query SCRUM-17 children for any gig quality story. Also read SCRUM-172 (E04 S4.8
GigQualityWeakness story) for the full AC/DoD listing expected fields.
Post planning comment on SCRUM-172 noting GigQualityScore ORM this cycle.

### Task 3: Create src/models/gig_quality_score.py — GigQualityScore ORM

class GigQualityScore(Base):
  __tablename__ = "gig_quality_scores"
  id: int (PK autoincrement)
  gig_id: int (nullable, ForeignKey to gigs.id — may be resolved by gig_url)
  gig_url: str (not null, indexed)
  keyword_id: int (ForeignKey keywords.id, nullable, indexed)
  run_id: str (nullable, indexed)
  analysis_complete: bool (not null, default False)

  # Score components (0.0 to 1.0 normalized, nullable until LLM runs)
  description_quality_score: float (nullable)   — higher = better quality (inverted for weakness)
  weakness_count: int (nullable)                — count of identified weaknesses (0-10+)
  thumbnail_quality_score: float (nullable)     — higher = better thumbnail
  faq_completeness_score: float (nullable)      — higher = more complete FAQ
  package_differentiation_score: float (nullable) — higher = better differentiated
  niche_specificity_score: float (nullable)     — higher = more niche-specific

  # Collection-based fields (populated without LLM)
  video_present: bool (nullable)
  portfolio_count: int (nullable)

  # LLM metadata
  llm_model_used: str (nullable)              — "gpt-4o", "gpt-4o-mini", etc.
  llm_prompt_version: str (nullable)
  analysis_notes: str (nullable)

  # Timestamps
  analysed_at: datetime (nullable)
  ttl_hours: int (default 720)

  UniqueConstraint("gig_url", "run_id")
  Index on (keyword_id, analysis_complete)
  Index on (gig_url)

### Task 4: Add GigQualityScore helpers

def write_gig_quality_score(
  gig_url: str,
  keyword_id: int,
  run_id: str,
  video_present: bool | None,
  portfolio_count: int | None,
  analysis_complete: bool,
  description_quality_score: float | None,
  weakness_count: int | None,
  db,
) -> "GigQualityScore | None":
  """Upserts a GigQualityScore row. Returns None if not a Session."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return None
  from datetime import datetime, UTC
  row = GigQualityScore(
    gig_url=gig_url, keyword_id=keyword_id, run_id=run_id,
    video_present=video_present, portfolio_count=portfolio_count,
    analysis_complete=analysis_complete,
    description_quality_score=description_quality_score,
    weakness_count=weakness_count,
    analysed_at=datetime.now(UTC) if analysis_complete else None,
  )
  db.merge(row)
  db.commit()
  return row

def get_gig_quality_scores(keyword_id: int, db) -> list["GigQualityScore"]:
  """Returns all GigQualityScore rows for a keyword."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return []
  return (db.query(GigQualityScore)
    .filter(GigQualityScore.keyword_id == keyword_id)
    .all())

def get_analysis_complete_count(keyword_id: int, db) -> int:
  """Returns count of gigs with analysis_complete=True for a keyword."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return 0
  return (db.query(GigQualityScore)
    .filter(GigQualityScore.keyword_id == keyword_id,
            GigQualityScore.analysis_complete == True).count())

### Task 5: Register GigQualityScore in src/models/__init__.py
Add import + __all__ + helper exports. Verify:
  python -c "from src.models import GigQualityScore; print(GigQualityScore.__tablename__)"

### Task 6: Verify weakness.py can use GigQualityScore
Read src/scoring/weakness.py._load_signals_from_db().
Verify the fields it tries to read (video_absence_rate, portfolio_absence_rate,
  analysis_complete) match GigQualityScore field names.
If there is a mismatch, document in your report — do NOT change weakness.py this cycle.

### Task 7: Write tests (tests/unit/test_gig_quality_score.py)
Required (minimum 14):
- test_gig_quality_score_table_name → "gig_quality_scores"
- test_gig_quality_score_insert_minimal → gig_url + run_id, query back
- test_gig_quality_score_insert_full → all fields, no exception
- test_gig_quality_score_unique_constraint → duplicate (gig_url, run_id) fails
- test_gig_quality_score_nullable_scores → all score fields can be None
- test_gig_quality_score_default_analysis → analysis_complete = False
- test_write_giq_dict_db → None returned
- test_write_giq_orm → row persisted
- test_write_giq_upsert → second call updates row
- test_get_scores_empty → []
- test_get_scores_for_keyword → returns correct rows
- test_get_analysis_complete_count_none → 0 when no complete rows
- test_get_analysis_complete_count_some → correct count
- test_gig_quality_score_in_base_metadata → "gig_quality_scores" in Base.metadata

### Task 8: Targeted patch coverage
python -m pytest -q --cov=src.models.gig_quality_score --cov-report=term-missing
All new code >= 90% covered.

### Task 9: Full validation block
All 6 commands. Target: >= 1477 tests. Coverage >= 90%.

### Task 10: Post Jira evidence
SCRUM-172 (E04 S4.8 weakness): "Cycle 027 Agent C: GigQualityScore ORM created.
  gig_quality_scores table with all weakness calculator fields. write_gig_quality_score(),
  get_gig_quality_scores(), get_analysis_complete_count() helpers. 14 tests.
  DoD remaining: real LLM analysis writes to this table, weakness calculator reads from it."

### Tasks 11-16: Standard completion
11. Update ACTIVE_STORY_DOD_LEDGER.md
12. Artifact hygiene
13. No-main / worktree check. Record SHA. Handoff to Agent D.
14. Create docs/cycle_reports/CYCLE_027_AGENT_C.md
15. Commit scoped files
16. Run python run.py collect-only + phase2-smoke → must pass

## COMMIT INSTRUCTIONS
git add src/models/gig_quality_score.py src/models/__init__.py
git add tests/unit/test_gig_quality_score.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_027_AGENT_C.md
git commit -m "feat(models): GigQualityScore ORM and write helpers [Agent C Cycle 027]"
====================================================================
END OF AGENT C PROMPT
====================================================================
