"""M3: add SRDI columns to search_results table."""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")  # type: ignore[attr-defined]
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M3 migration."""
    with engine.begin() as connection:
        _add_column(connection, "search_results", "search_strictness_used TEXT DEFAULT 'NONE'")
        _add_column(connection, "search_results", "sponsored_gig_count INTEGER DEFAULT 0")
        _add_column(connection, "search_results", "organic_gig_count INTEGER")
        _add_column(connection, "search_results", "organic_trc REAL")
        _add_column(connection, "search_results", "rsv_id INTEGER")
