"""Unit tests for sponsored-gig filtering in scoring paths."""
from __future__ import annotations

# pylint: disable=protected-access
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.profitability import ProfitabilityScoreCalculator


def _seed_sponsored_fixture() -> tuple[Session, int]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()

    niche = Niche(slug="r3-unit", name="R3 Unit", category_path="programming-tech/r3")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="sponsored filter", normalized_keyword="sponsored filter")
    session.add(keyword)
    session.flush()

    data = [(1, True, 999.0, 1000.0), (2, False, 25.0, 20.0)]
    for rank, is_sponsored, price, reviews in data:
        seller = Seller(seller_handle=f"unit-seller-{rank}", level="LEVEL_1", metadata_json={"is_pro": False})
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            keyword_id=keyword.id,
            run_id="unit-run",
            seller_username=seller.seller_handle,
            title=f"Unit gig {rank}",
            normalized_title=f"unit gig {rank}",
            starting_price=price,
            review_count=reviews,
            is_sponsored=is_sponsored,
            is_zombie=False,
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="unit-run",
                rank=rank,
                gig_id=gig.id,
                title=gig.title,
            )
        )

    session.commit()
    return session, keyword.id


def test_sponsored_gigs_excluded_from_competition_and_profitability() -> None:
    session, keyword_id = _seed_sponsored_fixture()
    try:
        competition = CompetitionScoreCalculator()
        profitability = ProfitabilityScoreCalculator()
        filtered_comp = competition._load_signals_from_db(keyword_id, session)
        unfiltered_comp = competition._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        filtered_prof = profitability._load_signals_from_db(keyword_id, session)
        unfiltered_prof = profitability._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        assert filtered_comp["avg_review_count_top10"] == 20.0
        assert unfiltered_comp["avg_review_count_top10"] > filtered_comp["avg_review_count_top10"]
        assert filtered_prof["avg_starting_price_top10"] == 25.0
        assert unfiltered_prof["avg_starting_price_top10"] > filtered_prof["avg_starting_price_top10"]
    finally:
        session.close()
