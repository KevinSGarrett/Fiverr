"""Unit tests for Workflow 7 Reddit signal collection."""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock, call

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.collection.workflows import reddit_signals as reddit_signals_module
from src.models import Keyword, Niche


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


class _FakePost:
    def __init__(self, title: str, selftext: str, score: int, created_utc: float) -> None:
        self.title = title
        self.selftext = selftext
        self.score = score
        self.created_utc = created_utc


class _FakeSubreddit:
    def __init__(
        self,
        name: str,
        *,
        search_map: dict[str, list[_FakePost]] | None = None,
        search_errors: dict[str, Exception] | None = None,
        id_error: Exception | None = None,
    ) -> None:
        self.name = name
        self._search_map = search_map or {}
        self._search_errors = search_errors or {}
        self._id_error = id_error
        self.id_access_count = 0
        self.search_calls: list[tuple[str, str, str, int]] = []

    @property
    def id(self) -> str:
        self.id_access_count += 1
        if self._id_error is not None:
            raise self._id_error
        return f"id-{self.name}"

    def search(self, query: str, *, sort: str, time_filter: str, limit: int) -> list[_FakePost]:
        self.search_calls.append((query, sort, time_filter, limit))
        error = self._search_errors.get(query)
        if error is not None:
            raise error
        return list(self._search_map.get(query, []))


class _FakeReddit:
    def __init__(self, subreddits: dict[str, _FakeSubreddit]) -> None:
        self._subreddits = subreddits

    def subreddit(self, name: str) -> _FakeSubreddit:
        return self._subreddits[name]


def _install_fake_praw(monkeypatch: pytest.MonkeyPatch, reddit_client: _FakeReddit) -> Mock:
    reddit_ctor = Mock(return_value=reddit_client)
    monkeypatch.setitem(sys.modules, "praw", SimpleNamespace(Reddit=reddit_ctor))
    return reddit_ctor


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    maker = sessionmaker(bind=engine, future=True)
    return maker()


def _run_real_collection(
    *,
    niche_id: str = "ai-agent",
    seed_keywords: list[str] | None = None,
    subreddits: list[str] | None = None,
    db: Any = None,
    pacing_manager: Any | None = None,
    llm_client: Any | None = None,
    cache: Any | None = None,
    checkpoint_manager: Any | None = None,
) -> dict[str, Any]:
    return _run(
        reddit_signals_module.run_reddit_signals_collection(
            niche_id=niche_id,
            seed_keywords=seed_keywords or ["seed-1"],
            subreddits=subreddits or ["Entrepreneur"],
            run_id="run-1",
            db=db,
            pacing_manager=pacing_manager or SimpleNamespace(wait=AsyncMock()),
            llm_client=llm_client,
            cache=cache,
            checkpoint_manager=checkpoint_manager,
            dry_run=False,
        )
    )


def test_reddit_dry_run_default() -> None:
    result = _run(
        reddit_signals_module.run_reddit_signals_collection(
            niche_id="ai_agents",
            seed_keywords=["ai agent"],
            subreddits=["Entrepreneur"],
            run_id="run-2",
            db=None,
            pacing_manager=None,
        )
    )
    assert result["dry_run"] is True
    assert result["signals_written"] == 0
    assert result["post_count_90d"] == 0


def test_reddit_real_checks_subreddit_accessibility(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"seed-1": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    result = _run_real_collection()
    assert subreddit.id_access_count == 1
    assert result["subreddits_accessed"] == ["Entrepreneur"]


def test_reddit_real_inaccessible_subreddit_skipped(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", id_error=RuntimeError("private subreddit"))
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    result = _run_real_collection()
    assert subreddit.search_calls == []
    assert result["subreddits_accessed"] == []
    assert "inaccessible" in caplog.text


def test_reddit_real_searches_per_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [], "beta": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    _run_real_collection(seed_keywords=["alpha", "beta"])
    assert subreddit.search_calls == [
        ("alpha", "relevance", "year", 25),
        ("beta", "relevance", "year", 25),
    ]


def test_reddit_real_handles_429(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit(
        "Entrepreneur",
        search_map={"beta": []},
        search_errors={"alpha": RuntimeError("429 TooManyRequests")},
    )
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    sleep_mock = AsyncMock()
    monkeypatch.setattr(reddit_signals_module.asyncio, "sleep", sleep_mock)
    pacing_manager = SimpleNamespace(wait=AsyncMock())
    _run_real_collection(seed_keywords=["alpha", "beta"], pacing_manager=pacing_manager)
    sleep_mock.assert_awaited_once_with(60)
    assert len(subreddit.search_calls) == 2
    pacing_manager.wait.assert_awaited_once_with("reddit_api", dry_run=False)


def test_reddit_real_logs_non_429_search_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    subreddit = _FakeSubreddit(
        "Entrepreneur",
        search_errors={"alpha": RuntimeError("temporary parse failure")},
    )
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    _run_real_collection(seed_keywords=["alpha"])
    assert "Reddit search Entrepreneur/alpha failed" in caplog.text


def test_reddit_real_calls_pacing_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [], "beta": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    pacing_manager = SimpleNamespace(wait=AsyncMock())
    _run_real_collection(seed_keywords=["alpha", "beta"], pacing_manager=pacing_manager)
    assert pacing_manager.wait.await_count == 2
    pacing_manager.wait.assert_has_awaits(
        [call("reddit_api", dry_run=False), call("reddit_api", dry_run=False)]
    )


def test_reddit_real_collects_post_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakePost("Need help hiring", "x" * 300, 12, 1700000000.0)
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [post]})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    captured_posts: list[dict[str, Any]] = []

    def _capture(posts: list[dict[str, Any]]) -> int:
        captured_posts.extend(posts)
        return 1

    monkeypatch.setattr(reddit_signals_module, "parse_reddit_post_count_90d", Mock(side_effect=_capture))
    _run_real_collection(seed_keywords=["alpha"])
    assert len(captured_posts) == 1
    collected = captured_posts[0]
    assert collected["title"] == "Need help hiring"
    assert len(collected["body_snippet"]) == 200
    assert collected["upvotes"] == 12
    assert collected["created_utc"] == 1700000000.0
    assert collected["subreddit"] == "Entrepreneur"


def test_reddit_real_computes_90d_count(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakePost("Need help", "body", 1, 1700000000.0)
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [post]})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    parse_mock = Mock(return_value=7)
    monkeypatch.setattr(reddit_signals_module, "parse_reddit_post_count_90d", parse_mock)
    result = _run_real_collection(seed_keywords=["alpha"])
    parse_mock.assert_called_once()
    assert result["post_count_90d"] == 7


def test_reddit_real_selects_top_10_for_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakePost("Need help", "body", 1, 1700000000.0)
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [post]})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    select_mock = Mock(return_value=[{"title": "top", "body_snippet": "body", "upvotes": 3}])
    llm_parse_mock = AsyncMock(return_value=(None, []))
    monkeypatch.setattr(reddit_signals_module, "select_top_posts_for_llm", select_mock)
    monkeypatch.setattr(reddit_signals_module, "_llm_reddit_demand_parse", llm_parse_mock)
    _run_real_collection(seed_keywords=["alpha"], llm_client=object(), cache=object())
    select_mock.assert_called_once()
    args, kwargs = select_mock.call_args
    assert kwargs["n"] == 10
    llm_parse_mock.assert_awaited_once()


def test_reddit_real_calls_llm_demand_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    post = _FakePost("Need help", "body", 1, 1700000000.0)
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [post]})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    llm_parse_mock = AsyncMock(return_value=(7.5, ["looking for freelancer"]))
    monkeypatch.setattr(reddit_signals_module, "_llm_reddit_demand_parse", llm_parse_mock)
    result = _run_real_collection(seed_keywords=["alpha"], llm_client=object(), cache=object())
    llm_parse_mock.assert_awaited_once()
    assert result["demand_intent_score"] == 7.5
    assert result["intent_phrases"] == ["looking for freelancer"]


def test_reddit_real_writes_signal_per_keyword(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [], "beta": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    resolve_mock = Mock(side_effect=[101, 202])
    write_mock = Mock()
    monkeypatch.setattr(reddit_signals_module, "_resolve_keyword_id", resolve_mock)
    monkeypatch.setattr(reddit_signals_module, "write_external_signal", write_mock)
    result = _run_real_collection(seed_keywords=["alpha", "beta"])
    assert result["signals_written"] == 2
    assert write_mock.call_count == 2
    for call_ in write_mock.call_args_list:
        assert call_.kwargs["signal_type"] == reddit_signals_module.SIGNAL_REDDIT_DEMAND
        assert call_.kwargs["collection_method"] == "reddit_api"


def test_reddit_real_scoped_keyword_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": [], "beta": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    db_token = object()
    resolve_mock = Mock(side_effect=[1, None])
    write_mock = Mock()
    monkeypatch.setattr(reddit_signals_module, "_resolve_keyword_id", resolve_mock)
    monkeypatch.setattr(reddit_signals_module, "write_external_signal", write_mock)
    _run_real_collection(niche_id="niche-x", seed_keywords=["alpha", "beta"], db=db_token)
    assert resolve_mock.call_args_list == [
        call("alpha", "niche-x", db_token),
        call("beta", "niche-x", db_token),
    ]
    assert write_mock.call_count == 1


def test_reddit_real_writes_checkpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    checkpoint_manager = SimpleNamespace(write=AsyncMock())
    monkeypatch.setattr(reddit_signals_module, "_resolve_keyword_id", Mock(return_value=10))
    monkeypatch.setattr(reddit_signals_module, "write_external_signal", Mock())
    _run_real_collection(seed_keywords=["alpha"], checkpoint_manager=checkpoint_manager)
    checkpoint_manager.write.assert_awaited_once()
    args = checkpoint_manager.write.await_args.args
    assert args[0] == "stage06_reddit"
    assert args[1] == "ai-agent"
    assert args[2]["run_id"] == "run-1"
    assert args[2]["signals_written"] == 1


def test_reddit_real_checkpoint_failure_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    subreddit = _FakeSubreddit("Entrepreneur", search_map={"alpha": []})
    _install_fake_praw(monkeypatch, _FakeReddit({"Entrepreneur": subreddit}))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    checkpoint_manager = SimpleNamespace(write=AsyncMock(side_effect=RuntimeError("disk error")))
    monkeypatch.setattr(reddit_signals_module, "_resolve_keyword_id", Mock(return_value=10))
    monkeypatch.setattr(reddit_signals_module, "write_external_signal", Mock())
    _run_real_collection(seed_keywords=["alpha"], checkpoint_manager=checkpoint_manager)
    assert "Failed to write Reddit checkpoint" in caplog.text


def test_resolve_maybe_await_returns_plain_value() -> None:
    assert _run(reddit_signals_module._resolve_maybe_await(5)) == 5


def test_safe_pacing_wait_without_wait_method() -> None:
    _run(reddit_signals_module._safe_pacing_wait(object(), "reddit_api", dry_run=False))


def test_llm_reddit_demand_parse_cache_hit() -> None:
    cache = SimpleNamespace(
        get=AsyncMock(return_value={"demand_intent_score": 8.5, "intent_phrases": ["hire me"]}),
        set=AsyncMock(),
    )
    llm_client = SimpleNamespace(complete=Mock())
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 8.5
    assert phrases == ["hire me"]
    llm_client.complete.assert_not_called()


def test_llm_reddit_demand_parse_cache_get_error_falls_back_to_llm() -> None:
    cache = SimpleNamespace(get=AsyncMock(side_effect=RuntimeError("cache offline")), set=AsyncMock())
    llm_client = SimpleNamespace(
        complete=AsyncMock(return_value='{"demand_intent_score": 6, "intent_phrases": ["need help"]}')
    )
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 6.0
    assert phrases == ["need help"]


def test_llm_reddit_demand_parse_cache_hit_with_none_score() -> None:
    cache = SimpleNamespace(
        get=AsyncMock(return_value={"demand_intent_score": None, "intent_phrases": ["hire me"]}),
        set=AsyncMock(),
    )
    llm_client = SimpleNamespace(complete=Mock())
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 0.0
    assert phrases == ["hire me"]


def test_llm_reddit_demand_parse_cache_hit_with_bad_score() -> None:
    cache = SimpleNamespace(
        get=AsyncMock(return_value={"demand_intent_score": "not-a-number", "intent_phrases": ["hire me"]}),
        set=AsyncMock(),
    )
    llm_client = SimpleNamespace(complete=Mock())
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 0.0
    assert phrases == ["hire me"]


class _TypeErrorCompleteClient:
    def __init__(self, payload: str) -> None:
        self._payload = payload
        self.calls = 0

    def complete(self, **kwargs: Any) -> str:
        self.calls += 1
        if "response_format" in kwargs:
            raise TypeError("response_format unsupported")
        return self._payload


def test_llm_reddit_demand_parse_typeerror_fallback_path() -> None:
    llm_client = _TypeErrorCompleteClient(
        '{"demand_intent_score": 4, "intent_phrases": ["can someone help"]}'
    )
    cache = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert llm_client.calls == 2
    assert score == 4.0
    assert phrases == ["can someone help"]


def test_llm_reddit_demand_parse_success_sets_cache() -> None:
    cache = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())
    llm_client = SimpleNamespace(
        complete=AsyncMock(return_value='{"demand_intent_score": 11, "intent_phrases": ["hire now", 1]}')
    )
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 10.0
    assert phrases == ["hire now"]
    cache.set.assert_awaited_once()


def test_llm_reddit_demand_parse_invalid_score_defaults_to_zero() -> None:
    cache = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())
    llm_client = SimpleNamespace(
        complete=AsyncMock(return_value='{"demand_intent_score": "bad", "intent_phrases": ["hire now"]}')
    )
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 0.0
    assert phrases == ["hire now"]


def test_llm_reddit_demand_parse_cache_set_error_is_non_fatal(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    cache = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock(side_effect=RuntimeError("fail")))
    llm_client = SimpleNamespace(
        complete=AsyncMock(return_value='{"demand_intent_score": 5, "intent_phrases": ["hire now"]}')
    )
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=cache,
        )
    )
    assert score == 5.0
    assert phrases == ["hire now"]
    assert "Reddit LLM cache set failed" in caplog.text


def test_llm_reddit_demand_parse_api_error(caplog: pytest.LogCaptureFixture) -> None:
    llm_client = SimpleNamespace(complete=Mock(side_effect=RuntimeError("boom")))
    score, phrases = _run(
        reddit_signals_module._llm_reddit_demand_parse(
            top_posts=[{"title": "Need help", "body_snippet": "body", "upvotes": 3}],
            niche_id="ai-agent",
            llm_client=llm_client,
            cache=None,
        )
    )
    assert score is None
    assert phrases == []
    assert "Reddit LLM demand parse failed" in caplog.text


def test_resolve_reddit_keyword_id_scoped_to_niche() -> None:
    db = _make_session()
    try:
        niche_a = Niche(slug="ai-agent", name="AI Agent", category_path="tech/ai")
        niche_b = Niche(slug="writer", name="Writer", category_path="writing")
        db.add_all([niche_a, niche_b])
        db.commit()
        db.refresh(niche_a)
        db.refresh(niche_b)

        keyword_a = Keyword(niche_id=int(niche_a.id), keyword="Shared", normalized_keyword="shared")
        keyword_b = Keyword(niche_id=int(niche_b.id), keyword="Shared", normalized_keyword="shared")
        db.add_all([keyword_a, keyword_b])
        db.commit()
        db.refresh(keyword_a)
        db.refresh(keyword_b)

        resolved_a = reddit_signals_module._resolve_keyword_id("Shared", "ai-agent", db)
        resolved_b = reddit_signals_module._resolve_keyword_id("Shared", "writer", db)
        assert resolved_a == int(keyword_a.id)
        assert resolved_b == int(keyword_b.id)
    finally:
        db.close()


def test_resolve_reddit_keyword_id_returns_none_when_missing() -> None:
    db = _make_session()
    try:
        niche = Niche(slug="ai-agent", name="AI Agent", category_path="tech/ai")
        db.add(niche)
        db.commit()
        assert reddit_signals_module._resolve_keyword_id("missing", "ai-agent", db) is None
    finally:
        db.close()


def test_resolve_reddit_niche_pk_numeric() -> None:
    assert reddit_signals_module._resolve_niche_pk("42", object()) == 42


def test_resolve_reddit_keyword_id_returns_none_when_niche_missing() -> None:
    db = _make_session()
    try:
        assert reddit_signals_module._resolve_keyword_id("alpha", "missing", db) is None
    finally:
        db.close()


def test_resolve_reddit_keyword_id_returns_none_when_keyword_empty() -> None:
    db = _make_session()
    try:
        niche = Niche(slug="ai-agent", name="AI Agent", category_path="tech/ai")
        db.add(niche)
        db.commit()
        assert reddit_signals_module._resolve_keyword_id("   ", "ai-agent", db) is None
    finally:
        db.close()


def test_build_subreddit_search_url() -> None:
    assert (
        reddit_signals_module.build_subreddit_search_url("Entrepreneur", "fiverr")
        == "https://www.reddit.com/r/Entrepreneur/search/?q=fiverr&restrict_sr=1&t=year"
    )


def test_build_subreddit_search_url_encodes_spaces() -> None:
    url = reddit_signals_module.build_subreddit_search_url("freelance", "buyer intent")
    assert "buyer%20intent" in url
    assert "+" not in url


def test_parse_post_count_90d_mixed() -> None:
    now = time.time()
    old_timestamp = now - (100 * 24 * 3600)
    posts = [
        {"created_utc": now - 100},
        {"created_utc": now - 200},
        {"created_utc": old_timestamp},
    ]
    assert reddit_signals_module.parse_reddit_post_count_90d(posts) == 2


def test_select_top_posts_limit() -> None:
    posts = [{"upvotes": idx} for idx in range(20)]
    selected = reddit_signals_module.select_top_posts_for_llm(posts, n=4)
    assert len(selected) == 4
    assert selected[0]["upvotes"] == 19


def test_build_demand_signal_json_includes_confidence_adjustment() -> None:
    payload = reddit_signals_module.build_reddit_demand_signal_json(
        post_count_90d=12,
        demand_intent_score=None,
        intent_phrases=["need help"],
        subreddits_searched=["Entrepreneur"],
    )
    assert payload["post_count_90d"] == 12
    assert payload["reddit_post_count_90d"] == 12
    assert payload["confidence_adjustment"] == -0.05
