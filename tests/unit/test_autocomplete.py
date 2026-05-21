"""Unit tests for Workflow 8 autocomplete collection and model writes."""

from __future__ import annotations

import asyncio
import builtins
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from src.collection import autocomplete as autocomplete_module
from src.collection.fiverr_selectors import AUTOCOMPLETE_ITEM_TEXT
from src.collection.workflows import autocomplete as autocomplete_workflow_module
from src.collection.workflows.autocomplete import (
    AutocompleteWorkflow,
    build_autocomplete_search_url,
    enqueue_autocomplete_job,
    run_autocomplete_collection,
)
from src.models.job import Job
from src.models.market import AutocompleteSuggestion, Keyword, write_autocomplete_suggestion
from src.models.niche import Niche


def _run(coro):
    return asyncio.run(coro)


class _FakeTextNode:
    def __init__(self, text: str):
        self._text = text

    async def inner_text(self) -> str:
        return self._text


class _FakeItem:
    def __init__(self, text: str):
        self._text = text

    async def query_selector(self, selector: str):
        if selector == AUTOCOMPLETE_ITEM_TEXT:
            return _FakeTextNode(self._text)
        return None

    async def inner_text(self) -> str:
        return self._text


def _build_page_with_suggestions(suggestions: list[str]) -> AsyncMock:
    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[_FakeItem(text) for text in suggestions])
    page.query_selector = AsyncMock(return_value=None)
    page.keyboard = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.close = AsyncMock()
    return page


def _build_managers(page: AsyncMock) -> tuple[AsyncMock, AsyncMock]:
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    session_manager.close_page = AsyncMock()

    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()
    return session_manager, pacing_manager


def _make_keyword_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    AutocompleteSuggestion.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()

    niche = Niche(slug="ai-saas", name="AI SaaS", category_path="programming-tech/ai-saas")
    db.add(niche)
    db.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="logo design",
        normalized_keyword="logo design",
    )
    db.add(keyword)
    db.commit()
    return db, keyword.id


def test_w8_real_navigates_to_fiverr() -> None:
    page = _build_page_with_suggestions(["one"])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="logo design",
                niche_id="ai_saas",
                run_id="run-w8-1",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    page.goto.assert_awaited_once_with(
        build_autocomplete_search_url("logo design"),
        wait_until="domcontentloaded",
        timeout=30_000,
    )


def test_w8_real_collects_suggestions() -> None:
    page = _build_page_with_suggestions(["one", "two", "three", "four", "five"])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion") as write_mock:
        result = _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-w8-2",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    assert result["collected"] is True
    assert result["suggestions_collected"] == 5
    assert write_mock.call_count == 5


def test_w8_real_caps_at_10_suggestions() -> None:
    page = _build_page_with_suggestions([f"suggestion {i}" for i in range(15)])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        result = _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-w8-3",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    assert result["suggestions_collected"] == 10


def test_w8_real_records_position() -> None:
    page = _build_page_with_suggestions([f"suggestion {i}" for i in range(10)])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion") as write_mock:
        _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-w8-4",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    positions = [call.kwargs["position"] for call in write_mock.call_args_list]
    assert positions == list(range(1, 11))


def test_w8_real_calls_pacing() -> None:
    page = _build_page_with_suggestions(["one"])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-w8-5",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    pacing_manager.wait.assert_awaited_once_with("fiverr_search", dry_run=False)


def test_w8_real_handles_timeout() -> None:
    page = _build_page_with_suggestions(["one"])
    page.goto.side_effect = TimeoutError("timeout")
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        with pytest.raises(TimeoutError, match="timeout"):
            _run(
                run_autocomplete_collection(
                    keyword_id=1,
                    keyword_text="keyword",
                    niche_id="ai_saas",
                    run_id="run-w8-6",
                    session_manager=session_manager,
                    pacing_manager=pacing_manager,
                    db=object(),
                    dry_run=False,
                )
            )
    assert pacing_manager.wait.await_count == 1


def test_w8_real_reraises_on_exception() -> None:
    page = _build_page_with_suggestions(["one"])
    page.goto.side_effect = RuntimeError("boom")
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        with pytest.raises(RuntimeError, match="boom"):
            _run(
                run_autocomplete_collection(
                    keyword_id=1,
                    keyword_text="keyword",
                    niche_id="ai_saas",
                    run_id="run-w8-reraise",
                    session_manager=session_manager,
                    pacing_manager=pacing_manager,
                    db=object(),
                    dry_run=False,
                )
            )
    session_manager.close_page.assert_awaited_once_with(page)


def test_w8_dry_run_still_returns_error_dict() -> None:
    result = _run(
        run_autocomplete_collection(
            keyword_id=1,
            keyword_text="keyword",
            niche_id="ai_saas",
            run_id="run-w8-dry-reraise",
            session_manager=None,
            pacing_manager=None,
            db=None,
            dry_run=True,
        )
    )
    assert isinstance(result, dict)
    assert result["dry_run"] is True
    assert result["collected"] is False
    assert result["suggestions_collected"] == 0


def test_w8_real_closes_page_on_success() -> None:
    page = _build_page_with_suggestions(["one"])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-w8-7",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    session_manager.close_page.assert_awaited_once_with(page)


def test_w8_real_closes_page_on_error() -> None:
    page = _build_page_with_suggestions(["one"])
    page.goto.side_effect = RuntimeError("boom")
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        with pytest.raises(RuntimeError, match="boom"):
            _run(
                run_autocomplete_collection(
                    keyword_id=1,
                    keyword_text="keyword",
                    niche_id="ai_saas",
                    run_id="run-w8-8",
                    session_manager=session_manager,
                    pacing_manager=pacing_manager,
                    db=object(),
                    dry_run=False,
                )
            )
    session_manager.close_page.assert_awaited_once_with(page)


def test_w8_real_writes_to_db() -> None:
    page = _build_page_with_suggestions(["one", "two", "three"])
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion") as write_mock:
        _run(
            run_autocomplete_collection(
                keyword_id=99,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-w8-9",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    assert write_mock.call_count == 3
    assert write_mock.call_args_list[0].kwargs["keyword_id"] == 99
    assert write_mock.call_args_list[0].kwargs["run_id"] == "run-w8-9"


def test_w8_dry_run_does_not_crash() -> None:
    result = _run(
        run_autocomplete_collection(
            keyword_id=1,
            keyword_text="keyword",
            niche_id="ai_saas",
            run_id="run-w8-10",
            session_manager=None,
            pacing_manager=None,
            db=None,
            dry_run=True,
        )
    )
    assert result["dry_run"] is True
    assert result["collected"] is False
    assert result["suggestions_collected"] == 0


def test_autocomplete_suggestion_model() -> None:
    db, keyword_id = _make_keyword_session()
    try:
        row = AutocompleteSuggestion(
            keyword_id=keyword_id,
            niche_id="ai_saas",
            suggestion_text="logo design package",
            position=1,
            run_id="run-model",
            source="fiverr_autocomplete",
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        assert row.id is not None
        assert row.position == 1
        assert row.suggestion_text == "logo design package"
    finally:
        db.close()


def test_write_autocomplete_suggestion() -> None:
    db, keyword_id = _make_keyword_session()
    try:
        row = write_autocomplete_suggestion(
            keyword_id=keyword_id,
            niche_id="ai_saas",
            suggestion_text="logo design package",
            position=1,
            run_id="run-write",
            db=db,
        )
        assert row is not None
        assert row.keyword_id == keyword_id
        assert row.run_id == "run-write"
    finally:
        db.close()


def test_write_autocomplete_suggestion_non_session_returns_none() -> None:
    row = write_autocomplete_suggestion(
        keyword_id=1,
        niche_id="ai_saas",
        suggestion_text="logo design package",
        position=1,
        run_id="run-non-session",
        db=object(),
    )
    assert row is None


def test_write_autocomplete_suggestion_blank_text_returns_none() -> None:
    db, keyword_id = _make_keyword_session()
    try:
        row = write_autocomplete_suggestion(
            keyword_id=keyword_id,
            niche_id="ai_saas",
            suggestion_text="   ",
            position=1,
            run_id="run-blank",
            db=db,
        )
        assert row is None
    finally:
        db.close()


def test_write_autocomplete_suggestion_integrity_error_without_row_returns_none(monkeypatch) -> None:
    db, keyword_id = _make_keyword_session()

    class _FakeQuery:
        def __init__(self) -> None:
            self.calls = 0

        def filter(self, *args: object) -> _FakeQuery:
            _ = args
            return self

        def one_or_none(self) -> None:
            self.calls += 1
            return None

    fake_query = _FakeQuery()

    def _fake_query(*args: object, **kwargs: object) -> _FakeQuery:
        _ = (args, kwargs)
        return fake_query

    def _raise_integrity_error() -> None:
        raise IntegrityError("INSERT INTO autocomplete_suggestions ...", {}, RuntimeError("duplicate"))

    monkeypatch.setattr(db, "query", _fake_query)
    monkeypatch.setattr(db, "commit", _raise_integrity_error)

    row = write_autocomplete_suggestion(
        keyword_id=keyword_id,
        niche_id="ai_saas",
        suggestion_text="logo design package",
        position=1,
        run_id="run-integrity-path",
        db=db,
    )
    assert row is None
    assert fake_query.calls == 2
    db.close()


def test_w8_model_write_unique_constraint() -> None:
    db, keyword_id = _make_keyword_session()
    try:
        first = write_autocomplete_suggestion(
            keyword_id=keyword_id,
            niche_id="ai_saas",
            suggestion_text="logo design package",
            position=1,
            run_id="run-unique",
            db=db,
        )
        second = write_autocomplete_suggestion(
            keyword_id=keyword_id,
            niche_id="ai_saas",
            suggestion_text="logo design package",
            position=2,
            run_id="run-unique",
            db=db,
        )
        count = db.query(AutocompleteSuggestion).count()

        assert first is not None
        assert second is not None
        assert count == 1
        assert second.position == 2
    finally:
        db.close()


def test_enqueue_autocomplete_job_creates_job() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE run_logs (run_id VARCHAR(64) PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE niche_configs (niche_id VARCHAR(64) PRIMARY KEY)"))
        conn.execute(text("INSERT INTO run_logs(run_id) VALUES ('run-queue')"))
        conn.execute(text("INSERT INTO niche_configs(niche_id) VALUES ('ai_saas')"))
    Job.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()
    try:
        created = enqueue_autocomplete_job(
            keyword_id=42,
            keyword_text="logo design",
            niche_id="ai_saas",
            run_id="run-queue",
            db=db,
        )
        row = db.query(Job).one()
        assert created is True
        assert row.job_type == "AUTOCOMPLETE"
        assert row.stage == 8
        assert row.status == "QUEUED"
        assert row.payload == {
            "keyword_id": 42,
            "keyword_text": "logo design",
            "niche_id": "ai_saas",
        }
    finally:
        db.close()


def test_w8_real_handles_missing_session_manager() -> None:
    result = _run(
        run_autocomplete_collection(
            keyword_id=1,
            keyword_text="keyword",
            niche_id="ai_saas",
            run_id="run-no-session",
            session_manager=None,
            pacing_manager=AsyncMock(),
            db=object(),
            dry_run=False,
        )
    )
    assert result["collected"] is False
    assert result["error"] == "session_manager_unavailable"


def test_w8_real_extracts_via_search_box_fallback() -> None:
    page = _build_page_with_suggestions([])
    page.query_selector_all = AsyncMock(
        side_effect=[[], [_FakeItem("fallback one"), _FakeItem("fallback two")]]
    )
    search_box = AsyncMock()
    search_box.click = AsyncMock()
    page.query_selector = AsyncMock(return_value=search_box)
    session_manager, pacing_manager = _build_managers(page)
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        result = _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-fallback",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    assert result["suggestions_collected"] == 2
    search_box.click.assert_awaited_once()
    page.keyboard.type.assert_awaited_once_with("keyword", delay=100)


def test_w8_real_uses_page_close_when_manager_missing_close_page() -> None:
    page = _build_page_with_suggestions(["one"])
    session_manager = AsyncMock(spec=["new_page"])
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-page-close",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    page.close.assert_awaited_once()


def test_w8_real_ignores_close_errors() -> None:
    page = _build_page_with_suggestions(["one"])
    session_manager, pacing_manager = _build_managers(page)
    session_manager.close_page = AsyncMock(side_effect=RuntimeError("close failed"))
    with patch("src.collection.workflows.autocomplete.write_autocomplete_suggestion"):
        result = _run(
            run_autocomplete_collection(
                keyword_id=1,
                keyword_text="keyword",
                niche_id="ai_saas",
                run_id="run-close-error",
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                db=object(),
                dry_run=False,
            )
        )
    assert result["collected"] is True


def test_safe_pacing_wait_without_wait_method() -> None:
    _run(autocomplete_workflow_module._safe_pacing_wait(object(), dry_run=False))


def test_checkpoint_write_primary_signature() -> None:
    checkpoint_manager = AsyncMock()
    checkpoint_manager.write = AsyncMock(return_value=None)
    _run(
        autocomplete_workflow_module._write_stage08_checkpoint(
            checkpoint_manager,
            keyword_id=1,
            niche_id="ai_saas",
            suggestions_collected=2,
            collected=True,
        )
    )
    checkpoint_manager.write.assert_awaited_once_with(
        "stage08",
        "ai_saas",
        {"keyword_id": 1, "suggestions_collected": 2, "collected": True},
    )


def test_checkpoint_write_legacy_signature() -> None:
    class _LegacyCheckpoint:
        def __init__(self) -> None:
            self.calls: list[tuple[object, ...]] = []

        def write(self, *args: object) -> None:
            self.calls.append(args)
            if args and args[0] == "stage08":
                raise TypeError("legacy signature")

    checkpoint_manager = _LegacyCheckpoint()
    _run(
        autocomplete_workflow_module._write_stage08_checkpoint(
            checkpoint_manager,
            keyword_id=9,
            niche_id="ai_saas",
            suggestions_collected=3,
            collected=True,
        )
    )
    assert checkpoint_manager.calls[0] == (
        "stage08",
        "ai_saas",
        {"keyword_id": 9, "suggestions_collected": 3, "collected": True},
    )
    assert checkpoint_manager.calls[1] == (
        "9",
        "stage08_autocomplete_ai_saas",
        {"keyword_id": 9, "suggestions_collected": 3, "collected": True},
    )


def test_checkpoint_write_exception_path() -> None:
    class _BrokenCheckpoint:
        def write(self, *args: object) -> None:
            _ = args
            raise RuntimeError("boom")

    _run(
        autocomplete_workflow_module._write_stage08_checkpoint(
            _BrokenCheckpoint(),
            keyword_id=1,
            niche_id="ai_saas",
            suggestions_collected=0,
            collected=False,
        )
    )


def test_checkpoint_write_with_missing_write_fn() -> None:
    class _NoWriteCheckpoint:
        write = None

    _run(
        autocomplete_workflow_module._write_stage08_checkpoint(
            _NoWriteCheckpoint(),
            keyword_id=1,
            niche_id="ai_saas",
            suggestions_collected=0,
            collected=False,
        )
    )


def test_checkpoint_write_legacy_signature_awaitable_path() -> None:
    class _LegacyAwaitableCheckpoint:
        def __init__(self) -> None:
            self.calls: list[tuple[object, ...]] = []

        def write(self, *args: object):
            self.calls.append(args)
            if args and args[0] == "stage08":
                raise TypeError("legacy signature")

            async def _done() -> None:
                return None

            return _done()

    checkpoint_manager = _LegacyAwaitableCheckpoint()
    _run(
        autocomplete_workflow_module._write_stage08_checkpoint(
            checkpoint_manager,
            keyword_id=4,
            niche_id="ai_saas",
            suggestions_collected=2,
            collected=True,
        )
    )
    assert len(checkpoint_manager.calls) == 2
    assert checkpoint_manager.calls[1][0] == "4"


def test_enqueue_autocomplete_job_non_session_returns_false() -> None:
    created = enqueue_autocomplete_job(
        keyword_id=1,
        keyword_text="keyword",
        niche_id="ai_saas",
        run_id="run-non-session",
        db={},
    )
    assert created is False


def test_enqueue_autocomplete_job_import_error_returns_false(monkeypatch) -> None:
    original_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object):
        if name == "sqlalchemy.orm":
            raise ImportError("forced")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    created = enqueue_autocomplete_job(
        keyword_id=1,
        keyword_text="keyword",
        niche_id="ai_saas",
        run_id="run-import-error",
        db=object(),
    )
    assert created is False


def test_autocomplete_workflow_wrapper_returns_legacy_module() -> None:
    assert AutocompleteWorkflow().run() is autocomplete_module
