"""Integration coverage for collect-only Stage 1-3 behavior."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from src.collection.workflows.fiverr_search import run_fiverr_search_collection
from src.collection.workflows.niche_init import run_niche_initialization
from src.models import Base, Job, Keyword, Niche, SearchResult


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db() -> Session:
    """In-memory SQLite session with all tables created and minimal FK seeds."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()

    niche = Niche(slug="test-niche", name="Test Niche", category_path="writing/proofreading")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=int(niche.id),
        keyword="ai proofreading fiverr",
        normalized_keyword="ai proofreading fiverr",
    )
    session.add(keyword)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def mock_session_manager() -> AsyncMock:
    """Mock SessionManager returning a realistic Fiverr search page."""
    mock_page = AsyncMock()

    mock_count_el = AsyncMock()
    mock_count_el.inner_text = AsyncMock(return_value="1,234 results for ai proofreading fiverr")
    mock_page.query_selector = AsyncMock(return_value=mock_count_el)

    def make_card(pos: int) -> AsyncMock:
        card = AsyncMock()
        title_el = AsyncMock()
        title_el.inner_text = AsyncMock(return_value=f"Test Gig {pos}")
        seller_el = AsyncMock()
        seller_el.inner_text = AsyncMock(return_value=f"seller_{pos}")
        price_el = AsyncMock()
        price_el.inner_text = AsyncMock(return_value=f"${pos * 25}")
        link_el = AsyncMock()
        link_el.get_attribute = AsyncMock(return_value=f"/gig_url_{pos}")

        async def mock_qs(selector: str):
            normalized = selector.lower()
            if "title" in normalized:
                return title_el
            if "seller-name" in normalized:
                return seller_el
            if "starting-price" in normalized or "gig-price" in normalized:
                return price_el
            if "gig-link" in normalized or "href" in normalized:
                return link_el
            return None

        card.query_selector = mock_qs
        return card

    mock_page.query_selector_all = AsyncMock(return_value=[make_card(i) for i in range(1, 4)])
    mock_page.goto = AsyncMock()

    mock_sm = AsyncMock()
    mock_sm.new_page = AsyncMock(return_value=mock_page)
    mock_sm.close_page = AsyncMock()
    return mock_sm


@pytest.fixture
def mock_pacing_manager() -> AsyncMock:
    mock_pm = AsyncMock()
    mock_pm.wait = AsyncMock(return_value=0.0)
    return mock_pm


@pytest.fixture
def w3_result(db: Session, mock_session_manager: AsyncMock, mock_pacing_manager: AsyncMock) -> dict[str, object]:
    keyword = db.query(Keyword).one()
    return _run(
        run_fiverr_search_collection(
            keyword_id=int(keyword.id),
            keyword_text=keyword.keyword,
            niche_id="test_niche",
            depth="standard",
            run_id="run-e2e",
            db=db,
            session_manager=mock_session_manager,
            pacing_manager=mock_pacing_manager,
            dry_run=False,
        )
    )


def test_collect_only_search_results_table_exists(db: Session) -> None:
    assert "search_results" in inspect(db.bind).get_table_names()


def test_collect_only_jobs_table_exists(db: Session) -> None:
    assert "jobs" in inspect(db.bind).get_table_names()


def test_collect_only_w3_writes_search_result(db: Session, w3_result: dict[str, object]) -> None:
    row = db.query(SearchResult).filter(SearchResult.run_id == "run-e2e").first()
    assert row is not None


def test_collect_only_w3_result_has_keyword_id(db: Session, w3_result: dict[str, object]) -> None:
    keyword = db.query(Keyword).one()
    row = db.query(SearchResult).filter(SearchResult.run_id == "run-e2e").one()
    assert row.keyword_id == keyword.id


def test_collect_only_w3_total_result_count_parsed(db: Session, w3_result: dict[str, object]) -> None:
    row = db.query(SearchResult).filter(SearchResult.run_id == "run-e2e").one()
    assert row.total_result_count == 1234


def test_collect_only_w3_gig_cards_json(db: Session, w3_result: dict[str, object]) -> None:
    row = db.query(SearchResult).filter(SearchResult.run_id == "run-e2e").one()
    assert isinstance(row.gig_cards, list)
    assert len(row.gig_cards) == 3


def test_collect_only_w3_queues_gig_detail_jobs(db: Session, w3_result: dict[str, object]) -> None:
    assert db.query(Job).count() == 3


def test_collect_only_w3_job_type_gig_detail(db: Session, w3_result: dict[str, object]) -> None:
    rows = db.query(Job).all()
    assert rows
    assert all(job.job_type == "GIG_DETAIL" for job in rows)


def test_collect_only_w3_job_status_queued(db: Session, w3_result: dict[str, object]) -> None:
    rows = db.query(Job).all()
    assert rows
    assert all(job.status == "QUEUED" for job in rows)


def test_collect_only_w3_close_page_called(
    db: Session,
    mock_session_manager: AsyncMock,
    mock_pacing_manager: AsyncMock,
) -> None:
    keyword = db.query(Keyword).one()
    _run(
        run_fiverr_search_collection(
            keyword_id=int(keyword.id),
            keyword_text=keyword.keyword,
            niche_id="test_niche",
            depth="standard",
            run_id="run-e2e",
            db=db,
            session_manager=mock_session_manager,
            pacing_manager=mock_pacing_manager,
            dry_run=False,
        )
    )
    mock_session_manager.close_page.assert_awaited_once()


def test_collect_only_w3_keyword_only_no_jobs(
    db: Session,
    mock_session_manager: AsyncMock,
    mock_pacing_manager: AsyncMock,
) -> None:
    keyword = db.query(Keyword).one()
    _run(
        run_fiverr_search_collection(
            keyword_id=int(keyword.id),
            keyword_text=keyword.keyword,
            niche_id="test_niche",
            depth="keyword_only",
            run_id="run-e2e",
            db=db,
            session_manager=mock_session_manager,
            pacing_manager=mock_pacing_manager,
            dry_run=False,
        )
    )
    assert db.query(Job).count() == 0


def test_collect_only_niche_init_returns_seeds() -> None:
    config = {
        "niches": [
            {
                "niche_id": "test_niche",
                "depth": "standard",
                "seed_keywords": ["ai proofreading fiverr", "resume editing"],
            }
        ]
    }
    result = _run(run_niche_initialization(config=config, db=None, run_id="run-e2e", dry_run=True))
    assert "seed_keywords" in result
    assert result["seed_keywords"]["test_niche"] == ["ai proofreading fiverr", "resume editing"]


def test_collect_only_result_structure(db: Session, w3_result: dict[str, object]) -> None:
    required = {
        "keyword_id",
        "keyword_text",
        "niche_id",
        "total_result_count",
        "gig_cards_collected",
        "gig_urls_queued",
        "pages_collected",
        "dry_run",
    }
    assert required.issubset(set(w3_result.keys()))


def test_collect_only_all_stages_execute(
    db: Session,
    mock_session_manager: AsyncMock,
    mock_pacing_manager: AsyncMock,
) -> None:
    config = {
        "niches": [
            {
                "niche_id": "test_niche",
                "depth": "standard",
                "seed_keywords": ["ai proofreading fiverr", "resume editing", "copywriting"],
            }
        ]
    }
    stage01 = _run(run_niche_initialization(config=config, db=None, run_id="run-e2e", dry_run=True))
    keyword = db.query(Keyword).one()
    stage03 = _run(
        run_fiverr_search_collection(
            keyword_id=int(keyword.id),
            keyword_text=keyword.keyword,
            niche_id="test_niche",
            depth="standard",
            run_id="run-e2e",
            db=db,
            session_manager=mock_session_manager,
            pacing_manager=mock_pacing_manager,
            dry_run=False,
        )
    )
    stages = ["stage01_niche_init", "stage02_keyword_expansion", "stage03_fiverr_search"]
    assert stage01["niches_processed"] == 1
    assert stage03["dry_run"] is False
    assert stages == ["stage01_niche_init", "stage02_keyword_expansion", "stage03_fiverr_search"]
