"""Shared fixtures for dashboard coverage uplift tests."""

from __future__ import annotations

import json
import sys
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import (
    Base,
    Keyword,
    KeywordScore,
    LLMUsageLog,
    Niche,
    PricingSnapshot,
    Recommendation,
    RunLog,
)


class FakeColumn:
    """Lightweight streamlit column test-double."""

    def __init__(self) -> None:
        self.metric = MagicMock()


@pytest.fixture(name="dashboard_engine")
def fixture_dashboard_engine():
    """Create a shared in-memory engine for dashboard fixtures."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(name="empty_db")
def fixture_empty_db(dashboard_engine):
    """In-memory DB with schema and no rows."""
    return dashboard_engine


@pytest.fixture(name="dashboard_session")
def fixture_dashboard_session(dashboard_engine) -> Generator[Session, None, None]:
    """Yield an ORM session bound to the in-memory engine."""
    session = sessionmaker(bind=dashboard_engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_context_factory():
    """Build context-manager mocks for page `get_db_session` patching."""

    def _factory(session: Session) -> MagicMock:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=session)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    return _factory


@pytest.fixture
def fake_streamlit(monkeypatch: pytest.MonkeyPatch):
    """Patch streamlit module with inspectable mocks."""
    streamlit_mock = SimpleNamespace(
        title=MagicMock(),
        subheader=MagicMock(),
        write=MagicMock(),
        warning=MagicMock(),
        success=MagicMock(),
        info=MagicMock(),
        caption=MagicMock(),
        dataframe=MagicMock(),
        metric=MagicMock(),
    )

    columns_created: list[FakeColumn] = []

    def _columns(count: int) -> list[FakeColumn]:
        cols = [FakeColumn() for _ in range(max(0, count))]
        columns_created.extend(cols)
        return cols

    streamlit_mock.columns = MagicMock(side_effect=_columns)
    streamlit_mock.columns_created = columns_created
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_mock)
    return streamlit_mock


@pytest.fixture(name="seeded_db")
def fixture_seeded_db(dashboard_engine):
    """DB seeded with minimal run-history, llm, and recommendation rows."""
    with Session(dashboard_engine) as session:
        niche = Niche(slug="prd_ai_saas", name="PRD AI SaaS", category_path="Programming & Tech")
        session.add(niche)
        session.flush()

        keyword = Keyword(
            niche_id=niche.id,
            keyword="ai prd writer",
            normalized_keyword="ai prd writer",
            cluster_id=1,
        )
        session.add(keyword)
        session.flush()

        session.add_all(
            [
                RunLog(
                    run_id=None,
                    mode="full",
                    stage="collect",
                    status="pass",
                    message="Collection completed",
                    created_at=datetime.now(UTC) - timedelta(days=1),
                ),
                RunLog(
                    run_id=None,
                    mode="full",
                    stage="analyze",
                    status="error",
                    message="Analysis failed on stage 10",
                    created_at=datetime.now(UTC),
                ),
            ]
        )

        session.add_all(
            [
                LLMUsageLog(
                    model_name="gpt-4o",
                    prompt_tokens=1200,
                    completion_tokens=300,
                    total_cost_usd=0.42,
                ),
                LLMUsageLog(
                    model_name="gpt-4o-mini",
                    prompt_tokens=400,
                    completion_tokens=100,
                    total_cost_usd=0.08,
                ),
            ]
        )

        session.add_all(
            [
                Recommendation(
                    keyword_id=keyword.id,
                    niche_id=niche.slug,
                    recommendation_type="positioning",
                    recommendation_text="Lead with AI PRD sprint delivery.",
                    final_score=88.0,
                    confidence=0.9,
                    generated_at=datetime.now(UTC),
                ),
                Recommendation(
                    keyword_id=keyword.id,
                    niche_id=niche.slug,
                    recommendation_type="packaging",
                    recommendation_text="Offer a discovery workshop package.",
                    final_score=72.0,
                    confidence=0.6,
                    generated_at=datetime.now(UTC) - timedelta(hours=1),
                ),
            ]
        )
        session.commit()
    return dashboard_engine


@pytest.fixture(name="seeded_db_with_scores")
def fixture_seeded_db_with_scores(dashboard_engine):
    """DB with niches, keywords, and keyword_scores for dashboard data paths."""
    niche_slugs = [
        "prd_ai_saas",
        "support_kb_readiness",
        "gumloop_lindy_workflow",
        "mcp_ai_agent",
        "python_automation",
        "ai_tool_llm_integration",
        "ai_agent_development",
        "workflow_automation",
        "python_web_scraping",
    ]

    with Session(dashboard_engine) as session:
        niches = []
        for slug in niche_slugs:
            niche = Niche(slug=slug, name=slug.replace("_", " ").title(), category_path="Programming & Tech")
            session.add(niche)
            niches.append(niche)
        session.flush()

        for index, niche in enumerate(niches, start=1):
            keyword = Keyword(
                niche_id=niche.id,
                keyword=f"{niche.slug} keyword",
                normalized_keyword=f"{niche.slug} keyword",
                cluster_id=index % 3 if index % 3 else None,
            )
            session.add(keyword)
            session.flush()
            session.add(
                KeywordScore(
                    keyword_id=keyword.id,
                    scoring_profile="default",
                    score_depth="standard",
                    final_score=45.0 + (index * 5),
                    confidence_modifier=0.5 + (index * 0.03),
                    tag="STRONG_GO" if index == 9 else "CONDITIONAL_GO",
                    demand_score=40.0 + index,
                    competition_score=55.0 - index,
                    opportunity_score=50.0 + index,
                )
            )
        session.commit()
    return dashboard_engine


@pytest.fixture(name="seeded_db_with_prices")
def fixture_seeded_db_with_prices(seeded_db_with_scores):
    """seeded_db_with_scores plus pricing snapshot rows."""
    with Session(seeded_db_with_scores) as session:
        keywords = session.query(Keyword).order_by(Keyword.id.asc()).limit(3).all()
        for kw in keywords:
            ladder = [
                {"milestone": milestone, "basic": 50 + milestone, "standard": 100 + milestone, "premium": 200 + milestone}
                for milestone in (5, 10, 25, 50, 100)
            ]
            session.add(
                PricingSnapshot(
                    keyword_id=kw.id,
                    niche_id="seeded-pricing",
                    run_id="test-run",
                    entry_basic=65.0,
                    entry_standard=145.0,
                    entry_premium=280.0,
                    acquisition_basic=55.0,
                    acquisition_standard=120.0,
                    acquisition_premium=240.0,
                    price_ladder=json.loads(json.dumps(ladder)),
                    market_type="WIDE_SPREAD",
                    confidence="MEDIUM",
                )
            )
        session.commit()
    return seeded_db_with_scores
