# Hypothesis Generation Prompts
# Fiverr Research System — Wave 10

**Document Status:** Complete
**Wave:** 10 — LLM-Powered Niche Discovery
**Purpose:** All 4 Jinja2 prompt templates for discovery modes — adjacent keyword, adjacent niche, gap exploit, and trend chase. Each with input variables, output schema, and calibration guidance.

---

## Template File Organization

```
src/llm/prompts/stage16_discovery/
├── adjacent_keyword.j2
├── adjacent_niche.j2
├── gap_exploit.j2
└── trend_chase.j2
```

All templates receive the `DiscoveryContext` from DISCOVERY_ENGINE_ARCHITECTURE.md. Model: gpt-4o. Temperature: 0.4 (slightly creative). JSON-only output mode.

---

## Template 1 — adjacent_keyword.j2

```jinja2
You are a Fiverr keyword researcher specializing in finding UNSEEN opportunities
adjacent to known high-performing keywords.

YOUR SKILL PROFILE:
{{ skill_profile.primary_skills | join(", ") }}
Tools: {{ skill_profile.tools | join(", ") }}

TOP PERFORMING KEYWORDS (these score well — find MORE like them):
{% for kw in top_keywords[:10] %}
{{ loop.index }}. "{{ kw.keyword }}" — Score: {{ kw.final_score | round(1) }}, Tag: {{ kw.tag }}
   Niche: {{ kw.niche }}, Cluster: {{ kw.cluster_label }}
   Demand: {{ kw.demand | round(0) }}, Competition: {{ kw.competition | round(0) }}
   Market: {{ kw.market_type }}
{% endfor %}

BOTTOM PERFORMING KEYWORDS (these fail — AVOID similar patterns):
{% for kw in bottom_keywords[:5] %}
- "{{ kw.keyword }}" — Score: {{ kw.final_score | round(1) }}, Niche: {{ kw.niche }}
{% endfor %}

{% if feedback_summary.total_hypotheses > 0 %}
FEEDBACK FROM YOUR PREVIOUS SUGGESTIONS:
- Total suggestions so far: {{ feedback_summary.total_hypotheses }}
- Hit rate (scored 60+): {{ feedback_summary.hit_rate_pct }}%
- Average actual score: {{ feedback_summary.avg_actual_score }}
- Gold discoveries (85+): {{ feedback_summary.gold_hits }}
{% if feedback_summary.mode_stats.adjacent_keyword %}
- YOUR MODE (adjacent_keyword): {{ feedback_summary.mode_stats.adjacent_keyword.hit_rate }}% hit rate, avg {{ feedback_summary.mode_stats.adjacent_keyword.avg_score }}
{% endif %}
{% if feedback_summary.pattern_notes %}
- Patterns learned: {{ feedback_summary.pattern_notes }}
{% endif %}
{% endif %}

EXISTING KEYWORDS (do NOT suggest duplicates or near-matches):
{{ existing_keywords[:50] | join(", ") }}
{% if existing_keywords | length > 50 %}
... and {{ existing_keywords | length - 50 }} more
{% endif %}

TASK: Suggest 5-10 NEW keywords that are ADJACENT to the top performers above.

Adjacent means:
- Same buyer intent but different phrasing
- Same service but narrower specialization (e.g., "AI PRD" → "AI MVP feature spec")
- Same niche but targeting a different buyer segment
- Related deliverable the same buyer would also search for

For each suggestion, estimate:
- hypothesis_confidence: 0.0-1.0 (how likely this scores 60+)
- expected_demand: LOW/MEDIUM/HIGH
- expected_competition: LOW/MEDIUM/HIGH

Return JSON only. No preamble.

{
  "hypotheses": [
    {
      "suggested_keyword": "string",
      "mode": "adjacent_keyword",
      "target_niche_id": "string (existing niche_id this belongs to)",
      "rationale": "string (must reference specific top keyword it's adjacent to and WHY)",
      "hypothesis_confidence": float,
      "expected_demand": "LOW|MEDIUM|HIGH",
      "expected_competition": "LOW|MEDIUM|HIGH",
      "category_path": "string (Fiverr category path)"
    }
  ]
}
```

---

## Template 2 — adjacent_niche.j2

```jinja2
You are a Fiverr market researcher finding ENTIRELY NEW service niches
where a seller with specific skills can compete with low competition and high demand.

SELLER'S SKILL PROFILE:
Primary: {{ skill_profile.primary_skills | join(", ") }}
Tools: {{ skill_profile.tools | join(", ") }}
Level: {{ skill_profile.experience_level }}

NICHES ALREADY BEING RESEARCHED (do NOT suggest these or close variants):
{% for niche in niche_summaries %}
- {{ niche.niche }} (avg score: {{ niche.avg_score }}, STRONG GO: {{ niche.strong_go_count }})
{% endfor %}

WHAT WORKS (characteristics of high-scoring niches):
{% for niche in niche_summaries | sort(attribute='avg_score', reverse=True) %}
{% if niche.avg_score >= 55 %}
- {{ niche.niche }}: avg {{ niche.avg_score }}, competition {{ niche.avg_competition }}, moat {{ niche.moat_strength }}
{% endif %}
{% endfor %}

WHAT DOESN'T WORK (low-scoring niches):
{% for niche in niche_summaries | sort(attribute='avg_score') %}
{% if niche.avg_score < 40 %}
- {{ niche.niche }}: avg {{ niche.avg_score }} — likely too competitive or low demand
{% endif %}
{% endfor %}

{% if feedback_summary.total_hypotheses > 0 %}
DISCOVERY FEEDBACK:
- Total discoveries: {{ feedback_summary.total_hypotheses }}, Gold: {{ feedback_summary.gold_hits }}
{% if feedback_summary.mode_stats.adjacent_niche %}
- Adjacent niche mode: {{ feedback_summary.mode_stats.adjacent_niche.hit_rate }}% hit rate
{% endif %}
{% if feedback_summary.top_hit_niches %}
- Best-performing discovery niches: {% for n in feedback_summary.top_hit_niches %}{{ n.niche }} ({{ n.count }} hits){% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
{% endif %}

FIVERR CATEGORY TREE (AI/Python relevant branches):
- Programming & Tech > AI & Machine Learning > [AI Agents, AI Applications, AI Integrations, AI Technology Consulting]
- Programming & Tech > Software Development > [Automations & Workflows, Desktop Applications, Scripts & Utilities]
- Programming & Tech > Web Programming > [Python, JavaScript, ...]
- Writing & Translation > Technical Writing
- Data > Data Science & ML, Data Processing, Data Visualization
- Business > Market Research, Business Plans

TASK: Suggest 3-5 ENTIRELY NEW niches that:
1. Match the seller's skill profile
2. Are likely UNSATURATED on Fiverr (not yet flooded with sellers)
3. Have genuine buyer demand (people are searching for this service)
4. Can be delivered by one person
5. Have pricing potential above $75 for basic tier

For each niche, provide 3 seed keywords to test.

Return JSON only:

{
  "hypotheses": [
    {
      "suggested_keyword": "string (primary seed keyword for this niche)",
      "mode": "adjacent_niche",
      "target_niche_id": null,
      "niche_name": "string (human-readable name for the new niche)",
      "niche_description": "string (what service this niche provides)",
      "category_path": "string (Fiverr category path)",
      "seed_keywords": ["keyword1", "keyword2", "keyword3"],
      "rationale": "string (why this niche should work, reference skill profile and market gap)",
      "hypothesis_confidence": float,
      "expected_demand": "LOW|MEDIUM|HIGH",
      "expected_competition": "LOW|MEDIUM|HIGH",
      "estimated_basic_price": integer
    }
  ]
}
```

---

## Template 3 — gap_exploit.j2

```jinja2
You are a Fiverr competitive strategist identifying keywords that target
SPECIFIC GAPS found in existing market data.

PRICING GAPS DETECTED (empty price bands where no sellers compete):
{% for gap in pricing_gaps[:10] %}
- {{ gap.niche }}, {{ gap.tier }} tier: ${{ gap.gap_start }}–${{ gap.gap_end }} (no sellers in this range)
{% endfor %}

QUALITY GAPS DETECTED (weaknesses most competitors share):
{% for gap in quality_gaps[:10] %}
- {{ gap.niche }}: {{ gap.gap_type }} ({{ gap.frequency }})
{% endfor %}

TOP COMPETITOR WEAKNESSES ACROSS ALL NICHES:
{% for niche in niche_summaries %}
{% if niche.top_weaknesses %}
{{ niche.niche }}:
{% for w in niche.top_weaknesses[:3] %}
  - {{ w }}
{% endfor %}
{% endif %}
{% endfor %}

SELLER'S SKILLS: {{ skill_profile.primary_skills | join(", ") }}

{% if feedback_summary.mode_stats.gap_exploit %}
FEEDBACK ON GAP EXPLOIT MODE:
- Hit rate: {{ feedback_summary.mode_stats.gap_exploit.hit_rate }}%
- Avg score: {{ feedback_summary.mode_stats.gap_exploit.avg_score }}
{% endif %}

TASK: Suggest 5-8 keywords that a buyer would search when they SPECIFICALLY want
what the gaps reveal is missing. Think from the buyer's perspective.

Example reasoning: "If 78% of AI agent gigs lack architecture diagrams, a buyer
who specifically wants architecture docs with their agent might search
'AI agent with architecture documentation' or 'documented AI agent development'."

Each keyword should TARGET a specific gap — not just be a generic keyword.

Return JSON only:

{
  "hypotheses": [
    {
      "suggested_keyword": "string",
      "mode": "gap_exploit",
      "target_niche_id": "string (existing niche this relates to)",
      "gap_targeted": "string (which specific gap this keyword exploits)",
      "gap_type": "pricing|quality|positioning",
      "rationale": "string (how this keyword targets the gap, from buyer's search perspective)",
      "hypothesis_confidence": float,
      "expected_demand": "LOW|MEDIUM|HIGH",
      "expected_competition": "LOW|MEDIUM|HIGH",
      "category_path": "string"
    }
  ]
}
```

---

## Template 4 — trend_chase.j2

```jinja2
You are a Fiverr trend analyst identifying EMERGING keywords before they become
saturated. You combine external trend signals with Fiverr market knowledge.

RISING TREND SIGNALS:
{% for signal in trend_signals[:15] %}
- "{{ signal.keyword }}": {{ signal.source }}, direction {{ signal.direction }}, acceleration {{ signal.acceleration }}x
{% endfor %}

{% if not trend_signals %}
(No strong trend signals detected this cycle — rely on general AI/Python/automation industry knowledge)
{% endif %}

SELLER'S SKILLS: {{ skill_profile.primary_skills | join(", ") }}
TOOLS: {{ skill_profile.tools | join(", ") }}

EXISTING NICHES (already covered):
{% for niche in existing_niches %}
- {{ niche }}
{% endfor %}

{% if feedback_summary.mode_stats.trend_chase %}
FEEDBACK ON TREND CHASE MODE:
- Hit rate: {{ feedback_summary.mode_stats.trend_chase.hit_rate }}%
- Avg score: {{ feedback_summary.mode_stats.trend_chase.avg_score }}
{% if feedback_summary.mode_stats.trend_chase.hit_rate < 20 %}
- NOTE: This mode has underperformed. Focus on trends with CLEAR buyer intent,
  not just rising search volume. A trend needs to translate to "someone will pay
  for this on Fiverr" to be valuable.
{% endif %}
{% endif %}

CURRENT DATE: {{ current_date }}

TASK: Suggest 3-5 EMERGING keywords that:
1. Relate to a trend that's GROWING but not yet saturated on Fiverr
2. Match the seller's skills
3. Have clear BUYER intent (someone would pay for this service)
4. Can realistically become a viable gig within 1-3 months

For each, rate urgency:
- IMMEDIATE: trend is accelerating fast — enter within 2 weeks or miss window
- MODERATE: growing steadily — enter within 1 month
- WATCH: early signal — monitor for 1-2 more cycles before committing

Return JSON only:

{
  "hypotheses": [
    {
      "suggested_keyword": "string",
      "mode": "trend_chase",
      "target_niche_id": "string or null",
      "trend_source": "string (what trend signal prompted this)",
      "urgency": "IMMEDIATE|MODERATE|WATCH",
      "rationale": "string (why this trend creates Fiverr demand NOW)",
      "hypothesis_confidence": float,
      "expected_demand": "LOW|MEDIUM|HIGH",
      "expected_competition": "LOW|MEDIUM|HIGH",
      "category_path": "string"
    }
  ]
}
```

---

## Prompt Engineering Notes

1. **Temperature 0.4** — higher than recommendation tasks (0.2) because discovery benefits from creative divergence. Not so high (0.7+) that outputs become unreliable.

2. **Feedback integration is critical.** The feedback block in each prompt changes the LLM's behavior over time. Early cycles have no feedback → LLM uses priors. After 3+ cycles, feedback steers the LLM away from unproductive patterns and toward proven strategies.

3. **Negative examples matter.** Including bottom-performing keywords teaches the LLM what to avoid. Without these, it tends to suggest generic high-volume keywords that are actually oversaturated.

4. **Deduplication list is essential.** Without it, the LLM frequently suggests keywords that are already in the database (just rephrased slightly). The explicit list + Jaccard similarity check catches 90%+ of duplicates.

5. **All templates enforce JSON-only output.** Same pattern as Wave 7 recommendation prompts.

6. **Self-correction retry on ValidationError.** Same policy: one retry with error appended.

---

## Hypothesis Output Schema

```python
# src/schemas/discovery_output.py

from pydantic import BaseModel, Field, validator

class DiscoveryHypothesis(BaseModel):
    """Single keyword/niche suggestion from the discovery engine."""
    suggested_keyword: str = Field(..., min_length=3, max_length=100)
    mode: str  # adjacent_keyword | adjacent_niche | gap_exploit | trend_chase
    target_niche_id: str | None = None
    rationale: str = Field(..., min_length=30, max_length=400)
    hypothesis_confidence: float = Field(..., ge=0.0, le=1.0)
    expected_demand: str  # LOW | MEDIUM | HIGH
    expected_competition: str  # LOW | MEDIUM | HIGH
    category_path: str | None = None

    # Mode-specific fields (optional)
    niche_name: str | None = None  # adjacent_niche only
    niche_description: str | None = None  # adjacent_niche only
    seed_keywords: list[str] | None = None  # adjacent_niche only
    gap_targeted: str | None = None  # gap_exploit only
    gap_type: str | None = None  # gap_exploit only
    trend_source: str | None = None  # trend_chase only
    urgency: str | None = None  # trend_chase only
    estimated_basic_price: int | None = None  # adjacent_niche only

    @validator("mode")
    def valid_mode(cls, v):
        valid = {"adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"}
        if v not in valid:
            raise ValueError(f"Invalid mode: {v}")
        return v

    @validator("expected_demand", "expected_competition")
    def valid_level(cls, v):
        if v not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError(f"Must be LOW, MEDIUM, or HIGH")
        return v


class DiscoveryOutput(BaseModel):
    """Output from a single discovery mode prompt."""
    hypotheses: list[DiscoveryHypothesis] = Field(..., min_items=1, max_items=15)
```

---

## LLM Execution

```python
async def generate_hypotheses(
    mode: str,
    context: DiscoveryContext,
    llm_client,
    cache,
) -> dict:
    """Generates hypotheses for a single discovery mode."""

    template_map = {
        "adjacent_keyword": "adjacent_keyword.j2",
        "adjacent_niche": "adjacent_niche.j2",
        "gap_exploit": "gap_exploit.j2",
        "trend_chase": "trend_chase.j2",
    }

    prompt = render_template(
        f"stage16_discovery/{template_map[mode]}",
        **context.model_dump(),
        current_date=datetime.utcnow().strftime("%Y-%m-%d"),
    )

    # Cache check
    cache_key = build_cache_key("gpt-4o", 0.4, prompt)
    cached = cache.get(cache_key)
    if cached:
        return {"hypotheses": cached, "cost_usd": 0.0}

    # LLM call
    result = await llm_client.complete(
        prompt=prompt,
        model="gpt-4o",
        temperature=0.4,
        response_format={"type": "json_object"},
    )

    parsed = json.loads(result.content)
    output = DiscoveryOutput(**parsed)

    # Cache
    cache.set(cache_key, [h.model_dump() for h in output.hypotheses], ttl_hours=24)

    return {
        "hypotheses": [h.model_dump() for h in output.hypotheses],
        "cost_usd": result.usage_cost,
    }
```
