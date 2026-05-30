"""M4: add SRDI columns to keyword_scores table."""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")  # type: ignore[attr-defined]
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M4 migration."""
    with engine.begin() as connection:
        _add_column(connection, "keyword_scores", "relevance_validation_applied BOOLEAN DEFAULT 0")
        _add_column(connection, "keyword_scores", "scoring_method TEXT DEFAULT 'legacy_pre_relevance_v1'")
        _add_column(connection, "keyword_scores", "trc_reliability_qualified BOOLEAN")
