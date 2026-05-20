====================================================================
AGENT C — CYCLE 022 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/022/integration
- Python 3.11+ | SQLAlchemy 2.0 | Click | Jinja2

## ⚠️ PROTOCOL CORRECTION — APPLIES TO ALL AGENTS
codecov/patch is now a hard merge blocker. Every new function you write must be
tested. Before handing off to Agent D, run:
  python -m pytest -q --cov=src/pricing/ --cov-report=term-missing
and add tests for any uncovered lines. This prevents the PR from being blocked.

## YOUR ROLE
Agent C owns E06 S6.4 and S6.5:
- S6.4: Integrate price distribution analysis into the run.py pipeline as a
  dedicated "price-analysis" stage that can run after scoring.
- S6.5: Create the pricing strategy LLM Jinja2 template and a
  generate_pricing_strategy_text() function that wraps PricingRecommendation
  into a human-readable pricing strategy narrative.

## GIT INSTRUCTIONS
1. Ensure on: cycle/022/integration. Pull latest.
2. Read Agent A + B handoffs.
3. All work on cycle/022/integration.
4. Commit: feat(pricing): pipeline integration and pricing strategy text [Agent C Cycle 022]
5. Do NOT push — human operator pushes.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_pricing.py tests/unit/test_pricing_analysis.py
Pass: all tests pass before you start.

## TASKS

### Task 1: Preflight + read all handoffs + read spec files
Read: docs/cycle_reports/CYCLE_022_AGENT_A.md, CYCLE_022_AGENT_B.md
Read: PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md
Read: src/pricing/analysis.py (Agent B's new file)
Read: src/pricing/new_seller_pricing.py (Agent C's prior work from Cycle 021)
Read: src/pricing/orchestrator.py (existing scaffold — may be empty)
Read: run.py (current pipeline modes)

### Task 2: Read E06 S6.4 and S6.5 Jira stories before coding
Find S6.4 and S6.5 keys from SCRUM-21 children.
Read full AC/DoD for each. Transition to In Progress. Post planning comments.

### Task 3: Implement src/pricing/orchestrator.py — pricing pipeline stage
Replace or augment the existing scaffold in src/pricing/orchestrator.py:

def run_pricing_stage(
  run_id: str,
  keyword_ids: list[int],
  db,
  config,
) -> dict:
  """
  Runs price distribution analysis and calculates new-seller pricing for each keyword.
  Returns summary: {analyzed, priced, failed, run_id}
  """
  summary = {"analyzed": 0, "priced": 0, "failed": 0, "run_id": run_id}
  for keyword_id in keyword_ids:
    try:
      # Step 1: Extract raw price data from DB Gig rows
      raw = extract_raw_price_data_from_db(keyword_id, run_id, db)
      if raw is None:
        summary["failed"] += 1; continue

      # Step 2: Run price distribution analysis → write PriceAnalysis row
      price_analysis = run_price_distribution_analysis(raw, db)
      summary["analyzed"] += 1

      # Step 3: Calculate new-seller pricing recommendation
      niche_config = _get_niche_config_for_keyword(keyword_id, db, config)
      pricing = calculate_new_seller_pricing(keyword_id, price_analysis, niche_config, db)
      summary["priced"] += 1

    except Exception as e:
      summary["failed"] += 1
  return summary

def _get_niche_config_for_keyword(keyword_id: int, db, config) -> dict:
  """Returns niche config dict for a keyword's niche_id."""
  # Try DB path first, then config fallback
  keyword = None
  if isinstance(db, Session):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
  niche_id = getattr(keyword, "niche_id", None)
  niches = config.get("niches", {}) if isinstance(config, dict) else {}
  if niche_id and niche_id in niches:
    return niches[niche_id]
  return {}  # empty dict causes calculator to use dignity floor prices

### Task 4: Wire price-analysis mode into run.py
Add "price-analysis" to AVAILABLE_MODES in run.py.
Add CLI handler: when mode == "price-analysis":
  from src.pricing.orchestrator import run_pricing_stage
  # Get keyword_ids and run_id from DB or use placeholder for smoke path
  result = run_pricing_stage(run_id, keyword_ids=[], db=db_proxy, config=config)
  click.echo(f"Price analysis complete: {result}")
Test: python run.py price-analysis → must not crash and must output summary.
Note: empty keyword_ids is acceptable for smoke; real IDs come from collection stage.

### Task 5: Implement generate_pricing_strategy_text()
Add to src/pricing/new_seller_pricing.py:

def generate_pricing_strategy_text(
  pricing: PricingRecommendation,
  niche_config: dict | None = None,
) -> str:
  """
  Generates a human-readable pricing strategy narrative from a PricingRecommendation.
  No LLM required — deterministic template-based generation.
  """
  ladder_summary = " → ".join(
    f"${step['basic']:.0f} ({step['milestone_reviews']}r)"
    for step in pricing.price_ladder[:5]  # first 5 milestones
  )
  gap_note = (
    f" A price gap exists at ${pricing.gap_target:.0f}."
    if pricing.gap_pricing_used and pricing.gap_target
    else ""
  )
  moat_note = (
    " Review moat detected — established sellers command a premium."
    if pricing.moat_adjustment > 0
    else ""
  )
  return (
    f"Enter at ${pricing.entry_basic:.0f} Basic / ${pricing.entry_standard:.0f} "
    f"Standard / ${pricing.entry_premium:.0f} Premium — "
    f"{pricing.undercut_pct:.0f}% below market median.{gap_note}{moat_note} "
    f"Price ladder: {ladder_summary}. "
    f"Target prices at 100 reviews: ${pricing.target_basic:.0f} / "
    f"${pricing.target_standard:.0f} / ${pricing.target_premium:.0f}. "
    f"Confidence: {pricing.confidence}."
  )

### Task 6: Write tests for pricing orchestrator + strategy text
Extend tests/unit/test_pricing.py with:
- test_run_pricing_stage_empty_keywords — empty keyword_ids → summary.analyzed == 0
- test_run_pricing_stage_no_gig_data — extract_raw returns None → failed count = 1
- test_run_pricing_stage_success — mock raw + analysis + pricing → priced count = 1
- test_run_pricing_stage_exception — exception mid-keyword → failed count = 1, no crash
- test_generate_pricing_strategy_text_basic — returns string with entry prices
- test_generate_pricing_strategy_text_contains_ladder — includes "r)" milestone format
- test_generate_pricing_strategy_text_gap_note — gap_pricing_used=True → mentions gap
- test_generate_pricing_strategy_text_no_gap — gap_pricing_used=False → no gap mention
- test_price_analysis_mode_cli — python run.py price-analysis → no crash (smoke)
Minimum 9 new tests.

### Task 7: Run targeted patch coverage check
python -m pytest -q --cov=src/pricing/ --cov-report=term-missing
Document every uncovered line. Add tests for any uncovered NEW functions.
This is required to prevent codecov/patch failure on the final PR.

### Task 8: Run targeted tests
python -m pytest -q tests/unit/test_pricing.py tests/unit/test_pricing_analysis.py
All must pass. Record counts.

### Task 9: Run ruff + mypy
python -m ruff check src/pricing/ tests/unit/test_pricing.py
python -m mypy src/pricing/
Both must pass.

### Task 10: Run full validation block
All 6 commands. Total tests ≥ 1034. Coverage ≥ 90%.

### Task 11: Post Jira evidence for E06 S6.4 and S6.5
S6.4: "Pipeline integration: run_pricing_stage() orchestrator. price-analysis CLI mode.
  Hooks into run.py AVAILABLE_MODES. 9 tests."
S6.5: "generate_pricing_strategy_text() deterministic narrative. No LLM required.
  Included in PricingRecommendation output path. Tested."

### Tasks 12-24: Standard completion items
12. Update ACTIVE_STORY_DOD_LEDGER.md with E06 S6.4, S6.5 rows.
13. Artifact hygiene check. No .env, *.db, coverage.xml staged.
14. No-main / worktree check.
15. Record SHA and handoff to Agent D.
16. Create docs/cycle_reports/CYCLE_022_AGENT_C.md.
17. Commit scoped files: pricing/orchestrator.py, run.py, pricing/new_seller_pricing.py,
    tests, ledger, report.
18-24. Standard verification (smoke, config-check, phase2-smoke, worktrees, SHA).

## COMMIT INSTRUCTIONS
git add src/pricing/orchestrator.py src/pricing/new_seller_pricing.py run.py
git add tests/unit/test_pricing.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_022_AGENT_C.md
git commit -m "feat(pricing): pipeline integration and pricing strategy text [Agent C Cycle 022]"
====================================================================
END OF AGENT C PROMPT
====================================================================
