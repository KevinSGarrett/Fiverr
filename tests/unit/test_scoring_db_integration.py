"""Integration tests for SQLAlchemy-backed scoring calculator paths."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    CompetitorProfile,
    ExternalSignal,
    Gig,
    GigQualityAnalysis,
    GigVisualAnalysis,
    Keyword,
    Niche,
    SaturationScore,
    SearchResult,
    Seller,
)
from src.models.gig_quality_analysis import GigQualityAnalysis as GigQualityAnalysisCompat
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.orchestrator import ScoringOrchestrator
from src.scoring.pipeline import SCORING_PROFILES, calculate_weighted_composite
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator, get_saturation_signal
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


def _session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _seed_keyword_data(session: Session) -> int:
    niche = Niche(slug="automation", name="Automation", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation",
        normalized_keyword="python automation",
        metadata_json={"autocomplete_position": 2, "intent_classification": "HIGH_INTENT"},
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 11):
        seller = Seller(
            seller_handle=f"seller_{rank}",
            level="Level 1" if rank <= 5 else "Level 2",
            metadata_json={"is_pro": rank in {1, 2}},
        )
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            title=f"I will automate task {rank}",
            normalized_title=f"automate task {rank if rank <= 8 else 8}",
            starting_price=30.0 + rank,
            review_count=50 + (rank * 20),
            metadata_json={
                "premium_price": 120.0 + rank,
                "delivery_time_days": 1 + (rank % 3),
                "extras": [{"name": "fast_delivery"}] if rank % 2 == 0 else [],
                "has_portfolio": rank % 3 != 0,
            },
        )
        session.add(gig)
        session.flush()
        search_result = SearchResult(
            keyword_id=keyword.id,
            rank=rank,
            gig_id=gig.id,
            title=gig.title,
        )
        session.add(search_result)
        if rank <= 6:
            session.add(GigVisualAnalysis(gig_id=gig.id, has_video=(rank % 2 == 0)))

    session.add(
        ExternalSignal(
            source_name="google",
            signal_type="google_trends",
            keyword_id=keyword.id,
            raw_value_json={
                "trends_12mo_score": 64,
                "trends_3mo_score": 70,
                "trends_3mo_avg": 68,
                "trends_12mo_avg": 60,
                "google_trends_12mo_series": [45, 48, 50, 54, 58, 62, 64, 66, 67, 68, 69, 70],
                "google_trends_3mo_series": [66, 68, 70],
            },
            normalized_value=64.0,
        )
    )
    session.add(
        ExternalSignal(
            source_name="reddit",
            signal_type="reddit_demand",
            keyword_id=keyword.id,
            raw_value_json={
                "reddit_demand_intent_score": 7.5,
                "reddit_recent_post_volume": 20,
                "reddit_historical_post_volume": 15,
                "reddit_activity_trend_score": 62,
            },
            normalized_value=7.5,
        )
    )
    session.commit()
    return keyword.id


def _seed_keyword_data_without_search_links(session: Session) -> int:
    niche = Niche(slug="automation-fallback", name="Automation Fallback", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation fallback",
        normalized_keyword="python automation fallback",
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 4):
        seller = Seller(
            seller_handle=f"fallback_seller_{rank}",
            level="Level 1",
            metadata_json={"is_pro": False},
        )
        session.add(seller)
        session.flush()
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/fallback/{rank}",
                keyword_id=keyword.id,
                run_id="fallback-run",
                seller_id=seller.id,
                seller_username=seller.seller_handle,
                title=f"Fallback gig {rank}",
                normalized_title=f"fallback gig {rank}",
                position=rank,
                starting_price=75.0 + rank,
                review_count=20 + rank,
                metadata_json={
                    "premium_price": 150.0 + rank,
                    "delivery_time_days": float(rank),
                    "extras": [{"name": "fast_delivery"}],
                    "has_video": rank % 2 == 0,
                    "has_portfolio": rank % 2 == 1,
                },
            )
        )

    session.commit()
    return keyword.id


def _seed_keyword_data_without_search_links_mixed_runs(session: Session) -> int:
    niche = Niche(
        slug="automation-fallback-mixed",
        name="Automation Fallback Mixed",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation run scoped fallback",
        normalized_keyword="python automation run scoped fallback",
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 3):
        stale_seller = Seller(
            seller_handle=f"stale_run_seller_{rank}",
            level="Level 2",
            metadata_json={"is_pro": True},
        )
        session.add(stale_seller)
        session.flush()
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/stale/{rank}",
                keyword_id=keyword.id,
                run_id="stale-run",
                seller_id=stale_seller.id,
                seller_username=stale_seller.seller_handle,
                title=f"Stale run gig {rank}",
                normalized_title=f"stale run gig {rank}",
                position=rank,
                starting_price=800.0 + rank,
                review_count=500 + rank,
                metadata_json={
                    "premium_price": 1200.0 + rank,
                    "delivery_time_days": 30.0,
                    "extras": [],
                    "has_video": False,
                    "has_portfolio": False,
                },
            )
        )

        active_seller = Seller(
            seller_handle=f"active_run_seller_{rank}",
            level="Level 1",
            metadata_json={"is_pro": False},
        )
        session.add(active_seller)
        session.flush()
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/active/{rank}",
                keyword_id=keyword.id,
                run_id="active-run",
                seller_id=active_seller.id,
                seller_username=active_seller.seller_handle,
                title=f"Active run gig {rank}",
                normalized_title=f"active run gig {rank}",
                position=rank,
                starting_price=20.0 + rank,
                review_count=10 + rank,
                metadata_json={
                    "premium_price": 40.0 + rank,
                    "delivery_time_days": 2.0,
                    "extras": [{"name": "extra"}],
                    "has_video": True,
                    "has_portfolio": True,
                },
            )
        )

    for rank in range(1, 3):
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="active-run",
                rank=rank,
                title=f"Active unlinked result {rank}",
                gig_id=None,
            )
        )

    session.commit()
    return keyword.id


def _seed_keyword_data_with_latest_unlinked_run(session: Session) -> int:
    niche = Niche(
        slug="automation-latest-unlinked",
        name="Automation Latest Unlinked",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation latest unlinked",
        normalized_keyword="python automation latest unlinked",
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 3):
        seller = Seller(
            seller_handle=f"linked_hist_seller_{rank}",
            level="Level 1",
            metadata_json={"is_pro": False},
        )
        session.add(seller)
        session.flush()
        gig = Gig(
            gig_url=f"https://www.fiverr.com/linked-hist/{rank}",
            keyword_id=keyword.id,
            run_id="historical-linked-run",
            seller_id=seller.id,
            seller_username=seller.seller_handle,
            title=f"Historical linked gig {rank}",
            normalized_title=f"historical linked gig {rank}",
            position=rank,
            starting_price=35.0 + rank,
            review_count=15 + rank,
            metadata_json={
                "premium_price": 75.0 + rank,
                "delivery_time_days": 2.0,
                "extras": [{"name": "extra"}],
                "has_video": rank % 2 == 0,
                "has_portfolio": rank % 2 == 1,
            },
        )
        session.add(gig)
        session.flush()

    for rank in range(1, 3):
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="latest-unlinked-run",
                rank=rank,
                title=f"Latest unlinked result {rank}",
                gig_id=None,
            )
        )

    session.commit()
    return keyword.id


def _seed_keyword_data_with_unlinked_page_cards(session: Session) -> int:
    niche = Niche(
        slug="automation-unlinked-cards",
        name="Automation Unlinked Cards",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation card fallback",
        normalized_keyword="python automation card fallback",
    )
    session.add(keyword)
    session.flush()

    gig_urls = [
        "https://www.fiverr.com/cards/one",
        "https://www.fiverr.com/cards/two",
    ]
    starting_prices = [40.0, 80.0]
    delivery_days = [2.0, 6.0]
    premium_prices = [120.0, 200.0]

    for idx, gig_url in enumerate(gig_urls, start=1):
        seller = Seller(
            seller_handle=f"card_seller_{idx}",
            level="Level 1",
            metadata_json={"is_pro": False},
        )
        session.add(seller)
        session.flush()
        session.add(
            Gig(
                gig_url=gig_url,
                keyword_id=keyword.id,
                run_id="cards-run",
                seller_id=seller.id,
                seller_username=seller.seller_handle,
                title=f"Card fallback gig {idx}",
                normalized_title=f"card fallback gig {idx}",
                position=idx,
                starting_price=starting_prices[idx - 1],
                review_count=10 + idx,
                metadata_json={
                    "premium_price": premium_prices[idx - 1],
                    "delivery_time_days": delivery_days[idx - 1],
                    "extras": [{"name": "expedite"}] if idx == 1 else [],
                    "has_video": idx == 2,
                    "has_portfolio": True,
                },
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id="automation-unlinked-cards",
                run_id="cards-run",
                rubric_score=60.0,
                video_absent=idx == 1,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=idx == 1,
                thumbnail_quality_flag=False,
                weakness_flags=["video_absent", "faq_absent"] if idx == 1 else ["faq_absent"],
            )
        )

    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="cards-run",
            rank=1,
            title="Card fallback row",
            gig_id=None,
            gig_cards=[
                {"position": 1, "gig_url": gig_urls[0], "starting_price": 40.0},
                {"position": 2, "gig_url": gig_urls[1], "starting_price": 80.0},
            ],
        )
    )
    session.commit()
    return keyword.id


def _seed_keyword_data_without_search_links_review_count_exact_only(session: Session) -> int:
    niche = Niche(slug="automation-fallback-exact", name="Automation Fallback Exact", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation exact fallback",
        normalized_keyword="python automation exact fallback",
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 4):
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/fallback-exact/{rank}",
                keyword_id=keyword.id,
                run_id="exact-fallback-run",
                title=f"Exact fallback gig {rank}",
                normalized_title=f"exact fallback gig {rank}",
                position=rank,
                starting_price=40.0 + (rank * 7.0),
                review_count=None,
                review_count_exact=rank * 5,
                metadata_json={
                    "premium_price": 90.0 + rank,
                    "delivery_time_days": float(rank),
                    "extras": [],
                    "has_video": False,
                    "has_portfolio": False,
                },
            )
        )

    session.commit()
    return keyword.id


def _seed_keyword_data_with_card_querystring_urls(session: Session) -> int:
    niche = Niche(
        slug="automation-card-query",
        name="Automation Card Query",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation card query urls",
        normalized_keyword="python automation card query urls",
    )
    session.add(keyword)
    session.flush()

    seller_one = Seller(seller_handle="query_card_seller_1", level="Level 1", metadata_json={"is_pro": False})
    seller_two = Seller(seller_handle="query_card_seller_2", level="Level 1", metadata_json={"is_pro": False})
    session.add_all([seller_one, seller_two])
    session.flush()

    gig_one = Gig(
        gig_url="https://www.fiverr.com/query/one",
        keyword_id=keyword.id,
        run_id="query-cards-run",
        seller_id=seller_one.id,
        seller_username=seller_one.seller_handle,
        title="Query card gig one",
        normalized_title="query card gig one",
        position=1,
        starting_price=50.0,
        review_count=12,
        metadata_json={"premium_price": 120.0, "delivery_time_days": 2.0, "has_video": True, "has_portfolio": True},
    )
    gig_two = Gig(
        gig_url="https://www.fiverr.com/query/two",
        keyword_id=keyword.id,
        run_id="query-cards-run",
        seller_id=seller_two.id,
        seller_username=seller_two.seller_handle,
        title="Query card gig two",
        normalized_title="query card gig two",
        position=2,
        starting_price=100.0,
        review_count=16,
        metadata_json={"premium_price": 220.0, "delivery_time_days": 5.0, "has_video": False, "has_portfolio": True},
    )
    session.add_all([gig_one, gig_two])
    session.flush()

    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="query-cards-run",
            rank=1,
            title="Query card sparse row",
            gig_id=gig_one.id,
            gig_cards=[
                {"position": 1, "gig_url": "https://www.fiverr.com/query/one?source=gig_cards"},
                {"position": 2, "gig_url": "https://www.fiverr.com/query/two?source=gig_cards"},
            ],
        )
    )
    session.commit()
    return keyword.id


def _seed_keyword_data_for_feasibility_high_scores(
    session: Session,
    *,
    use_card_path: bool,
    include_null_rows: bool = False,
    keyword_id_override: int | None = None,
    run_id: str = "feasibility-high-run",
) -> int:
    niche = Niche(
        slug=f"feasibility-{run_id}",
        name=f"Feasibility {run_id}",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword_kwargs = {
        "niche_id": niche.id,
        "keyword": f"feasibility {run_id}",
        "normalized_keyword": f"feasibility {run_id}",
    }
    if keyword_id_override is not None:
        keyword_kwargs["id"] = keyword_id_override

    keyword = Keyword(**keyword_kwargs)
    session.add(keyword)
    session.flush()

    level_values = [
        "LEVEL_1",
        "LEVEL_1",
        "NO_LEVEL",
        "LEVEL_1",
        "LEVEL_1",
        "LEVEL_2",
        "LEVEL_2",
        "LEVEL_2",
        "TRS",
        "LEVEL_2",
    ]
    starting_prices = [10.0, 20.0, 35.0, 55.0, 80.0, 120.0, 180.0, 260.0, 380.0, 520.0]
    review_counts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    gig_urls: list[str] = []

    for rank in range(1, 11):
        seller = Seller(
            seller_handle=f"{run_id}_seller_{rank}",
            level=level_values[rank - 1],
            metadata_json={"is_pro": level_values[rank - 1] == "TRS"},
        )
        session.add(seller)
        session.flush()

        gig_url = f"https://www.fiverr.com/{run_id}/gig-{rank}"
        gig_urls.append(gig_url)
        session.add(
            Gig(
                gig_url=gig_url,
                keyword_id=keyword.id,
                run_id=run_id,
                seller_id=seller.id,
                seller_username=seller.seller_handle,
                title=f"Feasibility high gig {rank}",
                normalized_title=f"feasibility high gig {rank}",
                position=rank,
                starting_price=starting_prices[rank - 1],
                review_count=review_counts[rank - 1],
                metadata_json={
                    "has_video": rank % 2 == 0,
                    "has_portfolio": rank % 3 != 0,
                },
            )
        )

    session.add(
        CompetitorProfile(
            niche_id=niche.slug,
            run_id=run_id,
            top_gig_count=10,
            seller_level_distribution={"LEVEL_1": 0.4, "LEVEL_2": 0.5, "TRS": 0.1},
            new_seller_gap={
                "gap_flags": [
                    "LOW_VIDEO_PRESENCE",
                    "LOW_PORTFOLIO_PRESENCE",
                    "HIGH_PRICE_VARIANCE",
                ]
            },
        )
    )

    if use_card_path:
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id=run_id,
                rank=1,
                title="Sparse card-only row",
                gig_id=None,
                gig_cards=[
                    {"position": position, "gig_url": gig_url}
                    for position, gig_url in enumerate(gig_urls, start=1)
                ],
            )
        )
        if include_null_rows:
            session.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id=run_id,
                    rank=2,
                    title="Additional sparse row",
                    gig_id=None,
                    gig_cards=[
                        {"position": 1, "gig_url": gig_urls[0]},
                        {"position": 2, "gig_url": gig_urls[1]},
                    ],
                )
            )
    else:
        linked_gigs = (
            session.query(Gig)
            .filter(Gig.keyword_id == keyword.id, Gig.run_id == run_id)
            .order_by(Gig.position.asc())
            .all()
        )
        for rank, gig in enumerate(linked_gigs, start=1):
            session.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id=run_id,
                    rank=rank,
                    title=f"Linked result {rank}",
                    gig_id=gig.id,
                )
            )

    session.commit()
    return keyword.id


def test_demand_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = DemandScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_demand_uses_search_result_total_result_count_when_available() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    try:
        session.add(
            SearchResult(
                keyword_id=keyword_id,
                run_id="high-volume-run",
                rank=99,
                title="High volume row",
                gig_id=None,
                total_result_count=20000,
            )
        )
        session.commit()
        signals = DemandScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["total_result_count"] == 20000.0
    finally:
        session.close()


def test_demand_pairs_strictness_with_selected_total_result_count_row() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    try:
        session.add(
            SearchResult(
                keyword_id=keyword_id,
                run_id="older-none-run",
                rank=99,
                title="Older unconstrained high-volume row",
                gig_id=None,
                total_result_count=25000,
                search_strictness_used="NONE",
                collected_at=datetime(2026, 5, 30, 10, 0, 0),
            )
        )
        session.add(
            SearchResult(
                keyword_id=keyword_id,
                run_id="newer-constrained-run",
                rank=100,
                title="Newer constrained low-volume row",
                gig_id=None,
                total_result_count=500,
                search_strictness_used="SUBCATEGORY",
                collected_at=datetime(2026, 5, 30, 12, 0, 0),
            )
        )
        session.commit()

        signals = DemandScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["total_result_count"] == 25000.0
        assert signals["search_strictness_used"] == "NONE"
    finally:
        session.close()


def test_demand_ignores_legacy_migration_default_none_strictness() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    try:
        session.add(
            SearchResult(
                keyword_id=keyword_id,
                run_id="legacy-migrated-run",
                rank=101,
                title="Legacy default strictness row",
                gig_id=None,
                total_result_count=22000,
                search_strictness_used="NONE",
                collected_at=datetime(2026, 5, 29, 12, 0, 0),
            )
        )
        session.commit()

        signals = DemandScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["total_result_count"] == 22000.0
        assert signals["search_strictness_used"] is None
    finally:
        session.close()


def test_demand_marketplace_result_count_ignores_sparse_fallback_rows() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    try:
        session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).delete()
        session.add(SearchResult(keyword_id=keyword_id, rank=1, title="Sparse row #1", gig_id=None))
        session.add(SearchResult(keyword_id=keyword_id, rank=2, title="Sparse row #2", gig_id=None))
        session.commit()

        signals = DemandScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["total_result_count"] is None
    finally:
        session.close()


def test_competition_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = CompetitionScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_opportunity_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = OpportunityScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_feasibility_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_profitability_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_intent_saturation_weakness_trend_sqlalchemy_paths_return_scores() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    assert ConversionIntentScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert SaturationScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert GigQualityWeaknessScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert TrendScoreCalculator().calculate(keyword_id, session).score_value is not None
    session.close()


def test_scoring_calculators_fallback_to_keyword_gigs_without_search_result_links() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links(session)

    feasibility_result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    profitability_result = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    weakness_result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)

    assert feasibility_result.score_value is not None
    assert profitability_result.score_value is not None
    assert weakness_result.score_value is not None
    session.close()


def test_feasibility_fallback_uses_review_count_exact_when_review_count_missing() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links_review_count_exact_only(session)

    feasibility_calculator = NewSellerFeasibilityCalculator()
    feasibility_signals = feasibility_calculator._load_signals_from_db(keyword_id, session)
    feasibility_result = feasibility_calculator.calculate(keyword_id, session)

    # Feasibility now uses the lowest available review barrier among top gigs.
    assert feasibility_signals["lowest_ranked_review_count_page1"] == 5.0
    assert feasibility_result.score_value is not None
    session.close()


def test_feasibility_returns_full_score_when_top_gigs_fully_priced() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=False, run_id="full-score")
    try:
        result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
        assert result.score_value == 100.0
        assert "price_diversity" in result.score_components
    finally:
        session.close()


def test_feasibility_uses_gig_card_fallback_when_direct_links_sparse() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=True, run_id="card-fallback")
    calculator = NewSellerFeasibilityCalculator()
    try:
        signals = calculator._load_signals_from_db(keyword_id, session)
        result = calculator.calculate(keyword_id, session)
        assert signals["top10_prices"] is not None
        assert len(signals["top10_prices"]) == 10
        assert signals["price_diversity_top10"] is not None
        assert result.score_value is not None
        assert result.score_value >= 90.0
    finally:
        session.close()


def test_feasibility_does_not_regress_below_90_for_fully_ranked_keyword() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=False, run_id="full-ranked")
    try:
        result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value >= 90.0
    finally:
        session.close()


def test_feasibility_handles_mixed_null_gig_id_rows_gracefully() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(
        session,
        use_card_path=True,
        include_null_rows=True,
        run_id="mixed-null-rows",
    )
    try:
        result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value >= 90.0
    finally:
        session.close()


def test_feasibility_run_scoped_fallback_recovers_when_run_mismatch() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links_mixed_runs(session)
    calculator = NewSellerFeasibilityCalculator()
    try:
        signals = calculator._load_signals_from_db(keyword_id, session)
        result = calculator.calculate(keyword_id, session)
        assert signals["top10_prices"] == [21.0, 22.0]
        assert result.score_value is not None
    finally:
        session.close()


def test_feasibility_score_is_consistent_between_direct_and_card_path() -> None:
    session = next(_session())
    direct_keyword_id = _seed_keyword_data_for_feasibility_high_scores(
        session,
        use_card_path=False,
        run_id="direct-path",
    )
    card_keyword_id = _seed_keyword_data_for_feasibility_high_scores(
        session,
        use_card_path=True,
        run_id="card-path",
    )
    calculator = NewSellerFeasibilityCalculator()
    try:
        direct_result = calculator.calculate(direct_keyword_id, session)
        card_result = calculator.calculate(card_keyword_id, session)
        assert direct_result.score_value is not None
        assert card_result.score_value is not None
        assert abs(direct_result.score_value - card_result.score_value) <= 0.01
    finally:
        session.close()


def test_feasibility_regression_value_above_90_for_kw96_post_fix() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(
        session,
        use_card_path=True,
        keyword_id_override=96,
        run_id="kw96-regression",
    )
    try:
        result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value >= 90.0
    finally:
        session.close()


# pylint: disable=protected-access
def test_scoring_fallback_queries_scope_to_active_run_id() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links_mixed_runs(session)

    feasibility_signals = NewSellerFeasibilityCalculator()._load_signals_from_db(keyword_id, session)
    profitability_signals = ProfitabilityScoreCalculator()._load_signals_from_db(keyword_id, session)
    weakness_signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)

    assert feasibility_signals["top10_prices"] == [21.0, 22.0]
    assert profitability_signals["avg_starting_price_top10"] == 21.5
    assert weakness_signals["top10_has_video"] == [True, True]
    assert weakness_signals["top10_has_portfolio"] == [True, True]
    session.close()


def test_scoring_fallback_queries_recover_when_latest_run_unlinked() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_latest_unlinked_run(session)

    feasibility_result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    profitability_result = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    weakness_result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)

    assert feasibility_result.score_value is not None
    assert profitability_result.score_value is not None
    assert weakness_result.score_value is not None
    session.close()


def test_scoring_uses_search_result_gig_cards_when_links_sparse() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_unlinked_page_cards(session)

    profitability_signals = ProfitabilityScoreCalculator()._load_signals_from_db(keyword_id, session)
    weakness_signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)

    assert profitability_signals["avg_starting_price_top10"] == 60.0
    assert profitability_signals["avg_premium_package_price_top10"] == 160.0
    assert profitability_signals["typical_delivery_days"] == 4.0
    assert weakness_signals["top10_has_video"] == [False, True]
    assert weakness_signals["top10_has_portfolio"] == [True, True]
    assert weakness_signals["weakness_flag_penalty"] == 32.5
    assert weakness_signals["overall_weakness_score_avg"] == 4.0
    session.close()


def test_gig_quality_analysis_compatibility_overall_weakness_score() -> None:
    session = next(_session())
    _seed_keyword_data_with_unlinked_page_cards(session)
    try:
        analysis_row = (
            session.query(GigQualityAnalysis)
            .filter(GigQualityAnalysis.run_id == "cards-run")
            .first()
        )
        assert analysis_row is not None
        assert analysis_row.rubric_score == 60.0
        assert analysis_row.overall_weakness_score == 4.0
    finally:
        session.close()


def test_gig_quality_analysis_wrapper_reexports_market_model() -> None:
    assert GigQualityAnalysisCompat is GigQualityAnalysis


def test_weakness_calculate_uses_overall_weakness_component_from_signals() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    keyword_id = 12345
    db_proxy = {
        keyword_id: {
            "overall_weakness_score_avg": 4.0,
            "video_absence_rate": 0.0,
            "portfolio_absence_rate": 0.0,
            "weakness_flag_penalty": 0.0,
        }
    }

    result = calculator.calculate(keyword_id, db_proxy)

    assert result.score_value is not None
    assert "overall_weakness_score" in result.score_components
    assert "gig_quality_analysis.overall_weakness_score" in result.source_evidence
    assert result.score_components["overall_weakness_score"].value == 40.0


def test_scoring_uses_card_urls_with_querystrings_for_sparse_links() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_card_querystring_urls(session)
    try:
        profitability_signals = ProfitabilityScoreCalculator()._load_signals_from_db(keyword_id, session)
        weakness_signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)

        assert profitability_signals["avg_starting_price_top10"] == 75.0
        assert profitability_signals["avg_premium_package_price_top10"] == 170.0
        assert profitability_signals["typical_delivery_days"] == 3.5
        assert weakness_signals["top10_has_video"] == [True, False]
        assert weakness_signals["top10_has_portfolio"] == [True, True]
    finally:
        session.close()


def test_confidence_modifier_sqlalchemy_context_returns_clamped_value() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    modifier = ConfidenceScoreModifier().calculate(keyword_id, None, session)
    assert 0.0 <= modifier <= 1.0
    session.close()


def test_orchestrator_run_with_sqlalchemy_session_returns_result() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    run_result = ScoringOrchestrator().run([keyword_id], session)
    assert run_result.keyword_results
    assert run_result.keyword_results[0]["final_payload"]["final_score"] >= 0.0
    session.close()


def test_dict_proxy_path_still_works_after_sqlalchemy_changes() -> None:
    keyword_id = 999
    db_proxy = {
        keyword_id: {
            "total_result_count": 800,
            "autocomplete_position": 1,
            "trends_12mo_score": 60,
            "reddit_demand_intent_score": 7.0,
        }
    }
    result = DemandScoreCalculator().calculate(keyword_id, db_proxy)
    assert result.score_value is not None


def test_missing_keyword_id_returns_none_score_gracefully() -> None:
    session = next(_session())
    result = DemandScoreCalculator().calculate(123456, session)
    assert result.score_value is None
    session.close()


def test_saturation_signal_reads_from_analysis_table() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    session.add(
        SaturationScore(
            keyword_id=keyword_id,
            niche_id="automation",
            run_id="legacy",
            saturation_score=77.5,
            count_score=80.0,
            title_dup_score=75.0,
            price_score=70.0,
            overlap_score=65.0,
            llm_class_score=60.0,
            title_duplication_rate=0.75,
            price_compression_rate=0.7,
            seller_overlap_rate=0.65,
            explanation_text="integration test",
        )
    )
    session.commit()

    assert get_saturation_signal(keyword_id, "legacy", session) == 77.5
    session.close()


def test_saturation_signal_none_when_no_row() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    assert get_saturation_signal(keyword_id, "legacy", session) is None
    session.close()


def test_saturation_signal_does_not_fallback_to_different_run() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    session.add(
        SaturationScore(
            keyword_id=keyword_id,
            niche_id="automation",
            run_id="old-run",
            saturation_score=81.0,
            count_score=80.0,
            title_dup_score=75.0,
            price_score=70.0,
            overlap_score=65.0,
            llm_class_score=60.0,
            title_duplication_rate=0.75,
            price_compression_rate=0.7,
            seller_overlap_rate=0.65,
            explanation_text="old run only",
        )
    )
    session.commit()

    assert get_saturation_signal(keyword_id, "current-run", session) is None
    assert get_saturation_signal(keyword_id, "", session) == 81.0
    session.close()


def test_saturation_signal_non_session_paths_handle_valid_and_invalid_values() -> None:
    class _SignalProvider:
        @staticmethod
        def get_saturation_signal(_keyword_id: int, _run_id: str) -> str:
            return "66.5"

    class _BadSignalProvider:
        @staticmethod
        def get_saturation_signal(_keyword_id: int, _run_id: str) -> str:
            return "not-a-number"

    class _InputsProvider:
        @staticmethod
        def get_saturation_inputs(_keyword_id: int) -> dict[str, float]:
            return {"saturation_score": 72.0}

    assert get_saturation_signal(101, "run-a", _SignalProvider()) == 66.5
    assert get_saturation_signal(101, "run-a", _BadSignalProvider()) is None
    assert get_saturation_signal(101, "run-a", _InputsProvider()) == 72.0
    assert get_saturation_signal(101, "run-a", {101: {"saturation_score": 55.0}}) == 55.0


def test_saturation_calculator_uses_mapping_run_id_for_analysis_output() -> None:
    db_proxy = {
        701: {
            "run_id": "run-map-701",
            "saturation_score": 73.4,
        }
    }
    result = SaturationScoreCalculator().calculate(
        701,
        db_proxy,
        config={"scoring": {"saturation": {"use_analysis_output": True}}},
    )
    assert result.score_value == 73.4
    assert "saturation_scores.saturation_score[run-map-701]" in result.source_evidence


def test_saturation_score_resolver_fallback_paths() -> None:
    calculator = SaturationScoreCalculator()
    assert calculator._resolve_title_duplication_score({"duplicate_title_count_top30": 12.0}) == 40.0
    assert calculator._resolve_price_compression_score({"price_diversity_top30": 0.25}) == 75.0
    assert calculator._resolve_llm_saturation_assessment({"llm_saturation_assessment": 6.4}) == 6.4


def test_saturation_normalization_and_price_compression_helpers() -> None:
    assert SaturationScoreCalculator._normalize_total_gig_count(0) == 0.0
    assert SaturationScoreCalculator._normalize_ratio_or_score(0.5) == 50.0
    assert SaturationScoreCalculator._normalize_ratio_or_score(6.0) == 60.0
    assert SaturationScoreCalculator._normalize_ratio_or_score(140.0) == 100.0
    assert SaturationScoreCalculator._price_compression_ratio([20.0, 20.0]) == 1.0
    assert SaturationScoreCalculator._price_compression_ratio([10.0]) is None


def test_saturation_score_inverted_correctly_in_composite() -> None:
    common_scores: dict[str, float | None] = {
        "demand_score": 70.0,
        "competition_score": 40.0,
        "opportunity_score": 65.0,
        "feasibility_score": 60.0,
        "profitability_score": 55.0,
        "intent_score": 50.0,
        "weakness_score": 45.0,
        "trend_score": 60.0,
    }
    low_saturation_scores = {**common_scores, "saturation_score": 10.0}
    high_saturation_scores = {**common_scores, "saturation_score": 90.0}

    low_value, _ = calculate_weighted_composite(low_saturation_scores, SCORING_PROFILES["default"])
    high_value, _ = calculate_weighted_composite(high_saturation_scores, SCORING_PROFILES["default"])
    assert low_value > high_value


def test_sponsored_gigs_never_included_in_competition_top10() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    try:
        top_gig = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank == 1)
            .first()
        )
        assert top_gig is not None
        top_gig.is_sponsored = True
        top_gig.review_count = 5000
        session.commit()

        calculator = CompetitionScoreCalculator()
        with_exclusion = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": True}},
        )
        without_exclusion = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": False}},
        )
        assert with_exclusion["avg_review_count_top10"] < without_exclusion["avg_review_count_top10"]
    finally:
        session.close()


def test_profitability_excludes_zombie_prices() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    try:
        top_gig = (
            session.query(Gig)
            .join(SearchResult, SearchResult.gig_id == Gig.id)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank == 1)
            .first()
        )
        assert top_gig is not None
        top_gig.is_zombie = True
        top_gig.starting_price = 9999.0
        session.commit()

        calculator = ProfitabilityScoreCalculator()
        filtered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_zombie_filter": True}},
        )
        unfiltered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_zombie_filter": False}},
        )
        assert filtered["avg_starting_price_top10"] < unfiltered["avg_starting_price_top10"]
    finally:
        session.close()
