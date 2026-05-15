# Gig Quality Rubric
# Fiverr Research System — Wave 5

**Document Status:** Complete
**Wave:** 5 — Analysis and Competitor Model
**Purpose:** 15+ quality criteria with detection methods, scoring, LLM prompt direction, composite weakness score formula, overall_weakness_score calculation, and exploitability threshold.

---

## Design Philosophy

The Gig Quality Rubric answers one question: **"How beatable is this gig?"**

A score of 10 = maximally weak competitor gig (high opportunity to beat it).
A score of 0 = near-perfect competitor gig (very hard to beat).

This rubric is the primary input to the **Gig Quality Weakness Score** (Score 8), which carries 10% weight in the Final Recommendation Score. It is entirely LLM-driven for qualitative criteria and rule-based for structural signals.

---

## The 15 Quality Criteria

---

### Criterion 1 — Keyword Targeting in Title
**Measures:** Whether the gig title contains the exact or close variant of the keyword a buyer would search.
**Score:** 0–10 (10 = title matches search intent perfectly; 0 = title is generic with no keyword)
**Detection:** LLM (gpt-4o-mini) + rule-based keyword overlap check
**LLM prompt direction:** "Does the title contain the search keyword or a close variant? Does it tell the buyer exactly what they'll receive?"
**HIGH score looks like:** "I will write a developer-ready AI SaaS MVP PRD and technical roadmap"
**LOW score looks like:** "I will help you with your software project"
**Weight in composite:** 8%

---

### Criterion 2 — Title Clarity and Specificity
**Measures:** How specifically the title describes the deliverable — what exactly the buyer receives.
**Score:** 0–10
**Detection:** LLM (gpt-4o-mini)
**LLM prompt direction:** "Is the deliverable named precisely in the title? Would a buyer know exactly what they're buying?"
**HIGH:** "I will create a 15-page AI-ready support knowledge base audit and remediation plan"
**LOW:** "I will write content for your website"
**Weight in composite:** 7%

---

### Criterion 3 — Description Specificity
**Measures:** How specific the description is about what is delivered, for whom, and in what format.
**Score:** 0–10
**Detection:** LLM (gpt-4o)
**LLM prompt direction:** "Count specific deliverable items mentioned. Is the scope clearly bounded? Does the buyer know exactly what they will receive?"
**HIGH:** Lists exact deliverables with page counts, formats, tools used, and named sections
**LOW:** "I will help you build your product and make it successful"
**Weight in composite:** 12%

---

### Criterion 4 — Benefit Language Strength
**Measures:** Whether the description focuses on buyer outcomes ("you will get X") vs. seller process ("I do X").
**Score:** 0–10
**Detection:** LLM (gpt-4o)
**LLM prompt direction:** "Does the description focus on what the buyer gains, or on what the seller does? Count benefit-oriented sentences vs. process-oriented sentences."
**HIGH:** "You'll have a complete PRD your development team can use immediately"
**LOW:** "I use agile methodology and have 5 years of experience"
**Weight in composite:** 10%

---

### Criterion 5 — Proof and Credibility Elements
**Measures:** Whether the description includes social proof, specific credentials, numbers, or past results.
**Score:** 0–10
**Detection:** LLM (gpt-4o)
**LLM prompt direction:** "Does the description include: specific past results (numbers, metrics), client types, credentials/certifications, tools expertise, or case study references?"
**HIGH:** "I've written PRDs for 40+ SaaS startups funded by Y Combinator and a16z"
**LOW:** No mention of past work, no numbers, no client references
**Weight in composite:** 12%

---

### Criterion 6 — CTA Strength
**Measures:** Whether the description ends with a clear call to action directing the buyer's next step.
**Score:** 0–10
**Detection:** LLM (gpt-4o-mini)
**LLM prompt direction:** "Does the last paragraph include a direct call to action? Does it tell the buyer what to do next?"
**HIGH:** "Drop me a message with your idea — I'll confirm fit and turnaround time within 2 hours"
**LOW:** Description ends abruptly with no buyer direction
**Weight in composite:** 5%

---

### Criterion 7 — Package Differentiation
**Measures:** How clearly the Basic/Standard/Premium packages differ from each other.
**Score:** 0–10
**Detection:** LLM (gpt-4o)
**LLM prompt direction:** "Are the three packages clearly differentiated in scope? Could a buyer easily choose the right tier? Or do they overlap and confuse?"
**HIGH:** Basic=audit only, Standard=audit+recommendations, Premium=full PRD+roadmap (clear escalation)
**LOW:** All three packages have similar vague descriptions with only the page count differing
**Weight in composite:** 8%

---

### Criterion 8 — FAQ Completeness and Relevance
**Measures:** Whether the FAQ addresses real buyer concerns for this niche, not generic questions.
**Score:** 0–10
**Detection:** LLM (gpt-4o-mini)
**LLM prompt direction:** "Does the FAQ address likely buyer concerns for this specific niche? Are the questions specific to the service? Or are they generic/placeholder?"
**HIGH:** FAQ covers: "What do I need to provide?", "Do you handle technical documentation?", "What's not included?", "How do revisions work?", "Can I use this with my developers?"
**LOW:** FAQ has 1–2 generic questions like "How long will it take?"
**Weight in composite:** 6%

---

### Criterion 9 — Thumbnail Quality
**Measures:** Visual quality and professionalism of the gig thumbnail.
**Score:** 0 (LOW_QUALITY) to 10 (PROFESSIONAL_PHOTO or GRAPHIC_DESIGN with clear value prop)
**Detection:** LLM (gpt-4o-mini) classifies thumbnail_class
**Score mapping:**
```
PROFESSIONAL_PHOTO  → 9.0
GRAPHIC_DESIGN      → 7.0  (depends on quality — LLM adjusts)
STOCK_IMAGE         → 4.0
TEXT_HEAVY          → 2.0
LOW_QUALITY         → 0.5
```
**Weight in composite:** 7%

---

### Criterion 10 — Video Presence
**Measures:** Whether a gig video is present.
**Score:** 0 or 8 (binary — no partial credit)
**Detection:** Rule-based — gigs.video_present
**Rationale:** Gig videos increase conversion significantly; absence is a clear weakness
**Weight in composite:** 6%

---

### Criterion 11 — Portfolio / Sample Presence
**Measures:** Whether portfolio work samples are present.
**Score:** 0–10 based on count
```
0 samples    → 0.0
1–2 samples  → 3.0
3–5 samples  → 6.5
6–10 samples → 8.5
10+ samples  → 10.0
```
**Detection:** Rule-based — gigs.portfolio_count
**Weight in composite:** 8%

---

### Criterion 12 — Niche Specificity
**Measures:** Whether the gig is positioned as a niche specialist vs. a generalist offering.
**Score:** 0–10
**Detection:** LLM (gpt-4o)
**LLM prompt direction:** "Is this gig written for a specific type of buyer in a specific context, or could it apply to anyone? Does the seller present as a specialist in this exact service?"
**HIGH:** "Built specifically for early-stage SaaS founders preparing for technical co-founder or first engineering hire"
**LOW:** "I can help any business with their documentation needs"
**Weight in composite:** 8%

---

### Criterion 13 — Pricing Clarity
**Measures:** Whether the pricing and package inclusions are clearly communicated without ambiguity.
**Score:** 0–10
**Detection:** LLM (gpt-4o-mini)
**LLM prompt direction:** "Is it clear what is and isn't included at each price tier? Are there hidden surprises a buyer might encounter? Is the value-for-price obvious?"
**HIGH:** Each package has a named deliverable with exact scope, page counts, and what is NOT included
**LOW:** "Price varies based on complexity" or vague package descriptions
**Weight in composite:** 5%

---

### Criterion 14 — Exclusions and Boundary Clarity
**Measures:** Whether the gig clearly states what is NOT included, reducing scope creep risk.
**Score:** 0–10
**Detection:** LLM (gpt-4o-mini)
**LLM prompt direction:** "Does the gig clearly state what is excluded? Are there boundary conditions that protect both the buyer and seller from scope creep?"
**HIGH:** "Does not include: actual development, UI design, market research, or investor materials"
**LOW:** No exclusions mentioned — buyer could expect anything
**Weight in composite:** 4%

---

### Criterion 15 — Delivery Time Competitiveness
**Measures:** Whether the Basic package delivery time is competitive vs. the niche median.
**Score:** 0–10
**Detection:** Rule-based — comparison against niche_median_delivery_days
```
<= 0.75× median → 10.0  (significantly faster than niche)
0.75–1.0× median → 7.0  (at or slightly above median)
1.0–1.5× median  → 4.0  (notably slower)
> 1.5× median    → 1.0  (much slower — significant disadvantage)
```
**Weight in composite:** 4%

---

## Composite Weakness Score Formula

The `overall_weakness_score` (0–10, stored in `gig_quality_scores`) is the weighted average of all 15 criteria, **inverted** — because we want a HIGH score to mean "this competitor is WEAK" (high opportunity for us).

```python
CRITERION_WEIGHTS = {
    "keyword_targeting":      0.08,
    "title_clarity":          0.07,
    "description_specificity":0.12,
    "benefit_language":       0.10,
    "proof_elements":         0.12,
    "cta_strength":           0.05,
    "package_differentiation":0.08,
    "faq_completeness":       0.06,
    "thumbnail_quality":      0.07,
    "video_presence":         0.06,
    "portfolio_presence":     0.08,
    "niche_specificity":      0.08,
    "pricing_clarity":        0.05,
    "exclusions_clarity":     0.04,
    "delivery_competitiveness":0.04,
}
# Sum = 1.00

def calculate_overall_weakness_score(criteria_scores: dict) -> float:
    """
    Calculates the overall_weakness_score for a gig.

    The score represents how WEAK this competitor gig is (0–10).
    Higher score = more exploitable weakness = higher opportunity for new entrant.

    Each criterion score is 0–10 where 10 = STRONG gig (no weakness).
    We invert each score: weakness_contribution = (10 - criterion_score)
    Then take the weighted average.
    """
    if not criteria_scores:
        return 5.0  # Default to neutral when data is missing

    total = 0.0
    weight_used = 0.0

    for criterion, weight in CRITERION_WEIGHTS.items():
        score = criteria_scores.get(criterion)
        if score is not None:
            weakness_contribution = 10.0 - score  # Invert: strong gig → low weakness
            total += weakness_contribution * weight
            weight_used += weight

    if weight_used < 0.5:
        return 5.0  # Not enough data — return neutral

    # Normalize for any missing criteria
    return round(total / weight_used, 2)
```

---

## Exploitability Threshold

| overall_weakness_score | Label | Meaning |
|---|---|---|
| 8.0–10.0 | HIGHLY EXPLOITABLE | This competitor's gig is very weak — a well-crafted new gig will beat it easily |
| 6.0–7.9 | EXPLOITABLE | Clear weaknesses exist — a new gig targeting these gaps has a good chance |
| 4.0–5.9 | MODERATE | Some weaknesses but also strengths — entry is possible with good execution |
| 2.0–3.9 | STRONG GIG | This competitor has a solid gig — hard to displace without exceptional proof |
| 0.0–1.9 | NEAR-PERFECT | Almost no exploitable weaknesses — don't directly compete, find a sub-niche |

The **Gig Quality Weakness Score** (Score 8) at the keyword level is the **average** `overall_weakness_score` across the top N gigs for that keyword. Higher average = more beatable competitive landscape.
