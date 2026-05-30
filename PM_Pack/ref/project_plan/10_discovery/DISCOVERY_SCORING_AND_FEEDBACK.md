# Discovery Scoring and Feedback
# Fiverr Research System — Wave 10

**Document Status:** Complete
**Wave:** 10 — LLM-Powered Niche Discovery
**Purpose:** How discovery hypotheses are evaluated after scoring, hit/miss tracking, feedback loop mechanics, pattern learning, auto-retire logic, gold detection, and discovery leaderboard.

---

## Evaluation Pipeline

Discovery keywords go through the normal pipeline (collect → analyze → score → rank) like any other keyword. The difference is what happens AFTER scoring:

```
Discovery keyword inserted (Stage 16, Run N)
    │
    ▼
Normal collection (Stage 3-5, Run N+1)
    │
    ▼
Normal analysis (Stage 7-9, Run N+1)
    │
    ▼
Normal scoring (Stage 10-12, Run N+1)
    │
    ▼
Discovery Evaluation (Stage 16, Run N+1)
    │
    ├── Compare actual_final_score to hypothesis_confidence
    ├── Classify: GOLD (85+) / HIT (60+) / MONITOR (40-59) / MISS (<40)
    ├── Log to discovery_outcomes table
    ├── Trigger alerts if GOLD
    ├── Auto-retire if score < 30
    └── Update feedback summary for next cycle
```

---

## Hit/Miss Classification

```python
# src/discovery/evaluation.py

from dataclasses import dataclass
from enum import Enum

class DiscoveryResult(Enum):
    GOLD = "gold"         # Score >= 85 — exceptional opportunity
    HIT = "hit"           # Score >= 60 — CONDITIONAL GO or better
    MONITOR = "monitor"   # Score 40-59 — worth watching
    MISS = "miss"         # Score < 40 — below useful threshold
    RETIRE = "retire"     # Score < 30 — auto-retired, never rescored


def classify_discovery_result(actual_score: float) -> DiscoveryResult:
    if actual_score >= 85:
        return DiscoveryResult.GOLD
    elif actual_score >= 60:
        return DiscoveryResult.HIT
    elif actual_score >= 40:
        return DiscoveryResult.MONITOR
    elif actual_score >= 30:
        return DiscoveryResult.MISS
    else:
        return DiscoveryResult.RETIRE
```

---

## Prediction Accuracy Tracking

For each hypothesis, we track how accurate the LLM's confidence was:

```python
@dataclass
class PredictionAccuracy:
    """Measures how well the LLM predicted the keyword's performance."""
    keyword_id: int
    hypothesis_confidence: float  # LLM's prediction (0-1, mapped to 0-100)
    actual_score: float
    prediction_error: float  # |actual - predicted|
    direction_correct: bool  # Did the LLM at least get the direction right?
    calibration_bucket: str  # "overconfident" | "well_calibrated" | "underconfident"


def calculate_prediction_accuracy(
    hypothesis_confidence: float,
    actual_score: float,
) -> PredictionAccuracy:
    """
    Compares the LLM's confidence to the actual score.
    Hypothesis confidence 0.7 → predicted score ~70.
    """
    predicted_score = hypothesis_confidence * 100
    error = abs(actual_score - predicted_score)

    # Direction: did LLM predict above/below 60 (the GO threshold) correctly?
    predicted_go = predicted_score >= 60
    actual_go = actual_score >= 60
    direction_correct = predicted_go == actual_go

    # Calibration: is the LLM systematically over- or under-confident?
    if predicted_score > actual_score + 15:
        calibration = "overconfident"
    elif predicted_score < actual_score - 15:
        calibration = "underconfident"
    else:
        calibration = "well_calibrated"

    return PredictionAccuracy(
        keyword_id=0,  # Set by caller
        hypothesis_confidence=hypothesis_confidence,
        actual_score=actual_score,
        prediction_error=round(error, 1),
        direction_correct=direction_correct,
        calibration_bucket=calibration,
    )
```

---

## Feedback Summary Generation

The feedback summary is the LLM's "memory" between cycles. It gets injected into every hypothesis prompt so the LLM can learn from past performance:

```python
def build_feedback_summary(db) -> dict:
    """
    Complete feedback summary for the discovery LLM.
    Called at start of each discovery cycle.
    """
    outcomes = db.query(DiscoveryOutcome).all()

    if not outcomes:
        return {"total_hypotheses": 0, "note": "First cycle — no history"}

    total = len(outcomes)
    results_by_class = {
        "gold": [o for o in outcomes if o.is_gold],
        "hit": [o for o in outcomes if o.is_hit and not o.is_gold],
        "monitor": [o for o in outcomes if 40 <= o.actual_final_score < 60],
        "miss": [o for o in outcomes if o.is_miss],
    }

    # Overall stats
    avg_score = sum(o.actual_final_score for o in outcomes) / total
    avg_confidence = sum(o.hypothesis_confidence for o in outcomes) / total
    avg_error = sum(abs(o.actual_final_score - o.hypothesis_confidence * 100) for o in outcomes) / total

    # Calibration analysis
    accuracies = [calculate_prediction_accuracy(o.hypothesis_confidence, o.actual_final_score)
                  for o in outcomes]
    overconfident_pct = sum(1 for a in accuracies if a.calibration_bucket == "overconfident") / total * 100
    underconfident_pct = sum(1 for a in accuracies if a.calibration_bucket == "underconfident") / total * 100
    direction_accuracy = sum(1 for a in accuracies if a.direction_correct) / total * 100

    # Per-mode breakdown
    mode_stats = {}
    for mode in ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]:
        mode_outcomes = [o for o in outcomes if o.discovery_mode == mode]
        if mode_outcomes:
            mode_total = len(mode_outcomes)
            mode_stats[mode] = {
                "count": mode_total,
                "avg_score": round(sum(o.actual_final_score for o in mode_outcomes) / mode_total, 1),
                "hit_rate": round(sum(1 for o in mode_outcomes if o.is_hit) / mode_total * 100, 1),
                "gold_count": sum(1 for o in mode_outcomes if o.is_gold),
                "avg_confidence": round(sum(o.hypothesis_confidence for o in mode_outcomes) / mode_total, 2),
                "avg_error": round(
                    sum(abs(o.actual_final_score - o.hypothesis_confidence * 100) for o in mode_outcomes) / mode_total, 1
                ),
            }

    # Winning characteristics — what do HITs have in common?
    hit_outcomes = [o for o in outcomes if o.is_hit]
    miss_outcomes = [o for o in outcomes if o.is_miss]

    hit_characteristics = _extract_characteristics(hit_outcomes, db)
    miss_characteristics = _extract_characteristics(miss_outcomes, db)

    # Build calibration guidance for the LLM
    calibration_guidance = []
    if overconfident_pct > 40:
        calibration_guidance.append(
            f"You've been OVERCONFIDENT {overconfident_pct:.0f}% of the time — "
            "lower your confidence estimates by ~15 points"
        )
    if underconfident_pct > 40:
        calibration_guidance.append(
            f"You've been UNDERCONFIDENT {underconfident_pct:.0f}% of the time — "
            "your estimates are too conservative"
        )
    if direction_accuracy < 60:
        calibration_guidance.append(
            f"Direction accuracy is only {direction_accuracy:.0f}% — "
            "focus on whether a keyword will be GO or NOT, not the exact score"
        )

    return {
        "total_hypotheses": total,
        "gold_hits": len(results_by_class["gold"]),
        "hits": len(results_by_class["hit"]) + len(results_by_class["gold"]),
        "misses": len(results_by_class["miss"]),
        "hit_rate_pct": round((len(results_by_class["hit"]) + len(results_by_class["gold"])) / total * 100, 1),
        "avg_actual_score": round(avg_score, 1),
        "avg_confidence": round(avg_confidence, 2),
        "avg_prediction_error": round(avg_error, 1),
        "direction_accuracy_pct": round(direction_accuracy, 1),
        "calibration": {
            "overconfident_pct": round(overconfident_pct, 1),
            "underconfident_pct": round(underconfident_pct, 1),
            "guidance": calibration_guidance,
        },
        "mode_stats": mode_stats,
        "best_mode": max(mode_stats.items(), key=lambda x: x[1]["hit_rate"])[0] if mode_stats else None,
        "worst_mode": min(mode_stats.items(), key=lambda x: x[1]["hit_rate"])[0] if mode_stats else None,
        "hit_characteristics": hit_characteristics,
        "miss_characteristics": miss_characteristics,
        "pattern_notes": _generate_pattern_notes(outcomes, mode_stats, hit_characteristics, miss_characteristics),
    }


def _extract_characteristics(outcomes: list, db) -> dict:
    """Extracts common characteristics from a set of outcomes."""
    if not outcomes:
        return {}

    niches = [o.niche_id for o in outcomes]
    from collections import Counter
    niche_counts = Counter(niches).most_common(3)

    # Average word count in keyword text
    avg_words = sum(len(o.keyword_text.split()) for o in outcomes) / len(outcomes)

    # Keywords containing specific patterns
    pattern_hits = {
        "integration": sum(1 for o in outcomes if "integration" in o.keyword_text.lower()),
        "automation": sum(1 for o in outcomes if "automat" in o.keyword_text.lower()),
        "ai": sum(1 for o in outcomes if "ai " in o.keyword_text.lower() or o.keyword_text.lower().startswith("ai")),
        "python": sum(1 for o in outcomes if "python" in o.keyword_text.lower()),
        "custom": sum(1 for o in outcomes if "custom" in o.keyword_text.lower()),
    }

    return {
        "top_niches": [{"niche": n, "count": c} for n, c in niche_counts],
        "avg_keyword_length_words": round(avg_words, 1),
        "keyword_patterns": {k: v for k, v in pattern_hits.items() if v > 0},
    }


def _generate_pattern_notes(outcomes, mode_stats, hit_chars, miss_chars) -> str:
    """Concise natural-language summary for the LLM."""
    notes = []

    # Mode insights
    for mode, stats in mode_stats.items():
        if stats["hit_rate"] >= 40:
            notes.append(f"{mode} works well ({stats['hit_rate']}% hit rate)")
        elif stats["hit_rate"] < 15 and stats["count"] >= 5:
            notes.append(f"{mode} underperforms ({stats['hit_rate']}% hit rate) — try different approach")

    # Keyword pattern insights
    if hit_chars.get("keyword_patterns"):
        top_pattern = max(hit_chars["keyword_patterns"].items(), key=lambda x: x[1])
        notes.append(f"Hits frequently contain '{top_pattern[0]}' ({top_pattern[1]} times)")

    if miss_chars.get("keyword_patterns"):
        top_miss_pattern = max(miss_chars["keyword_patterns"].items(), key=lambda x: x[1])
        notes.append(f"Misses frequently contain '{top_miss_pattern[0]}' — avoid this pattern")

    # Niche insights
    if hit_chars.get("top_niches"):
        top_niche = hit_chars["top_niches"][0]
        notes.append(f"Best discovery niche: {top_niche['niche']} ({top_niche['count']} hits)")

    return "; ".join(notes) if notes else "Insufficient data for pattern analysis"
```

---

## Auto-Retire Logic

Keywords that score below 30 are automatically retired to prevent wasting collection resources:

```python
def auto_retire_discovery_keywords(db):
    """
    Retires discovery keywords that scored below the retirement threshold.
    Retired keywords are excluded from future collection runs.
    """
    threshold = 30  # From config: discovery.auto_retire_threshold

    low_scorers = db.query(Keyword).filter(
        Keyword.is_discovery == True,
        Keyword.is_retired == False,
    ).join(KeywordScore).filter(
        KeywordScore.final_score < threshold,
        KeywordScore.final_score.isnot(None),
    ).all()

    for keyword in low_scorers:
        keyword.is_retired = True
        log.info(f"Auto-retired: '{keyword.keyword_text}' "
                 f"(score: {get_final_score(keyword.id, db)}, "
                 f"mode: {keyword.discovery_mode})")

    db.commit()
    return len(low_scorers)
```

Retired keywords:
- Are excluded from collection job queuing
- Are excluded from scoring recalculation
- Still appear in the discovery dashboard (grayed out) for learning purposes
- Can be manually un-retired by the user

---

## Gold Detection and Alerting

```python
GOLD_THRESHOLD = 85  # From config: discovery.gold_threshold

def check_gold_discoveries(run_id: str, db) -> list[dict]:
    """
    Checks for newly scored discovery keywords that hit gold threshold.
    Returns list of gold discoveries for alerting.
    """
    golds = db.query(Keyword).filter(
        Keyword.is_discovery == True,
        Keyword.discovery_evaluated == False,
    ).join(KeywordScore).filter(
        KeywordScore.final_score >= GOLD_THRESHOLD,
    ).all()

    gold_list = []
    for keyword in golds:
        score = get_final_score(keyword.id, db)
        gold_list.append({
            "keyword_id": keyword.id,
            "keyword_text": keyword.keyword_text,
            "niche_id": keyword.niche_id,
            "final_score": score,
            "discovery_mode": keyword.discovery_mode,
            "hypothesis_confidence": keyword.hypothesis_confidence,
        })

        # Create gold alert
        create_alert(
            alert_type="NEW_GOLD_DISCOVERY",
            severity="HIGH",
            message=(f"🏆 GOLD: '{keyword.keyword_text}' scored {score:.1f} "
                     f"(discovered via {keyword.discovery_mode}, "
                     f"predicted {keyword.hypothesis_confidence:.0%})"),
            metadata=gold_list[-1],
            db=db,
        )

    return gold_list
```

---

## Discovery Leaderboard

Ranked list of all discovery keywords by actual final score:

```python
def get_discovery_leaderboard(db, limit: int = 50) -> list[dict]:
    """
    Returns all scored discovery keywords ranked by actual performance.
    Used by the dashboard Discovery page.
    """
    discoveries = db.query(Keyword).filter(
        Keyword.is_discovery == True,
    ).join(KeywordScore, isouter=True).order_by(
        KeywordScore.final_score.desc().nullslast()
    ).limit(limit).all()

    leaderboard = []
    for kw in discoveries:
        score = get_final_score(kw.id, db)
        tag = get_tag(kw.id, db)
        result = classify_discovery_result(score) if score else None

        leaderboard.append({
            "keyword_text": kw.keyword_text,
            "niche": get_niche_name(kw.niche_id),
            "discovery_mode": kw.discovery_mode,
            "hypothesis_confidence": kw.hypothesis_confidence,
            "actual_score": score,
            "tag": tag,
            "result": result.value if result else "pending",
            "is_retired": kw.is_retired,
            "discovered_in_run": kw.discovered_in_run,
            "prediction_error": (
                round(abs(score - kw.hypothesis_confidence * 100), 1)
                if score and kw.hypothesis_confidence else None
            ),
        })

    return leaderboard
```

---

## Discovery Metrics Summary

Key metrics tracked over time:

| Metric | Calculation | Target |
|---|---|---|
| Hit Rate | (gold + hit) / total hypotheses | > 30% |
| Gold Rate | gold / total hypotheses | > 5% |
| Prediction Error | avg |actual_score - predicted_score| | < 20 points |
| Direction Accuracy | % of times predicted GO/NOT matched actual | > 65% |
| Cost per Hit | total discovery LLM cost / hits | < $0.50 |
| Cost per Gold | total discovery LLM cost / golds | < $5.00 |
| Discovery ROI | (value of gold discoveries) / (total discovery cost) | > 10x |

These metrics are displayed on the Discovery dashboard page and tracked over time to measure whether the feedback loop is improving hypothesis quality.


---

## SRDI ADDENDUM -- Discovery Scoring with Relevance Gating
**Source:** WAVE_G sections 3-4 (R6); Epic R6

### Extended Outcome Classification (5 classes)

GOLD         is_gold=True         final >= 85, relevance ok
HIT          is_hit=True          final 60-84, relevance ok
MONITOR      (no flag)            final 30-59, relevance ok
MISS         is_miss=True (retire) final < 30, relevance ok
INVALID [NEW] is_invalid=True     ghost_market_flag = True (retire immediately)
CONTAMINATED [NEW] is_contaminated=True  relevance < 0.40, not ghost (recollect)

is_invalid and is_miss are MUTUALLY EXCLUSIVE by design (Decision DL-206).
A ghost market is not a failed hypothesis -- it is bad input data. Recording it
as a miss would teach the discovery LLM to avoid this type of keyword, which is wrong.

### Discovery Activation Checklist

Must be complete before enabling discovery engine in production:
  R6 Gate 1-4 all implemented and tested
  is_invalid and is_contaminated columns present (R8 M6 applied)
  REG-25, REG-26, REG-27 all green
  R9 integration test test_discovery_relevance_gates.py passing
  Tier-1 gate signed off by operator

### Feedback Loop Protection Summary

Before SRDI: ALL outcomes fed back to discovery LLM
             -> ghost markets could teach "this keyword type works"
             -> contaminated outcomes could skew hit-rate statistics

After SRDI:  Only valid outcomes (not invalid, not contaminated) fed to LLM
             -> data_quality_note reports excluded counts to operator
             -> if 0 valid outcomes: LLM not called, note returned instead

### Monthly Discovery Health KPIs (tracked by R11)

ghost_market_rate: ghost keywords / total discovery keywords evaluated
target: < 8%

discovery_rejection_rate: rejected at gates / proposed hypotheses
target: 20-40% (healthy gate -- too low means gate is not working;
                              too high means hypotheses are poor quality)

feedback_validity_rate: valid outcomes / total outcomes evaluated
target: > 80%
