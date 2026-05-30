"""Unit tests for SRDI R8 migration idempotency and schema additions."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect

from src.migrations.srdi_r8.run_srdi_r8_migrations import run_srdi_r8_migrations
from src.models.database import initialize_database


def test_srdi_r8_migrations_apply_twice_without_errors(tmp_path: Path) -> None:
    db_path = tmp_path / "srdi_r8.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = initialize_database(database_url=db_url)
    run_srdi_r8_migrations(engine=engine)
    run_srdi_r8_migrations(engine=engine)

    inspector = inspect(engine)
    assert "result_set_validations" in inspector.get_table_names()
    gigs_columns = {column["name"] for column in inspector.get_columns("gigs")}
    assert "is_sponsored" in gigs_columns
    search_columns = {column["name"] for column in inspector.get_columns("search_results")}
    assert "search_strictness_used" in search_columns


def test_srdi_r8_run_with_database_url_creates_target_table(tmp_path: Path) -> None:
    db_path = tmp_path / "srdi_r8_url.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    initialize_database(database_url=db_url)
    run_srdi_r8_migrations(database_url=db_url)
    engine = create_engine(db_url, future=True)
    inspector = inspect(engine)
    assert "result_set_validations" in inspector.get_table_names()
