"""Integration test for Stage 13 saturation analysis pipeline."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from src.analysis.saturation_model import run_saturation_analysis_for_niche
from src.models.database import create_session_factory, initialize_database
from src.models.market import Keyword, SaturationScore
from src.models.niche import Niche
from src.models.search_result import SearchResult


def _seed_keyword(session: object, niche: Niche, keyword_text: str) -> Keyword:
    row = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text.lower(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_saturation_stage13_end_to_end_creates_rows_and_scores_in_range() -> None:
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        niche = Niche(slug="test_niche", name="Test Niche", category_path="programming-tech/testing")
        session.add(niche)
        session.commit()
        session.refresh(niche)

        keywords = [
            _seed_keyword(session, niche, "python scraper"),
            _seed_keyword(session, niche, "automation scripts"),
            _seed_keyword(session, niche, "data extraction"),
            _seed_keyword(session, niche, "api integration"),
            _seed_keyword(session, niche, "workflow setup"),
        ]

        base_sellers = ["seller_a", "seller_b", "seller_c", "seller_d", "seller_e"]
        for idx, keyword in enumerate(keywords):
            gig_cards = [
                {
                    "gig_title": f"I will build python automation workflow {slot % 3}",
                    "starting_price": float(15 + idx + (slot % 4)),
                    "seller_username": base_sellers[slot % len(base_sellers)],
                }
                for slot in range(12)
            ]
            session.add(
                SearchResult(
                    keyword_id=keyword.id,
                    run_id="integration-saturation-run",
                    page_collected=1,
                    rank=1,
                    total_result_count=1200 + (idx * 100),
                    gig_cards=gig_cards,
                )
            )
        session.commit()

        result = asyncio.run(
            run_saturation_analysis_for_niche(
                niche_id="test_niche",
                run_id="integration-saturation-run",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )

        rows = session.scalars(
            select(SaturationScore).where(SaturationScore.run_id == "integration-saturation-run")
        ).all()

        assert result["analyzed"] is True
        assert result["keywords_analyzed"] == 5
        assert len(rows) == 5
        assert all(0.0 <= row.saturation_score <= 100.0 for row in rows)
    finally:
        session.close()

