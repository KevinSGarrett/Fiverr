"""Unit tests for SRDI R8 migration_08_r2_columns."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from src.migrations.srdi_r8 import (
    migration_01_result_set_validations as m1,
)
from src.migrations.srdi_r8 import (
    migration_08_r2_columns as m8,
)
from src.migrations.srdi_r8.run_srdi_r8_migrations import run_srdi_r8_migrations

from tests.unit.test_srdi_r8_migrations import _bootstrap_base_tables


def _engine():
    return create_engine("sqlite+pysqlite:///:memory:", future=True)


def _column_names(engine, table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def test_apply_adds_both_columns() -> None:
    engine = _engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    m8.apply(engine)
    columns = _column_names(engine, "result_set_validations")
    assert "category_contamination_flag" in columns
    assert "used_fallback_strictness" in columns


def test_apply_is_idempotent() -> None:
    engine = _engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    m8.apply(engine)
    m8.apply(engine)
    columns = _column_names(engine, "result_set_validations")
    assert "category_contamination_flag" in columns
    assert "used_fallback_strictness" in columns


def test_rollback_drops_both_columns() -> None:
    engine = _engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    m8.apply(engine)
    m8.rollback(engine)
    columns = _column_names(engine, "result_set_validations")
    assert "category_contamination_flag" not in columns
    assert "used_fallback_strictness" not in columns


def test_reapply_after_rollback() -> None:
    engine = _engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    m8.apply(engine)
    m8.rollback(engine)
    m8.apply(engine)
    columns = _column_names(engine, "result_set_validations")
    assert "category_contamination_flag" in columns
    assert "used_fallback_strictness" in columns


def test_defaults_false_on_existing_rows() -> None:
    engine = _engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO result_set_validations (keyword_id, run_id, relevance_deduction) VALUES (1, 'r1', 0.0)"
        )
    m8.apply(engine)
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT category_contamination_flag, used_fallback_strictness FROM result_set_validations WHERE run_id='r1'"
            )
        ).first()
    assert row is not None
    assert int(row[0]) == 0
    assert int(row[1]) == 0


def test_registered_after_migration_07() -> None:
    engine = _engine()
    _bootstrap_base_tables(engine)
    run_srdi_r8_migrations(engine=engine)
    columns = _column_names(engine, "result_set_validations")
    assert "category_contamination_flag" in columns
    assert "used_fallback_strictness" in columns
