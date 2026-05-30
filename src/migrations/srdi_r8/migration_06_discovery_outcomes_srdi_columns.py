"""M6: add SRDI columns to discovery_outcomes table."""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")  # type: ignore[attr-defined]
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M6 migration."""
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS discovery_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
            """
        )
        _add_column(connection, "discovery_outcomes", "is_invalid BOOLEAN DEFAULT 0")
        _add_column(connection, "discovery_outcomes", "is_contaminated BOOLEAN DEFAULT 0")
        _add_column(connection, "discovery_outcomes", "relevance_score REAL")
        _add_column(connection, "discovery_outcomes", "contamination_reason TEXT")
