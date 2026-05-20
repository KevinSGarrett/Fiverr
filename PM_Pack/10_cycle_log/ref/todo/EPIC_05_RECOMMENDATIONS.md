# EPIC 05 — Recommendation Engine
# Fiverr Research System — Implementation To-Do

**Source Specs:** Wave 7 (06_analysis — recommendation files) + Wave 9 (pricing) + Wave 11 (playbook)
**Depends On:** Epic 04 (Scoring — needs tags and scores)
**Estimated Stories:** 10 | **Estimated Tasks:** 48

---

## Story 5.1 — Recommendation Context Builder

| ID | Task | Type | Description |
|---|---|---|---|
| 5.1.1 | Create RecommendationContext Pydantic model | TASK | All fields from RECOMMENDATION_ENGINE.md + Wave 9 pricing fields + Wave 11 profile/visual fields |
| 5.1.2 | Create build_recommendation_context() | TASK | Assembles context from keywords, scores, competitors, reviews, signals, pricing, visual data |
| 5.1.3 | Create context builder tests | TASK | Test with full data, partial data, missing sources |

## Story 5.2 — Eligibility and Gating

| ID | Task | Type | Description |
|---|---|---|---|
| 5.2.1 | Create get_eligible_keywords() | TASK | Query STRONG GO + CONDITIONAL GO keywords |
| 5.2.2 | Create passes_recommendation_gates() | TASK | Confidence ≥ 0.40, demand > 20, ≥ 1 gig analyzed |
| 5.2.3 | Create should_regenerate_recommendation() | TASK | Skip if score delta < 5 and no new competitor data |
| 5.2.4 | Create force-recommend override | TASK | Check config.yaml force_recommend_keywords list |
| 5.2.5 | Create eligibility tests | TASK | Test each gate condition, skip logic, override |

## Story 5.3 — LLM Task Implementations (14 Tasks)

| ID | Task | Type | Description |
|---|---|---|---|
| 5.3.1 | Create generate_gig_titles() | TASK | Task 1: gpt-4o, 5 title variants. Prompt: gig_titles.j2 |
| 5.3.2 | Create generate_tag_sets() | TASK | Task 2: gpt-4o-mini, 5 tag sets. Prompt: tag_sets.j2 |
| 5.3.3 | Create generate_package_structure() | TASK | Task 3: gpt-4o, 3-tier packages. Prompt: package_structure.j2 |
| 5.3.4 | Create generate_description_outline() | TASK | Task 4: gpt-4o, 5-7 sections. Prompt: description_outline.j2 |
| 5.3.5 | Create generate_faq_entries() | TASK | Task 5: gpt-4o-mini, 5-7 FAQs. Prompt: faq_entries.j2 |
| 5.3.6 | Create generate_differentiation_angle() | TASK | Task 6: gpt-4o, positioning + differentiators. Prompt: differentiation_angle.j2 |
| 5.3.7 | Create generate_buyer_persona() | TASK | Task 7: gpt-4o-mini. Prompt: buyer_persona.j2 |
| 5.3.8 | Create generate_thumbnail_direction() | TASK | Task 8: gpt-4o-mini. Prompt: thumbnail_direction.j2 |
| 5.3.9 | Create generate_upsell_structure() | TASK | Task 9: gpt-4o-mini, 2-4 extras. Prompt: upsell_structure.j2 |
| 5.3.10 | Create generate_red_flags() | TASK | Task 10: gpt-4o, risk assessment. Prompt: red_flags.j2 |
| 5.3.11 | Create generate_niche_viability() | TASK | Task 11: gpt-4o, strategic assessment. Prompt: niche_viability.j2 |
| 5.3.12 | Create generate_pricing_strategy() | TASK | Task 12 (Wave 9): gpt-4o, pricing recommendation. Prompt: pricing_strategy.j2 |
| 5.3.13 | Create generate_profile_optimization() | TASK | Task 13 (Wave 11): gpt-4o-mini, profile recs. Prompt: profile_optimization.j2 |
| 5.3.14 | Create generate_visual_recommendations() | TASK | Task 14 (Wave 11): Uses visual pattern analysis output, not LLM |

## Story 5.4 — Jinja2 Prompt Templates

| ID | Task | Type | Description |
|---|---|---|---|
| 5.4.1 | Create all 13 .j2 template files | TASK | Copy from LLM_PROMPT_TEMPLATES.md + PRICING_RECOMMENDATIONS_LLM.md + SELLER_PROFILE_OPTIMIZATION.md |
| 5.4.2 | Validate all templates render | TASK | Test each template with sample RecommendationContext |

## Story 5.5 — Pydantic Output Schemas

| ID | Task | Type | Description |
|---|---|---|---|
| 5.5.1 | Create all output schemas | TASK | GigTitle, PackageStructure, DescriptionOutline, FAQEntry, DifferentiationAngle, BuyerPersona, ThumbnailDirection, UpsellExtra, RedFlagsAssessment, NicheViability, PricingStrategy, ProfileOptimization |
| 5.5.2 | Create RecommendationOutput master schema | TASK | 14 Optional fields + completeness_ratio() + validators |
| 5.5.3 | Create schema validation tests | TASK | Test each schema with valid and invalid data |

## Story 5.6 — Async Concurrent Execution

| ID | Task | Type | Description |
|---|---|---|---|
| 5.6.1 | Create generate_recommendation() async function | TASK | asyncio.gather() for all 14 tasks, map results to fields, handle exceptions per task |
| 5.6.2 | Implement partial success handling | TASK | If 12/14 tasks succeed, store partial recommendation with generation_complete=False |
| 5.6.3 | Create concurrency tests | TASK | Test gather with mixed success/failure, verify partial storage |

## Story 5.7 — Recommendation Storage

| ID | Task | Type | Description |
|---|---|---|---|
| 5.7.1 | Implement recommendation UPSERT | TASK | db.merge() — update existing or insert new |
| 5.7.2 | Implement LLM cost tracking per recommendation | TASK | Sum costs across all 14 tasks, store in llm_cost_usd |
| 5.7.3 | Create storage tests | TASK | Test UPSERT, cost summation, generation_complete flag |

## Story 5.8 — Stage 13 Orchestration

| ID | Task | Type | Description |
|---|---|---|---|
| 5.8.1 | Create run_stage_13() | TASK | Loop eligible keywords, apply gates, check skip logic, generate, store |
| 5.8.2 | Implement `--mode recommendations-only` | TASK | Run Stage 13 only using existing scores |
| 5.8.3 | Implement per-keyword regeneration | TASK | Dashboard button triggers regeneration for single keyword |
| 5.8.4 | Create Stage 13 integration test | TASK | End-to-end test with pre-seeded score data |

## Story 5.9 — Recommendation Export

| ID | Task | Type | Description |
|---|---|---|---|
| 5.9.1 | Create export_recommendation_markdown() | TASK | Per-recommendation markdown rendering |
| 5.9.2 | Create export_recommendation_json() | TASK | Full Pydantic model dump to JSON |
| 5.9.3 | Create bulk_export_markdown() | TASK | All recommendations in one file |
| 5.9.4 | Create export tests | TASK | Test markdown + JSON format correctness |

---

## Epic 05 Summary: 10 Stories, 48 Tasks
