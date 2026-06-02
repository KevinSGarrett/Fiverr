"""Unit tests for Workflow 2 keyword expansion partial real implementation."""

from __future__ import annotations

import asyncio
import builtins
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.collection.workflows.keyword_expansion import (
    _FEATURE_FLAGS,
    KeywordExpansionWorkflow,
    _cache_get_embedding_map,
    _cache_get_keywords,
    _cache_set_embedding_map,
    _cache_set_keywords,
    _call_llm_json,
    _deduplicate_keywords,
    _extract_cached_embedding_map,
    _extract_cached_keywords,
    _extract_relevant_keywords,
    _fetch_fiverr_autocomplete,
    _fetch_google_suggest,
    _generate_embeddings,
    _is_session,
    _llm_classify_intent,
    _llm_generate_keywords,
    _llm_relevance_filter,
    _normalize_embedding_vector,
    _resolve_maybe_await,
    _resolve_niche_pk,
    _safe_pacing_wait,
    _write_keywords_to_db,
    run_keyword_expansion,
    run_keyword_expansion_stub,
)
from src.models.market import Keyword
from src.models.niche import Niche


def _run(coro):
    return asyncio.run(coro)


class _AsyncCache:
    def __init__(self, seed_data: dict[str, object] | None = None) -> None:
        self._store: dict[str, object] = dict(seed_data or {})
        self.get = AsyncMock(side_effect=self._get)
        self.set = AsyncMock(side_effect=self._set)

    async def _get(self, key: str):
        return self._store.get(key)

    async def _set(self, key: str, value):
        self._store[key] = value
        return None


def _set_feature_flags(
    monkeypatch,
    *,
    step_2a: bool = True,
    step_2c: bool = True,
    step_2d: bool = True,
    step_2f: bool = False,
    step_2g: bool = True,
):
    updated = dict(_FEATURE_FLAGS)
    updated["step_2a_fiverr_autocomplete"] = step_2a
    updated["step_2c_llm_generation"] = step_2c
    updated["step_2d_llm_relevance_filter"] = step_2d
    updated["step_2f_llm_intent_classification"] = step_2f
    updated["step_2g_embedding_generation"] = step_2g
    monkeypatch.setattr("src.collection.workflows.keyword_expansion._FEATURE_FLAGS", updated)


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


def _build_autocomplete_item(
    text: str,
    *,
    with_text_element: bool = False,
) -> AsyncMock:
    item = AsyncMock()
    if with_text_element:
        text_el = AsyncMock()
        text_el.inner_text = AsyncMock(return_value=text)
        item.query_selector = AsyncMock(return_value=text_el)
        item.inner_text = AsyncMock(return_value="unused")
    else:
        item.query_selector = AsyncMock(return_value=None)
        item.inner_text = AsyncMock(return_value=text)
    return item


def _build_autocomplete_page(
    *,
    initial_items: list[AsyncMock] | None = None,
    fallback_items: list[AsyncMock] | None = None,
    goto_error: Exception | None = None,
) -> tuple[AsyncMock, AsyncMock]:
    page = AsyncMock()
    page.goto = AsyncMock(side_effect=goto_error) if goto_error else AsyncMock()
    if fallback_items is None:
        page.query_selector_all = AsyncMock(return_value=initial_items or [])
    else:
        page.query_selector_all = AsyncMock(side_effect=[initial_items or [], fallback_items])
    search_box = AsyncMock()
    search_box.click = AsyncMock()
    page.query_selector = AsyncMock(return_value=search_box)
    page.keyboard = SimpleNamespace(type=AsyncMock())
    page.wait_for_timeout = AsyncMock()
    page.close = AsyncMock()
    return page, search_box


def test_fetch_fiverr_autocomplete_returns_suggestions() -> None:
    item = _build_autocomplete_item("  AI logo design  ", with_text_element=True)
    page, _search_box = _build_autocomplete_page(initial_items=[item])
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    result = _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    assert result == [{"text": "AI logo design", "position": 1}]
    session_manager.new_page.assert_awaited_once()


def test_fetch_fiverr_autocomplete_approach_b_keypress() -> None:
    item = _build_autocomplete_item("fallback suggestion")
    page, search_box = _build_autocomplete_page(initial_items=[], fallback_items=[item])
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    result = _run(
        _fetch_fiverr_autocomplete(
            "seed term",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    assert result == [{"text": "fallback suggestion", "position": 1}]
    search_box.click.assert_awaited_once()
    page.keyboard.type.assert_awaited_once_with("seed term", delay=100)
    page.wait_for_timeout.assert_awaited_once_with(1000)


def test_fetch_fiverr_autocomplete_caps_at_10() -> None:
    items = [_build_autocomplete_item(f"kw-{idx}") for idx in range(15)]
    page, _search_box = _build_autocomplete_page(initial_items=items)
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    result = _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    assert len(result) == 10
    assert result[0]["position"] == 1
    assert result[-1]["position"] == 10
    assert result[-1]["text"] == "kw-9"


def test_fetch_fiverr_autocomplete_timeout_returns_empty() -> None:
    page, _search_box = _build_autocomplete_page(goto_error=TimeoutError("timeout"))
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    result = _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    assert result == []


def test_fetch_fiverr_autocomplete_calls_pacing() -> None:
    item = _build_autocomplete_item("keyword")
    page, _search_box = _build_autocomplete_page(initial_items=[item])
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    pacing_manager.wait.assert_awaited_once_with("fiverr_search", dry_run=False)


def test_fetch_fiverr_autocomplete_closes_page_on_success() -> None:
    item = _build_autocomplete_item("keyword")
    page, _search_box = _build_autocomplete_page(initial_items=[item])
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    page.close.assert_awaited_once()


def test_fetch_fiverr_autocomplete_closes_page_on_error() -> None:
    page, _search_box = _build_autocomplete_page(goto_error=RuntimeError("boom"))
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    page.close.assert_awaited_once()


def test_fetch_fiverr_autocomplete_blank_seed_or_missing_session_returns_empty() -> None:
    assert _run(_fetch_fiverr_autocomplete("   ", "ai_saas", None, AsyncMock())) == []


def test_fetch_fiverr_autocomplete_ignores_close_errors() -> None:
    item = _build_autocomplete_item("keyword")
    page, _search_box = _build_autocomplete_page(initial_items=[item])
    page.close = AsyncMock(side_effect=RuntimeError("close failed"))
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    result = _run(
        _fetch_fiverr_autocomplete(
            "ai",
            "ai_saas",
            session_manager,
            pacing_manager,
        )
    )

    assert result == [{"text": "keyword", "position": 1}]
    pacing_manager.wait.assert_awaited_once_with("fiverr_search", dry_run=False)


def test_safe_pacing_wait_without_wait_method_keyword_expansion() -> None:
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


def test_llm_generate_keywords_returns_list(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {
                    "keywords": [
                        {"text": "AI chatbot for startups", "intent_hint": "buyer"},
                        {"text": "ai chatbot consultant", "intent_hint": "buyer"},
                    ]
                }
            )
        )
    )
    cache = _AsyncCache()

    result = _run(_llm_generate_keywords("ai_saas", ["ai chatbot"], llm_client, cache, "run-1"))

    assert result == ["AI chatbot for startups", "ai chatbot consultant"]
    llm_client.complete.assert_awaited_once()


def test_llm_generate_keywords_cache_hit(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._cache_key_for_keywords",
        lambda *args, **kwargs: "kw-gen-cache-hit",
    )
    llm_client = SimpleNamespace(complete=AsyncMock())
    cache = _AsyncCache(seed_data={"kw-gen-cache-hit": ["cached keyword"]})

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, cache, "run-1"))

    assert result == ["cached keyword"]
    llm_client.complete.assert_not_called()


def test_llm_generate_keywords_cache_miss(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._cache_key_for_keywords",
        lambda *args, **kwargs: "kw-gen-cache-miss",
    )
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps({"keywords": [{"text": "keyword one", "intent_hint": "buyer"}]})
        )
    )
    cache = _AsyncCache()

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, cache, "run-1"))

    assert result == ["keyword one"]
    cache.get.assert_awaited_once_with("kw-gen-cache-miss")
    cache.set.assert_awaited_once_with("kw-gen-cache-miss", ["keyword one"])


def test_llm_generate_keywords_json_decode_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(return_value="{oops"))
    cache = _AsyncCache()

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, cache, "run-1"))

    assert result == []


def test_llm_generate_keywords_api_error(caplog, monkeypatch) -> None:
    caplog.set_level("WARNING")
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(side_effect=RuntimeError("boom")))
    cache = _AsyncCache()

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, cache, "run-1"))

    assert result == []
    assert "LLM keyword generation failed niche=ai_saas" in caplog.text


def test_llm_generate_keywords_empty_seeds() -> None:
    llm_client = SimpleNamespace(complete=AsyncMock())
    cache = _AsyncCache()

    result = _run(_llm_generate_keywords("ai_saas", [], llm_client, cache, "run-1"))

    assert result == []
    llm_client.complete.assert_not_called()


def test_llm_generate_keywords_none_llm_client() -> None:
    cache = _AsyncCache()
    result = _run(_llm_generate_keywords("ai_saas", ["seed"], None, cache, "run-1"))
    assert result == []


def test_llm_generate_keywords_filters_empty_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {
                    "keywords": [
                        {"text": ""},
                        {"text": "   "},
                        {"text": "valid keyword"},
                    ]
                }
            )
        )
    )
    cache = _AsyncCache()

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, cache, "run-1"))

    assert result == ["valid keyword"]


def test_llm_relevance_filter_returns_relevant_only(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {
                    "results": [
                        {"keyword": "keep this", "relevance": "RELEVANT"},
                        {"keyword": "drop this", "relevance": "IRRELEVANT"},
                    ]
                }
            )
        )
    )
    cache = _AsyncCache()

    result = _run(
        _llm_relevance_filter("ai_saas", ["keep this", "drop this"], llm_client, cache)
    )

    assert result == ["keep this"]


def test_llm_relevance_filter_batches_50(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    batch_one = [f"keyword-{idx}" for idx in range(50)]
    batch_two = [f"keyword-{idx}" for idx in range(50, 60)]
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "results": [
                            {"keyword": keyword, "relevance": "RELEVANT"} for keyword in batch_one
                        ]
                    }
                ),
                json.dumps(
                    {
                        "results": [
                            {"keyword": keyword, "relevance": "RELEVANT"} for keyword in batch_two
                        ]
                    }
                ),
            ]
        )
    )
    cache = _AsyncCache()
    candidates = batch_one + batch_two

    result = _run(_llm_relevance_filter("ai_saas", candidates, llm_client, cache))

    assert result == candidates
    assert llm_client.complete.await_count == 2


def test_llm_relevance_filter_cache_hit(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._cache_key_for_keywords",
        lambda *args, **kwargs: "rel-cache-hit",
    )
    llm_client = SimpleNamespace(complete=AsyncMock())
    cache = _AsyncCache(seed_data={"rel-cache-hit": ["cached keep"]})

    result = _run(_llm_relevance_filter("ai_saas", ["cached keep"], llm_client, cache))

    assert result == ["cached keep"]
    llm_client.complete.assert_not_called()


def test_llm_relevance_filter_api_error_fallback(caplog, monkeypatch) -> None:
    caplog.set_level("WARNING")
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(side_effect=RuntimeError("llm down")))
    cache = _AsyncCache()
    candidates = ["one", "two"]

    result = _run(_llm_relevance_filter("ai_saas", candidates, llm_client, cache))

    assert result == candidates
    assert "LLM relevance filter failed niche=ai_saas" in caplog.text


def test_llm_relevance_filter_json_error_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(return_value="not-json"))
    cache = _AsyncCache()
    candidates = ["one", "two"]

    result = _run(_llm_relevance_filter("ai_saas", candidates, llm_client, cache))

    assert result == candidates


def test_llm_relevance_filter_empty_candidates() -> None:
    llm_client = SimpleNamespace(complete=AsyncMock())
    cache = _AsyncCache()

    result = _run(_llm_relevance_filter("ai_saas", [], llm_client, cache))

    assert result == []
    llm_client.complete.assert_not_called()


def test_llm_relevance_filter_unknown_relevance_value(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {
                    "results": [
                        {"keyword": "maybe keep", "relevance": "MAYBE"},
                        {"keyword": "def keep", "relevance": "RELEVANT"},
                    ]
                }
            )
        )
    )
    cache = _AsyncCache()

    result = _run(_llm_relevance_filter("ai_saas", ["maybe keep", "def keep"], llm_client, cache))

    assert result == ["maybe keep", "def keep"]


def test_run_expansion_includes_llm_keywords_when_step_2c_enabled(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=True, step_2d=False)
    fetch_mock = AsyncMock(return_value=["google keyword"])
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps({"keywords": [{"text": "llm keyword", "intent_hint": "buyer"}]})
        )
    )
    with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=fetch_mock):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["seed"],
                depth="standard",
                run_id="run-step2c",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=False,
                llm_client=llm_client,
                cache=_AsyncCache(),
            )
        )

    assert result["sources"]["llm_generated"] == 1
    assert result["keywords_queued"] == 2
    llm_client.complete.assert_awaited_once()


def test_run_expansion_applies_relevance_filter_when_step_2d_enabled(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=True)
    fetch_mock = AsyncMock(return_value=["keep me", "drop me"])
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {
                    "results": [
                        {"keyword": "keep me", "relevance": "RELEVANT"},
                        {"keyword": "drop me", "relevance": "IRRELEVANT"},
                    ]
                }
            )
        )
    )
    with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=fetch_mock):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["seed"],
                depth="standard",
                run_id="run-step2d",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=False,
                llm_client=llm_client,
                cache=_AsyncCache(),
            )
        )

    assert result["keywords_queued"] == 1
    assert result["sources"]["llm_generated"] == 0


def test_run_expansion_skips_llm_when_flags_false(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False)
    fetch_mock = AsyncMock(return_value=["google only"])
    llm_client = SimpleNamespace(complete=AsyncMock())

    with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=fetch_mock):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["seed"],
                depth="standard",
                run_id="run-flags-off",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=False,
                llm_client=llm_client,
                cache=_AsyncCache(),
            )
        )

    assert result["keywords_queued"] == 1
    llm_client.complete.assert_not_called()


def test_run_expansion_step2a_autocomplete_enabled(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2a=True, step_2c=False, step_2d=False, step_2f=False, step_2g=False)
    autocomplete_mock = AsyncMock(return_value=[{"text": "fiverr keyword", "position": 1}])
    google_mock = AsyncMock(return_value=["google keyword"])

    with patch("src.collection.workflows.keyword_expansion._fetch_fiverr_autocomplete", new=autocomplete_mock):
        with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=google_mock):
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="standard",
                    run_id="run-step2a-on",
                    db=None,
                    session_manager=AsyncMock(),
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                )
            )

    assert result["sources"]["fiverr_autocomplete"] == 1
    assert result["autocomplete_count"] == 1
    assert result["keywords_queued"] == 2
    autocomplete_mock.assert_awaited_once()


def test_run_expansion_step2a_autocomplete_no_session_manager(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2a=True, step_2c=False, step_2d=False, step_2f=False, step_2g=False)
    autocomplete_mock = AsyncMock(return_value=[{"text": "fiverr keyword", "position": 1}])
    google_mock = AsyncMock(return_value=["google keyword"])

    with patch("src.collection.workflows.keyword_expansion._fetch_fiverr_autocomplete", new=autocomplete_mock):
        with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=google_mock):
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="standard",
                    run_id="run-step2a-no-session",
                    db=None,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                )
            )

    assert result["sources"]["fiverr_autocomplete"] == 0
    assert result["autocomplete_count"] == 0
    autocomplete_mock.assert_not_awaited()


def test_run_expansion_step2a_skips_non_string_seed(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2a=True, step_2c=False, step_2d=False, step_2f=False, step_2g=False)
    autocomplete_mock = AsyncMock(return_value=[])
    google_mock = AsyncMock(return_value=[])

    with patch("src.collection.workflows.keyword_expansion._fetch_fiverr_autocomplete", new=autocomplete_mock):
        with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=google_mock):
            _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed", 123],
                    depth="standard",
                    run_id="run-step2a-seed-filter",
                    db=None,
                    session_manager=AsyncMock(),
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                )
            )

    assert autocomplete_mock.await_count == 1
    assert autocomplete_mock.await_args.kwargs["seed"] == "seed"


def test_run_expansion_step2a_autocomplete_disabled(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2a=False, step_2c=False, step_2d=False, step_2f=False, step_2g=False)
    autocomplete_mock = AsyncMock(return_value=[{"text": "fiverr keyword", "position": 1}])
    google_mock = AsyncMock(return_value=["google keyword"])

    with patch("src.collection.workflows.keyword_expansion._fetch_fiverr_autocomplete", new=autocomplete_mock):
        with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=google_mock):
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="standard",
                    run_id="run-step2a-off",
                    db=None,
                    session_manager=AsyncMock(),
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                )
            )

    assert result["sources"]["fiverr_autocomplete"] == 0
    assert result["autocomplete_count"] == 0
    autocomplete_mock.assert_not_awaited()


def test_run_expansion_dry_run_unchanged(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=True, step_2d=True)
    fetch_mock = AsyncMock(return_value=["should not run"])
    llm_client = SimpleNamespace(complete=AsyncMock())
    cache = _AsyncCache()
    with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=fetch_mock):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["seed"],
                depth="standard",
                run_id="run-dry-unchanged",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=True,
                llm_client=llm_client,
                cache=cache,
            )
        )

    assert result == {
        "niche_id": "ai_saas",
        "keywords_queued": 0,
        "sources": {
            "fiverr_autocomplete": 0,
            "google_suggest": 0,
            "llm_generated": 0,
        },
        "dry_run": True,
        "note": "Dry run: no real Playwright or LLM calls made",
    }
    fetch_mock.assert_not_called()
    llm_client.complete.assert_not_called()
    cache.get.assert_not_called()
    cache.set.assert_not_called()


def test_run_expansion_llm_failure_does_not_break_pipeline(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=True, step_2d=True)
    fetch_mock = AsyncMock(return_value=["google keyword"])
    llm_client = SimpleNamespace(
        complete=AsyncMock(side_effect=[RuntimeError("step2c boom"), RuntimeError("step2d boom")])
    )
    with patch("src.collection.workflows.keyword_expansion._fetch_google_suggest", new=fetch_mock):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["seed"],
                depth="standard",
                run_id="run-llm-failure",
                db=None,
                session_manager=None,
                pacing_manager=AsyncMock(),
                dry_run=False,
                llm_client=llm_client,
                cache=_AsyncCache(),
            )
        )

    assert result["dry_run"] is False
    assert result["keywords_queued"] == 1
    assert result["sources"]["llm_generated"] == 0


def test_resolve_maybe_await_returns_plain_value_keyword_expansion() -> None:
    assert _run(_resolve_maybe_await("plain")) == "plain"


def test_extract_cached_keywords_from_dict_value_key() -> None:
    assert _extract_cached_keywords({"keywords": [" one ", "", "two"]}, "keywords") == ["one", "two"]


def test_cache_get_keywords_none_cache_returns_none() -> None:
    assert _run(_cache_get_keywords(None, "key", "keywords")) is None


def test_cache_get_keywords_handles_exception() -> None:
    class _BrokenCache:
        def get(self, key: str):
            raise RuntimeError(key)

    assert _run(_cache_get_keywords(_BrokenCache(), "key", "keywords")) is None


def test_cache_set_keywords_none_cache_noop() -> None:
    _run(_cache_set_keywords(None, "key", "keywords", ["value"]))


def test_cache_set_keywords_typeerror_fallback_success() -> None:
    class _FallbackCache:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

        def set(self, key: str, value, *args, **kwargs):
            self.calls.append((key, (value, *args), kwargs))
            if not kwargs:
                raise TypeError("requires kwargs")
            return None

    cache = _FallbackCache()
    _run(_cache_set_keywords(cache, "key", "keywords", ["value"]))

    assert len(cache.calls) == 2
    assert cache.calls[1][0] == "key"
    assert cache.calls[1][2]["model"] == "gpt-4o-mini"


def test_cache_set_keywords_typeerror_fallback_exception() -> None:
    class _FailingFallbackCache:
        def set(self, key: str, value, *args, **kwargs):
            _ = (key, value, args)
            if not kwargs:
                raise TypeError("requires kwargs")
            raise RuntimeError("fallback failed")

    _run(_cache_set_keywords(_FailingFallbackCache(), "key", "keywords", ["value"]))


def test_normalize_embedding_vector_rejects_bool() -> None:
    assert _normalize_embedding_vector([1.0, True]) is None


def test_extract_cached_embedding_map_supports_wrapped_payload_and_missing_values() -> None:
    cached = {"embedding_map": {"alpha": [1, 2]}}
    result = _extract_cached_embedding_map(cached, ["alpha", "beta"])
    assert result == {"alpha": [1.0, 2.0], "beta": None}


def test_extract_cached_embedding_map_rejects_invalid_vector() -> None:
    cached = {"embedding_map": {"alpha": [1.0, "bad"]}}
    assert _extract_cached_embedding_map(cached, ["alpha"]) is None


def test_cache_get_embedding_map_none_cache_returns_none() -> None:
    assert _run(_cache_get_embedding_map(None, "key", ["alpha"])) is None


def test_cache_get_embedding_map_handles_exception() -> None:
    class _BrokenCache:
        def get(self, key: str):
            raise RuntimeError(key)

    assert _run(_cache_get_embedding_map(_BrokenCache(), "key", ["alpha"])) is None


def test_cache_set_embedding_map_none_cache_noop() -> None:
    _run(_cache_set_embedding_map(None, "key", {"alpha": [1.0]}))


def test_cache_set_embedding_map_fallback_exception_path() -> None:
    class _FallbackErrorCache:
        def __init__(self) -> None:
            self.calls = 0

        def set(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                raise TypeError("legacy signature")
            raise RuntimeError("fallback failed")

    cache = _FallbackErrorCache()
    _run(_cache_set_embedding_map(cache, "key", {"alpha": [1.0]}))
    assert cache.calls == 2


def test_cache_set_embedding_map_primary_exception_path() -> None:
    class _PrimaryErrorCache:
        def __init__(self) -> None:
            self.calls = 0

        def set(self, *_args, **_kwargs):
            self.calls += 1
            raise RuntimeError("primary set failed")

    cache = _PrimaryErrorCache()
    _run(_cache_set_embedding_map(cache, "key", {"alpha": [1.0]}))
    assert cache.calls == 1


def test_call_llm_json_typeerror_fallback_uses_no_response_format() -> None:
    class _LegacyClient:
        def complete(self, *, prompt: str, model: str):
            _ = (prompt, model)
            return '{"keywords": []}'

    assert (
        _run(_call_llm_json(_LegacyClient(), prompt="prompt", model="gpt-4o-mini"))
        == '{"keywords": []}'
    )


def test_call_llm_json_uses_text_attr() -> None:
    class _Response:
        text = '{"keywords": []}'

    llm_client = SimpleNamespace(complete=AsyncMock(return_value=_Response()))
    assert _run(_call_llm_json(llm_client, prompt="prompt", model="gpt-4o-mini")) == '{"keywords": []}'


def test_call_llm_json_stringifies_non_string_response() -> None:
    llm_client = SimpleNamespace(complete=AsyncMock(return_value={"k": "v"}))
    assert _run(_call_llm_json(llm_client, prompt="prompt", model="gpt-4o-mini")) == "{'k': 'v'}"


def test_llm_generate_keywords_non_object_payload_returns_empty(caplog, monkeypatch) -> None:
    caplog.set_level("WARNING")
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(return_value="[]"))

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, _AsyncCache(), "run-1"))

    assert result == []
    assert "LLM keyword generation failed niche=ai_saas" in caplog.text


def test_llm_generate_keywords_non_list_keywords_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(return_value='{"keywords": {"text": "one"}}'))

    result = _run(_llm_generate_keywords("ai_saas", ["seed"], llm_client, _AsyncCache(), "run-1"))

    assert result == []


def test_extract_relevant_keywords_non_list_results_returns_batch() -> None:
    payload = {"results": "bad-shape"}
    assert _extract_relevant_keywords(payload, ["one", "two"]) == ["one", "two"]


def test_extract_relevant_keywords_skips_invalid_rows() -> None:
    payload = {
        "results": [
            "not-dict",
            {"keyword": 123, "relevance": "IRRELEVANT"},
            {"keyword": "outside-batch", "relevance": "IRRELEVANT"},
            {"keyword": "in-batch", "relevance": "RELEVANT"},
        ]
    }
    assert _extract_relevant_keywords(payload, ["in-batch"]) == ["in-batch"]


def test_llm_relevance_filter_non_object_payload_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(return_value="[]"))
    candidates = ["keep", "all"]

    result = _run(_llm_relevance_filter("ai_saas", candidates, llm_client, _AsyncCache()))

    assert result == candidates


def test_llm_classify_intent_returns_dict_mapping(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {
                    "results": [
                        {"keyword": "how to write a prd", "intent_class": "INFORMATIONAL"},
                        {"keyword": "best prd writer", "intent_class": "CONSIDERATION"},
                    ]
                }
            )
        )
    )

    result = _run(
        _llm_classify_intent(
            niche_id="ai_saas",
            keywords=["how to write a prd", "best prd writer"],
            llm_client=llm_client,
            cache=_AsyncCache(),
        )
    )

    assert result == {
        "how to write a prd": "INFORMATIONAL",
        "best prd writer": "CONSIDERATION",
    }


def test_llm_classify_intent_batches_50(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    batch_one = [f"kw-{idx}" for idx in range(50)]
    batch_two = [f"kw-{idx}" for idx in range(50, 60)]
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "results": [
                            {"keyword": keyword, "intent_class": "HIGH_INTENT"}
                            for keyword in batch_one
                        ]
                    }
                ),
                json.dumps(
                    {
                        "results": [
                            {"keyword": keyword, "intent_class": "TRANSACTIONAL"}
                            for keyword in batch_two
                        ]
                    }
                ),
            ]
        )
    )
    result = _run(
        _llm_classify_intent(
            niche_id="ai_saas",
            keywords=batch_one + batch_two,
            llm_client=llm_client,
            cache=_AsyncCache(),
        )
    )

    assert llm_client.complete.await_count == 2
    assert len(result) == 60
    assert result["kw-0"] == "HIGH_INTENT"
    assert result["kw-59"] == "TRANSACTIONAL"


def test_llm_classify_intent_cache_hit(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._cache_key_for_keywords",
        lambda *args, **kwargs: "intent-cache-hit",
    )
    llm_client = SimpleNamespace(complete=AsyncMock())
    cache = _AsyncCache(seed_data={"intent-cache-hit": {"cached kw": "HIGH_INTENT"}})

    result = _run(_llm_classify_intent("ai_saas", ["cached kw"], llm_client, cache))

    assert result == {"cached kw": "HIGH_INTENT"}
    llm_client.complete.assert_not_called()


def test_llm_classify_intent_invalid_class_becomes_null(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {"results": [{"keyword": "unknown intent keyword", "intent_class": "UNKNOWN"}]}
            )
        )
    )

    result = _run(
        _llm_classify_intent(
            niche_id="ai_saas",
            keywords=["unknown intent keyword"],
            llm_client=llm_client,
            cache=_AsyncCache(),
        )
    )

    assert result == {"unknown intent keyword": None}


def test_llm_classify_intent_api_error_returns_null_map(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(complete=AsyncMock(side_effect=RuntimeError("llm unavailable")))

    result = _run(
        _llm_classify_intent(
            niche_id="ai_saas",
            keywords=["kw-1", "kw-2"],
            llm_client=llm_client,
            cache=_AsyncCache(),
        )
    )

    assert result == {"kw-1": None, "kw-2": None}


def test_llm_classify_intent_missing_kw_in_response_becomes_null(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._render_stage02_template",
        lambda *args, **kwargs: "prompt",
    )
    llm_client = SimpleNamespace(
        complete=AsyncMock(
            return_value=json.dumps(
                {"results": [{"keyword": "present", "intent_class": "HIGH_INTENT"}]}
            )
        )
    )

    result = _run(
        _llm_classify_intent(
            niche_id="ai_saas",
            keywords=["present", "missing"],
            llm_client=llm_client,
            cache=_AsyncCache(),
        )
    )

    assert result == {"present": "HIGH_INTENT", "missing": None}


def test_run_expansion_step2f_sets_intent_on_db_keywords(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False, step_2f=True)
    session, niche = _build_keyword_session()
    try:
        with patch(
            "src.collection.workflows.keyword_expansion._fetch_google_suggest",
            new=AsyncMock(return_value=["buy logo design", "what is logo design"]),
        ):
            llm_client = SimpleNamespace(
                complete=AsyncMock(
                    return_value=json.dumps(
                        {
                            "results": [
                                {"keyword": "buy logo design", "intent_class": "TRANSACTIONAL"},
                                {"keyword": "what is logo design", "intent_class": "INFORMATIONAL"},
                            ]
                        }
                    )
                )
            )
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="standard",
                    run_id="run-step2f-db",
                    db=session,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                    llm_client=llm_client,
                    cache=_AsyncCache(),
                )
            )

        rows = session.query(Keyword).filter(Keyword.niche_id == niche.id).all()
        intent_by_keyword = {row.keyword: row.intent_class for row in rows}
        assert result["keywords_queued"] == 2
        assert intent_by_keyword["buy logo design"] == "TRANSACTIONAL"
        assert intent_by_keyword["what is logo design"] == "INFORMATIONAL"
    finally:
        session.close()


def test_run_expansion_step2f_flag_false_no_classification(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False, step_2f=False)
    session, niche = _build_keyword_session()
    intent_mock = AsyncMock(return_value={"buy logo design": "TRANSACTIONAL"})
    try:
        with patch(
            "src.collection.workflows.keyword_expansion._fetch_google_suggest",
            new=AsyncMock(return_value=["buy logo design"]),
        ):
            with patch("src.collection.workflows.keyword_expansion._llm_classify_intent", new=intent_mock):
                _run(
                    run_keyword_expansion(
                        niche_id="ai_saas",
                        seeds=["seed"],
                        depth="standard",
                        run_id="run-step2f-off",
                        db=session,
                        session_manager=None,
                        pacing_manager=AsyncMock(),
                        dry_run=False,
                        llm_client=SimpleNamespace(complete=AsyncMock()),
                        cache=_AsyncCache(),
                    )
                )

        rows = session.query(Keyword).filter(Keyword.niche_id == niche.id).all()
        assert len(rows) == 1
        assert rows[0].intent_class is None
        intent_mock.assert_not_awaited()
    finally:
        session.close()


def test_run_expansion_step2f_flag_false_skips_intent_classification(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False, step_2f=False)
    intent_mock = AsyncMock(return_value={"buy logo design": "TRANSACTIONAL"})

    with patch(
        "src.collection.workflows.keyword_expansion._fetch_google_suggest",
        new=AsyncMock(return_value=["buy logo design"]),
    ):
        with patch("src.collection.workflows.keyword_expansion._llm_classify_intent", new=intent_mock):
            _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="standard",
                    run_id="run-step2f-off-intent",
                    db=None,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                    llm_client=SimpleNamespace(complete=AsyncMock()),
                    cache=_AsyncCache(),
                )
            )

    intent_mock.assert_not_awaited()


def test_generate_embeddings_returns_dict_mapping() -> None:
    llm_client = SimpleNamespace(
        embed=AsyncMock(return_value={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
    )

    result = _run(
        _generate_embeddings(
            niche_id="ai_saas",
            keywords=["kw-one", "kw-two"],
            llm_client=llm_client,
            cache=_AsyncCache(),
        )
    )

    assert result == {"kw-one": [0.1, 0.2], "kw-two": [0.3, 0.4]}
    llm_client.embed.assert_awaited_once_with(["kw-one", "kw-two"], model="text-embedding-3-small")


def test_generate_embeddings_batches_100() -> None:
    keywords = [f"kw-{idx}" for idx in range(150)]

    async def _embed(texts: list[str], *, model: str):
        _ = model
        return {"embeddings": [[float(idx)] for idx, _kw in enumerate(texts)]}

    llm_client = SimpleNamespace(embed=AsyncMock(side_effect=_embed))
    result = _run(_generate_embeddings("ai_saas", keywords, llm_client, _AsyncCache()))

    assert len(result) == 150
    assert llm_client.embed.await_count == 2
    first_call_texts = llm_client.embed.await_args_list[0].args[0]
    second_call_texts = llm_client.embed.await_args_list[1].args[0]
    assert len(first_call_texts) == 100
    assert len(second_call_texts) == 50


def test_generate_embeddings_cache_hit(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._cache_key_for_keywords",
        lambda *args, **kwargs: "embed-cache-hit",
    )
    llm_client = SimpleNamespace(embed=AsyncMock())
    cache = _AsyncCache(seed_data={"embed-cache-hit": {"kw-one": [1.0], "kw-two": [2.0]}})

    result = _run(_generate_embeddings("ai_saas", ["kw-one", "kw-two"], llm_client, cache))

    assert result == {"kw-one": [1.0], "kw-two": [2.0]}
    llm_client.embed.assert_not_called()


def test_generate_embeddings_api_error_returns_null_map(caplog) -> None:
    caplog.set_level("WARNING")
    llm_client = SimpleNamespace(embed=AsyncMock(side_effect=RuntimeError("embed down")))

    result = _run(_generate_embeddings("ai_saas", ["kw-one", "kw-two"], llm_client, _AsyncCache()))

    assert result == {"kw-one": None, "kw-two": None}
    assert "Embedding generation failed niche=ai_saas" in caplog.text


def test_generate_embeddings_payload_not_list_falls_back_to_null(caplog) -> None:
    caplog.set_level("WARNING")
    llm_client = SimpleNamespace(embed=AsyncMock(return_value={"embeddings": "not-a-list"}))

    result = _run(_generate_embeddings("ai_saas", ["kw-one", "kw-two"], llm_client, _AsyncCache()))

    assert result == {"kw-one": None, "kw-two": None}
    assert "Embedding generation failed niche=ai_saas" in caplog.text


def test_generate_embeddings_truncated_payload_logs_warning(caplog) -> None:
    caplog.set_level("WARNING")
    llm_client = SimpleNamespace(embed=AsyncMock(return_value={"embeddings": [[0.9, 0.8]]}))

    result = _run(_generate_embeddings("ai_saas", ["kw-one", "kw-two"], llm_client, _AsyncCache()))

    assert result["kw-one"] == [0.9, 0.8]
    assert result["kw-two"] is None
    assert "Embedding response truncated niche=ai_saas" in caplog.text


def test_generate_embeddings_empty_keywords() -> None:
    llm_client = SimpleNamespace(embed=AsyncMock())

    result = _run(_generate_embeddings("ai_saas", [], llm_client, _AsyncCache()))

    assert result == {}
    llm_client.embed.assert_not_called()


def test_llm_classify_intent_empty_keywords_returns_empty() -> None:
    llm_client = SimpleNamespace(complete=AsyncMock())
    result = _run(_llm_classify_intent("ai_saas", [], llm_client, _AsyncCache()))
    assert result == {}
    llm_client.complete.assert_not_called()


def test_run_expansion_step2g_sets_embedding_on_db_keywords(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False, step_2f=False, step_2g=True)
    session, niche = _build_keyword_session()
    try:
        with patch(
            "src.collection.workflows.keyword_expansion._fetch_google_suggest",
            new=AsyncMock(return_value=["buy logo design", "logo design consultant"]),
        ):
            llm_client = SimpleNamespace(
                complete=AsyncMock(),
                embed=AsyncMock(return_value={"embeddings": [[0.11, 0.22], [0.33, 0.44]]}),
            )
            result = _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="standard",
                    run_id="run-step2g-db",
                    db=session,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                    llm_client=llm_client,
                    cache=_AsyncCache(),
                )
            )

        rows = session.query(Keyword).filter(Keyword.niche_id == niche.id).all()
        vector_map = {row.keyword: row.embedding_vector for row in rows}
        assert result["keywords_queued"] == 2
        assert json.loads(vector_map["buy logo design"]) == [0.11, 0.22]
        assert json.loads(vector_map["logo design consultant"]) == [0.33, 0.44]
    finally:
        session.close()


def test_run_expansion_step2g_flag_false_no_embedding(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False, step_2f=False, step_2g=False)
    session, niche = _build_keyword_session()
    embedding_mock = AsyncMock(return_value={"buy logo design": [0.11, 0.22]})
    try:
        with patch(
            "src.collection.workflows.keyword_expansion._fetch_google_suggest",
            new=AsyncMock(return_value=["buy logo design"]),
        ):
            with patch("src.collection.workflows.keyword_expansion._generate_embeddings", new=embedding_mock):
                _run(
                    run_keyword_expansion(
                        niche_id="ai_saas",
                        seeds=["seed"],
                        depth="standard",
                        run_id="run-step2g-off",
                        db=session,
                        session_manager=None,
                        pacing_manager=AsyncMock(),
                        dry_run=False,
                        llm_client=SimpleNamespace(complete=AsyncMock(), embed=AsyncMock()),
                        cache=_AsyncCache(),
                    )
                )

        rows = session.query(Keyword).filter(Keyword.niche_id == niche.id).all()
        assert len(rows) == 1
        assert rows[0].embedding_vector is None
        embedding_mock.assert_not_awaited()
    finally:
        session.close()


def test_run_expansion_step2g_embedding_skipped_at_feasibility_depth(monkeypatch) -> None:
    _set_feature_flags(monkeypatch, step_2c=False, step_2d=False, step_2f=False, step_2g=True)
    embedding_mock = AsyncMock(return_value={"buy logo design": [0.11, 0.22]})

    with patch(
        "src.collection.workflows.keyword_expansion._fetch_google_suggest",
        new=AsyncMock(return_value=["buy logo design"]),
    ):
        with patch("src.collection.workflows.keyword_expansion._generate_embeddings", new=embedding_mock):
            _run(
                run_keyword_expansion(
                    niche_id="ai_saas",
                    seeds=["seed"],
                    depth="feasibility",
                    run_id="run-step2g-feasibility",
                    db=None,
                    session_manager=None,
                    pacing_manager=AsyncMock(),
                    dry_run=False,
                    llm_client=SimpleNamespace(complete=AsyncMock(), embed=AsyncMock()),
                    cache=_AsyncCache(),
                )
            )

    embedding_mock.assert_not_awaited()


def test_run_expansion_step2g_skipped_at_feasibility_depth(monkeypatch) -> None:
    # Keep exact spec-requested test name while preserving embedding-focused selector run.
    test_run_expansion_step2g_embedding_skipped_at_feasibility_depth(monkeypatch)


def test_run_keyword_expansion_stub_alias() -> None:
    result = _run(
        run_keyword_expansion_stub(
            niche_id="ai_saas",
            seeds=["seed"],
            depth="standard",
            run_id="run-stub",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["dry_run"] is True


def test_keyword_expansion_workflow_run_returns_module() -> None:
    workflow = KeywordExpansionWorkflow()
    module = workflow.run()
    assert hasattr(module, "__name__")
