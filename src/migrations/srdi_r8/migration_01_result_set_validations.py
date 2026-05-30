"""M1: create result_set_validations table and indexes."""

from __future__ import annotations

from sqlalchemy import Engine


def apply(engine: Engine) -> None:
    """Apply M1 migration."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS result_set_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER NOT NULL REFERENCES keywords(id),
                run_id VARCHAR(64) NOT NULL,
                validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                result_count INTEGER,
                relevant_count INTEGER,
                sponsored_count INTEGER,
                result_set_relevance_score REAL,
                ghost_market_flag BOOLEAN DEFAULT 0,
                ghost_evidence JSON,
                validation_method TEXT,
                search_strictness_used TEXT,
                per_gig_relevance JSON,
                relevance_deduction REAL DEFAULT 0.0,
                CONSTRAINT uq_result_set_validations_keyword_run UNIQUE (keyword_id, run_id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_result_set_validations_keyword_id ON result_set_validations(keyword_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_result_set_validations_run_id ON result_set_validations(run_id)"
        )
