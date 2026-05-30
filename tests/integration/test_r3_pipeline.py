from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.migrations.srdi_r8.migration_07_r3_columns import apply as apply_m7
from src.migrations.srdi_r8.migration_07_r3_columns import rollback as rollback_m7
from src.models import Base, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.competition import CompetitionScoreCalculator

from tests.unit.test_srdi_r8_migrations import _bootstrap_base_tables, _column_names


def test_migration_07_apply_and_rollback() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    _bootstrap_base_tables(engine)
    apply_m7(engine)
    assert "zombie_score" in _column_names(engine, "gigs")
    rollback_m7(engine)


def test_pagination_caps_scoring_at_top_10() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, future=True)()
    try:
        niche = Niche(slug="r3-cap", name="R3 Cap", category_path="programming-tech/r3")
        db.add(niche)
        db.flush()
        keyword = Keyword(niche_id=niche.id, keyword="r3 cap", normalized_keyword="r3 cap")
        db.add(keyword)
        db.flush()
        for rank in range(1, 16):
            seller = Seller(seller_handle=f"seller-{rank}", level="LEVEL_1")
            db.add(seller)
            db.flush()
            gig = Gig(
                gig_url=f"https://www.fiverr.com/r3cap/{rank}",
                seller_username=seller.seller_handle,
                seller_id=seller.id,
                keyword_id=keyword.id,
                run_id="r3cap-run",
                review_count=rank,
                starting_price=10.0,
            )
            db.add(gig)
            db.flush()
            db.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id="r3cap-run",
                    rank=rank,
                    gig_id=gig.id,
                    title=f"gig {rank}",
                )
            )
        db.commit()
        calc = CompetitionScoreCalculator()
        top_10 = calc._load_signals_from_db(keyword.id, db, config={"relevance": {"top_n_for_scoring": 10}})
        top_5 = calc._load_signals_from_db(keyword.id, db, config={"relevance": {"top_n_for_scoring": 5}})
        assert top_10["avg_review_count_top10"] != top_5["avg_review_count_top10"]
    finally:
        db.close()


def test_sponsored_zombie_flags_flow_into_scoring() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, future=True)()
    try:
        niche = Niche(slug="r3-flags", name="R3 Flags", category_path="programming-tech/r3")
        db.add(niche)
        db.flush()
        keyword = Keyword(niche_id=niche.id, keyword="r3 flags", normalized_keyword="r3 flags")
        db.add(keyword)
        db.flush()
        for rank in range(1, 4):
            seller = Seller(seller_handle=f"flag-seller-{rank}", level="LEVEL_1")
            db.add(seller)
            db.flush()
            gig = Gig(
                gig_url=f"https://www.fiverr.com/r3flags/{rank}",
                seller_username=seller.seller_handle,
                seller_id=seller.id,
                keyword_id=keyword.id,
                run_id="r3flags-run",
                review_count=rank * 100,
                starting_price=20.0,
                is_sponsored=(rank == 1),
                is_zombie=(rank == 2),
            )
            db.add(gig)
            db.flush()
            db.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id="r3flags-run",
                    rank=rank,
                    gig_id=gig.id,
                    title=f"gig {rank}",
                )
            )
        db.commit()

        calc = CompetitionScoreCalculator()
        excluded = calc._load_signals_from_db(
            keyword.id,
            db,
            config={"relevance": {"enable_sponsored_exclusion": True, "enable_zombie_filter": True}},
        )
        included = calc._load_signals_from_db(
            keyword.id,
            db,
            config={"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}},
        )
        assert excluded["avg_review_count_top10"] != included["avg_review_count_top10"]
    finally:
        db.close()
