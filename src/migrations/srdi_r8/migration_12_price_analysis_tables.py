"""C062 Wave 9: add price analysis tables."""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.engine import Connection


def _get_columns(connection: Connection, table_name: str) -> set[str]:
    rows = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _add_column_if_missing(connection: Connection, table_name: str, column_name: str, declaration: str) -> None:
    existing = _get_columns(connection, table_name)
    if column_name in existing:
        return
    connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {declaration}")


def apply(engine: Engine) -> None:
    """Create Wave 9 pricing tables idempotently."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS price_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER NOT NULL,
                niche_id VARCHAR(128) NOT NULL,
                run_id VARCHAR(128) NOT NULL,
                basic_n INTEGER,
                basic_median FLOAT,
                basic_mean FLOAT,
                basic_mode FLOAT,
                basic_std FLOAT,
                basic_q1 FLOAT,
                basic_q3 FLOAT,
                basic_p10 FLOAT,
                basic_p90 FLOAT,
                basic_skewness FLOAT,
                basic_cv FLOAT,
                basic_clusters JSON,
                basic_gaps JSON,
                standard_n INTEGER,
                standard_median FLOAT,
                standard_mean FLOAT,
                standard_mode FLOAT,
                standard_std FLOAT,
                standard_q1 FLOAT,
                standard_q3 FLOAT,
                standard_p10 FLOAT,
                standard_p90 FLOAT,
                standard_skewness FLOAT,
                standard_cv FLOAT,
                standard_clusters JSON,
                standard_gaps JSON,
                premium_n INTEGER,
                premium_median FLOAT,
                premium_mean FLOAT,
                premium_mode FLOAT,
                premium_std FLOAT,
                premium_q1 FLOAT,
                premium_q3 FLOAT,
                premium_p10 FLOAT,
                premium_p90 FLOAT,
                premium_skewness FLOAT,
                premium_cv FLOAT,
                premium_clusters JSON,
                premium_gaps JSON,
                price_review_correlation FLOAT,
                moat_strength VARCHAR(16),
                review_premium_usd FLOAT,
                new_seller_avg_price FLOAT,
                new_seller_discount_pct FLOAT,
                market_type VARCHAR(32),
                avg_extras_count FLOAT,
                avg_extras_price FLOAT,
                extras_price_range JSON,
                analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(keyword_id) REFERENCES keywords (id),
                CONSTRAINT uq_price_analysis_keyword_run UNIQUE (keyword_id, run_id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_price_analysis_keyword_id ON price_analysis (keyword_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_price_analysis_niche_id ON price_analysis (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_price_analysis_run_id ON price_analysis (run_id)"
        )

        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS niche_price_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_id VARCHAR(128) NOT NULL UNIQUE,
                run_id VARCHAR(128) NOT NULL,
                keywords_analyzed INTEGER,
                basic_median FLOAT,
                basic_mean FLOAT,
                basic_p25 FLOAT,
                basic_p75 FLOAT,
                standard_median FLOAT,
                standard_mean FLOAT,
                standard_p25 FLOAT,
                standard_p75 FLOAT,
                premium_median FLOAT,
                premium_mean FLOAT,
                premium_p25 FLOAT,
                premium_p75 FLOAT,
                avg_price_review_correlation FLOAT,
                moat_strength VARCHAR(16),
                analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_niche_price_analysis_niche_id ON niche_price_analysis (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_niche_price_analysis_run_id ON niche_price_analysis (run_id)"
        )

        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS pricing_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER NOT NULL,
                niche_id VARCHAR(128) NOT NULL,
                run_id VARCHAR(128) NOT NULL,
                entry_basic FLOAT,
                entry_standard FLOAT,
                entry_premium FLOAT,
                acquisition_basic FLOAT,
                acquisition_standard FLOAT,
                acquisition_premium FLOAT,
                target_basic FLOAT,
                target_standard FLOAT,
                target_premium FLOAT,
                price_ladder JSON,
                undercut_pct FLOAT,
                moat_adjustment FLOAT,
                gap_pricing_used BOOLEAN NOT NULL DEFAULT 0,
                gap_target FLOAT,
                market_type VARCHAR(32),
                confidence VARCHAR(16),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(keyword_id) REFERENCES keywords (id)
            )
            """
        )
        # Backfill pre-C062 pricing_snapshots schema in-place for idempotent upgrades.
        _add_column_if_missing(connection, "pricing_snapshots", "niche_id", "VARCHAR(128)")
        _add_column_if_missing(connection, "pricing_snapshots", "run_id", "VARCHAR(128)")
        _add_column_if_missing(connection, "pricing_snapshots", "entry_basic", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "entry_standard", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "entry_premium", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "acquisition_basic", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "acquisition_standard", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "acquisition_premium", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "target_basic", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "target_standard", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "target_premium", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "price_ladder", "JSON")
        _add_column_if_missing(connection, "pricing_snapshots", "undercut_pct", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "moat_adjustment", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "gap_pricing_used", "BOOLEAN NOT NULL DEFAULT 0")
        _add_column_if_missing(connection, "pricing_snapshots", "gap_target", "FLOAT")
        _add_column_if_missing(connection, "pricing_snapshots", "market_type", "VARCHAR(32)")
        _add_column_if_missing(connection, "pricing_snapshots", "confidence", "VARCHAR(16)")
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_pricing_snapshots_keyword_id ON pricing_snapshots (keyword_id)"
        )
        if "niche_id" in _get_columns(connection, "pricing_snapshots"):
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_pricing_snapshots_niche_id ON pricing_snapshots (niche_id)"
            )
        if "run_id" in _get_columns(connection, "pricing_snapshots"):
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_pricing_snapshots_run_id ON pricing_snapshots (run_id)"
            )
