====================================================================
AGENT D — CYCLE 023 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/023/integration
- Python 3.11+ | Pydantic v2 | GitHub CLI

## ⚠️ MANDATORY MERGE GATE — APPLIES TO EVERY TASK YOU DO

This is the MANDATORY protocol. Failure to follow either point blocks the merge:

1. codecov/patch ≥ 90% — HARD BLOCKER
   If patch shows < 90%, add tests. Push. Wait for re-check. Confirm PASS. Then merge.

2. Codex review threads — ALL must be queried, classified, replied, resolved.
   Run the EXACT GraphQL query. Document every thread. Fix VALID_FIXED with regression
   test. Reply to ALL threads with disposition format. Resolve ALL threads manually.

You MUST fill and post the complete merge gate checklist in your report AND as a PR comment.
No merge recommendation without all checklist items showing PASS/YES.

## YOUR ROLE
Agent D owns: (1) E09 dashboard display schemas for OpportunityCard and PricingDisplay
(Pydantic schemas that the dashboard can consume), (2) final patch coverage audit for
all modules from cycles 020-023, (3) board reconciliation, (4) PR #27 with full merge
gate checklist. Every function you write must be tested before creating the PR.

## GIT INSTRUCTIONS
1. Ensure on: cycle/023/integration. Pull latest.
2. Read ALL A/B/C handoffs before starting.
3. Commit: feat(dashboard): E09 display schemas and patch coverage [Agent D Cycle 023]
4. gh pr create --base develop --head cycle/023/integration
   --title "feat(cycle-023): Task 12 pricing, E07 discovery, E09 schemas, patch coverage"
5. After CI settles: verify ALL checks including codecov/patch. Handle Codex. Fill checklist.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass with coverage ≥ 90%.

## TASKS

### Task 1: Read all A/B/C handoffs + run full suite
Read all 3 cycle reports. Run full validation block. Record count and coverage.

### Task 2: Run comprehensive patch coverage audit
Run targeted coverage for every module touched in cycles 020-023:
  python -m pytest -q --cov=src.scoring.pipeline --cov-report=term-missing
  python -m pytest -q --cov=src.recommendations --cov-report=term-missing
  python -m pytest -q --cov=src.pricing --cov-report=term-missing
  python -m pytest -q --cov=src.schemas --cov-report=term-missing
  python -m pytest -q --cov=src.models.discovery --cov-report=term-missing
  python -m pytest -q --cov=src.discovery --cov-report=term-missing
Document: for every file, list uncovered lines.

### Task 3: Add patch gap tests for any uncovered lines
Add to existing test files. Target: ≥ 90% coverage on every module.
Add minimum 8 targeted gap tests.

### Task 4: Read E09 Dashboard spec and Jira stories before coding
Read: PM_Pack/ref/project_plan/07_reporting/DASHBOARD_PLAN.md
Read: PM_Pack/ref/project_plan/12_dashboard_ux/DESIGN_SYSTEM.md
Query SCRUM-24 children. Find E09 dashboard schema stories. Read AC/DoD.
Transition first 2 stories to In Progress. Post planning comments.

### Task 5: Create src/dashboard/schemas/opportunity_card.py
Spec: DASHBOARD_PLAN.md (OpportunityCard section)

from pydantic import BaseModel, Field
from typing import Optional

class ScoreBreakdown(BaseModel):
  demand: float | None = None
  competition: float | None = None
  opportunity: float | None = None
  feasibility: float | None = None
  profitability: float | None = None
  confidence_modifier: float | None = None

class OpportunityCardSchema(BaseModel):
  """Display schema for a single keyword opportunity card in the dashboard."""
  keyword_id: int
  keyword_text: str
  niche_id: str
  niche_name: str | None = None
  tag: str  # STRONG_GO / CONDITIONAL_GO / MONITOR / CAUTION / PASS
  final_score: float = Field(..., ge=0.0, le=100.0)
  confidence_modifier: float = Field(..., ge=0.0, le=1.0)
  score_breakdown: ScoreBreakdown
  red_flags: list[str] = Field(default_factory=list)
  missing_data_warnings: list[str] = Field(default_factory=list)
  explanation_text: str | None = None
  scored_at: str | None = None  # ISO datetime string for serialization
  rank: int | None = None
  percentile: float | None = None  # 0-100

  @classmethod
  def from_keyword_score(cls, ks: "KeywordScore", rank: int | None = None) -> "OpportunityCardSchema":
    """Builds OpportunityCardSchema from a KeywordScore ORM row."""
    breakdown = ScoreBreakdown(
      demand=ks.demand_score,
      competition=ks.competition_score,
      opportunity=ks.opportunity_score,
      feasibility=ks.feasibility_score,
      profitability=ks.profitability_score,
      confidence_modifier=ks.confidence_modifier,
    )
    return cls(
      keyword_id=ks.keyword_id,
      keyword_text="",  # caller populates from Keyword table
      niche_id="",
      tag=ks.tag or "MONITOR",
      final_score=ks.final_score or 0.0,
      confidence_modifier=ks.confidence_modifier or 0.0,
      score_breakdown=breakdown,
      red_flags=[f["flag"] for f in (ks.red_flags or [])],
      missing_data_warnings=ks.missing_data_warnings or [],
      explanation_text=ks.explanation_text,
      scored_at=ks.scored_at.isoformat() if ks.scored_at else None,
      rank=rank,
    )

### Task 6: Create src/dashboard/schemas/pricing_display.py
from pydantic import BaseModel, Field

class PriceLadderDisplayStep(BaseModel):
  milestone_reviews: int
  label: str
  basic: float
  standard: float
  premium: float
  basic_increase_pct: float = 0.0

class PricingDisplaySchema(BaseModel):
  """Display schema for pricing strategy in the dashboard."""
  keyword_id: int
  keyword_text: str
  market_type: str | None = None
  moat_strength: str | None = None
  entry_basic: float
  entry_standard: float
  entry_premium: float
  acquisition_basic: float | None = None
  target_basic: float | None = None
  target_standard: float | None = None
  target_premium: float | None = None
  undercut_pct: float | None = None
  confidence: str | None = None  # HIGH / MEDIUM / LOW
  price_ladder: list[PriceLadderDisplayStep] = Field(default_factory=list)
  strategy_narrative: str | None = None
  llm_pricing_strategy: dict | None = None  # Task 12 output
  revenue_projections: dict | None = None

  @classmethod
  def from_pricing_recommendation(cls, pr: "PricingRecommendation", keyword_text: str) -> "PricingDisplaySchema":
    steps = [PriceLadderDisplayStep(**step) for step in pr.price_ladder]
    return cls(
      keyword_id=pr.keyword_id,
      keyword_text=keyword_text,
      market_type=pr.market_type,
      moat_strength=None,
      entry_basic=pr.entry_basic,
      entry_standard=pr.entry_standard,
      entry_premium=pr.entry_premium,
      acquisition_basic=pr.acquisition_basic,
      target_basic=pr.target_basic,
      target_standard=pr.target_standard,
      target_premium=pr.target_premium,
      undercut_pct=pr.undercut_pct,
      confidence=pr.confidence,
      price_ladder=steps,
    )

### Task 7: Create src/dashboard/__init__.py with exports
Export: OpportunityCardSchema, PricingDisplaySchema, ScoreBreakdown, PriceLadderDisplayStep

### Task 8: Write tests for dashboard schemas (tests/unit/test_dashboard_schemas.py)
Create: tests/unit/test_dashboard_schemas.py
Required tests (minimum 14):
- test_opportunity_card_valid_construction — all required fields, no exception
- test_opportunity_card_tag_required — tag missing → ValidationError
- test_opportunity_card_score_range — final_score > 100 → ValidationError
- test_opportunity_card_from_keyword_score — from_keyword_score returns correct schema
- test_opportunity_card_red_flags_extracted — red_flags dict list → flat string list
- test_opportunity_card_defaults — empty red_flags, missing_data_warnings default to []
- test_pricing_display_valid_construction — all required fields, no exception
- test_pricing_display_price_ladder_empty — empty ladder list accepted
- test_pricing_display_from_pricing_rec — from_pricing_recommendation returns schema
- test_pricing_display_ladder_steps — price_ladder has correct milestone structure
- test_score_breakdown_all_none — all None fields accepted
- test_score_breakdown_populated — populated values stored correctly
- test_pricing_display_narrative_none — strategy_narrative defaults None
- test_opportunity_card_json_serializable — .model_dump() produces JSON-safe dict

### Task 9: Run targeted patch coverage
python -m pytest -q --cov=src.dashboard --cov-report=term-missing
All new dashboard code ≥ 90% covered.

### Task 10: Run targeted tests
python -m pytest -q tests/unit/test_dashboard_schemas.py tests/unit/test_discovery.py
All must pass.

### Task 11: Run full validation block
All 6 commands. Target: ≥ 1141 tests. Coverage ≥ 90%.

### Task 12: Board reconciliation
Verify: SCRUM-511 Done, SCRUM-512 In Progress, SCRUM-19/20/21/22/24/25 In Progress.
E07 S7.1 and E09 dashboard schema stories: In Progress.
Correct any stale statuses.

### Task 13: Commit patch gap + dashboard schemas before creating PR
Message: feat(dashboard): E09 display schemas and patch coverage [Agent D Cycle 023]

### Task 14: Create PR #27
gh pr create --base develop --head cycle/023/integration \
  --title "feat(cycle-023): Task 12 pricing, E07 discovery, E09 schemas, patch coverage"
PR body: summary, Jira keys, changed files, validation, AC/DoD table, guardrails.

### Task 15: Monitor ALL CI checks — codecov/patch is a HARD BLOCKER
gh pr checks [PR_NUMBER] — wait for ALL to settle.
Required: Lint/Typecheck/Tests/Gates SUCCESS, codecov/project SUCCESS, codecov/patch SUCCESS.
If codecov/patch FAILURE: add tests, push, re-check. DO NOT merge until PASS.

### Task 16: ⚠️ MANDATORY CODEX DISPOSITION QUERY (for PR #27)
Run the EXACT Codex query:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=[PR_NUMBER]
Document: raw result, total threads found.
If 0: "Codex query confirmed 0 review threads. No disposition required."
If any threads:
  - Classify: VALID_FIXED | VALID_DEFERRED_BLOCKER | VALID_DEFERRED_NONBLOCKING | NOT_APPLICABLE | FALSE_POSITIVE
  - VALID_FIXED: fix code, add regression test, push, wait for CI, reply, resolve thread
  - Others: evidence reply, note in PR body, resolve thread
  - EVERY thread must be replied to and resolved before merge

### Task 17: ⚠️ FILL AND POST MANDATORY MERGE GATE CHECKLIST
Post this EXACTLY in your report AND as a PR comment on PR #27:

```
MERGE GATE CHECKLIST — Cycle 023 PR #27
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
[ ] PR #27 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```
ALL items MUST show PASS/YES before recommending merge.

### Task 18: Final SHA freeze
git rev-parse origin/cycle/023/integration → final pushed SHA. Match to PR head.
Post freeze comment to PR #27.

### Task 19-22: Final cleanup
19. Confirm all 4 agent reports present.
20. Artifact hygiene (no .env, *.db, coverage.xml staged).
21. Create docs/cycle_reports/CYCLE_023_AGENT_D.md (sections: all A/B/C handoffs,
    patch coverage audit, dashboard schema design, CI results, Codex disposition,
    board reconciliation, merge gate checklist filled, final SHA, merge recommendation).
22. State: "PR #27 is ready to merge when approved." or list blockers.

## COMMIT INSTRUCTIONS
git add src/dashboard/ tests/unit/test_dashboard_schemas.py
git add tests/unit/test_pricing_strategy.py tests/unit/test_recommendations.py
git add tests/unit/test_discovery.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_023_AGENT_D.md
git commit -m "feat(dashboard): E09 display schemas and patch coverage [Agent D Cycle 023]"
====================================================================
END OF AGENT D PROMPT
====================================================================
