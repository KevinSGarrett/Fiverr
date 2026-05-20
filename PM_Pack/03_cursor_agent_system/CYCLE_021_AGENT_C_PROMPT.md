====================================================================
AGENT C — CYCLE 021 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/021/integration
- Python 3.11+ | SQLAlchemy 2.0 | Pydantic v2

## YOUR ROLE
Agent C starts E06 Pricing Engine. You have two deliverables:
(1) PriceAnalysis ORM model — the data structure that stores price distribution analysis
    for a keyword (medians, CV, gaps, market type, moat strength).
(2) new_seller_pricing.py — the pricing calculator that converts PriceAnalysis +
    NicheConfig into a full PricingRecommendation with entry prices, acquisition prices,
    price ladder, revenue projections.

Both are specified in full detail in PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md.
Read that file completely before writing a single line of code.

## GIT INSTRUCTIONS
1. Ensure on: cycle/021/integration. Pull latest.
2. Read Agent A + B handoffs before coding.
3. All work on cycle/021/integration.
4. Commit: feat(pricing): PriceAnalysis model and new_seller_pricing calculator [Agent C Cycle 021]
5. Do NOT push — human operator pushes.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_scoring.py tests/unit/test_keyword_score.py
Pass: branch = cycle/021/integration, Agent A+B tests pass.

## TASKS

### Task 1: Preflight + read Agent A/B handoffs + read spec files
Read: docs/cycle_reports/CYCLE_021_AGENT_A.md, CYCLE_021_AGENT_B.md
Read: PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md (FULL file — required)
Read: PM_Pack/ref/project_plan/09_pricing/PRICE_DISTRIBUTION_ANALYSIS.md (if exists)
Read: src/models/ directory (understand Base, existing models for import pattern)
Note from Agent B handoff: exact SCRUM-21 child story keys for S6.1 and S6.2.

### Task 2: Read E06 Jira story keys before coding
Use the story keys provided by Agent B in their handoff.
Read full story description, AC, and DoD for S6.1 (Price Distribution Analysis) and
S6.2 (New Seller Pricing Calculator).
Transition S6.1 and S6.2 from To Do to In Progress.
Post planning comment on each key with your implementation scope.

### Task 3: Create src/models/pricing.py — PriceAnalysis ORM model
Spec: PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md

class PriceAnalysis(Base):
  __tablename__ = "price_analyses"
  id: int (PK autoincrement)
  keyword_id: int (ForeignKey keywords.id, indexed)
  run_id: str (indexed)
  analyzed_at: datetime (UTC, default now)

  # Basic tier statistics
  basic_n: int (nullable — count of prices in sample)
  basic_min: float (nullable)
  basic_max: float (nullable)
  basic_median: float (nullable)
  basic_mean: float (nullable)
  basic_cv: float (nullable — coefficient of variation)
  basic_skewness: float (nullable)
  basic_gaps: JSON (nullable — list of gap dicts with gap_midpoint, gap_width, pct_of_range)

  # Standard tier statistics
  standard_n: int (nullable)
  standard_min: float (nullable)
  standard_max: float (nullable)
  standard_median: float (nullable)
  standard_mean: float (nullable)

  # Premium tier statistics
  premium_n: int (nullable)
  premium_min: float (nullable)
  premium_max: float (nullable)
  premium_median: float (nullable)
  premium_mean: float (nullable)

  # Market characterization
  market_type: str (nullable — "COMMODITY", "MODERATE_SPREAD", "WIDE_SPREAD", "FRAGMENTED")
  moat_strength: str (nullable — "HIGH", "MEDIUM", "LOW")
  review_premium: float (nullable — extra price commanded by sellers with 50+ reviews)

UniqueConstraint on (keyword_id, run_id).
Index on (keyword_id, analyzed_at.desc()).

Definition of Done:
  - [ ] All fields present and typed correctly
  - [ ] Inherits from Base
  - [ ] JSON fields use SQLAlchemy JSON type
  - [ ] Constraints and indexes defined
  - [ ] Table creatable via Base.metadata.create_all()

### Task 4: Register PriceAnalysis in src/models/__init__.py
Add: from src.models.pricing import PriceAnalysis
Verify: python -c "from src.models import PriceAnalysis; print(PriceAnalysis.__tablename__)"

### Task 5: Create src/pricing/new_seller_pricing.py — pricing calculator
Spec: PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md

Implement the FULL spec from that file including:

@dataclass
class PricingRecommendation:
  keyword_id, keyword_text, niche_id
  entry_basic, entry_standard, entry_premium (float)
  acquisition_basic, acquisition_standard, acquisition_premium (float)
  price_ladder: list[dict]  # per-milestone prices
  target_basic, target_standard, target_premium (float)
  undercut_pct, moat_adjustment (float)
  gap_pricing_used: bool
  gap_target: float | None
  market_type, confidence (str)

def calculate_new_seller_pricing(keyword_id, price_analysis, niche_config, db) -> PricingRecommendation:
  Implements the 10-step calculator from the spec:
  1. Determine reference prices (market medians from PriceAnalysis)
  2. Calculate undercut_pct via _calculate_undercut(price_analysis)
  3. Apply moat adjustment via _calculate_moat_adjustment(price_analysis)
  4. Find price gap via _find_gap_opportunity(price_analysis)
  5. Calculate entry prices = ref * (1 - total_discount)
  6. Apply gap targeting if applicable and beneficial
  7. Apply floor prices via _get_floor_price()
  8. Ensure tier ordering (basic < standard < premium)
  9. Acquisition prices = entry * (1 - acquisition_discount)
  10. Build price ladder via _build_price_ladder()

def _calculate_undercut(price_analysis) -> float:  (base 0.05-0.40 by market_type + density + skewness)
def _calculate_moat_adjustment(price_analysis) -> float:  (0.00/0.05/0.10 by moat_strength)
def _find_gap_opportunity(price_analysis) -> tuple[float|None, bool]:  (returns gap_midpoint, should_use)
def _get_floor_price(tier, niche_config) -> float:  ($15/$30/$50 dignity floors)
def _build_price_ladder(entry_basic, entry_standard, entry_premium,
  target_basic, target_standard, target_premium) -> list[dict]:
  (6 milestones: 0/5/10/25/50/100 reviews with lerped prices)
def _lerp(start, end, progress) -> float:
def _apply_discount(price, discount_pct) -> float:
def _assess_pricing_confidence(price_analysis) -> str:  ("HIGH"/"MEDIUM"/"LOW" by basic_n)

Also implement:
def project_revenue_at_entry_pricing(pricing, niche_config) -> dict:
  REVENUE_GATES = {4: 1720, 6: 4770, 9: 17795, 10: 25045, 12: 37500}
  Returns projections per month gate with orders_needed, orders_per_month, feasible flag.

### Task 6: Create src/pricing/__init__.py with exports
Export: PricingRecommendation, calculate_new_seller_pricing, project_revenue_at_entry_pricing

### Task 7: Ensure src/pricing/ directory has __init__.py
Check: src/pricing/ already exists (created during audit). If not, create it.
The directory was created as a stub in audit PR #16. Add real __init__.py with exports.

### Task 8: Write tests for PriceAnalysis model (tests/unit/test_pricing.py)
Create: tests/unit/test_pricing.py
Required tests (minimum 20):
Model tests:
- test_price_analysis_table_name → "price_analyses"
- test_price_analysis_create_all → table created in in-memory DB
- test_price_analysis_insert → insert row, query back
- test_price_analysis_nullable_json → basic_gaps can be None
- test_price_analysis_unique_constraint → duplicate (keyword_id, run_id) fails

Calculator tests:
- test_calculate_undercut_commodity → COMMODITY market → base 0.10
- test_calculate_undercut_wide_spread → WIDE_SPREAD → base 0.25
- test_calculate_undercut_crowded → basic_n > 15 → adds 0.05
- test_calculate_moat_high → moat HIGH → 0.10
- test_calculate_moat_low → moat LOW → 0.00
- test_find_gap_below_median → gap_midpoint < median and pct_of_range > 15 → returns gap
- test_find_gap_no_gaps → empty gaps → None, False
- test_floor_prices_basic → floor $15 applied
- test_floor_prices_premium → floor $50 applied
- test_price_ladder_6_milestones → ladder has 6 entries
- test_price_ladder_milestone_0 → milestone 0 = entry prices
- test_price_ladder_milestone_100 → milestone 100 = target prices
- test_lerp_midpoint → lerp(0, 100, 0.5) == 50
- test_calculate_new_seller_pricing_basic → returns PricingRecommendation with all fields
- test_entry_less_than_standard → entry_basic < entry_standard always
- test_acquisition_less_than_entry → acquisition_basic < entry_basic
- test_project_revenue_month_4 → month_4 gate returns orders_needed and feasible
- test_confidence_high_n → basic_n >= 10 → "HIGH"
- test_confidence_low_n → basic_n < 5 → "LOW"

### Task 9: Run targeted tests
python -m pytest -q tests/unit/test_pricing.py
All 20+ tests must pass. Record count.

### Task 10: Run full scoring + recommendations suite (no regression)
python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py tests/unit/test_keyword_score.py tests/unit/test_recommendations.py
All must pass.

### Task 11: Run ruff + mypy on pricing module
python -m ruff check src/models/pricing.py src/pricing/new_seller_pricing.py tests/unit/test_pricing.py
python -m mypy src/models/pricing.py src/pricing/
Both must pass. Fix all type errors.

### Task 12: Run full validation block
All 6 commands. Total tests >= 985 (965 + 20 new). Coverage >= 90%.

### Task 13: Post Jira evidence for E06 S6.1 and S6.2
For S6.1 (PriceAnalysis): "Cycle 021 Agent C: PriceAnalysis ORM model created in
  src/models/pricing.py. market_type, moat_strength, basic/standard/premium stats,
  gap detection fields. Table registered in Base.metadata. 5 model tests passing.
  DoD remaining: real collection data feeding into analysis, dashboard integration."
For S6.2 (new_seller_pricing.py): "Cycle 021 Agent C: calculate_new_seller_pricing()
  implemented with 10-step formula, undercut strategy, moat adjustment, gap detection,
  price ladder (6 milestones), floor prices, acquisition pricing. 15 pricing tests passing.
  DoD remaining: connected to scoring pipeline, LLM pricing LLM task, dashboard display."

### Task 14: Post SCRUM-21 (E06 epic) status comment
Comment: "E06 Pricing Engine started in Cycle 021. S6.1 (PriceAnalysis model) and S6.2
  (new_seller_pricing.py calculator) implemented. 20 tests. Full validation pass.
  Remaining E06 scope (S6.3-S6.8): price distribution analysis runner, revenue gate tracker,
  LLM pricing LLM task, dashboard pricing widgets."

### Task 15: Read src/pricing/__init__.py and orchestrator.py (if exists)
After creating your files, read what currently exists in src/pricing/ from the audit scaffold.
If orchestrator.py exists there, leave it unchanged. Only add your new files.

### Task 16: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent C rows
Add rows for E06 S6.1 and S6.2 story keys with files, AC advanced, DoD remaining, validation.

### Task 17: Verify PriceAnalysis in Base.metadata table list
python -c "from src.models import Base; print([t for t in Base.metadata.tables])"
Confirm "price_analyses" appears. Record output.

### Task 18: No-main / artifact hygiene / worktree check
git worktree list → canonical root only. No main changes.
Commit only: src/models/pricing.py, src/pricing/new_seller_pricing.py, src/pricing/__init__.py,
tests/unit/test_pricing.py, ledger, report.

### Task 19: Record SHA and handoff to Agent D
git rev-parse HEAD → record.
Handoff to Agent D: "PriceAnalysis model + pricing calculator implemented. E06 S6.1/S6.2
In Progress. Agent D: wire E05 end-to-end test, advance SCRUM-231, create PR #25."

### Task 20: Create Agent C report at docs/cycle_reports/CYCLE_021_AGENT_C.md
Sections: Preflight, E06 story keys, PriceAnalysis design (all fields), pricing calculator
design, 10-step formula summary, price ladder design, test count, validation block, handoff.

### Task 21: Verify calculate_new_seller_pricing handles None PriceAnalysis gracefully
Test behavior when price_analysis.basic_median is None → uses niche_config fallback prices.
Document the None-safe behavior in your report and ensure it's tested.

### Task 22: Check niche_config key names match existing config.yaml structure
Read config.yaml. Find the relevant niche pricing fields.
Ensure new_seller_pricing.py references the correct config keys:
  niche_config.get("starter_price_basic") vs niche_config["metadata"]["starter_price_basic"]
Document which key path is correct in your report.

### Task 23: Commit scoped changes
Message: feat(pricing): PriceAnalysis model and new_seller_pricing calculator [Agent C Cycle 021]

### Task 24: Run python run.py phase2-smoke one final time
Confirm phase2-smoke still passes after all pricing module additions.
Record output in report.

## FILES CREATED THIS CYCLE (Agent C)
| Action | File |
|---|---|
| CREATE | src/models/pricing.py |
| MODIFY | src/models/__init__.py |
| MODIFY | src/pricing/__init__.py |
| CREATE | src/pricing/new_seller_pricing.py |
| CREATE | tests/unit/test_pricing.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_021_AGENT_C.md |

## COMMIT INSTRUCTIONS
git add src/models/pricing.py src/models/__init__.py src/pricing/
git add tests/unit/test_pricing.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_021_AGENT_C.md
git commit -m "feat(pricing): PriceAnalysis model and new_seller_pricing calculator [Agent C Cycle 021]"
====================================================================
END OF AGENT C PROMPT
====================================================================
