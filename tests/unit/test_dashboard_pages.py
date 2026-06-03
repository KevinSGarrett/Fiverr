"""Coverage for dashboard page render functions (empty DB live-data mode)."""

from __future__ import annotations

import sys
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from src.dashboard.pages.competitors import render_competitors_page
from src.dashboard.pages.discovery import render_discovery_page
from src.dashboard.pages.keywords import render_keywords_page
from src.dashboard.pages.llm_costs import render_llm_costs_page
from src.dashboard.pages.opportunities import render_opportunities_page
from src.dashboard.pages.playbook import render_playbook_page
from src.dashboard.pages.pricing import render_pricing_page
from src.dashboard.pages.recommendations import render_recommendations_page
from src.dashboard.pages.run_history import render_run_history_page
from src.models.base import Base
from src.models.keyword_score import KeywordScore
from src.models.market import Keyword
from src.models.niche import Niche


class _FakeColumn:
    def metric(self, *_args: object, **_kwargs: object) -> None:
        return None


class _FakeStreamlit:
    def title(self, *_args: object, **_kwargs: object) -> None:
        return None

    def subheader(self, *_args: object, **_kwargs: object) -> None:
        return None

    def write(self, *_args: object, **_kwargs: object) -> None:
        return None

    def warning(self, *_args: object, **_kwargs: object) -> None:
        return None

    def success(self, *_args: object, **_kwargs: object) -> None:
        return None

    def info(self, *_args: object, **_kwargs: object) -> None:
        return None

    def caption(self, *_args: object, **_kwargs: object) -> None:
        return None

    def dataframe(self, *_args: object, **_kwargs: object) -> None:
        return None

    def metric(self, *_args: object, **_kwargs: object) -> None:
        return None

    def columns(self, count: int) -> list[_FakeColumn]:
        return [_FakeColumn() for _ in range(max(0, count))]


@pytest.fixture
def empty_db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_streamlit(monkeypatch: pytest.MonkeyPatch) -> _FakeStreamlit:
    fake_streamlit = _FakeStreamlit()
    monkeypatch.setitem(
        sys.modules,
        "streamlit",
        SimpleNamespace(
            title=fake_streamlit.title,
            subheader=fake_streamlit.subheader,
            write=fake_streamlit.write,
            warning=fake_streamlit.warning,
            success=fake_streamlit.success,
            info=fake_streamlit.info,
            caption=fake_streamlit.caption,
            dataframe=fake_streamlit.dataframe,
            metric=fake_streamlit.metric,
            columns=fake_streamlit.columns,
        ),
    )
    return fake_streamlit


def _db_context(session: Session) -> MagicMock:
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def test_opportunities_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.opportunities.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_opportunities_page()


def test_keywords_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.keywords.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_keywords_page()


def test_competitors_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.competitors.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_competitors_page()


def test_recommendations_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.recommendations.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_recommendations_page()


def test_run_history_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.run_history.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_run_history_page()


def test_llm_costs_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.llm_costs.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_llm_costs_page()


def test_discovery_renders_empty_db_gracefully(
    empty_db_session: Session,
    fake_streamlit: _FakeStreamlit,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.discovery.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_discovery_page()


def test_playbook_renders_empty_db_gracefully(fake_streamlit: _FakeStreamlit) -> None:
    render_playbook_page()


def test_pricing_renders_empty_db_gracefully(fake_streamlit: _FakeStreamlit) -> None:
    render_pricing_page()


@pytest.fixture
def mock_db_context(
    empty_db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=empty_db_session)
    ctx.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr("src.dashboard.db_helpers.get_db_session", lambda: ctx)
    return ctx


@pytest.fixture
def mock_streamlit(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    title = MagicMock()
    subheader = MagicMock()
    info = MagicMock()
    error = MagicMock()
    warning = MagicMock()
    success = MagicMock()
    dataframe = MagicMock()
    write = MagicMock()
    columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    metric = MagicMock()
    caption = MagicMock()

    monkeypatch.setitem(
        sys.modules,
        "streamlit",
        SimpleNamespace(
            title=title,
            subheader=subheader,
            info=info,
            error=error,
            warning=warning,
            success=success,
            dataframe=dataframe,
            write=write,
            columns=columns,
            metric=metric,
            caption=caption,
        ),
    )

    patched = SimpleNamespace(
        title=title,
        subheader=subheader,
        info=info,
        error=error,
        warning=warning,
        success=success,
        dataframe=dataframe,
        write=write,
        columns=columns,
        metric=metric,
        caption=caption,
    )
    return patched


def test_dashboard_opportunities_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.opportunities.get_db_session", lambda: mock_db_context)
    render_opportunities_page()
    assert mock_streamlit.info.called


def test_dashboard_opportunities_uses_latest_score_per_keyword_profile(
    empty_db_session: Session,
    mock_streamlit: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    niche = Niche(
        slug="niche-1",
        name="Niche One",
        category_path="graphics/design",
    )
    empty_db_session.add(niche)
    empty_db_session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation script",
        normalized_keyword="python automation script",
    )
    empty_db_session.add(keyword)
    empty_db_session.flush()

    older = KeywordScore(
        keyword_id=keyword.id,
        scoring_profile="default",
        final_score=99.0,
        confidence_modifier=0.5,
        tag="OLD",
        scored_at=datetime.now(UTC) - timedelta(days=1),
    )
    latest = KeywordScore(
        keyword_id=keyword.id,
        scoring_profile="default",
        final_score=62.7,
        confidence_modifier=1.0,
        tag="CONDITIONAL_GO",
        scored_at=datetime.now(UTC),
    )
    empty_db_session.add_all([older, latest])
    empty_db_session.commit()

    monkeypatch.setattr(
        "src.dashboard.pages.opportunities.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_opportunities_page()

    assert mock_streamlit.dataframe.called
    displayed_rows = mock_streamlit.dataframe.call_args.args[0]
    assert len(displayed_rows) == 1
    assert displayed_rows[0]["status"] == "CONDITIONAL_GO"


def test_dashboard_keywords_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.keywords.get_db_session", lambda: mock_db_context)
    render_keywords_page()
    assert mock_streamlit.info.called


def test_dashboard_competitors_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.competitors.get_db_session", lambda: mock_db_context)
    render_competitors_page()
    assert mock_streamlit.info.called or mock_streamlit.write.called


def test_dashboard_recommendations_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.recommendations.get_db_session", lambda: mock_db_context)
    render_recommendations_page()
    assert mock_streamlit.info.called


def test_dashboard_run_history_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.run_history.get_db_session", lambda: mock_db_context)
    render_run_history_page()
    assert mock_streamlit.info.called


def test_dashboard_llm_costs_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.llm_costs.get_db_session", lambda: mock_db_context)
    render_llm_costs_page()
    assert mock_streamlit.info.called


def test_dashboard_discovery_renders_empty_db_gracefully(
    mock_streamlit: SimpleNamespace,
    mock_db_context: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = mock_db_context
    monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: mock_db_context)
    render_discovery_page()
    assert mock_streamlit.info.called


def test_dashboard_playbook_renders_empty_db_gracefully(mock_streamlit: SimpleNamespace) -> None:
    render_playbook_page()
    assert mock_streamlit.info.called


def test_dashboard_pricing_renders_empty_db_gracefully(mock_streamlit: SimpleNamespace) -> None:
    render_pricing_page()
    assert mock_streamlit.info.called
