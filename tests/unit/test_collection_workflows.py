"""Unit tests for collection workflow Stage 1/2 stubs."""

from __future__ import annotations

import asyncio
import builtins

import pytest
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
    build_fiverr_search_url,
    is_keyword_only_depth,
    parse_gig_cards_from_page,
    run_fiverr_search_collection,
    should_collect_page_2,
)
from src.collection.workflows.gig_detail import (
    GigDetailWorkflow,
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


def test_keyword_expansion_raises_without_dry_run() -> None:
    with pytest.raises(NotImplementedError):
        _run(
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


def test_fiverr_search_raises_without_dry_run() -> None:
    with pytest.raises(NotImplementedError):
        _run(
            run_fiverr_search_collection(
                keyword_id=2,
                keyword_text="python",
                niche_id="ai_saas",
                depth="standard",
                run_id="run-17",
                db=None,
                session_manager=None,
                pacing_manager=None,
                dry_run=False,
            )
        )


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
    with pytest.raises(NotImplementedError):
        _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/gig-3",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-20",
                db=None,
                session_manager=None,
                pacing_manager=None,
                checkpoint_manager=None,
                dry_run=False,
            )
        )


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
    assert RedditSignalWorkflow().run() is community_signals_module
    assert SellerProfileWorkflow().run() is seller_profile_module
    with pytest.raises(NotImplementedError):
        FiverrSearchWorkflow().run()
    with pytest.raises(NotImplementedError):
        AutoPromotionWorkflow().run()
