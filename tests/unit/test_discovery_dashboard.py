"""S7.9 discovery dashboard data-layer tests."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from src.dashboard.pages.discovery import (
    get_discovery_stats,
    get_gold_discoveries,
    get_mode_performance,
    render_discovery_page,
)
from src.models import DiscoveryCycleLog, Keyword, Niche

pytest_plugins = ("tests.unit.conftest_dashboard",)


@pytest.fixture(name="discovery_seeded_db")
def fixture_discovery_seeded_db(dashboard_engine):
    with Session(dashboard_engine) as session:
        niche_a = Niche(slug="prd_ai_saas", name="PRD AI SaaS", category_path="Programming & Tech")
        niche_b = Niche(slug="python_automation", name="Python Automation", category_path="Programming & Tech")
        session.add_all([niche_a, niche_b])
        session.flush()

        session.add_all(
            [
                DiscoveryCycleLog(
                    run_id="r-001",
                    hypotheses_generated=8,
                    hypotheses_gated=2,
                    hypotheses_accepted=3,
                    total_cost_usd=0.0,
                ),
                DiscoveryCycleLog(
                    run_id="r-002",
                    hypotheses_generated=10,
                    hypotheses_gated=4,
                    hypotheses_accepted=5,
                    total_cost_usd=0.0,
                ),
            ]
        )

        session.add_all(
            [
                Keyword(
                    niche_id=niche_a.id,
                    keyword="ai prd assistant",
                    normalized_keyword="ai prd assistant",
                    is_discovery=True,
                    discovery_mode="adjacent_keyword",
                    hypothesis_confidence=0.81,
                    discovered_in_run="r-002",
                ),
                Keyword(
                    niche_id=niche_a.id,
                    keyword="ai sprint prd",
                    normalized_keyword="ai sprint prd",
                    is_discovery=True,
                    discovery_mode="gap_exploit",
                    hypothesis_confidence=0.74,
                    discovered_in_run="r-002",
                ),
                Keyword(
                    niche_id=niche_a.id,
                    keyword="legacy unknown mode",
                    normalized_keyword="legacy unknown mode",
                    is_discovery=True,
                    discovery_mode=None,
                    hypothesis_confidence=0.79,
                    discovered_in_run="r-001",
                ),
                Keyword(
                    niche_id=niche_b.id,
                    keyword="low confidence row",
                    normalized_keyword="low confidence row",
                    is_discovery=True,
                    discovery_mode="trend_chase",
                    hypothesis_confidence=0.55,
                    discovered_in_run="r-001",
                ),
                Keyword(
                    niche_id=niche_b.id,
                    keyword="seed keyword",
                    normalized_keyword="seed keyword",
                    is_discovery=False,
                    discovery_mode="adjacent_keyword",
                    hypothesis_confidence=0.95,
                    discovered_in_run="r-001",
                ),
            ]
        )
        session.commit()
    return dashboard_engine


class TestGetDiscoveryStats:
    def test_empty_db_returns_zero_contract(self, empty_db) -> None:
        with Session(empty_db) as session:
            stats = get_discovery_stats(session)
        assert stats == {
            "total_runs": 0,
            "total_inserted": 0,
            "total_gated": 0,
            "last_run_at": None,
            "last_run_id": None,
        }

    def test_real_data_totals_are_correct(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            stats = get_discovery_stats(session)
        assert stats["total_runs"] == 2
        assert stats["total_inserted"] == 8
        assert stats["total_gated"] == 6

    def test_last_run_id_is_set(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            stats = get_discovery_stats(session)
        assert stats["last_run_id"] in {"r-001", "r-002"}

    def test_key_types_match_contract(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            stats = get_discovery_stats(session)
        assert isinstance(stats["total_runs"], int)
        assert isinstance(stats["total_inserted"], int)
        assert isinstance(stats["total_gated"], int)

    def test_all_required_keys_present(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            stats = get_discovery_stats(session)
        assert set(stats.keys()) == {
            "total_runs",
            "total_inserted",
            "total_gated",
            "last_run_at",
            "last_run_id",
        }

    def test_error_handling_returns_defaults(self) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("boom")
        stats = get_discovery_stats(db)
        assert stats["total_runs"] == 0
        assert stats["last_run_id"] is None


class TestGetGoldDiscoveries:
    def test_empty_returns_empty_list(self, empty_db) -> None:
        with Session(empty_db) as session:
            rows = get_gold_discoveries(session)
        assert rows == []

    def test_field_mapping_returns_expected_keys(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            rows = get_gold_discoveries(session)
        assert rows
        assert set(rows[0].keys()) == {
            "keyword_text",
            "niche_id",
            "discovery_mode",
            "specificity_score",
            "discovered_in_run",
        }

    def test_threshold_filters_out_low_confidence_rows(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            rows = get_gold_discoveries(session)
        texts = {row["keyword_text"] for row in rows}
        assert "low confidence row" not in texts

    def test_non_discovery_rows_are_excluded(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            rows = get_gold_discoveries(session)
        texts = {row["keyword_text"] for row in rows}
        assert "seed keyword" not in texts

    def test_limit_is_enforced(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            rows = get_gold_discoveries(session, limit=1)
        assert len(rows) == 1

    def test_niche_id_is_string(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            rows = get_gold_discoveries(session)
        assert all(isinstance(row["niche_id"], str) for row in rows)

    def test_error_returns_empty_list(self) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("db down")
        assert get_gold_discoveries(db) == []


class TestGetModePerformance:
    def test_empty_returns_empty_dict(self, empty_db) -> None:
        with Session(empty_db) as session:
            perf = get_mode_performance(session)
        assert perf == {}

    def test_groups_discovery_modes(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            perf = get_mode_performance(session)
        assert "adjacent_keyword" in perf
        assert "gap_exploit" in perf

    def test_none_mode_uses_unknown_key(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            perf = get_mode_performance(session)
        assert "unknown" in perf

    def test_rounds_average_to_three_decimals(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            perf = get_mode_performance(session)
        value = perf["adjacent_keyword"]["avg_specificity"]
        assert isinstance(value, float)
        assert value == round(value, 3)

    def test_counts_are_int(self, discovery_seeded_db) -> None:
        with Session(discovery_seeded_db) as session:
            perf = get_mode_performance(session)
        assert all(isinstance(data["count"], int) for data in perf.values())

    def test_error_returns_empty_dict(self) -> None:
        db = MagicMock()
        db.query.side_effect = RuntimeError("db down")
        assert get_mode_performance(db) == {}


class TestRenderDiscoveryPage:
    def test_empty_db_renders_info_guidance(
        self, empty_db, fake_streamlit, db_context_factory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with Session(empty_db) as session:
            monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: db_context_factory(session))
            render_discovery_page()
        assert fake_streamlit.info.called

    def test_renders_three_metric_columns(
        self, discovery_seeded_db, fake_streamlit, db_context_factory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with Session(discovery_seeded_db) as session:
            monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: db_context_factory(session))
            render_discovery_page()
        assert fake_streamlit.columns.called
        assert len(fake_streamlit.columns_created) == 3

    def test_shows_last_run_caption(
        self, discovery_seeded_db, fake_streamlit, db_context_factory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with Session(discovery_seeded_db) as session:
            monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: db_context_factory(session))
            render_discovery_page()
        assert fake_streamlit.caption.called

    def test_gold_data_renders_dataframe(
        self, discovery_seeded_db, fake_streamlit, db_context_factory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with Session(discovery_seeded_db) as session:
            monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: db_context_factory(session))
            render_discovery_page()
        assert fake_streamlit.dataframe.called

    def test_mode_data_renders_dataframe(
        self, discovery_seeded_db, fake_streamlit, db_context_factory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with Session(discovery_seeded_db) as session:
            monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: db_context_factory(session))
            render_discovery_page()
        assert fake_streamlit.dataframe.call_count >= 2

    def test_outer_error_path_never_raises(self, fake_streamlit, monkeypatch: pytest.MonkeyPatch) -> None:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(side_effect=RuntimeError("boom"))
        ctx.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr("src.dashboard.pages.discovery.get_db_session", lambda: ctx)
        render_discovery_page()
        assert fake_streamlit.info.called


class TestS79Integration:
    def test_discovery_helpers_are_importable(self) -> None:
        from src.dashboard.pages.discovery import get_discovery_stats as _stats
        from src.dashboard.pages.discovery import get_gold_discoveries as _gold
        from src.dashboard.pages.discovery import get_mode_performance as _mode

        assert callable(_stats)
        assert callable(_gold)
        assert callable(_mode)

    def test_stage16_imports_remain_intact(self) -> None:
        from src.discovery.stage16 import _select_modes, run_discovery_cycle

        assert callable(run_discovery_cycle)
        assert callable(_select_modes)

    def test_wave9_pricing_imports_remain_intact(self) -> None:
        from src.pricing import (
            analyze_price_distribution,
            build_pricing_export_payload,
            calculate_new_seller_pricing,
            export_all_pricing,
        )

        assert callable(analyze_price_distribution)
        assert callable(calculate_new_seller_pricing)
        assert callable(build_pricing_export_payload)
        assert callable(export_all_pricing)

    def test_discover_command_still_wired(self) -> None:
        content = Path("run.py").read_text(encoding="utf-8")
        assert "discover" in content

    def test_stage16_function_inventory_still_contains_core_symbols(self) -> None:
        tree = ast.parse(Path("src/discovery/stage16.py").read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        assert "run_discovery_cycle" in names
        assert "_select_modes" in names
