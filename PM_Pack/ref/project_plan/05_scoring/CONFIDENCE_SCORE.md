# Confidence Score
# Fiverr Research System — Wave 6, Score 11

**Status:** Complete | **Range:** 0.0–1.0 (multiplier, not 0–100) | **Direction:** Higher = more confident | **Floor:** 0.20 | **Depth:** All

---

## What It Measures
How confident the system is in the keyword's Final Score, based on data completeness, freshness, source diversity, and LLM analysis success rate. **This is a multiplier on the Final Score, not a standalone 0–100 score.**

A confidence_modifier of 1.0 means "all data is fresh, complete, and from multiple sources."
A confidence_modifier of 0.5 means "use this score with caution — significant data gaps."
A confidence_modifier below 0.5 triggers automatic GO/PASS tag demotion.

---

## Data Inputs

| Component | Source | Weight |
|---|---|---|
| Data completeness ratio | All collection tables (field presence vs. expected) | 30% |
| Data freshness score | All collection tables (age vs. TTL) | 30% |
| Source diversity score | external_signals presence + collection success | 20% |
| LLM analysis completion ratio | llm_usage_logs (success vs. failure rate) | 20% |

---

## Full Python Formula

```python
def calculate_confidence_modifier(
    keyword_id: int,
    scores: dict[str, float | None],
    db,
) -> tuple[float, dict]:
    """
    Calculates the Confidence Modifier (0.0–1.0) for a keyword.
    Returns (modifier_value, breakdown_dict).

    The modifier is multiplied into the Final Score, then floored at 0.20
    in calculate_final_score() to prevent any single keyword from being
    scored to zero by low confidence alone.
    """
    components = {}

    # Component 1: Data Completeness (30%)
    completeness = _calculate_data_completeness(keyword_id, scores, db)
    components["data_completeness"] = completeness

    # Component 2: Data Freshness (30%)
    freshness = _calculate_data_freshness(keyword_id, db)
    components["data_freshness"] = freshness

    # Component 3: Source Diversity (20%)
    diversity = _calculate_source_diversity(keyword_id, db)
    components["source_diversity"] = diversity

    # Component 4: LLM Analysis Completion (20%)
    llm_completion = _calculate_llm_completion_ratio(keyword_id, db)
    components["llm_completion"] = llm_completion

    # Weighted composite (all components are 0.0–1.0)
    modifier = (
        completeness["score"]   * 0.30 +
        freshness["score"]      * 0.30 +
        diversity["score"]      * 0.20 +
        llm_completion["score"] * 0.20
    )

    # Build human-readable reason string
    reasons = []
    if completeness["score"] < 0.8:
        reasons.append(f"data completeness {completeness['score']:.0%}")
    if freshness["score"] < 0.8:
        reasons.append(f"data freshness {freshness['score']:.0%}")
    if diversity["score"] < 0.8:
        reasons.append(f"source diversity {diversity['score']:.0%}")
    if llm_completion["score"] < 0.8:
        reasons.append(f"LLM completion {llm_completion['score']:.0%}")

    confidence_reason = (
        "High confidence — all data complete and fresh"
        if not reasons
        else f"Confidence reduced by: {', '.join(reasons)}"
    )

    return round(min(1.0, max(0.0, modifier)), 4), {
        "components": components,
        "reason": confidence_reason,
        "missing_data_warnings": _list_missing_data(keyword_id, scores, db),
    }
```

---

## Component 1: Data Completeness

```python
def _calculate_data_completeness(keyword_id: int, scores: dict, db) -> dict:
    """
    Measures what proportion of expected scores were successfully calculated.
    Returns score (0.0–1.0) and breakdown.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    expected_scores = DEPTH_SCORE_AVAILABILITY[depth]["available_scores"]
    score_field_map = {
        1: "demand_score",       2: "competition_score",
        3: "opportunity_score",  4: "feasibility_score",
        5: "profitability_score", 6: "intent_score",
        7: "saturation_score",   8: "weakness_score",
        9: "trend_score",
    }

    expected = [score_field_map[i] for i in expected_scores if i in score_field_map]
    present = [f for f in expected if scores.get(f) is not None]

    completeness_ratio = len(present) / max(1, len(expected))
    return {
        "score": round(completeness_ratio, 3),
        "expected_count": len(expected),
        "present_count": len(present),
        "missing": [f for f in expected if scores.get(f) is None],
    }
```

---

## Component 2: Data Freshness

```python
from datetime import datetime

def _calculate_data_freshness(keyword_id: int, db) -> dict:
    """
    Measures how fresh the data underlying this keyword's scores is.
    Returns score (0.0–1.0) and oldest contributing record timestamp.

    Uses the formula from FRESHNESS_MODEL.md:
        individual_freshness = max(0.0, 1.0 - staleness_ratio)
        composite = mean(individual_freshness across all contributing records)
    """
    records = _get_all_contributing_records(keyword_id, db)
    if not records:
        return {"score": 0.0, "oldest_record_at": None, "n_records": 0}

    freshness_scores = []
    oldest_at = None
    for record in records:
        age_hours = (datetime.utcnow() - record["collected_at"]).total_seconds() / 3600
        ttl = record.get("ttl_hours", 168)
        ratio = age_hours / ttl  # 0.0 = just collected; 1.0 = at TTL; >1.0 = stale
        individual_freshness = max(0.0, 1.0 - ratio)
        freshness_scores.append(individual_freshness)

        if oldest_at is None or record["collected_at"] < oldest_at:
            oldest_at = record["collected_at"]

    composite = sum(freshness_scores) / len(freshness_scores)
    return {
        "score": round(composite, 3),
        "oldest_record_at": oldest_at.isoformat() if oldest_at else None,
        "n_records": len(freshness_scores),
    }
```

---

## Component 3: Source Diversity

```python
def _calculate_source_diversity(keyword_id: int, db) -> dict:
    """
    Measures how many distinct source types contributed to this keyword's scores.
    More sources = more independent confirmation = higher confidence.

    Expected sources at full depth:
      1. Fiverr search results
      2. Fiverr gig detail pages
      3. Fiverr seller profiles
      4. Google Trends
      5. Reddit
      6. YouTube (optional)
      7. LLM cluster synthesis
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    sources_present = set()

    if get_latest_search_result(keyword_id, db):
        sources_present.add("fiverr_search")
    if get_gigs_for_keyword(keyword_id, db):
        sources_present.add("fiverr_gig_detail")
    if get_sellers_for_keyword(keyword_id, db):
        sources_present.add("fiverr_seller_profile")
    if get_external_signal(keyword_id, "google_trends", db):
        sources_present.add("google_trends")
    if get_external_signal_for_niche(keyword.niche_id, "reddit_demand", db):
        sources_present.add("reddit")
    if get_external_signal(keyword_id, "youtube_count", db):
        sources_present.add("youtube")
    if get_cluster_analysis_for_keyword(keyword_id, db):
        sources_present.add("llm_cluster_synthesis")

    # Expected count varies by depth
    expected_sources_by_depth = {
        "full":         7,
        "standard":     6,
        "feasibility":  4,
        "keyword_only": 2,  # Just fiverr_search + external signals
    }
    expected = expected_sources_by_depth.get(depth, 4)
    diversity_score = min(1.0, len(sources_present) / expected)

    return {
        "score": round(diversity_score, 3),
        "sources_present": sorted(sources_present),
        "expected_count": expected,
    }
```

---

## Component 4: LLM Analysis Completion

```python
def _calculate_llm_completion_ratio(keyword_id: int, db) -> dict:
    """
    Measures the success rate of LLM calls that contributed to this keyword's scores.
    LLM failures (ValidationError after self-correction retry) reduce confidence.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche_id = keyword.niche_id

    # Get all LLM calls for this keyword's niche from current run
    llm_logs = db.query(LLMUsageLog).filter(
        LLMUsageLog.niche_id == niche_id,
        LLMUsageLog.run_id == get_current_run_id(),
    ).all()

    if not llm_logs:
        return {"score": 1.0, "note": "No LLM calls made — N/A defaults to 1.0"}

    total = len(llm_logs)
    successful = sum(1 for log in llm_logs if log.success)
    completion_ratio = successful / total

    return {
        "score": round(completion_ratio, 3),
        "total_calls": total,
        "successful": successful,
        "failed": total - successful,
    }
```

---

## Confidence Floor in Final Score

```python
# From SCORING_SYSTEM.md
def calculate_final_score(
    weighted_composite: float,
    confidence_modifier: float,
    confidence_floor: float = 0.20,
) -> float:
    effective_modifier = max(confidence_modifier, confidence_floor)
    final = weighted_composite * effective_modifier
    return round(min(100.0, max(0.0, final)), 2)
```

The 0.20 floor prevents extreme confidence penalties from zeroing out keywords with otherwise strong demand/competition signals.

---

## Confidence-Based GO/PASS Demotion

```python
# Also from SCORING_SYSTEM.md
def assign_tag(final_score: float, confidence_modifier: float) -> str:
    base_tag = _base_tag_from_score(final_score)
    if confidence_modifier < 0.5:
        return _demote_tag(base_tag)  # STRONG GO → CONDITIONAL GO, etc.
    return base_tag
```

Keywords with `confidence_modifier < 0.5` get their GO tag demoted by one tier in the dashboard — buyer beware indicator.

---

## Score Interpretation

| Confidence Modifier | Meaning | Dashboard Behavior |
|---|---|---|
| 0.90–1.00 | High confidence | Standard display, no warning |
| 0.70–0.89 | Good confidence | Standard display |
| 0.50–0.69 | Moderate confidence | Yellow badge: "Confidence: Moderate" |
| 0.30–0.49 | Low confidence | Red badge + tag demoted by 1 tier |
| 0.00–0.29 | Very low confidence | Red badge + tag demoted + warning text |

---

## Example Calculation

**Keyword:** "AI SaaS PRD" (full depth, weekly run)

Components:
- Data completeness: 9 of 9 expected scores calculated → 1.000
- Data freshness: 5 contributing records, avg age 18h vs avg TTL 100h → 0.820
- Source diversity: 6 of 7 expected sources present (no YouTube) → 0.857
- LLM completion: 47 of 48 LLM calls succeeded → 0.979

Calculation:
```
modifier = (1.000 × 0.30) + (0.820 × 0.30) + (0.857 × 0.20) + (0.979 × 0.20)
         = 0.300 + 0.246 + 0.171 + 0.196
         = 0.913
```

Result: **Confidence Modifier = 0.913** → "High confidence."

The reason string: "High confidence — all data complete and fresh"

If Final Composite was 65.5, then Final Score = 65.5 × 0.913 = 59.81 → "CONDITIONAL GO" tag.

---

## Second Example — Low Confidence Scenario

**Keyword:** "MCP server integration" (feasibility depth, Reddit failed, some stale data)

Components:
- Data completeness: 4 of 5 expected scores → 0.800
- Data freshness: oldest record at 78% of TTL → 0.490
- Source diversity: 3 of 4 expected (Reddit failed) → 0.750
- LLM completion: 12 of 15 LLM calls succeeded (3 failed) → 0.800

Calculation:
```
modifier = (0.800 × 0.30) + (0.490 × 0.30) + (0.750 × 0.20) + (0.800 × 0.20)
         = 0.240 + 0.147 + 0.150 + 0.160
         = 0.697
```

Result: **Confidence Modifier = 0.697** → "Good confidence" but reduced.

The reason string: "Confidence reduced by: data freshness 49%, LLM completion 80%"

Tag would NOT be demoted (modifier 0.697 > 0.5 threshold), but the dashboard would show the reduced confidence breakdown.


---

## SRDI ADDENDUM -- Confidence Modifier Integrity Extensions
**Source:** WAVE_C (R2), WAVE_D (R3), WAVE_H (R7); Epics R2, R3, R7

### New confidence_breakdown Entries (SRDI-Added)

Key                          Source  Deduction/Bonus  Condition
result_set_contamination     R2      -0.05 to -0.30   RSV 0.20-0.80 (tiered)
ghost_market_detected        R2      -0.50            ghost_market_flag = True
trc_reliability_low          R4.1    -0.05            trc_reliability_score < 0.70
zombie_concentration_high    R3      -0.10            >= 50% gigs are zombie
zombie_concentration_moderate R3     -0.05            25-49% gigs are zombie
unconstrained_search         R1      -0.08            search_strictness_used = NONE
low_youtube_legitimacy       R7      -0.03            youtube_count < 10
high_youtube_legitimacy      R7      +0.02            youtube_count >= 500
external_signal_quality      R7      weighted         sqrt(freshness x relevance)

### RSV Deduction Integration

Load ResultSetValidation for keyword/run:
  If rsv is None: no deduction applied (backward compat -- identical to pre-SRDI)
  If rsv.ghost_market_flag: confidence_breakdown["ghost_market_detected"] = -0.50
  Elif rsv.category_contamination_flag:
    score = rsv.result_set_relevance_score
    if score >= 0.60: deduction = -0.05
    elif score >= 0.40: deduction = -0.15
    elif score >= 0.20: deduction = -0.30
    else: deduction = -0.50
    confidence_breakdown["result_set_contamination"] = deduction

### Zombie Concentration Deduction

zombie_count = sum(1 for g in top_gigs[:10] if g.is_zombie is True)
zombie_fraction = zombie_count / max(len(top_gigs[:10]), 1)
if zombie_fraction >= 0.50: confidence_breakdown["zombie_concentration_high"] = -0.10
elif zombie_fraction >= 0.25: confidence_breakdown["zombie_concentration_moderate"] = -0.05

### Freshness x Relevance Quality (R7)

_compute_freshness_relevance_quality(keyword_id, db):
  Load ExternalSignal for keyword
  age_days = (now - esig.collected_at).days
  freshness: <=7d->1.0; <=30d->0.85; <=90d->0.70; <=180d->0.50; else->0.30
  relevance = esig.fiverr_relevance_qualifier or RSV.result_set_relevance_score or 0.70
  quality = round(sqrt(freshness * relevance), 3)
  Stored as ExternalSignal.signal_quality_score
  Contributes to confidence as "external_signal_quality" entry
