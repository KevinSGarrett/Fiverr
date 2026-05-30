"""M2: add SRDI columns to gigs table."""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")  # type: ignore[attr-defined]
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M2 migration."""
    with engine.begin() as connection:
        _add_column(connection, "gigs", "is_sponsored BOOLEAN")
        _add_column(connection, "gigs", "is_zombie BOOLEAN")
        _add_column(connection, "gigs", "relevance_flag BOOLEAN")
        _add_column(connection, "gigs", "relevance_score REAL")
        _add_column(connection, "gigs", "excluded_from_scoring BOOLEAN DEFAULT 0")
