====================================================================
AGENT B — CYCLE 023 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/023/integration
- Python 3.11+ | Pydantic v2 | SQLAlchemy 2.0

## ⚠️ HARD GATE REMINDER
codecov/patch must be ≥ 90% on the final PR. For every new function you write,
run: python -m pytest -q --cov=src.recommendations.context --cov-report=term-missing
and add tests for uncovered lines before handing off to Agent D.

## YOUR ROLE
Agent B extends RecommendationContext with the Wave 9 pricing fields from
PRICING_RECOMMENDATIONS_LLM.md and wires the pricing data path so that
generate_pricing_strategy() actually receives real pricing context. The spec adds
6 new optional fields to RecommendationContext (price_distribution, market_type,
calculated_entry_prices, calculated_price_ladder, new_seller_discount_pct,
competitor_price_positions). Agent B adds these fields, updates build_recommendation_context()
to populate them from PriceAnalysis + PricingRecommendation DB data, and adds tests.

## GIT INSTRUCTIONS
1. Ensure on: cycle/023/integration. Pull latest.
2. Read Agent A handoff before coding.
3. All work on cycle/023/integration.
4. Commit: feat(recommendations): extend RecommendationContext with pricing fields [Agent B Cycle 023]
5. Do NOT push — human operator pushes.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_pricing_strategy.py tests/unit/test_recommendations.py
Pass: branch = cycle/023/integration, Agent A tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + read spec
Read: docs/cycle_reports/CYCLE_023_AGENT_A.md
Read: PM_Pack/ref/project_plan/09_pricing/PRICING_RECOMMENDATIONS_LLM.md
  (focus on "Extended RecommendationContext" section)
Read: src/recommendations/context.py (current RecommendationContext fields)
Read: src/models/pricing.py (PriceAnalysis fields)
Read: src/pricing/new_seller_pricing.py (PricingRecommendation dataclass)

### Task 2: Read E05 Jira story for context extension before coding
Read SCRUM-20 children — find a story related to "pricing context" or "recommendation context".
If no specific story exists, note: this work advances SCRUM-183 (context builder) and
the E06 pricing integration stories. Post planning comment on SCRUM-183 and the E06 story.

### Task 3: Add Wave 9 pricing fields to RecommendationContext
Spec: PRICING_RECOMMENDATIONS_LLM.md "Extended RecommendationContext" section.

Add to src/recommendations/context.py (RecommendationContext class):
  # Wave 9 pricing fields — all optional, default None
  price_distribution: dict | None = None
  # {"basic": {"median": float, "mean": float, "min": float, "max": float,
  #             "cv": float, "gaps": list[dict]}, "standard": {...}, "premium": {...}}
  price_review_correlation: dict | None = None
  # {"pearson": float, "moat_strength": str, "review_premium_usd": float,
  #  "new_seller_avg_price": float, "new_seller_discount_pct": float}
  market_type: str | None = None
  calculated_entry_prices: dict | None = None
  # {"basic": int, "standard": int, "premium": int}
  calculated_price_ladder: list[dict] | None = None
  new_seller_discount_pct: float | None = None
  competitor_price_positions: list[dict] | None = None
  # [{"seller": str, "level": str, "reviews": int, "basic": int, "standard": int|None}]

### Task 4: Update build_recommendation_context() to populate pricing fields
In src/recommendations/context.py, update build_recommendation_context():

Add after existing DB queries:

  # --- Wave 9 pricing fields ---
  price_analysis = None
  pricing_rec = None

  # Try to load latest PriceAnalysis for this keyword
  try:
    from src.models.pricing import PriceAnalysis
    if isinstance(db, Session):
      price_analysis = (db.query(PriceAnalysis)
        .filter(PriceAnalysis.keyword_id == keyword_id)
        .order_by(PriceAnalysis.analyzed_at.desc()).first())
  except Exception:
    pass

  # Try to build PricingRecommendation from PriceAnalysis
  if price_analysis:
    try:
      from src.pricing.new_seller_pricing import calculate_new_seller_pricing
      niche_cfg = config.get("niches", {}) if isinstance(config, dict) else {}
      niche_info = {}
      if isinstance(niche_cfg, list):
        for n in niche_cfg:
          if getattr(n, "niche_id", None) == keyword.niche_id:
            niche_info = n.__dict__ if hasattr(n, "__dict__") else {}
            break
      pricing_rec = calculate_new_seller_pricing(keyword_id, price_analysis, niche_info, db)
    except Exception:
      pass

  # Build price_distribution dict from PriceAnalysis
  price_distribution = None
  if price_analysis:
    price_distribution = {
      "basic": {
        "median": price_analysis.basic_median,
        "mean": price_analysis.basic_mean,
        "min": price_analysis.basic_min,
        "max": price_analysis.basic_max,
        "cv": price_analysis.basic_cv,
        "gaps": price_analysis.basic_gaps or [],
      },
      "standard": {
        "median": price_analysis.standard_median,
        "mean": price_analysis.standard_mean,
        "min": price_analysis.standard_min,
        "max": price_analysis.standard_max,
      },
      "premium": {
        "median": price_analysis.premium_median,
        "mean": price_analysis.premium_mean,
        "min": price_analysis.premium_min,
        "max": price_analysis.premium_max,
      },
    }

  # Build price_review_correlation dict
  price_review_correlation = None
  if price_analysis and price_analysis.moat_strength:
    price_review_correlation = {
      "moat_strength": price_analysis.moat_strength,
      "review_premium_usd": price_analysis.review_premium,
      "pearson": None,  # Correlation coefficient not yet computed
      "new_seller_avg_price": None,
      "new_seller_discount_pct": None,
    }

  # Populate competitor_price_positions from top competitor gigs
  competitor_price_positions = []
  if isinstance(db, Session):
    try:
      from src.models.market import Gig, Seller
      top_gigs = (db.query(Gig, Seller)
        .outerjoin(Seller, Gig.seller_username == Seller.username)
        .filter(Gig.keyword_id == keyword_id)
        .order_by(Gig.position.asc()).limit(5).all())
      for gig, seller in top_gigs:
        competitor_price_positions.append({
          "seller": gig.seller_username,
          "level": getattr(seller, "seller_level", "UNKNOWN") if seller else "UNKNOWN",
          "reviews": gig.review_count_visible or 0,
          "basic": gig.starting_price,
          "standard": None,
        })
    except Exception:
      pass

  # Build calculated_entry_prices from PricingRecommendation
  calculated_entry_prices = None
  calculated_price_ladder = None
  if pricing_rec:
    calculated_entry_prices = {
      "basic": pricing_rec.entry_basic,
      "standard": pricing_rec.entry_standard,
      "premium": pricing_rec.entry_premium,
    }
    calculated_price_ladder = [
      {"milestone_reviews": step["milestone_reviews"],
       "basic": step["basic"],
       "standard": step["standard"],
       "premium": step["premium"]}
      for step in pricing_rec.price_ladder
    ]

  # Add all pricing fields to the returned RecommendationContext
  # (Update the RecommendationContext(**...) call to include these new fields)
  return RecommendationContext(
    ... # all existing fields ...
    price_distribution=price_distribution,
    price_review_correlation=price_review_correlation,
    market_type=getattr(price_analysis, "market_type", None),
    calculated_entry_prices=calculated_entry_prices,
    calculated_price_ladder=calculated_price_ladder,
    new_seller_discount_pct=None,  # computed in future cycle
    competitor_price_positions=competitor_price_positions,
  )

### Task 5: Write tests for context pricing extension
Add to tests/unit/test_recommendations.py:
- test_context_pricing_fields_default_none — RecommendationContext has all 7 pricing fields, all default None
- test_context_price_distribution_populated — build_context with PriceAnalysis → price_distribution populated
- test_context_market_type_populated — PriceAnalysis.market_type flows to context.market_type
- test_context_calculated_prices_populated — PricingRecommendation → calculated_entry_prices populated
- test_context_price_ladder_populated — PricingRecommendation ladder → calculated_price_ladder
- test_context_no_price_analysis_safe — no PriceAnalysis → all pricing fields remain None, no crash
- test_context_competitor_positions_populated — Gig rows → competitor_price_positions list
- test_generate_pricing_strategy_with_price_distribution — price_distribution set → task runs
Minimum 8 new tests.

### Task 6: Run targeted patch coverage for context.py
python -m pytest -q --cov=src.recommendations.context --cov-report=term-missing
All new code branches must be ≥90% covered. Add tests for any uncovered branches.

### Task 7: Run full suite and validation block
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
Target: ≥ 1103 tests. Coverage ≥ 90%. All PASS.

### Task 8: Post Jira evidence
Comment on SCRUM-183 and E06 pricing story with context extension evidence and test count.

### Tasks 9-16: Standard completion
9. Update ACTIVE_STORY_DOD_LEDGER.md.
10. Artifact hygiene check. No .env, *.db, coverage.xml staged.
11. No-main / worktree check.
12. Record SHA. Handoff to Agent C.
13. Create docs/cycle_reports/CYCLE_023_AGENT_B.md.
14. Commit scoped files.
15. Run python run.py recommendations-only → must pass.
16. Run python run.py phase2-smoke → must pass.

## COMMIT INSTRUCTIONS
git add src/recommendations/context.py tests/unit/test_recommendations.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_023_AGENT_B.md
git commit -m "feat(recommendations): extend RecommendationContext with pricing fields [Agent B Cycle 023]"
====================================================================
END OF AGENT B PROMPT
====================================================================
