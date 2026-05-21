"""Unit tests for Workflow 8 YouTube count collection."""
from __future__ import annotations

import asyncio
import re
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock, call

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.collection import orchestrator as collection_orchestrator
from src.collection.workflows import youtube_count as youtube_count_module
from src.models import Keyword, Niche


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse | None = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error

    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)
        return None

    async def get(self, *_args: Any, **_kwargs: Any) -> _FakeResponse:
        if self._error is not None:
            raise self._error
        if self._response is None:
            raise RuntimeError("missing response")
        return self._response


def _make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, future=True)()


def test_youtube_fetch_returns_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_count_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            response=_FakeResponse("<html>About 12,345 results</html>")
        ),
    )
    pacing = SimpleNamespace(wait=AsyncMock())

    result = _run(youtube_count_module._fetch_youtube_count("ai agents", pacing))

    assert result == 12345
    pacing.wait.assert_awaited_once_with("youtube", dry_run=False)


def test_youtube_fetch_none_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_count_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=RuntimeError("network down")),
    )
    pacing = SimpleNamespace(wait=AsyncMock())

    result = _run(youtube_count_module._fetch_youtube_count("ai agents", pacing))

    assert result is None


def test_youtube_real_calls_pacing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_count_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response=_FakeResponse("About 123 results")),
    )
    monkeypatch.setattr(youtube_count_module, "_resolve_keyword_id", Mock(return_value=1))
    monkeypatch.setattr(youtube_count_module, "write_external_signal", Mock())
    pacing = SimpleNamespace(wait=AsyncMock())

    _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-1",
            seed_keywords=["alpha"],
            run_id="run-youtube-1",
            db=object(),
            pacing_manager=pacing,
            dry_run=False,
        )
    )

    pacing.wait.assert_awaited_once_with("youtube", dry_run=False)


def test_youtube_real_writes_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(youtube_count_module, "_fetch_youtube_count", AsyncMock(return_value=345))
    monkeypatch.setattr(youtube_count_module, "_resolve_keyword_id", Mock(return_value=77))
    write_mock = Mock()
    monkeypatch.setattr(youtube_count_module, "write_external_signal", write_mock)

    result = _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-2",
            seed_keywords=["alpha"],
            run_id="run-youtube-2",
            db=object(),
            pacing_manager=SimpleNamespace(wait=AsyncMock()),
            dry_run=False,
        )
    )

    assert result["signals_written"] == 1
    assert write_mock.call_count == 1
    assert write_mock.call_args.kwargs["signal_type"] == youtube_count_module.SIGNAL_YOUTUBE_COUNT
    assert write_mock.call_args.kwargs["signal_value"] == 345.0


def test_youtube_real_scoped_keyword_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(youtube_count_module, "_fetch_youtube_count", AsyncMock(return_value=10))
    resolve_mock = Mock(side_effect=[101, None])
    write_mock = Mock()
    db_token = object()
    monkeypatch.setattr(youtube_count_module, "_resolve_keyword_id", resolve_mock)
    monkeypatch.setattr(youtube_count_module, "write_external_signal", write_mock)

    _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-x",
            seed_keywords=["alpha", "beta"],
            run_id="run-youtube-3",
            db=db_token,
            pacing_manager=SimpleNamespace(wait=AsyncMock()),
            dry_run=False,
        )
    )

    assert resolve_mock.call_args_list == [
        call("alpha", "niche-x", db_token),
        call("beta", "niche-x", db_token),
    ]
    assert write_mock.call_count == 1


def test_youtube_dry_run_does_not_write(monkeypatch: pytest.MonkeyPatch) -> None:
    write_mock = Mock()
    monkeypatch.setattr(youtube_count_module, "write_external_signal", write_mock)

    result = _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-3",
            seed_keywords=["alpha"],
            run_id="run-youtube-4",
            db=object(),
            pacing_manager=SimpleNamespace(wait=AsyncMock()),
            dry_run=True,
        )
    )

    assert result["dry_run"] is True
    assert result["signals_written"] == 0
    write_mock.assert_not_called()


def test_youtube_handles_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(youtube_count_module, "_fetch_youtube_count", AsyncMock(return_value=None))
    monkeypatch.setattr(youtube_count_module, "_resolve_keyword_id", Mock(return_value=88))
    write_mock = Mock()
    monkeypatch.setattr(youtube_count_module, "write_external_signal", write_mock)

    result = _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-4",
            seed_keywords=["alpha"],
            run_id="run-youtube-5",
            db=object(),
            pacing_manager=SimpleNamespace(wait=AsyncMock()),
            dry_run=False,
        )
    )

    assert result["signals_written"] == 1
    assert write_mock.call_args.kwargs["signal_value"] is None


def test_youtube_stage_registered_in_pipeline() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-youtube-stage",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )

    assert "stage06c_youtube_count" in result["stages_run"]


def test_parse_youtube_result_count_handles_invalid_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_count_module,
        "_RESULT_COUNT_PATTERNS",
        (re.compile(r"(invalid-number)"),),
    )
    assert youtube_count_module.parse_youtube_result_count("invalid-number") is None


def test_safe_pacing_wait_without_wait_method() -> None:
    _run(youtube_count_module._safe_pacing_wait(object(), "youtube"))


def test_fetch_blank_seed_returns_none() -> None:
    assert _run(youtube_count_module._fetch_youtube_count("   ", SimpleNamespace(wait=AsyncMock()))) is None


def test_fetch_logs_warning_when_parse_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_count_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response=_FakeResponse("<html>no count</html>")),
    )
    warning_mock = Mock()
    monkeypatch.setattr(youtube_count_module.logger, "warning", warning_mock)

    result = _run(
        youtube_count_module._fetch_youtube_count(
            "alpha",
            SimpleNamespace(wait=AsyncMock()),
        )
    )

    assert result is None
    assert warning_mock.call_count >= 1


def test_fetch_ignores_pacing_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        youtube_count_module.httpx,
        "AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response=_FakeResponse("About 100 results")),
    )
    debug_mock = Mock()
    monkeypatch.setattr(youtube_count_module.logger, "debug", debug_mock)
    pacing = SimpleNamespace(wait=AsyncMock(side_effect=RuntimeError("pacing boom")))

    result = _run(youtube_count_module._fetch_youtube_count("alpha", pacing))

    assert result == 100
    debug_mock.assert_called_once()


def test_resolve_niche_pk_and_keyword_id() -> None:
    db = _make_session()
    try:
        niche = Niche(slug="niche-alpha", name="Niche Alpha", category_path="cat/alpha")
        db.add(niche)
        db.commit()
        db.refresh(niche)
        keyword = Keyword(
            niche_id=int(niche.id),
            keyword="Shared Keyword",
            normalized_keyword="shared keyword",
        )
        db.add(keyword)
        db.commit()
        db.refresh(keyword)

        assert youtube_count_module._resolve_niche_pk(str(niche.id), db) == int(niche.id)
        assert youtube_count_module._resolve_niche_pk("niche-alpha", db) == int(niche.id)
        assert youtube_count_module._resolve_keyword_id("Shared Keyword", "niche-alpha", db) == int(keyword.id)
    finally:
        db.close()


def test_resolve_keyword_id_handles_missing_cases() -> None:
    db = _make_session()
    try:
        niche = Niche(slug="niche-alpha", name="Niche Alpha", category_path="cat/alpha")
        db.add(niche)
        db.commit()

        assert youtube_count_module._resolve_keyword_id("kw", "missing-niche", db) is None
        assert youtube_count_module._resolve_keyword_id("  ", "niche-alpha", db) is None
        assert youtube_count_module._resolve_keyword_id("kw", "niche-alpha", object()) is None
    finally:
        db.close()


def test_youtube_checkpoint_write_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(youtube_count_module, "_fetch_youtube_count", AsyncMock(return_value=50))
    monkeypatch.setattr(youtube_count_module, "_resolve_keyword_id", Mock(return_value=9))
    monkeypatch.setattr(youtube_count_module, "write_external_signal", Mock())

    checkpoint_manager = SimpleNamespace(write=AsyncMock(return_value=None))
    result = _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-cp",
            seed_keywords=["seed"],
            run_id="run-cp",
            db=object(),
            pacing_manager=SimpleNamespace(wait=AsyncMock()),
            checkpoint_manager=checkpoint_manager,
            dry_run=False,
        )
    )
    assert result["signals_written"] == 1
    checkpoint_manager.write.assert_awaited_once()

    warning_mock = Mock()
    monkeypatch.setattr(youtube_count_module.logger, "warning", warning_mock)
    checkpoint_manager_fail = SimpleNamespace(write=AsyncMock(side_effect=RuntimeError("disk fail")))
    _run(
        youtube_count_module.run_youtube_count_collection(
            niche_id="niche-cp",
            seed_keywords=["seed"],
            run_id="run-cp-fail",
            db=object(),
            pacing_manager=SimpleNamespace(wait=AsyncMock()),
            checkpoint_manager=checkpoint_manager_fail,
            dry_run=False,
        )
    )
    assert warning_mock.call_count >= 1
