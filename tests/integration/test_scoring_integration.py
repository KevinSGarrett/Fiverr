"""Integration tests for CompetitorProfile -> competition score wiring."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, Keyword, Niche, SearchResult, Seller, write_competitor_profile
from src.scoring.competition import CompetitionScoreCalculator

RUN_ID = "run-score-integration"


def _build_session() -> tuple[Session, Keyword, Niche]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()

    niche = Niche(slug="test_niche", name="Test Niche", category_path="programming-tech/testing")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation",
        normalized_keyword="python automation",
    )
    session.add(keyword)
    session.commit()
    session.refresh(keyword)
    session.refresh(niche)
    return session, keyword, niche


def _seed_keyword_market(
    *,
    session: Session,
    keyword: Keyword,
    seller_level: str,
    review_count: int,
    starting_price: float,
    pro_verified: bool,
) -> None:
    for rank in range(1, 11):
        seller = Seller(
            seller_username=f"seller_{rank}",
            run_id=RUN_ID,
            seller_level=seller_level,
            metadata_json={"is_pro": pro_verified},
            profile_collected=True,
        )
        session.add(seller)
        session.flush()

        gig = Gig(
            gig_url=f"https://fiverr.com/gig/{rank}",
            keyword_id=keyword.id,
            run_id=RUN_ID,
            seller_username=seller.seller_username,
            seller_id=seller.id,
            gig_title_full=f"Gig {rank}",
            title=f"Gig {rank}",
            starting_price=starting_price,
            review_count=review_count,
            review_count_exact=review_count,
            detail_collected=True,
            position=rank,
        )
        session.add(gig)
        session.flush()

        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id=RUN_ID,
                page_collected=rank,
                rank=rank,
                gig_id=gig.id,
                title=gig.gig_title_full,
            )
        )

    session.commit()


def test_competition_score_uses_seeded_competitor_profile() -> None:
    session, keyword, niche = _build_session()
    try:
        _seed_keyword_market(
            session=session,
            keyword=keyword,
            seller_level="Level 1",
            review_count=20,
            starting_price=20.0,
            pro_verified=False,
        )
        calculator = CompetitionScoreCalculator()
        baseline = calculator.calculate(keyword.id, session, config={"scoring": {"competition": {"use_competitor_profile": True}}})

        write_competitor_profile(
            niche_id=niche.slug,
            run_id=RUN_ID,
            db=session,
            top_gig_count=10,
            mean_reviews=800.0,
            median_price=140.0,
            seller_level_distribution={"TOP_RATED": 0.7, "LEVEL_2": 0.3},
            new_seller_gap={"gap_flags": ["LOW_VIDEO_PRESENCE"]},
        )
        profiled = calculator.calculate(keyword.id, session, config={"scoring": {"competition": {"use_competitor_profile": True}}})

        assert baseline.score_value is not None
        assert profiled.score_value is not None
        assert profiled.score_value > baseline.score_value
        assert profiled.score_components["avg_reviews"].raw == 800.0
        assert profiled.score_components["seller_level"].raw == {"TOP_RATED": 0.7, "LEVEL_2": 0.3}
    finally:
        session.close()


def test_competition_score_falls_back_when_profile_absent() -> None:
    session, keyword, _niche = _build_session()
    try:
        _seed_keyword_market(
            session=session,
            keyword=keyword,
            seller_level="Level 2",
            review_count=120,
            starting_price=60.0,
            pro_verified=True,
        )
        calculator = CompetitionScoreCalculator()
        with_guard = calculator.calculate(keyword.id, session, config={"scoring": {"competition": {"use_competitor_profile": True}}})
        without_guard = calculator.calculate(
            keyword.id,
            session,
            config={"scoring": {"competition": {"use_competitor_profile": False}}},
        )
        assert with_guard.score_value == without_guard.score_value
    finally:
        session.close()
