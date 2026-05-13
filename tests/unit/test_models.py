"""Unit tests for SQLAlchemy foundation models."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect, select
from src.models.database import build_engine, get_db, initialize_database
from src.models.niche import NicheConfigRecord


def test_create_all_builds_niche_configs_table(tmp_path: Path) -> None:
    db_path = tmp_path / "create_all.db"
    engine = build_engine(f"sqlite:///{db_path.as_posix()}")
    initialize_database(engine)

    table_names = inspect(engine).get_table_names()
    assert "niche_configs" in table_names


def test_niche_config_record_json_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "json_roundtrip.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = initialize_database(build_engine(db_url))

    with get_db(db_url) as session:
        session.add(
            NicheConfigRecord(
                niche_id="test_niche",
                name="Test Niche",
                depth="standard",
                category_path="programming-tech/test",
                metadata_json={"tier": 2, "slot": 5},
                settings={"collect_top_n": 10, "models": ["gpt-4o-mini"]},
            )
        )

    with get_db(db_url) as session:
        result = session.execute(
            select(NicheConfigRecord).where(NicheConfigRecord.niche_id == "test_niche")
        ).scalar_one()
        assert result.metadata_json["tier"] == 2
        assert result.settings["collect_top_n"] == 10

    engine.dispose()


def test_get_db_commit_and_rollback(tmp_path: Path) -> None:
    db_path = tmp_path / "transactions.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    initialize_database(build_engine(db_url))

    with get_db(db_url) as session:
        session.add(
            NicheConfigRecord(
                niche_id="commit_case",
                name="Commit Case",
                depth="standard",
                category_path="programming-tech/commit",
            )
        )

    with get_db(db_url) as session:
        committed = session.execute(
            select(NicheConfigRecord).where(NicheConfigRecord.niche_id == "commit_case")
        ).scalar_one_or_none()
        assert committed is not None

    with pytest.raises(RuntimeError):
        with get_db(db_url) as session:
            session.add(
                NicheConfigRecord(
                    niche_id="rollback_case",
                    name="Rollback Case",
                    depth="standard",
                    category_path="programming-tech/rollback",
                )
            )
            raise RuntimeError("forcing rollback")

    with get_db(db_url) as session:
        rolled_back = session.execute(
            select(NicheConfigRecord).where(NicheConfigRecord.niche_id == "rollback_case")
        ).scalar_one_or_none()
        assert rolled_back is None
