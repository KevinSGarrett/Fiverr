"""Unit tests for collection workflow Stage 1/2 stubs."""

from __future__ import annotations

import asyncio

import pytest
from src.collection import autocomplete as autocomplete_module
from src.collection import community_signals as community_signals_module
from src.collection import external_signals as external_signals_module
from src.collection import gig_detail as gig_detail_module
from src.collection import keyword_expansion as keyword_expansion_module
from src.collection import seller_profile as seller_profile_module
from src.collection.workflows.auto_promotion import AutoPromotionWorkflow
from src.collection.workflows.autocomplete import AutocompleteWorkflow
from src.collection.workflows.fiverr_search import FiverrSearchWorkflow
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
