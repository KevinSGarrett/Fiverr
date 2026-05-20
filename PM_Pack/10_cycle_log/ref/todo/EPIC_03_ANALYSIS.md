# EPIC 03 — Analysis Engine
# Fiverr Research System — Implementation To-Do

**Epic Owner:** ML/Data Engineer
**Source Specs:** Wave 5 (06_analysis — first 6 files)
**Depends On:** Epic 02 (Collection — data must exist)
**Priority:** P0
**Estimated Stories:** 14 | **Estimated Tasks:** 58

---

## Story 3.1 — Keyword Clustering (Stage 9)

| ID | Task | Type | Description |
|---|---|---|---|
| 3.1.1 | Create KeywordClusteringWorkflow | TASK | `src/analysis/clustering.py` — Embed keywords, KMeans cluster, label clusters via LLM |
| 3.1.2 | Implement embedding generation | TASK | OpenAI text-embedding-3-small for all keyword texts per niche. L2 normalize. Store in keywords.embedding_vector (JSON) |
| 3.1.3 | Implement KMeans clustering | TASK | k = ceil(sqrt(n/2)), capped 2-20. Per-niche only. scikit-learn KMeans |
| 3.1.4 | Implement silhouette score check | TASK | Compute silhouette score, warn if < 0.3, log in cluster_analysis |
| 3.1.5 | Implement cluster labeling (LLM) | TASK | gpt-4o-mini: given keywords in cluster, generate 3-5 word label |
| 3.1.6 | Implement re-cluster detection | TASK | Re-cluster when > 15% new keywords since last cluster run |
| 3.1.7 | Store ClusterAnalysis entries | TASK | cluster_id, cluster_label, keyword_count, centroid, silhouette |
| 3.1.8 | Update Keyword.cluster_id | TASK | Assign cluster_id to each keyword |
| 3.1.9 | Create clustering tests | TASK | Test K selection, silhouette check, label generation, re-cluster trigger |

---

## Story 3.2 — Gig Quality Analysis (Stage 7)

| ID | Task | Type | Description |
|---|---|---|---|
| 3.2.1 | Create GigQualityWorkflow | TASK | `src/analysis/gig_quality.py` — LLM analyzes each gig against 15-criteria rubric |
| 3.2.2 | Create gig quality LLM prompt | TASK | Jinja2 template: gig title, description, packages, FAQ, extras → 15 criteria scores |
| 3.2.3 | Implement 15-criteria scoring | TASK | Each criterion: 0-10. Source: GIG_QUALITY_RUBRIC.md |
| 3.2.4 | Implement weakness detection | TASK | Extract weakness types: NO_PROOF, GENERIC_DESCRIPTION, OVERPRICED, SLOW_DELIVERY, etc. |
| 3.2.5 | Implement overall_weakness_score | TASK | Inverted composite: higher = more exploitable weaknesses |
| 3.2.6 | Implement red_flag_boost | TASK | 20% boost for HIGHLY_EXPLOITABLE gigs (weakness_score ≥ 8.0) |
| 3.2.7 | Store GigQualityScore entries | TASK | Per-gig scores with criteria breakdown and weakness list |
| 3.2.8 | Create gig quality tests | TASK | Test rubric scoring, weakness detection, overall score calculation |

---

## Story 3.3 — Competitor Profiling (Stage 8)

| ID | Task | Type | Description |
|---|---|---|---|
| 3.3.1 | Create CompetitorProfilingWorkflow | TASK | `src/analysis/competitor_profiling.py` — Per-cluster competitor analysis |
| 3.3.2 | Implement competitor_strength score | TASK | 0-10, 9 components: reviews, level, response rate, portfolio, proof elements, etc. |
| 3.3.3 | Implement weakness aggregation | TASK | Aggregate weaknesses from GigQualityScores per cluster |
| 3.3.4 | Implement cluster synthesis (LLM) | TASK | gpt-4o: 4-section output (who_dominates, why_they_win, the_gap, entry_verdict) + feasibility 0-10 |
| 3.3.5 | Implement positioning gap detection | TASK | Identify gaps in competitor positioning (price, quality, specialization) |
| 3.3.6 | Implement dominant seller identification | TASK | Top 3 sellers by authority_score per cluster |
| 3.3.7 | Store CompetitorAnalysis entries | TASK | synthesis_narrative, entry_feasibility_rating, positioning_gaps |
| 3.3.8 | Create competitor profiling tests | TASK | Test strength scoring, weakness aggregation, synthesis prompt |

---

## Story 3.4 — Seller Strength Model

| ID | Task | Type | Description |
|---|---|---|---|
| 3.4.1 | Create SellerStrengthAnalyzer | TASK | `src/analysis/seller_strength.py` — Compute authority_score per seller |
| 3.4.2 | Implement authority_score formula | TASK | 9 weighted components: review_count, rating, response_time, response_rate, level, portfolio, bio_quality, skill_tests, member_tenure |
| 3.4.3 | Implement new seller detection | TASK | Reviews < 5 OR member_since < 6 months → is_new_seller = True |
| 3.4.4 | Implement 4-quadrant classification | TASK | HIGH_AUTH+LOW_COUNT, HIGH_AUTH+HIGH_COUNT, LOW_AUTH+LOW_COUNT, LOW_AUTH+HIGH_COUNT |
| 3.4.5 | Store SellerScore entries | TASK | authority_score, quadrant, weakness list, is_new_seller |
| 3.4.6 | Create seller strength tests | TASK | Test formula, new seller detection, quadrant assignment |

---

## Story 3.5 — Saturation Model

| ID | Task | Type | Description |
|---|---|---|---|
| 3.5.1 | Create SaturationAnalyzer | TASK | `src/analysis/saturation.py` — 5-component saturation formula |
| 3.5.2 | Implement title deduplication (Jaccard) | TASK | Jaccard similarity on gig titles, threshold 0.65 → flag as near-duplicate |
| 3.5.3 | Implement 5 saturation components | TASK | gig_density, title_uniqueness, price_spread, seller_diversity, new_seller_ratio |
| 3.5.4 | Implement saturation_score (0-100) | TASK | Weighted composite of 5 components. Inverted in final score |
| 3.5.5 | Create saturation tests | TASK | Test Jaccard, each component, composite calculation |

---

## Story 3.6 — Review Analysis

| ID | Task | Type | Description |
|---|---|---|---|
| 3.6.1 | Create ReviewAnalyzer | TASK | `src/analysis/review_analysis.py` — Detect red flag patterns in reviews |
| 3.6.2 | Implement 7 red flag types | TASK | Pattern matching: LATE_DELIVERY, COMMUNICATION_ISSUE, SCOPE_MISMATCH, QUALITY_BELOW_EXPECTED, REFUND_REQUEST, REVISION_EXCESSIVE, UNRESPONSIVE |
| 3.6.3 | Implement review insight extraction | TASK | Top buyer complaints, top buyer praise, competitor failure modes |
| 3.6.4 | Store review insights | TASK | Per-niche review intelligence stored for recommendation context |
| 3.6.5 | Create review analysis tests | TASK | Test each red flag pattern, insight extraction |

---

## Story 3.7 — Intent Classification (LLM)

| ID | Task | Type | Description |
|---|---|---|---|
| 3.7.1 | Create IntentClassifier | TASK | `src/analysis/intent_classifier.py` — LLM classifies keyword intent |
| 3.7.2 | Implement intent LLM prompt | TASK | gpt-4o-mini: classify as TRANSACTIONAL, HIGH_INTENT, CONSIDERATION, INFORMATIONAL |
| 3.7.3 | Update Keyword.intent_class | TASK | Set intent_class on all keywords |
| 3.7.4 | Create intent classification tests | TASK | Test known keywords against expected intent classes |

---

## Story 3.8 — Stage Wiring (Stages 7-9)

| ID | Task | Type | Description |
|---|---|---|---|
| 3.8.1 | Wire Stage 7 (Gig Quality) | TASK | Orchestrator calls GigQualityWorkflow after collection |
| 3.8.2 | Wire Stage 8 (Competitor Analysis) | TASK | Orchestrator calls CompetitorProfilingWorkflow |
| 3.8.3 | Wire Stage 9 (Clustering) | TASK | Orchestrator calls KeywordClusteringWorkflow |
| 3.8.4 | Wire intent classification | TASK | Runs during Stage 7 or as sub-stage |

---

## Epic 03 Summary

| Metric | Count |
|---|---|
| Stories | 8 |
| Tasks | 58 |
| New Python Files | ~10 |
| New Jinja2 Templates | ~4 |
