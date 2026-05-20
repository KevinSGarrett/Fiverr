"""Unit tests for Workflow 2 keyword expansion partial real implementation."""

from __future__ import annotations

import asyncio
import builtins
from unittest.mock import AsyncMock, patch

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.collection.workflows.keyword_expansion import (
    _deduplicate_keywords,
    _fetch_google_suggest,
    _is_session,
    _resolve_niche_pk,
    _safe_pacing_wait,
    _write_keywords_to_db,
    run_keyword_expansion,
)
from src.models.market import Keyword
from src.models.niche import Niche


def _run(coro):
    return asyncio.run(coro)


class _FakeResponse:
    def __init__(self, payload, status_error: Exception | None = None):
        self._payload = payload
        self._status_error = status_error

    def raise_for_status(self) -> None:
        if self._status_error is not None:
            raise self._status_error

    def json(self):
        return self._payload


class _FakeAsyncClient:
    def __init__(
        self,
        *,
        response: _FakeResponse | None = None,
        request_error: Exception | None = None,
    ) -> None:
        self._response = response
        self._request_error = request_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc, _tb) -> None:
        return None

    async def get(self, _url: str, *, params: dict[str, str], headers: dict[str, str]):
        _ = params
        _ = headers
        if self._request_error is not None:
            raise self._request_error
        if self._response is None:
            raise RuntimeError("Missing fake response")
        return self._response


def _build_keyword_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    maker = sessionmaker(bind=engine, future=True)
    session = maker()
    niche = Niche(slug="ai_saas", name="AI SaaS", category_path="Business/AI")
    session.add(niche)
    session.commit()
    return session, niche


def test_fetch_google_suggest_returns_list(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            response=_FakeResponse(["seed", ["AI chatbot", "AI prompt engineer"]])
        ),
    )
    pacing_manager = AsyncMock()
    result = _run(_fetch_google_suggest("ai", pacing_manager))
    assert result == ["AI chatbot", "AI prompt engineer"]
    pacing_manager.wait.assert_awaited_once_with("external_default", dry_run=False)


def test_fetch_google_suggest_empty_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response=_FakeResponse([])),
    )
    pacing_manager = AsyncMock()
    result = _run(_fetch_google_suggest("ai", pacing_manager))
    assert result == []


def test_fetch_google_suggest_http_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            response=_FakeResponse(["seed", ["one"]], status_error=httpx.HTTPError("bad status"))
        ),
    )
    pacing_manager = AsyncMock()
    result = _run(_fetch_google_suggest("ai", pacing_manager))
    assert result == []


def test_fetch_google_suggest_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(request_error=TimeoutError("timeout")),
    )
    pacing_manager = AsyncMock()
    result = _run(_fetch_google_suggest("ai", pacing_manager))
    assert result == []


def test_fetch_google_suggest_blank_seed_returns_empty() -> None:
    result = _run(_fetch_google_suggest("   ", pacing_manager=object()))
    assert result == []


def test_fetch_google_suggest_uses_query_params(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _CaptureAsyncClient(_FakeAsyncClient):
        async def get(self, _url: str, *, params: dict[str, str], headers: dict[str, str]):
            captured["url"] = _url
            captured["params"] = dict(params)
            captured["headers"] = dict(headers)
            return await super().get(_url, params=params, headers=headers)

    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.httpx.AsyncClient",
        lambda *args, **kwargs: _CaptureAsyncClient(response=_FakeResponse(["seed", ["result"]])),
    )
    pacing_manager = AsyncMock()

    result = _run(_fetch_google_suggest("ai & ml+dev #1", pacing_manager))

    assert result == ["result"]
    assert captured["url"] == "https://suggestqueries.google.com/complete/search"
    assert captured["params"] == {"q": "ai & ml+dev #1", "client": "firefox"}


def test_safe_pacing_wait_without_wait_method() -> None:
    _run(_safe_pacing_wait(object(), "external_default", dry_run=False))


def test_deduplicate_case_insensitive() -> None:
    assert _deduplicate_keywords(["AI Chatbot", "ai chatbot"]) == ["AI Chatbot"]


def test_deduplicate_strips_whitespace() -> None:
    assert _deduplicate_keywords([" AI Chatbot "]) == ["AI Chatbot"]


def test_deduplicate_removes_empty() -> None:
    assert _deduplicate_keywords(["AI", "", "  "]) == ["AI"]


def test_run_keyword_expansion_dry_run() -> None:
    result = _run(
        run_keyword_expansion(
            niche_id="ai_saas",
            seeds=["ai chatbot"],
            depth="standard",
            run_id="run-dry",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["dry_run"] is True
    assert result["keywords_queued"] == 0


def test_run_keyword_expansion_real_google_suggest() -> None:
    with patch(
        "src.collection.workflows.keyword_expansion._fetch_google_suggest",
        new=AsyncMock(return_value=["AI Chatbot", "ai chatbot", "AI prompt engineer"]),
    ):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["ai"],
                depth="standard",
                run_id="run-real",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=False,
            )
        )

    assert result["dry_run"] is False
    assert result["keywords_queued"] == 2
    assert result["sources"]["google_suggest"] == 2


def test_run_keyword_expansion_real_writes_to_db() -> None:
    session, niche = _build_keyword_session()
    try:
        with patch(
            "src.collection.workflows.keyword_expansion._fetch_google_suggest",
            new=AsyncMock(return_value=["AI Chatbot", "AI prompt engineer"]),
        ):
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["ai"],
                    depth="standard",
                    run_id="run-db",
                    db=session,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                )
            )

        rows = session.query(Keyword).filter(Keyword.niche_id == niche.id).all()
        assert result["keywords_queued"] == 2
        assert len(rows) == 2
        assert rows[0].external_source == "google_suggest"
        assert rows[0].metadata_json["autocomplete_position"] is None
    finally:
        session.close()


def test_run_keyword_expansion_real_deduplicates() -> None:
    session, niche = _build_keyword_session()
    try:
        with patch(
            "src.collection.workflows.keyword_expansion._fetch_google_suggest",
            new=AsyncMock(side_effect=[["AI Chatbot", "ai chatbot"], [" AI Chatbot "]]),
        ):
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed-one", "seed-two"],
                    depth="standard",
                    run_id="run-dedup",
                    db=session,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                )
            )

        rows = session.query(Keyword).filter(Keyword.niche_id == niche.id).all()
        assert result["keywords_queued"] == 1
        assert len(rows) == 1
        assert rows[0].keyword == "AI Chatbot"
    finally:
        session.close()


def test_run_keyword_expansion_pacing_called(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response=_FakeResponse(["seed", ["AI chatbot"]])),
    )
    pacing_manager = AsyncMock()
    result = _run(
        run_keyword_expansion(
            niche_id="ai_saas",
            seeds=["ai"],
            depth="standard",
            run_id="run-pacing",
            db=None,
            session_manager=None,
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )
    assert result["keywords_queued"] == 1
    pacing_manager.wait.assert_awaited_once_with("external_default", dry_run=False)


def test_is_session_handles_sqlalchemy_import_error(monkeypatch) -> None:
    original_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object):
        if name == "sqlalchemy.orm":
            raise ImportError("sqlalchemy unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    assert _is_session(object()) is False


def test_resolve_niche_pk_numeric_string_returns_int() -> None:
    assert _resolve_niche_pk("7", db=object()) == 7


def test_resolve_niche_pk_import_error(monkeypatch) -> None:
    original_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object):
        if name == "src.models.niche":
            raise ImportError("forced")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    assert _resolve_niche_pk("9", db=object()) == 9
    assert _resolve_niche_pk("ai_saas", db=object()) is None


def test_resolve_niche_pk_query_failure_returns_none() -> None:
    class _BadDb:
        def query(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    assert _resolve_niche_pk("ai_saas", db=_BadDb()) is None


def test_resolve_niche_pk_missing_record_returns_none() -> None:
    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return None

    class _Db:
        def query(self, *_args, **_kwargs):
            return _Query()

    assert _resolve_niche_pk("ai_saas", db=_Db()) is None


def test_write_keywords_to_db_non_session_returns_zero() -> None:
    assert _write_keywords_to_db("ai_saas", ["AI chatbot"], db=object()) == 0


def test_write_keywords_to_db_unresolved_niche_returns_zero() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    session = sessionmaker(bind=engine, future=True)()
    try:
        assert _write_keywords_to_db("missing_niche", ["AI chatbot"], db=session) == 0
    finally:
        session.close()


def test_write_keywords_to_db_lookup_failure_returns_zero() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    session = sessionmaker(bind=engine, future=True)()
    try:
        session.add(Niche(slug="ai_saas", name="AI SaaS", category_path="Business/AI"))
        session.commit()
        assert _write_keywords_to_db("ai_saas", ["AI chatbot"], db=session) == 0
    finally:
        session.close()


def test_write_keywords_to_db_skips_existing_duplicates() -> None:
    session, niche = _build_keyword_session()
    try:
        session.add(
            Keyword(
                niche_id=niche.id,
                keyword="AI Chatbot",
                normalized_keyword="ai chatbot",
                external_source="seed",
            )
        )
        session.commit()
        inserted = _write_keywords_to_db("ai_saas", ["ai chatbot", "AI Chatbot", "AI prompt engineer"], session)
        assert inserted == 1
    finally:
        session.close()


def test_run_keyword_expansion_skips_non_string_seed() -> None:
    fetch_mock = AsyncMock(return_value=["AI chatbot"])
    with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=fetch_mock):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["ai", 42],  # type: ignore[list-item]
                depth="standard",
                run_id="run-non-string",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=False,
            )
        )

    assert result["keywords_queued"] == 1
    assert fetch_mock.await_count == 1
