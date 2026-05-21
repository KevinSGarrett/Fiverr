"""Unit tests for Stage 13 saturation model analysis."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from src.analysis import saturation_model
from src.models.database import create_session_factory, initialize_database
from src.models.market import Keyword, SaturationScore
from src.models.niche import Niche
from src.models.search_result import SearchResult


def _make_session():
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    return session_factory()


def _seed_niche(session: Any, slug: str = "test_niche") -> Niche:
    niche = Niche(slug=slug, name=slug.replace("_", " ").title(), category_path="programming-tech/testing")
    session.add(niche)
    session.commit()
    session.refresh(niche)
    return niche


def _seed_keyword(session: Any, niche: Niche, keyword_text: str) -> Keyword:
    keyword = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text.lower(),
    )
    session.add(keyword)
    session.commit()
    session.refresh(keyword)
    return keyword


def _seed_search_result(
    session: Any,
    *,
    keyword_id: int,
    run_id: str,
    gig_cards: list[dict[str, Any]],
    total_result_count: int,
) -> SearchResult:
    row = SearchResult(
        keyword_id=keyword_id,
        run_id=run_id,
        page_collected=1,
        rank=1,
        gig_cards=gig_cards,
        total_result_count=total_result_count,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_tokenize_removes_stop_words() -> None:
    tokens = saturation_model.tokenize_title("I will create the best python automation workflow")
    assert "will" not in tokens
    assert "create" not in tokens
    assert "best" not in tokens
    assert "python" in tokens


def test_tokenize_lowercase_and_regex() -> None:
    tokens = saturation_model.tokenize_title("PYTHON-API, Scraper!!! v2")
    assert tokens == {"python", "api", "scraper"}


def test_jaccard_identical_sets_returns_1() -> None:
    assert saturation_model.jaccard_similarity({"python", "scraper"}, {"python", "scraper"}) == 1.0


def test_jaccard_disjoint_sets_returns_0() -> None:
    assert saturation_model.jaccard_similarity({"python"}, {"design"}) == 0.0


def test_duplication_rate_zero_when_all_unique() -> None:
    cards = [
        {"gig_title": "I will build python scraper"},
        {"gig_title": "I will design logo package"},
        {"gig_title": "I will write sales emails"},
    ]
    assert saturation_model.calculate_title_duplication_rate(cards) == 0.0


def test_duplication_rate_one_when_all_identical() -> None:
    cards = [{"gig_title": "I will build python scraper"} for _ in range(5)]
    assert saturation_model.calculate_title_duplication_rate(cards) == 1.0


def test_duplication_rate_with_two_gigs_below_threshold() -> None:
    cards = [
        {"gig_title": "I will build python scraper"},
        {"gig_title": "I will design brand logo"},
    ]
    assert saturation_model.calculate_title_duplication_rate(cards) == 0.0


def test_duplication_rate_partial_duplicates() -> None:
    cards = [
        {"gig_title": "I will build python web scraper"},
        {"gig_title": "I will create python web scraper"},
        {"gig_title": "I will design modern logo kit"},
        {"gig_title": "I will write outreach email copy"},
    ]
    assert saturation_model.calculate_title_duplication_rate(cards) == 0.5


def test_duplication_rate_returns_zero_for_single_gig() -> None:
    assert saturation_model.calculate_title_duplication_rate([{"gig_title": "I will build python scraper"}]) == 0.0


def test_price_compression_zero_for_diverse_prices() -> None:
    cards = [{"starting_price": value} for value in [5, 20, 50, 100, 200, 320]]
    score = saturation_model.calculate_price_compression(cards, niche_context={"historical_median_price": 50})
    assert score < 0.5


def test_price_compression_high_for_uniform_prices() -> None:
    cards = [{"starting_price": 20.0} for _ in range(10)]
    score = saturation_model.calculate_price_compression(cards, niche_context={"historical_median_price": 40.0})
    assert score > 0.9


def test_price_compression_default_for_insufficient_data() -> None:
    cards = [{"starting_price": 15.0}, {"starting_price": 25.0}, {"starting_price": 35.0}]
    assert saturation_model.calculate_price_compression(cards, niche_context={}) == 0.3


def test_seller_overlap_zero_all_unique_sellers() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "unique_overlap")
        keyword_a = _seed_keyword(session, niche, "python scraper")
        keyword_b = _seed_keyword(session, niche, "ai automation")
        _seed_search_result(
            session,
            keyword_id=keyword_a.id,
            run_id="run-overlap-1",
            total_result_count=200,
            gig_cards=[{"seller_username": f"seller_a_{idx}"} for idx in range(5)],
        )
        _seed_search_result(
            session,
            keyword_id=keyword_b.id,
            run_id="run-overlap-1",
            total_result_count=200,
            gig_cards=[{"seller_username": f"seller_b_{idx}"} for idx in range(5)],
        )
        assert saturation_model.calculate_seller_overlap(keyword_a.id, "unique_overlap", session) == 0.0
    finally:
        session.close()


def test_seller_overlap_high_same_sellers_everywhere() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "high_overlap")
        keyword_a = _seed_keyword(session, niche, "python scraper")
        keyword_b = _seed_keyword(session, niche, "ai automation")
        sellers = [{"seller_username": username} for username in ["seller1", "seller2", "seller3", "seller4", "seller5"]]
        _seed_search_result(
            session,
            keyword_id=keyword_a.id,
            run_id="run-overlap-2",
            total_result_count=250,
            gig_cards=sellers,
        )
        _seed_search_result(
            session,
            keyword_id=keyword_b.id,
            run_id="run-overlap-2",
            total_result_count=250,
            gig_cards=sellers,
        )
        assert saturation_model.calculate_seller_overlap(keyword_a.id, "high_overlap", session) == 1.0
    finally:
        session.close()


def test_seller_overlap_single_keyword_returns_zero() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "single_keyword_overlap")
        keyword = _seed_keyword(session, niche, "python scraper")
        _seed_search_result(
            session,
            keyword_id=keyword.id,
            run_id="run-overlap-3",
            total_result_count=100,
            gig_cards=[{"seller_username": "seller_only"}],
        )
        assert saturation_model.calculate_seller_overlap(keyword.id, "single_keyword_overlap", session) == 0.0
    finally:
        session.close()


def test_saturation_score_formula_components_weighted_correctly(monkeypatch) -> None:
    fake_result = SimpleNamespace(gig_cards=[{"gig_title": "x", "starting_price": 10}], total_result_count=1_000)
    monkeypatch.setattr(saturation_model, "get_latest_search_result", lambda *_args, **_kwargs: fake_result)
    monkeypatch.setattr(saturation_model, "calculate_title_duplication_rate", lambda *_args, **_kwargs: 0.4)
    monkeypatch.setattr(saturation_model, "calculate_price_compression", lambda *_args, **_kwargs: 0.5)
    monkeypatch.setattr(saturation_model, "calculate_seller_overlap", lambda *_args, **_kwargs: 0.2)
    monkeypatch.setattr(saturation_model, "get_llm_saturation_score", lambda *_args, **_kwargs: 80.0)

    score = saturation_model.calculate_saturation_score(
        keyword_id=1,
        niche_id="niche",
        db=None,
        niche_context={"median_result_count": 500},
    )
    assert score == 60.0


def test_saturation_score_clamped_to_0_100(monkeypatch) -> None:
    fake_result = SimpleNamespace(gig_cards=[{"gig_title": "x", "starting_price": 10}], total_result_count=10_000)
    monkeypatch.setattr(saturation_model, "get_latest_search_result", lambda *_args, **_kwargs: fake_result)
    monkeypatch.setattr(saturation_model, "calculate_title_duplication_rate", lambda *_args, **_kwargs: 1.0)
    monkeypatch.setattr(saturation_model, "calculate_price_compression", lambda *_args, **_kwargs: 1.0)
    monkeypatch.setattr(saturation_model, "calculate_seller_overlap", lambda *_args, **_kwargs: 1.0)
    monkeypatch.setattr(saturation_model, "get_llm_saturation_score", lambda *_args, **_kwargs: 200.0)

    high = saturation_model.calculate_saturation_score(
        keyword_id=1,
        niche_id="niche",
        db=None,
        niche_context={"median_result_count": 500},
    )
    assert high == 100.0

    monkeypatch.setattr(saturation_model, "calculate_title_duplication_rate", lambda *_args, **_kwargs: 0.0)
    monkeypatch.setattr(saturation_model, "calculate_price_compression", lambda *_args, **_kwargs: 0.0)
    monkeypatch.setattr(saturation_model, "calculate_seller_overlap", lambda *_args, **_kwargs: 0.0)
    monkeypatch.setattr(saturation_model, "get_llm_saturation_score", lambda *_args, **_kwargs: -200.0)

    low = saturation_model.calculate_saturation_score(
        keyword_id=1,
        niche_id="niche",
        db=None,
        niche_context={"median_result_count": 500},
    )
    assert low == 0.0


def test_saturation_score_returns_default_without_search_result(monkeypatch) -> None:
    monkeypatch.setattr(saturation_model, "get_latest_search_result", lambda *_args, **_kwargs: None)
    score = saturation_model.calculate_saturation_score(
        keyword_id=1,
        niche_id="niche",
        db=None,
        niche_context={"median_result_count": 500},
    )
    assert score == 50.0


def test_saturation_score_high_for_commoditized_niche() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "commoditized")
        keyword_a = _seed_keyword(session, niche, "python scraper")
        keyword_b = _seed_keyword(session, niche, "automation scripts")

        shared_cards = [
            {
                "gig_title": "I will build python web scraper automation",
                "starting_price": 10.0,
                "seller_username": f"shared_seller_{idx % 5}",
            }
            for idx in range(30)
        ]
        _seed_search_result(
            session,
            keyword_id=keyword_a.id,
            run_id="run-commoditized",
            total_result_count=3_500,
            gig_cards=shared_cards,
        )
        _seed_search_result(
            session,
            keyword_id=keyword_b.id,
            run_id="run-commoditized",
            total_result_count=3_000,
            gig_cards=shared_cards,
        )

        score = saturation_model.calculate_saturation_score(
            keyword_id=keyword_a.id,
            niche_id="commoditized",
            db=session,
            niche_context={"median_result_count": 500, "historical_median_price": 25.0},
        )
        assert score > 70.0
    finally:
        session.close()


def test_run_saturation_writes_per_keyword() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "run_saturation")
        keyword_a = _seed_keyword(session, niche, "python scraper")
        keyword_b = _seed_keyword(session, niche, "automation scripts")
        cards = [{"gig_title": "I will build python scraper", "starting_price": 20.0, "seller_username": "seller1"}]
        _seed_search_result(session, keyword_id=keyword_a.id, run_id="run-stage13", total_result_count=900, gig_cards=cards)
        _seed_search_result(session, keyword_id=keyword_b.id, run_id="run-stage13", total_result_count=800, gig_cards=cards)

        result = asyncio.run(
            saturation_model.run_saturation_analysis_for_niche(
                niche_id="run_saturation",
                run_id="run-stage13",
                db=session,
                config={"niches": [{"niche_id": "run_saturation", "is_active": True}]},
            )
        )
        rows = session.scalars(select(SaturationScore)).all()
        assert result["analyzed"] is True
        assert result["keywords_analyzed"] == 2
        assert len(rows) == 2
    finally:
        session.close()


def test_run_saturation_empty_niche_returns_false() -> None:
    session = _make_session()
    try:
        _seed_niche(session, "empty_saturation")
        result = asyncio.run(
            saturation_model.run_saturation_analysis_for_niche(
                niche_id="empty_saturation",
                run_id="run-empty",
                db=session,
                config={"niches": [{"niche_id": "empty_saturation", "is_active": True}]},
            )
        )
        assert result["analyzed"] is False
        assert result["reason"] == "no_keywords"
    finally:
        session.close()


def test_run_saturation_returns_avg_score(monkeypatch) -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "avg_saturation")
        keyword_a = _seed_keyword(session, niche, "python scraper")
        keyword_b = _seed_keyword(session, niche, "automation scripts")
        _seed_search_result(
            session,
            keyword_id=keyword_a.id,
            run_id="run-avg",
            total_result_count=100,
            gig_cards=[{"gig_title": "x", "starting_price": 10.0, "seller_username": "s1"}],
        )
        _seed_search_result(
            session,
            keyword_id=keyword_b.id,
            run_id="run-avg",
            total_result_count=100,
            gig_cards=[{"gig_title": "x", "starting_price": 10.0, "seller_username": "s1"}],
        )

        values = iter([40.0, 60.0])

        def _fake_components(*_args, **_kwargs):
            value = next(values)
            return {
                "saturation_score": value,
                "count_score": value,
                "title_dup_score": value,
                "price_score": value,
                "overlap_score": value,
                "llm_class_score": value,
                "title_duplication_rate": 0.0,
                "price_compression_rate": 0.3,
                "seller_overlap_rate": 0.0,
                "explanation_text": "mocked",
            }

        monkeypatch.setattr(saturation_model, "_calculate_saturation_components", _fake_components)
        result = asyncio.run(
            saturation_model.run_saturation_analysis_for_niche(
                niche_id="avg_saturation",
                run_id="run-avg",
                db=session,
                config={"niches": [{"niche_id": "avg_saturation", "is_active": True}]},
            )
        )
        assert result["avg_saturation"] == 50.0
    finally:
        session.close()


def test_niche_context_defaults_used() -> None:
    session = _make_session()
    try:
        _seed_niche(session, "context_defaults")
        context = saturation_model.build_niche_context("context_defaults", session, niche_context=None)
        assert context["median_result_count"] == 500.0
        assert "historical_median_price" not in context
    finally:
        session.close()


def test_niche_context_overrides_defaults() -> None:
    session = _make_session()
    try:
        _seed_niche(session, "context_overrides")
        context = saturation_model.build_niche_context(
            "context_overrides",
            session,
            niche_context={"median_result_count": 900, "historical_median_price": 42},
        )
        assert context["median_result_count"] == 900.0
        assert context["historical_median_price"] == 42.0
    finally:
        session.close()

