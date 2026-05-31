"""M8 (R2): add contamination/fallback strictness columns to RSV."""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.engine import Connection

MIGRATION_ID = "08_r2_columns"
TABLE = "result_set_validations"
COLUMNS = [
    ("category_contamination_flag", "BOOLEAN NOT NULL DEFAULT 0"),
    ("used_fallback_strictness", "BOOLEAN NOT NULL DEFAULT 0"),
]


def _has_column(connection: Connection, table: str, column: str) -> bool:
    rows = connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    return any(str(row[1]) == column for row in rows)


def apply(engine: Engine) -> None:
    """Apply M8 migration in an idempotent manner."""
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

    temp_table = f"{TABLE}__tmp_r2_rollback"
    keep_csv = ", ".join(keep_names)
    connection.exec_driver_sql(f"CREATE TABLE {temp_table} ({', '.join(column_defs)})")
    connection.exec_driver_sql(f"INSERT INTO {temp_table} ({keep_csv}) SELECT {keep_csv} FROM {TABLE}")
    connection.exec_driver_sql(f"DROP TABLE {TABLE}")
    connection.exec_driver_sql(f"ALTER TABLE {temp_table} RENAME TO {TABLE}")


def rollback(engine: Engine) -> None:
    """Rollback M8 migration. SQLite uses table rebuild drop pattern."""
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
