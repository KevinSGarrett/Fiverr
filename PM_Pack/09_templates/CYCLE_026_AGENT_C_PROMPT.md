====================================================================
AGENT C — CYCLE 026 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/026/integration
- Python 3.11+ | SQLAlchemy 2.0

## ⚠️ HARD GATE REMINDER
codecov/patch >= 90% hard blocker. Run targeted coverage on all new files.

## YOUR ROLE
Agent C builds the Gig ORM model — the target table for Workflow 4 (Gig Detail
Collection). The Gig model stores individual gig data collected from gig detail pages.
Also adds write_gig_card() helper so the collection orchestrator has a write path.
Spec: PM_Pack/ref/project_plan/03_data/SCHEMA.md (gigs table section)
      PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (W4 output spec)

## GIT INSTRUCTIONS
1. Ensure on: cycle/026/integration. Pull latest.
2. Read Agents A + B handoffs.
3. Commit: feat(models): Gig ORM and write_gig_card helper [Agent C Cycle 026]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_search_result.py tests/unit/test_collection_workflows.py
Pass: all A+B tests pass.

## TASKS

### Task 1: Preflight + read all handoffs + read spec
Read: docs/cycle_reports/CYCLE_026_AGENT_A.md, CYCLE_026_AGENT_B.md
Read: PM_Pack/ref/project_plan/03_data/SCHEMA.md (gigs + gig_quality_scores tables)
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (W4 output)
Read: src/models/ to check if Gig model already exists (src/models/market.py perhaps)

### Task 2: Read E02 S2.9 Jira story (SCRUM-149) before coding
Read full AC/DoD for gig detail collection. Post planning comment.

### Task 3: Verify or create Gig ORM model
Check: does src/models/market.py or src/models/gig.py have a Gig class?
If a partial model exists: extend it to include all required fields below.
If not: create src/models/gig.py

class Gig(Base):
  __tablename__ = "gigs"
  id: int (PK autoincrement)
  gig_url: str (unique, not null)
  keyword_id: int (ForeignKey keywords.id, nullable, indexed)
  run_id: str (nullable, indexed)
  seller_username: str (not null, indexed)
  gig_title_full: str (nullable)
  description_text: str (nullable)
  packages: JSON (nullable)        — list of {tier, price, delivery_days, items}
  gig_extras: JSON (nullable)      — list of {name, price, description}
  tags: JSON (nullable)            — list of tag strings
  faq_text: str (nullable)         — concatenated FAQ Q+A text
  video_present: bool (nullable)
  portfolio_count: int (nullable)
  review_count_exact: int (nullable)
  rating_exact: float (nullable)
  review_snippets: JSON (nullable) — list of {reviewer, rating, text} dicts
  starting_price: float (nullable)
  thumbnail_url: str (nullable)
  orders_in_queue: int (nullable)
  position: int (nullable)         — position in search results page
  detail_collected: bool (default False)
  detail_collected_at: datetime (nullable)
  ttl_hours: int (default 168)
  sponsored_flag: bool (default False)

  Index on (keyword_id, detail_collected)
  Index on (seller_username)
  Index on (run_id, keyword_id)

Helper methods:
  def is_stale(self) -> bool:
    from datetime import datetime, UTC, timedelta
    if not self.detail_collected or not self.detail_collected_at: return True
    return datetime.now(UTC) > self.detail_collected_at + timedelta(hours=self.ttl_hours)

### Task 4: Add write_gig_card() helper

def write_gig_card(
  gig_url: str,
  keyword_id: int,
  run_id: str,
  seller_username: str,
  position: int,
  starting_price: float | None,
  gig_title: str | None,
  sponsored_flag: bool,
  db,
) -> "Gig | None":
  """
  Upserts a minimal Gig row from search card data.
  Call this from Workflow 3 output. Returns None if db is not a Session.
  """
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return None
  row = Gig(
    gig_url=gig_url, keyword_id=keyword_id, run_id=run_id,
    seller_username=seller_username, position=position,
    starting_price=starting_price, gig_title_full=gig_title,
    sponsored_flag=sponsored_flag, detail_collected=False,
  )
  db.merge(row)
  db.commit()
  return row

def get_gigs_for_keyword(keyword_id: int, db, limit: int = 20) -> list["Gig"]:
  """Returns up to `limit` gigs for a keyword, ordered by position."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return []
  return (db.query(Gig)
    .filter(Gig.keyword_id == keyword_id)
    .order_by(Gig.position.asc().nullslast())
    .limit(limit).all())

### Task 5: Register Gig in src/models/__init__.py
Add import and __all__ entry. Verify:
  python -c "from src.models import Gig; print(Gig.__tablename__)"

### Task 6: Write tests for Gig model (tests/unit/test_gig_model.py)
Required (minimum 14):
- test_gig_table_name → "gigs"
- test_gig_insert_minimal → gig_url + seller_username, query back
- test_gig_insert_full → all fields, no exception
- test_gig_unique_gig_url → duplicate gig_url fails
- test_gig_detail_collected_default → False
- test_gig_is_stale_not_collected → True (never collected)
- test_gig_is_stale_fresh → False (recent)
- test_gig_is_stale_expired → True (past TTL)
- test_write_gig_card_dict_db → None returned
- test_write_gig_card_orm → row persisted
- test_write_gig_card_upsert → second call updates
- test_get_gigs_for_keyword_empty → []
- test_get_gigs_for_keyword_ordered → ordered by position
- test_gig_packages_json → packages stores list of dicts

### Task 7: Targeted patch coverage
python -m pytest -q --cov=src.models.gig --cov-report=term-missing
All new code >= 90% covered.

### Task 8: Full validation block
All 6 commands. Target: >= 1390 tests. Coverage >= 90%.

### Task 9: Post Jira evidence for SCRUM-149
Post: "Cycle 026 Agent C: Gig ORM model created (gigs table, all fields from spec,
  write_gig_card() helper, get_gigs_for_keyword(), is_stale() method). 14 tests.
  DoD remaining: Workflow 4 real Playwright writes gig details to this table."

### Tasks 10-16: Standard completion
10. Update ACTIVE_STORY_DOD_LEDGER.md
11. Artifact hygiene
12. No-main / worktree check. Record SHA. Handoff to Agent D.
13. Create docs/cycle_reports/CYCLE_026_AGENT_C.md
14. Commit scoped files
15. Run python run.py collect-only → must pass
16. Final SHA + test count

## COMMIT INSTRUCTIONS
git add src/models/gig.py src/models/__init__.py
git add tests/unit/test_gig_model.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_026_AGENT_C.md
git commit -m "feat(models): Gig ORM and write_gig_card helper [Agent C Cycle 026]"
====================================================================
END OF AGENT C PROMPT
====================================================================
