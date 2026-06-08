# CYCLE 069 — AGENT B HANDOFF (S7.5 TREND CHASE)

Date: 2026-06-07  
Branch: `cycle/069/integration`  
Story: `SCRUM-200` (parent `SCRUM-22`)  
Control: `SCRUM-1031`  
Base SHA reference: `53979fa`

## Scope for B (Exact)

Files to MODIFY: src/discovery/hypothesis.py, src/discovery/contracts.py  
Files to CREATE: tests/unit/test_trend_chase_hypotheses.py  
Files to COMMIT: src/, tests/, docs/CYCLE_069_AGENT_B.md ONLY

Primary intent:
- Implement S7.5 trend-chase hypothesis generation.
- Keep S7.2/S7.3/S7.4 behavior intact.
- Add >=30 substantive tests.

## Required S7.5 Constants

Add module-level constants in `src/discovery/hypothesis.py`:

```python
TREND_SCORE_THRESHOLD: float = 0.60
TREND_VELOCITY_THRESHOLD: float = 0.40
TREND_SCORE_WEIGHT: float = 0.55
TREND_VELOCITY_WEIGHT: float = 0.45
```

Important:
- Same numeric thresholds as S7.4 (`0.60`, `0.40`) but different semantic signal.
- Different weights than S7.4 (`0.55/0.45` vs `0.60/0.40`).

## Required S7.5 Functions

```python
def generate_trend_chase_hypotheses(
    source_niche_id: str,
    keyword_trends: list[dict],
    existing_hypotheses: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
    trend_score_threshold: float = TREND_SCORE_THRESHOLD,
    trend_velocity_threshold: float = TREND_VELOCITY_THRESHOLD,
) -> list[HypothesisContract]:
    ...

def _identify_trending_keywords(
    keyword_trends: list[dict],
    *,
    trend_score_threshold: float = TREND_SCORE_THRESHOLD,
    trend_velocity_threshold: float = TREND_VELOCITY_THRESHOLD,
) -> list[dict]:
    ...

def _score_trend_hypothesis_confidence(
    kw_data: dict,
    *,
    trend_score_weight: float = TREND_SCORE_WEIGHT,
    trend_velocity_weight: float = TREND_VELOCITY_WEIGHT,
) -> float:
    ...
```

## S7.5 Logic Contract

- Trending candidate requires BOTH:
  - `trend_score >= 0.60`
  - `trend_velocity >= 0.40`
- Confidence formula:
  - `0.55 * trend_score + 0.45 * trend_velocity`
  - bounded to `[0.0, 1.0]`
  - no base bonus
- Budget gate default:
  - accepted only when `confidence >= min_confidence` (`0.50` default)
- Output:
  - `list[HypothesisContract]`
  - preserve accepted and rejected outcomes with rationale
- Dedup:
  - compare against `existing_hypotheses`
- Mapping:
  - `hypothesis_text` is the keyword string
  - `niche_id` is `source_niche_id`

## S7.5 vs S7.4 Difference (Do Not Blur)

- S7.4 uses scoring-pipeline demand/competition/opportunity.
- S7.5 uses trend-signal score/velocity.
- S7.5 identifies rising momentum (direction), not only current market state.

## keyword_trends Input Format

```python
keyword_trends = [
    {
        "keyword": "python ai automation agent",
        "trend_score": 0.78,
        "trend_velocity": 0.65,
        "opportunity_score": 0.70,
    },
]
```

Input handling rules:
- Missing score/velocity/opportunity keys default to `0.0`.
- Missing keyword text rows are skipped.
- Empty list must return `[]`.

## Sample Fixture Trend Data (SEED/CI)

```python
SAMPLE_TREND_DATA = [
    {"keyword": "python ai agent automation", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78},
    {"keyword": "workflow automation tool 2025", "trend_score": 0.75, "trend_velocity": 0.70, "opportunity_score": 0.72},
    {"keyword": "established stable market", "trend_score": 0.85, "trend_velocity": 0.15, "opportunity_score": 0.60},
    {"keyword": "declining interest keyword", "trend_score": 0.30, "trend_velocity": 0.10, "opportunity_score": 0.20},
]
```

Expected:
- First two are trend candidates.
- Last two are excluded.

## Required Tests (>=30)

Create `tests/unit/test_trend_chase_hypotheses.py` covering:
- dual-threshold behavior and inclusive boundaries (`>=`)
- all-below-threshold returns no candidates
- all-above-threshold accepts up to max
- sparse/missing-field handling
- empty input behavior
- dedup behavior vs existing hypotheses
- confidence precision and bounds
- `hypothesis_text` and `niche_id` mapping
- rationale/audit-trail behavior for accepted/rejected records

Suggested classes:
- `TestIdentifyTrendingKeywords`
- `TestScoreTrendHypothesisConfidence`
- `TestGenerateTrendChaseHypotheses`

## SCRUM-200 Mapping (7.5.1-7.5.4)

- 7.5.1 trend-based generation: `generate_trend_chase_hypotheses`
- 7.5.2 dual-threshold filter: `_identify_trending_keywords`
- 7.5.3 confidence + lineage/rationale: generator + scorer
- 7.5.4 tests for rising/sparse/dup/empty: new unit file

## TierD-2 Context

- C069 correctness does not require live ScrapFly.
- S7.5 quality improves materially with live trend feeds post TierD-2.
