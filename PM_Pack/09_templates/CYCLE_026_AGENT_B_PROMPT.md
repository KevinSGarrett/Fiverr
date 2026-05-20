====================================================================
AGENT B — CYCLE 026 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/026/integration
- Python 3.11+ | Playwright async (mocked in tests) | SQLAlchemy 2.0

## ⚠️ HARD GATE + SCOPE GAP CONTEXT

codecov/patch >= 90% is a hard merge blocker. Run targeted coverage before handoff.

Cycle 025 Agent B pivoted to RetryHandler instead of Workflow 3 real implementation.
That gap is now YOUR responsibility. The SearchResult ORM was built by Agent A this cycle.
Workflow 3's real (non-dry_run) implementation is YOUR primary deliverable.

## YOUR ROLE
Implement the real Playwright navigation path for Workflow 3 (Fiverr Search Collection).
This replaces the NotImplementedError stub with actual:
- page.goto() to Fiverr search URL
- total_result_count extraction via SEARCH_RESULT_COUNT selector
- Gig card collection via GIG_CARD_CONTAINER selector + _extract_gig_card()
- write_search_result() DB write
- Job row creation for each gig URL (for Workflow 4)
All tests still use AsyncMock — no real browser launched.

## GIT INSTRUCTIONS
1. Ensure on: cycle/026/integration. Pull latest.
2. Read Agent A handoff before coding.
3. Commit: feat(collection): Workflow 3 real Playwright implementation [Agent B Cycle 026]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_search_result.py
Pass: branch=cycle/026/integration, Agent A SearchResult tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + read specs
Read: docs/cycle_reports/CYCLE_026_AGENT_A.md
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflow 3 full spec)
Read: src/collection/fiverr_selectors.py (all selector constants)
Read: src/collection/session_manager.py (new_page, close_page API)
Read: src/models/search_result.py (write_search_result from Agent A)
Read: src/models/job.py (Job model for gig detail job creation)

### Task 2: Read E02 S2.8 Jira story (SCRUM-148) before coding
Read full AC/DoD. Post planning comment noting "Workflow 3 real impl this cycle."

### Task 3: Implement real Workflow 3 in src/collection/workflows/fiverr_search.py

Replace the NotImplementedError path with real implementation.
Pattern: keep existing dry_run=True path intact, replace only the else clause.

```python
# In run_fiverr_search_collection() — real implementation (dry_run=False path):
from src.collection.fiverr_selectors import (
    SEARCH_RESULT_COUNT, GIG_CARD_CONTAINER,
    GIG_CARD_TITLE, GIG_CARD_SELLER_NAME, GIG_CARD_SELLER_LEVEL,
    GIG_CARD_PRICE, GIG_CARD_REVIEW_COUNT, GIG_CARD_LINK, GIG_CARD_SPONSORED,
)
from src.models.search_result import write_search_result
from src.models.job import Job

url = build_fiverr_search_url(keyword_text)
gig_cards = []
total_result_count = None
gig_urls_queued = 0

page = await session_manager.new_page()
try:
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    await pacing_manager.wait("fiverr_search", dry_run=False)

    count_el = await page.query_selector(SEARCH_RESULT_COUNT)
    if count_el:
        total_result_count = _parse_result_count(await count_el.inner_text())

    card_els = await page.query_selector_all(GIG_CARD_CONTAINER)
    for i, card in enumerate(card_els[:20]):
        data = await _extract_gig_card(card, i + 1)
        if data:
            gig_cards.append(data)

    write_search_result(keyword_id=keyword_id, run_id=run_id,
        total_result_count=total_result_count,
        pagination_depth=None, gig_cards=gig_cards, page_collected=1, db=db)

    gig_urls_queued = _queue_gig_detail_jobs(
        keyword_id, niche_id, run_id, gig_cards, depth, db)

except Exception:
    raise
finally:
    await session_manager.close_page(page)

return {"keyword_id": keyword_id, "keyword_text": keyword_text,
        "total_result_count": total_result_count,
        "gig_cards_collected": len(gig_cards),
        "gig_urls_queued": gig_urls_queued,
        "pages_collected": 1, "dry_run": False}
```

Also implement:
async def _extract_gig_card(card_element, position: int) -> dict | None:
  """Extracts structured data from a single gig card Playwright element."""
  (Use selectors: GIG_CARD_TITLE, GIG_CARD_SELLER_NAME, GIG_CARD_PRICE,
   GIG_CARD_LINK, GIG_CARD_SPONSORED — all from fiverr_selectors.py)

def _parse_result_count(text: str) -> int | None:
  """Parses '1,234 results for X' → 1234."""
  import re
  if not text: return None
  nums = re.findall(r"[\d]+", text.replace(",", ""))
  return int(nums[0]) if nums else None

def _parse_price(text: str | None) -> float | None:
  """Parses '$95' → 95.0."""
  import re
  if not text: return None
  nums = re.findall(r"[\d.]+", text)
  return float(nums[0]) if nums else None

def _queue_gig_detail_jobs(keyword_id, niche_id, run_id, gig_cards, depth, db) -> int:
  """Creates Job rows for gig URLs based on depth. Returns count queued."""
  from sqlalchemy.orm import Session
  from datetime import datetime, UTC
  import uuid
  if depth == "keyword_only" or not isinstance(db, Session):
    return 0
  top_n = {"full": 20, "standard": 10, "feasibility": 5}.get(depth, 10)
  queued = 0
  for card in gig_cards[:top_n]:
    if not card.get("gig_url"): continue
    db.add(Job(
      job_id=f"gig_detail_{uuid.uuid4().hex[:12]}",
      run_id=run_id, job_type="GIG_DETAIL", stage=4,
      niche_id=niche_id, priority="STANDARD", status="QUEUED",
      payload={"gig_url": card["gig_url"], "keyword_id": keyword_id},
      created_at=datetime.now(UTC),
    ))
    queued += 1
  db.commit()
  return queued

### Task 4: Write tests for Workflow 3 real implementation
Add to tests/unit/test_collection_workflows.py (extend existing file).
All tests use AsyncMock for session_manager/page. NO real browser.
Required (minimum 15 new tests):
- test_w3_real_navigates_to_correct_url — page.goto called with Fiverr URL
- test_w3_real_calls_pacing_wait — pacing_manager.wait called
- test_w3_real_extracts_result_count — mock returns count text → int
- test_w3_real_collects_gig_cards — mock card_elements → list populated
- test_w3_real_writes_search_result — write_search_result called with correct args
- test_w3_real_queues_gig_detail_jobs — standard depth → Job rows created
- test_w3_real_keyword_only_no_jobs — keyword_only depth → 0 jobs queued
- test_w3_real_closes_page_on_success — close_page called in finally
- test_w3_real_closes_page_on_error — exception → close_page still called
- test_w3_real_max_20_cards — > 20 elements → capped at 20
- test_parse_result_count_with_commas — "1,234 results" → 1234
- test_parse_result_count_none → None → None
- test_parse_price_dollar — "$95" → 95.0
- test_parse_price_none → None → None
- test_queue_jobs_full_depth — full depth → up to 20 jobs created

### Task 5: Targeted patch coverage
python -m pytest -q --cov=src.collection.workflows.fiverr_search --cov-report=term-missing
All new code >= 90% covered.

### Task 6: Full validation block
All 6 commands. Target: >= 1376 tests. Coverage >= 90%.

### Task 7: Post Jira evidence for SCRUM-148
Post: "Cycle 026 Agent B: Workflow 3 real Playwright implementation complete.
  page.goto() + selector-based gig card extraction + write_search_result() DB write
  + Job queue creation for Workflow 4. 15 tests (AsyncMock). All tests passing.
  DoD remaining: validated against live Fiverr session with real data."

### Tasks 8-16: Standard completion
8. Update ACTIVE_STORY_DOD_LEDGER.md
9. Artifact hygiene
10. No-main / worktree check
11. Record SHA. Handoff to Agent C.
12. Create docs/cycle_reports/CYCLE_026_AGENT_B.md
13. Commit scoped files
14. Run python run.py phase2-smoke → must pass
15. Run python run.py collect-only → must pass
16. Final SHA + test count

## COMMIT INSTRUCTIONS
git add src/collection/workflows/fiverr_search.py
git add tests/unit/test_collection_workflows.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_026_AGENT_B.md
git commit -m "feat(collection): Workflow 3 real Playwright implementation [Agent B Cycle 026]"
====================================================================
END OF AGENT B PROMPT
====================================================================
