# CYCLE 068 — AGENT B HANDOFF (S7.4 GAP OPPORTUNITY)

Date: 2026-06-06  
Branch: `cycle/068/integration`  
Base SHA: `19e4ca2`  
Story: `SCRUM-199` (parent `SCRUM-22`)  
Control: `SCRUM-1030`

## Scope for B (Exact)

Files to modify:
- `src/discovery/hypothesis.py` (add S7.4 functions/constants)

Files to possibly modify:
- `src/discovery/contracts.py` (only if `HypothesisMode.GAP_EXPLOIT` were missing; it is already present at C068 base)

Files to create:
- `tests/unit/test_gap_exploit_hypotheses.py` (>=30 substantive tests)

Out of scope for C068 B:
- Live collection wiring and stage orchestration (`S7.6-S7.8`)
- Dashboard widgets (`S7.9`)
- Trend chase mode (`S7.5`)
- Migrations/new DB tables

## Required S7.4 Functions

Implement these in `src/discovery/hypothesis.py`:

```python
def generate_gap_exploit_hypotheses(
    source_niche_id: str,
    keyword_scores: list[dict],
    existing_hypotheses: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
    demand_threshold: float = 0.60,
    competition_threshold: float = 0.40,
) -> list[HypothesisContract]:
    ...

def _identify_gap_keywords(
    keyword_scores: list[dict],
    *,
    demand_threshold: float = 0.60,
    competition_threshold: float = 0.40,
) -> list[dict]:
    ...

def _score_gap_hypothesis_confidence(
    kw_data: dict,
    *,
    demand_weight: float = 0.60,
    opportunity_weight: float = 0.40,
) -> float:
    ...
```

## Required Constants (No Magic Numbers)

Add named constants:

```python
GAP_DEMAND_THRESHOLD: float = 0.60
GAP_COMPETITION_THRESHOLD: float = 0.40
GAP_DEMAND_WEIGHT: float = 0.60
GAP_OPPORTUNITY_WEIGHT: float = 0.40
```

## S7.4 Logic Contract

- Gap candidate criteria: `demand_score >= demand_threshold` AND `competition_score <= competition_threshold`.
- Confidence formula:  
  `confidence = GAP_DEMAND_WEIGHT * demand_score + GAP_OPPORTUNITY_WEIGHT * opportunity_score`
- Confidence must be bounded to `[0.0, 1.0]`.
- Budget gate: candidate accepted only when `confidence >= min_confidence` (default `0.50`).
- Deduplicate against `existing_hypotheses` (normalized case/spacing).
- `hypothesis_text` must be the gap keyword string (not niche ID).
- `niche_id` must be `source_niche_id`.

## S7.4 vs S7.2/S7.3 (Key Difference)

- S7.2 and S7.3 are static-map driven.
- S7.4 is data-driven and requires `keyword_scores` input.
- In SEED mode, S7.4 uses fixture/CI DB score data; do not require live ScrapFly calls.

## keyword_scores Input Format

```python
keyword_scores = [
    {
        "keyword": "python workflow automation",
        "demand_score": 0.75,
        "competition_score": 0.25,
        "opportunity_score": 0.80,
    }
]
```

Validation expectations:
- Missing numeric keys should default to `0.0`.
- Missing/blank `keyword` rows should be skipped.
- Handle sparse/empty lists gracefully (`[]` output, no exception).

## Data Source Notes (C068 Baseline)

`foundation_gate_ci.db` has the score columns in `keyword_scores`:
- `demand_score`
- `competition_score`
- `opportunity_score`
- `final_score`

Observed schema path for keyword text linkage:
- `keyword_scores.keyword_id -> keywords.id`
- keyword string in `keywords.keyword`

## Required Tests (Minimum)

Create `tests/unit/test_gap_exploit_hypotheses.py` with at least:
- Gap filtering at threshold boundaries
- All-below-threshold => no candidates
- All-above-threshold => all candidates eligible
- Confidence formula precision checks
- Confidence bounds and budget gate behavior
- Dedup against existing hypotheses
- Empty keyword_scores returns `[]`
- Sparse/missing-field inputs handled safely
- Verify `hypothesis_text` and `niche_id` mapping
- Verify accepted/rejected rationale strings are explicit

Suggested class layout:
- `TestIdentifyGapKeywords`
- `TestScoreGapHypothesisConfidence`
- `TestGenerateGapExploitHypotheses`

## Acceptance Criteria Mapping (SCRUM-199)

Per story acceptance:
- Gap-based hypotheses generated from weakness/scoring context.
- Hypotheses preserve rationale, lineage, confidence, budget context.
- Tests include candidate generation, duplicate handling, sparse inputs, empty outputs.

This handoff covers `7.4.1` through `7.4.4`.

Verbatim Jira acceptance criteria:
- Gap-based hypotheses are generated from competitor weakness and scoring context.
- Hypotheses preserve rationale, lineage, confidence, and budget context.
- Tests cover candidate generation, duplicate handling, sparse inputs, and empty outputs.

Carry-forward clarification:
- Jira story text does not explicitly spell out fixed numeric thresholds.
- C068 implementation contract sets `demand >= 0.60`, `competition <= 0.40`, and
  `min_confidence >= 0.50` per cycle prompt governance requirements.

## 9 Valid Source Niches

`source_niche_id` must accept any of:
- `ai_agent_development`
- `ai_tool_llm_integration`
- `gumloop_lindy_workflow`
- `mcp_ai_agent`
- `prd_ai_saas`
- `python_automation`
- `python_web_scraping`
- `support_kb_readiness`
- `workflow_automation`
