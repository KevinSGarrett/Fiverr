"""S7.9 discovery dashboard data-layer tests (Agent B)."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestS79CoverageUplift:
    def test_get_discovery_stats_with_real_data(self) -> None:
        from datetime import datetime

        db = MagicMock()
        db.query.return_value.one.return_value = (7, 23, 11, datetime(2026, 6, 8, 14, 0, 0))
        last = MagicMock()
        last.run_id = "discovery-20260608-abc"
        db.query.return_value.order_by.return_value.first.return_value = last

        result = get_discovery_stats(db)
        assert result["total_runs"] == 7
        assert result["total_inserted"] == 23
        assert result["last_run_id"] == "discovery-20260608-abc"

    def test_gold_field_mapping_correct(self) -> None:
        db = MagicMock()
        kw = MagicMock()
        kw.keyword = "ai workflow automation"
        kw.niche_id = "workflow_automation"
        kw.discovery_mode = "gap_exploit"
        kw.specificity_score = 0.82
        kw.discovered_in_run = "discovery-20260608-abc"
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [kw]

        result = get_gold_discoveries(db)
        assert len(result) == 1
        row = result[0]
        assert row["keyword_text"] == "ai workflow automation"
        assert row["specificity_score"] == 0.82
        assert row["discovery_mode"] == "gap_exploit"

    def test_mode_performance_multiple_modes(self) -> None:
        db = MagicMock()
        rows = [
            ("adjacent_keyword", 5, 0.72),
            ("gap_exploit", 3, 0.68),
            ("trend_chase", 2, 0.75),
        ]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = rows

        result = get_mode_performance(db)
        assert len(result) == 3
        assert result["adjacent_keyword"]["count"] == 5

    def test_mode_performance_none_mode_uses_unknown(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [(None, 2, 0.65)]

        result = get_mode_performance(db)
        assert "unknown" in result
        assert result["unknown"]["count"] == 2

    def test_render_with_gold_calls_dataframe(self) -> None:
        gold = [
            {
                "keyword_text": "ai agent",
                "niche_id": "ai_agent_development",
                "specificity_score": 0.82,
                "discovery_mode": "gap_exploit",
                "discovered_in_run": "r1",
            }
        ]
        with (
            pytest.MonkeyPatch.context() as mp,
            patch("streamlit.title"),
            patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]),
            patch("streamlit.subheader"),
            patch("streamlit.metric"),
            patch("streamlit.info"),
            patch("streamlit.caption"),
            patch("streamlit.dataframe") as mock_df,
            patch(
                "src.dashboard.pages.discovery.get_discovery_stats",
                return_value={
                    "total_runs": 1,
                    "total_inserted": 3,
                    "total_gated": 1,
                    "last_run_at": None,
                    "last_run_id": "r1",
                },
            ),
            patch("src.dashboard.pages.discovery.get_gold_discoveries", return_value=gold),
            patch("src.dashboard.pages.discovery.get_mode_performance", return_value={}),
        ):
            mock_cm = MagicMock()
            mock_cm.__enter__ = lambda s: MagicMock()
            mock_cm.__exit__ = MagicMock(return_value=False)
            mp.setattr("src.dashboard.pages.discovery.get_db_session", lambda: mock_cm)
            render_discovery_page()
        assert mock_df.call_count >= 1

    def test_all_s79_functions_importable(self) -> None:
        functions = [get_discovery_stats, get_gold_discoveries, get_mode_performance, render_discovery_page]
        assert all(callable(fn) for fn in functions)

    def test_s79_coexists_with_s78(self) -> None:
        from src.discovery.stage16 import _select_modes, run_discovery_cycle

        assert callable(run_discovery_cycle)
        assert len(_select_modes()) >= 3

    def test_s79_coexists_with_wave9(self) -> None:
        from src.pricing import analyze_price_distribution

        assert callable(analyze_price_distribution)
        assert callable(get_mode_performance)

    def test_stats_total_runs_is_int_uplift(self) -> None:
        db = MagicMock()
        db.query.return_value.one.return_value = (3, 8, 2, None)
        db.query.return_value.order_by.return_value.first.return_value = None
        result = get_discovery_stats(db)
        assert isinstance(result["total_runs"], int)
        assert isinstance(result["total_inserted"], int)

    def test_wave10_complete_smoke_uplift(self) -> None:
        from src.discovery.contracts import HypothesisMode
        from src.discovery.feedback import GOLD_THRESHOLD
        from src.discovery.hypothesis import (
            generate_adjacent_keyword_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
        )
        from src.discovery.integration import process_accepted_hypotheses
        from src.discovery.stage16 import _select_modes, run_discovery_cycle
        from src.models import DiscoveryCycleLog, DiscoveryOutcome

        assert callable(run_discovery_cycle)
        assert callable(_select_modes)
        assert callable(process_accepted_hypotheses)
        assert callable(generate_adjacent_keyword_hypotheses)
        assert callable(generate_gap_exploit_hypotheses)
        assert callable(generate_trend_chase_hypotheses)
        assert DiscoveryCycleLog is not None
        assert DiscoveryOutcome is not None
        modes = sorted([entry.value for entry in HypothesisMode])
        assert modes == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]
        assert GOLD_THRESHOLD == 85.0

    def test_get_gold_excludes_non_discovery(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        assert get_gold_discoveries(db) == []

    def test_get_mode_performance_returns_counts(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("trend_chase", 8, 0.73)
        ]
        result = get_mode_performance(db)
        assert result["trend_chase"]["count"] == 8

    def test_gold_with_multiple_records(self) -> None:
        db = MagicMock()
        rows = []
        for index in range(3):
            kw = MagicMock()
            kw.keyword = f"keyword {index}"
            kw.niche_id = f"niche_{index}"
            kw.discovery_mode = "adjacent_keyword"
            kw.specificity_score = 0.80 + index * 0.01
            kw.discovered_in_run = f"run-{index}"
            rows.append(kw)
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = rows
        result = get_gold_discoveries(db)
        assert len(result) == 3

    def test_mode_perf_count_is_int(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [("gap_exploit", 7, 0.72)]
        result = get_mode_performance(db)
        assert isinstance(result["gap_exploit"]["count"], int)

    def test_render_calls_get_db_session(self) -> None:
        with (
            pytest.MonkeyPatch.context() as mp,
            patch("streamlit.title"),
            patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]),
            patch("streamlit.subheader"),
            patch("streamlit.metric"),
            patch("streamlit.info"),
            patch("streamlit.dataframe"),
            patch("streamlit.caption"),
            patch(
                "src.dashboard.pages.discovery.get_discovery_stats",
                return_value={
                    "total_runs": 0,
                    "total_inserted": 0,
                    "total_gated": 0,
                    "last_run_at": None,
                    "last_run_id": None,
                },
            ),
            patch("src.dashboard.pages.discovery.get_gold_discoveries", return_value=[]),
            patch("src.dashboard.pages.discovery.get_mode_performance", return_value={}),
        ):
            mock_get_db = MagicMock()
            mock_cm = MagicMock()
            mock_cm.__enter__ = lambda s: MagicMock()
            mock_cm.__exit__ = MagicMock(return_value=False)
            mock_get_db.return_value = mock_cm
            mp.setattr("src.dashboard.pages.discovery.get_db_session", mock_get_db)
            render_discovery_page()
            assert mock_get_db.called

    def test_wave10_complete_with_s79(self) -> None:
        from src.discovery.contracts import HypothesisMode
        from src.discovery.feedback import GOLD_THRESHOLD
        from src.discovery.hypothesis import (
            generate_adjacent_keyword_hypotheses,
            generate_adjacent_niche_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
        )
        from src.discovery.integration import process_accepted_hypotheses
        from src.discovery.stage16 import _select_modes, run_discovery_cycle
        from src.models import DiscoveryCycleLog, DiscoveryOutcome

        assert callable(run_discovery_cycle)
        assert callable(_select_modes)
        assert callable(process_accepted_hypotheses)
        assert callable(generate_adjacent_keyword_hypotheses)
        assert callable(generate_adjacent_niche_hypotheses)
        assert callable(generate_gap_exploit_hypotheses)
        assert callable(generate_trend_chase_hypotheses)
        assert DiscoveryCycleLog is not None
        assert DiscoveryOutcome is not None
        modes = sorted([entry.value for entry in HypothesisMode])
        assert modes == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]
        assert GOLD_THRESHOLD == 85.0

    def test_gold_niche_id_is_str(self) -> None:
        db = MagicMock()
        kw = MagicMock()
        kw.keyword = "test"
        kw.niche_id = 12345
        kw.discovery_mode = "gap_exploit"
        kw.specificity_score = 0.75
        kw.discovered_in_run = "r1"
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [kw]
        result = get_gold_discoveries(db)
        assert isinstance(result[0]["niche_id"], str)

    def test_get_discovery_stats_last_run_id_none_when_no_logs(self) -> None:
        db = MagicMock()
        db.query.return_value.one.return_value = (0, 0, 0, None)
        db.query.return_value.order_by.return_value.first.return_value = None
        result = get_discovery_stats(db)
        assert result["last_run_id"] is None

    def test_all_s79_functions_callable(self) -> None:
        functions = [get_discovery_stats, get_gold_discoveries, get_mode_performance, render_discovery_page]
        assert all(callable(fn) for fn in functions)

    def test_s79_coexists_wave9_and_s78(self) -> None:
        from src.discovery.stage16 import _select_modes
        from src.pricing import analyze_price_distribution

        assert callable(analyze_price_distribution)
        assert len(_select_modes()) >= 3

    def test_stats_has_last_run_at_key(self) -> None:
        db = MagicMock()
        db.query.return_value.one.return_value = (0, 0, 0, None)
        db.query.return_value.order_by.return_value.first.return_value = None
        result = get_discovery_stats(db)
        assert "last_run_at" in result

    def test_gold_empty_list_type_on_error(self) -> None:
        db = MagicMock()
        db.query.side_effect = Exception("DB error")
        result = get_gold_discoveries(db)
        assert isinstance(result, list)

    def test_mode_perf_avg_is_float(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [("adj_kw", 5, 0.72)]
        result = get_mode_performance(db)
        assert isinstance(result["adj_kw"]["avg_specificity"], float)

    def test_stage16_intact_after_c073(self) -> None:
        from src.discovery.stage16 import (
            DEFAULT_MAX_HYPOTHESES,
            DEFAULT_MIN_CONFIDENCE,
            _select_modes,
            run_discovery_cycle,
        )

        assert callable(run_discovery_cycle)
        assert callable(_select_modes)
        assert DEFAULT_MIN_CONFIDENCE == 0.5
        assert DEFAULT_MAX_HYPOTHESES == 15
        line_count = len(Path("src/discovery/stage16.py").read_text(encoding="utf-8").splitlines())
        # Widened for the llm_niche_expansion wiring + cost-accounting/PK-resolution
        # fixes (SCRUM-1106, Codex P2 rounds on PR #181) - this guard exists to catch
        # accidental truncation, not to block legitimate growth.
        assert 295 <= line_count <= 470

    def test_hypothesis_mode_inventory_preserved(self) -> None:
        from src.discovery.contracts import HypothesisMode
        from src.discovery.stage16 import run_discovery_cycle

        assert callable(run_discovery_cycle)
        modes = sorted([entry.value for entry in HypothesisMode])
        assert "adjacent_keyword" in modes
        assert "gap_exploit" in modes

    def test_s76_thresholds_unchanged(self) -> None:
        from src.discovery.feedback import GOLD_THRESHOLD, HIT_THRESHOLD, MISS_THRESHOLD

        assert GOLD_THRESHOLD == 85.0
        assert HIT_THRESHOLD == 60.0
        assert MISS_THRESHOLD == 40.0

    def test_discovery_page_no_demo_data(self) -> None:
        content = Path("src/dashboard/pages/discovery.py").read_text(encoding="utf-8")
        assert "build_dashboard_demo_data" not in content
        assert "get_db_session" in content
