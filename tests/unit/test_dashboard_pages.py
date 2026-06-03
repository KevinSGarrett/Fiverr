"""Coverage for dashboard page render functions (sample-data mode)."""

from __future__ import annotations

import sys
from types import SimpleNamespace

from src.dashboard.pages.competitors import render_competitors_page
from src.dashboard.pages.discovery import render_discovery_page
from src.dashboard.pages.keywords import render_keywords_page
from src.dashboard.pages.llm_costs import render_llm_costs_page
from src.dashboard.pages.opportunities import render_opportunities_page
from src.dashboard.pages.playbook import render_playbook_page
from src.dashboard.pages.pricing import render_pricing_page
from src.dashboard.pages.recommendations import render_recommendations_page
from src.dashboard.pages.run_history import render_run_history_page


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


def test_dashboard_pages_render_with_sample_data(monkeypatch) -> None:
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

    render_opportunities_page()
    render_keywords_page()
    render_competitors_page()
    render_recommendations_page()
    render_run_history_page()
    render_llm_costs_page()
    render_discovery_page()
    render_playbook_page()
    render_pricing_page()
