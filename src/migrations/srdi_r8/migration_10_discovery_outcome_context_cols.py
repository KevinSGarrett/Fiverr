"""M10: add context/audit columns to discovery_outcomes.

Adds run_id, niche_id, keyword_text, and created_at columns that are defined
in the DiscoveryOutcome ORM model but were absent from earlier migrations.
All four are nullable and additive; existing rows are unaffected.
The migration is idempotent: a second apply() on a DB that already has these
columns is a no-op (the inner exception handler swallows the duplicate-column error).
"""

from __future__ import annotations

from sqlalchemy import Engine


def _add_column(connection: object, table_name: str, ddl: str) -> None:
    try:
        connection.exec_driver_sql(  # type: ignore[attr-defined]
            f"ALTER TABLE {table_name} ADD COLUMN {ddl}"
        )
    except Exception:
        return


def apply(engine: Engine) -> None:
    """Apply M10 migration."""
    with engine.begin() as connection:
        _add_column(connection, "discovery_outcomes", "run_id VARCHAR(64)")
        _add_column(connection, "discovery_outcomes", "niche_id VARCHAR(128)")
        _add_column(connection, "discovery_outcomes", "keyword_text VARCHAR(256)")
        _add_column(
            connection,
            "discovery_outcomes",
            "created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)",
        )
