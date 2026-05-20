# Scoring System — Master Document
# Fiverr Research System — Wave 6

**Document Status:** Complete
**Wave:** 6 — Scoring System
**Purpose:** Master reference for all 11 scores. Each score has its own detailed file (DEMAND_SCORE.md, etc.) in this folder. This document is the single source of truth for how scores combine into the Final Recommendation Score.

---

## The 11 Scores at a Glance

| # | Score | File | Range | Direction | Weight (Default) | Depth Required |
|---|---|---|---|---|---|---|
| 1 | Demand Score | DEMAND_SCORE.md | 0–100 | Higher = better | 20% | All depths |
| 2 | Competition Score | COMPETITION_SCORE.md | 0–100 | Lower = better (inverted in composite) | 20% | All depths |
| 3 | Opportunity Score | OPPORTUNITY_SCORE.md | 0–100 | Higher = better | 25% | All depths |
| 4 | New Seller Feasibility | NEW_SELLER_FEASIBILITY.md | 0–100 | Higher = better | 15% | standard + full |
| 5 | Profitability Score | PROFITABILITY_SCORE.md | 0–100 | Higher = better | 10% | feasibility + above |
| 6 | Conversion Intent Score | CONVERSION_INTENT_SCORE.md | 0–100 | Higher = better | 10% | standard + full |
| 7 | Saturation Score | SATURATION_SCORE.md | 0–100 | Lower = better (inverted in composite) | 5% | standard + full |
| 8 | Gig Quality Weakness Score | GIG_QUALITY_WEAKNESS_SCORE.md | 0–100 | Higher = better (more weakness to exploit) | 10% | standard + full |
| 9 | Trend Score | TREND_SCORE.md | 0–100 | Higher = better | 5% | standard + full |
| 10 | Final Recommendation Score | FINAL_SCORE.md | 0–100 | Higher = better | Composite | standard + full |
| 11 | Confidence Modifier | CONFIDENCE_SCORE.md | 0.0–1.0 | Multiplier on Final Score | n/a | All depths |

---

## Depth-Tier Behavior

```python
DEPTH_SCORE_AVAILABILITY = {
    "full": {
        "available_scores": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "label": "all_11",
    },
    "standard": {
        "available_scores": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "label": "all_11",
    },
    "feasibility": {
        "available_scores": [1, 2, 3, 4, 5, 11],
        "label": "scores_1_to_5",
    },
    "keyword_only": {
        "available_scores": [1, 2, 3, 11],
        "label": "scores_1_to_3",
    },
}
```

When a score is unavailable due to depth, it is stored as `null` in `keyword_scores` and contributes nothing to the weighted composite (weight is redistributed proportionally to remaining available scores).

---

## Named Scoring Profiles

Profiles are weight presets. The `active_profile` in config.yaml selects which is used. Each profile's weights must sum to 1.0 (validated at startup).

```python
SCORING_PROFILES = {
    "default": {
        "demand":          0.20,
        "competition_inv": 0.20,
        "opportunity":     0.25,
        "feasibility":     0.15,
        "profitability":   0.10,
        "intent":          0.10,
        "saturation_inv":  0.05,
        "weakness":        0.10,
        "trend":           0.05,
    },
    "aggressive_new_seller": {
        "feasibility":     0.25,
        "weakness":        0.20,
        "opportunity":     0.20,
        "demand":          0.15,
        "competition_inv": 0.10,
        "profitability":   0.05,
        "intent":          0.05,
        "saturation_inv":  0.00,
        "trend":           0.00,
    },
    "profitability_focus": {
        "profitability":   0.25,
        "intent":          0.20,
        "opportunity":     0.20,
        "demand":          0.15,
        "competition_inv": 0.10,
        "feasibility":     0.05,
        "weakness":        0.05,
        "saturation_inv":  0.00,
        "trend":           0.00,
    },
    "trend_chaser": {
        "trend":           0.25,
        "demand":          0.25,
        "opportunity":     0.20,
        "competition_inv": 0.15,
        "feasibility":     0.10,
        "profitability":   0.05,
        "intent":          0.00,
        "weakness":        0.00,
        "saturation_inv":  0.00,
    },
}

def validate_scoring_profile(profile_name: str, weights: dict) -> None:
    """Raises ValueError if weights don't sum to 1.0."""
    total = sum(weights.values())
    if not (0.999 <= total <= 1.001):
        raise ValueError(
            f"Scoring profile '{profile_name}' weights sum to {total:.4f}, must equal 1.0"
        )
```

---

## Weighted Composite Calculation

```python
# src/scoring/composite_scorer.py

def calculate_weighted_composite(
    scores: dict[str, float | None],
    profile_weights: dict[str, float],
) -> tuple[float, dict]:
    """
    Calculates the weighted composite score.

    Handles missing scores by redistributing their weight proportionally
    among the available scores. This ensures that a keyword_only depth
    keyword (only 3 scores available) still gets a valid 0–100 score.

    Returns:
        (composite_score, score_components_dict)
    """
    score_to_weight_key = {
        "demand_score":        "demand",
        "competition_score":   "competition_inv",  # inverted in calculation
        "opportunity_score":   "opportunity",
        "feasibility_score":   "feasibility",
        "profitability_score": "profitability",
        "intent_score":        "intent",
        "saturation_score":    "saturation_inv",   # inverted in calculation
        "weakness_score":      "weakness",
        "trend_score":         "trend",
    }

    weighted_sum = 0.0
    weight_used = 0.0
    components = {}

    for score_field, weight_key in score_to_weight_key.items():
        score_value = scores.get(score_field)
        weight = profile_weights.get(weight_key, 0.0)

        if weight == 0.0:
            continue  # Profile excludes this score

        if score_value is None:
            components[score_field] = {"value": None, "weight": weight, "contribution": None}
            continue  # Missing data — weight will be redistributed

        # Invert competition and saturation (lower raw = better, but composite expects "higher = better")
        if weight_key in ("competition_inv", "saturation_inv"):
            effective_value = 100.0 - score_value
        else:
            effective_value = score_value

        contribution = effective_value * weight
        weighted_sum += contribution
        weight_used += weight

        components[score_field] = {
            "value": round(score_value, 2),
            "effective_value": round(effective_value, 2),
            "weight": weight,
            "contribution": round(contribution, 2),
        }

    if weight_used < 0.5:
        # Not enough data to compute a meaningful composite
        return 0.0, components

    # Normalize for any missing scores: redistribute their weight
    composite = weighted_sum / weight_used
    return round(min(100.0, max(0.0, composite)), 2), components
```

---

## Final Recommendation Score

The Final Recommendation Score = Weighted Composite × Confidence Modifier (with floor)

```python
def calculate_final_score(
    weighted_composite: float,
    confidence_modifier: float,
    confidence_floor: float = 0.20,
) -> float:
    """
    Applies the confidence modifier to the weighted composite.

    The confidence_modifier is in [0.0, 1.0] but floored at confidence_floor
    to prevent any single keyword from being scored to zero by low confidence alone.
    This preserves ordering while still penalizing low-confidence keywords.
    """
    effective_modifier = max(confidence_modifier, confidence_floor)
    final = weighted_composite * effective_modifier
    return round(min(100.0, max(0.0, final)), 2)
```

**Why a confidence floor of 0.20?**
- Without a floor, a keyword with confidence_modifier = 0.0 would have final_score = 0
- A keyword with weak data but real demand signals (e.g., 75 raw composite) shouldn't drop to 0
- 0.20 floor means even maximum-uncertainty keywords retain 20% of their raw score for ranking
- Users can still see them in the dashboard with a clear "LOW CONFIDENCE" badge

---

## GO/PASS Tag Assignment

```python
OPPORTUNITY_TAGS = [
    ("STRONG GO",      80, 100),
    ("CONDITIONAL GO", 60,  80),
    ("MONITOR",        40,  60),
    ("CAUTION",        20,  40),
    ("PASS",            0,  20),
]

def assign_tag(final_score: float, confidence_modifier: float) -> str:
    """
    Assigns GO/PASS tag based on final_score.
    Demotes by one tier if confidence_modifier < 0.5 — buyer beware.
    """
    base_tag = None
    for tag, low, high in OPPORTUNITY_TAGS:
        if low <= final_score < high:
            base_tag = tag
            break
    if base_tag is None and final_score >= 100:
        base_tag = "STRONG GO"
    if base_tag is None:
        base_tag = "PASS"

    # Confidence demotion
    if confidence_modifier < 0.5:
        demotion_map = {
            "STRONG GO": "CONDITIONAL GO",
            "CONDITIONAL GO": "MONITOR",
            "MONITOR": "CAUTION",
            "CAUTION": "PASS",
            "PASS": "PASS",
        }
        return demotion_map[base_tag]

    return base_tag
```

---

## End-to-End Scoring Pipeline

```python
async def score_keyword(keyword_id: int, profile_name: str, db, llm_client, cache):
    """
    Complete scoring pipeline for a single keyword.
    Called for every keyword in Stage 10.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth
    available = DEPTH_SCORE_AVAILABILITY[depth]["available_scores"]

    # Calculate individual scores (None if not available at this depth)
    scores = {
        "demand_score":        calculate_demand_score(keyword_id, db) if 1 in available else None,
        "competition_score":   calculate_competition_score(keyword_id, db) if 2 in available else None,
        "opportunity_score":   None,  # Calculated after demand and competition
        "feasibility_score":   calculate_feasibility_score(keyword_id, db) if 4 in available else None,
        "profitability_score": calculate_profitability_score(keyword_id, db) if 5 in available else None,
        "intent_score":        calculate_conversion_intent_score(keyword_id, db) if 6 in available else None,
        "saturation_score":    calculate_saturation_score(keyword_id, db) if 7 in available else None,
        "weakness_score":      calculate_gig_quality_weakness_score(keyword_id, db) if 8 in available else None,
        "trend_score":         calculate_trend_score(keyword_id, db) if 9 in available else None,
    }

    # Opportunity Score depends on Demand and Competition
    if scores["demand_score"] is not None and scores["competition_score"] is not None:
        scores["opportunity_score"] = calculate_opportunity_score(
            scores["demand_score"], scores["competition_score"]
        )

    # Profile weights
    profile_weights = SCORING_PROFILES[profile_name]

    # Weighted composite
    weighted_composite, components = calculate_weighted_composite(scores, profile_weights)

    # Confidence Modifier
    confidence_modifier, confidence_breakdown = calculate_confidence_modifier(keyword_id, scores, db)

    # Final Score
    final_score = calculate_final_score(weighted_composite, confidence_modifier)

    # Tag
    tag = assign_tag(final_score, confidence_modifier)

    # LLM explanation (gpt-4o)
    explanation_text = await generate_score_explanation(
        keyword_id, scores, components, final_score, tag, llm_client, cache
    )

    # Red flags
    red_flags = detect_red_flags_from_scores(scores, components, keyword_id, db)

    # Write keyword_scores row
    write_keyword_score(
        keyword_id=keyword_id,
        scores=scores,
        weighted_composite=weighted_composite,
        confidence_modifier=confidence_modifier,
        final_score=final_score,
        tag=tag,
        score_components=components,
        confidence_breakdown=confidence_breakdown,
        explanation_text=explanation_text,
        red_flags=red_flags,
        scoring_profile=profile_name,
        score_depth=DEPTH_SCORE_AVAILABILITY[depth]["label"],
        db=db,
    )
```

---

## Index of Score Files

For full formulas and implementation details, see the individual files:

| # | File |
|---|---|
| 1 | DEMAND_SCORE.md |
| 2 | COMPETITION_SCORE.md |
| 3 | OPPORTUNITY_SCORE.md |
| 4 | NEW_SELLER_FEASIBILITY.md |
| 5 | PROFITABILITY_SCORE.md |
| 6 | CONVERSION_INTENT_SCORE.md |
| 7 | SATURATION_SCORE.md |
| 8 | GIG_QUALITY_WEAKNESS_SCORE.md |
| 9 | TREND_SCORE.md |
| 10 | FINAL_SCORE.md |
| 11 | CONFIDENCE_SCORE.md |
