# CYCLE_056_AGENT_B — §11.5 Model-Migration Parity Audit

Branch HEAD: fb15c64f6c077a4b3186ef7b7b3eacd1c77ee159
Develop base: abc1234

## §11.5 Retroactive Parity Audit Results

Audit date: 2026-06-01  
Models audited: 9

### Model: discovery_outcome.py (table: discovery_outcomes)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | `migration_06_discovery_outcomes_srdi_columns.py` | `id INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| run_id | str \| None | yes | no | `migration_10_discovery_outcome_context_cols.py` | `run_id VARCHAR(64)` | YES |
| niche_id | str \| None | yes | no | `migration_10_discovery_outcome_context_cols.py` | `niche_id VARCHAR(128)` | YES |
| keyword_text | str \| None | yes | no | `migration_10_discovery_outcome_context_cols.py` | `keyword_text VARCHAR(256)` | YES |
| is_invalid | bool | no | yes | `migration_06_discovery_outcomes_srdi_columns.py` | `is_invalid BOOLEAN DEFAULT 0` | YES |
| is_contaminated | bool | no | yes | `migration_06_discovery_outcomes_srdi_columns.py` | `is_contaminated BOOLEAN DEFAULT 0` | YES |
| relevance_score | float \| None | yes | no | `migration_06_discovery_outcomes_srdi_columns.py` | `relevance_score REAL` | YES |
| contamination_reason | str \| None | yes | no | `migration_06_discovery_outcomes_srdi_columns.py` | `contamination_reason TEXT` | YES |
| created_at | datetime | no | yes | `migration_10_discovery_outcome_context_cols.py` | `created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)` | YES |

PRAGMA output: `['contamination_reason', 'created_at', 'id', 'is_contaminated', 'is_invalid', 'keyword_text', 'niche_id', 'relevance_score', 'run_id']`  
Result: ALL YES

### Model: keyword_score.py (table: keyword_scores)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | baseline table | `INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| keyword_id | int | no | no | baseline table | `INTEGER` | YES |
| scoring_profile | str | no | yes | baseline table | `VARCHAR(64)` | YES |
| score_depth | str | no | yes | baseline table | `VARCHAR(32)` | YES |
| scored_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| data_as_of | datetime \| None | yes | no | baseline table | `DATETIME` | YES |
| demand_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| competition_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| opportunity_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| feasibility_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| profitability_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| intent_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| saturation_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| weakness_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| trend_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| final_score | float \| None | yes | no | baseline table | `FLOAT` | YES |
| confidence_modifier | float \| None | yes | no | baseline table | `FLOAT` | YES |
| trc_reliability | float \| None | yes | no | `migration_09_keyword_score_integrity_cols.py` | `trc_reliability FLOAT` | YES |
| opportunity_relevance_factor | float \| None | yes | no | `migration_09_keyword_score_integrity_cols.py` | `opportunity_relevance_factor FLOAT` | YES |
| price_outliers_excluded | int \| None | yes | no | `migration_09_keyword_score_integrity_cols.py` | `price_outliers_excluded INTEGER` | YES |
| clean_gig_count | int \| None | yes | no | `migration_09_keyword_score_integrity_cols.py` | `clean_gig_count INTEGER` | YES |
| competitor_profile_source | str \| None | yes | no | `migration_09_keyword_score_integrity_cols.py` | `competitor_profile_source VARCHAR(32)` | YES |
| tag | str \| None | yes | no | baseline table | `VARCHAR(32)` | YES |
| score_components | dict \| None | yes | no | baseline table | `JSON` | YES |
| confidence_breakdown | dict \| None | yes | no | baseline table | `JSON` | YES |
| explanation_text | str \| None | yes | no | baseline table | `VARCHAR(4096)` | YES |
| red_flags | list \| None | yes | no | baseline table | `JSON` | YES |
| missing_data_warnings | list \| None | yes | no | baseline table | `JSON` | YES |
| source_evidence | list \| None | yes | no | baseline table | `JSON` | YES |
| llm_inputs_used | dict \| None | yes | no | baseline table | `JSON` | YES |
| niche_tier | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |

PRAGMA output: `['clean_gig_count', 'competition_score', 'competitor_profile_source', 'confidence_breakdown', 'confidence_modifier', 'data_as_of', 'demand_score', 'explanation_text', 'feasibility_score', 'final_score', 'id', 'intent_score', 'keyword_id', 'llm_inputs_used', 'missing_data_warnings', 'niche_tier', 'opportunity_relevance_factor', 'opportunity_score', 'price_outliers_excluded', 'profitability_score', 'red_flags', 'saturation_score', 'score_components', 'score_depth', 'scored_at', 'scoring_profile', 'source_evidence', 'tag', 'trc_reliability', 'trend_score', 'weakness_score']`  
Result: ALL YES (note: legacy DB still contains extra non-ORM columns from older migration_04; no parity gap)

### Model: keyword.py (actual class `Keyword` in `src/models/market.py`, table: keywords)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | baseline table | `INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| niche_id | int | no | no | baseline table | `INTEGER` | YES |
| keyword | str | no | no | baseline table | `VARCHAR(256)` | YES |
| normalized_keyword | str | no | no | baseline table | `VARCHAR(256)` | YES |
| language | str \| None | yes | no | baseline table | `VARCHAR(32)` | YES |
| intent_class | str \| None | yes | no | baseline table | `VARCHAR(32)` | YES |
| embedding_vector | str \| None | yes | no | baseline table | `TEXT` | YES |
| cluster_id | int \| None | yes | no | baseline table | `INTEGER` | YES |
| search_volume_hint | int \| None | yes | no | baseline table | `INTEGER` | YES |
| is_discovery | bool | no | yes | baseline table | `BOOLEAN` | YES |
| discovery_mode | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| hypothesis_confidence | float \| None | yes | no | baseline table | `FLOAT` | YES |
| ghost_market_flag | bool | no | yes | `migration_05_keywords_srdi_columns.py` | `ghost_market_flag BOOLEAN DEFAULT 0` | YES |
| discovery_needs_recollection | bool | no | yes | `migration_05_keywords_srdi_columns.py` | `discovery_needs_recollection BOOLEAN DEFAULT 0` | YES |
| last_relevance_validated_at | str \| None | yes | no | `migration_05_keywords_srdi_columns.py` | `last_relevance_validated_at TEXT` | YES |
| created_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| updated_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| external_source | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| source_url | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| source_collected_at | datetime \| None | yes | no | baseline table | `DATETIME` | YES |
| metadata_json | dict | no | yes | baseline table | `JSON` | YES |
| status | str | no | yes | baseline table | `VARCHAR(32)` | YES |
| error_message | str \| None | yes | no | baseline table | `VARCHAR(2048)` | YES |

PRAGMA output: `['cluster_id', 'created_at', 'discovery_mode', 'discovery_needs_recollection', 'embedding_vector', 'error_message', 'external_source', 'ghost_market_flag', 'hypothesis_confidence', 'id', 'intent_class', 'is_discovery', 'keyword', 'language', 'last_relevance_validated_at', 'metadata_json', 'niche_id', 'normalized_keyword', 'search_volume_hint', 'source_collected_at', 'source_url', 'status', 'updated_at']`  
Result: ALL YES

### Model: gig.py (table: gigs)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | baseline table | `INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| gig_url | str | no | no | baseline table | `VARCHAR(1024)` | YES |
| keyword_id | int \| None | yes | no | baseline table | `INTEGER` | YES |
| run_id | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| seller_username | str | no | no | baseline table | `VARCHAR(256)` | YES |
| gig_title_full | str \| None | yes | no | baseline table | `VARCHAR(512)` | YES |
| description_text | str \| None | yes | no | baseline table | `TEXT` | YES |
| packages | list \| None | yes | no | baseline table | `JSON` | YES |
| gig_extras | list \| None | yes | no | baseline table | `JSON` | YES |
| tags | list \| None | yes | no | baseline table | `JSON` | YES |
| faq_text | str \| None | yes | no | baseline table | `TEXT` | YES |
| video_present | bool \| None | yes | no | baseline table | `BOOLEAN` | YES |
| portfolio_count | int \| None | yes | no | baseline table | `INTEGER` | YES |
| review_count_exact | int \| None | yes | no | baseline table | `INTEGER` | YES |
| rating_exact | float \| None | yes | no | baseline table | `FLOAT` | YES |
| review_snippets | list \| None | yes | no | baseline table | `JSON` | YES |
| starting_price | float \| None | yes | no | baseline table | `FLOAT` | YES |
| thumbnail_url | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| orders_in_queue | int \| None | yes | no | baseline table | `INTEGER` | YES |
| position | int \| None | yes | no | baseline table | `INTEGER` | YES |
| detail_collected | bool | no | yes | baseline table | `BOOLEAN` | YES |
| detail_collected_at | datetime \| None | yes | no | baseline table | `DATETIME` | YES |
| ttl_hours | int | no | yes | baseline table | `INTEGER` | YES |
| sponsored_flag | bool | no | yes | baseline table | `BOOLEAN` | YES |
| is_sponsored | bool \| None | yes | no | `migration_02_gigs_srdi_columns.py` | `is_sponsored BOOLEAN` | YES |
| is_zombie | bool \| None | yes | no | `migration_02_gigs_srdi_columns.py` | `is_zombie BOOLEAN` | YES |
| relevance_flag | bool \| None | yes | no | `migration_02_gigs_srdi_columns.py` | `relevance_flag BOOLEAN` | YES |
| relevance_score | float \| None | yes | no | `migration_02_gigs_srdi_columns.py` | `relevance_score REAL` | YES |
| excluded_from_scoring | bool \| None | yes | yes | `migration_02_gigs_srdi_columns.py` | `excluded_from_scoring BOOLEAN DEFAULT 0` | YES |
| zombie_score | float \| None | yes | no | `migration_07_r3_columns.py` | `zombie_score REAL` | YES |
| zombie_signals | str \| None | yes | no | `migration_07_r3_columns.py` | `zombie_signals TEXT` | YES |
| last_reviewed_at | datetime \| None | yes | no | `migration_07_r3_columns.py` | `last_reviewed_at TIMESTAMP` | YES |
| external_gig_id | str \| None | yes | no | baseline table | `VARCHAR(128)` | YES |
| seller_id | int \| None | yes | no | baseline table | `INTEGER` | YES |
| title | str \| None | yes | no | baseline table | `VARCHAR(512)` | YES |
| normalized_title | str \| None | yes | no | baseline table | `VARCHAR(512)` | YES |
| category | str \| None | yes | no | baseline table | `VARCHAR(128)` | YES |
| currency | str \| None | yes | no | baseline table | `VARCHAR(8)` | YES |
| avg_rating | float \| None | yes | no | baseline table | `FLOAT` | YES |
| review_count | int \| None | yes | no | baseline table | `INTEGER` | YES |
| created_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| updated_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| external_source | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| source_url | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| source_collected_at | datetime \| None | yes | no | baseline table | `DATETIME` | YES |
| metadata_json | dict | no | yes | baseline table | `JSON` | YES |
| status | str | no | yes | baseline table | `VARCHAR(32)` | YES |
| error_message | str \| None | yes | no | baseline table | `VARCHAR(2048)` | YES |

PRAGMA output: `['avg_rating', 'category', 'created_at', 'currency', 'description_text', 'detail_collected', 'detail_collected_at', 'error_message', 'excluded_from_scoring', 'external_gig_id', 'external_source', 'faq_text', 'gig_extras', 'gig_title_full', 'gig_url', 'id', 'is_sponsored', 'is_zombie', 'keyword_id', 'last_reviewed_at', 'metadata_json', 'normalized_title', 'orders_in_queue', 'packages', 'portfolio_count', 'position', 'rating_exact', 'relevance_flag', 'relevance_score', 'review_count', 'review_count_exact', 'review_snippets', 'run_id', 'seller_id', 'seller_username', 'source_collected_at', 'source_url', 'sponsored_flag', 'starting_price', 'status', 'tags', 'thumbnail_url', 'title', 'ttl_hours', 'updated_at', 'video_present', 'zombie_score', 'zombie_signals']`  
Result: ALL YES

### Model: search_result.py (table: search_results)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | baseline table | `INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| keyword_id | int | no | no | baseline table | `INTEGER` | YES |
| run_id | str | no | yes | baseline table | `VARCHAR(64)` | YES |
| total_result_count | int \| None | yes | no | baseline table | `INTEGER` | YES |
| pagination_depth | int \| None | yes | no | baseline table | `INTEGER` | YES |
| gig_cards | list \| None | yes | no | baseline table | `JSON` | YES |
| page_collected | int | no | yes | baseline table | `INTEGER` | YES |
| collected_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| ttl_hours | int | no | yes | baseline table | `INTEGER` | YES |
| is_stale | bool | no | yes | baseline table | `BOOLEAN` | YES |
| raw_html_ref | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| search_strictness_used | str \| None | yes | no | `migration_03_search_results_srdi_columns.py` | `search_strictness_used TEXT DEFAULT 'NONE'` | YES |
| sponsored_gig_count | int \| None | yes | no | `migration_03_search_results_srdi_columns.py` | `sponsored_gig_count INTEGER DEFAULT 0` | YES |
| organic_gig_count | int \| None | yes | no | `migration_03_search_results_srdi_columns.py` | `organic_gig_count INTEGER` | YES |
| organic_trc | float \| None | yes | no | `migration_03_search_results_srdi_columns.py` | `organic_trc REAL` | YES |
| rsv_id | int \| None | yes | no | `migration_03_search_results_srdi_columns.py` | `rsv_id INTEGER` | YES |
| pages_collected | int \| None | yes | no | `migration_07_r3_columns.py` | `pages_collected INTEGER` | YES |
| rank | int \| None | yes | no | baseline table | `INTEGER` | YES |
| title | str \| None | yes | no | baseline table | `VARCHAR(512)` | YES |
| gig_id | int \| None | yes | no | baseline table | `INTEGER` | YES |
| result_url | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| observed_at | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| created_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| updated_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| external_source | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| source_url | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| source_collected_at | datetime \| None | yes | no | baseline table | `DATETIME` | YES |
| metadata_json | dict | no | yes | baseline table | `JSON` | YES |
| status | str | no | yes | baseline table | `VARCHAR(32)` | YES |
| error_message | str \| None | yes | no | baseline table | `VARCHAR(2048)` | YES |

PRAGMA output: `['collected_at', 'created_at', 'error_message', 'external_source', 'gig_cards', 'gig_id', 'id', 'is_stale', 'keyword_id', 'metadata_json', 'observed_at', 'organic_gig_count', 'organic_trc', 'page_collected', 'pages_collected', 'pagination_depth', 'rank', 'raw_html_ref', 'result_url', 'rsv_id', 'run_id', 'search_strictness_used', 'source_collected_at', 'source_url', 'sponsored_gig_count', 'status', 'title', 'total_result_count', 'ttl_hours', 'updated_at']`  
Result: ALL YES

### Model: external_signal.py (table: external_signals)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | baseline table | `INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| keyword_id | int | no | no | baseline table | `INTEGER` | YES |
| signal_type | str | no | no | baseline table | `VARCHAR(64)` | YES |
| signal_value | float \| None | yes | no | baseline table | `FLOAT` | YES |
| signal_json | dict \| None | yes | no | baseline table | `JSON` | YES |
| source_url | str \| None | yes | no | baseline table | `VARCHAR(1024)` | YES |
| collected_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| ttl_hours | int | no | yes | baseline table | `INTEGER` | YES |
| is_stale | bool | no | yes | baseline table | `BOOLEAN` | YES |
| run_id | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| collection_method | str \| None | yes | no | baseline table | `VARCHAR(64)` | YES |
| error_message | str \| None | yes | no | baseline table | `VARCHAR(2048)` | YES |
| created_at | datetime | no | yes | baseline table | `DATETIME` | YES |
| updated_at | datetime | no | yes | baseline table | `DATETIME` | YES |

PRAGMA output: `['collected_at', 'collection_method', 'created_at', 'error_message', 'id', 'is_stale', 'keyword_id', 'run_id', 'signal_json', 'signal_type', 'signal_value', 'source_url', 'ttl_hours', 'updated_at']`  
Result: ALL YES

### Model: result_set_validation.py (table: result_set_validations)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | `migration_01_result_set_validations.py` | `id INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| keyword_id | int | no | no | `migration_01_result_set_validations.py` | `keyword_id INTEGER NOT NULL` | YES |
| run_id | str | no | no | `migration_01_result_set_validations.py` | `run_id VARCHAR(64) NOT NULL` | YES |
| validated_at | datetime | no | yes | `migration_01_result_set_validations.py` | `validated_at DATETIME DEFAULT CURRENT_TIMESTAMP` | YES |
| result_count | int \| None | yes | no | `migration_01_result_set_validations.py` | `result_count INTEGER` | YES |
| relevant_count | int \| None | yes | no | `migration_01_result_set_validations.py` | `relevant_count INTEGER` | YES |
| sponsored_count | int \| None | yes | no | `migration_01_result_set_validations.py` | `sponsored_count INTEGER` | YES |
| result_set_relevance_score | float \| None | yes | no | `migration_01_result_set_validations.py` | `result_set_relevance_score REAL` | YES |
| ghost_market_flag | bool | no | yes | `migration_01_result_set_validations.py` | `ghost_market_flag BOOLEAN DEFAULT 0` | YES |
| ghost_evidence | dict \| None | yes | no | `migration_01_result_set_validations.py` | `ghost_evidence JSON` | YES |
| validation_method | str \| None | yes | no | `migration_01_result_set_validations.py` | `validation_method TEXT` | YES |
| search_strictness_used | str \| None | yes | no | `migration_01_result_set_validations.py` | `search_strictness_used TEXT` | YES |
| per_gig_relevance | dict \| None | yes | no | `migration_01_result_set_validations.py` | `per_gig_relevance JSON` | YES |
| relevance_deduction | float | no | yes | `migration_01_result_set_validations.py` | `relevance_deduction REAL DEFAULT 0.0` | YES |
| category_contamination_flag | bool | no | yes | `migration_08_r2_columns.py` | `category_contamination_flag BOOLEAN NOT NULL DEFAULT 0` | YES |
| used_fallback_strictness | bool | no | yes | `migration_08_r2_columns.py` | `used_fallback_strictness BOOLEAN NOT NULL DEFAULT 0` | YES |
| created_at | datetime | no | yes | baseline table extension | `DATETIME` | YES |
| updated_at | datetime | no | yes | baseline table extension | `DATETIME` | YES |

PRAGMA output: `['category_contamination_flag', 'created_at', 'ghost_evidence', 'ghost_market_flag', 'id', 'keyword_id', 'per_gig_relevance', 'relevance_deduction', 'relevant_count', 'result_count', 'result_set_relevance_score', 'run_id', 'search_strictness_used', 'sponsored_count', 'updated_at', 'used_fallback_strictness', 'validated_at', 'validation_method']`  
Result: ALL YES

### Model: market.py (table: markets)

Model file present, but no `Market` ORM class and no `markets` table in `foundation_gate_ci.db`.  
Result: model not present — skip (recorded per §11.5 rule).

### Model: competitor_profile.py (actual class `CompetitorProfile` in `src/models/market.py`, table: competitor_profiles)

| Column name | ORM type annotation | nullable | has_default | Migration file | Migration DDL | Present in DB? |
|---|---|---:|---:|---|---|---|
| id | int | no | no | baseline table / compatibility bootstrap | `INTEGER PRIMARY KEY AUTOINCREMENT` | YES |
| niche_id | str | no | no | baseline table / compatibility bootstrap | `VARCHAR(64)` | YES |
| run_id | str | no | no | baseline table / compatibility bootstrap | `VARCHAR(64)` | YES |
| top_gig_count | int | no | yes | baseline table / compatibility bootstrap | `INTEGER` | YES |
| median_price | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| mean_price | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| price_std | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| median_rating | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| mean_reviews | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| seller_level_distribution | dict | no | yes | baseline table / compatibility bootstrap | `JSON` | YES |
| min_delivery_days | int \| None | yes | no | baseline table / compatibility bootstrap | `INTEGER` | YES |
| max_delivery_days | int \| None | yes | no | baseline table / compatibility bootstrap | `INTEGER` | YES |
| video_present_rate | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| portfolio_present_rate | float \| None | yes | no | baseline table / compatibility bootstrap | `FLOAT` | YES |
| new_seller_gap | dict | no | yes | baseline table / compatibility bootstrap | `JSON NOT NULL DEFAULT '{}'` | YES |
| collected_at | datetime | no | yes | baseline table / compatibility bootstrap | `DATETIME DEFAULT CURRENT_TIMESTAMP` | YES |

PRAGMA output: `['collected_at', 'id', 'max_delivery_days', 'mean_price', 'mean_reviews', 'median_price', 'median_rating', 'min_delivery_days', 'new_seller_gap', 'niche_id', 'portfolio_present_rate', 'price_std', 'run_id', 'seller_level_distribution', 'top_gig_count', 'video_present_rate']`  
Result: ALL YES

### Summary

Models with ALL YES: `discovery_outcome.py`, `keyword_score.py`, `keyword.py` (`market.py::Keyword`), `gig.py`, `search_result.py`, `external_signal.py`, `result_set_validation.py`, `competitor_profile.py` (`market.py::CompetitorProfile`)  
Models with gaps found and fixed: None (all ORM columns covered by existing migrations and baseline schema once migrations are applied)  
Models that do not exist: `src/models/keyword.py`, `src/models/competitor_profile.py`; `market.py` has no `Market` model / no `markets` table

Conclusion: All ORM `Mapped[]` columns in all existing audited models are covered by migrations/baseline schema through `migration_10`. No uncovered ORM columns remain as of this audit.

## New Migrations Written

None — all models fully covered after applying existing `migration_01` through `migration_10`.

## migration_10 Verification

- Verified `migration_10_discovery_outcome_context_cols.py` contains all four `_add_column()` calls: `run_id`, `niche_id`, `keyword_text`, `created_at`.
- Verified `run_srdi_r8_migrations.py` imports and calls `migration_10` after `migration_09`.
- Re-ran foundation gate and PRAGMA on `discovery_outcomes`:
  - `['contamination_reason', 'created_at', 'id', 'is_contaminated', 'is_invalid', 'keyword_text', 'niche_id', 'relevance_score', 'run_id']`
- Result: migration_10 verified and complete.

## Niche IDs Drift Check

NICHE_VALIDATION_CONFIG keys vs config.yaml niches: MATCH

- Fix applied in `src/analysis/result_set_validator.py`: canonicalized `NICHE_VALIDATION_CONFIG` keys to exactly match the 9 `config.yaml` `niche_id` values.
- Preserved backward compatibility by mapping legacy validator slugs (`devvit_apps`, `chatbot_build`, `data_pipeline`, `prompt_engineering`, `browser_automation`) via `_LEGACY_NICHE_ALIASES`.

## Context Columns Usage Audit (discovery_outcome.py)

- `run_id`, `niche_id`, and `keyword_text` are actively written in `DiscoveryOrchestrator._record_outcome()` when instantiating `DiscoveryOutcome`.
- `_record_outcome()` is invoked from all gated outcome paths in the orchestrator.
- `created_at` in `DiscoveryOutcome` uses ORM default `func.now()`, so inserts populate timestamp without explicit assignment.

## Migration Style Audit

Migration file style audit: 7/10 follow the strict `_add_column() + apply(engine.begin())` standard pattern.

- Standard pattern: `migration_02`, `migration_03`, `migration_04`, `migration_05`, `migration_06`, `migration_07`, `migration_10`
- Non-standard but valid/idempotent: `migration_01` (table create), `migration_08`, `migration_09` (PRAGMA-based guards)
- No style deviations produced ruff/mypy failures.

## Verification Evidence

- ruff check `src/migrations/ src/analysis/result_set_validator.py`: `All checks passed!`
- mypy `src`: `Success: no issues found in 223 source files`
- foundation-gate: `[PASS] config_load`, `[PASS] database_registry`, `[PASS] smoke_imports`, `[PASS] repo_hygiene`
- PRAGMA discovery_outcomes: `['contamination_reason', 'created_at', 'id', 'is_contaminated', 'is_invalid', 'keyword_text', 'niche_id', 'relevance_score', 'run_id']`
- File-scoped regressions:
  - `test_discovery_relevance_gates + integration`: 26 passed
  - `test_opportunity_extended + profitability + competition`: 101 passed
  - `test_scoring_db_integration`: 41 passed
  - 26-name regression expression: 34 passed
  - `test_discovery_relevance_gates + test_discovery + test_demand_score_extended + test_opportunity_extended + test_competition_score`: 184 passed
  - `test_result_set_validator`: 41 passed
- Golden OFF parity: `status PASS`
  - `kw=110 final_score=62.7 confidence_modifier=1.0 tag=CONDITIONAL_GO`
  - `kw=96 final_score=35.8 tag=CAUTION`
  - `kw=3 final_score=56.66 tag=MONITOR`
- phase2-smoke: `Phase2 smoke OK` checks passed.
- Post-commit verification sequence:
  - foundation-gate re-run: PASS
  - quick REG-25/26/27 subset: 3 passed
  - config-check re-run: `Config OK: niches=9`
  - golden parity re-run: PASS (`kw=110=62.7`, `kw=96=35.8`, `kw=3=56.66`)

## Changed File Set

- `src/analysis/result_set_validator.py`
- `docs/cycle_reports/CYCLE_056_AGENT_B.md`

## Commit SHA

fb15c64f6c077a4b3186ef7b7b3eacd1c77ee159

## CI Status

Green on pushed HEAD:

- `Lint, Typecheck, Tests, and Gates`: `success` (required)
- `codecov/project`: `success`
- `codecov/patch`: `success` (advisory)
- `Secret Scan`: `success`
- `Dependency Audit`: `success`
- `Validate PR`: `failure` (non-required check)

## Completion Checklist (Task 25)

- [x] §11.5 parity audit run on all 9 model targets
- [x] Consolidated parity table in `CYCLE_056_AGENT_B.md` with all YES / explicit skips
- [x] New migration files handled (none required; existing migrations verified/applied)
- [x] `run_srdi_r8_migrations.py` verified in-order through `migration_10`
- [x] Niche IDs drift check documented and fixed in `src`
- [x] Context columns usage audit documented
- [x] Migration style audit documented
- [x] ruff zero errors
- [x] mypy zero errors (`223` files)
- [x] foundation-gate ALL PASS including `database_registry`
- [x] Golden OFF parity PASS (`62.7 / 35.8 / 56.66`)
- [x] 26-name regression pack PASS (`34 passed`)
- [x] Staged set contained only `src/` + `docs/cycle_reports/` files
- [x] ZERO `PM_Pack/`, `config.yaml`, `.env`, `*.db` files staged
- [x] CI green on pushed HEAD for required gate
- [x] Signal to Agent C written in report

Agent B complete. Branch at fb15c64f6c077a4b3186ef7b7b3eacd1c77ee159. §11.5 audit done — all YES / 0 gaps fixed. Golden parity PASS. Mypy/ruff clean. CI green on required gate. Agent C may proceed.
