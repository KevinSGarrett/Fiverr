"""Integration tests for database initialization and session helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect, select
from src.models.database import (
    build_engine,
    create_session_factory,
    get_session,
    initialize_database,
    list_tables,
    verify_required_tables,
)
from src.models.niche import NicheConfigRecord
from src.models.registry import get_registered_table_names, verify_required_phase2_tables


def test_initialize_database_creates_expected_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "init_test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    engine = initialize_database(database_url=db_url)
    tables = set(list_tables(engine))

    assert set(get_registered_table_names()).issubset(tables)


def test_verify_required_tables_reports_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "verify_tables.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")

    missing = verify_required_tables(engine, ["niche_configs", "does_not_exist"])
    assert missing == ["does_not_exist"]


def test_initialize_database_creates_every_registered_table(tmp_path: Path) -> None:
    db_path = tmp_path / "registered_tables.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    missing = verify_required_tables(engine)
    assert missing == []


def test_initialize_database_satisfies_phase2_required_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "phase2_required.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    missing = verify_required_phase2_tables(list_tables(engine))
    assert missing == []


def test_get_session_commit_and_rollback_behavior(tmp_path: Path) -> None:
    db_path = tmp_path / "session_behavior.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = initialize_database(database_url=db_url)
    session_factory = create_session_factory(engine)

    with get_session(session_factory) as session:
        session.add(
            NicheConfigRecord(
                niche_id="commit_case",
                name="Commit",
                depth="standard",
                category_path="programming-tech/commit",
            )
        )

    with get_session(session_factory) as session:
        committed = session.execute(
            select(NicheConfigRecord).where(NicheConfigRecord.niche_id == "commit_case")
        ).scalar_one_or_none()
        assert committed is not None

    with pytest.raises(RuntimeError):
        with get_session(session_factory) as session:
            session.add(
                NicheConfigRecord(
                    niche_id="rollback_case",
                    name="Rollback",
                    depth="standard",
                    category_path="programming-tech/rollback",
                )
            )
            raise RuntimeError("force rollback")

    with get_session(session_factory) as session:
        rolled_back = session.execute(
            select(NicheConfigRecord).where(NicheConfigRecord.niche_id == "rollback_case")
        ).scalar_one_or_none()
        assert rolled_back is None


def test_initialize_database_creates_parent_data_path(tmp_path: Path) -> None:
    nested_db_path = tmp_path / "nested" / "data" / "foundation.db"
    db_url = f"sqlite:///{nested_db_path.as_posix()}"

    initialize_database(database_url=db_url)

    assert nested_db_path.exists()
    engine = build_engine(db_url)
    assert "niche_configs" in list_tables(engine)


def test_initialize_database_backfills_keyword_intent_class_for_legacy_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_keyword_schema.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = initialize_database(database_url=db_url)

    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE keywords DROP COLUMN intent_class")

    columns_before = {column["name"] for column in inspect(engine).get_columns("keywords")}
    assert "intent_class" not in columns_before

    initialize_database(engine=engine)

    columns_after = {column["name"] for column in inspect(engine).get_columns("keywords")}
    assert "intent_class" in columns_after
