"""Unit tests for collection workflow Stage 1/2 stubs."""

from __future__ import annotations

import asyncio
import builtins
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from src.collection import autocomplete as autocomplete_module
from src.collection import community_signals as community_signals_module
from src.collection import external_signals as external_signals_module
from src.collection import gig_detail as gig_detail_module
from src.collection import keyword_expansion as keyword_expansion_module
from src.collection import seller_profile as seller_profile_module
from src.collection.workflows.auto_promotion import AutoPromotionWorkflow
from src.collection.workflows.autocomplete import AutocompleteWorkflow
from src.collection.workflows.fiverr_search import (
    FiverrSearchWorkflow,
    _extract_gig_card,
    _parse_price,
    _parse_result_count,
    _queue_gig_detail_jobs,
    _safe_attribute,
    build_fiverr_search_url,
    is_keyword_only_depth,
    parse_gig_cards_from_page,
    run_fiverr_search_collection,
    should_collect_page_2,
)
from src.collection.workflows.gig_detail import (
    GigDetailWorkflow,
    _parse_rating,
    _parse_review_count,
    build_gig_detail_url,
    get_top_n_gig_urls_for_keyword,
    is_gig_removed,
    parse_gig_detail_fields,
    run_gig_detail_collection,
    should_skip_gig_detail,
)
from src.collection.workflows.google_trends import GoogleTrendsWorkflow
from src.collection.workflows.keyword_expansion import (
    KeywordExpansionWorkflow,
    run_keyword_expansion,
    run_keyword_expansion_stub,
)
from src.collection.workflows.niche_init import run_niche_initialization
from src.collection.workflows.reddit_signals import RedditSignalWorkflow
from src.collection.workflows.seller_profile import (
    SellerProfileWorkflow,
    build_seller_profile_url,
    parse_seller_profile_fields,
    run_seller_profile_collection,
    should_skip_seller_profile,
)
from src.collection.workflows.youtube_count import YoutubeCountWorkflow


def _run(coro):
    return asyncio.run(coro)


def test_niche_init_empty_niches() -> None:
    result = _run(run_niche_initialization(config={"niches": []}, db=None, run_id="run-1"))
    assert result["niches_processed"] == 0
    assert result["niche_specs"] == []


def test_niche_init_single_niche() -> None:
    config = {"niches": [{"niche_id": "ai_saas", "depth": "standard", "seed_keywords": ["mvp", "prd"]}]}
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-1"))
    assert result["niches_processed"] == 1
    assert result["niche_specs"][0]["niche_id"] == "ai_saas"
    assert result["niche_specs"][0]["seed_count"] == 2


def test_niche_init_seed_loading() -> None:
    config = {
        "niches": [
            {"niche_id": "ai_saas", "seed_keywords": ["  roadmap ", "", "Roadmap", "pricing  ", None]}
        ]
    }
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-2"))
    assert result["seed_keywords"]["ai_saas"] == ["roadmap", "pricing"]


def test_niche_init_depth_resolved(monkeypatch) -> None:
    config = {"niches": [{"niche_id": "ai_saas", "depth": "standard", "seed_keywords": ["mvp"]}]}
    monkeypatch.setattr("src.collection.workflows.niche_init._resolve_niche_depth", lambda *_: "full")
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-3"))
    assert result["niche_specs"][0]["depth"] == "full"


def test_niche_init_gate_check_applied() -> None:
    config = {
        "niches": [
            {
                "niche_id": "ai_saas",
                "depth": "full",
                "gating": {"enabled": True, "gate_passed": False},
                "seed_keywords": ["mvp"],
            }
        ]
    }
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-4"))
    assert result["niche_specs"][0]["depth"] == "keyword_only"


def test_niche_init_gate_check_passed() -> None:
    config = {
        "niches": [
            {
                "niche_id": "ai_saas",
                "depth": "standard",
                "gating": {"enabled": True, "gate_passed": True},
                "seed_keywords": ["mvp"],
            }
        ]
    }
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-5"))
    assert result["niche_specs"][0]["depth"] == "standard"


def test_niche_init_dry_run_default() -> None:
    config = {"niches": [{"niche_id": "ai_saas", "seed_keywords": ["one", "two", "three", "four"]}]}
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-6"))
    assert result["dry_run"] is True
    assert result["niche_specs"][0]["seeds"] == ["one", "two", "three"]


def test_keyword_expansion_dry_run() -> None:
    result = _run(
        run_keyword_expansion(
            niche_id="ai_saas",
            seeds=["mvp"],
            depth="standard",
            run_id="run-7",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["dry_run"] is True
    assert result["keywords_queued"] == 0


def test_w2_full_pipeline_dry_run_all_flags_active() -> None:
    all_real_flags = {
        "step_2a_fiverr_autocomplete": True,
        "step_2c_llm_generation": True,
        "step_2d_llm_relevance_filter": True,
        "step_2f_llm_intent_classification": True,
        "step_2g_embedding_generation": True,
    }
    with patch("src.collection.workflows.keyword_expansion._FEATURE_FLAGS", all_real_flags):
        result = _run(
            run_keyword_expansion(
                niche_id="ai_saas",
                seeds=["mvp", "roadmap"],
                depth="standard",
                run_id="run-w2-dry-all-flags",
                db=None,
                session_manager=AsyncMock(),
                pacing_manager=AsyncMock(),
                dry_run=True,
                llm_client=AsyncMock(),
            )
        )

    assert result["dry_run"] is True
    assert result["niche_id"] == "ai_saas"
    assert "sources" in result
    assert set(result["sources"].keys()) == {"fiverr_autocomplete", "google_suggest", "llm_generated"}


def test_keyword_expansion_real_path_returns_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_fetch(_seed: str, _pacing_manager: object) -> list[str]:
        return ["mvp roadmap", "MVP Roadmap"]

    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion._fetch_google_suggest",
        _fake_fetch,
    )

    result = _run(
        run_keyword_expansion(
            niche_id="ai_saas",
            seeds=["mvp"],
            depth="standard",
            run_id="run-8",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=False,
        )
    )
    assert result["dry_run"] is False
    assert result["keywords_queued"] == 1


def test_workflow_niche_id_in_result() -> None:
    result = _run(
        run_keyword_expansion(
            niche_id="my_niche",
            seeds=[],
            depth="keyword_only",
            run_id="run-9",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["niche_id"] == "my_niche"


def test_niche_init_loads_config_when_none(monkeypatch) -> None:
    class _Loader:
        def load(self):
            class _Cfg:
                def model_dump(self):
                    return {"niches": [{"niche_id": "loaded", "seed_keywords": ["x"]}]}

            return _Cfg()

    monkeypatch.setattr("src.config.loader.ConfigLoader", _Loader)
    result = _run(run_niche_initialization(config=None, db=None, run_id="run-10"))
    assert result["niches_processed"] == 1


def test_niche_init_accepts_dict_niches_map() -> None:
    config = {"niches": {"a": {"niche_id": "a", "seed_keywords": ["a1"]}}}
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-11"))
    assert result["niches_processed"] == 1


def test_niche_init_skips_missing_niche_id() -> None:
    config = {"niches": [{"seed_keywords": ["x"]}]}
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-12"))
    assert result["niches_processed"] == 0


def test_niche_init_handles_non_list_seed_container() -> None:
    config = {"niches": [{"niche_id": "bad", "seed_keywords": "not-a-list"}]}
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-13"))
    assert result["seed_keywords"]["bad"] == []


def test_niche_init_handles_invalid_niches_container() -> None:
    result = _run(run_niche_initialization(config={"niches": "invalid"}, db=None, run_id="run-13b"))
    assert result["niches_processed"] == 0
    assert result["niche_specs"] == []


def test_niche_init_load_seeds_drops_whitespace_only_values() -> None:
    config = {"niches": [{"niche_id": "n1", "seed_keywords": ["   ", "valid"]}]}
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-13c"))
    assert result["seed_keywords"]["n1"] == ["valid"]


def test_resolve_niche_depth_falls_back_when_sqlalchemy_unavailable(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "sqlalchemy.orm":
            raise ImportError("forced")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from src.collection.workflows.niche_init import _resolve_niche_depth

    assert _resolve_niche_depth("n1", {"depth": "standard"}, db=object()) == "standard"


def test_resolve_niche_depth_handles_model_lookup_failure(monkeypatch) -> None:
    from src.collection.workflows.niche_init import _resolve_niche_depth

    class _FakeSession:
        pass

    monkeypatch.setattr("sqlalchemy.orm.Session", _FakeSession)
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "src.models.niche":
            raise RuntimeError("forced")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert _resolve_niche_depth("n1", {"depth": "full"}, db=_FakeSession()) == "full"


def test_resolve_niche_depth_uses_db_override(monkeypatch) -> None:
    from src.collection.workflows.niche_init import _resolve_niche_depth

    class _Record:
        depth = "full"

    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return _Record()

    class _FakeSession:
        def query(self, *_args, **_kwargs):
            return _Query()

    monkeypatch.setattr("sqlalchemy.orm.Session", _FakeSession)
    assert _resolve_niche_depth("n1", {"depth": "standard"}, db=_FakeSession()) == "full"


def test_keyword_expansion_stub_alias() -> None:
    result = _run(
        run_keyword_expansion_stub(
            niche_id="ai_saas",
            seeds=[],
            depth="standard",
            run_id="run-14",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["dry_run"] is True


def test_fiverr_search_dry_run() -> None:
    result = _run(
        run_fiverr_search_collection(
            keyword_id=1,
            keyword_text="python automation",
            niche_id="ai_saas",
            depth="standard",
            run_id="run-15",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["dry_run"] is True
    assert result["keyword_id"] == 1
    assert result["keyword_text"] == "python automation"
    assert result["gig_cards_collected"] == 0
    assert result["gig_urls_queued"] == 0


def test_fiverr_search_result_structure() -> None:
    result = _run(
        run_fiverr_search_collection(
            keyword_id=7,
            keyword_text="test keyword",
            niche_id="niche",
            depth="full",
            run_id="run-16",
            db=None,
            session_manager=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    required_keys = {
        "keyword_id",
        "keyword_text",
        "total_result_count",
        "gig_cards_collected",
        "gig_urls_queued",
        "dry_run",
        "niche_id",
    }
    assert required_keys.issubset(result.keys())


class _FakeElement:
    def __init__(self, text: str | None = None, attrs: dict[str, str] | None = None):
        self._text = text
        self._attrs = attrs or {}

    async def inner_text(self) -> str:
        return self._text or ""

    async def get_attribute(self, key: str) -> str | None:
        return self._attrs.get(key)


class _FakeCard:
    def __init__(self, mapping: dict[str, _FakeElement | None]):
        self.mapping = mapping

    async def query_selector(self, selector: str):
        return self.mapping.get(selector)


class _FakeNode:
    def __init__(self, text: str | None = None, mapping: dict[str, _FakeNode | None] | None = None):
        self._text = text
        self._mapping = mapping or {}

    async def inner_text(self) -> str:
        return self._text or ""

    async def query_selector(self, selector: str):
        return self._mapping.get(selector)


def _build_real_search_mocks(
    *, count_text: str = "1,234 results", cards: list[_FakeCard] | None = None
) -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock(return_value=_FakeElement(count_text))
    page.query_selector_all = AsyncMock(return_value=cards or [])

    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    session_manager.close_page = AsyncMock()

    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()
    return page, session_manager, pacing_manager


def _build_real_gig_detail_mocks(
    *,
    title: str = "Gig Title",
    description: str = "Long description",
    has_video: bool = True,
    portfolio_count: int = 2,
    review_text: str | None = "1,234 reviews",
    rating_text: str | None = "4.9",
) -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    from src.collection.fiverr_selectors import (
        GIG_DETAIL_DESCRIPTION,
        GIG_DETAIL_FAQ_ANSWER,
        GIG_DETAIL_FAQ_ITEMS,
        GIG_DETAIL_FAQ_QUESTION,
        GIG_DETAIL_PACKAGE_PRICE,
        GIG_DETAIL_PACKAGES,
        GIG_DETAIL_PORTFOLIO,
        GIG_DETAIL_RATING,
        GIG_DETAIL_REVIEW_COUNT,
        GIG_DETAIL_TAGS,
        GIG_DETAIL_TITLE,
        GIG_DETAIL_VIDEO,
    )

    package = _FakeNode(mapping={GIG_DETAIL_PACKAGE_PRICE: _FakeNode("$50")})
    faq = _FakeNode(mapping={GIG_DETAIL_FAQ_QUESTION: _FakeNode("Q1"), GIG_DETAIL_FAQ_ANSWER: _FakeNode("A1")})
    tags = [_FakeNode("Tag 1"), _FakeNode("Tag 2")]
    portfolios = [_FakeNode("P") for _ in range(portfolio_count)]

    selector_map = {
        GIG_DETAIL_TITLE: _FakeNode(title),
        GIG_DETAIL_DESCRIPTION: _FakeNode(description),
        GIG_DETAIL_VIDEO: _FakeNode("video") if has_video else None,
        GIG_DETAIL_REVIEW_COUNT: _FakeNode(review_text) if review_text else None,
        GIG_DETAIL_RATING: _FakeNode(rating_text) if rating_text else None,
    }
    selector_all_map = {
        GIG_DETAIL_PACKAGES: [package],
        GIG_DETAIL_TAGS: tags,
        GIG_DETAIL_FAQ_ITEMS: [faq],
        GIG_DETAIL_PORTFOLIO: portfolios,
    }

    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock(side_effect=lambda selector: selector_map.get(selector))
    page.query_selector_all = AsyncMock(side_effect=lambda selector: selector_all_map.get(selector, []))

    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    session_manager.close_page = AsyncMock()

    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()
    return page, session_manager, pacing_manager


def test_w3_real_navigates_to_correct_url() -> None:
    page, session_manager, pacing_manager = _build_real_search_mocks()
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python automation",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-17",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )

    page.goto.assert_awaited_once_with(
        "https://www.fiverr.com/search/gigs?query=python%20automation",
        wait_until="domcontentloaded",
        timeout=30_000,
    )


def test_w3_real_calls_pacing_wait() -> None:
    _page, session_manager, pacing_manager = _build_real_search_mocks()
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-18",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    pacing_manager.wait.assert_awaited_once_with("fiverr_search", dry_run=False)


def test_w3_real_extracts_result_count() -> None:
    _page, session_manager, pacing_manager = _build_real_search_mocks(count_text="9,876 results for test")
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        result = _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-19",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    assert result["total_result_count"] == 9876


def test_w3_real_collects_gig_cards() -> None:
    card = _FakeCard(
        {
            "[data-testid='gig-title'], .gig-title": _FakeElement("Gig A"),
            "[data-testid='seller-name'], .seller-name": _FakeElement("seller_a"),
            "[data-testid='seller-level-badge'], .seller-level-badge": _FakeElement("Level 2"),
            "[data-testid='starting-price'], .gig-price": _FakeElement("$95"),
            "[data-testid='rating-count-number'], .reviews-count": _FakeElement("123"),
            "a[data-testid='gig-link'], a.gig-link": _FakeElement(attrs={"href": "https://www.fiverr.com/gig/a"}),
            "[data-testid='promoted-badge'], .promoted-badge": None,
        }
    )
    _page, session_manager, pacing_manager = _build_real_search_mocks(cards=[card])
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        result = _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-20",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    assert result["gig_cards_collected"] == 1


def test_w3_real_writes_search_result() -> None:
    _page, session_manager, pacing_manager = _build_real_search_mocks()
    with patch("src.collection.workflows.fiverr_search.write_search_result") as write_mock, patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        _run(
            run_fiverr_search_collection(
                keyword_id=7,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-21",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    assert write_mock.call_args.kwargs["keyword_id"] == 7
    assert write_mock.call_args.kwargs["run_id"] == "run-21"
    assert write_mock.call_args.kwargs["page_collected"] == 1


def _make_job_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE run_logs (run_id VARCHAR(64) PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE niche_configs (niche_id VARCHAR(64) PRIMARY KEY)"))
        conn.execute(text("INSERT INTO run_logs(run_id) VALUES ('run-queue')"))
        conn.execute(text("INSERT INTO niche_configs(niche_id) VALUES ('ai_saas')"))
    from src.models.job import Job

    Job.__table__.create(bind=engine, checkfirst=True)
    maker = sessionmaker(bind=engine, future=True)
    return maker()


def test_w3_real_queues_gig_detail_jobs() -> None:
    session = _make_job_test_session()
    try:
        gig_cards = [{"gig_url": f"https://www.fiverr.com/gig/{i}"} for i in range(12)]
        queued = _queue_gig_detail_jobs(10, "ai_saas", "run-queue", gig_cards, "standard", session)
        assert queued == 10
        rows = session.execute(text("SELECT COUNT(*) FROM jobs")).scalar_one()
        assert rows == 10
    finally:
        session.close()


def test_w3_real_keyword_only_no_jobs() -> None:
    session = _make_job_test_session()
    try:
        queued = _queue_gig_detail_jobs(
            10,
            "ai_saas",
            "run-queue",
            [{"gig_url": "https://www.fiverr.com/gig/a"}],
            "keyword_only",
            session,
        )
        assert queued == 0
        rows = session.execute(text("SELECT COUNT(*) FROM jobs")).scalar_one()
        assert rows == 0
    finally:
        session.close()


def test_w3_real_enqueues_autocomplete_job_when_enabled() -> None:
    _page, session_manager, pacing_manager = _build_real_search_mocks()
    db = object()
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ), patch("src.collection.workflows.fiverr_search.enqueue_autocomplete_job", return_value=True) as enqueue_mock:
        result = _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-22a",
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
                enqueue_autocomplete=True,
            )
        )

    enqueue_mock.assert_called_once_with(
        keyword_id=2,
        keyword_text="python",
        niche_id="ai_saas",
        run_id="run-22a",
        db=db,
    )
    assert result["autocomplete_jobs_queued"] == 1


def test_w3_real_closes_page_on_success() -> None:
    _page, session_manager, pacing_manager = _build_real_search_mocks()
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-22",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    session_manager.close_page.assert_awaited_once()


def test_w3_real_closes_page_on_error() -> None:
    page, session_manager, pacing_manager = _build_real_search_mocks()
    page.goto.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-23",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    session_manager.close_page.assert_awaited_once()


def test_w3_real_max_20_cards() -> None:
    cards = [
        _FakeCard(
            {
                "[data-testid='gig-title'], .gig-title": _FakeElement(f"Gig {i}"),
                "a[data-testid='gig-link'], a.gig-link": _FakeElement(
                    attrs={"href": f"https://www.fiverr.com/gig/{i}"}
                ),
                "[data-testid='promoted-badge'], .promoted-badge": None,
            }
        )
        for i in range(25)
    ]
    _page, session_manager, pacing_manager = _build_real_search_mocks(cards=cards)
    with patch("src.collection.workflows.fiverr_search.write_search_result"), patch(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", return_value=0
    ):
        result = _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-24",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                dry_run=False,
            )
        )
    assert result["gig_cards_collected"] == 20


def test_parse_result_count_with_commas() -> None:
    assert _parse_result_count("1,234 results for test") == 1234


def test_parse_result_count_none() -> None:
    assert _parse_result_count(None) is None


def test_parse_price_dollar() -> None:
    assert _parse_price("$95") == 95.0


def test_parse_price_with_commas() -> None:
    assert _parse_price("From $1,200") == 1200.0


def test_parse_price_none() -> None:
    assert _parse_price(None) is None


def test_safe_attribute_returns_none_when_selector_missing() -> None:
    card = _FakeCard({})
    value = _run(_safe_attribute(card, "a[data-testid='gig-link'], a.gig-link", "href"))
    assert value is None


def test_safe_attribute_returns_none_when_attribute_missing() -> None:
    card = _FakeCard({"a[data-testid='gig-link'], a.gig-link": _FakeElement(attrs={})})
    value = _run(_safe_attribute(card, "a[data-testid='gig-link'], a.gig-link", "href"))
    assert value is None


def test_extract_gig_card_returns_none_when_url_and_title_missing() -> None:
    card = _FakeCard(
        {
            "a[data-testid='gig-link'], a.gig-link": _FakeElement(attrs={}),
            "[data-testid='gig-title'], .gig-title": _FakeElement(""),
        }
    )
    assert _run(_extract_gig_card(card, 1)) is None


def test_queue_jobs_skips_cards_without_url() -> None:
    session = _make_job_test_session()
    try:
        gig_cards = [{"seller_username": "no-url-card"}, {"gig_url": "https://www.fiverr.com/gig/ok"}]
        queued = _queue_gig_detail_jobs(10, "ai_saas", "run-queue", gig_cards, "standard", session)
        assert queued == 1
        rows = session.execute(text("SELECT COUNT(*) FROM jobs")).scalar_one()
        assert rows == 1
    finally:
        session.close()


def test_queue_jobs_full_depth() -> None:
    session = _make_job_test_session()
    try:
        gig_cards = [{"gig_url": f"https://www.fiverr.com/gig/{i}"} for i in range(30)]
        queued = _queue_gig_detail_jobs(10, "ai_saas", "run-queue", gig_cards, "full", session)
        assert queued == 20
        rows = session.execute(text("SELECT COUNT(*) FROM jobs")).scalar_one()
        assert rows == 20
    finally:
        session.close()


def test_build_fiverr_search_url_basic() -> None:
    assert (
        build_fiverr_search_url("python automation")
        == "https://www.fiverr.com/search/gigs?query=python%20automation"
    )


def test_build_fiverr_search_url_spaces() -> None:
    url = build_fiverr_search_url("a b c")
    assert "%20" in url
    assert "+" not in url


def test_build_fiverr_search_url_special_chars() -> None:
    url = build_fiverr_search_url("c++/node.js")
    assert url == "https://www.fiverr.com/search/gigs?query=c%2B%2B/node.js"


def test_parse_gig_cards_empty() -> None:
    assert parse_gig_cards_from_page({"cards": []}) == []


def test_parse_gig_cards_stub() -> None:
    cards = [{"title": "test"}]
    assert parse_gig_cards_from_page({"cards": cards}) == cards


def test_should_collect_page_2_full_high_intent() -> None:
    assert should_collect_page_2("full", "HIGH_INTENT") is True


def test_should_collect_page_2_standard_depth() -> None:
    assert should_collect_page_2("standard", "HIGH_INTENT") is False


def test_should_collect_page_2_informational() -> None:
    assert should_collect_page_2("full", "INFORMATIONAL") is False


def test_is_keyword_only_depth() -> None:
    assert is_keyword_only_depth("keyword_only") is True
    assert is_keyword_only_depth("standard") is False


def test_gig_detail_dry_run() -> None:
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/my-gig",
            keyword_id=123,
            niche_id="ai_saas",
            depth="standard",
            run_id="run-18",
            db=None,
            session_manager=None,
            pacing_manager=None,
            checkpoint_manager=None,
            dry_run=True,
        )
    )
    assert result["gig_url"] == "https://www.fiverr.com/seller/my-gig"
    assert result["keyword_id"] == 123
    assert result["collected"] is False
    assert result["seller_queued"] is False
    assert result["fields_collected"] == []
    assert result["dry_run"] is True


def test_gig_detail_result_keys() -> None:
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-2",
            keyword_id=1,
            niche_id="niche",
            depth="full",
            run_id="run-19",
            db=None,
            session_manager=None,
            pacing_manager=None,
            checkpoint_manager=None,
            dry_run=True,
        )
    )
    required_keys = {
        "gig_url",
        "keyword_id",
        "collected",
        "seller_queued",
        "fields_collected",
        "dry_run",
        "note",
    }
    assert required_keys.issubset(result.keys())


def test_gig_detail_not_implemented() -> None:
    page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-3",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-20",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["detail_collected"] is True
    session_manager.close_page.assert_awaited_once()
    page.goto.assert_awaited_once()


def test_w4_real_navigates_to_gig_url() -> None:
    page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    gig_url = "https://www.fiverr.com/seller/gig-4"
    _run(
        run_gig_detail_collection(
            gig_url=gig_url,
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-1",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    page.goto.assert_awaited_once_with(build_gig_detail_url(gig_url), wait_until="domcontentloaded", timeout=30_000)


def test_w4_real_calls_pacing_wait() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-5",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-2",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    pacing_manager.wait.assert_awaited_once_with("fiverr_gig_detail", dry_run=False)


def test_w4_real_extracts_title() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(title="Exact Gig Title")
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-title",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-3",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["title"] == "Exact Gig Title"


def test_w4_real_extracts_description() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(description="Detailed description body")
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-description",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-4",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["description_length"] == len("Detailed description body")


def test_w4_real_video_present() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(has_video=True)
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-video",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-5",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["has_video"] is True


def test_w4_real_video_absent() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(has_video=False)
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-no-video",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-6",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["has_video"] is False


def test_w4_real_portfolio_count() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(portfolio_count=3)
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-portfolio",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-7",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["portfolio_count"] == 3


def test_w4_real_updates_gig_row() -> None:
    from src.models.gig import Gig

    engine = create_engine("sqlite:///:memory:", future=True)
    Gig.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()
    try:
        db.add(Gig(gig_url="https://www.fiverr.com/seller/gig-db", seller_username="seller"))
        db.commit()

        _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(title="DB Title")
        _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/gig-db",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-w4-8",
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )
        row = db.query(Gig).filter(Gig.gig_url == "https://www.fiverr.com/seller/gig-db").first()
        assert row is not None
        assert row.detail_collected is True
        assert row.detail_collected_at is not None
        assert row.gig_title_full == "DB Title"
    finally:
        db.close()


def test_w4_real_closes_page_on_success() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-close-ok",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-9",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    session_manager.close_page.assert_awaited_once()


def test_w4_real_closes_page_on_error() -> None:
    page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    page.goto.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/gig-close-error",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-w4-10",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )
    session_manager.close_page.assert_awaited_once()


def test_w4_real_no_gig_row_in_db() -> None:
    from src.models.gig import Gig

    engine = create_engine("sqlite:///:memory:", future=True)
    Gig.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()
    try:
        _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
        result = _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/not-found",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-w4-11",
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )
        assert result["detail_collected"] is True
    finally:
        db.close()


def test_parse_review_count_with_commas() -> None:
    assert _parse_review_count("1,234 reviews") == 1234


def test_parse_review_count_none() -> None:
    assert _parse_review_count(None) is None


def test_parse_rating_decimal() -> None:
    assert _parse_rating("Rated 4.9 stars") == 4.9


def test_parse_rating_none() -> None:
    assert _parse_rating(None) is None


def test_get_top_n_full_depth() -> None:
    assert get_top_n_gig_urls_for_keyword(1, "full", db=None) == []


def test_get_top_n_keyword_only() -> None:
    assert get_top_n_gig_urls_for_keyword(1, "keyword_only", db=None) == []


def test_get_top_n_dict_db() -> None:
    assert get_top_n_gig_urls_for_keyword(1, "standard", db={"fake": "db"}) == []


def test_get_top_n_with_sqlalchemy_session_returns_stub_list() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", future=True)
    session = sessionmaker(bind=engine)()
    try:
        assert get_top_n_gig_urls_for_keyword(1, "standard", db=session) == []
    finally:
        session.close()


def test_get_top_n_handles_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    original_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object):
        if name == "sqlalchemy.orm":
            raise ImportError("sqlalchemy unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    assert get_top_n_gig_urls_for_keyword(1, "full", db=None) == []


def test_parse_gig_detail_fields_stub() -> None:
    result = parse_gig_detail_fields({"any": "payload"})
    expected_keys = {
        "gig_title_full",
        "description_text",
        "packages",
        "gig_extras",
        "tags",
        "faq_text",
        "faq_entries",
        "video_present",
        "portfolio_count",
        "review_count_exact",
        "rating_exact",
        "review_snippets",
        "orders_in_queue",
        "thumbnail_url",
    }
    assert set(result.keys()) == expected_keys
    assert all(value is None for value in result.values())


def test_is_gig_removed_404() -> None:
    assert is_gig_removed({"status_code": 404}) is True


def test_is_gig_removed_false() -> None:
    assert is_gig_removed({"status_code": 200, "gig_removed": False}) is False


def test_should_skip_gig_stub() -> None:
    assert should_skip_gig_detail("https://www.fiverr.com/seller/gig-4", "run-21", db=None) is False


def test_seller_profile_dry_run() -> None:
    result = _run(
        run_seller_profile_collection(
            seller_username="top_seller",
            niche_id="ai_saas",
            run_id="run-22",
            db=None,
            session_manager=None,
            pacing_manager=None,
            checkpoint_manager=None,
            dry_run=True,
        )
    )
    assert result["seller_username"] == "top_seller"
    assert result["collected"] is False
    assert result["fields_collected"] == []
    assert result["dry_run"] is True


def test_seller_profile_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        _run(
            run_seller_profile_collection(
                seller_username="top_seller",
                niche_id="ai_saas",
                run_id="run-23",
                db=None,
                session_manager=None,
                pacing_manager=None,
                checkpoint_manager=None,
                dry_run=False,
            )
        )


def test_build_seller_profile_url() -> None:
    assert build_seller_profile_url("myuser") == "https://www.fiverr.com/myuser"


def test_parse_seller_fields_stub() -> None:
    result = parse_seller_profile_fields({"some": "payload"})
    expected_keys = {
        "seller_level",
        "member_since",
        "response_time",
        "response_rate",
        "languages",
        "bio_text",
        "total_reviews",
        "total_gigs",
        "active_gig_titles",
        "portfolio_count",
        "badges",
    }
    assert set(result.keys()) == expected_keys
    assert all(value is None for value in result.values())


def test_should_skip_seller_stub() -> None:
    assert should_skip_seller_profile("top_seller", "run-24", db=None) is False


def test_wrapper_workflow_modules_and_pending_paths() -> None:
    assert KeywordExpansionWorkflow().run() is keyword_expansion_module
    assert AutocompleteWorkflow().run() is autocomplete_module
    assert GigDetailWorkflow().run() is gig_detail_module
    assert GoogleTrendsWorkflow().run() is external_signals_module
    assert YoutubeCountWorkflow().run() is external_signals_module
    assert RedditSignalWorkflow().run() is community_signals_module
    assert SellerProfileWorkflow().run() is seller_profile_module
    with pytest.raises(NotImplementedError):
        FiverrSearchWorkflow().run()
    with pytest.raises(NotImplementedError):
        AutoPromotionWorkflow().run()
