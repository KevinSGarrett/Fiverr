# Gig Suggestion Templates
# Fiverr Research System — Wave 7

**Document Status:** Complete
**Wave:** 7 — Recommendation Engine
**Purpose:** Complete design for all 11 LLM recommendation tasks — input spec, output schema, model selection, cache strategy, retry behavior, and quality standards per task.

---

## Task Index

| # | Task | Model | Est. Cost | Cache Key Inputs |
|---|---|---|---|---|
| 1 | Gig Titles (5 variants) | gpt-4o | $0.012 | keyword_text + niche_id + competitor_weaknesses_hash |
| 2 | Tag Sets (5 sets) | gpt-4o-mini | $0.001 | keyword_text + niche_id |
| 3 | Package Structure | gpt-4o | $0.018 | niche_pricing + competitor_packages_hash |
| 4 | Description Outline | gpt-4o | $0.024 | keyword_text + niche_id + exclusions_hash |
| 5 | FAQ Entries (5–7) | gpt-4o-mini | $0.001 | keyword_text + niche_id |
| 6 | Differentiation Angle | gpt-4o | $0.020 | competitor_weaknesses_hash + review_complaints |
| 7 | Buyer Persona | gpt-4o-mini | $0.001 | keyword_text + niche_id + demand_signals_hash |
| 8 | Thumbnail Direction | gpt-4o-mini | $0.001 | keyword_text + niche_id |
| 9 | Upsell Structure | gpt-4o-mini | $0.001 | niche_pricing + competitor_extras_hash |
| 10 | Red Flags | gpt-4o | $0.015 | all_scores_hash + competitor_data_hash |
| 11 | Niche Viability Assessment | gpt-4o | $0.018 | all_scores + synthesis_narrative + tag |

All tasks use structured JSON output mode + Pydantic validation. On validation failure, one self-correction retry is attempted (see RETRY_AND_CHECKPOINT.md).

---

## Task 1 — Gig Titles (5 Variants)

**Model:** gpt-4o
**Input:** keyword_text, niche_name, top 3 competitor gig titles, top 3 competitor weaknesses
**Output:** 5 unique title variants optimized for Fiverr search and buyer conversion

**Quality Standards:**
- Each title must start with "I will" (Fiverr convention)
- Each title must contain the primary keyword or a close semantic variant
- Titles must be 60–80 characters (Fiverr truncates beyond ~80)
- Each of the 5 must use a different positioning angle (specialist, outcome, speed, proof, scope)
- No generic claims ("best", "professional", "amazing") without specifics

**Output Schema:**
```json
{
  "titles": [
    {
      "title": "I will write a developer-ready AI SaaS MVP PRD with technical roadmap",
      "positioning_angle": "outcome",
      "character_count": 72,
      "primary_keyword_present": true
    }
  ]
}
```

**Retry:** 1 retry with self-correction if titles are too short, too long, or missing "I will" prefix.

---

## Task 2 — Tag Sets (5 Sets)

**Model:** gpt-4o-mini
**Input:** keyword_text, niche_name, competitor tags from top 5 gigs
**Output:** 5 tag set options, each with exactly 5 tags (Fiverr's per-gig limit)

**Quality Standards:**
- Tags must be 2–25 characters each (Fiverr limit)
- Tags must include the primary keyword and close variants
- Each set should take a different angle (service type, deliverable type, buyer type, tool/technology, industry)
- No duplicate tags within a set

**Output Schema:**
```json
{
  "tag_sets": [
    ["AI SaaS PRD", "MVP roadmap", "product requirements", "technical spec", "SaaS planning"],
    ["PRD writing", "AI product", "developer-ready PRD", "startup roadmap", "MVP specification"]
  ]
}
```

---

## Task 3 — Package Structure

**Model:** gpt-4o
**Input:** niche pricing from config (starter_price_basic/standard/premium), competitor packages from top 5 gigs, hard_exclusions from config
**Output:** Complete Basic/Standard/Premium package structure

**Quality Standards:**
- Prices must match or be within ±15% of niche config pricing tiers
- Each tier must have a distinct, named deliverable scope (not just "more pages")
- Deliverables must be specific and countable ("5-page audit report" not "analysis")
- Delivery days must be realistic (not 1 day for a 30-page PRD)
- Revisions should increase with tier (1/2/3 typical pattern)
- Hard_exclusions from niche config must NOT appear as deliverables

**Output Schema:**
```json
{
  "basic": {
    "name": "Idea-to-Scope Audit",
    "price": 95,
    "deliverables": ["3-page scope audit", "Feature priority matrix", "Technical feasibility assessment"],
    "delivery_days": 3,
    "revisions": 1
  },
  "standard": {
    "name": "Complete MVP PRD",
    "price": 225,
    "deliverables": ["10-page PRD", "User stories", "Technical architecture overview", "Feature priority matrix"],
    "delivery_days": 5,
    "revisions": 2
  },
  "premium": {
    "name": "PRD + Technical Roadmap Bundle",
    "price": 395,
    "deliverables": ["15-page PRD", "Detailed technical roadmap", "User stories with acceptance criteria", "Architecture diagrams", "Implementation timeline"],
    "delivery_days": 7,
    "revisions": 3
  }
}
```

---

## Task 4 — Description Outline

**Model:** gpt-4o
**Input:** keyword_text, niche_name, hard_exclusions, top competitor weaknesses, buyer complaints, package structure (from Task 3)
**Output:** Structured gig description with section headings, copy direction, and proof element placeholders

**Quality Standards:**
- 5–7 sections with clear headings
- First section must be a benefit-led hook (not "I am a professional...")
- Must include at least one proof element section ("Why Choose Me" or "What You Get")
- Must include explicit exclusions section derived from config.hard_exclusions
- Must end with a CTA section
- Copy direction per section tells the user what to write in their own voice

**Output Schema:**
```json
{
  "sections": [
    {
      "heading": "Get a Developer-Ready PRD in 5 Days",
      "copy_direction": "Lead with the specific deliverable and its primary benefit to the buyer. Name the target audience (SaaS founders, product managers). Include one credential sentence.",
      "proof_elements": ["Client count", "Industry focus", "Deliverable format"],
      "estimated_words": 80
    },
    {
      "heading": "What's Included",
      "copy_direction": "Bullet list of specific deliverables matching the package tiers. Each bullet should name the deliverable and its purpose.",
      "proof_elements": [],
      "estimated_words": 100
    },
    {
      "heading": "What's NOT Included",
      "copy_direction": "List exclusions from hard_exclusions config. Frame positively: 'This service focuses on X. It does not include Y.'",
      "proof_elements": [],
      "estimated_words": 60
    }
  ]
}
```

---

## Task 5 — FAQ Entries (5–7)

**Model:** gpt-4o-mini
**Input:** keyword_text, niche_name, hard_exclusions, top buyer complaints from review analysis
**Output:** 5–7 FAQ entries addressing real buyer concerns

**Quality Standards:**
- Questions must be phrased as a buyer would ask them (first person: "Can you...", "Do you...", "What if...")
- Answers must be specific to this niche (not generic)
- At least 2 FAQs should address known buyer complaints from review analysis
- At least 1 FAQ should set scope boundaries (preventing scope creep)
- Answers should be 2–4 sentences each

**Output Schema:**
```json
{
  "faq_entries": [
    {
      "question": "What do I need to provide before you start?",
      "answer": "I'll send you a structured intake questionnaire covering your product idea, target users, and technical constraints. This typically takes 15–20 minutes to complete. The more detail you provide, the stronger the PRD will be.",
      "addresses_complaint": null
    },
    {
      "question": "Can you also build the product or write the code?",
      "answer": "This service focuses exclusively on the PRD and roadmap documentation. I don't provide development services, UI/UX design, or ongoing technical consulting. If you need development, I can recommend how to structure your developer brief.",
      "addresses_complaint": "SCOPE_CREEP"
    }
  ]
}
```

---

## Task 6 — Differentiation Angle

**Model:** gpt-4o
**Input:** top_competitor_weaknesses (from Wave 5), buyer complaints (from review analysis), positioning_gaps (from cluster synthesis)
**Output:** A specific, evidence-based positioning statement + 3–5 tactical differentiators

**Quality Standards:**
- Must reference specific competitor weaknesses by name (not generic advice)
- Must be actionable (not "be better" — exactly what to do differently)
- Must connect each weakness to a buyer pain point
- 100–200 words for the positioning statement
- Each differentiator must be a concrete action the seller takes in their gig

**Output Schema:**
```json
{
  "positioning_statement": "Top 10 gigs in this keyword have generic descriptions with no proof elements and vague deliverable scoping...",
  "differentiators": [
    {
      "action": "Include a 3-bullet proof block: X clients delivered, Y years in SaaS, Z deliverables shipped",
      "competitor_weakness_exploited": "no_proof_elements",
      "buyer_pain_addressed": "Buyers can't evaluate quality before purchasing"
    }
  ],
  "one_sentence_pitch": "Position as the only PRD writer who delivers a developer-ready document with architecture diagrams and acceptance criteria — not a generic strategy deck."
}
```

**Skip condition:** Skipped if `top_competitor_weaknesses` is empty (no competitor analysis available). Stores null.

---

## Task 7 — Buyer Persona

**Model:** gpt-4o-mini
**Input:** keyword_text, niche_name, demand signals (Reddit intent phrases, total_result_count), trends_slope
**Output:** Detailed buyer persona

**Output Schema:**
```json
{
  "name": "Alex",
  "role": "Non-technical SaaS founder",
  "company_stage": "Pre-seed / bootstrapped",
  "pain_points": ["Needs to communicate product vision to developers", "Can't write technical specs", "Doesn't know what developers need to start building"],
  "budget_range": "$100–$400 for a single PRD",
  "decision_trigger": "Just hired first developer or technical co-founder",
  "where_they_search": "Fiverr search, Reddit r/startups, ProductHunt discussions",
  "what_makes_them_buy": "Clear deliverable description + proof the seller understands their industry"
}
```

---

## Task 8 — Thumbnail Direction

**Model:** gpt-4o-mini
**Input:** keyword_text, niche_name, competitor thumbnail_class distribution
**Output:** Thumbnail creative direction (text — not an actual image)

**Output Schema:**
```json
{
  "concept": "Clean professional mockup showing a PRD document with visible section headers",
  "style": "Minimal, dark background with white/blue accent colors",
  "elements_to_include": ["Visible document pages", "Your logo/brand mark", "Keyword text overlay: 'AI SaaS MVP PRD'"],
  "elements_to_avoid": ["Stock photos of people", "Cluttered text-heavy designs", "Generic tech imagery"],
  "differentiation_note": "78% of competitors use text-heavy thumbnails — a clean image-forward approach stands out"
}
```

---

## Task 9 — Upsell Structure

**Model:** gpt-4o-mini
**Input:** niche pricing, competitor gig_extras data
**Output:** 2–4 gig extras (upsells) with pricing

**Output Schema:**
```json
{
  "extras": [
    {"name": "Express 48-hour delivery", "price": 50, "description": "Expedited delivery within 2 business days"},
    {"name": "Additional revision round", "price": 25, "description": "One extra round of revisions"},
    {"name": "Technical architecture diagram", "price": 75, "description": "Visual architecture diagram (draw.io or Mermaid format)"},
    {"name": "Developer handoff call", "price": 100, "description": "30-minute video call to walk through the PRD with your development team"}
  ]
}
```

---

## Task 10 — Red Flags

**Model:** gpt-4o
**Input:** All 11 scores, competitor data, trend data, confidence modifier
**Output:** Risk assessment with specific, actionable warnings

**Output Schema:**
```json
{
  "red_flags": [
    {
      "flag_type": "high_competition_no_weak_spots",
      "description": "Top 3 sellers are Level 2+ with 500+ reviews each and strong descriptions — displacing them requires exceptional proof assets",
      "severity": "HIGH",
      "mitigation": "Build 3+ portfolio samples before publishing. Consider starting with a related but less competitive keyword."
    }
  ],
  "overall_risk_level": "MEDIUM",
  "proceed_recommendation": "Proceed with caution — build proof assets first, then publish"
}
```

---

## Task 11 — Niche Viability Assessment

**Model:** gpt-4o
**Input:** All scores + synthesis narrative + tag + demand signals + trend + pricing + red flags
**Output:** 100–300 word strategic assessment paragraph

**Quality Standards:**
- Must reference actual score values and what they mean (not just "good opportunity")
- Must address timing (is now the right time based on trend?)
- Must address risk (what could go wrong)
- Must give a blunt recommendation (enter now / prepare first / avoid)
- Tone adjusted by tag (STRONG GO = actionable framing, CONDITIONAL GO = cautious framing)

**Output Schema:**
```json
{
  "viability_assessment": "This keyword scores 82 (STRONG GO) driven by strong demand (75) and exploitable competitor weaknesses (69). The competitive field includes 5 Level 2+ sellers, but 4 of the top 10 gigs have generic descriptions with no proof elements — a clear differentiation window...",
  "timing_assessment": "Google Trends shows RISING demand with 22% acceleration over the past 3 months. Entry now captures the growth curve before additional competitors notice.",
  "risk_summary": "Primary risk: strong competition from established sellers with review moats. Mitigation: launch with 3+ proof assets and competitive pricing at the Basic tier.",
  "blunt_recommendation": "Enter now with proof assets ready. Don't publish without portfolio samples and a video."
}
```

---

## Cache Strategy (All Tasks)

All 11 tasks use the LLM cache. Cache key = SHA-256 of (model + temperature + rendered prompt text). Cache is invalidated when:
- Source data contributing to the prompt changes (via source_data_hash in llm_cache table)
- Cache TTL expires (default 72 hours)

Estimated cache hit rate on re-runs with unchanged data: 60–80%.

---

## Retry Behavior (All Tasks)

All tasks follow the LLM retry policy from RETRY_AND_CHECKPOINT.md:
1. First attempt: standard structured output call
2. On ValidationError: one self-correction retry with error appended to prompt
3. On second failure: store null for that field, set `generation_complete = False`
4. Task failure does NOT block other tasks (asyncio.gather continues)
