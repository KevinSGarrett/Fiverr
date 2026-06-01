"""M9 (R4): add keyword score integrity columns."""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.engine import Connection

MIGRATION_ID = "09_keyword_score_integrity_cols"
TABLE = "keyword_scores"
COLUMNS = [
    ("trc_reliability", "FLOAT"),
    ("opportunity_relevance_factor", "FLOAT"),
    ("price_outliers_excluded", "INTEGER"),
    ("clean_gig_count", "INTEGER"),
    ("competitor_profile_source", "VARCHAR(32)"),
]


def _has_column(connection: Connection, table: str, column: str) -> bool:
    rows = connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    return any(str(row[1]) == column for row in rows)


def apply(engine: Engine) -> None:
    """Apply M9 migration in an idempotent manner."""
    with engine.begin() as connection:
        for column, declaration in COLUMNS:
            if not _has_column(connection, TABLE, column):
                connection.exec_driver_sql(f"ALTER TABLE {TABLE} ADD COLUMN {column} {declaration}")


def _sqlite_rebuild_without_columns(connection: Connection, drop_columns: list[str]) -> None:
    info_rows = connection.exec_driver_sql(f"PRAGMA table_info({TABLE})").fetchall()
    keep_rows = [row for row in info_rows if str(row[1]) not in set(drop_columns)]
    keep_names = [str(row[1]) for row in keep_rows]
    if not keep_names:
        return

    column_defs: list[str] = []
    for row in keep_rows:
        name = str(row[1])
        col_type = str(row[2] or "")
        not_null = bool(row[3])
        default_value = row[4]
        pk = bool(row[5])
        part = f"{name} {col_type}".strip()
        if not_null:
            part += " NOT NULL"
        if default_value is not None:
            part += f" DEFAULT {default_value}"
        if pk:
            part += " PRIMARY KEY"
        column_defs.append(part)

    temp_table = f"{TABLE}__tmp_r4_rollback"
    keep_csv = ", ".join(keep_names)
    connection.exec_driver_sql(f"CREATE TABLE {temp_table} ({', '.join(column_defs)})")
    connection.exec_driver_sql(f"INSERT INTO {temp_table} ({keep_csv}) SELECT {keep_csv} FROM {TABLE}")
    connection.exec_driver_sql(f"DROP TABLE {TABLE}")
    connection.exec_driver_sql(f"ALTER TABLE {temp_table} RENAME TO {TABLE}")


def rollback(engine: Engine) -> None:
    """Rollback M9 migration. SQLite uses table rebuild drop pattern."""
    if engine.dialect.name != "sqlite":
        with engine.begin() as connection:
            for column, _declaration in COLUMNS:
                try:
                    connection.exec_driver_sql(f"ALTER TABLE {TABLE} DROP COLUMN {column}")
                except Exception:
                    continue
        return

    with engine.begin() as connection:
        _sqlite_rebuild_without_columns(connection, [column for column, _ in COLUMNS])
