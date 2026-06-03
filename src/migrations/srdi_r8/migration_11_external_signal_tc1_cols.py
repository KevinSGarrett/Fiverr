"""C061 TC-1: add raw_value, relevance_score, trend_direction to external_signals."""
from sqlalchemy import Engine
from sqlalchemy.engine import Connection


def _add_column(connection: Connection, table_name: str, ddl: str) -> None:
    """Add a column idempotently -- ignores duplicate-column errors."""
    try:
        connection.exec_driver_sql(
            f"ALTER TABLE {table_name} ADD COLUMN {ddl}"
        )
    except Exception:
        return


def apply(engine: Engine) -> None:
    with engine.begin() as connection:
        _add_column(connection, "external_signals", "raw_value REAL")
        _add_column(connection, "external_signals", "relevance_score REAL")
        _add_column(connection, "external_signals", "trend_direction VARCHAR(16)")
