====================================================================
AGENT B — CYCLE 027 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/027/integration
- Python 3.11+ | Playwright async (mocked in tests) | SQLAlchemy 2.0

## ⚠️ HARD GATE REMINDER
codecov/patch >= 90% hard blocker. Run targeted coverage before handoff.
All tests use AsyncMock — no real Playwright browser launched.

## YOUR ROLE
Agent B implements the real Playwright path for Workflow 4 — Gig Detail Collection.
Workflow 4 navigates to individual gig pages and extracts package tiers, description,
tags, FAQ, video presence, portfolio count, and starting price.
Spec: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflow 4 full spec)

## GIT INSTRUCTIONS
1. Ensure on: cycle/027/integration. Pull latest.
2. Read Agent A handoff before coding.
3. Commit: feat(collection): Workflow 4 real Playwright implementation [Agent B Cycle 027]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_external_signal.py tests/unit/test_gig_model.py
Pass: branch=cycle/027/integration, Agent A tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + read specs
Read: docs/cycle_reports/CYCLE_027_AGENT_A.md
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflow 4 full spec)
Read: src/collection/fiverr_selectors.py (GIG_DETAIL_* selector constants)
Read: src/collection/workflows/gig_detail.py (current stub)
Read: src/models/gig.py (Gig ORM fields to populate from detail page)

### Task 2: Read SCRUM-149 Jira story before coding
Read full AC/DoD. Post planning comment noting real W4 implementation this cycle.

### Task 3: Implement real Workflow 4 in src/collection/workflows/gig_detail.py

Replace the NotImplementedError path:

```python
async def run_gig_detail_collection(
  gig_url, keyword_id, niche_id, run_id, depth,
  db, session_manager, pacing_manager, dry_run=True
) -> dict:
  if dry_run:
    return { ...existing stub... }

  # REAL IMPLEMENTATION:
  from src.collection.fiverr_selectors import (
    GIG_DETAIL_TITLE, GIG_DETAIL_DESCRIPTION, GIG_DETAIL_TAGS,
    GIG_DETAIL_PACKAGE_CONTAINER, GIG_DETAIL_PACKAGE_PRICE,
    GIG_DETAIL_PACKAGE_DELIVERY, GIG_DETAIL_FAQ_CONTAINER,
    GIG_DETAIL_VIDEO_EMBED, GIG_DETAIL_PORTFOLIO_ITEMS,
    GIG_DETAIL_REVIEW_COUNT, GIG_DETAIL_RATING,
  )
  from src.models.gig import Gig
  from sqlalchemy.orm import Session

  detail_url = build_gig_detail_url(gig_url)
  page = await session_manager.new_page()
  try:
    await page.goto(detail_url, wait_until="domcontentloaded", timeout=30_000)
    await pacing_manager.wait("gig_detail", dry_run=False)

    # Extract fields
    title_el = await page.query_selector(GIG_DETAIL_TITLE)
    desc_el = await page.query_selector(GIG_DETAIL_DESCRIPTION)
    title = await title_el.inner_text() if title_el else None
    description = await desc_el.inner_text() if desc_el else None

    # Extract packages
    packages = await _extract_packages(page)

    # Extract tags
    tags = await _extract_tags(page)

    # Extract FAQ
    faq_text = await _extract_faq(page)

    # Check video + portfolio
    video_present = await page.query_selector(GIG_DETAIL_VIDEO_EMBED) is not None
    portfolio_els = await page.query_selector_all(GIG_DETAIL_PORTFOLIO_ITEMS)
    portfolio_count = len(portfolio_els)

    # Extract review count + rating
    review_el = await page.query_selector(GIG_DETAIL_REVIEW_COUNT)
    rating_el = await page.query_selector(GIG_DETAIL_RATING)
    review_count = _parse_review_count(await review_el.inner_text() if review_el else None)
    rating = _parse_rating(await rating_el.inner_text() if rating_el else None)

    # Update Gig row
    if isinstance(db, Session):
      gig = db.query(Gig).filter(Gig.gig_url == gig_url).first()
      if gig:
        gig.gig_title_full = title
        gig.description_text = description
        gig.packages = packages
        gig.tags = tags
        gig.faq_text = faq_text
        gig.video_present = video_present
        gig.portfolio_count = portfolio_count
        gig.review_count_exact = review_count
        gig.rating_exact = rating
        gig.detail_collected = True
        gig.detail_collected_at = datetime.now(UTC)
        db.commit()

    return {
      "gig_url": gig_url, "detail_collected": True,
      "title": title, "description_length": len(description) if description else 0,
      "packages_count": len(packages), "tags_count": len(tags),
      "has_video": video_present, "portfolio_count": portfolio_count,
      "review_count": review_count, "rating": rating,
      "seller_queued": False, "dry_run": False,
    }
  except Exception:
    raise
  finally:
    await session_manager.close_page(page)
```

Implement helpers:
async def _extract_packages(page) -> list[dict]:
  """Extracts package tier pricing from gig detail page."""
  (Use GIG_DETAIL_PACKAGE_CONTAINER, GIG_DETAIL_PACKAGE_PRICE selectors)

async def _extract_tags(page) -> list[str]:
  """Extracts tags from gig detail page."""

async def _extract_faq(page) -> str:
  """Extracts FAQ Q+A concatenated text."""

def _parse_review_count(text: str | None) -> int | None:
  import re
  if not text: return None
  nums = re.findall(r"[\d,]+", text)
  return int(nums[0].replace(",", "")) if nums else None

def _parse_rating(text: str | None) -> float | None:
  import re
  if not text: return None
  nums = re.findall(r"\d+\.\d+|\d+", text)
  return float(nums[0]) if nums else None

### Task 4: Write tests for Workflow 4 real implementation
Add to tests/unit/test_gig_detail.py (extend existing file).
ALL AsyncMock — no real browser.
Required (minimum 15 new tests):
- test_w4_real_navigates_to_gig_url — page.goto called with correct URL
- test_w4_real_calls_pacing_wait — pacing_manager.wait called
- test_w4_real_extracts_title — mock returns title text
- test_w4_real_extracts_description — mock returns description text
- test_w4_real_video_present — mock selector found → True
- test_w4_real_video_absent — mock selector None → False
- test_w4_real_portfolio_count — mock 3 portfolio elements → 3
- test_w4_real_updates_gig_row — Gig.detail_collected=True, detail_collected_at set
- test_w4_real_closes_page_on_success — close_page called in finally
- test_w4_real_closes_page_on_error — exception → close_page still called
- test_w4_real_no_gig_row_in_db — gig_url not in DB → no crash
- test_parse_review_count_with_commas — "1,234" → 1234
- test_parse_review_count_none → None → None
- test_parse_rating_decimal — "4.9" → 4.9
- test_parse_rating_none → None → None

### Task 5: Targeted patch coverage
python -m pytest -q --cov=src.collection.workflows.gig_detail --cov-report=term-missing
All new code >= 90% covered.

### Task 6: Full validation block
All 6 commands. Target: >= 1463 tests. Coverage >= 90%.

### Task 7: Post Jira evidence for SCRUM-149
Post: "Cycle 027 Agent B: Workflow 4 real Playwright implementation complete.
  page.goto + selector-based gig detail extraction (title, description, packages,
  tags, FAQ, video, portfolio, reviews). Updates Gig.detail_collected=True.
  15 tests (AsyncMock). DoD remaining: live session validation with real gig data."

### Tasks 8-16: Standard completion
8. Update ACTIVE_STORY_DOD_LEDGER.md
9. Artifact hygiene
10. No-main / worktree check. Record SHA. Handoff to Agent C.
11. Create docs/cycle_reports/CYCLE_027_AGENT_B.md
12. Commit scoped files
13. Run python run.py collect-only → must pass
14. Run python run.py phase2-smoke → must pass
15. Final SHA + test count
16. Post Agent C planning hint: GigQualityScore fields needed for weakness.py

## COMMIT INSTRUCTIONS
git add src/collection/workflows/gig_detail.py
git add tests/unit/test_gig_detail.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_027_AGENT_B.md
git commit -m "feat(collection): Workflow 4 real Playwright implementation [Agent B Cycle 027]"
====================================================================
END OF AGENT B PROMPT
====================================================================
