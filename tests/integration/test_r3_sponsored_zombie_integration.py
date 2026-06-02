"""Integration tests for R3 sponsored/zombie filtering behavior."""
from __future__ import annotations

# pylint: disable=protected-access
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.profitability import ProfitabilityScoreCalculator


def _build_r3_dataset() -> tuple[Session, int]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="r3-integration", name="R3 Integration", category_path="programming-tech/r3")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="r3 integration keyword", normalized_keyword="r3 integration keyword")
    session.add(keyword)
    session.flush()

    fixtures = [
        (1, True, False, 150.0, 300.0),
        (2, False, True, 120.0, 180.0),
        (3, False, False, 35.0, 18.0),
    ]
    for rank, sponsored, zombie, price, reviews in fixtures:
        seller = Seller(seller_handle=f"r3-int-seller-{rank}", level="LEVEL_1", metadata_json={"is_pro": False})
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            keyword_id=keyword.id,
            run_id="r3-int-run",
            seller_username=seller.seller_handle,
            title=f"R3 integration gig {rank}",
            normalized_title=f"r3 integration gig {rank}",
            starting_price=price,
            review_count=reviews,
            is_sponsored=sponsored,
            is_zombie=zombie,
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="r3-int-run",
                rank=rank,
                gig_id=gig.id,
                title=gig.title,
            )
        )
    session.commit()
    return session, keyword.id


def test_sponsored_exclusion_reduces_competition_pressure() -> None:
    session, keyword_id = _build_r3_dataset()
    try:
        calculator = CompetitionScoreCalculator()
        default_signals = calculator._load_signals_from_db(keyword_id, session)
        no_filters = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        assert default_signals["avg_review_count_top10"] == 18.0
        assert no_filters["avg_review_count_top10"] > default_signals["avg_review_count_top10"]
        assert no_filters["avg_starting_price_top10"] > default_signals["avg_starting_price_top10"]
    finally:
        session.close()


def test_zombie_exclusion_reduces_profitability_price_inputs() -> None:
    session, keyword_id = _build_r3_dataset()
    try:
        calculator = ProfitabilityScoreCalculator()
        default_signals = calculator._load_signals_from_db(keyword_id, session)
        zombie_enabled_only = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": True}},
        )
        no_filters = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        assert default_signals["avg_starting_price_top10"] == 35.0
        assert zombie_enabled_only["avg_starting_price_top10"] == (150.0 + 35.0) / 2.0
        assert no_filters["avg_starting_price_top10"] > zombie_enabled_only["avg_starting_price_top10"]
    finally:
        session.close()


def test_sponsored_and_zombie_flags_persist_on_gigs() -> None:
    session, keyword_id = _build_r3_dataset()
    try:
        gigs = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        assert len(gigs) == 3
        assert gigs[0].is_sponsored is True and gigs[0].is_zombie is False
        assert gigs[1].is_sponsored is False and gigs[1].is_zombie is True
        assert gigs[2].is_sponsored is False and gigs[2].is_zombie is False
    finally:
        session.close()
