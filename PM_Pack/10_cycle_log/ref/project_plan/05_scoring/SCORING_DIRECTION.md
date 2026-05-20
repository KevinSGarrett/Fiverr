# Scoring System Direction
# Fiverr Research System — Wave 0 Rev 3 + 9-Niche Portfolio

**Version:** 0.3 — LLM-Enhanced Inputs for All 11 Scores Across 9 Niches

---

## Scoring Philosophy

Every opportunity assessment is built from 11 quantifiable, explainable scores. No score is a black box. Every score has a formula, LLM-enhanced inputs where relevant, normalization, default weights, confidence caveats, missing-data handling, and a gpt-4o-generated explanation field. Scores are calculated per keyword, per niche, and per niche tier.

**Master Formula:**
```
Final Recommendation Score = SUM(weight_i x normalized_score_i) x Confidence_Modifier
```
Confidence_Modifier = 0.0–1.0 based on data completeness, freshness, and source diversity.

---

## Niche-Tier Scoring Behavior

| Tier | Niches | Score Depth |
|---|---|---|
| Tier 1 Full (PRD) | Slot 1 | All 11 scores, all LLM inputs, full confidence |
| Tier 1 Gated (Slots 2–4) | Support-KB, Gumloop/Lindy, MCP | Scores 1–3 only (demand, competition, opportunity) until gate passed |
| Tier 2 Standard (Slots 5–9) | Python Auto, AI Tool, AI Agent, Workflow Auto, Python Scraping | All 11 scores at standard collection depth |

---

## Score 1 — Demand Score (Default Weight: 20%)

**Purpose:** How much buyer interest exists for this keyword/niche.

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Fiverr search result count | Stage 3 | 25% |
| Fiverr autocomplete position | Stage 2 | 20% |
| Google Trends 12-month score | Stage 6 (pytrends) | 25% |
| Google search result count | Stage 6 | 10% |
| Reddit post volume | Stage 6 (Reddit API) | 10% |
| YouTube search result count | Stage 6 | 5% |
| LLM demand intent signal (Reddit text parse) | Stage 6 (gpt-4o-mini) | 5% |

**Normalization:** Min-max to 0–100 within keyword universe per niche per run.
**Missing Data Rule:** Google Trends unavailable → Confidence −0.15. Reddit unavailable → Confidence −0.05.

---

## Score 2 — Competition Score (Default Weight: 20%)

**Purpose:** How competitive the keyword is. Higher = more competition. Inverted in Opportunity Score.

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Total Fiverr search result count | Stage 3 | 20% |
| Average review count of top 10 gigs | Stage 3/4 | 25% |
| Average seller level of top 10 gigs | Stage 3/4 | 20% |
| Proportion of top 10 with 100+ reviews | Stage 3/4 | 15% |
| Pro-verified seller presence in top 10 | Stage 4 | 10% |
| Average starting price top 10 (market establishment) | Stage 4 | 5% |
| LLM competitor strength rating (cluster synthesis) | Stage 8 (gpt-4o) | 5% |

---

## Score 3 — Opportunity Score (Default Weight: 25%)

**Purpose:** Net opportunity signal — highest weight in the composite.

**Formula:**
```
Opportunity Score = normalize_0_100(
    (Demand Score x 1.2) - (Competition Score x 0.8)
)
```

---

## Score 4 — New Seller Feasibility Score (Default Weight: 15%)

**Purpose:** Can a new Fiverr seller realistically enter and win in this niche?

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Proportion of top 10 held by Level 1 or No Level sellers | Stage 3/4 | 30% |
| Review count of lowest-ranking gig on page 1 | Stage 3/4 | 25% |
| Price diversity in top results | Stage 4 | 15% |
| LLM gig quality weakness avg of top 10 | Stage 7 (gpt-4o) | 20% |
| LLM entry gap assessment | Stage 8 (gpt-4o) | 10% |

**Niche-specific context:** For Tier 2 niches (Python, AI Tool, AI Agent, Workflow, Scraping), this score is particularly important for identifying whether a new seller with a strong portfolio can enter without existing reviews.

---

## Score 5 — Profitability Score (Default Weight: 10%)

**Purpose:** Revenue potential per gig order in this niche.

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Average starting price of top 10 | Stage 4 | 30% |
| Average premium package price | Stage 4 | 30% |
| Typical delivery time (effort cost proxy) | Stage 4 | 15% |
| Gig extras presence and pricing | Stage 4 | 15% |
| LLM upsell potential assessment | Stage 13 (gpt-4o-mini) | 10% |

**Revenue model integration (from Wave 19–20):** Profitability Score uses the delayed-AOV ramp reality. Month 1–3 AOV is $95–$175. Month 6+ AOV rises to $300+. The score reflects long-term potential, not immediate launch reality. Explanation fields include the trust-stage context.

---

## Score 6 — Conversion Intent Score (Default Weight: 10%)

**Purpose:** How likely a buyer searching this keyword is ready to purchase.

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Keyword specificity (long-tail vs. broad) | Stage 2 | 25% |
| Commercial modifier presence | Stage 2 LLM (gpt-4o-mini) | 25% |
| Average review count top gigs | Stage 3/4 | 20% |
| LLM buyer intent classification | Stage 2 (gpt-4o-mini) | 20% |
| Reddit demand intent signal | Stage 6 LLM (gpt-4o-mini) | 10% |

**LLM classification:** INFORMATIONAL / CONSIDERATION / HIGH INTENT / TRANSACTIONAL

---

## Score 7 — Saturation Score (Default Weight: 5%, applied inverted)

**Purpose:** How flooded the niche is with similar, undifferentiated offerings.

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Total gig count for keyword | Stage 3 | 25% |
| Gig title duplication rate (near-identical titles in top 30) | Stage 3 LLM (gpt-4o-mini) | 25% |
| Price compression signal | Stage 4 | 20% |
| Seller portfolio overlap | Stage 3/5 | 15% |
| LLM saturation assessment | Stage 9 (gpt-4o-mini) | 15% |

---

## Score 8 — Gig Quality Weakness Score (Default Weight: 10%)

**Purpose:** How weak existing competitor gigs are. Higher = more opportunity. Most LLM-intensive score.

**Inputs — All LLM-Derived or Collection-Derived:**
| Input | Source | Model |
|---|---|---|
| Description quality score (inverted) | Stage 7 LLM | gpt-4o |
| Weakness count per gig | Stage 7 LLM | gpt-4o |
| Video absence rate | Stage 4 collection | — |
| Portfolio absence rate | Stage 4 collection | — |
| Thumbnail quality (inverted) | Stage 7 LLM | gpt-4o-mini |
| FAQ completeness (inverted) | Stage 7 LLM | gpt-4o-mini |
| Package differentiation (inverted) | Stage 7 LLM | gpt-4o |
| Niche specificity (inverted — generic = more opportunity) | Stage 7 LLM | gpt-4o |

---

## Score 9 — Trend Score (Default Weight: 5%)

**Purpose:** Is interest growing, stable, or declining?

**Inputs:**
| Input | Source | Weight Within Score |
|---|---|---|
| Google Trends 12-month slope | Stage 6 (pytrends) | 40% |
| Google Trends 3-month vs. 12-month (acceleration) | Stage 6 | 25% |
| Reddit activity trend | Stage 6 | 15% |
| LLM trend classification | Stage 14 (gpt-4o-mini) | 20% |

**LLM classification:** STRONGLY RISING / RISING / STABLE / DECLINING / STRONGLY DECLINING

---

## Score 10 — Final Recommendation Score (Master Composite)

**Formula:**
```python
final_score = (
    demand_score          * weights.demand            # default 0.20
  + (100 - competition)   * weights.competition_inv   # default 0.20
  + opportunity_score     * weights.opportunity        # default 0.25
  + feasibility_score     * weights.feasibility        # default 0.15
  + profitability_score   * weights.profitability      # default 0.10
  + intent_score          * weights.intent             # default 0.10
  + (100 - saturation)    * weights.saturation_inv    # default 0.05
  + weakness_score        * weights.weakness           # default 0.10
  + trend_score           * weights.trend              # default 0.05
) * confidence_modifier
```

**Thresholds:**
| Range | Tag | Meaning |
|---|---|---|
| 80–100 | STRONG GO | High priority — pursue immediately |
| 60–79 | CONDITIONAL GO | Worth pursuing with strong execution |
| 40–59 | MONITOR | Possible but not priority |
| 20–39 | CAUTION | High competition or low demand |
| 0–19 | PASS | Not recommended |

**Named Scoring Profiles:**
```yaml
scoring:
  active_profile: default
  profiles:
    default:
      demand: 0.20
      competition_inv: 0.20
      opportunity: 0.25
      feasibility: 0.15
      profitability: 0.10
      intent: 0.10
      saturation_inv: 0.05
      weakness: 0.10
      trend: 0.05
    aggressive_new_seller:
      feasibility: 0.25
      weakness: 0.20
      opportunity: 0.20
      demand: 0.15
      competition_inv: 0.10
      profitability: 0.05
      intent: 0.05
      saturation_inv: 0.00
      trend: 0.00
    profitability_focus:
      profitability: 0.25
      intent: 0.20
      opportunity: 0.20
      demand: 0.15
      competition_inv: 0.10
      feasibility: 0.05
      weakness: 0.05
      saturation_inv: 0.00
      trend: 0.00
    trend_chaser:
      trend: 0.25
      demand: 0.25
      opportunity: 0.20
      competition_inv: 0.15
      feasibility: 0.10
      profitability: 0.05
      intent: 0.00
      weakness: 0.00
      saturation_inv: 0.00
```

---

## Score 11 — Confidence Score (Modifier: 0.0–1.0)

**Formula:**
```python
confidence_modifier = (
    data_completeness_ratio  * 0.50
  + data_freshness_score     * 0.30
  + source_diversity_score   * 0.20
) * llm_analysis_completion_ratio
# Clamped 0.0–1.0
```

**Confidence Deductions Reference:**
| Missing Data | Deduction |
|---|---|
| Google Trends unavailable | −0.15 |
| No gig detail collected (search only) | −0.20 |
| Seller profiles not collected | −0.10 |
| Reddit signals unavailable | −0.05 |
| LLM gig quality incomplete | −0.08 per gig (max −0.20) |
| LLM competitor synthesis failed | −0.10 |
| Data older than 2x TTL | −0.15 |
| Niche in keyword_only or feasibility mode | −0.25 (partial score only) |

---

## Explanation Field Standard (All Scores)

Every score record in keyword_scores must include:

| Field | Type | Description |
|---|---|---|
| score_value | float 0–100 | The computed score |
| score_components | JSON | Breakdown of each input's contribution |
| confidence_modifier | float 0–1 | Applied confidence modifier |
| confidence_breakdown | JSON | Per-component deductions |
| confidence_reason | string | Human-readable confidence explanation |
| explanation_text | string | gpt-4o-generated explanation (Stage 14) |
| red_flags | JSON array | Warning signals |
| missing_data_warnings | JSON array | Null/missing fields |
| source_evidence | JSON array | Data sources that contributed |
| llm_inputs_used | JSON | Which LLM tasks contributed |
| niche_tier | string | tier1_full / tier1_gated / tier2_standard |
| scored_at | timestamp | When score was calculated |
| data_as_of | timestamp | Oldest data record feeding this score |
