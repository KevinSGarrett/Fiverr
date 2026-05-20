"""Integration tests for Stage 9 + Stage 10 analysis pipeline."""

from __future__ import annotations

import asyncio
import json

import numpy as np
from sqlalchemy import select
from src.analysis.competitor_profiler import run_competitor_profiling_for_niche
from src.analysis.keyword_clusterer import run_clustering_for_niche
from src.models.database import create_session_factory, initialize_database
from src.models.gig import Gig
from src.models.gig_quality_score import GigQualityScore
from src.models.market import ClusterAssignment, CompetitorProfile, Keyword
from src.models.niche import Niche
from src.models.search_result import SearchResult
from src.models.seller import Seller


def _run(coro):
    return asyncio.run(coro)


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


def test_stage9_and_stage10_pipeline_with_seeded_data(monkeypatch) -> None:
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        niche = Niche(slug="test_niche", name="Test Niche", category_path="programming-tech/testing")
        session.add(niche)
        session.commit()
        session.refresh(niche)

        keywords = [
            _seed_keyword(session, niche, "python automation", [0.1, 0.2, 0.3]),
            _seed_keyword(session, niche, "workflow automation", [0.2, 0.3, 0.4]),
            _seed_keyword(session, niche, "python scraping", [0.9, 0.8, 0.7]),
        ]

        sellers = [
            Seller(
                seller_username="seller_a",
                run_id="integration-run",
                seller_level="Level 2",
                total_reviews=120,
                total_gigs=3,
                response_rate="98%",
                member_since="Jan 2019",
                profile_collected=True,
            ),
            Seller(
                seller_username="seller_b",
                run_id="integration-run",
                seller_level="Top Rated",
                total_reviews=420,
                total_gigs=4,
                response_rate="99%",
                member_since="Jan 2017",
                profile_collected=True,
            ),
            Seller(
                seller_username="seller_c",
                run_id="integration-run",
                seller_level="Level 1",
                total_reviews=55,
                total_gigs=2,
                response_rate="90%",
                member_since="Mar 2022",
                profile_collected=True,
            ),
        ]
        session.add_all(sellers)
        session.commit()

        rank_by_keyword: dict[int, int] = {keyword.id: 0 for keyword in keywords}
        for idx in range(10):
            keyword = keywords[idx % len(keywords)]
            rank_by_keyword[keyword.id] += 1
            rank = rank_by_keyword[keyword.id]
            seller_username = sellers[idx % len(sellers)].seller_username
            gig = Gig(
                gig_url=f"https://fiverr.com/gig/integration-{idx}",
                keyword_id=keyword.id,
                run_id="integration-run",
                seller_username=seller_username,
                starting_price=50.0 + float(idx * 10),
                rating_exact=4.1 + float((idx % 4) * 0.2),
                review_count_exact=15 + idx * 7,
                orders_in_queue=idx % 5,
                video_present=(idx % 2 == 0),
                portfolio_count=idx % 3,
                packages=[{"name": "Basic", "price": 50 + idx * 10, "delivery_days": 2 + (idx % 4)}],
                position=rank,
                detail_collected=True,
            )
            session.add(gig)
            session.flush()

            session.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id="integration-run",
                    page_collected=rank,
                    rank=rank,
                    gig_id=gig.id,
                )
            )
            session.add(
                GigQualityScore(
                    gig_id=gig.id,
                    gig_url=gig.gig_url,
                    keyword_id=keyword.id,
                    run_id="integration-run",
                    analysis_complete=True,
                    video_present=(idx % 2 == 0),
                    portfolio_count=idx % 3,
                )
            )
            session.commit()

        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 0, 1], dtype=int), 0.55),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)

        clustering_result = _run(
            run_clustering_for_niche(
                niche_id="test_niche",
                run_id="integration-run",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "depth": "standard"}]},
                llm_client=None,
                cache=None,
            )
        )
        profiling_result = _run(
            run_competitor_profiling_for_niche(
                niche_id="test_niche",
                run_id="integration-run",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )

        assignments = session.scalars(select(ClusterAssignment)).all()
        competitor_profile = session.scalars(select(CompetitorProfile)).one_or_none()
        refreshed_keywords = session.scalars(select(Keyword).order_by(Keyword.id)).all()

        assert clustering_result["clustered"] is True
        assert len(assignments) == 3
        assert profiling_result["profiled"] is True
        assert competitor_profile is not None
        assert competitor_profile.median_price is not None
        assert all(keyword.cluster_id is not None for keyword in refreshed_keywords)
    finally:
        session.close()

