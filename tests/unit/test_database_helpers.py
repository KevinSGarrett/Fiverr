"""Targeted unit tests for database helper edge paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from src.models.database import (
    _ensure_cluster_assignments_table,
    _ensure_cluster_labels_table,
    _ensure_competitor_profiles_new_seller_gap_column,
    _ensure_competitor_profiles_table,
    _ensure_external_signal_tc1_columns,
    _ensure_gig_quality_analyses_table,
    _ensure_keyword_cluster_id_column,
    _ensure_keyword_intent_class_column,
    _ensure_review_analyses_table,
    _ensure_saturation_scores_table,
    _sqlite_path_from_url,
    drop_database_for_tests,
    get_db,
    initialize_database,
    normalize_database_url,
)


def test_normalize_database_url_and_sqlite_path_helpers() -> None:
    assert normalize_database_url("postgresql://localhost/fiverr") == "postgresql://localhost/fiverr"
    assert _sqlite_path_from_url("postgresql://localhost/fiverr") is None
    assert _sqlite_path_from_url("sqlite:///:memory:") is None
    assert _sqlite_path_from_url("sqlite:///data/test.sqlite3") == Path("data/test.sqlite3")
    with pytest.raises(ValueError):
        normalize_database_url("   ")


def test_ensure_keyword_intent_column_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"

    missing_keywords_inspector = MagicMock()
    missing_keywords_inspector.get_table_names.return_value = ["niches"]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: missing_keywords_inspector)
    _ensure_keyword_intent_class_column(engine)
    missing_keywords_inspector.get_columns.assert_not_called()

    has_column_inspector = MagicMock()
    has_column_inspector.get_table_names.return_value = ["keywords"]
    has_column_inspector.get_columns.return_value = [{"name": "id"}, {"name": "intent_class"}]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: has_column_inspector)
    _ensure_keyword_intent_class_column(engine)
    engine.begin.assert_not_called()


def test_ensure_keyword_intent_column_non_sqlite_noops() -> None:
    engine = MagicMock()
    engine.dialect.name = "postgresql"
    _ensure_keyword_intent_class_column(engine)
    engine.begin.assert_not_called()


def test_ensure_keyword_cluster_id_column_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"

    missing_keywords_inspector = MagicMock()
    missing_keywords_inspector.get_table_names.return_value = ["niches"]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: missing_keywords_inspector)
    _ensure_keyword_cluster_id_column(engine)
    missing_keywords_inspector.get_columns.assert_not_called()

    has_column_inspector = MagicMock()
    has_column_inspector.get_table_names.return_value = ["keywords"]
    has_column_inspector.get_columns.return_value = [{"name": "id"}, {"name": "cluster_id"}]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: has_column_inspector)
    _ensure_keyword_cluster_id_column(engine)
    engine.begin.assert_not_called()


def test_ensure_keyword_cluster_id_column_adds_column_and_swallows_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["keywords"]
    inspector.get_columns.return_value = [{"name": "id"}, {"name": "keyword"}]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: inspector)

    connection = MagicMock()

    class _BeginCtx:
        def __enter__(self):
            return connection

        def __exit__(self, *_args):
            return False

    engine.begin.return_value = _BeginCtx()
    _ensure_keyword_cluster_id_column(engine)
    connection.exec_driver_sql.assert_called_once_with("ALTER TABLE keywords ADD COLUMN cluster_id INTEGER")

    connection.exec_driver_sql.reset_mock()
    connection.exec_driver_sql.side_effect = RuntimeError("alter failed")
    _ensure_keyword_cluster_id_column(engine)


def test_ensure_backfill_tables_short_circuit_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"
    inspector = MagicMock()
    inspector.get_table_names.return_value = [
        "cluster_assignments",
        "cluster_labels",
        "competitor_profiles",
        "gig_quality_analyses",
        "review_analyses",
    ]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: inspector)

    _ensure_cluster_assignments_table(engine)
    _ensure_cluster_labels_table(engine)
    _ensure_competitor_profiles_table(engine)
    _ensure_gig_quality_analyses_table(engine)
    _ensure_review_analyses_table(engine)

    engine.begin.assert_not_called()


def test_ensure_backfill_tables_create_sql_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _make_engine() -> tuple[MagicMock, MagicMock]:
        engine = MagicMock()
        engine.dialect.name = "sqlite"
        inspector = MagicMock()
        inspector.get_table_names.return_value = []
        monkeypatch.setattr("src.models.database.inspect", lambda _engine: inspector)

        connection = MagicMock()

        class _BeginCtx:
            def __enter__(self):
                return connection

            def __exit__(self, *_args):
                return False

        engine.begin.return_value = _BeginCtx()
        return engine, connection

    for helper in (
        _ensure_cluster_assignments_table,
        _ensure_cluster_labels_table,
        _ensure_competitor_profiles_table,
        _ensure_gig_quality_analyses_table,
        _ensure_review_analyses_table,
    ):
        engine, connection = _make_engine()
        helper(engine)
        assert connection.exec_driver_sql.call_count >= 3


def test_ensure_competitor_profiles_new_seller_gap_column_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"

    missing_table_inspector = MagicMock()
    missing_table_inspector.get_table_names.return_value = ["keywords"]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: missing_table_inspector)
    _ensure_competitor_profiles_new_seller_gap_column(engine)
    missing_table_inspector.get_columns.assert_not_called()

    existing_column_inspector = MagicMock()
    existing_column_inspector.get_table_names.return_value = ["competitor_profiles"]
    existing_column_inspector.get_columns.return_value = [{"name": "id"}, {"name": "new_seller_gap"}]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: existing_column_inspector)
    _ensure_competitor_profiles_new_seller_gap_column(engine)
    engine.begin.assert_not_called()


def test_ensure_competitor_profiles_new_seller_gap_column_adds_and_swallow_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["competitor_profiles"]
    inspector.get_columns.return_value = [{"name": "id"}]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: inspector)

    connection = MagicMock()

    class _BeginCtx:
        def __enter__(self):
            return connection

        def __exit__(self, *_args):
            return False

    engine.begin.return_value = _BeginCtx()
    _ensure_competitor_profiles_new_seller_gap_column(engine)
    connection.exec_driver_sql.assert_called_once()

    connection.exec_driver_sql.reset_mock()
    connection.exec_driver_sql.side_effect = RuntimeError("alter failed")
    _ensure_competitor_profiles_new_seller_gap_column(engine)


def test_ensure_saturation_scores_table_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    sqlite_engine = MagicMock()
    sqlite_engine.dialect.name = "sqlite"
    sqlite_inspector = MagicMock()
    sqlite_inspector.get_table_names.return_value = ["saturation_scores"]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: sqlite_inspector)
    _ensure_saturation_scores_table(sqlite_engine)
    sqlite_engine.begin.assert_not_called()

    non_sqlite_engine = MagicMock()
    non_sqlite_engine.dialect.name = "postgresql"
    _ensure_saturation_scores_table(non_sqlite_engine)
    non_sqlite_engine.begin.assert_not_called()


def test_ensure_external_signal_tc1_columns_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    sqlite_engine = MagicMock()
    sqlite_engine.dialect.name = "sqlite"

    missing_table_inspector = MagicMock()
    missing_table_inspector.get_table_names.return_value = ["keywords"]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: missing_table_inspector)
    _ensure_external_signal_tc1_columns(sqlite_engine)
    missing_table_inspector.get_columns.assert_not_called()

    existing_columns_inspector = MagicMock()
    existing_columns_inspector.get_table_names.return_value = ["external_signals"]
    existing_columns_inspector.get_columns.return_value = [
        {"name": "id"},
        {"name": "raw_value"},
        {"name": "relevance_score"},
        {"name": "trend_direction"},
    ]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: existing_columns_inspector)
    _ensure_external_signal_tc1_columns(sqlite_engine)
    sqlite_engine.begin.assert_not_called()


def test_ensure_external_signal_tc1_columns_adds_missing_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["external_signals"]
    inspector.get_columns.return_value = [{"name": "id"}]
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: inspector)

    connection = MagicMock()

    class _BeginCtx:
        def __enter__(self):
            return connection

        def __exit__(self, *_args):
            return False

    engine.begin.return_value = _BeginCtx()

    _ensure_external_signal_tc1_columns(engine)

    executed = [call.args[0] for call in connection.exec_driver_sql.call_args_list]
    assert "ALTER TABLE external_signals ADD COLUMN raw_value REAL" in executed
    assert "ALTER TABLE external_signals ADD COLUMN relevance_score REAL" in executed
    assert "ALTER TABLE external_signals ADD COLUMN trend_direction VARCHAR(16)" in executed


def test_ensure_saturation_scores_table_creates_schema_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = MagicMock()
    engine.dialect.name = "sqlite"
    inspector = MagicMock()
    inspector.get_table_names.return_value = []
    monkeypatch.setattr("src.models.database.inspect", lambda _engine: inspector)
    connection = MagicMock()

    class _BeginCtx:
        def __enter__(self):
            return connection

        def __exit__(self, *_args):
            return False

    engine.begin.return_value = _BeginCtx()
    _ensure_saturation_scores_table(engine)
    assert connection.exec_driver_sql.call_count >= 4


def test_initialize_database_creates_parent_directories(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "dir" / "helpers.sqlite3"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    assert db_path.parent.exists()
    assert "helpers.sqlite3" in str(engine.url)


def test_drop_database_for_tests_rejects_unsafe_urls_and_removes_test_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError):
        drop_database_for_tests("sqlite:///data/prod.sqlite3")

    db_path = tmp_path / "pytest_drop.sqlite3"
    db_url = f"sqlite:///{db_path.as_posix()}"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("placeholder", encoding="utf-8")
    assert db_path.exists()

    # Avoid Windows sqlite file locks while still exercising unlink branch.
    monkeypatch.setattr("src.models.database.build_engine", lambda _url: object())
    monkeypatch.setattr("src.models.database.Base.metadata.drop_all", lambda _engine: None)
    drop_database_for_tests(db_url)
    assert not db_path.exists()


def test_get_db_uses_database_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    fake_engine = object()
    fake_factory = object()
    fake_session = object()

    class _SessionCtx:
        def __enter__(self) -> object:
            return fake_session

        def __exit__(self, *_args) -> None:
            return None

    def _fake_create_session_factory(engine: object) -> object:
        captured["factory_engine"] = engine
        return fake_factory

    def _fake_get_session(session_factory: object) -> _SessionCtx:
        captured["session_factory"] = session_factory
        return _SessionCtx()

    monkeypatch.setattr("src.models.database.build_engine", lambda database_url=None: fake_engine)
    monkeypatch.setattr("src.models.database.create_session_factory", _fake_create_session_factory)
    monkeypatch.setattr("src.models.database.get_session", _fake_get_session)

    with get_db("sqlite:///:memory:") as session:
        assert session is fake_session
    assert captured["factory_engine"] is fake_engine
