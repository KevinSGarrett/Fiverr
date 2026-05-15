# Go/No-Go Logic
# Fiverr Research System — Wave 7

**Document Status:** Complete
**Wave:** 7 — Recommendation Engine
**Purpose:** Tag thresholds, confidence gating, override conditions, missing data handling for recommendations, and run-mode interactions.

---

## Tag Thresholds (from config.yaml)

```yaml
opportunity_thresholds:
  strong_go: 80
  conditional_go: 60
  monitor: 40
  caution: 20
```

| Final Score Range | Tag | Recommendation Generated? |
|---|---|---|
| 80–100 | STRONG GO | Yes — full 11-component package |
| 60–79.99 | CONDITIONAL GO | Yes — full package with conditions flagged |
| 40–59.99 | MONITOR | No — keyword visible in dashboard for observation |
| 20–39.99 | CAUTION | No — appears with low-priority badge |
| 0–19.99 | PASS | No — deprioritized in display |

---

## Confidence Gating

Confidence is enforced at two levels: tag assignment and recommendation generation.

### Level 1 — Tag Demotion (applied in Stage 12)

When `confidence_modifier < 0.50`, the tag is demoted by one tier before recommendation eligibility is checked:

```
STRONG GO → CONDITIONAL GO  (still generates recommendation)
CONDITIONAL GO → MONITOR     (no longer generates recommendation)
MONITOR → CAUTION
CAUTION → PASS
```

This means a keyword with a raw composite of 82 (STRONG GO range) but confidence_modifier of 0.45 gets demoted to CONDITIONAL GO. If confidence_modifier were 0.35, that CONDITIONAL GO would demote further to MONITOR — and no recommendation would be generated.

### Level 2 — Recommendation Gate (applied in Stage 13)

Even after tag assignment, a second confidence check runs before generating the recommendation:

```python
RECOMMENDATION_CONFIDENCE_MINIMUM = 0.40

def passes_confidence_gate(keyword_data: dict) -> bool:
    """
    Minimum confidence required to generate a recommendation.
    Even CONDITIONAL GO keywords need at least 0.40 confidence.
    """
    return keyword_data["confidence_modifier"] >= RECOMMENDATION_CONFIDENCE_MINIMUM
```

---

## Override Conditions

### Manual Force-Recommend

The user can force a recommendation for any keyword, regardless of tag or confidence:

```python
# In config.yaml or via API endpoint:
force_recommend_keywords:
  - keyword_id: 1234
    reason: "User override — want to see recommendation for this keyword despite MONITOR tag"
  - keyword_text: "MCP server integration"
    niche_id: "mcp_ai_agent"
    reason: "Testing MCP feasibility — want recommendation package even at low confidence"
```

Implementation:
```python
def is_keyword_force_recommended(keyword_id: int, db) -> bool:
    """Checks if user has forced recommendation for this keyword."""
    # Check config.yaml force list
    for override in config.get("force_recommend_keywords", []):
        if override.get("keyword_id") == keyword_id:
            return True
        # Also support by keyword_text + niche_id
        if (override.get("keyword_text") and override.get("niche_id")):
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if (keyword.keyword_text == override["keyword_text"]
                    and keyword.niche_id == override["niche_id"]):
                return True
    return False
```

When force-recommended, the recommendation is generated but flagged:
```python
recommendation.red_flags.append({
    "flag_type": "USER_OVERRIDE",
    "description": "This recommendation was generated via user override — "
                   f"keyword tag is {keyword_data['tag']}, "
                   f"confidence is {keyword_data['confidence_modifier']:.2f}",
    "severity": "INFO",
})
```

### Niche-Level Override

Each niche profile in config.yaml has `llm.recommendation_generation`:
- `true` (default for full and standard depth niches): recommendations are generated
- `false` (default for keyword_only and feasibility niches): no recommendations regardless of tag

The user can set `recommendation_generation: true` for a gated niche to enable recommendations even at reduced depth — useful for testing.

---

## Missing Data Handling for Recommendations

Not all LLM tasks require all data. When specific inputs are missing, some tasks adapt and others skip:

| LLM Task | Required Inputs | If Missing |
|---|---|---|
| Gig titles | keyword_text, niche_name | Always runs — minimal data needed |
| Tag sets | keyword_text, niche_name | Always runs |
| Package structure | niche pricing from config, competitor packages | Uses config pricing if competitor data missing |
| Description outline | keyword_text, niche_name, hard_exclusions | Always runs — uses exclusions from config |
| FAQ entries | keyword_text, niche_name | Always runs |
| Differentiation angle | top_competitor_weaknesses | **Skips** if no competitor weakness data — stores null |
| Buyer persona | keyword_text, demand signals | Uses generic template if demand signals missing |
| Thumbnail direction | keyword_text | Always runs |
| Upsell structure | competitor gig_extras data | Uses generic upsell template if no extras data |
| Red flags | all scores + competitor data | Runs with partial data — flags what's missing |
| Niche viability | all scores + synthesis narrative | Runs with partial data — notes low confidence |

```python
def determine_skippable_tasks(context: RecommendationContext) -> list[str]:
    """
    Returns list of task names that should be skipped due to missing data.
    All other tasks run even with partial data.
    """
    skip = []

    if not context.top_competitor_weaknesses:
        skip.append("differentiation_angle")
        log.info(f"Skipping differentiation_angle for {context.keyword_text} — "
                 "no competitor weakness data available")

    return skip
```

---

## STRONG GO vs. CONDITIONAL GO Behavior

| Aspect | STRONG GO (80+) | CONDITIONAL GO (60–79) |
|---|---|---|
| All 11 LLM tasks run | Yes | Yes |
| Red flags severity | Only strategic red flags | Strategic + confidence warnings |
| Niche viability tone | Actionable — "enter now" framing | Cautious — "viable if conditions met" framing |
| Dashboard priority | Displayed first with gold badge | Displayed second with silver badge |
| Export inclusion | Always included in PDF/Excel exports | Included only if config.exports.include_conditional = true |

The viability prompt includes the tag as context so gpt-4o adjusts its tone:

```python
# In the viability prompt:
if context.tag == "STRONG GO":
    framing_instruction = ("Frame this as an actionable opportunity — tell the seller "
                          "what to do now and what to expect.")
else:
    framing_instruction = ("Frame this as a conditional opportunity — identify what conditions "
                          "need to be true and what risks to monitor before acting.")
```

---

## Run-Mode Interactions

| Run Mode | Stage 13 Behavior |
|---|---|
| `--mode full` | Generates recommendations for all eligible keywords after Stages 10–12 |
| `--mode score-only` | Does NOT run Stage 13 — use `--mode recommendations-only` separately |
| `--mode recommendations-only` | Runs Stage 13 only, using existing scores from the latest run |
| `--mode collect-only` | Does NOT run Stage 13 |
| `--mode analyze-only` | Does NOT run Stage 13 |
| `--mode resume` | Resumes Stage 13 from checkpoint if it was interrupted |

---

## Recommendation Lifecycle

```
Run 1: Keyword scores 72 → CONDITIONAL GO → Recommendation generated
Run 2: Keyword scores 74 (delta < 5) → Skip regeneration → Reuse Run 1 recommendation
Run 3: Keyword scores 81 (delta > 5) → STRONG GO → Recommendation regenerated
Run 4: Keyword scores 79 (delta < 5) → CONDITIONAL GO → Skip regeneration
Run 5: Competitor data refreshed → Recommendation regenerated (competitor trigger)
Run 6: User changes niche pricing in config → User runs --mode recommendations-only → All recommendations for niche regenerated
```

This lifecycle keeps LLM costs low — most runs regenerate only a few recommendations where scores actually changed.

---

## Error Handling in Stage 13

```python
async def run_stage_13(run_id: str, db, config, llm_client, cache):
    """Stage 13 orchestrator."""
    eligible = get_eligible_keywords(run_id, db, config)
    log.info(f"Stage 13: {len(eligible)} keywords eligible for recommendations")

    generated = 0
    skipped = 0
    failed = 0

    for keyword_data in eligible:
        # Gate check
        passes, reason = passes_recommendation_gates(keyword_data, db)
        if not passes:
            log.info(f"Skipped {keyword_data['keyword_text']}: {reason}")
            skipped += 1
            continue

        # Skip logic
        if not should_regenerate_recommendation(
            keyword_data["keyword_id"], keyword_data["final_score"], db
        ):
            log.debug(f"Skipped {keyword_data['keyword_text']}: score unchanged")
            skipped += 1
            continue

        try:
            context = build_recommendation_context(keyword_data["keyword_id"], db, config)
            result = await generate_recommendation(
                keyword_data["keyword_id"], context, llm_client, cache, db
            )
            generated += 1
            if not result["generation_complete"]:
                log.warning(f"Partial recommendation for {keyword_data['keyword_text']} — "
                           "some LLM tasks failed")
        except Exception as e:
            log.error(f"Failed to generate recommendation for "
                     f"{keyword_data['keyword_text']}: {e}")
            failed += 1

    log.info(f"Stage 13 complete: {generated} generated, {skipped} skipped, {failed} failed")
    return {"generated": generated, "skipped": skipped, "failed": failed}
```

If an individual LLM task fails within a recommendation, the other 10 tasks still complete and the recommendation is stored with `generation_complete = False`. The dashboard shows a "Partial" badge and the failed task's field is null. The user can re-run `--mode recommendations-only` to retry failed tasks.
