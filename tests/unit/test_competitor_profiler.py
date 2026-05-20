"""Unit tests for Stage 10 competitor profiling and seller strength helpers."""

from __future__ import annotations

import asyncio
import json

import pandas as pd
from sqlalchemy import select
from src.analysis.competitor_profiler import (
    compute_market_benchmarks,
    compute_new_seller_gap,
    compute_seller_level_distribution,
    extract_top_n_competitor_gigs,
    load_gig_data_for_niche,
    run_competitor_profiling_for_niche,
)
from src.analysis.seller_strength import classify_seller_tier, compute_seller_strength_score
from src.models.database import create_session_factory, initialize_database
from src.models.gig import Gig
from src.models.gig_quality_score import GigQualityScore
from src.models.market import CompetitorProfile, Keyword, write_competitor_profile
from src.models.niche import Niche
from src.models.search_result import SearchResult
from src.models.seller import Seller


def _run(coro):
    return asyncio.run(coro)


def _build_session() -> tuple[object, Niche]:
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()
    niche = Niche(slug="test_niche", name="Test Niche", category_path="programming-tech/testing")
    session.add(niche)
    session.commit()
    session.refresh(niche)
    return session, niche


def _seed_keyword(session: object, niche: Niche, keyword_text: str, vector: list[float]) -> Keyword:
    row = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text.lower(),
        embedding_vector=json.dumps(vector),
        external_source="seed",
        metadata_json={},
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _seed_gig(
    session: object,
    *,
    keyword: Keyword,
    run_id: str,
    gig_url: str,
    seller_username: str,
    rank: int,
    price: float | None,
    rating: float | None,
    review_count: int | None,
    has_video: bool | None,
    portfolio_count: int | None,
    delivery_days: int,
) -> Gig:
    gig = Gig(
        gig_url=gig_url,
        keyword_id=keyword.id,
        run_id=run_id,
        seller_username=seller_username,
        starting_price=price,
        rating_exact=rating,
        review_count_exact=review_count,
        orders_in_queue=rank + 1,
        video_present=has_video,
        portfolio_count=portfolio_count,
        packages=[{"name": "Basic", "price": price or 0.0, "delivery_days": delivery_days}],
        position=rank,
        detail_collected=True,
    )
    session.add(gig)
    session.flush()

    search_result = SearchResult(
        keyword_id=keyword.id,
        run_id=run_id,
        page_collected=rank,
        rank=rank,
        gig_id=gig.id,
        title=gig.gig_title_full,
    )
    session.add(search_result)
    session.commit()
    session.refresh(gig)
    return gig


def _seed_quality_score(
    session: object,
    *,
    gig: Gig,
    keyword: Keyword,
    run_id: str,
    has_video: bool | None,
    portfolio_count: int | None,
) -> None:
    row = GigQualityScore(
        gig_id=gig.id,
        gig_url=gig.gig_url,
        keyword_id=keyword.id,
        run_id=run_id,
        analysis_complete=True,
        video_present=has_video,
        portfolio_count=portfolio_count,
    )
    session.add(row)
    session.commit()


def _seed_seller(
    session: object,
    *,
    run_id: str,
    username: str,
    level: str | None,
    total_reviews: int,
    total_gigs: int,
    response_rate: str | None = "95%",
    member_since: str | None = "Jan 2020",
) -> None:
    row = Seller(
        seller_username=username,
        run_id=run_id,
        seller_level=level,
        total_reviews=total_reviews,
        total_gigs=total_gigs,
        response_rate=response_rate,
        member_since=member_since,
        profile_collected=True,
    )
    session.add(row)
    session.commit()


def _seed_competitor_fixture(session: object, niche: Niche, run_id: str = "run-stage10") -> None:
    keyword_one = _seed_keyword(session, niche, "python automation", [0.1, 0.2, 0.3])
    keyword_two = _seed_keyword(session, niche, "workflow automation", [0.12, 0.22, 0.32])

    gig_one = _seed_gig(
        session,
        keyword=keyword_one,
        run_id=run_id,
        gig_url="https://fiverr.com/gig/1",
        seller_username="seller_a",
        rank=1,
        price=50.0,
        rating=4.9,
        review_count=120,
        has_video=True,
        portfolio_count=4,
        delivery_days=3,
    )
    gig_two = _seed_gig(
        session,
        keyword=keyword_two,
        run_id=run_id,
        gig_url="https://fiverr.com/gig/2",
        seller_username="seller_b",
        rank=2,
        price=90.0,
        rating=4.7,
        review_count=80,
        has_video=False,
        portfolio_count=0,
        delivery_days=5,
    )
    _seed_quality_score(
        session,
        gig=gig_one,
        keyword=keyword_one,
        run_id=run_id,
        has_video=True,
        portfolio_count=4,
    )
    _seed_quality_score(
        session,
        gig=gig_two,
        keyword=keyword_two,
        run_id=run_id,
        has_video=False,
        portfolio_count=0,
    )

    _seed_seller(
        session,
        run_id=run_id,
        username="seller_a",
        level="Level 2",
        total_reviews=250,
        total_gigs=4,
    )
    _seed_seller(
        session,
        run_id=run_id,
        username="seller_b",
        level="Top Rated",
        total_reviews=530,
        total_gigs=3,
    )


def test_competitor_profile_model() -> None:
    session, _niche = _build_session()
    try:
        row = CompetitorProfile(
            niche_id="test_niche",
            run_id="run-model",
            top_gig_count=10,
            median_price=65.0,
            mean_price=72.0,
            price_std=15.5,
            median_rating=4.8,
            mean_reviews=210.0,
            seller_level_distribution={"LEVEL_2": 0.6, "TOP_RATED": 0.4},
            min_delivery_days=2,
            max_delivery_days=7,
            video_present_rate=0.5,
            portfolio_present_rate=0.7,
        )
        session.add(row)
        session.commit()

        fetched = session.scalars(select(CompetitorProfile)).one()
        assert fetched.niche_id == "test_niche"
        assert fetched.run_id == "run-model"
        assert fetched.top_gig_count == 10
        assert fetched.seller_level_distribution["LEVEL_2"] == 0.6
    finally:
        session.close()


def test_write_competitor_profile() -> None:
    session, _niche = _build_session()
    try:
        created = write_competitor_profile(
            niche_id="test_niche",
            run_id="run-upsert",
            db=session,
            top_gig_count=8,
            median_price=45.0,
            mean_price=50.0,
            price_std=10.0,
            median_rating=4.6,
            mean_reviews=90.0,
            seller_level_distribution={"LEVEL_1": 0.5, "LEVEL_2": 0.5},
            min_delivery_days=2,
            max_delivery_days=6,
            video_present_rate=0.5,
            portfolio_present_rate=0.4,
        )
        assert created is not None
        assert created.top_gig_count == 8

        updated = write_competitor_profile(
            niche_id="test_niche",
            run_id="run-upsert",
            db=session,
            top_gig_count=9,
            median_price=55.0,
            mean_price=60.0,
            price_std=11.0,
            median_rating=4.7,
            mean_reviews=120.0,
            seller_level_distribution={"TOP_RATED": 1.0},
            min_delivery_days=1,
            max_delivery_days=7,
            video_present_rate=0.7,
            portfolio_present_rate=0.8,
        )
        assert updated is not None
        assert updated.id == created.id
        assert updated.top_gig_count == 9
        assert updated.seller_level_distribution == {"TOP_RATED": 1.0}
    finally:
        session.close()


def test_load_gig_data_returns_dataframe() -> None:
    session, niche = _build_session()
    try:
        _seed_competitor_fixture(session, niche, run_id="run-load-data")
        gig_df = load_gig_data_for_niche("test_niche", "run-load-data", session)
        assert isinstance(gig_df, pd.DataFrame)
        assert list(gig_df.columns) == [
            "gig_url",
            "seller_username",
            "price",
            "rating",
            "review_count",
            "queue",
            "delivery_days",
            "has_video",
            "portfolio_count",
        ]
        assert len(gig_df) == 2
    finally:
        session.close()


def test_load_gig_data_empty_niche() -> None:
    session, _niche = _build_session()
    try:
        gig_df = load_gig_data_for_niche("missing_niche", "run-empty", session)
        assert gig_df.empty
    finally:
        session.close()


def test_compute_benchmarks_median_price() -> None:
    gig_df = pd.DataFrame(
        {
            "price": [25.0, 50.0, 100.0],
            "rating": [4.2, 4.5, 4.8],
            "review_count": [10, 20, 30],
            "delivery_days": [2, 3, 5],
            "has_video": [True, False, True],
            "portfolio_count": [1, 0, 3],
        }
    )
    benchmarks = compute_market_benchmarks(gig_df)
    assert benchmarks["median_price"] == 50.0
    assert benchmarks["mean_price"] == 58.333333333333336


def test_compute_benchmarks_video_rate() -> None:
    gig_df = pd.DataFrame(
        {
            "price": [40.0, 60.0, 90.0],
            "rating": [4.1, 4.4, 4.9],
            "review_count": [15, 25, 40],
            "delivery_days": [1, 2, 3],
            "has_video": [True, False, True],
            "portfolio_count": [0, 1, 3],
        }
    )
    benchmarks = compute_market_benchmarks(gig_df)
    assert benchmarks["video_present_rate"] == 2 / 3
    assert benchmarks["portfolio_present_rate"] == 2 / 3


def test_compute_benchmarks_empty_df_returns_empty_dict() -> None:
    assert compute_market_benchmarks(pd.DataFrame()) == {}


def test_seller_level_distribution_fractions_sum_to_1() -> None:
    seller_df = pd.DataFrame({"seller_level": ["Level 1", "Level 2", "Level 2", "Top Rated"]})
    distribution = compute_seller_level_distribution(seller_df)
    assert abs(sum(distribution.values()) - 1.0) < 1e-9


def test_seller_level_distribution_handles_null() -> None:
    seller_df = pd.DataFrame({"seller_level": [None, "Level 2", ""]})
    distribution = compute_seller_level_distribution(seller_df)
    assert "UNKNOWN" in distribution
    assert abs(sum(distribution.values()) - 1.0) < 1e-9


def test_extract_top_n_sorted_by_quality() -> None:
    gig_df = pd.DataFrame(
        {
            "gig_url": ["g1", "g2", "g3"],
            "seller_username": ["s1", "s2", "s3"],
            "price": [50.0, 80.0, 30.0],
            "rating": [4.9, 4.7, 4.4],
            "review_count": [10, 200, 5],
            "queue": [1, 2, 0],
            "delivery_days": [3, 5, 2],
            "has_video": [True, True, False],
            "portfolio_count": [2, 4, 0],
        }
    )
    top = extract_top_n_competitor_gigs(gig_df, n=2)
    assert len(top) == 2
    assert top[0]["gig_url"] == "g2"
    assert top[0]["quality_rank_score"] >= top[1]["quality_rank_score"]


def test_extract_top_n_empty_returns_empty() -> None:
    assert extract_top_n_competitor_gigs(pd.DataFrame(), n=10) == []


def test_compute_new_seller_gap_low_video_flagged() -> None:
    gap = compute_new_seller_gap(
        {
            "video_present_rate": 0.2,
            "portfolio_present_rate": 0.7,
            "price_std": 10.0,
        },
        {"competitor_profiling": {"video_present_rate_threshold": 0.5}},
    )
    assert "low_video_presence" in gap["gap_flags"]
    assert gap["opportunity_score"] > 0.0


def test_run_profiling_returns_profiled_true() -> None:
    session, niche = _build_session()
    try:
        _seed_competitor_fixture(session, niche, run_id="run-profiled")
        result = _run(
            run_competitor_profiling_for_niche(
                niche_id="test_niche",
                run_id="run-profiled",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        assert result["profiled"] is True
        assert "benchmarks" in result
        assert isinstance(result["gap_flags"], list)
    finally:
        session.close()


def test_run_profiling_skips_empty_niche() -> None:
    session, _niche = _build_session()
    try:
        result = _run(
            run_competitor_profiling_for_niche(
                niche_id="test_niche",
                run_id="run-empty-profile",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        assert result["profiled"] is False
        assert result["reason"] == "no_gig_data"
    finally:
        session.close()


def test_run_profiling_writes_to_db() -> None:
    session, niche = _build_session()
    try:
        _seed_competitor_fixture(session, niche, run_id="run-write-profile")
        _run(
            run_competitor_profiling_for_niche(
                niche_id="test_niche",
                run_id="run-write-profile",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        stored = session.scalars(select(CompetitorProfile)).all()
        assert len(stored) == 1
        assert stored[0].niche_id == "test_niche"
        assert stored[0].median_price is not None
    finally:
        session.close()


def test_profiling_with_no_seller_data() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "python scraping", [0.2, 0.3, 0.4])
        _seed_gig(
            session,
            keyword=keyword,
            run_id="run-no-sellers",
            gig_url="https://fiverr.com/gig/no-seller",
            seller_username="ghost_seller",
            rank=1,
            price=35.0,
            rating=4.5,
            review_count=22,
            has_video=False,
            portfolio_count=0,
            delivery_days=4,
        )
        result = _run(
            run_competitor_profiling_for_niche(
                niche_id="test_niche",
                run_id="run-no-sellers",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        assert result["profiled"] is True
        assert "seller_level_distribution" not in result
    finally:
        session.close()


def test_profiling_with_partial_gig_data() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "python bot", [0.3, 0.4, 0.5])
        _seed_gig(
            session,
            keyword=keyword,
            run_id="run-partial-gig",
            gig_url="https://fiverr.com/gig/partial",
            seller_username="seller_partial",
            rank=1,
            price=20.0,
            rating=None,
            review_count=None,
            has_video=None,
            portfolio_count=None,
            delivery_days=7,
        )
        result = _run(
            run_competitor_profiling_for_niche(
                niche_id="test_niche",
                run_id="run-partial-gig",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        assert result["profiled"] is True
        assert result["benchmarks"]["median_price"] == 20.0
    finally:
        session.close()


def test_benchmarks_return_none_for_missing_columns() -> None:
    benchmarks = compute_market_benchmarks(pd.DataFrame({"price": [10.0, 20.0]}))
    assert benchmarks["median_price"] == 15.0
    assert benchmarks["median_rating"] is None
    assert benchmarks["mean_reviews"] is None
    assert benchmarks["video_present_rate"] is None


def test_seller_strength_high_reviews_scores_high() -> None:
    strong = compute_seller_strength_score(
        {
            "seller_level": "Top Rated",
            "total_reviews": 900,
            "total_gigs": 3,
            "response_rate": "99%",
            "member_since": "Jan 2018",
        }
    )
    weak = compute_seller_strength_score(
        {
            "seller_level": "No Level",
            "total_reviews": 3,
            "total_gigs": 15,
            "response_rate": "45%",
            "member_since": "Jan 2026",
        }
    )
    assert strong > weak


def test_seller_strength_missing_fields_no_crash() -> None:
    score = compute_seller_strength_score({})
    assert score >= 0.0


def test_seller_tier_classification() -> None:
    assert classify_seller_tier(85.0) == "DOMINANT"
    assert classify_seller_tier(70.0) == "STRONG"
    assert classify_seller_tier(50.0) == "MODERATE"
    assert classify_seller_tier(20.0) == "WEAK"


def test_seller_strength_top_rated_seller() -> None:
    score = compute_seller_strength_score(
        {
            "seller_level": "Top Rated",
            "total_reviews": 500,
            "total_gigs": 4,
            "response_rate": "98%",
            "member_since": "Feb 2019",
        }
    )
    assert score >= 70.0


def test_analysis_package_exports_public_api() -> None:
    from src.analysis import (  # noqa: PLC0415
        compute_seller_strength_score as exported_strength,
    )
    from src.analysis import (  # noqa: PLC0415
        run_clustering_for_niche as exported_cluster,
    )
    from src.analysis import (  # noqa: PLC0415
        run_competitor_profiling_for_niche as exported_profile,
    )

    assert callable(exported_cluster)
    assert callable(exported_profile)
    assert callable(exported_strength)

