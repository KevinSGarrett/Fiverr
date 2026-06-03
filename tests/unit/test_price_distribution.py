from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models import Base, Gig, Keyword, Niche
from src.pricing.analysis import (
    PriceDistribution,
    RawPriceData,
    _compute_tier_stats,
    _extract_tier_prices,
    _find_price_gaps,
    _simple_cluster_detection,
    analyze_niche_pricing,
    analyze_price_dispersion,
    analyze_price_distribution,
    calculate_price_review_correlation,
    detect_price_clusters,
    detect_price_gaps,
    extract_raw_price_data_from_db,
    extract_extras_pricing,
    extract_tier_prices,
    get_keywords_for_niche,
    get_niche_name,
    persist_keyword_pricing,
    run_price_distribution_analysis,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def _seed_keyword(session: Session, slug: str = "python_automation") -> tuple[Niche, Keyword]:
    niche = Niche(slug=slug, name=slug, category_path="Programming & Tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword=f"{slug} keyword", normalized_keyword=f"{slug} keyword")
    session.add(keyword)
    session.flush()
    return niche, keyword


def _gig(prices: dict[str, float] | list[dict[str, float]] | str | None, reviews: int = 0) -> SimpleNamespace:
    return SimpleNamespace(packages=prices, review_count=reviews, review_count_exact=reviews)


def test_analyze_price_distribution_with_normal_data() -> None:
    gigs = [_gig({"basic": {"price": 50 + i * 10}, "standard": {"price": 90 + i * 10}, "premium": {"price": 140 + i * 10}}) for i in range(6)]
    values = analyze_price_distribution.__globals__["get_gigs_for_keyword"]
    analyze_price_distribution.__globals__["get_gigs_for_keyword"] = lambda keyword_id, db: gigs
    try:
        output = analyze_price_distribution(1, object())
    finally:
        analyze_price_distribution.__globals__["get_gigs_for_keyword"] = values
    assert set(output.keys()) == {"basic", "standard", "premium"}
    assert output["basic"].n_gigs == 6


def test_analyze_price_distribution_sparse_data_no_crash() -> None:
    gigs = [_gig({"basic": {"price": 50}}), _gig({"basic": {"price": 60}})]
    original = analyze_price_distribution.__globals__["get_gigs_for_keyword"]
    analyze_price_distribution.__globals__["get_gigs_for_keyword"] = lambda keyword_id, db: gigs
    try:
        output = analyze_price_distribution(1, object())
    finally:
        analyze_price_distribution.__globals__["get_gigs_for_keyword"] = original
    assert output == {}


def test_detect_price_clusters_bimodal_distribution() -> None:
    prices = np.array([50, 52, 53, 55, 57, 180, 182, 185, 190, 195], dtype=float)
    clusters = detect_price_clusters(prices)
    assert len(clusters) >= 2


def test_detect_price_clusters_small_n_fallback() -> None:
    prices = np.array([50, 55, 60, 200], dtype=float)
    clusters = detect_price_clusters(prices)
    assert clusters == _simple_cluster_detection(prices)


def test_detect_price_gaps_large_gap() -> None:
    prices = np.array([50, 55, 60, 200, 205], dtype=float)
    gaps = detect_price_gaps(prices)
    assert gaps and gaps[0]["gap_width"] > 100


def test_detect_price_gaps_no_significant_gap() -> None:
    prices = np.array([50, 55, 60, 65, 70], dtype=float)
    assert detect_price_gaps(prices) == []


def test_calculate_price_review_correlation_strong_positive() -> None:
    gigs = [_gig({"basic": {"price": 20 + i * 20}}, reviews=i * 20) for i in range(1, 7)]
    original = calculate_price_review_correlation.__globals__["get_gigs_for_keyword"]
    calculate_price_review_correlation.__globals__["get_gigs_for_keyword"] = lambda keyword_id, db: gigs
    try:
        output = calculate_price_review_correlation(1, object())
    finally:
        calculate_price_review_correlation.__globals__["get_gigs_for_keyword"] = original
    assert output["moat_strength"] in {"MEDIUM", "HIGH"}


def test_calculate_price_review_correlation_weak() -> None:
    gigs = [_gig({"basic": {"price": 100}}, reviews=i * 10) for i in range(1, 8)]
    original = calculate_price_review_correlation.__globals__["get_gigs_for_keyword"]
    calculate_price_review_correlation.__globals__["get_gigs_for_keyword"] = lambda keyword_id, db: gigs
    try:
        output = calculate_price_review_correlation(1, object())
    finally:
        calculate_price_review_correlation.__globals__["get_gigs_for_keyword"] = original
    assert output["moat_strength"] == "LOW"


def test_calculate_price_review_correlation_insufficient_data() -> None:
    gigs = [_gig({"basic": {"price": 100}}, reviews=5) for _ in range(3)]
    original = calculate_price_review_correlation.__globals__["get_gigs_for_keyword"]
    calculate_price_review_correlation.__globals__["get_gigs_for_keyword"] = lambda keyword_id, db: gigs
    try:
        output = calculate_price_review_correlation(1, object())
    finally:
        calculate_price_review_correlation.__globals__["get_gigs_for_keyword"] = original
    assert output["interpretation"] == "insufficient_data"


def test_analyze_price_dispersion_commodity() -> None:
    dist = PriceDistribution(10, 90, 110, 100, 100, 100, 5, 95, 105, 10, 92, 108, 0.1, [], [], 0.1)
    assert analyze_price_dispersion(dist)["market_type"] == "COMMODITY"


def test_analyze_price_dispersion_fragmented() -> None:
    dist = PriceDistribution(10, 20, 300, 120, 100, 90, 65, 60, 170, 110, 30, 280, 0.8, [], [], 0.6)
    assert analyze_price_dispersion(dist)["market_type"] == "FRAGMENTED"


def test_extract_tier_prices_handles_dict() -> None:
    assert extract_tier_prices([_gig({"basic": {"price": 75}})], "basic") == [75.0]


def test_extract_tier_prices_handles_list() -> None:
    assert extract_tier_prices([_gig([{"price": 75}, {"price": 150}, {"price": 300}])], "basic") == [75.0]


def test_extract_tier_prices_handles_json_string_packages() -> None:
    payload = json.dumps({"basic": {"price": 80}, "standard": {"price": 140}})
    assert extract_tier_prices([_gig(payload)], "basic") == [80.0]


def test_extract_tier_prices_handles_none_packages() -> None:
    assert extract_tier_prices([_gig(None)], "basic") == []


def test_extract_tier_prices_excludes_non_positive_prices() -> None:
    assert extract_tier_prices([_gig({"basic": {"price": 0}}), _gig({"basic": {"price": -5}})], "basic") == []


def test_price_distribution_dataclass_fields_present() -> None:
    dist = PriceDistribution(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, [], [], 0.0)
    assert dist.coefficient_of_variation == 0.0


def test_analyze_niche_pricing_returns_correct_niche_id() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "niche_a")
    session.add(Gig(keyword_id=keyword.id, seller_username="a", gig_url="u://1", packages={"basic": {"price": 70}}))
    session.add(Gig(keyword_id=keyword.id, seller_username="b", gig_url="u://2", packages={"basic": {"price": 90}}))
    session.add(Gig(keyword_id=keyword.id, seller_username="c", gig_url="u://3", packages={"basic": {"price": 110}}))
    session.commit()
    result = analyze_niche_pricing(niche.slug, session)
    assert result["niche_id"] == niche.slug
    session.close()


def test_analyze_niche_pricing_handles_no_keywords() -> None:
    session = _session()
    assert analyze_niche_pricing("missing", session) == {}
    session.close()


def test_analyze_niche_pricing_aggregates_medians() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "niche_b")
    for idx, price in enumerate([50, 100, 150], start=1):
        session.add(Gig(keyword_id=keyword.id, seller_username=f"s{idx}", gig_url=f"u://b{idx}", packages={"basic": {"price": price}}))
    session.commit()
    result = analyze_niche_pricing(niche.slug, session)
    assert result["basic_median"] == 100.0
    session.close()


def test_analyze_niche_pricing_moat_strength_aggregated() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "niche_c")
    for idx in range(1, 7):
        session.add(Gig(keyword_id=keyword.id, seller_username=f"s{idx}", gig_url=f"u://c{idx}", packages={"basic": {"price": 40 + idx * 20}}, review_count=idx * 20))
    session.commit()
    result = analyze_niche_pricing(niche.slug, session)
    assert result["moat_strength"] in {"LOW", "MEDIUM", "HIGH"}
    session.close()


def test_analyze_niche_pricing_with_single_keyword() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "niche_d")
    for idx, price in enumerate([80, 90, 100], start=1):
        session.add(Gig(keyword_id=keyword.id, seller_username=f"v{idx}", gig_url=f"u://d{idx}", packages={"basic": {"price": price}}))
    session.commit()
    result = analyze_niche_pricing(niche.slug, session)
    assert result["keywords_analyzed"] == 1
    session.close()


def test_price_cluster_sorting_highest_count_first() -> None:
    prices = np.array([50, 50, 50, 100, 100, 200], dtype=float)
    clusters = _simple_cluster_detection(prices)
    assert clusters[0]["count"] >= clusters[-1]["count"]


def test_price_gap_sorting_widest_first() -> None:
    gaps = detect_price_gaps(np.array([10, 20, 80, 200, 205], dtype=float), min_gap_pct=0.1)
    assert gaps[0]["gap_width"] >= gaps[-1]["gap_width"]


def test_right_skew_distribution_positive_skewness() -> None:
    dist = PriceDistribution(8, 20, 300, 90, 55, 50, 80, 40, 100, 60, 25, 250, 1.2, [], [], 0.7)
    assert dist.skewness > 0


def test_extras_pricing_empty_extras() -> None:
    result = extract_extras_pricing([SimpleNamespace(gig_extras=None)])
    assert result["min"] is None and result["avg_count"] == 0.0


def test_extras_pricing_handles_json_string() -> None:
    payload = json.dumps([{"name": "fast", "price": 20}, {"name": "extra", "price": 40}])
    result = extract_extras_pricing([SimpleNamespace(gig_extras=payload)])
    assert result["max"] == 40.0


@pytest.mark.parametrize(
    ("packages", "tier", "expected"),
    [
        ({"basic": {"price": 10}}, "basic", [10.0]),
        ({"basic": {"price": 20}}, "basic", [20.0]),
        ({"basic": {"price": 30}}, "basic", [30.0]),
        ({"standard": {"price": 40}}, "standard", [40.0]),
        ({"standard": {"price": 50}}, "standard", [50.0]),
        ({"standard": {"price": 60}}, "standard", [60.0]),
        ({"premium": {"price": 70}}, "premium", [70.0]),
        ({"premium": {"price": 80}}, "premium", [80.0]),
        ({"premium": {"price": 90}}, "premium", [90.0]),
        ([{"price": 15}, {"price": 25}, {"price": 35}], "basic", [15.0]),
        ([{"price": 16}, {"price": 26}, {"price": 36}], "basic", [16.0]),
        ([{"price": 17}, {"price": 27}, {"price": 37}], "basic", [17.0]),
        ([{"price": 18}, {"price": 28}, {"price": 38}], "standard", [28.0]),
        ([{"price": 19}, {"price": 29}, {"price": 39}], "standard", [29.0]),
        ([{"price": 20}, {"price": 30}, {"price": 40}], "standard", [30.0]),
        ([{"price": 21}, {"price": 31}, {"price": 41}], "premium", [41.0]),
        ([{"price": 22}, {"price": 32}, {"price": 42}], "premium", [42.0]),
        ([{"price": 23}, {"price": 33}, {"price": 43}], "premium", [43.0]),
        (json.dumps({"basic": {"price": 55}}), "basic", [55.0]),
        (json.dumps({"basic": {"price": 65}}), "basic", [65.0]),
    ],
)
def test_extract_tier_prices_matrix(packages: object, tier: str, expected: list[float]) -> None:
    assert extract_tier_prices([_gig(packages)], tier) == expected


def test_run_price_distribution_analysis_persists_row() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "raw_run")
    raw = RawPriceData(
        keyword_id=keyword.id,
        run_id="run-raw",
        basic_prices=[50, 60, 70, 80, 90],
        standard_prices=[90, 100, 120, 140, 160],
        premium_prices=[150, 180, 210, 240, 270],
        seller_review_counts=[0, 5, 10, 55, 90],
        seller_levels=["A"] * 5,
    )
    row = run_price_distribution_analysis(raw, session)
    session.commit()
    assert row.basic_n == 5 and row.market_type is not None
    session.close()


def test_extract_raw_price_data_from_db_returns_payload() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "raw_extract")
    for idx in range(1, 4):
        session.add(
            Gig(
                keyword_id=keyword.id,
                seller_username=f"s{idx}",
                gig_url=f"u://raw/{idx}",
                packages={"basic": {"price": 40 + idx * 5}, "standard": {"price": 80 + idx * 10}, "premium": {"price": 120 + idx * 20}},
                review_count=idx * 10,
            )
        )
    session.commit()
    raw = extract_raw_price_data_from_db(keyword.id, "run-x", session)
    assert raw is not None and len(raw.basic_prices) == 3
    session.close()


def test_persist_keyword_pricing_returns_price_analysis() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "persist_kw")
    for idx in range(1, 5):
        session.add(
            Gig(
                keyword_id=keyword.id,
                seller_username=f"s{idx}",
                gig_url=f"u://persist/{idx}",
                packages={"basic": {"price": 50 + idx * 10}, "standard": {"price": 100 + idx * 10}, "premium": {"price": 150 + idx * 20}},
                review_count=idx * 10,
            )
        )
    session.commit()
    row, snapshot = persist_keyword_pricing(keyword.id, "run-persist", session)
    assert row is not None and snapshot is None
    session.close()


def test_get_keywords_for_niche_numeric_and_slug() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "lookup_niche")
    by_slug = get_keywords_for_niche(niche.slug, session)
    by_numeric = get_keywords_for_niche(str(niche.id), session)
    assert by_slug and by_numeric and by_slug[0].id == keyword.id
    session.close()


def test_get_niche_name_returns_slug_name() -> None:
    session = _session()
    niche, _ = _seed_keyword(session, "name_niche")
    assert get_niche_name(niche.slug, session) == niche.name
    session.close()


def test_compute_tier_stats_and_find_gaps_compatibility_helpers() -> None:
    stats = _compute_tier_stats([10, 20, 30, 60])
    gaps = _find_price_gaps([10, 20, 30, 60])
    assert stats["n"] == 4 and isinstance(gaps, list)


def test_extract_tier_prices_legacy_helper_with_metadata_json() -> None:
    gig = SimpleNamespace(starting_price=55, metadata_json={"packages": {"standard": {"price": 90}, "premium": {"price": 150}}}, packages=None)
    basic, standard, premium = _extract_tier_prices(gig)
    assert basic == 55 and standard == 90 and premium == 150
