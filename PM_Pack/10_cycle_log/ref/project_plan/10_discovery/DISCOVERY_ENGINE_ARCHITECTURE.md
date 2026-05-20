# Discovery Engine Architecture
# Fiverr Research System — Wave 10

**Document Status:** Complete
**Wave:** 10 — LLM-Powered Niche Discovery ("Gold Mining")
**Purpose:** Autonomous discovery loop architecture — how the system learns from scored data, generates hypotheses for new keywords and niches, tests them through normal collection and scoring, feeds results back to the LLM, and iteratively improves hypothesis quality.

---

## The Problem This Solves

The current system researches 9 pre-defined niches. But the BEST opportunity on Fiverr right now might be a keyword or sub-niche you've never considered. Manual brainstorming is limited by what you already know. This engine turns the LLM into an autonomous research partner that:

1. Studies everything the system has collected and scored
2. Identifies patterns in what makes high-scoring keywords successful
3. Generates hypotheses for NEW keywords that should score similarly
4. Tests those hypotheses through normal collection and scoring
5. Compares predictions to actual results
6. Feeds outcomes back to improve future hypotheses
7. Alerts you immediately when it finds a "gold" opportunity (85+ score)

---

## Discovery Loop Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    DISCOVERY CYCLE                            │
│                                                              │
│  ┌─────────────┐     ┌──────────────────┐                   │
│  │ LEARN        │────▶│ HYPOTHESIZE       │                   │
│  │ Analyze all  │     │ LLM generates     │                   │
│  │ scored data  │     │ keyword/niche     │                   │
│  │ + past hits  │     │ suggestions       │                   │
│  │ + past misses│     │ with confidence   │                   │
│  └─────────────┘     └────────┬─────────┘                   │
│                               │                              │
│                               ▼                              │
│                      ┌────────────────┐                      │
│                      │ GATE            │                      │
│                      │ hypothesis_     │                      │
│                      │ confidence ≥    │                      │
│                      │ 0.50 to proceed │                      │
│                      └───────┬────────┘                      │
│                              │                               │
│                    ┌─────────▼──────────┐                    │
│                    │ TEST                │                    │
│                    │ Add to keyword DB   │                    │
│                    │ Run normal pipeline │                    │
│                    │ (collect → analyze  │                    │
│                    │  → score → rank)    │                    │
│                    └─────────┬──────────┘                    │
│                              │                               │
│                    ┌─────────▼──────────┐                    │
│                    │ EVALUATE            │                    │
│                    │ Compare actual      │                    │
│                    │ score to predicted  │                    │
│                    │ confidence          │                    │
│                    └─────────┬──────────┘                    │
│                              │                               │
│                    ┌─────────▼──────────┐                    │
│                    │ FEEDBACK            │                    │
│                    │ Log hit/miss        │                    │
│                    │ Summarize patterns  │                    │
│                    │ Feed to next LEARN  │                    │
│                    └─────────┬──────────┘                    │
│                              │                               │
│              ┌───────────────┤                               │
│              │               │                               │
│   ┌──────────▼─────┐ ┌──────▼───────┐                       │
│   │ GOLD ALERT     │ │ AUTO-RETIRE  │                        │
│   │ Score ≥ 85     │ │ Score < 30   │                        │
│   │ → notification │ │ → retired    │                        │
│   └────────────────┘ └──────────────┘                        │
│                                                              │
│  ◄───────── REPEAT EVERY RUN ──────────►                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Discovery Modes

The LLM uses four distinct strategies for generating hypotheses, each targeting a different type of opportunity:

### Mode 1: Adjacent Keyword Discovery

**Strategy:** Find keywords semantically close to existing high-scorers that the seed list missed.

**How it works:**
- Input: Top 10 keywords by final_score + their score breakdowns + cluster labels
- LLM reasoning: "If 'AI SaaS PRD' scores 82 with high demand and exploitable weaknesses, what RELATED keywords might buyers search that we haven't tested?"
- Output: 5–10 related keywords like "AI product spec", "SaaS feature roadmap", "AI MVP specification"

**When to use:** Every run. Lowest cost, highest hit rate (30–50% expected).

### Mode 2: Adjacent Niche Discovery

**Strategy:** Identify entirely new Fiverr categories where the user's skills (Python, AI, automation) are in demand but competition is low.

**How it works:**
- Input: User skill profile (from config), all 9 existing niche names + scores, Fiverr category tree
- LLM reasoning: "The user excels at Python + AI + technical writing. Beyond the 9 niches being researched, what OTHER Fiverr categories could these skills serve where demand exists and competition is low?"
- Output: 3–5 new niche suggestions with category paths and seed keywords

**When to use:** Every 3rd run. Higher cost, lower hit rate (10–20%), but highest value when it hits.

### Mode 3: Gap Exploit Discovery

**Strategy:** Find keywords that target specific pricing, quality, or positioning gaps identified in existing data.

**How it works:**
- Input: All price gaps detected (Wave 9), all gig quality weaknesses (Wave 5), all positioning gaps from competitor analysis
- LLM reasoning: "In the 'AI agent' niche, there's a price gap at $150–$250 for Standard tier and most competitors lack architecture diagrams. What keyword would a buyer search if they specifically wanted an AI agent with architecture documentation at a mid-range price?"
- Output: 5–8 keywords targeting specific gaps

**When to use:** Every run (after Wave 9 price analysis completes). Medium hit rate (20–35%).

### Mode 4: Trend Chase Discovery

**Strategy:** Identify emerging keywords before they saturate, using external trend signals.

**How it works:**
- Input: Google Trends rising queries in AI/automation/Python, Reddit post volume trends, new Fiverr category announcements
- LLM reasoning: "Google Trends shows 'Claude API integration' rising 300% in 3 months. Reddit r/automation has 5x more posts about 'n8n' vs 6 months ago. What keywords should we test before these niches saturate?"
- Output: 3–5 trend-driven keywords with urgency rating

**When to use:** Every run. Lowest hit rate (10–15%) but captures time-sensitive opportunities.

---

## Stage 16 — Discovery Engine (New Pipeline Stage)

Inserted as the final stage, after all reporting and export:

```
Stage 15: Export
    │
    ▼
Stage 16: Discovery Engine (NEW)
    │
    ├── Step 1: Build discovery context (aggregate scored data)
    ├── Step 2: Load feedback from previous cycles
    ├── Step 3: Select discovery modes for this run
    ├── Step 4: Generate hypotheses (LLM calls)
    ├── Step 5: Gate hypotheses (confidence ≥ 0.50)
    ├── Step 6: Deduplicate against existing keywords
    ├── Step 7: Insert accepted hypotheses into keywords table
    ├── Step 8: Queue collection jobs for next run
    └── Step 9: Log discovery cycle results
```

---

## Discovery Context Builder

```python
# src/discovery/context_builder.py

from pydantic import BaseModel

class DiscoveryContext(BaseModel):
    """All data the discovery LLM needs to generate hypotheses."""

    # Existing keyword performance (top performers)
    top_keywords: list[dict]
    # [{"keyword": "AI SaaS PRD", "niche": "PRD", "final_score": 82.3,
    #   "demand": 75, "competition": 66, "opportunity": 26, "tag": "STRONG GO",
    #   "cluster_label": "PRD - MVP Scoping", "market_type": "WIDE_SPREAD"}]

    # Bottom performers (for learning what doesn't work)
    bottom_keywords: list[dict]
    # Same structure, final_score < 30

    # Niche-level summaries
    niche_summaries: list[dict]
    # [{"niche": "PRD", "avg_score": 52, "strong_go_count": 3,
    #   "avg_competition": 65, "moat_strength": "MEDIUM",
    #   "top_cluster": "PRD - MVP Scoping"}]

    # Pricing gaps (from Wave 9)
    pricing_gaps: list[dict]
    # [{"niche": "AI Agent", "tier": "standard", "gap_start": 150, "gap_end": 250}]

    # Quality gaps (from Wave 5)
    quality_gaps: list[dict]
    # [{"niche": "PRD", "gap_type": "no_architecture_diagrams", "frequency": "78% of top 10"}]

    # Trend signals
    trend_signals: list[dict]
    # [{"keyword": "Claude API", "source": "google_trends", "direction": "RISING",
    #   "acceleration": 3.2}]

    # User skill profile
    skill_profile: dict
    # {"primary_skills": ["Python", "AI/ML", "automation", "technical writing"],
    #  "tools": ["OpenAI", "Claude", "Playwright", "n8n", "Make"],
    #  "experience_level": "intermediate"}

    # Existing niche list (for deduplication)
    existing_niches: list[str]
    existing_keywords: list[str]

    # Discovery feedback from previous cycles
    feedback_summary: dict
    # {"total_hypotheses": 42, "gold_hits": 3, "avg_actual_score": 48.2,
    #  "best_mode": "adjacent_keyword", "worst_mode": "trend_chase",
    #  "pattern_notes": "Adjacent keywords in PRD niche hit 60% of the time..."}

    # Budget constraints
    max_hypotheses_this_run: int  # From config, default 15
    max_discovery_cost_usd: float  # From config, default 0.50


def build_discovery_context(run_id: str, db, config) -> DiscoveryContext:
    """Assembles all data needed for discovery hypothesis generation."""

    # Top 10 keywords by final score
    top_keywords = get_top_keywords(db, limit=10, min_score=60)

    # Bottom 10 keywords (for negative learning)
    bottom_keywords = get_bottom_keywords(db, limit=10, max_score=30)

    # Niche summaries
    niche_summaries = []
    for niche_id in get_active_niche_ids(db):
        summary = build_niche_summary(niche_id, db)
        niche_summaries.append(summary)

    # Pricing gaps from Wave 9
    pricing_gaps = get_all_pricing_gaps(db)

    # Quality gaps from Wave 5
    quality_gaps = get_all_quality_gaps(db)

    # Trend signals
    trend_signals = get_rising_trends(db, min_acceleration=1.5)

    # Skill profile from config
    skill_profile = config.get("discovery", {}).get("skill_profile", {
        "primary_skills": ["Python", "AI/ML", "automation", "technical writing"],
        "tools": ["OpenAI", "Claude", "Playwright", "n8n", "Make"],
        "experience_level": "intermediate",
    })

    # Existing keywords for dedup
    existing_keywords = [kw.keyword_text for kw in db.query(Keyword).all()]
    existing_niches = [n.name for n in db.query(NicheConfig).all()]

    # Feedback from previous discovery cycles
    feedback_summary = build_feedback_summary(db)

    # Budget
    max_hypotheses = config.get("discovery", {}).get("max_hypotheses_per_run", 15)
    max_cost = config.get("discovery", {}).get("max_cost_per_run_usd", 0.50)

    return DiscoveryContext(
        top_keywords=top_keywords,
        bottom_keywords=bottom_keywords,
        niche_summaries=niche_summaries,
        pricing_gaps=pricing_gaps,
        quality_gaps=quality_gaps,
        trend_signals=trend_signals,
        skill_profile=skill_profile,
        existing_niches=existing_niches,
        existing_keywords=existing_keywords,
        feedback_summary=feedback_summary,
        max_hypotheses_this_run=max_hypotheses,
        max_discovery_cost_usd=max_cost,
    )
```

---

## Discovery Orchestrator

```python
# src/discovery/orchestrator.py

import asyncio

async def run_discovery_stage(
    run_id: str,
    db,
    config,
    llm_client,
    cache,
) -> dict:
    """
    Stage 16: Discovery Engine orchestrator.
    """
    discovery_config = config.get("discovery", {})
    if not discovery_config.get("enabled", True):
        log.info("Discovery engine disabled in config — skipping Stage 16")
        return {"status": "disabled"}

    context = build_discovery_context(run_id, db, config)

    # Determine which modes to run this cycle
    run_number = get_total_run_count(db)
    modes_to_run = _select_modes(run_number, discovery_config)

    log.info(f"Stage 16: Running discovery modes: {modes_to_run}")

    # Generate hypotheses (concurrent across modes)
    all_hypotheses = []
    total_cost = 0.0

    tasks = []
    for mode in modes_to_run:
        tasks.append(generate_hypotheses(mode, context, llm_client, cache))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for mode, result in zip(modes_to_run, results):
        if isinstance(result, Exception):
            log.warning(f"Discovery mode {mode} failed: {result}")
            continue
        all_hypotheses.extend(result.get("hypotheses", []))
        total_cost += result.get("cost_usd", 0.0)

    log.info(f"Discovery generated {len(all_hypotheses)} raw hypotheses "
             f"(cost: ${total_cost:.3f})")

    # Gate: filter by confidence threshold
    min_confidence = discovery_config.get("min_hypothesis_confidence", 0.50)
    gated = [h for h in all_hypotheses if h["hypothesis_confidence"] >= min_confidence]
    log.info(f"After confidence gate (≥{min_confidence}): {len(gated)} hypotheses")

    # Deduplicate against existing keywords
    deduped = _deduplicate(gated, context.existing_keywords)
    log.info(f"After deduplication: {len(deduped)} new hypotheses")

    # Enforce budget limit
    max_hypotheses = context.max_hypotheses_this_run
    accepted = deduped[:max_hypotheses]

    # Insert accepted hypotheses into keywords table
    inserted_count = 0
    for hypothesis in accepted:
        keyword_id = insert_discovery_keyword(hypothesis, run_id, db)
        if keyword_id:
            inserted_count += 1
            # Queue collection jobs for next run
            queue_discovery_collection(keyword_id, hypothesis, db)

    # Log discovery cycle
    log_discovery_cycle(
        run_id=run_id,
        modes_run=modes_to_run,
        hypotheses_generated=len(all_hypotheses),
        hypotheses_gated=len(gated),
        hypotheses_accepted=inserted_count,
        total_cost_usd=total_cost,
        db=db,
    )

    return {
        "status": "complete",
        "modes_run": modes_to_run,
        "hypotheses_generated": len(all_hypotheses),
        "hypotheses_accepted": inserted_count,
        "cost_usd": total_cost,
    }


def _select_modes(run_number: int, config: dict) -> list[str]:
    """
    Determines which discovery modes to run this cycle.
    Adjacent keyword runs every time.
    Adjacent niche runs every 3rd run.
    Gap exploit runs every time (after Wave 9).
    Trend chase runs every time.
    """
    modes = ["adjacent_keyword", "gap_exploit", "trend_chase"]

    if run_number % 3 == 0:
        modes.append("adjacent_niche")

    # Respect config overrides
    enabled_modes = config.get("enabled_modes", modes)
    return [m for m in modes if m in enabled_modes]


def _deduplicate(hypotheses: list[dict], existing_keywords: list[str]) -> list[dict]:
    """
    Removes hypotheses that match existing keywords.
    Uses normalized lowercase comparison + Jaccard similarity > 0.80.
    """
    existing_normalized = {kw.lower().strip() for kw in existing_keywords}
    unique = []

    for h in hypotheses:
        suggested = h["suggested_keyword"].lower().strip()

        # Exact match
        if suggested in existing_normalized:
            continue

        # Jaccard similarity check (catch near-duplicates)
        is_duplicate = False
        suggested_tokens = set(suggested.split())
        for existing in existing_normalized:
            existing_tokens = set(existing.split())
            if suggested_tokens and existing_tokens:
                jaccard = len(suggested_tokens & existing_tokens) / len(
                    suggested_tokens | existing_tokens
                )
                if jaccard > 0.80:
                    is_duplicate = True
                    break

        if not is_duplicate:
            unique.append(h)
            existing_normalized.add(suggested)  # Prevent intra-batch duplicates

    return unique
```

---

## Hypothesis Insertion and Collection Queueing

```python
def insert_discovery_keyword(
    hypothesis: dict,
    run_id: str,
    db,
) -> int | None:
    """
    Inserts a discovery hypothesis as a new keyword in the keywords table.
    Returns the keyword_id or None if insertion failed.
    """
    # Determine which niche to assign this keyword to
    niche_id = hypothesis.get("target_niche_id")
    if not niche_id:
        # For adjacent_niche mode, create a temporary "discovery" niche
        niche_id = "discovery_pool"
        ensure_discovery_niche_exists(db)

    keyword = Keyword(
        keyword_text=hypothesis["suggested_keyword"],
        niche_id=niche_id,
        source="discovery",
        discovery_mode=hypothesis.get("mode"),
        hypothesis_confidence=hypothesis.get("hypothesis_confidence"),
        hypothesis_rationale=hypothesis.get("rationale"),
        discovered_in_run=run_id,
        intent_class=None,  # Will be classified during normal pipeline
        is_discovery=True,
    )
    db.add(keyword)
    db.commit()

    log.info(f"Inserted discovery keyword: '{keyword.keyword_text}' "
             f"(mode={hypothesis.get('mode')}, confidence={hypothesis.get('hypothesis_confidence')})")

    return keyword.id


def queue_discovery_collection(keyword_id: int, hypothesis: dict, db):
    """
    Queues collection jobs for a discovery keyword.
    Discovery keywords start at 'standard' depth — enough for scoring
    but not full competitor analysis until they prove valuable.
    """
    jobs = [
        Job(keyword_id=keyword_id, job_type="FIVERR_SEARCH",
            priority="STANDARD", stage=3),
        Job(keyword_id=keyword_id, job_type="GIG_DETAIL",
            priority="STANDARD", stage=4),
    ]

    # Only add external signals if hypothesis confidence is high
    if hypothesis.get("hypothesis_confidence", 0) >= 0.70:
        jobs.append(Job(keyword_id=keyword_id, job_type="GOOGLE_TRENDS_FETCH",
                        priority="LOW", stage=6))

    for job in jobs:
        db.add(job)
    db.commit()
```

---

## Feedback Loop — Learning from Results

```python
# src/discovery/feedback.py

def evaluate_discovery_results(run_id: str, db):
    """
    Called at the START of each discovery cycle to evaluate
    hypotheses from previous runs that now have scores.
    """
    # Find discovery keywords that have been scored since last evaluation
    scored_discoveries = db.query(Keyword).filter(
        Keyword.is_discovery == True,
        Keyword.discovery_evaluated == False,
    ).join(KeywordScore).filter(
        KeywordScore.final_score.isnot(None),
    ).all()

    for keyword in scored_discoveries:
        score = db.query(KeywordScore).filter(
            KeywordScore.keyword_id == keyword.id,
        ).first()

        # Record the outcome
        outcome = DiscoveryOutcome(
            keyword_id=keyword.id,
            keyword_text=keyword.keyword_text,
            niche_id=keyword.niche_id,
            discovery_mode=keyword.discovery_mode,
            hypothesis_confidence=keyword.hypothesis_confidence,
            actual_final_score=score.final_score,
            actual_tag=get_tag_for_keyword(keyword.id, db),
            score_delta=score.final_score - (keyword.hypothesis_confidence * 100),
            is_gold=score.final_score >= 85,
            is_hit=score.final_score >= 60,  # CONDITIONAL GO or better
            is_miss=score.final_score < 40,  # Below MONITOR
        )
        db.add(outcome)

        # Mark as evaluated
        keyword.discovery_evaluated = True

        # Gold alert
        if outcome.is_gold:
            create_alert(
                alert_type="NEW_GOLD_DISCOVERY",
                severity="HIGH",
                message=(f"🏆 Gold discovery: '{keyword.keyword_text}' scored "
                         f"{score.final_score:.1f} (mode: {keyword.discovery_mode})"),
                metadata={
                    "keyword_id": keyword.id,
                    "keyword_text": keyword.keyword_text,
                    "final_score": score.final_score,
                    "discovery_mode": keyword.discovery_mode,
                },
                db=db,
            )

        # Auto-retire: low-scoring discoveries don't get rescored
        if score.final_score < 30:
            keyword.is_retired = True
            log.info(f"Auto-retired discovery keyword '{keyword.keyword_text}' "
                     f"(score: {score.final_score:.1f})")

    db.commit()


def build_feedback_summary(db) -> dict:
    """
    Builds a summary of all discovery outcomes to feed back to the LLM.
    The LLM uses this to improve future hypothesis quality.
    """
    outcomes = db.query(DiscoveryOutcome).all()

    if not outcomes:
        return {
            "total_hypotheses": 0,
            "note": "No discovery history yet — first cycle",
        }

    total = len(outcomes)
    gold_count = sum(1 for o in outcomes if o.is_gold)
    hit_count = sum(1 for o in outcomes if o.is_hit)
    miss_count = sum(1 for o in outcomes if o.is_miss)
    avg_score = sum(o.actual_final_score for o in outcomes) / total

    # Per-mode breakdown
    mode_stats = {}
    for mode in ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]:
        mode_outcomes = [o for o in outcomes if o.discovery_mode == mode]
        if mode_outcomes:
            mode_stats[mode] = {
                "count": len(mode_outcomes),
                "avg_score": round(sum(o.actual_final_score for o in mode_outcomes) / len(mode_outcomes), 1),
                "hit_rate": round(sum(1 for o in mode_outcomes if o.is_hit) / len(mode_outcomes) * 100, 1),
                "gold_count": sum(1 for o in mode_outcomes if o.is_gold),
            }

    # Find best and worst modes
    best_mode = max(mode_stats.items(), key=lambda x: x[1]["hit_rate"])[0] if mode_stats else None
    worst_mode = min(mode_stats.items(), key=lambda x: x[1]["hit_rate"])[0] if mode_stats else None

    # Pattern analysis: what characteristics do hits share?
    hit_niches = [o.niche_id for o in outcomes if o.is_hit]
    miss_niches = [o.niche_id for o in outcomes if o.is_miss]

    # Top hit niches
    from collections import Counter
    hit_niche_counts = Counter(hit_niches).most_common(3)
    miss_niche_counts = Counter(miss_niches).most_common(3)

    return {
        "total_hypotheses": total,
        "gold_hits": gold_count,
        "hits": hit_count,
        "misses": miss_count,
        "hit_rate_pct": round(hit_count / total * 100, 1),
        "avg_actual_score": round(avg_score, 1),
        "mode_stats": mode_stats,
        "best_mode": best_mode,
        "worst_mode": worst_mode,
        "top_hit_niches": [{"niche": n, "count": c} for n, c in hit_niche_counts],
        "top_miss_niches": [{"niche": n, "count": c} for n, c in miss_niche_counts],
        "pattern_notes": _generate_pattern_notes(outcomes, mode_stats),
    }


def _generate_pattern_notes(outcomes, mode_stats) -> str:
    """
    Generates a concise summary of discovery patterns for the LLM feedback prompt.
    """
    notes = []

    # Mode performance
    for mode, stats in mode_stats.items():
        if stats["hit_rate"] >= 40:
            notes.append(f"{mode} performs well ({stats['hit_rate']}% hit rate, "
                        f"avg score {stats['avg_score']})")
        elif stats["hit_rate"] < 15:
            notes.append(f"{mode} underperforms ({stats['hit_rate']}% hit rate) — "
                        "consider adjusting strategy")

    # Gold patterns
    gold_outcomes = [o for o in outcomes if o.is_gold]
    if gold_outcomes:
        gold_niches = [o.niche_id for o in gold_outcomes]
        notes.append(f"Gold discoveries found in: {', '.join(set(gold_niches))}")

    return "; ".join(notes) if notes else "Not enough data for pattern analysis yet"
```

---

## Discovery Budget Management

```python
# Discovery budget controls in config.yaml:

# discovery:
#   enabled: true
#   max_hypotheses_per_run: 15
#   max_cost_per_run_usd: 0.50
#   min_hypothesis_confidence: 0.50
#   gold_threshold: 85
#   auto_retire_threshold: 30
#   enabled_modes:
#     - adjacent_keyword
#     - gap_exploit
#     - trend_chase
#     - adjacent_niche
#   skill_profile:
#     primary_skills: ["Python", "AI/ML", "automation", "technical writing"]
#     tools: ["OpenAI", "Claude", "Playwright", "n8n", "Make"]
#     experience_level: "intermediate"
#   adjacent_niche_frequency: 3  # every Nth run
```

**Cost estimation per discovery cycle:**

| Mode | Model | Calls | Est. Cost |
|---|---|---|---|
| Adjacent keyword | gpt-4o | 1 | ~$0.08 |
| Gap exploit | gpt-4o | 1 | ~$0.06 |
| Trend chase | gpt-4o | 1 | ~$0.06 |
| Adjacent niche (every 3rd) | gpt-4o | 1 | ~$0.10 |
| Feedback evaluation | gpt-4o-mini | 1 | ~$0.01 |
| **Total per cycle** | | **3–4 calls** | **~$0.20–0.30** |

---

## Storage Schema — New Tables

```python
class DiscoveryOutcome(Base):
    """Tracks the outcome of each discovery hypothesis after scoring."""
    __tablename__ = "discovery_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    keyword_text = Column(String, nullable=False)
    niche_id = Column(String, nullable=False)
    discovery_mode = Column(String, nullable=False)
    hypothesis_confidence = Column(Float, nullable=False)
    actual_final_score = Column(Float, nullable=False)
    actual_tag = Column(String)
    score_delta = Column(Float)  # actual - (confidence * 100)
    is_gold = Column(Boolean, default=False)
    is_hit = Column(Boolean, default=False)  # Score >= 60
    is_miss = Column(Boolean, default=False)  # Score < 40
    evaluated_at = Column(DateTime, default=datetime.utcnow)


class DiscoveryCycleLog(Base):
    """Logs each discovery cycle's results."""
    __tablename__ = "discovery_cycle_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False, index=True)
    modes_run = Column(JSON)
    hypotheses_generated = Column(Integer)
    hypotheses_gated = Column(Integer)
    hypotheses_accepted = Column(Integer)
    total_cost_usd = Column(Float)
    feedback_summary = Column(JSON)
    cycle_at = Column(DateTime, default=datetime.utcnow)
```

**Keywords table additions:**

```python
# New columns on existing Keyword model:
is_discovery = Column(Boolean, default=False, index=True)
discovery_mode = Column(String, nullable=True)
hypothesis_confidence = Column(Float, nullable=True)
hypothesis_rationale = Column(Text, nullable=True)
discovered_in_run = Column(String, nullable=True)
discovery_evaluated = Column(Boolean, default=False)
is_retired = Column(Boolean, default=False)
```

---

## Run Mode Integration

| Run Mode | Discovery Behavior |
|---|---|
| `--mode full` | Stage 16 runs at end of pipeline |
| `--mode discovery-only` | Runs Stage 16 only — generates hypotheses but doesn't collect |
| `--mode collect-only` | Does NOT run Stage 16 |
| `--mode score-only` | Does NOT run Stage 16, but evaluates previous discovery outcomes |
| `--mode discovery-collect` | Runs collection for pending discovery keywords + new Stage 16 cycle |

---

## Discovery Lifecycle Example

```
Run 1: System has 9 niches, 312 keywords scored.
  Stage 16: Discovery generates 12 hypotheses.
  8 pass confidence gate. 7 are unique. Inserted into keywords table.

Run 2: 7 discovery keywords collected and scored.
  Evaluation: 3 scored 60+ (hits), 2 scored 40-59 (monitor), 2 scored <30 (auto-retired).
  Stage 16: Feedback notes "adjacent_keyword hit rate 57%, gap_exploit hit rate 25%".
  New cycle generates 10 hypotheses, informed by feedback.

Run 3: Adjacent niche mode runs (every 3rd run).
  Discovers "AI data pipeline documentation" niche — generates 5 seed keywords.
  2 discovery keywords from Run 2 now score 85+ → GOLD ALERT triggered.

Run 5: Discovery hit rate stabilizes at 35-40%.
  Feedback loop has learned: "Keywords with 'integration' in the name hit 2x more often
  than generic keywords. Trend-based hypotheses underperform — reducing weight."
  System self-adjusts mode allocation.
```
