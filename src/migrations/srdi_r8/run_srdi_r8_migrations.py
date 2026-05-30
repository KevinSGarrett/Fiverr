"""Run SRDI R8 migrations in deterministic order."""

from __future__ import annotations

from sqlalchemy import Engine

from src.models.database import build_engine, normalize_database_url

from . import (
    migration_01_result_set_validations,
    migration_02_gigs_srdi_columns,
    migration_03_search_results_srdi_columns,
    migration_04_keyword_scores_srdi_columns,
    migration_05_keywords_srdi_columns,
    migration_06_discovery_outcomes_srdi_columns,
    migration_07_r3_columns,
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
