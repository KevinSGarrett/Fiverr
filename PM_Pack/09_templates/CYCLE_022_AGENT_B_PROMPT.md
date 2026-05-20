====================================================================
AGENT B — CYCLE 022 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/022/integration
- Python 3.11+ | SQLAlchemy 2.0 | statistics module

## ⚠️ PROTOCOL CORRECTION — APPLIES TO ALL AGENTS
codecov/patch is a hard merge blocker. If Agent D's PR check shows codecov/patch FAIL,
you are required to add more tests for your files. Agent D will request this if needed.
Make sure every new function you write in this cycle has at least one direct test.

## YOUR ROLE
Agent B builds E06 S6.3 — the price distribution analysis runner. After gig prices
are collected for a keyword, someone needs to analyze the distribution (median, CV,
gaps, market type, moat strength) and write a PriceAnalysis row to the DB. That is
your job: create src/pricing/analysis.py with the runner function that processes
raw gig price data and produces a PriceAnalysis result.

## GIT INSTRUCTIONS
1. Ensure on: cycle/022/integration. Pull latest.
2. Read Agent A handoff before coding.
3. All work on cycle/022/integration.
4. Commit: feat(pricing): price distribution analysis runner [Agent B Cycle 022]
5. Do NOT push — human operator pushes.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_scoring_pipeline.py tests/unit/test_keyword_score.py
Pass: branch = cycle/022/integration, Agent A tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + read spec files
Read: docs/cycle_reports/CYCLE_022_AGENT_A.md
Read: PM_Pack/ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md
Read: PM_Pack/ref/project_plan/09_pricing/PRICE_DISTRIBUTION_ANALYSIS.md (if exists)
Read: src/models/pricing.py (PriceAnalysis ORM from Cycle 021)
Read: src/models/market.py (Gig model — where to get gig prices)
Read: src/pricing/new_seller_pricing.py (existing calculator)

### Task 2: Read E06 S6.3 Jira story before coding
Query SCRUM-21 children → find S6.3 story key (likely SCRUM-189 or similar).
Read full story description, AC, and DoD.
Transition S6.3 to In Progress. Post planning comment.

### Task 3: Create src/pricing/analysis.py — PriceDistributionAnalyzer
Implement:

from statistics import median, mean, stdev, variance
from dataclasses import dataclass

@dataclass
class RawPriceData:
  keyword_id: int
  run_id: str
  basic_prices: list[float]     # list of starting prices from top-N gigs
  standard_prices: list[float]  # list of standard tier prices
  premium_prices: list[float]   # list of premium tier prices
  seller_review_counts: list[int] # review count per gig (same order as prices)
  seller_levels: list[str]      # "NO_LEVEL", "LEVEL_1", "LEVEL_2", "TRS", "PRO"

def run_price_distribution_analysis(
  raw: RawPriceData,
  db,
) -> PriceAnalysis:
  """
  Analyzes price distribution from raw gig data and returns a PriceAnalysis ORM row.
  """
  basic_stats = _compute_tier_stats(raw.basic_prices)
  standard_stats = _compute_tier_stats(raw.standard_prices)
  premium_stats = _compute_tier_stats(raw.premium_prices)

  market_type = _classify_market_type(basic_stats)
  moat_strength = _classify_moat_strength(raw)
  review_premium = _calculate_review_premium(raw)
  basic_gaps = _find_price_gaps(raw.basic_prices) if raw.basic_prices else []

  row = PriceAnalysis(
    keyword_id=raw.keyword_id,
    run_id=raw.run_id,
    basic_n=basic_stats["n"],
    basic_min=basic_stats["min"],
    basic_max=basic_stats["max"],
    basic_median=basic_stats["median"],
    basic_mean=basic_stats["mean"],
    basic_cv=basic_stats["cv"],
    basic_skewness=basic_stats["skewness"],
    basic_gaps=basic_gaps,
    standard_n=standard_stats["n"],
    standard_min=standard_stats["min"],
    standard_max=standard_stats["max"],
    standard_median=standard_stats["median"],
    standard_mean=standard_stats["mean"],
    premium_n=premium_stats["n"],
    premium_min=premium_stats["min"],
    premium_max=premium_stats["max"],
    premium_median=premium_stats["median"],
    premium_mean=premium_stats["mean"],
    market_type=market_type,
    moat_strength=moat_strength,
    review_premium=review_premium,
  )
  if isinstance(db, Session):
    db.merge(row); db.commit()
  return row

def _compute_tier_stats(prices: list[float]) -> dict:
  if not prices:
    return {k: None for k in ("n","min","max","median","mean","cv","skewness")}
  n = len(prices)
  med = median(prices)
  mn = mean(prices)
  sd = stdev(prices) if n > 1 else 0.0
  cv = sd / mn if mn > 0 else 0.0
  # skewness approximation: (mean - median) / std
  skew = (mn - med) / sd if sd > 0 else 0.0
  return {"n": n, "min": min(prices), "max": max(prices),
          "median": med, "mean": mn, "cv": cv, "skewness": skew}

def _classify_market_type(basic_stats: dict) -> str:
  cv = basic_stats.get("cv")
  if cv is None: return "UNKNOWN"
  if cv < 0.20: return "COMMODITY"          # tight pricing
  if cv < 0.35: return "MODERATE_SPREAD"    # normal spread
  if cv < 0.60: return "WIDE_SPREAD"        # wide variation
  return "FRAGMENTED"                        # chaotic pricing

def _classify_moat_strength(raw: RawPriceData) -> str:
  # Moat = established sellers (50+ reviews) charge significantly more
  if not raw.basic_prices or not raw.seller_review_counts:
    return "UNKNOWN"
  established_prices = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts) if r >= 50]
  new_prices = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts) if r < 5]
  if not established_prices or not new_prices: return "LOW"
  premium = mean(established_prices) / mean(new_prices) - 1.0
  if premium > 0.30: return "HIGH"
  if premium > 0.15: return "MEDIUM"
  return "LOW"

def _calculate_review_premium(raw: RawPriceData) -> float | None:
  if not raw.basic_prices or not raw.seller_review_counts: return None
  established = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts) if r >= 50]
  newbie = [p for p, r in zip(raw.basic_prices, raw.seller_review_counts) if r < 5]
  if not established or not newbie: return None
  return round(mean(established) - mean(newbie), 2)

def _find_price_gaps(prices: list[float]) -> list[dict]:
  if len(prices) < 3: return []
  sorted_prices = sorted(prices)
  total_range = sorted_prices[-1] - sorted_prices[0]
  if total_range == 0: return []
  gaps = []
  for i in range(len(sorted_prices) - 1):
    gap_width = sorted_prices[i+1] - sorted_prices[i]
    pct = (gap_width / total_range) * 100
    if pct > 10:  # only report gaps > 10% of total range
      gaps.append({
        "gap_start": sorted_prices[i],
        "gap_end": sorted_prices[i+1],
        "gap_width": round(gap_width, 2),
        "gap_midpoint": round((sorted_prices[i] + sorted_prices[i+1]) / 2, 2),
        "pct_of_range": round(pct, 1),
      })
  return gaps

Also add: def extract_raw_price_data_from_db(keyword_id, run_id, db) -> RawPriceData | None
  - Queries Gig rows for keyword_id
  - Extracts basic/standard/premium prices and seller review counts
  - Returns None if no gig data found

### Task 4: Update src/pricing/__init__.py exports
Add: run_price_distribution_analysis, RawPriceData, extract_raw_price_data_from_db

### Task 5: Write tests for analysis.py (tests/unit/test_pricing_analysis.py)
Create: tests/unit/test_pricing_analysis.py
Required tests (minimum 16):
- test_compute_tier_stats_normal — 5 prices → all stats populated
- test_compute_tier_stats_empty — empty list → all None
- test_compute_tier_stats_single — single price → no crash, cv/skewness safe
- test_classify_commodity — cv=0.10 → COMMODITY
- test_classify_wide_spread — cv=0.50 → WIDE_SPREAD
- test_classify_fragmented — cv=0.70 → FRAGMENTED
- test_moat_high — established sellers charge 35% more → HIGH
- test_moat_low — no significant premium → LOW
- test_moat_missing_data — empty seller_review_counts → UNKNOWN or LOW
- test_find_gaps_meaningful — prices with clear gap → gap_midpoint populated
- test_find_gaps_no_gaps — evenly spaced prices → empty list
- test_find_gaps_too_few_prices — < 3 prices → empty list
- test_run_analysis_dict_db — dict db path → row returned, no DB write attempted
- test_run_analysis_orm_db — Session path → db.merge called
- test_run_analysis_review_premium — established 50% more → positive review_premium
- test_extract_raw_price_data_no_gigs — no Gig rows → returns None

### Task 6: Run targeted tests
python -m pytest -q tests/unit/test_pricing_analysis.py tests/unit/test_pricing.py
All must pass. Record counts.

### Task 7: Run patch coverage check on Agent B files
python -m pytest -q --cov=src/pricing/analysis.py --cov-report=term-missing
Every function must have > 0% coverage. Add tests for any uncovered lines now.
This prevents codecov/patch failure on the final PR.

### Task 8: Run ruff + mypy
python -m ruff check src/pricing/ tests/unit/test_pricing_analysis.py
python -m mypy src/pricing/
Both must pass.

### Task 9: Run full validation block
All 6 commands. Total tests ≥ 1025. Coverage ≥ 90%. Record in report.

### Task 10: Post Jira evidence for E06 S6.3
Post: "Cycle 022 Agent B: Price distribution analysis runner built in src/pricing/analysis.py.
  RawPriceData → PriceAnalysis ORM. Market type classification, moat strength, gap detection.
  16 tests. Full validation pass. DoD remaining: run with real collection data, hook into
  run.py price-analysis stage."

### Task 11-16: Standard completion tasks
11. Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent B rows (E06 S6.3 key).
12. Artifact hygiene — no .env, *.db, coverage.xml staged.
13. No-main / worktree check.
14. Record SHA and handoff to Agent C.
15. Create docs/cycle_reports/CYCLE_022_AGENT_B.md.
16. Commit scoped files only.

Message: feat(pricing): price distribution analysis runner [Agent B Cycle 022]

### Tasks 17-24: E06 forward planning
17. Read SCRUM-21 children for S6.4 story key (likely SCRUM-190).
18. Post planning intent comment on S6.4 for Agent C.
19. Verify python run.py recommendations-only still passes.
20. Verify python run.py phase2-smoke still passes.
21. Confirm .cursorrules compliance.
22. Confirm no push.
23. Final SHA + test count for handoff.
24. Note in handoff: "analysis.py uses statistics module only — no scipy dependency."

## FILES CREATED THIS CYCLE (Agent B)
| Action | File |
|---|---|
| CREATE | src/pricing/analysis.py |
| MODIFY | src/pricing/__init__.py |
| CREATE | tests/unit/test_pricing_analysis.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_022_AGENT_B.md |

## COMMIT INSTRUCTIONS
git add src/pricing/analysis.py src/pricing/__init__.py
git add tests/unit/test_pricing_analysis.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_022_AGENT_B.md
git commit -m "feat(pricing): price distribution analysis runner [Agent B Cycle 022]"
====================================================================
END OF AGENT B PROMPT
====================================================================
