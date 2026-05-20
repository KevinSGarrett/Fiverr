# LLM Prompt Templates
# Fiverr Research System — Wave 7

**Document Status:** Complete
**Wave:** 7 — Recommendation Engine
**Purpose:** All 11 Stage 13 Jinja2 prompt templates — copy-paste ready with input variables, output JSON schemas, and quality calibration examples.

---

## Template File Organization

```
src/llm/prompts/stage13_recommendations/
├── gig_titles.j2
├── tag_sets.j2
├── package_structure.j2
├── description_outline.j2
├── faq_entries.j2
├── differentiation_angle.j2
├── buyer_persona.j2
├── thumbnail_direction.j2
├── upsell_structure.j2
├── red_flags.j2
└── niche_viability.j2
```

Each template receives the `RecommendationContext` object from RECOMMENDATION_ENGINE.md.

---

## Template 1 — gig_titles.j2

```jinja2
You are a Fiverr gig title optimization specialist. Create 5 gig title variants
for a {{ niche_name }} service targeting the keyword "{{ keyword_text }}".

CONTEXT:
- This keyword has {{ total_result_count or "unknown" }} existing results on Fiverr
- Competition level: {{ competition_score | round(0) }}/100
- Demand level: {{ demand_score | round(0) }}/100
- Top competitor titles:
{% for comp in top_competitor_weaknesses[:3] %}
  - "{{ comp.gig_title }}"
{% endfor %}

REQUIREMENTS:
1. Every title MUST start with "I will"
2. Every title MUST contain "{{ keyword_text }}" or a close semantic variant
3. Length: 60–80 characters each
4. Each title must use a DIFFERENT positioning angle:
   - Title 1: Outcome-focused ("I will create a [deliverable] that [outcome]")
   - Title 2: Specialist-focused ("I will [action] as a [credential] specialist")
   - Title 3: Speed-focused ("I will [action] with [timeframe] turnaround")
   - Title 4: Proof-focused ("I will [action] backed by [proof element]")
   - Title 5: Scope-focused ("I will [action] including [specific extras]")
5. NO generic words: "best", "amazing", "professional", "top-quality", "expert" (unless earned)
6. DIFFERENTIATE from competitor titles listed above

Return JSON only. No preamble.

{
  "titles": [
    {
      "title": "string (60-80 chars, starts with 'I will')",
      "positioning_angle": "outcome|specialist|speed|proof|scope",
      "character_count": integer,
      "primary_keyword_present": boolean
    }
  ]
}
```

---

## Template 2 — tag_sets.j2

```jinja2
Generate 5 tag set options for a Fiverr gig in the {{ niche_name }} niche.
Primary keyword: "{{ keyword_text }}"

Each set must have exactly 5 tags. Tags must be 2–25 characters each.

Competitor tags observed:
{% for comp in top_competitor_weaknesses[:5] %}
{% if comp.tags %}  - {{ comp.tags | join(", ") }}{% endif %}
{% endfor %}

Create 5 sets with different angles:
Set 1: Service-type focused
Set 2: Deliverable-type focused
Set 3: Buyer-type focused
Set 4: Tool/technology focused
Set 5: Industry/use-case focused

Return JSON only:
{ "tag_sets": [["tag1","tag2","tag3","tag4","tag5"], ...] }
```

---

## Template 3 — package_structure.j2

```jinja2
Design a 3-tier Fiverr package structure for a {{ niche_name }} gig.

KEYWORD: "{{ keyword_text }}"
PRICING GUIDANCE (from niche config):
- Basic: ~${{ starter_price_basic }}
- Standard: ~${{ starter_price_standard }}
- Premium: ~${{ starter_price_premium }}

COMPETITOR PACKAGES (top 3 gigs):
{% for comp in top_competitor_weaknesses[:3] %}
{% if comp.packages %}
  {{ comp.gig_title }}:
  {% for pkg in comp.packages %}
    - {{ pkg.name }}: ${{ pkg.price }} — {{ pkg.deliverables | join(", ") }} ({{ pkg.delivery_days }}d, {{ pkg.revisions }} rev)
  {% endfor %}
{% endif %}
{% endfor %}

HARD EXCLUSIONS (must NOT be listed as deliverables):
{% for excl in hard_exclusions %}
- {{ excl }}
{% endfor %}

REQUIREMENTS:
1. Each tier must have a distinct, named scope (not just "more pages")
2. Deliverables must be specific and countable
3. Basic = entry-level quick win. Standard = complete core deliverable. Premium = everything + extras.
4. Prices within ±15% of guidance above
5. Delivery days realistic (Basic 2-4d, Standard 4-7d, Premium 7-14d typical)
6. Revisions increase with tier (1/2/3 typical)

Return JSON only:
{
  "basic": {"name":"...","price":int,"deliverables":[...],"delivery_days":int,"revisions":int},
  "standard": {"name":"...","price":int,"deliverables":[...],"delivery_days":int,"revisions":int},
  "premium": {"name":"...","price":int,"deliverables":[...],"delivery_days":int,"revisions":int}
}
```

---

## Template 4 — description_outline.j2

```jinja2
Create a structured gig description outline for a {{ niche_name }} Fiverr gig.

KEYWORD: "{{ keyword_text }}"
TAG: {{ tag }} (Final Score: {{ final_score | round(1) }})

COMPETITOR WEAKNESSES TO EXPLOIT:
{% for comp in top_competitor_weaknesses[:3] %}
{% for w in comp.weaknesses[:2] %}
- {{ w.weakness }} ({{ w.severity }})
{% endfor %}
{% endfor %}

BUYER COMPLAINTS FROM COMPETITOR REVIEWS:
{% for complaint in top_buyer_complaints[:3] %}
- {{ complaint }}
{% endfor %}

HARD EXCLUSIONS:
{% for excl in hard_exclusions %}
- {{ excl }}
{% endfor %}

Create 5-7 description sections. Requirements:
1. Section 1: Benefit-led hook (NOT "I am a professional..." — start with what the buyer gets)
2. Include a "What You Get" section with specific deliverables
3. Include a "What's NOT Included" section using the hard exclusions above
4. Address at least 2 buyer complaints from the list above
5. End with a clear CTA section
6. Total estimated word count: 400-600 words across all sections

Return JSON only:
{
  "sections": [
    {
      "heading": "string",
      "copy_direction": "string (instructions for what to write)",
      "proof_elements": ["list of proof/credential elements to include"],
      "estimated_words": integer
    }
  ]
}
```

---

## Template 5 — faq_entries.j2

```jinja2
Write 5-7 FAQ entries for a {{ niche_name }} Fiverr gig targeting "{{ keyword_text }}".

BUYER COMPLAINTS FROM COMPETITOR REVIEWS:
{% for complaint in top_buyer_complaints[:5] %}
- {{ complaint }}
{% endfor %}

HARD EXCLUSIONS:
{% for excl in hard_exclusions[:5] %}
- {{ excl }}
{% endfor %}

Requirements:
1. Questions must be phrased as buyers would ask them ("Can you...", "What if...", "Do you...")
2. At least 2 FAQs must address known buyer complaints above
3. At least 1 FAQ must set scope boundaries (prevent scope creep)
4. Answers: 2-4 sentences, specific to this niche
5. Include 1 FAQ about the revision process

Return JSON only:
{
  "faq_entries": [
    {"question":"...","answer":"...","addresses_complaint":"COMPLAINT_TYPE or null"}
  ]
}
```

---

## Template 6 — differentiation_angle.j2

```jinja2
You are a Fiverr competitive positioning strategist. Create a differentiation
angle for a NEW SELLER entering the "{{ keyword_text }}" market in {{ niche_name }}.

TOP COMPETITOR WEAKNESSES (from gig quality analysis):
{% for comp in top_competitor_weaknesses[:5] %}
{{ loop.index }}. "{{ comp.gig_title }}" — Weaknesses:
{% for w in comp.weaknesses %}
   - {{ w.weakness }} ({{ w.severity }}): {{ w.description }}
{% endfor %}
{% endfor %}

BUYER COMPLAINTS FROM COMPETITOR REVIEWS:
{% for complaint in top_buyer_complaints %}
- {{ complaint }}
{% endfor %}

POSITIONING GAPS IDENTIFIED:
{% for gap in positioning_gaps or [] %}
- {{ gap.gap }}: {{ gap.evidence }}
{% endfor %}

COMPETITIVE LANDSCAPE SYNTHESIS:
{{ cluster_synthesis_narrative or "Not available" }}

Create a specific, evidence-based differentiation strategy. Requirements:
1. Reference specific competitor weaknesses by name
2. Connect each weakness to a buyer pain point
3. Provide 3-5 concrete tactical actions the seller should take
4. 100-200 words for positioning statement

Return JSON only:
{
  "positioning_statement": "string (100-200 words)",
  "differentiators": [
    {"action":"...","competitor_weakness_exploited":"...","buyer_pain_addressed":"..."}
  ],
  "one_sentence_pitch": "string (1 sentence positioning statement for quick reference)"
}
```

---

## Template 7 — buyer_persona.j2

```jinja2
Create a buyer persona for someone searching "{{ keyword_text }}" on Fiverr in {{ niche_name }}.

DEMAND SIGNALS:
- Fiverr results: {{ total_result_count or "unknown" }}
- Google Trends direction: {{ trends_slope or "unknown" }}
- Reddit demand intent: {{ reddit_intent_score or "unknown" }}/10
{% if top_buyer_praise %}
- What buyers praise in reviews: {{ top_buyer_praise | join(", ") }}
{% endif %}

Return JSON only:
{
  "name": "string (first name)",
  "role": "string (job title/role)",
  "company_stage": "string",
  "pain_points": ["list of 3-4 pain points"],
  "budget_range": "string ($X–$Y)",
  "decision_trigger": "string (what event makes them search for this)",
  "where_they_search": "string (platforms/channels)",
  "what_makes_them_buy": "string (the deciding factor)"
}
```

---

## Template 8 — thumbnail_direction.j2

```jinja2
Provide thumbnail creative direction for a {{ niche_name }} Fiverr gig: "{{ keyword_text }}".

Competitor thumbnail distribution:
{% for class_name, count in thumbnail_class_distribution.items() %}
- {{ class_name }}: {{ count }} gigs
{% endfor %}

Return JSON only:
{
  "concept": "string (1-2 sentence visual concept)",
  "style": "string (color scheme, aesthetic)",
  "elements_to_include": ["list of 3-4 visual elements"],
  "elements_to_avoid": ["list of 2-3 things NOT to include"],
  "differentiation_note": "string (how this stands out from competitors)"
}
```

---

## Template 9 — upsell_structure.j2

```jinja2
Design 2-4 gig extras (upsells) for a {{ niche_name }} gig at the ${{ starter_price_basic }}–${{ starter_price_premium }} price range.

Competitor extras observed:
{% for extra in competitor_extras[:10] %}
- {{ extra.name }}: ${{ extra.price }}
{% endfor %}

Return JSON only:
{
  "extras": [
    {"name":"string (2-5 words)","price":integer,"description":"string (1 sentence)"}
  ]
}
```

---

## Template 10 — red_flags.j2

```jinja2
Analyze risk factors for a NEW SELLER entering "{{ keyword_text }}" in {{ niche_name }}.

SCORES:
- Demand: {{ demand_score | round(1) }}/100
- Competition: {{ competition_score | round(1) }}/100
- Opportunity: {{ opportunity_score | round(1) }}/100
- Feasibility: {{ feasibility_score | round(1) if feasibility_score else "N/A" }}/100
- Trend: {{ trend_score | round(1) if trend_score else "N/A" }}/100
- Confidence: {{ confidence_modifier | round(2) }}
- Tag: {{ tag }}

COMPETITOR FIELD:
{{ cluster_synthesis_narrative or "Not available" }}

Identify 2-5 specific risk factors. Do NOT list generic risks.

Return JSON only:
{
  "red_flags": [
    {"flag_type":"string","description":"string (specific)","severity":"HIGH|MEDIUM|LOW","mitigation":"string (specific action)"}
  ],
  "overall_risk_level": "LOW|MEDIUM|HIGH",
  "proceed_recommendation": "string (1-2 sentences)"
}
```

---

## Template 11 — niche_viability.j2

```jinja2
Write a strategic niche viability assessment for "{{ keyword_text }}" in {{ niche_name }}.

TAG: {{ tag }}
FINAL SCORE: {{ final_score | round(1) }}/100

ALL SCORES:
- Demand: {{ demand_score | round(1) }}/100
- Competition: {{ competition_score | round(1) }}/100 (lower = weaker competition)
- Opportunity: {{ opportunity_score | round(1) }}/100
- Feasibility: {{ feasibility_score | round(1) if feasibility_score else "N/A" }}/100
- Profitability: {{ profitability_score | round(1) if profitability_score else "N/A" }}/100
- Weakness: {{ weakness_score | round(1) if weakness_score else "N/A" }}/100 (higher = more exploitable)
- Trend: {{ trend_score | round(1) if trend_score else "N/A" }}/100
- Saturation: {{ saturation_score | round(1) if saturation_score else "N/A" }}/100 (lower = less saturated)

COMPETITIVE LANDSCAPE:
{{ cluster_synthesis_narrative or "Not available" }}

OPPORTUNITY CONTEXT:
{{ opportunity_narrative or "Not available" }}

{% if tag == "STRONG GO" %}
Frame this as an actionable opportunity — tell the seller what to do now and what to expect.
{% else %}
Frame this as a conditional opportunity — identify what conditions need to be true before acting.
{% endif %}

Write a 100-300 word strategic assessment covering:
1. Why this opportunity exists right now (reference actual score values)
2. Timing considerations (trend direction, market stage)
3. Primary risk and its mitigation
4. Blunt recommendation: enter now / prepare first / avoid

Return JSON only:
{
  "viability_assessment": "string (100-300 words)",
  "timing_assessment": "string (1-2 sentences on timing)",
  "risk_summary": "string (1-2 sentences on primary risk)",
  "blunt_recommendation": "string (1 sentence directive)"
}
```

---

## Prompt Engineering Notes

1. **All templates use JSON-only output mode.** The instruction "Return JSON only. No preamble." is critical — it prevents markdown fences and commentary from being included in the response.

2. **All templates embed the output schema.** The model sees the exact JSON structure it must produce, reducing parse failures.

3. **Temperature is 0.2 for all recommendation tasks.** Low temperature produces more consistent, reliable outputs. Creative variation comes from the diverse input data, not from temperature randomness.

4. **All templates receive the RecommendationContext object.** Templates access fields via Jinja2 syntax: `{{ keyword_text }}`, `{{ top_competitor_weaknesses }}`, etc.

5. **Templates are rendered by the Jinja2 engine before being sent to the LLM.** The rendered prompt is a complete, self-contained instruction with all data embedded.
