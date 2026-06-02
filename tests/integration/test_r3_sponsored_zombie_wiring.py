"""Integration tests for R3 sponsored/zombie gig filtering."""
from __future__ import annotations

# pylint: disable=protected-access
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.demand import trc_adjustment
from src.scoring.profitability import ProfitabilityScoreCalculator


def _seed_keyword_with_r3_flags() -> tuple[Session, int]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()

    niche = Niche(slug="r3-wiring", name="R3 Wiring", category_path="programming-tech/r3")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="r3 keyword", normalized_keyword="r3 keyword")
    session.add(keyword)
    session.flush()

    rows = [
        {"rank": 1, "is_sponsored": True, "is_zombie": False, "price": 999.0, "reviews": 300.0},
        {"rank": 2, "is_sponsored": False, "is_zombie": True, "price": 888.0, "reviews": 200.0},
        {"rank": 3, "is_sponsored": False, "is_zombie": False, "price": 40.0, "reviews": 12.0},
    ]
    for row in rows:
        seller = Seller(seller_handle=f"r3-seller-{row['rank']}", level="LEVEL_1", metadata_json={"is_pro": False})
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            keyword_id=keyword.id,
            run_id="r3-run",
            seller_username=seller.seller_handle,
            title=f"R3 gig {row['rank']}",
            normalized_title=f"r3 gig {row['rank']}",
            starting_price=row["price"],
            review_count=row["reviews"],
            is_sponsored=row["is_sponsored"],
            is_zombie=row["is_zombie"],
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="r3-run",
                rank=row["rank"],
                gig_id=gig.id,
                title=gig.title,
            )
        )

    session.commit()
    return session, keyword.id


def test_sponsored_gig_excluded_from_competition_scoring() -> None:
    session, keyword_id = _seed_keyword_with_r3_flags()
    try:
        calculator = CompetitionScoreCalculator()
        filtered = calculator._load_signals_from_db(keyword_id, session)
        unfiltered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        assert filtered["avg_review_count_top10"] == 12.0
        assert unfiltered["avg_review_count_top10"] > filtered["avg_review_count_top10"]
        assert unfiltered["avg_starting_price_top10"] > filtered["avg_starting_price_top10"]
    finally:
        session.close()


def test_zombie_gig_excluded_from_profitability_signals() -> None:
    session, keyword_id = _seed_keyword_with_r3_flags()
    try:
        calculator = ProfitabilityScoreCalculator()
        filtered = calculator._load_signals_from_db(keyword_id, session)
        unfiltered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        assert filtered["avg_starting_price_top10"] == 40.0
        assert unfiltered["avg_starting_price_top10"] > filtered["avg_starting_price_top10"]
        assert unfiltered["avg_premium_package_price_top10"] is None
    finally:
        session.close()


def test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20pct() -> None:
    multiplier_high = trc_adjustment(
        sponsored_gig_count=3,
        total=10,
        config={"relevance": {"enable_sponsored_exclusion": True}},
        strictness_used="SUBCATEGORY",
    )
    multiplier_low = trc_adjustment(
        sponsored_gig_count=1,
        total=10,
        config={"relevance": {"enable_sponsored_exclusion": True}},
        strictness_used="SUBCATEGORY",
    )
    assert multiplier_high == 0.80
    assert multiplier_low == 1.00
    assert multiplier_high < multiplier_low
