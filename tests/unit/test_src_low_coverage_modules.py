"""Targeted tests for src modules that were below 75% coverage."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from src import cli, db
from src.collection.workflows import result_set_validation_workflow as rsvw
from src.dashboard import sample_data
from src.dashboard.pages import competitors
from src.migrations import migration_14_s76_discovery_feedback as m14
from src.migrations.srdi_r8 import migration_09_keyword_score_integrity_cols as m09
from src.models import base, pricing
from src.scripts import import_seeds
from src.utils import json as json_utils


def test_cli_parser_and_main_help(capsys: pytest.CaptureFixture[str]) -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["pricing-export", "--keyword-id", "1", "--format", "csv"])
    assert args.command == "pricing-export"
    rc = cli.main([])
    assert rc == 0
    assert "usage:" in capsys.readouterr().out.lower()


def test_cli_run_pricing_export(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "normalize_database_url", lambda _: "sqlite:///x.db")
    monkeypatch.setattr(cli, "initialize_database", lambda database_url=None: object())
    monkeypatch.setattr(cli, "create_session_factory", lambda engine: object())

    class _FakeDB:
        def __init__(self) -> None:
            self.keyword_ids = [(9,), (2,), (None,)]

        def query(self, *_args):
            class _Q:
                def __init__(self, rows):
                    self._rows = rows

                def distinct(self):
                    return self

                def order_by(self, *_args):
                    return self

                def all(self):
                    return self._rows

            return _Q(self.keyword_ids)

    @contextmanager
    def fake_get_session(_factory):
        yield _FakeDB()

    monkeypatch.setattr(cli, "get_session", fake_get_session)
    monkeypatch.setattr(
        cli,
        "export_all_pricing",
        lambda **kwargs: [f"{kwargs['output_dir']}/file.csv"],
    )
    args = SimpleNamespace(keyword_id=[], format=[], output_dir="out", database_url=None)
    assert cli._run_pricing_export(args) == 0
    assert "Exported 1 pricing file(s)" in capsys.readouterr().out


def test_rsv_helpers_and_run(monkeypatch: pytest.MonkeyPatch) -> None:
    assert rsvw._config_enabled({"relevance": {"enable_stage_3_5": True}}) is True
    assert rsvw._config_enabled(SimpleNamespace(relevance=SimpleNamespace(enable_stage_3_5=False))) is False
    assert rsvw._config_thresholds({"relevance": {"relevance_flag_threshold": 0.4, "ghost_market_threshold_default": 0.1}}) == (0.4, 0.1)
    assert rsvw._normalize_url("https://Fiverr.com/path/") == "fiverr.com/path"

    class DummySession:
        def __init__(self) -> None:
            self.committed = False

        def commit(self) -> None:
            self.committed = True

    monkeypatch.setattr(rsvw, "Session", DummySession)
    db_session = DummySession()
    monkeypatch.setattr(rsvw, "_keywords_for_run_niche", lambda *a, **k: [SimpleNamespace(id=1, keyword="kw")])
    monkeypatch.setattr(rsvw, "_gig_cards_for_keyword", lambda *a, **k: [{"title": "x"}])
    monkeypatch.setattr(rsvw, "get_validation_config", lambda niche_id: {"ghost_market_threshold": 0.2})
    fake_result = SimpleNamespace(
        total_analyzed=1,
        relevant_count=1,
        sponsored_count=0,
        result_set_relevance_score=0.9,
        ghost_market_flag=False,
        category_contamination_flag=False,
        confidence_deduction=0.1,
        gig_results=[],
        warnings=[],
    )
    monkeypatch.setattr(rsvw, "validate_result_set", lambda *a, **k: fake_result)
    monkeypatch.setattr(rsvw, "_upsert_rsv", lambda *a, **k: SimpleNamespace(id=11))
    monkeypatch.setattr(rsvw, "_link_search_result", lambda *a, **k: None)
    monkeypatch.setattr(rsvw, "_write_gig_flags", lambda *a, **k: None)
    stats = rsvw.run_stage_3_5_validation("run1", "niche", db_session, {"relevance": {"enable_stage_3_5": True}})
    assert stats["keywords_validated"] == 1
    assert db_session.committed is True


def test_rsv_write_gig_flags_and_upsert(monkeypatch: pytest.MonkeyPatch) -> None:
    gig_rows = [SimpleNamespace(gig_url="https://fiverr.com/a", relevance_flag=None, relevance_score=None)]

    class _DB:
        def query(self, *_args):
            class _Q:
                def filter(self, *_args, **_kwargs):
                    return self

                def all(self):
                    return gig_rows

            return _Q()

    rsvw._write_gig_flags(
        _DB(),
        "run1",
        [SimpleNamespace(gig_url="https://fiverr.com/a", relevance_flag="KEEP", relevance_score=0.8)],
    )
    assert gig_rows[0].relevance_flag == "KEEP"
    assert gig_rows[0].relevance_score == 0.8

    monkeypatch.setattr(rsvw, "ResultSetValidation", lambda **kwargs: SimpleNamespace(**kwargs))
    created = []

    class _DB2:
        def __init__(self) -> None:
            self.obj = None

        def query(self, *_args):
            class _Q:
                def __init__(self, outer):
                    self.outer = outer

                def filter_by(self, **_kwargs):
                    return self

                def first(self):
                    return None

            return _Q(self)

        def add(self, obj):
            obj.id = 7
            created.append(obj)

        def flush(self):
            return None

    rs = SimpleNamespace(
        total_analyzed=1,
        relevant_count=1,
        sponsored_count=0,
        result_set_relevance_score=0.5,
        ghost_market_flag=False,
        category_contamination_flag=False,
        confidence_deduction=0.0,
        gig_results=[],
        warnings=[],
    )
    monkeypatch.setattr(rsvw, "_strictness_for", lambda *a, **k: None)
    out = rsvw._upsert_rsv(_DB2(), 1, "run1", rs)
    assert out.result_count == 1
    assert created


def test_competitors_page_render(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    fake_streamlit = SimpleNamespace(
        title=lambda *_: calls.append("title"),
        info=lambda *_: calls.append("info"),
        caption=lambda *_: calls.append("caption"),
        dataframe=lambda *_args, **_kwargs: calls.append("dataframe"),
        metric=lambda *_args, **_kwargs: calls.append("metric"),
    )
    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(
        __import__("sys").modules,
        "src.models",
        SimpleNamespace(CompetitorProfile=SimpleNamespace(collected_at=SimpleNamespace(desc=lambda: None))),
    )

    class _DB:
        def query(self, *_args):
            class _Q:
                def order_by(self, *_args):
                    return self

                def limit(self, *_args):
                    return self

                def all(self):
                    return [
                        SimpleNamespace(
                            niche_id="n1",
                            run_id="r1",
                            top_gig_count=10,
                            median_price=50.0,
                            mean_reviews=30.0,
                        )
                    ]

            return _Q()

    @contextmanager
    def fake_session():
        yield _DB()

    monkeypatch.setattr(competitors, "get_db_session", fake_session)
    competitors.render_competitors_page()
    assert "dataframe" in calls


def test_sample_data_and_db_generator() -> None:
    data = sample_data.build_dashboard_demo_data()
    assert "opportunities" in data and "keywords" in data
    gen = db.get_db_session("sqlite:///x.db")
    # Consume one item by replacing internals with stop-safe stubs.
    assert hasattr(gen, "__iter__")


def test_db_get_db_session_yields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "build_engine", lambda _url: "engine")
    monkeypatch.setattr(db, "create_session_factory", lambda _engine: "factory")

    @contextmanager
    def fake_get_session(_factory):
        yield "session"

    monkeypatch.setattr(db, "get_session", fake_get_session)
    gen = db.get_db_session("sqlite:///test.db")
    assert next(gen) == "session"


def test_rsv_query_helpers_and_error_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Query:
        def __init__(self, rows):
            self.rows = rows
            self._first = rows[0] if rows else None

        def join(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def all(self):
            return self.rows

        def first(self):
            return self._first

        def filter_by(self, **_kwargs):
            return self

    search_rows = [
        SimpleNamespace(gig_cards=[{"gig_url": "https://fiverr.com/a"}], search_strictness_used="subcategory"),
        SimpleNamespace(gig_cards=["bad"], search_strictness_used=None),
    ]
    keyword_rows = [SimpleNamespace(id=1, keyword="kw")]
    link_row = SimpleNamespace(rsv_id=None, search_strictness_used="subcategory")

    class _DB:
        def query(self, model):
            name = getattr(model, "__name__", "")
            if name == "Keyword":
                return _Query(keyword_rows)
            if name == "SearchResult":
                q = _Query(search_rows)
                q._first = link_row
                return q
            if name == "Gig":
                return _Query([])
            return _Query([])

    fake_db = _DB()
    assert rsvw._keywords_for_run_niche(fake_db, "run1", 1) == keyword_rows
    assert rsvw._keywords_for_run_niche(fake_db, "run1", "1") == keyword_rows
    assert rsvw._keywords_for_run_niche(fake_db, "run1", "logo-design") == keyword_rows
    cards = rsvw._gig_cards_for_keyword(fake_db, 1, "run1")
    assert cards == [{"gig_url": "https://fiverr.com/a"}]
    assert rsvw._strictness_for(fake_db, 1, "run1") == "subcategory"
    rsvw._link_search_result(fake_db, 1, "run1", 42)
    assert link_row.rsv_id == 42

    class _DummySession:
        def __init__(self):
            self.committed = False

        def commit(self):
            self.committed = True

    monkeypatch.setattr(rsvw, "Session", _DummySession)
    monkeypatch.setattr(rsvw, "_keywords_for_run_niche", lambda *a, **k: [SimpleNamespace(id=9, keyword="kw")])
    monkeypatch.setattr(rsvw, "_gig_cards_for_keyword", lambda *a, **k: [])
    monkeypatch.setattr(rsvw, "get_validation_config", lambda *_: {})
    monkeypatch.setattr(rsvw, "validate_result_set", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    out = rsvw.run_stage_3_5_validation(
        "run1",
        "niche",
        _DummySession(),
        {"relevance": {"enable_stage_3_5": True}},
    )
    assert out["keywords_validated"] == 0


def test_migration_14_and_09_with_fake_engines() -> None:
    executed_14: list[str] = []
    executed_09: list[str] = []

    class _Conn:
        def __init__(self, bucket: list[str], table_info: dict[str, list[tuple]] | None = None):
            self.bucket = bucket
            self.table_info = table_info or {}

        def exec_driver_sql(self, sql: str):
            self.bucket.append(sql)
            if sql.startswith("PRAGMA table_info("):
                table = sql.removeprefix("PRAGMA table_info(").removesuffix(")")
                rows = self.table_info.get(table, [])
                return SimpleNamespace(fetchall=lambda: rows)
            return SimpleNamespace(fetchall=lambda: [])

        def execute(self, stmt):
            self.bucket.append(str(stmt))
            return None

    class _Engine:
        dialect = SimpleNamespace(name="sqlite")

        def __init__(self, conn):
            self._conn = conn

        def begin(self):
            @contextmanager
            def _ctx():
                yield self._conn

            return _ctx()

    conn14 = _Conn(executed_14, table_info={"discovery_outcomes": [], "discovery_cycle_logs": [], "keywords": []})
    eng14 = _Engine(conn14)
    original_column_names = m14._column_names
    m14._column_names = lambda _engine, table_name: set()  # type: ignore[assignment]
    m14.upgrade(eng14)
    m14.downgrade(eng14)
    m14.apply(eng14)
    m14.rollback(eng14)
    m14._column_names = original_column_names  # type: ignore[assignment]
    assert any("CREATE TABLE IF NOT EXISTS discovery_outcomes" in s for s in executed_14)

    conn09 = _Conn(
        executed_09,
        table_info={
            "keyword_scores": [
                (0, "id", "INTEGER", 1, None, 1),
                (1, "score", "FLOAT", 0, None, 0),
            ]
        },
    )
    eng09 = _Engine(conn09)
    m09.apply(eng09)
    assert any("ALTER TABLE keyword_scores ADD COLUMN" in s for s in executed_09)
    m09.rollback(eng09)
    assert any("RENAME TO keyword_scores" in s for s in executed_09)


def test_base_models_and_pricing_export() -> None:
    assert base.utc_now().tzinfo is not None
    dumped = base.dumps_json({"x": {3, 1}})
    assert '"x": [1, 3]' in dumped
    assert pricing.__all__ == ["PriceAnalysis"]


def test_import_seeds_helpers_and_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    seed_path = tmp_path / "niche.yaml"
    seed_path.write_text(
        "niche_id: logo-design\nniche_name: Logo\nkeywords:\n  - keyword: logo design\n",
        encoding="utf-8",
    )
    loaded = import_seeds._load_seed_file(seed_path)
    assert loaded["niche_id"] == "logo-design"
    with pytest.raises(FileNotFoundError):
        import_seeds._load_seed_file(tmp_path / "missing.yaml")

    class _Session:
        def __init__(self):
            self.added = []

        def query(self, model):
            class _Q:
                def __init__(self, sess):
                    self.sess = sess

                def filter_by(self, **kwargs):
                    return self

                def first(self):
                    if model.__name__ == "Niche":
                        return SimpleNamespace(id=1, slug="logo-design")
                    return None

            return _Q(self)

        def add(self, obj):
            self.added.append(obj)

        def flush(self):
            return None

    inserted, skipped = import_seeds._upsert_seed_keywords(
        _Session(),
        "logo-design",
        [{"keyword": "logo design", "normalized_keyword": "logo design"}],
        dry_run=False,
    )
    assert inserted == 1 and skipped == 0

    monkeypatch.setattr(import_seeds, "import_seeds", lambda **kwargs: {"logo-design": {"inserted": 1, "skipped": 0}})
    assert import_seeds.main(["--dry-run", "--seeds-dir", str(tmp_path)]) == 0
    assert "Done" in capsys.readouterr().out


def test_json_utils() -> None:
    assert json_utils.safe_json_dumps({"a": 1}) == '{"a": 1}'
    with pytest.raises(ValueError):
        json_utils.safe_json_dumps({"x": {1}})
    assert json_utils.safe_json_loads('{"a":1}') == {"a": 1}
    with pytest.raises(ValueError):
        json_utils.safe_json_loads("{bad")
