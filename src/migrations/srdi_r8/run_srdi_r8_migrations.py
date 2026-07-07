"""Run SRDI R8 migrations in deterministic order."""

from __future__ import annotations

from sqlalchemy import Engine

# migration_14/15 live at the top level (src/migrations/), not in this srdi_r8 package.
# migration_14 was ORPHANED — never registered here — so its S7.6 discovery-feedback
# tables were never created even though discovery code depends on them. Register both as
# the final steps.
from src.migrations import migration_14_s76_discovery_feedback, migration_15_price_analysis_min_max
from src.models.database import build_engine, normalize_database_url

from . import (
    migration_01_result_set_validations,
    migration_02_gigs_srdi_columns,
    migration_03_search_results_srdi_columns,
    migration_04_keyword_scores_srdi_columns,
    migration_05_keywords_srdi_columns,
    migration_06_discovery_outcomes_srdi_columns,
    migration_07_r3_columns,
    migration_08_r2_columns,
    migration_09_keyword_score_integrity_cols,
    migration_10_discovery_outcome_context_cols,
    migration_11_external_signal_tc1_cols,
    migration_12_price_analysis_tables,
    migration_13_ladder_revenue_llm_observability,
)


def run_srdi_r8_migrations(database_url: str | None = None, engine: Engine | None = None) -> None:
    """Apply all SRDI R8 migrations in-order."""
    active_engine = engine or build_engine(normalize_database_url(database_url))
    migration_01_result_set_validations.apply(active_engine)
    migration_02_gigs_srdi_columns.apply(active_engine)
    migration_03_search_results_srdi_columns.apply(active_engine)
    migration_04_keyword_scores_srdi_columns.apply(active_engine)
    migration_05_keywords_srdi_columns.apply(active_engine)
    migration_06_discovery_outcomes_srdi_columns.apply(active_engine)
    migration_07_r3_columns.apply(active_engine)
    migration_08_r2_columns.apply(active_engine)
    migration_09_keyword_score_integrity_cols.apply(active_engine)
    migration_10_discovery_outcome_context_cols.apply(active_engine)
    migration_11_external_signal_tc1_cols.apply(active_engine)
    migration_12_price_analysis_tables.apply(active_engine)
    migration_13_ladder_revenue_llm_observability.apply(active_engine)
    migration_14_s76_discovery_feedback.apply(active_engine)
    migration_15_price_analysis_min_max.apply(active_engine)
