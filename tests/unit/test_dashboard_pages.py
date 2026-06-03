"""Coverage for dashboard page render functions (empty DB live-data mode)."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
def empty_db_session():
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
def fake_streamlit(monkeypatch) -> _FakeStreamlit:
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


def _db_context(session):
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def test_opportunities_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.opportunities.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_opportunities_page()


def test_keywords_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.keywords.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_keywords_page()


def test_competitors_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.competitors.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_competitors_page()


def test_recommendations_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.recommendations.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_recommendations_page()


def test_run_history_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.run_history.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_run_history_page()


def test_llm_costs_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.llm_costs.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_llm_costs_page()


def test_discovery_renders_empty_db_gracefully(empty_db_session, fake_streamlit, monkeypatch) -> None:
    monkeypatch.setattr(
        "src.dashboard.pages.discovery.get_db_session",
        lambda: _db_context(empty_db_session),
    )
    render_discovery_page()


def test_playbook_renders_empty_db_gracefully(fake_streamlit) -> None:
    render_playbook_page()


def test_pricing_renders_empty_db_gracefully(fake_streamlit) -> None:
    render_pricing_page()
