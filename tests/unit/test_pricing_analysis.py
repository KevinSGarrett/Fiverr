"""Unit tests for pricing distribution analysis runner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, Keyword, Niche, PriceAnalysis, SearchResult, Seller
from src.pricing.analysis import (
    RawPriceData,
    _calculate_review_premium,
    _classify_market_type,
    _classify_moat_strength,
    _compute_tier_stats,
    _find_price_gaps,
    extract_raw_price_data_from_db,
    run_price_distribution_analysis,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _seed_keyword(session: Session) -> int:
    niche = Niche(slug="analysis-tests", name="Analysis Tests", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="analysis keyword",
        normalized_keyword="analysis keyword",
        metadata_json={},
    )
    session.add(keyword)
    session.commit()
    return int(keyword.id)


def _raw(**overrides: object) -> RawPriceData:
    payload = {
        "keyword_id": 11,
        "run_id": "run-11",
        "basic_prices": [50.0, 55.0, 75.0, 80.0, 120.0],
        "standard_prices": [90.0, 110.0, 140.0],
        "premium_prices": [160.0, 210.0, 275.0],
        "seller_review_counts": [0, 2, 60, 90, 4],
        "seller_levels": ["NO_LEVEL", "NO_LEVEL", "LEVEL_2", "TRS", "NO_LEVEL"],
    }
    payload.update(overrides)
    return RawPriceData(**payload)


def test_compute_tier_stats_normal() -> None:
    stats = _compute_tier_stats([50, 75, 100, 125, 150])
    assert stats["n"] == 5
    assert stats["median"] == 100
    assert stats["mean"] == 100
    assert stats["min"] == 50
    assert stats["max"] == 150
    assert stats["cv"] is not None
    assert stats["skewness"] is not None


def test_compute_tier_stats_empty() -> None:
    stats = _compute_tier_stats([])
    assert all(value is None for value in stats.values())


def test_compute_tier_stats_single() -> None:
    stats = _compute_tier_stats([99.0])
    assert stats["n"] == 1
    assert stats["cv"] == 0.0
    assert stats["skewness"] == 0.0


def test_classify_commodity() -> None:
    assert _classify_market_type({"cv": 0.10}) == "COMMODITY"


def test_classify_wide_spread() -> None:
    assert _classify_market_type({"cv": 0.50}) == "WIDE_SPREAD"


def test_classify_fragmented() -> None:
    assert _classify_market_type({"cv": 0.70}) == "FRAGMENTED"


def test_moat_high() -> None:
    raw = _raw(basic_prices=[100.0, 110.0, 145.0, 150.0], seller_review_counts=[0, 1, 80, 99])
    assert _classify_moat_strength(raw) == "HIGH"


def test_moat_low() -> None:
    raw = _raw(basic_prices=[100.0, 101.0, 108.0, 109.0], seller_review_counts=[0, 1, 80, 99])
    assert _classify_moat_strength(raw) == "LOW"


def test_moat_missing_data() -> None:
    raw = _raw(seller_review_counts=[])
    assert _classify_moat_strength(raw) == "UNKNOWN"


def test_find_gaps_meaningful() -> None:
    gaps = _find_price_gaps([10.0, 11.0, 12.0, 40.0, 41.0])
    assert gaps
    assert gaps[0]["gap_midpoint"] > 20


def test_find_gaps_no_gaps() -> None:
    assert _find_price_gaps([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]) == []


def test_find_gaps_too_few_prices() -> None:
    assert _find_price_gaps([10.0, 100.0]) == []


def test_run_analysis_dict_db() -> None:
    row = run_price_distribution_analysis(_raw(), db={})
    assert isinstance(row, PriceAnalysis)
    assert row.keyword_id == 11
    assert row.basic_n == 5


def test_run_analysis_orm_db() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    raw = _raw(keyword_id=keyword_id, run_id="run-orm")
    merge_spy = MagicMock(wraps=session.merge)
    commit_spy = MagicMock(wraps=session.commit)
    session.merge = merge_spy  # type: ignore[method-assign]
    session.commit = commit_spy  # type: ignore[method-assign]

    row = run_price_distribution_analysis(raw, db=session)
    assert row.run_id == "run-orm"
    assert merge_spy.call_count == 1
    assert commit_spy.call_count == 1
    session.close()


def test_run_analysis_review_premium() -> None:
    raw = _raw(basic_prices=[100.0, 100.0, 150.0, 160.0], seller_review_counts=[0, 3, 60, 75])
    row = run_price_distribution_analysis(raw, db={})
    assert row.review_premium is not None
    assert row.review_premium > 0


def test_extract_raw_price_data_no_gigs() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    raw = extract_raw_price_data_from_db(keyword_id=keyword_id, run_id="run-no-gigs", db=session)
    assert raw is None
    session.close()


def test_extract_raw_price_data_with_gigs() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    seller = Seller(seller_handle="analysis-seller", level="LEVEL_1")
    gig = Gig(
        seller=seller,
        title="Gig A",
        normalized_title="gig a",
        starting_price=75.0,
        review_count=9,
        metadata_json={"packages": {"standard": {"price": 110}, "premium": {"price": 160}}},
    )
    session.add_all([seller, gig])
    session.flush()
    session.add(SearchResult(keyword_id=keyword_id, rank=1, gig_id=gig.id, metadata_json={}))
    session.commit()

    raw = extract_raw_price_data_from_db(keyword_id=keyword_id, run_id="run-with-gigs", db=session)
    assert raw is not None
    assert raw.basic_prices == [75.0]
    assert raw.standard_prices == [110.0]
    assert raw.premium_prices == [160.0]
    assert raw.seller_levels == ["LEVEL_1"]
    session.close()


def test_calculate_review_premium_none_without_segments() -> None:
    raw = _raw(basic_prices=[100.0, 110.0], seller_review_counts=[10, 20])
    assert _calculate_review_premium(raw) is None


def test_calculate_review_premium_value() -> None:
    raw = _raw(basic_prices=[100.0, 100.0, 150.0, 170.0], seller_review_counts=[0, 2, 80, 120])
    assert _calculate_review_premium(raw) == 60.0


def test_extract_tier_prices_list_package_metadata() -> None:
    fake_gig = SimpleNamespace(
        starting_price=55.0,
        metadata_json={"packages": [{"price": 60}, {"price": 90}, {"price": 140}]},
    )
    raw = _raw(keyword_id=77, run_id="run-list-pkg", basic_prices=[], standard_prices=[], premium_prices=[], seller_review_counts=[], seller_levels=[])
    del raw  # maintain function-local scope checks for mypy

    from src.pricing.analysis import _extract_tier_prices

    basic, standard, premium = _extract_tier_prices(fake_gig)  # type: ignore[arg-type]
    assert basic == 60.0
    assert standard == 90.0
    assert premium == 140.0


def test_classify_market_type_unknown_when_cv_missing() -> None:
    assert _classify_market_type({"cv": None}) == "UNKNOWN"


def test_classify_moat_strength_medium() -> None:
    raw = _raw(basic_prices=[100.0, 105.0, 120.0, 125.0], seller_review_counts=[0, 1, 80, 90])
    assert _classify_moat_strength(raw) == "MEDIUM"


def test_classify_moat_strength_low_when_no_segment_groups() -> None:
    raw = _raw(basic_prices=[100.0, 110.0], seller_review_counts=[8, 9])
    assert _classify_moat_strength(raw) == "LOW"


def test_classify_moat_strength_low_when_new_average_non_positive() -> None:
    raw = _raw(basic_prices=[0.0, 0.0, 120.0, 130.0], seller_review_counts=[0, 1, 80, 90])
    assert _classify_moat_strength(raw) == "LOW"


def test_calculate_review_premium_none_without_prices_or_reviews() -> None:
    raw = _raw(basic_prices=[], seller_review_counts=[])
    assert _calculate_review_premium(raw) is None


def test_find_price_gaps_returns_empty_when_range_is_zero() -> None:
    assert _find_price_gaps([25.0, 25.0, 25.0]) == []


def test_extract_raw_price_data_returns_none_when_all_prices_missing() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    seller = Seller(seller_handle="analysis-no-prices", level="LEVEL_1")
    gig = Gig(
        seller=seller,
        title="Gig No Price",
        normalized_title="gig no price",
        starting_price=None,
        review_count=2,
        metadata_json={},
    )
    session.add_all([seller, gig])
    session.flush()
    session.add(SearchResult(keyword_id=keyword_id, rank=1, gig_id=gig.id, metadata_json={}))
    session.commit()
    assert extract_raw_price_data_from_db(keyword_id=keyword_id, run_id="run-no-prices", db=session) is None
    session.close()


def test_price_from_package_invalid_shapes_return_none() -> None:
    from src.pricing.analysis import _price_from_package

    assert _price_from_package({"price": None}) is None
    assert _price_from_package({"price": object()}) is None
    assert _price_from_package({"price": "not-a-number"}) is None
