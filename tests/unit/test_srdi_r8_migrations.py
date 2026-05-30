"""Unit tests for SRDI R8 migration idempotency and schema additions."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from src.migrations.srdi_r8 import (
    migration_01_result_set_validations as m1,
)
from src.migrations.srdi_r8 import (
    migration_02_gigs_srdi_columns as m2,
)
from src.migrations.srdi_r8 import (
    migration_03_search_results_srdi_columns as m3,
)
from src.migrations.srdi_r8 import (
    migration_04_keyword_scores_srdi_columns as m4,
)
from src.migrations.srdi_r8 import (
    migration_05_keywords_srdi_columns as m5,
)
from src.migrations.srdi_r8 import (
    migration_06_discovery_outcomes_srdi_columns as m6,
)
from src.migrations.srdi_r8 import (
    migration_07_r3_columns as m7,
)
from src.migrations.srdi_r8.run_srdi_r8_migrations import run_srdi_r8_migrations
from src.models import Keyword, Niche
from src.models.database import initialize_database
from src.models.result_set_validation import ResultSetValidation


def _build_memory_engine():
    return create_engine("sqlite+pysqlite:///:memory:", future=True)


def _bootstrap_base_tables(engine, *, include_discovery_outcomes: bool = True) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE IF NOT EXISTS keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        connection.exec_driver_sql("CREATE TABLE IF NOT EXISTS gigs (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        connection.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS search_results (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS keyword_scores (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        if include_discovery_outcomes:
            connection.exec_driver_sql(
                "CREATE TABLE IF NOT EXISTS discovery_outcomes (id INTEGER PRIMARY KEY AUTOINCREMENT)"
            )


def _column_names(engine, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def test_migration_m1_creates_result_set_validations_table() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    inspector = inspect(engine)
    assert "result_set_validations" in inspector.get_table_names()
    columns = _column_names(engine, "result_set_validations")
    assert "keyword_id" in columns
    assert "run_id" in columns
    assert "relevance_deduction" in columns


def test_migration_m1_is_idempotent() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m1.apply(engine)
    m1.apply(engine)
    assert "result_set_validations" in inspect(engine).get_table_names()


def test_migration_m2_adds_is_sponsored_to_gigs() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m2.apply(engine)
    columns = _column_names(engine, "gigs")
    assert "is_sponsored" in columns
    with engine.connect() as connection:
        pragma_rows = connection.execute(text("PRAGMA table_info(gigs)")).all()
    row_by_name = {str(row[1]): row for row in pragma_rows}
    is_sponsored_default = row_by_name["is_sponsored"][4]
    assert is_sponsored_default in (None, "0", "FALSE", "false")


def test_migration_m2_is_idempotent() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m2.apply(engine)
    m2.apply(engine)
    assert "is_sponsored" in _column_names(engine, "gigs")


def test_migration_m3_adds_search_strictness_to_search_results() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m3.apply(engine)
    assert "search_strictness_used" in _column_names(engine, "search_results")


def test_migration_m4_adds_scoring_method_to_keyword_scores() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m4.apply(engine)
    assert "scoring_method" in _column_names(engine, "keyword_scores")


def test_migration_m5_adds_ghost_market_flag_to_keywords() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m5.apply(engine)
    assert "ghost_market_flag" in _column_names(engine, "keywords")


def test_migration_m6_adds_is_invalid_to_discovery_outcomes() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine, include_discovery_outcomes=False)
    m6.apply(engine)
    assert "is_invalid" in _column_names(engine, "discovery_outcomes")


def test_run_all_migrations_sequentially() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    run_srdi_r8_migrations(engine=engine)
    assert "result_set_validations" in inspect(engine).get_table_names()
    assert "is_sponsored" in _column_names(engine, "gigs")
    assert "search_strictness_used" in _column_names(engine, "search_results")
    assert "scoring_method" in _column_names(engine, "keyword_scores")
    assert "ghost_market_flag" in _column_names(engine, "keywords")
    assert "is_invalid" in _column_names(engine, "discovery_outcomes")
    assert "zombie_score" in _column_names(engine, "gigs")
    assert "pages_collected" in _column_names(engine, "search_results")


def test_migration_m7_adds_zombie_and_pages_collected_columns() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m7.apply(engine)
    assert "zombie_score" in _column_names(engine, "gigs")
    assert "zombie_signals" in _column_names(engine, "gigs")
    assert "last_reviewed_at" in _column_names(engine, "gigs")
    assert "pages_collected" in _column_names(engine, "search_results")


def test_migration_m7_is_idempotent_and_rollback_safe() -> None:
    engine = _build_memory_engine()
    _bootstrap_base_tables(engine)
    m7.apply(engine)
    m7.apply(engine)
    m7.rollback(engine)
    assert "zombie_score" in _column_names(engine, "gigs")


def test_result_set_validation_model_is_importable() -> None:
    assert ResultSetValidation.__tablename__ == "result_set_validations"


def test_result_set_validation_model_creates_row(tmp_path: Path) -> None:
    db_path = tmp_path / "rsv_model.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    run_srdi_r8_migrations(engine=engine)
    session = sessionmaker(bind=engine, future=True)()
    niche = Niche(slug="srdi_r8_model", name="SRDI R8", category_path="programming")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=int(niche.id), keyword="rsv keyword", normalized_keyword="rsv keyword")
    session.add(keyword)
    session.flush()
    row = ResultSetValidation(keyword_id=int(keyword.id), run_id="srdi-r8-row", result_count=10, relevant_count=8)
    session.add(row)
    session.commit()
    saved_count = session.execute(text("SELECT COUNT(*) FROM result_set_validations")).scalar_one()
    assert saved_count == 1
    session.close()
