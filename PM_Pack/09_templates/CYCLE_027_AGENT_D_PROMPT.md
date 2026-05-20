====================================================================
AGENT D — CYCLE 027 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/027/integration
- Python 3.11+ | asyncio | SQLAlchemy 2.0 | GitHub CLI

## ⚠️ MANDATORY MERGE GATE — NO EXCEPTIONS

RULE G-001: codecov/patch >= 90% — HARD BLOCKER. Add tests if FAIL. Never merge.
RULE G-003: Run Codex query. Classify ALL threads. Fix VALID_FIXED with regression test.
  Reply ALL threads. Resolve ALL manually. Document verbatim.
RULE G-004: Fill COMPLETE merge gate checklist in report AND PR comment. ALL PASS/YES.

## YOUR ROLE
Agent D owns: (1) collect-only end-to-end integration test (Stages 1-3 with mock session
verifying actual DB writes to search_results and jobs tables), (2) comprehensive patch
coverage audit for all new Cycle 027 modules, (3) board reconciliation, (4) PR #31.

## GIT INSTRUCTIONS
1. Ensure on: cycle/027/integration. Pull latest.
2. Read ALL A/B/C handoffs.
3. Commit: feat(integration): collect-only e2e test and patch coverage [Agent D Cycle 027]
4. gh pr create --base develop --head cycle/027/integration
   --title "feat(cycle-027): ExternalSignal+GigQualityScore ORMs, Workflow 4 real, collect-only e2e"
5. After CI: verify ALL checks. codecov/patch MUST be PASS. Handle Codex. Fill checklist.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass, coverage >= 90%.

## TASKS

### Task 1: Read all A/B/C handoffs + run full suite
Read all 3 cycle reports. Run full validation. Record count and coverage.

### Task 2: Read SCRUM-231 (E10 End-to-End) before coding
Read AC/DoD for SCRUM-231. Confirm: integration test with mock session will advance
this story. Post planning comment noting collect-only e2e test this cycle.

### Task 3: Create tests/integration/test_collect_only_e2e.py
This tests the Stage 1-3 pipeline with in-memory SQLite + AsyncMock SessionManager.
It verifies that after running collect-only, real rows are in the DB.

Implement:

```python
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.models import Base, SearchResult, Job, Keyword

@pytest.fixture
def db():
    """In-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Seed a test keyword
    kw = Keyword(id=1, keyword_text="ai proofreading fiverr",
                 niche_id="test_niche", autocomplete_position=1)
    session.add(kw)
    session.commit()
    yield session
    session.close()

@pytest.fixture
def mock_session_manager():
    """Mocked SessionManager that returns a page with realistic Fiverr-like elements."""
    mock_page = AsyncMock()
    # Mock total result count
    mock_count_el = AsyncMock()
    mock_count_el.inner_text = AsyncMock(return_value="1,234 results for ai proofreading fiverr")
    mock_page.query_selector = AsyncMock(return_value=mock_count_el)
    # Mock 3 gig card elements
    def make_card(pos):
        card = AsyncMock()
        title_el = AsyncMock(); title_el.inner_text = AsyncMock(return_value=f"Test Gig {pos}")
        seller_el = AsyncMock(); seller_el.inner_text = AsyncMock(return_value=f"seller_{pos}")
        price_el = AsyncMock(); price_el.inner_text = AsyncMock(return_value=f"${pos * 25}")
        link_el = AsyncMock(); link_el.get_attribute = AsyncMock(return_value=f"/gig_url_{pos}")
        async def mock_qs(selector):
            if "title" in selector.lower(): return title_el
            if "seller" in selector.lower(): return seller_el
            if "price" in selector.lower(): return price_el
            if "link" in selector.lower() or "href" in selector.lower(): return link_el
            return None
        card.query_selector = mock_qs
        return card
    mock_page.query_selector_all = AsyncMock(return_value=[make_card(i) for i in range(1, 4)])
    mock_page.goto = AsyncMock()
    mock_sm = AsyncMock()
    mock_sm.new_page = AsyncMock(return_value=mock_page)
    mock_sm.close_page = AsyncMock()
    return mock_sm

@pytest.fixture
def mock_pacing_manager():
    mock_pm = AsyncMock()
    mock_pm.wait = AsyncMock(return_value=0.0)
    return mock_pm
```

Required integration tests (minimum 14):
- test_collect_only_search_results_table_exists — "search_results" in DB tables
- test_collect_only_jobs_table_exists — "jobs" in DB tables
- test_collect_only_w3_writes_search_result — SearchResult row present after W3 run
- test_collect_only_w3_result_has_keyword_id — SearchResult.keyword_id == 1
- test_collect_only_w3_total_result_count_parsed — total_result_count == 1234
- test_collect_only_w3_gig_cards_json — gig_cards is list with 3 entries
- test_collect_only_w3_queues_gig_detail_jobs — Job rows created for standard depth
- test_collect_only_w3_job_type_gig_detail — Job.job_type == "GIG_DETAIL"
- test_collect_only_w3_job_status_queued — Job.status == "QUEUED"
- test_collect_only_w3_close_page_called — close_page called after page operations
- test_collect_only_w3_keyword_only_no_jobs — depth="keyword_only" → 0 Job rows
- test_collect_only_niche_init_returns_seeds — Stage 1 returns seed_keywords dict
- test_collect_only_result_structure — return dict has required keys
- test_collect_only_all_stages_execute — stages list has stage01 through stage03 entries

### Task 4: Verify tests/integration/__init__.py exists
If missing: echo "" > tests/integration/__init__.py

### Task 5: Comprehensive patch coverage audit for Cycle 027 new modules
  python -m pytest -q --cov=src.models.external_signal --cov-report=term-missing
  python -m pytest -q --cov=src.models.gig_quality_score --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows.gig_detail --cov-report=term-missing
Document uncovered lines. Add gap tests (minimum 8).

### Task 6: Full validation block
All 6 commands + python run.py collect-only.
Target: >= 1492 tests. Coverage >= 90%.

### Task 7: Board reconciliation
Verify: SCRUM-515 Done, SCRUM-516 In Progress, SCRUM-17 In Progress.
SCRUM-172 (weakness): In Progress. SCRUM-231: In Review.

### Task 8: Post SCRUM-231 progress comment
Post: "Cycle 027 integration test evidence: tests/integration/test_collect_only_e2e.py
  (14 tests) verifies Stage 1-3 pipeline with mock session writes SearchResult rows
  and Job queue entries to in-memory SQLite DB. All assertions passing. This is the
  first automated evidence that the collection → DB write pipeline executes correctly.
  Status: keep In Review pending live authenticated session run with real Fiverr data."

### Task 9: Post SCRUM-17 epic progress comment
Post: "Cycle 027: ExternalSignal ORM, GigQualityScore ORM, Workflow 4 real implementation,
  collect-only e2e integration test all complete. DB model inventory now includes:
  search_results, gigs, sellers, external_signals, gig_quality_scores, keyword_scores,
  price_analyses, jobs, discovery_candidates. All scoring calculators have real DB
  query paths. Next cycle: scoring calculators run with real collected data."

### Task 10: Commit integration test + patch gap tests before PR

### Task 11: Create PR #31
gh pr create --base develop --head cycle/027/integration \
  --title "feat(cycle-027): ExternalSignal+GigQualityScore ORMs, Workflow 4 real, collect-only e2e"
PR body: all deliverables, Jira keys (SCRUM-516, SCRUM-141, SCRUM-149, SCRUM-172, SCRUM-231),
  changed files, validation, AC/DoD, guardrails.

### Task 12: Monitor ALL CI checks — codecov/patch HARD BLOCKER
If codecov/patch FAILURE: add tests, push, re-check. DO NOT merge.

### Task 13: ⚠️ MANDATORY CODEX DISPOSITION QUERY
Run GraphQL query for PR #31. Document verbatim.
If 0: "0 threads confirmed. No disposition required."
If any: classify → fix VALID_FIXED + regression → reply ALL → resolve ALL.

### Task 14: ⚠️ FILL MANDATORY MERGE GATE CHECKLIST
Post EXACTLY in report AND as PR comment on PR #31:

```
MERGE GATE CHECKLIST — Cycle 027 PR #31
==========================================
CODECOV:
[ ] codecov/project: [PASS/FAIL] — [exact %]
[ ] codecov/patch: [PASS/FAIL] — [exact %]
[ ] Local --cov-fail-under=90: [PASS/FAIL]
[ ] All new lines covered by tests: [YES/NO]
  If NO, uncovered files: [list or N/A]

CODEX:
[ ] reviewThreads query executed: YES
[ ] Total threads found: [N]
[ ] All threads dispositioned: [YES/N/A]
[ ] All VALID_FIXED threads have regression tests: [YES/N/A]
[ ] All threads manually resolved with reply: [YES/N/A]
[ ] Zero unresolved threads: [YES]

FINAL:
[ ] PR #31 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```

ALL items MUST show PASS/YES before recommending merge.

### Tasks 15-22: Final cleanup
15. Final SHA freeze.
16. Confirm all 4 agent reports present.
17. Update ACTIVE_STORY_DOD_LEDGER.md
18. Create docs/cycle_reports/CYCLE_027_AGENT_D.md
19. Artifact hygiene
20. No-main / worktree check
21. Post SCRUM-516 final steward summary
22. "PR #31 is ready to merge when approved." or list blockers.

## COMMIT INSTRUCTIONS
git add tests/integration/test_collect_only_e2e.py tests/integration/__init__.py
git add tests/unit/ docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_027_AGENT_D.md
git commit -m "feat(integration): collect-only e2e test and patch coverage [Agent D Cycle 027]"
====================================================================
END OF AGENT D PROMPT
====================================================================
