"""Targeted tests for live pilot backfill helpers."""

from __future__ import annotations

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.collection.live_pilot import _backfill_gigs_from_search_results
from src.models import Base
from src.models.gig import Gig
from src.models.market import Keyword
from src.models.niche import Niche
from src.models.search_result import SearchResult


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return factory()


def test_backfill_gigs_from_search_results_handles_list_cards() -> None:
    session = _session()
    niche = Niche(slug="python_automation", name="Python Automation", category_path="programming-tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="python automation", normalized_keyword="python automation")
    session.add(keyword)
    session.flush()
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="run_1",
            page_collected=1,
            gig_cards=[
                {
                    "gig_url": "https://www.fiverr.com/gig/sample-1",
                    "seller_username": "seller_one",
                    "position": 3,
                    "starting_price": 25,
                    "gig_title": "I will automate Python workflows",
                    "sponsored_flag": True,
                }
            ],
        )
    )
    session.commit()

    count = _backfill_gigs_from_search_results(db=session, run_id="run_1", max_cards=10)

    assert count == 1
    assert session.query(Gig).count() == 1


def test_backfill_gigs_from_search_results_handles_json_string_cards() -> None:
    session = _session()
    niche = Niche(slug="ai_agent", name="AI Agent", category_path="programming-tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="ai agent", normalized_keyword="ai agent")
    session.add(keyword)
    session.flush()
    cards_payload = json.dumps(
        [
            {
                "gig_url": "https://www.fiverr.com/gig/sample-2",
                "seller_username": "seller_two",
                "position": "2",
                "starting_price": 30,
                "gig_title": "I will build your AI agent",
                "sponsored_flag": False,
            }
        ]
    )
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="run_2",
            page_collected=1,
            gig_cards=cards_payload,
        )
    )
    session.commit()

    count = _backfill_gigs_from_search_results(db=session, run_id="run_2", max_cards=10)

    assert count == 1


def test_backfill_gigs_from_search_results_skips_invalid_json_payload() -> None:
    session = _session()
    niche = Niche(slug="niche_invalid_json", name="Invalid JSON Niche", category_path="programming-tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="invalid json", normalized_keyword="invalid json")
    session.add(keyword)
    session.flush()
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="run_3",
            page_collected=1,
            gig_cards="{not valid json",
        )
    )
    session.commit()

    count = _backfill_gigs_from_search_results(db=session, run_id="run_3", max_cards=10)

    assert count == 0
    assert session.query(Gig).count() == 0


def test_backfill_gigs_from_search_results_respects_max_cards_limit() -> None:
    session = _session()
    niche = Niche(slug="niche_limit", name="Limit Niche", category_path="programming-tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="limit cards", normalized_keyword="limit cards")
    session.add(keyword)
    session.flush()
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="run_4",
            page_collected=1,
            gig_cards=[
                {"gig_url": "https://www.fiverr.com/gig/limit-1", "seller_username": "seller_a"},
                {"gig_url": "https://www.fiverr.com/gig/limit-2", "seller_username": "seller_b"},
                {"gig_url": "", "seller_username": "seller_c"},
            ],
        )
    )
    session.commit()

    count = _backfill_gigs_from_search_results(db=session, run_id="run_4", max_cards=1)

    assert count == 1
    assert session.query(Gig).count() == 1


def test_backfill_gigs_from_search_results_returns_zero_for_non_session() -> None:
    count = _backfill_gigs_from_search_results(db=object(), run_id="run_x", max_cards=10)
    assert count == 0
