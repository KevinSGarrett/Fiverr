"""M5: add SRDI columns to keywords table."""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")  # type: ignore[attr-defined]
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M5 migration."""
    with engine.begin() as connection:
        _add_column(connection, "keywords", "ghost_market_flag BOOLEAN DEFAULT 0")
        _add_column(connection, "keywords", "discovery_needs_recollection BOOLEAN DEFAULT 0")
        _add_column(connection, "keywords", "last_relevance_validated_at TEXT")
