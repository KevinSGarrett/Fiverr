# EPIC 04 — Scoring Engine
# Fiverr Research System — Implementation To-Do

**Source Specs:** Wave 6 (05_scoring)
**Depends On:** Epic 03 (Analysis)
**Estimated Stories:** 15 | **Estimated Tasks:** 52

---

## Story 4.1 — Demand Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.1.1 | Create DemandScoreCalculator | TASK | `src/scoring/demand.py` — 4 components: fiverr_count (log-scaled 50%), autocomplete (20%), trends (20%), reddit (10%) |
| 4.1.2 | Implement log-scaled fiverr count | TASK | `min(100, log10(count + 1) / log10(max_count + 1) * 100)` |
| 4.1.3 | Implement autocomplete position score | TASK | Position 1=100, 2=90, ..., 10=10, absent=0 |
| 4.1.4 | Implement trends score component | TASK | RISING=80-100, STABLE=40-60, DECLINING=0-20 |
| 4.1.5 | Implement reddit signal component | TASK | Scale reddit_demand_intent_score to 0-100 |
| 4.1.6 | Create demand score tests | TASK | Test each component + composite for known inputs |

## Story 4.2 — Competition Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.2.1 | Create CompetitionScoreCalculator | TASK | `src/scoring/competition.py` — 3 components: avg_authority (60%), seller_level (25%), new_seller_ratio inverted (15%) |
| 4.2.2 | Implement avg authority component | TASK | Average authority_score across top 10 sellers, scaled to 0-100 |
| 4.2.3 | Implement seller level distribution | TASK | Weighted by Level 2/TRS/Pro presence |
| 4.2.4 | Implement new seller ratio (inverted) | TASK | Higher new seller % = lower competition |
| 4.2.5 | Create competition score tests | TASK | Test with known seller distributions |

## Story 4.3 — Opportunity Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.3.1 | Create OpportunityScoreCalculator | TASK | `src/scoring/opportunity.py` — Non-linear interaction: base + leverage_bonus for high-demand+low-competition |
| 4.3.2 | Implement quadrant detection | TASK | HIGH_DEMAND+LOW_COMP = leverage bonus. LOW_DEMAND+HIGH_COMP = penalty |
| 4.3.3 | Implement leverage bonus formula | TASK | `bonus = max(0, (demand - 60) * (100 - competition - 40) * 0.01)` |
| 4.3.4 | Create opportunity score tests | TASK | Test all 4 quadrants |

## Story 4.4 — New Seller Feasibility Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.4.1 | Create FeasibilityScoreCalculator | TASK | `src/scoring/feasibility.py` — quadrant_contribution (40%), LLM entry_rating (40%), new_seller_ratio (20%) |
| 4.4.2 | Implement quadrant feasibility mapping | TASK | Map entry difficulty quadrant to 0-100 feasibility |
| 4.4.3 | Implement LLM entry rating integration | TASK | Read entry_feasibility_rating from competitor_analysis |
| 4.4.4 | Create feasibility tests | TASK | Test with various quadrant + LLM combinations |

## Story 4.5 — Profitability Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.5.1 | Create ProfitabilityScoreCalculator | TASK | `src/scoring/profitability.py` — pricing vs platform avg (50%), upsell opportunity (30%), AOV trajectory (20%) |
| 4.5.2 | Create profitability tests | TASK | Test with known pricing data |

## Story 4.6 — Conversion Intent Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.6.1 | Create IntentScoreCalculator | TASK | `src/scoring/intent.py` — LLM intent_class (50%), reddit intent (30%), autocomplete bonus (20%) |
| 4.6.2 | Create intent score tests | TASK | Test TRANSACTIONAL=high, INFORMATIONAL=low |

## Story 4.7 — Saturation Score (Scoring Layer)

| ID | Task | Type | Description |
|---|---|---|---|
| 4.7.1 | Create SaturationScoreCalculator | TASK | `src/scoring/saturation_score.py` — Read saturation model output, normalize to 0-100, inverted in composite |
| 4.7.2 | Create saturation score tests | TASK | Test normalization and inversion |

## Story 4.8 — Gig Quality Weakness Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.8.1 | Create WeaknessScoreCalculator | TASK | `src/scoring/weakness.py` — avg_weakness (70%), red_flag_boost (20%), distribution_skew (10%) |
| 4.8.2 | Create weakness score tests | TASK | Test with known quality data |

## Story 4.9 — Trend Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.9.1 | Create TrendScoreCalculator | TASK | `src/scoring/trend.py` — 12mo baseline (40%), slope (40%), acceleration (20%) |
| 4.9.2 | Implement acceleration ratio | TASK | (last 3 months avg / first 3 months avg) as acceleration |
| 4.9.3 | Create trend score tests | TASK | Test rising, stable, declining trends |

## Story 4.10 — Confidence Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.10.1 | Create ConfidenceCalculator | TASK | `src/scoring/confidence.py` — completeness (30%), freshness (30%), diversity (20%), LLM (20%) |
| 4.10.2 | Implement completeness check | TASK | Count non-null data fields per keyword / total expected fields |
| 4.10.3 | Implement freshness check | TASK | Penalize data older than TTL per source |
| 4.10.4 | Implement source diversity | TASK | Count distinct sources that contributed data |
| 4.10.5 | Create confidence tests | TASK | Test full data=1.0, empty data=0.2, mixed data |

## Story 4.11 — Final Composite Score

| ID | Task | Type | Description |
|---|---|---|---|
| 4.11.1 | Create FinalScoreCalculator | TASK | `src/scoring/final.py` — weighted_composite × max(confidence_modifier, 0.20) |
| 4.11.2 | Implement weight profile loading | TASK | Read active profile from config, apply weights per score |
| 4.11.3 | Implement 4 named profiles | TASK | default, aggressive_new_seller, profitability_focus, trend_chaser |
| 4.11.4 | Implement tag assignment | TASK | STRONG GO 80+, CONDITIONAL GO 60-79, MONITOR 40-59, CAUTION 20-39, PASS 0-19 |
| 4.11.5 | Implement confidence-based demotion | TASK | If confidence < 0.50, demote tag by one tier |
| 4.11.6 | Create final score tests | TASK | Test composite calculation, all 4 profiles, tag thresholds, demotion |

## Story 4.12 — Opportunity Ranking (Stage 11-12)

| ID | Task | Type | Description |
|---|---|---|---|
| 4.12.1 | Create RankingEngine | TASK | `src/scoring/ranking.py` — Rank keywords by final_score per niche, write OpportunityRanking |
| 4.12.2 | Implement cross-niche ranking | TASK | Optional global ranking across all niches |
| 4.12.3 | Create ranking tests | TASK | Test correct ordering, tag assignment |

## Story 4.13 — Score Orchestration (Stage 10-12)

| ID | Task | Type | Description |
|---|---|---|---|
| 4.13.1 | Wire Stage 10 (scoring) | TASK | Calculate all 11 scores for every keyword |
| 4.13.2 | Wire Stage 11 (ranking) | TASK | Rank and assign tags |
| 4.13.3 | Wire Stage 12 (tag assignment) | TASK | Write final tags with confidence demotion |
| 4.13.4 | Implement `--mode score-only` | TASK | Run Stages 10-12 on existing data |

---

## Epic 04 Summary

| Metric | Count |
|---|---|
| Stories | 13 |
| Tasks | 52 |
| New Python Files | ~13 |
