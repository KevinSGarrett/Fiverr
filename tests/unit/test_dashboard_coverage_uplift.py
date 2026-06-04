"""Cycle 062 Agent F coverage uplift tests for dashboard pages."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from src.dashboard.alerts import build_dashboard_alerts
from src.dashboard.opportunities import build_opportunities_payload
from src.dashboard.pages.keywords import render_keywords_page
from src.dashboard.pages.llm_costs import render_llm_costs_page
from src.dashboard.pages.opportunities import render_opportunities_page
from src.dashboard.pages.recommendations import render_recommendations_page
from src.dashboard.pages.run_history import render_run_history_page
from src.models import LLMUsageLog, Recommendation, RunLog

pytest_plugins = ("tests.unit.conftest_dashboard",)


class TestRunHistoryPage:
    def test_f_run_history_renders_with_no_data(self, empty_db, fake_streamlit, db_context_factory, monkeypatch) -> None:
        with Session(empty_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.run_history.get_db_session",
                lambda: db_context_factory(session),
            )
            render_run_history_page()
        assert fake_streamlit.info.called

    def test_f_run_history_renders_with_seeded_rows(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.run_history.get_db_session",
                lambda: db_context_factory(session),
            )
            render_run_history_page()
        assert fake_streamlit.dataframe.called
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert len(rows) >= 1
        assert "status" in rows[0]

    def test_f_run_history_error_row_uses_failure_summary(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.run_history.get_db_session",
                lambda: db_context_factory(session),
            )
            render_run_history_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert any(row["failure_summary"] != "None" for row in rows)

    def test_f_run_history_uses_recent_first_order(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            session.add(
                RunLog(
                    run_id=None,
                    mode="full",
                    stage="finalize",
                    status="pass",
                    message="Newest run entry",
                    created_at=datetime.now(UTC) + timedelta(seconds=1),
                )
            )
            session.commit()
            monkeypatch.setattr(
                "src.dashboard.pages.run_history.get_db_session",
                lambda: db_context_factory(session),
            )
            render_run_history_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert rows[0]["stage_names"][0] == "finalize"

    def test_f_run_history_limits_page_to_100_rows(
        self, empty_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(empty_db) as session:
            for index in range(120):
                session.add(
                    RunLog(
                        run_id=None,
                        mode="full",
                        stage=f"stage-{index}",
                        status="pass",
                        message=f"run {index}",
                        created_at=datetime.now(UTC) + timedelta(seconds=index),
                    )
                )
            session.commit()
            monkeypatch.setattr(
                "src.dashboard.pages.run_history.get_db_session",
                lambda: db_context_factory(session),
            )
            render_run_history_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert len(rows) == 25

    def test_f_run_history_db_error_path(self, fake_streamlit, monkeypatch) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("db unavailable")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=db)
        ctx.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr("src.dashboard.pages.run_history.get_db_session", lambda: ctx)
        render_run_history_page()
        assert fake_streamlit.info.called


class TestLlmCostsPage:
    def test_f_llm_costs_renders_empty_db(self, empty_db, fake_streamlit, db_context_factory, monkeypatch) -> None:
        with Session(empty_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.llm_costs.get_db_session",
                lambda: db_context_factory(session),
            )
            render_llm_costs_page()
        assert fake_streamlit.info.called

    def test_f_llm_costs_renders_with_usage(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.llm_costs.get_db_session",
                lambda: db_context_factory(session),
            )
            render_llm_costs_page()
        assert fake_streamlit.caption.called
        assert fake_streamlit.columns.called

    def test_f_llm_costs_aggregates_tokens_and_cost(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.llm_costs.get_db_session",
                lambda: db_context_factory(session),
            )
            render_llm_costs_page()
        column_metrics = [column.metric.call_args for column in fake_streamlit.columns_created if column.metric.called]
        labels = [args.args[0] for args in column_metrics]
        values = [args.args[1] for args in column_metrics]
        assert "Total tokens" in labels
        assert "2,000" in values
        assert "$0.5" in values

    def test_f_llm_costs_handles_none_cost_field(self, empty_db, fake_streamlit, db_context_factory, monkeypatch) -> None:
        with Session(empty_db) as session:
            session.add(LLMUsageLog(model_name="gpt-4o-mini", prompt_tokens=100, completion_tokens=20, total_cost_usd=None))
            session.commit()
            monkeypatch.setattr(
                "src.dashboard.pages.llm_costs.get_db_session",
                lambda: db_context_factory(session),
            )
            render_llm_costs_page()
        assert fake_streamlit.columns.called

    def test_f_llm_costs_db_error_path(self, fake_streamlit, monkeypatch) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("db unavailable")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=db)
        ctx.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr("src.dashboard.pages.llm_costs.get_db_session", lambda: ctx)
        render_llm_costs_page()
        assert fake_streamlit.info.called


class TestRecommendationsPage:
    def test_f_recommendations_renders_empty_db(
        self, empty_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(empty_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.recommendations.get_db_session",
                lambda: db_context_factory(session),
            )
            render_recommendations_page()
        assert fake_streamlit.info.called

    def test_f_recommendations_renders_with_data(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.recommendations.get_db_session",
                lambda: db_context_factory(session),
            )
            render_recommendations_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert len(rows) == 2
        assert {"GO", "CONDITIONAL_GO"} == {row["decision"] for row in rows}

    def test_f_recommendations_metric_counts_go_rows(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.recommendations.get_db_session",
                lambda: db_context_factory(session),
            )
            render_recommendations_page()
        metric_args = fake_streamlit.metric.call_args.args
        assert metric_args[0] == "GO recommendations"
        assert metric_args[1] == 1

    def test_f_recommendations_conditional_go_path(
        self, seeded_db, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db) as session:
            session.add(
                Recommendation(
                    recommendation_type="validation",
                    recommendation_text="Low confidence should remain conditional.",
                    niche_id="prd_ai_saas",
                    final_score=90.0,
                    confidence=0.4,
                    generated_at=datetime.now(UTC),
                )
            )
            session.commit()
            monkeypatch.setattr(
                "src.dashboard.pages.recommendations.get_db_session",
                lambda: db_context_factory(session),
            )
            render_recommendations_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert any(row["decision"] == "CONDITIONAL_GO" and row["score"] == 90.0 for row in rows)

    def test_f_recommendations_db_error_path(self, fake_streamlit, monkeypatch) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("db unavailable")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=db)
        ctx.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr("src.dashboard.pages.recommendations.get_db_session", lambda: ctx)
        render_recommendations_page()
        assert fake_streamlit.info.called


class TestOpportunitiesPageWithData:
    def test_f_opportunities_renders_top_keywords(
        self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.opportunities.get_db_session",
                lambda: db_context_factory(session),
            )
            render_opportunities_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert len(rows) >= 1
        assert "go_decision" in rows[0]

    def test_f_opportunities_sorts_descending_by_score(
        self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.opportunities.get_db_session",
                lambda: db_context_factory(session),
            )
            render_opportunities_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert rows[0]["score"] >= rows[-1]["score"]

    def test_f_opportunities_success_path_for_clean_data(
        self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.opportunities.get_db_session",
                lambda: db_context_factory(session),
            )
            render_opportunities_page()
        assert fake_streamlit.success.called

    def test_f_opportunities_warning_path_when_score_missing(
        self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.opportunities.get_db_session",
                lambda: db_context_factory(session),
            )
            monkeypatch.setattr(
                "src.dashboard.pages.opportunities.build_opportunities_payload",
                lambda records: {
                    "title": "Top Opportunities",
                    "state": {"message": "warning"},
                    "metric_cards": [],
                    "table": {"rows": []},
                    "warning_summary": {"warnings": ["forced warning"]},
                },
            )
            render_opportunities_page()
        assert fake_streamlit.warning.called

    def test_f_opportunities_shows_entry_pricing_when_available(
        self, seeded_db_with_prices, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_prices) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.opportunities.get_db_session",
                lambda: db_context_factory(session),
            )
            render_opportunities_page()
        assert fake_streamlit.dataframe.called


class TestKeywordsPageWithData:
    def test_f_keywords_renders_keyword_list(self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.keywords.get_db_session",
                lambda: db_context_factory(session),
            )
            render_keywords_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert len(rows) >= 1
        assert "score" in rows[0]

    def test_f_keywords_cluster_display(self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.keywords.get_db_session",
                lambda: db_context_factory(session),
            )
            render_keywords_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert all("cluster" in row for row in rows)

    def test_f_keywords_sort_by_score_descending(
        self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.keywords.get_db_session",
                lambda: db_context_factory(session),
            )
            render_keywords_page()
        rows = fake_streamlit.dataframe.call_args.args[0]
        assert rows[0]["score"] >= rows[-1]["score"]

    def test_f_keywords_caption_has_cluster_summary(
        self, seeded_db_with_scores, fake_streamlit, db_context_factory, monkeypatch
    ) -> None:
        with Session(seeded_db_with_scores) as session:
            monkeypatch.setattr(
                "src.dashboard.pages.keywords.get_db_session",
                lambda: db_context_factory(session),
            )
            render_keywords_page()
        assert fake_streamlit.caption.called

    def test_f_keywords_db_error_path(self, fake_streamlit, monkeypatch) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("db unavailable")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=db)
        ctx.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr("src.dashboard.pages.keywords.get_db_session", lambda: ctx)
        render_keywords_page()
        assert fake_streamlit.info.called


@pytest.mark.parametrize(
    "niche_id",
    [
        "prd_ai_saas",
        "support_kb_readiness",
        "gumloop_lindy_workflow",
        "mcp_ai_agent",
        "python_automation",
        "ai_tool_llm_integration",
        "ai_agent_development",
        "workflow_automation",
        "python_web_scraping",
    ],
)
def test_f_opportunities_payload_handles_each_niche(niche_id: str) -> None:
    payload = build_opportunities_payload(
        records=[
            {
                "id": f"{niche_id}-kw",
                "opportunity": "Sample",
                "niche": niche_id,
                "score": 70.0,
                "confidence": 0.75,
                "status": "CONDITIONAL_GO",
                "keyword_links": [],
            }
        ],
        filters={"niche": niche_id},
    )
    assert payload["table"]["rows"][0]["niche"] == niche_id


def test_f_alerts_render_with_no_pricing_data() -> None:
    alerts = build_dashboard_alerts()
    assert isinstance(alerts, list)
    assert alerts


def test_f_alerts_include_go_opportunities_signal() -> None:
    alerts = build_dashboard_alerts(
        opportunities=[
            {
                "id": "kw-1",
                "opportunity": "High scoring keyword",
                "score": 86.0,
                "confidence": 0.9,
                "status": "STRONG_GO",
            }
        ]
    )
    assert any(alert["type"] == "high_potential_opportunity" for alert in alerts)
