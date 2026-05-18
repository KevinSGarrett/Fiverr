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
from src.collection.workflows.gig_detail import GigDetailWorkflow
from src.collection.workflows.google_trends import GoogleTrendsWorkflow
from src.collection.workflows.keyword_expansion import (
    KeywordExpansionWorkflow,
    run_keyword_expansion,
    run_keyword_expansion_stub,
)
from src.collection.workflows.niche_init import run_niche_initialization
from src.collection.workflows.reddit_signals import RedditSignalWorkflow
from src.collection.workflows.seller_profile import SellerProfileWorkflow


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
