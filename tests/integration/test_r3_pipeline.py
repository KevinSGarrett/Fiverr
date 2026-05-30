from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.migrations.srdi_r8.migration_02_gigs_srdi_columns import apply as apply_m2
from src.migrations.srdi_r8.migration_03_search_results_srdi_columns import apply as apply_m3
from src.migrations.srdi_r8.migration_07_r3_columns import apply as apply_m7
from src.migrations.srdi_r8.migration_07_r3_columns import rollback as rollback_m7
from src.models import Base, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator

from tests.unit.test_srdi_r8_migrations import _bootstrap_base_tables, _column_names


def test_migration_07_apply_and_rollback() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    _bootstrap_base_tables(engine)
    apply_m2(engine)
    apply_m3(engine)
    apply_m7(engine)
    apply_m7(engine)
    assert "zombie_score" in _column_names(engine, "gigs")
    assert "is_sponsored" in _column_names(engine, "gigs")
    assert "is_zombie" in _column_names(engine, "gigs")
    assert "sponsored_gig_count" in _column_names(engine, "search_results")
    assert "organic_gig_count" in _column_names(engine, "search_results")
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
                    pages_collected=3,
                )
            )
        db.commit()
        calc = CompetitionScoreCalculator()
        top_10 = calc._load_signals_from_db(keyword.id, db, config={"relevance": {"top_n_for_scoring": 10}})
        top_5 = calc._load_signals_from_db(keyword.id, db, config={"relevance": {"top_n_for_scoring": 5}})
        assert top_10["avg_review_count_top10"] != top_5["avg_review_count_top10"]
        persisted = db.query(SearchResult).filter(SearchResult.keyword_id == keyword.id).first()
        assert persisted is not None
        assert persisted.pages_collected == 3
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


def test_golden_run_parity_toggles_off_matches_legacy_inputs() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, future=True)()
    try:
        niche = Niche(slug="r3-parity", name="R3 Parity", category_path="programming-tech/r3")
        db.add(niche)
        db.flush()
        keyword = Keyword(niche_id=niche.id, keyword="r3 parity", normalized_keyword="r3 parity")
        db.add(keyword)
        db.flush()
        for rank in range(1, 4):
            seller = Seller(seller_handle=f"parity-seller-{rank}", level="LEVEL_1")
            db.add(seller)
            db.flush()
            gig = Gig(
                gig_url=f"https://www.fiverr.com/r3parity/{rank}",
                seller_username=seller.seller_handle,
                seller_id=seller.id,
                keyword_id=keyword.id,
                run_id="r3parity-run",
                review_count=rank * 100,
                starting_price=20.0 + rank,
                is_sponsored=(rank == 1),
                is_zombie=(rank == 2),
            )
            db.add(gig)
            db.flush()
            db.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id="r3parity-run",
                    rank=rank,
                    gig_id=gig.id,
                    title=f"gig {rank}",
                )
            )
        db.commit()

        off_cfg = {"relevance": {"enable_sponsored_exclusion": False, "enable_zombie_filter": False}}
        competition_signals = CompetitionScoreCalculator()._load_signals_from_db(keyword.id, db, config=off_cfg)
        feasibility_signals = NewSellerFeasibilityCalculator()._load_signals_from_db(keyword.id, db, config=off_cfg)

        assert competition_signals["avg_review_count_top10"] == 200.0
        assert feasibility_signals["lowest_ranked_review_count_page1"] == 100.0
    finally:
        db.close()
