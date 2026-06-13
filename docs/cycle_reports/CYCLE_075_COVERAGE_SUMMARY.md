# CYCLE_075 Coverage Summary

| Module | Lines | Covered | % | Meets 90% |
|---|---:|---:|---:|:---:|
| automation\__init__.py | 2 | 2 | 100% | YES |
| automation\claude_sub_gate.py | 64 | 56 | 88% | NO |
| automation\codex_thread_reader.py | 80 | 80 | 100% | YES |
| automation\config_loader.py | 42 | 36 | 86% | NO |
| automation\drift_detector.py | 134 | 127 | 95% | YES |
| automation\failure_classifier.py | 90 | 89 | 99% | YES |
| automation\freeze_gate.py | 31 | 31 | 100% | YES |
| automation\github_client.py | 103 | 82 | 80% | NO |
| automation\jira_client.py | 99 | 91 | 92% | YES |
| automation\lock_manager.py | 119 | 103 | 87% | NO |
| automation\merge_gate.py | 252 | 0 | 0% | NO |
| automation\model_gate.py | 94 | 25 | 27% | NO |
| automation\notification_router.py | 138 | 33 | 24% | NO |
| automation\pm_pack_loader.py | 84 | 27 | 32% | NO |
| automation\policy_compiler.py | 49 | 13 | 27% | NO |
| automation\prompt_generator.py | 181 | 20 | 11% | NO |
| automation\prompt_validator.py | 95 | 26 | 27% | NO |
| automation\repair_loop.py | 127 | 0 | 0% | NO |
| automation\report_generator.py | 77 | 13 | 17% | NO |
| automation\secret_guard.py | 85 | 0 | 0% | NO |
| src\__init__.py | 1 | 1 | 100% | YES |
| src\analysis\__init__.py | 20 | 20 | 100% | YES |
| src\analysis\clustering.py | 94 | 89 | 95% | YES |
| src\analysis\competitor_profiler.py | 301 | 280 | 93% | YES |
| src\analysis\competitors.py | 75 | 74 | 99% | YES |
| src\analysis\contracts.py | 374 | 367 | 98% | YES |
| src\analysis\emerging_bonus.py | 34 | 34 | 100% | YES |
| src\analysis\external_signals.py | 74 | 74 | 100% | YES |
| src\analysis\gig_quality.py | 72 | 71 | 99% | YES |
| src\analysis\gig_quality_rubric.py | 151 | 150 | 99% | YES |
| src\analysis\intent.py | 139 | 129 | 93% | YES |
| src\analysis\keyword_clusterer.py | 276 | 266 | 96% | YES |
| src\analysis\keyword_features.py | 50 | 49 | 98% | YES |
| src\analysis\llm_relevance_classifier.py | 102 | 100 | 98% | YES |
| src\analysis\negation_exclusion.py | 17 | 15 | 88% | NO |
| src\analysis\orchestrator.py | 615 | 585 | 95% | YES |
| src\analysis\persistence.py | 44 | 42 | 95% | YES |
| src\analysis\pre_validator.py | 34 | 34 | 100% | YES |
| src\analysis\quality.py | 2 | 2 | 100% | YES |
| src\analysis\quality_gate.py | 22 | 18 | 82% | NO |
| src\analysis\registry.py | 19 | 19 | 100% | YES |
| src\analysis\result_set_validator.py | 125 | 110 | 88% | NO |
| src\analysis\review_analyzer.py | 215 | 35 | 16% | NO |
| src\analysis\reviews.py | 67 | 60 | 90% | YES |
| src\analysis\saturation.py | 81 | 79 | 98% | YES |
| src\analysis\saturation_model.py | 242 | 32 | 13% | NO |
| src\analysis\seller_strength.py | 163 | 144 | 88% | NO |
| src\analysis\sellers.py | 2 | 2 | 100% | YES |
| src\analysis\zombie_gig_detector.py | 84 | 42 | 50% | NO |
| src\cli.py | 39 | 0 | 0% | NO |
| src\collection\__init__.py | 20 | 20 | 100% | YES |
| src\collection\autocomplete.py | 56 | 51 | 91% | YES |
| src\collection\checkpoint.py | 98 | 98 | 100% | YES |
| src\collection\community_signals.py | 62 | 50 | 81% | NO |
| src\collection\contracts.py | 179 | 143 | 80% | NO |
| src\collection\external_signals.py | 60 | 53 | 88% | NO |
| src\collection\fiverr_selectors.py | 55 | 55 | 100% | YES |
| src\collection\gig_detail.py | 328 | 320 | 98% | YES |
| src\collection\html_text.py | 36 | 36 | 100% | YES |
| src\collection\http_fetcher.py | 44 | 20 | 45% | NO |
| src\collection\human_events.py | 13 | 6 | 46% | NO |
| src\collection\keyword_expansion.py | 60 | 55 | 92% | YES |
| src\collection\live_pilot.py | 92 | 84 | 91% | YES |
| src\collection\orchestrator.py | 514 | 465 | 90% | YES |
| src\collection\pacing.py | 131 | 120 | 92% | YES |
| src\collection\pilot_logger.py | 53 | 53 | 100% | YES |
| src\collection\playwright_check.py | 6 | 3 | 50% | NO |
| src\collection\proxy.py | 35 | 18 | 51% | NO |
| src\collection\queue.py | 30 | 30 | 100% | YES |
| src\collection\safety.py | 10 | 4 | 40% | NO |
| src\collection\scrapfly_client.py | 142 | 58 | 41% | NO |
| src\collection\search_plan.py | 35 | 35 | 100% | YES |
| src\collection\search_result_parser.py | 189 | 46 | 24% | NO |
| src\collection\search_url_builder.py | 153 | 63 | 41% | NO |
| src\collection\selectors.py | 54 | 54 | 100% | YES |
| src\collection\seller_profile.py | 308 | 142 | 46% | NO |
| src\collection\session.py | 64 | 64 | 100% | YES |
| src\collection\session_manager.py | 237 | 71 | 30% | NO |
| src\collection\workflows\__init__.py | 11 | 11 | 100% | YES |
| src\collection\workflows\auto_promotion.py | 5 | 5 | 100% | YES |
| src\collection\workflows\autocomplete.py | 100 | 100 | 100% | YES |
| src\collection\workflows\fiverr_search.py | 166 | 124 | 75% | NO |
| src\collection\workflows\gig_detail.py | 351 | 349 | 99% | YES |
| src\collection\workflows\google_trends.py | 194 | 194 | 100% | YES |
| src\collection\workflows\keyword_expansion.py | 478 | 453 | 95% | YES |
| src\collection\workflows\niche_init.py | 70 | 70 | 100% | YES |
| src\collection\workflows\reddit_devvit_bridge.py | 123 | 22 | 18% | NO |
| src\collection\workflows\reddit_signals.py | 214 | 60 | 28% | NO |
| src\collection\workflows\result_set_validation_workflow.py | 119 | 26 | 22% | NO |
| src\collection\workflows\seller_profile.py | 162 | 38 | 23% | NO |
| src\collection\workflows\youtube_count.py | 98 | 28 | 29% | NO |
| src\config\__init__.py | 3 | 3 | 100% | YES |
| src\config\loader.py | 72 | 56 | 78% | NO |
| src\config\models.py | 297 | 283 | 95% | YES |
| src\dashboard\__init__.py | 9 | 9 | 100% | YES |
| src\dashboard\_pages_legacy.py | 15 | 15 | 100% | YES |
| src\dashboard\alert_generator.py | 47 | 40 | 85% | NO |
| src\dashboard\alerts.py | 93 | 88 | 95% | YES |
| src\dashboard\app.py | 342 | 327 | 96% | YES |
| src\dashboard\badge_renderer.py | 15 | 15 | 100% | YES |
| src\dashboard\components.py | 152 | 147 | 97% | YES |
| src\dashboard\contracts.py | 100 | 96 | 96% | YES |
| src\dashboard\db_helpers.py | 23 | 20 | 87% | NO |
| src\dashboard\design.py | 30 | 27 | 90% | YES |
| src\dashboard\keywords.py | 109 | 104 | 95% | YES |
| src\dashboard\navigation.py | 10 | 10 | 100% | YES |
| src\dashboard\opportunities.py | 91 | 83 | 91% | YES |
| src\dashboard\pages\__init__.py | 12 | 12 | 100% | YES |
| src\dashboard\pages\competitors.py | 21 | 13 | 62% | NO |
| src\dashboard\pages\discovery.py | 76 | 74 | 97% | YES |
| src\dashboard\pages\keywords.py | 77 | 73 | 95% | YES |
| src\dashboard\pages\llm_costs.py | 26 | 25 | 96% | YES |
| src\dashboard\pages\opportunities.py | 66 | 63 | 95% | YES |
| src\dashboard\pages\playbook.py | 6 | 5 | 83% | NO |
| src\dashboard\pages\pricing.py | 6 | 5 | 83% | NO |
| src\dashboard\pages\recommendations.py | 60 | 48 | 80% | NO |
| src\dashboard\pages\run_history.py | 67 | 56 | 84% | NO |
| src\dashboard\queries.py | 324 | 304 | 94% | YES |
| src\dashboard\query_layer.py | 32 | 32 | 100% | YES |
| src\dashboard\relevance_dashboard.py | 33 | 8 | 24% | NO |
| src\dashboard\run_history.py | 110 | 102 | 93% | YES |
| src\dashboard\sample_data.py | 4 | 0 | 0% | NO |
| src\dashboard\schemas\__init__.py | 3 | 3 | 100% | YES |
| src\dashboard\schemas\opportunity_card.py | 29 | 29 | 100% | YES |
| src\dashboard\schemas\pricing_display.py | 32 | 32 | 100% | YES |
| src\dashboard\state.py | 61 | 61 | 100% | YES |
| src\db.py | 9 | 0 | 0% | NO |
| src\discovery\__init__.py | 7 | 7 | 100% | YES |
| src\discovery\candidates.py | 70 | 70 | 100% | YES |
| src\discovery\contracts.py | 55 | 53 | 96% | YES |
| src\discovery\feedback.py | 134 | 109 | 81% | NO |
| src\discovery\hypothesis.py | 325 | 319 | 98% | YES |
| src\discovery\integration.py | 87 | 85 | 98% | YES |
| src\discovery\orchestrator.py | 100 | 94 | 94% | YES |
| src\discovery\stage16.py | 119 | 110 | 92% | YES |
| src\exports\__init__.py | 7 | 7 | 100% | YES |
| src\exports\csv_export.py | 65 | 15 | 23% | NO |
| src\exports\formats.py | 49 | 22 | 45% | NO |
| src\exports\json_export.py | 62 | 16 | 26% | NO |
| src\exports\manifest.py | 77 | 36 | 47% | NO |
| src\exports\markdown_export.py | 42 | 11 | 26% | NO |
| src\exports\placeholders.py | 56 | 18 | 32% | NO |
| src\llm\__init__.py | 9 | 9 | 100% | YES |
| src\llm\cache.py | 119 | 113 | 95% | YES |
| src\llm\client.py | 86 | 76 | 88% | NO |
| src\llm\costs.py | 13 | 13 | 100% | YES |
| src\llm\provider.py | 32 | 32 | 100% | YES |
| src\llm\retry.py | 40 | 38 | 95% | YES |
| src\llm\schemas.py | 33 | 33 | 100% | YES |
| src\llm\template_renderer.py | 36 | 34 | 94% | YES |
| src\llm\validation.py | 31 | 30 | 97% | YES |
| src\migrations\migration_13_ladder_revenue_llm_observability.py | 27 | 7 | 26% | NO |
| src\migrations\migration_14_s76_discovery_feedback.py | 76 | 0 | 0% | NO |
| src\migrations\srdi_r8\__init__.py | 2 | 2 | 100% | YES |
| src\migrations\srdi_r8\migration_01_result_set_validations.py | 7 | 3 | 43% | NO |
| src\migrations\srdi_r8\migration_02_gigs_srdi_columns.py | 14 | 4 | 29% | NO |
| src\migrations\srdi_r8\migration_03_search_results_srdi_columns.py | 14 | 4 | 29% | NO |
| src\migrations\srdi_r8\migration_04_keyword_scores_srdi_columns.py | 12 | 4 | 33% | NO |
| src\migrations\srdi_r8\migration_05_keywords_srdi_columns.py | 12 | 4 | 33% | NO |
| src\migrations\srdi_r8\migration_06_discovery_outcomes_srdi_columns.py | 14 | 4 | 29% | NO |
| src\migrations\srdi_r8\migration_07_r3_columns.py | 26 | 6 | 23% | NO |
| src\migrations\srdi_r8\migration_08_r2_columns.py | 52 | 10 | 19% | NO |
| src\migrations\srdi_r8\migration_09_keyword_score_integrity_cols.py | 52 | 10 | 19% | NO |
| src\migrations\srdi_r8\migration_10_discovery_outcome_context_cols.py | 13 | 4 | 31% | NO |
| src\migrations\srdi_r8\migration_11_external_signal_tc1_cols.py | 12 | 4 | 33% | NO |
| src\migrations\srdi_r8\migration_12_price_analysis_tables.py | 44 | 6 | 14% | NO |
| src\migrations\srdi_r8\migration_13_ladder_revenue_llm_observability.py | 4 | 4 | 100% | YES |
| src\migrations\srdi_r8\run_srdi_r8_migrations.py | 19 | 5 | 26% | NO |
| src\models\__init__.py | 26 | 26 | 100% | YES |
| src\models\analysis.py | 48 | 48 | 100% | YES |
| src\models\associations.py | 13 | 13 | 100% | YES |
| src\models\auto_promotion.py | 14 | 14 | 100% | YES |
| src\models\base.py | 39 | 29 | 74% | NO |
| src\models\collection_runtime.py | 49 | 49 | 100% | YES |
| src\models\database.py | 245 | 216 | 88% | NO |
| src\models\discovery.py | 25 | 25 | 100% | YES |
| src\models\discovery_cycle.py | 24 | 24 | 100% | YES |
| src\models\discovery_outcome.py | 25 | 25 | 100% | YES |
| src\models\external_signal.py | 74 | 74 | 100% | YES |
| src\models\gig.py | 101 | 101 | 100% | YES |
| src\models\gig_quality_analysis.py | 2 | 2 | 100% | YES |
| src\models\gig_quality_score.py | 53 | 53 | 100% | YES |
| src\models\init.py | 4 | 4 | 100% | YES |
| src\models\job.py | 42 | 33 | 79% | NO |
| src\models\keyword_score.py | 43 | 43 | 100% | YES |
| src\models\market.py | 274 | 219 | 80% | NO |
| src\models\niche.py | 22 | 22 | 100% | YES |
| src\models\order.py | 19 | 19 | 100% | YES |
| src\models\price_analysis.py | 103 | 103 | 100% | YES |
| src\models\price_ladder_snapshot.py | 22 | 22 | 100% | YES |
| src\models\pricing.py | 2 | 0 | 0% | NO |
| src\models\registry.py | 40 | 31 | 78% | NO |
| src\models\result_set_validation.py | 25 | 25 | 100% | YES |
| src\models\revenue_gate_record.py | 18 | 18 | 100% | YES |
| src\models\runtime.py | 68 | 68 | 100% | YES |
| src\models\scoring.py | 58 | 58 | 100% | YES |
| src\models\search_result.py | 113 | 44 | 39% | NO |
| src\models\seller.py | 78 | 61 | 78% | NO |
| src\models\visual.py | 20 | 20 | 100% | YES |
| src\monitoring\__init__.py | 2 | 2 | 100% | YES |
| src\monitoring\monitors.py | 29 | 10 | 34% | NO |
| src\orchestrator.py | 325 | 160 | 49% | NO |
| src\playbook\__init__.py | 3 | 3 | 100% | YES |
| src\playbook\generator.py | 165 | 126 | 76% | NO |
| src\playbook\seed_guidance.py | 37 | 10 | 27% | NO |
| src\pricing\__init__.py | 10 | 10 | 100% | YES |
| src\pricing\analysis.py | 397 | 80 | 20% | NO |
| src\pricing\contracts.py | 46 | 46 | 100% | YES |
| src\pricing\ladder_tracker.py | 69 | 61 | 88% | NO |
| src\pricing\llm_task.py | 99 | 18 | 18% | NO |
| src\pricing\new_seller_pricing.py | 180 | 45 | 25% | NO |
| src\pricing\orchestrator.py | 71 | 23 | 32% | NO |
| src\pricing\pricing_export.py | 162 | 31 | 19% | NO |
| src\pricing\revenue_gate.py | 30 | 25 | 83% | NO |
| src\recommendations\__init__.py | 16 | 16 | 100% | YES |
| src\recommendations\context.py | 209 | 145 | 69% | NO |
| src\recommendations\context_builder.py | 188 | 23 | 12% | NO |
| src\recommendations\contracts.py | 137 | 137 | 100% | YES |
| src\recommendations\eligibility.py | 303 | 129 | 43% | NO |
| src\recommendations\executor.py | 51 | 51 | 100% | YES |
| src\recommendations\export.py | 334 | 320 | 96% | YES |
| src\recommendations\llm_tasks.py | 209 | 201 | 96% | YES |
| src\recommendations\orchestrator.py | 11 | 9 | 82% | NO |
| src\recommendations\pipeline.py | 89 | 27 | 30% | NO |
| src\recommendations\run.py | 39 | 11 | 28% | NO |
| src\recommendations\schemas.py | 148 | 141 | 95% | YES |
| src\recommendations\storage.py | 240 | 31 | 13% | NO |
| src\recommendations\tasks.py | 201 | 43 | 21% | NO |
| src\recommendations\template_validation.py | 4 | 3 | 75% | NO |
| src\reports\__init__.py | 4 | 4 | 100% | YES |
| src\reports\placeholders.py | 283 | 86 | 30% | NO |
| src\reports\run_summary.py | 42 | 17 | 40% | NO |
| src\reports\templates.py | 207 | 131 | 63% | NO |
| src\scheduler\__init__.py | 4 | 4 | 100% | YES |
| src\scheduler\exceptions.py | 11 | 6 | 55% | NO |
| src\scheduler\init.py | 2 | 2 | 100% | YES |
| src\scheduler\queue_processor.py | 56 | 47 | 84% | NO |
| src\scheduler\retry_config.py | 27 | 27 | 100% | YES |
| src\scheduler\retry_handler.py | 84 | 23 | 27% | NO |
| src\schemas\pricing_output.py | 54 | 45 | 83% | NO |
| src\scoring\__init__.py | 5 | 5 | 100% | YES |
| src\scoring\competition.py | 545 | 529 | 97% | YES |
| src\scoring\confidence.py | 203 | 182 | 90% | YES |
| src\scoring\contracts.py | 125 | 123 | 98% | YES |
| src\scoring\demand.py | 453 | 407 | 90% | YES |
| src\scoring\feasibility.py | 423 | 389 | 92% | YES |
| src\scoring\final.py | 91 | 74 | 81% | NO |
| src\scoring\intent.py | 204 | 168 | 82% | NO |
| src\scoring\opportunity.py | 81 | 41 | 51% | NO |
| src\scoring\orchestrator.py | 128 | 31 | 24% | NO |
| src\scoring\pipeline.py | 373 | 229 | 61% | NO |
| src\scoring\profitability.py | 267 | 135 | 51% | NO |
| src\scoring\ranking.py | 57 | 19 | 33% | NO |
| src\scoring\result_set_relevance.py | 12 | 12 | 100% | YES |
| src\scoring\saturation_score.py | 275 | 43 | 16% | NO |
| src\scoring\trend.py | 205 | 39 | 19% | NO |
| src\scoring\weakness.py | 596 | 123 | 21% | NO |
| src\scripts\__init__.py | 3 | 3 | 100% | YES |
| src\scripts\foundation_gate.py | 62 | 52 | 84% | NO |
| src\scripts\import_seeds.py | 89 | 0 | 0% | NO |
| src\scripts\init_db.py | 10 | 9 | 90% | YES |
| src\scripts\repo_hygiene.py | 41 | 35 | 85% | NO |
| src\utils\__init__.py | 10 | 10 | 100% | YES |
| src\utils\datetime.py | 50 | 50 | 100% | YES |
| src\utils\export.py | 17 | 16 | 94% | YES |
| src\utils\governance.py | 32 | 11 | 34% | NO |
| src\utils\hashing.py | 15 | 15 | 100% | YES |
| src\utils\json.py | 13 | 5 | 38% | NO |
| src\utils\logging.py | 29 | 27 | 93% | YES |
| src\utils\paths.py | 10 | 6 | 60% | NO |
| src\utils\retry.py | 26 | 8 | 31% | NO |
| src\utils\validation.py | 26 | 24 | 92% | YES |

## Modules Below 90%

- automation\claude_sub_gate.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\config_loader.py (86%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\github_client.py (80%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\lock_manager.py (87%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\merge_gate.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\model_gate.py (27%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\notification_router.py (24%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\pm_pack_loader.py (32%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\policy_compiler.py (27%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\prompt_generator.py (11%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\prompt_validator.py (27%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\repair_loop.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\report_generator.py (17%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- automation\secret_guard.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\negation_exclusion.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\quality_gate.py (82%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\result_set_validator.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\review_analyzer.py (16%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\saturation_model.py (13%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\seller_strength.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\analysis\zombie_gig_detector.py (50%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\cli.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\community_signals.py (81%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\contracts.py (80%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\external_signals.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\http_fetcher.py (45%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\human_events.py (46%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\playwright_check.py (50%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\proxy.py (51%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\safety.py (40%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\scrapfly_client.py (41%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\search_result_parser.py (24%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\search_url_builder.py (41%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\seller_profile.py (46%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\session_manager.py (30%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\workflows\fiverr_search.py (75%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\workflows\reddit_devvit_bridge.py (18%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\workflows\reddit_signals.py (28%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\workflows\result_set_validation_workflow.py (22%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\workflows\seller_profile.py (23%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\collection\workflows\youtube_count.py (29%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\config\loader.py (78%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\alert_generator.py (85%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\db_helpers.py (87%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\pages\competitors.py (62%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\pages\playbook.py (83%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\pages\pricing.py (83%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\pages\recommendations.py (80%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\pages\run_history.py (84%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\relevance_dashboard.py (24%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\dashboard\sample_data.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\db.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\discovery\feedback.py (81%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\exports\csv_export.py (23%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\exports\formats.py (45%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\exports\json_export.py (26%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\exports\manifest.py (47%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\exports\markdown_export.py (26%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\exports\placeholders.py (32%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\llm\client.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\migration_13_ladder_revenue_llm_observability.py (26%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\migration_14_s76_discovery_feedback.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_01_result_set_validations.py (43%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_02_gigs_srdi_columns.py (29%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_03_search_results_srdi_columns.py (29%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_04_keyword_scores_srdi_columns.py (33%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_05_keywords_srdi_columns.py (33%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_06_discovery_outcomes_srdi_columns.py (29%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_07_r3_columns.py (23%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_08_r2_columns.py (19%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_09_keyword_score_integrity_cols.py (19%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_10_discovery_outcome_context_cols.py (31%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_11_external_signal_tc1_cols.py (33%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\migration_12_price_analysis_tables.py (14%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\migrations\srdi_r8\run_srdi_r8_migrations.py (26%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\base.py (74%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\database.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\job.py (79%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\market.py (80%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\pricing.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\registry.py (78%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\search_result.py (39%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\models\seller.py (78%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\monitoring\monitors.py (34%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\orchestrator.py (49%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\playbook\generator.py (76%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\playbook\seed_guidance.py (27%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\analysis.py (20%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\ladder_tracker.py (88%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\llm_task.py (18%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\new_seller_pricing.py (25%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\orchestrator.py (32%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\pricing_export.py (19%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\pricing\revenue_gate.py (83%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\context.py (69%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\context_builder.py (12%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\eligibility.py (43%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\orchestrator.py (82%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\pipeline.py (30%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\run.py (28%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\storage.py (13%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\tasks.py (21%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\recommendations\template_validation.py (75%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\reports\placeholders.py (30%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\reports\run_summary.py (40%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\reports\templates.py (63%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scheduler\exceptions.py (55%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scheduler\queue_processor.py (84%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scheduler\retry_handler.py (27%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\schemas\pricing_output.py (83%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\final.py (81%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\intent.py (82%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\opportunity.py (51%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\orchestrator.py (24%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\pipeline.py (61%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\profitability.py (51%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\ranking.py (33%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\saturation_score.py (16%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\trend.py (19%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scoring\weakness.py (21%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scripts\foundation_gate.py (84%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scripts\import_seeds.py (0%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\scripts\repo_hygiene.py (85%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\utils\governance.py (34%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\utils\json.py (38%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\utils\paths.py (60%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
- src\utils\retry.py (31%): add focused unit tests for happy path, error path, boundary behavior, and exception handling branches.
