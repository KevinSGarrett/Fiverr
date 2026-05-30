"""M7 (R3): add zombie and pagination audit columns."""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")  # type: ignore[attr-defined]
    except Exception:
        return


def _drop_column(connection: object, table_name: str, column_name: str) -> None:
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")  # type: ignore[attr-defined]
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M7 migration."""
    with engine.begin() as connection:
        _add_column(connection, "gigs", "zombie_score REAL")
        _add_column(connection, "gigs", "zombie_signals TEXT")
        _add_column(connection, "gigs", "last_reviewed_at TIMESTAMP")
        _add_column(connection, "search_results", "pages_collected INTEGER")


def rollback(engine: Engine) -> None:
    """
    Roll back M7 migration.

    SQLite pre-3.35 lacks DROP COLUMN support, and SRDI R8 migrations are validated
    for safe/no-error reversibility rather than guaranteed physical column removal.
    """
    if engine.dialect.name == "sqlite":
        return
    with engine.begin() as connection:
        _drop_column(connection, "gigs", "zombie_score")
        _drop_column(connection, "gigs", "zombie_signals")
        _drop_column(connection, "gigs", "last_reviewed_at")
        _drop_column(connection, "search_results", "pages_collected")
