"""Unit tests for pricing model and new-seller pricing calculator."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from run import cli
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Keyword, Niche, PriceAnalysis
from src.pricing import orchestrator as pricing_orchestrator
from src.pricing.new_seller_pricing import (
    PricingRecommendation,
    _assess_pricing_confidence,
    _build_price_ladder,
    _calculate_moat_adjustment,
    _calculate_undercut,
    _coerce_positive,
    _find_gap_opportunity,
    _get_floor_price,
    _lerp,
    _resolve_starter_prices,
    calculate_new_seller_pricing,
    generate_pricing_strategy_text,
    project_revenue_at_entry_pricing,
)


class _FakeQuery:
    def __init__(self, row: object | None) -> None:
        self._row = row

    def filter(self, *args: object, **kwargs: object) -> _FakeQuery:
        return self

    def first(self) -> object | None:
        return self._row


class _FakeDB:
    def __init__(self, keyword: object | None) -> None:
        self._keyword = keyword

    def query(self, model: object) -> _FakeQuery:
        del model
        return _FakeQuery(self._keyword)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _seed_keyword(session: Session) -> int:
    niche = Niche(slug="pricing-test", name="Pricing Tests", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="ai pricing test",
        normalized_keyword="ai pricing test",
        metadata_json={},
    )
    session.add(keyword)
    session.commit()
    return int(keyword.id)


def _price_analysis(**overrides: object) -> SimpleNamespace:
    base = {
        "market_type": "MODERATE_SPREAD",
        "moat_strength": "MEDIUM",
        "basic_n": 12,
        "basic_skewness": 0.1,
        "basic_median": 100.0,
        "standard_median": 200.0,
        "premium_median": 350.0,
        "basic_gaps": [],
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _niche_config() -> dict[str, object]:
    return {"starter_prices": {"basic": 95, "standard": 225, "premium": 395}}


def _pricing_recommendation(**overrides: object) -> PricingRecommendation:
    base = PricingRecommendation(
        keyword_id=7,
        keyword_text="pricing keyword",
        niche_id=1,
        entry_basic=65.0,
        entry_standard=145.0,
        entry_premium=280.0,
        acquisition_basic=55.0,
        acquisition_standard=130.0,
        acquisition_premium=266.0,
        price_ladder=[
            {"milestone_reviews": 0, "basic": 65.0},
            {"milestone_reviews": 5, "basic": 75.0},
            {"milestone_reviews": 10, "basic": 85.0},
            {"milestone_reviews": 25, "basic": 95.0},
            {"milestone_reviews": 50, "basic": 105.0},
            {"milestone_reviews": 100, "basic": 115.0},
        ],
        target_basic=115.0,
        target_standard=230.0,
        target_premium=375.0,
        undercut_pct=25.0,
        moat_adjustment=5.0,
        gap_pricing_used=False,
        gap_target=None,
        market_type="WIDE_SPREAD",
        confidence="HIGH",
    )
    values = base.__dict__.copy()
    values.update(overrides)
    return PricingRecommendation(**values)


def test_price_analysis_table_name() -> None:
    assert PriceAnalysis.__tablename__ == "price_analyses"


def test_price_analysis_create_all() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    assert "price_analyses" in inspect(engine).get_table_names()


def test_price_analysis_insert() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    row = PriceAnalysis(keyword_id=keyword_id, run_id="run-1", basic_median=100.0)
    session.add(row)
    session.commit()
    fetched = session.query(PriceAnalysis).filter(PriceAnalysis.keyword_id == keyword_id).first()
    assert fetched is not None
    assert fetched.run_id == "run-1"
    session.close()


def test_price_analysis_nullable_json() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    row = PriceAnalysis(keyword_id=keyword_id, run_id="run-2", basic_gaps=None)
    session.add(row)
    session.commit()
    assert row.basic_gaps is None
    session.close()


def test_price_analysis_unique_constraint() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    session.add(PriceAnalysis(keyword_id=keyword_id, run_id="dupe"))
    session.commit()
    session.add(PriceAnalysis(keyword_id=keyword_id, run_id="dupe"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.close()


def test_calculate_undercut_commodity() -> None:
    assert _calculate_undercut(_price_analysis(market_type="COMMODITY", basic_n=10, basic_skewness=0.0)) == 0.10


def test_calculate_undercut_wide_spread() -> None:
    assert _calculate_undercut(_price_analysis(market_type="WIDE_SPREAD", basic_n=10, basic_skewness=0.0)) == 0.25


def test_calculate_undercut_crowded() -> None:
    assert _calculate_undercut(_price_analysis(market_type="MODERATE_SPREAD", basic_n=20, basic_skewness=0.0)) == 0.25


def test_calculate_moat_high() -> None:
    assert _calculate_moat_adjustment(_price_analysis(moat_strength="HIGH")) == 0.10


def test_calculate_moat_low() -> None:
    assert _calculate_moat_adjustment(_price_analysis(moat_strength="LOW")) == 0.00


def test_find_gap_below_median() -> None:
    gap, used = _find_gap_opportunity(
        _price_analysis(
            basic_gaps=[
                {"gap_midpoint": 70.0, "gap_width": 20.0, "pct_of_range": 18.0},
                {"gap_midpoint": 80.0, "gap_width": 10.0, "pct_of_range": 16.0},
            ]
        )
    )
    assert used is True
    assert gap == 70.0


def test_find_gap_no_gaps() -> None:
    gap, used = _find_gap_opportunity(_price_analysis(basic_gaps=[]))
    assert gap is None
    assert used is False


def test_floor_prices_basic() -> None:
    assert _get_floor_price("basic", {}) == 15.0


def test_floor_prices_premium() -> None:
    assert _get_floor_price("premium", {}) == 50.0


def test_price_ladder_6_milestones() -> None:
    ladder = _build_price_ladder(60.0, 120.0, 180.0, 100.0, 200.0, 300.0)
    assert len(ladder) == 6


def test_price_ladder_milestone_0() -> None:
    ladder = _build_price_ladder(60.0, 120.0, 180.0, 100.0, 200.0, 300.0)
    assert ladder[0]["milestone_reviews"] == 0
    assert ladder[0]["basic"] == 60.0


def test_price_ladder_milestone_100() -> None:
    ladder = _build_price_ladder(60.0, 120.0, 180.0, 100.0, 200.0, 300.0)
    assert ladder[-1]["milestone_reviews"] == 100
    assert ladder[-1]["premium"] == 300.0


def test_lerp_midpoint() -> None:
    assert _lerp(0, 100, 0.5) == 50


def test_calculate_new_seller_pricing_basic() -> None:
    db = _FakeDB(SimpleNamespace(id=33, keyword="ai pricing", niche_id=7))
    pricing = calculate_new_seller_pricing(33, _price_analysis(), _niche_config(), db)
    assert pricing.keyword_id == 33
    assert pricing.keyword_text == "ai pricing"
    assert pricing.market_type == "MODERATE_SPREAD"
    assert isinstance(pricing.price_ladder, list)


def test_entry_less_than_standard() -> None:
    db = _FakeDB(SimpleNamespace(id=33, keyword="ai pricing", niche_id=7))
    pricing = calculate_new_seller_pricing(33, _price_analysis(), _niche_config(), db)
    assert pricing.entry_basic < pricing.entry_standard


def test_acquisition_less_than_entry() -> None:
    db = _FakeDB(SimpleNamespace(id=33, keyword="ai pricing", niche_id=7))
    analysis = _price_analysis(basic_median=120.0, standard_median=240.0, premium_median=420.0)
    pricing = calculate_new_seller_pricing(33, analysis, _niche_config(), db)
    assert pricing.acquisition_basic < pricing.entry_basic


def test_project_revenue_month_4() -> None:
    db = _FakeDB(SimpleNamespace(id=33, keyword="ai pricing", niche_id=7))
    pricing = calculate_new_seller_pricing(33, _price_analysis(), _niche_config(), db)
    projection = project_revenue_at_entry_pricing(pricing, _niche_config())
    month_4 = projection["month_4"]
    assert "orders_needed" in month_4
    assert "orders_per_month" in month_4
    assert "feasible" in month_4


def test_confidence_high_n() -> None:
    assert _assess_pricing_confidence(_price_analysis(basic_n=10)) == "HIGH"


def test_confidence_low_n() -> None:
    assert _assess_pricing_confidence(_price_analysis(basic_n=4)) == "LOW"


def test_calculate_undercut_handles_low_sample_and_negative_skew() -> None:
    value = _calculate_undercut(_price_analysis(market_type="FRAGMENTED", basic_n=2, basic_skewness=-0.5))
    assert value == 0.20


def test_find_gap_ignores_non_dict_entries() -> None:
    gap, used = _find_gap_opportunity(_price_analysis(basic_gaps=["skip", {"gap_midpoint": 70, "pct_of_range": 5}]))
    assert gap is None
    assert used is False


def test_resolve_starter_prices_supports_metadata_fallback() -> None:
    basic, standard, premium = _resolve_starter_prices(
        {"metadata": {"starter_price_basic": 80, "starter_price_standard": 190, "starter_price_premium": 330}}
    )
    assert (basic, standard, premium) == (80.0, 190.0, 330.0)


def test_coerce_positive_uses_fallback_for_invalid_values() -> None:
    assert _coerce_positive("bad", 42.0) == 42.0
    assert _coerce_positive(0, 42.0) == 42.0


def test_calculate_new_seller_pricing_fallback_when_median_none() -> None:
    db = _FakeDB(SimpleNamespace(id=99, keyword="fallback pricing", niche_id=4))
    analysis = _price_analysis(basic_median=None, standard_median=None, premium_median=None)
    pricing = calculate_new_seller_pricing(99, analysis, _niche_config(), db)
    assert pricing.target_basic == 95.0
    assert pricing.target_standard == 225.0
    assert pricing.target_premium == 415.0


def test_calculate_new_seller_pricing_uses_lower_gap_target() -> None:
    db = _FakeDB(SimpleNamespace(id=33, keyword="ai pricing", niche_id=7))
    analysis = _price_analysis(
        basic_median=100.0,
        basic_gaps=[{"gap_midpoint": 60.0, "gap_width": 20.0, "pct_of_range": 20.0}],
    )
    pricing = calculate_new_seller_pricing(33, analysis, _niche_config(), db)
    assert pricing.entry_basic == 60.0


def test_calculate_undercut_positive_skew_reduction() -> None:
    value = _calculate_undercut(_price_analysis(market_type="MODERATE_SPREAD", basic_n=10, basic_skewness=0.8))
    assert value == pytest.approx(0.15)


def test_confidence_medium_n() -> None:
    assert _assess_pricing_confidence(_price_analysis(basic_n=5)) == "MEDIUM"


def test_get_niche_config_for_keyword_from_session() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    config = {"niches": {"1": {"starter_prices": {"basic": 80, "standard": 160, "premium": 240}}}}
    niche_config = pricing_orchestrator._get_niche_config_for_keyword(keyword_id=keyword_id, db=session, config=config)
    assert niche_config["starter_prices"]["basic"] == 80
    session.close()


def test_get_niche_config_for_keyword_from_list_payload() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    config = {
        "niches": [
            {"niche_id": "999", "starter_prices": {"basic": 10, "standard": 20, "premium": 30}},
            {"niche_id": "1", "starter_prices": {"basic": 70, "standard": 140, "premium": 210}},
        ]
    }
    niche_config = pricing_orchestrator._get_niche_config_for_keyword(keyword_id=keyword_id, db=session, config=config)
    assert niche_config["starter_prices"]["basic"] == 70
    session.close()


def test_get_niche_config_for_keyword_list_skips_non_dict_and_returns_empty() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    config = {"niches": ["bad-entry", {"niche_id": "999", "starter_prices": {"basic": 10}}]}
    niche_config = pricing_orchestrator._get_niche_config_for_keyword(keyword_id=keyword_id, db=session, config=config)
    assert niche_config == {}
    session.close()


def test_run_pricing_stage_empty_keywords() -> None:
    summary = pricing_orchestrator.run_pricing_stage(
        run_id="run-empty",
        keyword_ids=[],
        db=object(),
        config={},
    )
    assert summary["analyzed"] == 0
    assert summary["priced"] == 0
    assert summary["failed"] == 0


def test_run_pricing_stage_no_gig_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pricing_orchestrator, "extract_raw_price_data_from_db", lambda **kwargs: None)
    summary = pricing_orchestrator.run_pricing_stage(
        run_id="run-no-gigs",
        keyword_ids=[11],
        db=object(),
        config={},
    )
    assert summary["analyzed"] == 0
    assert summary["priced"] == 0
    assert summary["failed"] == 1


def test_run_pricing_stage_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pricing_orchestrator, "extract_raw_price_data_from_db", lambda **kwargs: object())
    monkeypatch.setattr(pricing_orchestrator, "run_price_distribution_analysis", lambda raw, db: _price_analysis())
    monkeypatch.setattr(
        pricing_orchestrator,
        "calculate_new_seller_pricing",
        lambda keyword_id, price_analysis, niche_config, db: _pricing_recommendation(keyword_id=keyword_id),
    )
    summary = pricing_orchestrator.run_pricing_stage(
        run_id="run-success",
        keyword_ids=[101],
        db=object(),
        config={"niches": {}},
    )
    assert summary["analyzed"] == 1
    assert summary["priced"] == 1
    assert summary["failed"] == 0


def test_run_pricing_stage_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pricing_orchestrator, "extract_raw_price_data_from_db", lambda **kwargs: object())

    def _raise(*args: object, **kwargs: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(pricing_orchestrator, "run_price_distribution_analysis", _raise)
    summary = pricing_orchestrator.run_pricing_stage(
        run_id="run-exception",
        keyword_ids=[55],
        db=object(),
        config={},
    )
    assert summary["analyzed"] == 0
    assert summary["priced"] == 0
    assert summary["failed"] == 1


def test_generate_pricing_strategy_text_basic() -> None:
    text = generate_pricing_strategy_text(_pricing_recommendation())
    assert isinstance(text, str)
    assert "Enter at $65 Basic / $145 Standard / $280 Premium" in text


def test_generate_pricing_strategy_text_contains_ladder() -> None:
    text = generate_pricing_strategy_text(_pricing_recommendation())
    assert "Price ladder:" in text
    assert "r)" in text


def test_generate_pricing_strategy_text_gap_note() -> None:
    text = generate_pricing_strategy_text(_pricing_recommendation(gap_pricing_used=True, gap_target=72.0))
    assert "A price gap exists at $72." in text


def test_generate_pricing_strategy_text_no_gap() -> None:
    text = generate_pricing_strategy_text(_pricing_recommendation(gap_pricing_used=False, gap_target=None))
    assert "A price gap exists at" not in text


def test_price_analysis_mode_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("run.run_pipeline", lambda **kwargs: 0)
    runner = CliRunner()
    result = runner.invoke(cli, ["price-analysis"])
    assert result.exit_code == 0
