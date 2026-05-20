# DOD — EPIC 05: Recommendation Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 5.1 — Recommendation Context Builder

### Definition of Done
- [ ] RecommendationContext built with all required fields
- [ ] completeness_ratio() computed correctly
- [ ] Wave 9 pricing + Wave 11 visual fields included

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.1.1 | RecommendationContext contains all required fields: keyword data, scores, competitor profiles, review insights, pricing data, visual data | Pydantic model instantiation test |
| AC-5.1.2 | build_recommendation_context() for keyword with full data returns context with completeness_ratio ≥ 0.90 | Completeness test with pre-seeded data |
| AC-5.1.3 | build_recommendation_context() for keyword with missing trends/reddit returns context with completeness_ratio ≥ 0.60 | Partial data test |
| AC-5.1.4 | Context includes Wave 9 pricing fields: price_clusters, market_type, moat_strength, price_gap_positions | Field presence test |
| AC-5.1.5 | Context includes Wave 11 visual fields: thumbnail_patterns, profile_patterns, top_visual_styles | Field presence test |

---

## Story 5.2 — Eligibility and Gating

### Definition of Done
- [ ] get_eligible_keywords() filters to STRONG GO + CONDITIONAL GO
- [ ] passes_recommendation_gates() enforces all 3 gate conditions
- [ ] force_recommend_keywords override honoured

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.2.1 | get_eligible_keywords() returns only STRONG GO and CONDITIONAL GO keywords | Tag filter test |
| AC-5.2.2 | Keyword with confidence 0.35 is excluded by passes_recommendation_gates() | Gate rejection test |
| AC-5.2.3 | Keyword with demand_score 15 is excluded | Gate rejection test |
| AC-5.2.4 | Keyword with 0 gigs analyzed is excluded | Gate rejection test |
| AC-5.2.5 | should_regenerate_recommendation() returns False when score delta < 5 and no new competitor data | Skip logic test |
| AC-5.2.6 | Keyword listed in force_recommend_keywords bypasses all gates | Override test |

---

## Story 5.3 — LLM Task Implementations (14 Tasks)

### Definition of Done
- [ ] All 14 LLM task functions implemented returning correct schema
- [ ] Each task failure returns None without crashing other tasks
- [ ] asyncio.gather() runs all 14 tasks concurrently

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.3.1 | generate_gig_titles() returns exactly 5 title variants, each ≤ 80 characters | Count + length test |
| AC-5.3.2 | generate_tag_sets() returns exactly 5 tag sets, each with 5 tags | Structure test |
| AC-5.3.3 | generate_package_structure() returns 3 tiers (basic/standard/premium) with ascending prices | Tier count + price order test |
| AC-5.3.4 | generate_description_outline() returns 5-7 sections with title + body each | Count + structure test |
| AC-5.3.5 | generate_faq_entries() returns 5-7 FAQ items with question + answer each | Count + structure test |
| AC-5.3.6 | generate_differentiation_angle() returns positioning statement + ≥ 2 differentiators | Non-empty test |
| AC-5.3.7 | generate_buyer_persona() returns name, pain_points, decision_factors | Structure test |
| AC-5.3.8 | generate_thumbnail_direction() returns visual concept + color palette + text overlay | Structure test |
| AC-5.3.9 | generate_upsell_structure() returns 2-4 extras with name, price, description | Count + structure test |
| AC-5.3.10 | generate_red_flags() returns risk_level (LOW/MEDIUM/HIGH) + ≥ 1 risk item | Enum + count test |
| AC-5.3.11 | generate_niche_viability() returns viability_rating (0-10) + reasoning text | Range + non-empty test |
| AC-5.3.12 | generate_pricing_strategy() returns entry_price, target_price, milestone prices | Structure test |
| AC-5.3.13 | generate_profile_optimization() returns bio_template + headline + specialization_tags | Structure test |
| AC-5.3.14 | generate_visual_recommendations() returns thumbnail_style + gallery_recommendations | Structure test |
| AC-5.3.15 | Each task that fails returns None without crashing the other 13 tasks | Error isolation test |

---

## Story 5.4 — Jinja2 Prompt Templates

### Definition of Done
- [ ] All 13 E05-spec .j2 templates exist in src/llm/prompts/
- [ ] Every template renders without error with a sample context
- [ ] No template references undefined variables

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.4.1 | All 13 .j2 files exist in src/llm/prompts/ directory | File existence check |
| AC-5.4.2 | Each template renders without error when given a valid RecommendationContext | Render test with sample context |
| AC-5.4.3 | Each rendered prompt is ≤ 4000 tokens (stays within context window budget) | Token count test |
| AC-5.4.4 | Templates include system prompt + user prompt sections | Structure test |

---

## Story 5.5 — Pydantic Output Schemas

### Definition of Done
- [ ] All 14 Pydantic output schemas validate correctly
- [ ] RecommendationOutput.completeness_ratio() returns correct fraction
- [ ] Optional fields default to None

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.5.1 | Each of 12 output schemas validates correct data and rejects malformed data | Valid + invalid test per schema |
| AC-5.5.2 | RecommendationOutput.completeness_ratio() returns correct fraction (e.g., 12/14 = 0.857) | Calculation test |
| AC-5.5.3 | RecommendationOutput serializes to JSON and deserializes back identically | Roundtrip test |

---

## Story 5.6 — Async Concurrent Execution

### Definition of Done
- [ ] asyncio.gather() collects all 14 task results
- [ ] Partial success stored with generation_complete=False
- [ ] No unhandled exceptions escape the gather

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.6.1 | All 14 tasks execute concurrently via asyncio.gather(), not sequentially | Timing test: 14 tasks finish in < 2× single task time |
| AC-5.6.2 | If 2 tasks fail, the other 12 results are still stored | Partial failure injection test |
| AC-5.6.3 | generation_complete is True only when all 14 tasks succeed | Flag test |
| AC-5.6.4 | generation_complete is False when ≥ 1 task failed | Partial failure flag test |

---

## Story 5.7 — Recommendation Storage

### Definition of Done
- [ ] Recommendation UPSERTs correctly
- [ ] llm_cost_usd summed across all 14 tasks
- [ ] generation_complete flag set correctly

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.7.1 | UPSERT: first generation creates new row; second overwrites existing | Count assertion after 2 calls |
| AC-5.7.2 | llm_cost_usd equals sum of costs from all 14 individual LLM calls | Cost summation test |
| AC-5.7.3 | Recommendation.run_id links to the correct RunLog entry | Foreign key test |

---

## Story 5.8 — Stage 13 Orchestration

### Definition of Done
- [ ] run_stage_13() loops all eligible keywords
- [ ] --mode recommendations-only runs Stage 13 only
- [ ] Per-keyword regeneration trigger works from dashboard

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.8.1 | `--mode recommendations-only` generates recommendations for all eligible keywords | Count match test |
| AC-5.8.2 | Keywords that fail gates are skipped with a log message | Log capture test |
| AC-5.8.3 | Per-keyword regeneration updates the existing recommendation row | UPSERT test |
| AC-5.8.4 | Total LLM cost for Stage 13 is logged in RunLog.llm_cost_total | Cost tracking test |

---

## Story 5.9 — Recommendation Export

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-5.9.1 | Markdown export contains all 14 sections with proper headers | Section count test |
| AC-5.9.2 | JSON export matches Pydantic model_dump() output | Schema validation test |
| AC-5.9.3 | Bulk markdown export contains all eligible recommendations in one file | Count test |
| AC-5.9.4 | Export files are written to data/exports/ with timestamped filenames | File existence test |

---

## Epic 05 — Overall Definition of Done

1. ✅ `--mode recommendations-only` generates recommendations for all STRONG GO + CONDITIONAL GO keywords
2. ✅ All 14 LLM tasks produce valid structured output
3. ✅ Failed tasks don't crash the pipeline — partial recommendations are stored
4. ✅ LLM costs are tracked per-recommendation and per-run
5. ✅ Export produces valid Markdown and JSON files
6. ✅ All recommendation tests pass
