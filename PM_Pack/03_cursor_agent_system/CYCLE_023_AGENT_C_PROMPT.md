====================================================================
AGENT C — CYCLE 023 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/023/integration
- Python 3.11+ | SQLAlchemy 2.0 | Pydantic v2

## ⚠️ HARD GATE REMINDER
codecov/patch ≥ 90% is a hard merge blocker. Run targeted coverage on every file you create:
  python -m pytest -q --cov=src.models.discovery --cov-report=term-missing
  python -m pytest -q --cov=src.discovery --cov-report=term-missing
Add tests for any uncovered lines before handoff to Agent D.

## YOUR ROLE
Agent C starts E07 Discovery Engine — the first new epic since E06 Pricing. You are
building the foundation: the DiscoveryCandidate ORM model that stores niche hypothesis
candidates, and the hypothesis generation stubs that will eventually use LLM to
surface new niche ideas. Also add E09 dashboard OpportunityCard schema.
Spec: PM_Pack/ref/project_plan/10_discovery/DISCOVERY_ENGINE_ARCHITECTURE.md (read in full).

## GIT INSTRUCTIONS
1. Ensure on: cycle/023/integration. Pull latest.
2. Read Agent A + B handoffs.
3. All work on cycle/023/integration.
4. Commit: feat(discovery): DiscoveryCandidate model and hypothesis stubs [Agent C Cycle 023]
5. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_pricing_strategy.py tests/unit/test_recommendations.py
Pass: branch = cycle/023/integration, all A+B tests pass.

## TASKS

### Task 1: Preflight + read all handoffs + read discovery spec
Read: docs/cycle_reports/CYCLE_023_AGENT_A.md, CYCLE_023_AGENT_B.md
Read in full: PM_Pack/ref/project_plan/10_discovery/DISCOVERY_ENGINE_ARCHITECTURE.md
Read: PM_Pack/ref/project_plan/10_discovery/HYPOTHESIS_GENERATION_PROMPTS.md
Read: PM_Pack/ref/project_plan/10_discovery/DISCOVERY_SCORING_AND_FEEDBACK.md
Read: src/discovery/ (existing scaffold from audit PR #16)
Read: PM_Pack/ref/project_plan/07_reporting/DASHBOARD_PLAN.md (for E09 schema)

### Task 2: Read E07 and E09 Jira stories before coding
Query SCRUM-22 children for E07 stories. Read first 2 story descriptions.
Query SCRUM-24 children for E09 stories. Read first 2 story descriptions.
Transition first E07 story (likely S7.1) to In Progress. Post planning comment.
Note exact story keys in your report.

### Task 3: Create src/models/discovery.py — DiscoveryCandidate ORM model
Spec: DISCOVERY_ENGINE_ARCHITECTURE.md (data model section)

class DiscoveryCandidate(Base):
  __tablename__ = "discovery_candidates"
  id: int (PK autoincrement)
  candidate_id: str (unique, e.g. "disc_prd_ai_saas_20260518")
  hypothesis_text: str (the niche hypothesis being tested)
  hypothesis_type: str ("niche_expansion" | "adjacent_keyword" | "trend_signal" |
                        "reddit_thread" | "manual_submission")
  source_signal: str (nullable — what triggered this: keyword_text, reddit_url, etc.)
  source_niche_id: str (nullable — which existing niche spawned this hypothesis)
  status: str ("PENDING" | "EVALUATED" | "ACCEPTED" | "REJECTED" | "MONITORING")
  discovery_score: float (nullable — computed after evaluation)
  market_size_signal: float (nullable)
  competition_gap_signal: float (nullable)
  trend_signal: float (nullable)
  llm_hypothesis_text: str (nullable — LLM-generated description of the opportunity)
  llm_reasoning: str (nullable — LLM explanation of why this is promising)
  created_at: datetime (UTC, default now)
  evaluated_at: datetime (nullable)
  accepted_at: datetime (nullable)
  run_id: str (nullable — which run triggered this discovery)
  user_notes: str (nullable)

Index on (status, discovery_score.desc())
Index on (source_niche_id, created_at)

### Task 4: Register DiscoveryCandidate in src/models/__init__.py
Add import and __all__ entry. Verify:
  python -c "from src.models import DiscoveryCandidate; print(DiscoveryCandidate.__tablename__)"

### Task 5: Create src/discovery/candidates.py — candidate qualification
Implement:

def is_valid_candidate(hypothesis_text: str, existing_niches: list[str]) -> tuple[bool, str]:
  """
  Returns (is_valid, reason).
  Rejects if: < 3 words, > 100 chars, exact match to existing niche name,
  contains blocked terms (adult, spam, etc.), or empty.
  """

def create_discovery_candidate(
  hypothesis_text: str,
  hypothesis_type: str,
  source_signal: str | None,
  source_niche_id: str | None,
  run_id: str | None,
  db,
) -> DiscoveryCandidate | None:
  """Creates and persists a DiscoveryCandidate row. Returns None if invalid."""
  is_valid, reason = is_valid_candidate(hypothesis_text, [])
  if not is_valid: return None
  candidate = DiscoveryCandidate(...)
  if isinstance(db, Session): db.add(candidate); db.commit(); db.refresh(candidate)
  return candidate

def get_pending_candidates(db, limit: int = 50) -> list[DiscoveryCandidate]:
  """Returns up to `limit` PENDING candidates ordered by created_at asc."""
  if not isinstance(db, Session): return []
  return (db.query(DiscoveryCandidate)
    .filter(DiscoveryCandidate.status == "PENDING")
    .order_by(DiscoveryCandidate.created_at.asc()).limit(limit).all())

def update_candidate_status(candidate_id: str, new_status: str, db) -> bool:
  """Updates status field. Returns True on success."""

### Task 6: Create src/discovery/hypothesis.py — hypothesis generation stubs
Spec: HYPOTHESIS_GENERATION_PROMPTS.md

Implement (stubs — LLM calls are feature-flagged):

async def generate_niche_hypotheses(
  source_niche_id: str,
  existing_keywords: list[str],
  llm_client,
  cache,
) -> list[dict]:
  """
  Generates candidate niche hypotheses from an existing niche.
  Returns list of {hypothesis_text, hypothesis_type, source_signal}.
  When llm_client is None: returns empty list (no LLM available).
  """
  if llm_client is None:
    return []
  # LLM path: render prompt, call gpt-4o-mini, parse JSON array of hypotheses
  # Return list of dicts; on failure return []
  ...

def score_hypothesis_signals(
  candidate: DiscoveryCandidate,
  market_size_signal: float | None,
  competition_gap_signal: float | None,
  trend_signal: float | None,
) -> float | None:
  """
  Calculates discovery_score from three signals.
  Weights: market_size 40%, competition_gap 35%, trend 25%.
  Returns None if all three signals are None.
  """
  ...

### Task 7: Create src/discovery/__init__.py with exports
Export: DiscoveryCandidate, is_valid_candidate, create_discovery_candidate,
  get_pending_candidates, update_candidate_status,
  generate_niche_hypotheses, score_hypothesis_signals

### Task 8: Write tests for discovery module (tests/unit/test_discovery.py)
Create: tests/unit/test_discovery.py
Required tests (minimum 16):
- test_discovery_candidate_table_name — "discovery_candidates"
- test_discovery_candidate_insert_minimal — insert row, query back
- test_discovery_candidate_status_enum — valid statuses accepted
- test_discovery_candidate_nullable_fields — all nullable fields can be None
- test_is_valid_candidate_too_short — 1 word → False
- test_is_valid_candidate_too_long — > 100 chars → False
- test_is_valid_candidate_empty — empty → False
- test_is_valid_candidate_valid — 3+ word hypothesis → True
- test_create_candidate_returns_none_for_invalid — invalid text → None
- test_create_candidate_dict_db — dict db → returns DiscoveryCandidate without DB write
- test_create_candidate_orm_db — Session db → candidate persisted
- test_get_pending_candidates_empty — no PENDING → empty list
- test_get_pending_candidates_filters_status — only PENDING returned
- test_update_candidate_status_success — status updated
- test_score_hypothesis_signals_all_present — weighted average computed
- test_score_hypothesis_signals_all_none — returns None
- test_generate_hypotheses_no_llm — llm_client=None → empty list
- test_generate_hypotheses_mock_llm — mock returns list → returned correctly

Minimum 16 tests (some bonus OK).

### Task 9: Run targeted patch coverage
python -m pytest -q --cov=src.models.discovery --cov-report=term-missing
python -m pytest -q --cov=src.discovery --cov-report=term-missing
All new code ≥ 90% covered.

### Task 10: Run targeted tests
python -m pytest -q tests/unit/test_discovery.py
All 16+ tests pass.

### Task 11: Run ruff + mypy
python -m ruff check src/models/discovery.py src/discovery/ tests/unit/test_discovery.py
python -m mypy src/models/discovery.py src/discovery/
Both must pass.

### Task 12: Run full validation block
All 6 commands. Target: ≥ 1119 tests. Coverage ≥ 90%.

### Task 13: Post Jira evidence for E07 S7.1 (and S7.2 if covered)
Post: "Cycle 023 Agent C: DiscoveryCandidate ORM model. candidates.py with validation,
  create, get, update functions. hypothesis.py with generate and score stubs (LLM
  feature-flagged). 16+ tests. Full validation pass. DoD remaining: LLM evaluation
  pipeline, discovery scoring with real signals, discovery dashboard widget."

### Tasks 14-24: Standard completion
14. Update ACTIVE_STORY_DOD_LEDGER.md with E07 story keys.
15. Artifact hygiene check.
16. No-main / worktree check.
17. Record SHA and handoff to Agent D.
18. Create docs/cycle_reports/CYCLE_023_AGENT_C.md.
19. Commit scoped files.
20. Run python run.py phase2-smoke → must pass.
21. Read DASHBOARD_PLAN.md and post discovery context note for Agent D.
22-24. Final SHA, test count, coverage recorded.

## COMMIT INSTRUCTIONS
git add src/models/discovery.py src/discovery/ src/models/__init__.py
git add tests/unit/test_discovery.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_023_AGENT_C.md
git commit -m "feat(discovery): DiscoveryCandidate model and hypothesis stubs [Agent C Cycle 023]"
====================================================================
END OF AGENT C PROMPT
====================================================================
