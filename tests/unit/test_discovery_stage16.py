"""Tests for S7.8 Stage 16 discovery orchestration."""

from __future__ import annotations

import ast
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

RUN_ID = "discovery-20260608-120000-abc12345"


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    return db


class TestSelectModes:
    def test_base_modes_always_included(self) -> None:
        from src.discovery.stage16 import _select_modes

        modes = _select_modes()
        assert "adjacent_keyword" in modes
        assert "gap_exploit" in modes
        assert "trend_chase" in modes

    def test_adjacent_niche_every_3rd_run(self) -> None:
        from src.discovery.stage16 import _select_modes

        assert "adjacent_niche" in _select_modes(run_number=0)
        assert "adjacent_niche" in _select_modes(run_number=3)
        assert "adjacent_niche" in _select_modes(run_number=6)

    def test_adjacent_niche_not_on_non_3rd_run(self) -> None:
        from src.discovery.stage16 import _select_modes

        assert "adjacent_niche" not in _select_modes(run_number=1)
        assert "adjacent_niche" not in _select_modes(run_number=2)
        assert "adjacent_niche" not in _select_modes(run_number=4)

    def test_no_run_number_returns_base_only(self) -> None:
        from src.discovery.stage16 import _select_modes

        modes = _select_modes(run_number=None)
        assert "adjacent_niche" not in modes
        assert len(modes) == 3

    def test_config_override_filters_modes(self) -> None:
        from src.discovery.stage16 import _select_modes

        config = {"discovery": {"enabled_modes": ["adjacent_keyword", "gap_exploit"]}}
        modes = _select_modes(config=config)
        assert "trend_chase" not in modes
        assert modes == ["adjacent_keyword", "gap_exploit"]

    def test_empty_config_returns_defaults(self) -> None:
        from src.discovery.stage16 import _select_modes

        assert _select_modes(config={}) == ["adjacent_keyword", "gap_exploit", "trend_chase"]

    def test_returns_list_type(self) -> None:
        from src.discovery.stage16 import _select_modes

        result = _select_modes()
        assert isinstance(result, list)

    def test_select_modes_deterministic(self) -> None:
        from src.discovery.stage16 import _select_modes

        assert _select_modes(run_number=1) == _select_modes(run_number=1)
        assert all(isinstance(mode, str) for mode in _select_modes())

    @pytest.mark.parametrize("run_number", [None, 0, 1, 2, 3, 99])
    def test_modes_never_empty(self, run_number: int | None) -> None:
        from src.discovery.stage16 import _select_modes

        assert len(_select_modes(run_number=run_number)) > 0

    def test_no_duplicate_modes(self) -> None:
        from src.discovery.stage16 import _select_modes

        for run_number in [0, 1, 2, 3]:
            modes = _select_modes(run_number=run_number)
            assert len(modes) == len(set(modes))

    def test_adjacent_niche_included_on_run_0(self) -> None:
        from src.discovery.stage16 import _select_modes

        modes = _select_modes(run_number=0)
        assert "adjacent_niche" in modes
        assert len(modes) == 4

    def test_adjacent_niche_included_on_run_6(self) -> None:
        from src.discovery.stage16 import _select_modes

        assert "adjacent_niche" in _select_modes(run_number=6)


class TestBuildSeedData:
    def test_returns_required_keys(self) -> None:
        from src.discovery.stage16 import _build_seed_data

        db = _mock_db()
        with patch("src.discovery.stage16._resolve_niche_pk", return_value=1):
            result = _build_seed_data(
                "python_automation",
                db,
                ["adjacent_keyword", "gap_exploit", "trend_chase"],
            )
        assert set(result.keys()) == {
            "seed_keywords",
            "gap_signals",
            "trend_signals",
            "existing_kw_texts",
        }

    def test_db_error_returns_empty_lists(self) -> None:
        from src.discovery.stage16 import _build_seed_data

        db = _mock_db()
        with patch("src.discovery.stage16._resolve_niche_pk", side_effect=Exception("DB error")):
            result = _build_seed_data("python_automation", db, ["adjacent_keyword"])
        assert result["seed_keywords"] == []
        assert result["existing_kw_texts"] == []

    def test_missing_niche_returns_empty(self) -> None:
        from src.discovery.stage16 import _build_seed_data

        db = _mock_db()
        with patch("src.discovery.stage16._resolve_niche_pk", return_value=None):
            result = _build_seed_data("python_automation", db, ["adjacent_keyword"])
        assert result["seed_keywords"] == []
        assert result["gap_signals"] == []
        assert result["trend_signals"] == []

    def test_build_seed_data_with_rows(self) -> None:
        from src.discovery.stage16 import _build_seed_data

        db = MagicMock()
        keyword_rows = [SimpleNamespace(keyword="python automation"), SimpleNamespace(keyword="ai workflows")]
        gap_rows = [
            (
                SimpleNamespace(keyword="python automation"),
                SimpleNamespace(demand_score=0.9, competition_score=0.2, opportunity_score=0.8, score_components={}),
            )
        ]
        trend_rows = [
            (
                SimpleNamespace(keyword="ai workflows"),
                SimpleNamespace(trend_score=0.7, opportunity_score=0.8, score_components={"trend_velocity": 0.6}),
            )
        ]
        db.query.return_value.filter.return_value.limit.return_value.all.side_effect = [
            keyword_rows,
            gap_rows,
            trend_rows,
        ]
        db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.side_effect = [
            gap_rows,
            trend_rows,
        ]
        with patch("src.discovery.stage16._resolve_niche_pk", return_value=1):
            result = _build_seed_data("python_automation", db, ["gap_exploit", "trend_chase"])
        assert result["seed_keywords"][:2] == ["python automation", "ai workflows"]


class TestGenerateAllHypotheses:
    def test_returns_tuple(self) -> None:
        from src.discovery.stage16 import _generate_all_hypotheses

        seed = {"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []}
        result = _generate_all_hypotheses("python_automation", ["adjacent_keyword"], seed, 0.50)
        assert isinstance(result, tuple) and len(result) == 2

    def test_mode_failure_non_fatal(self) -> None:
        from src.discovery.stage16 import _generate_all_hypotheses

        seed = {"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []}
        with patch(
            "src.discovery.stage16.generate_adjacent_keyword_hypotheses",
            side_effect=Exception("mode error"),
        ):
            hypotheses, gated = _generate_all_hypotheses(
                "python_automation",
                ["adjacent_keyword"],
                seed,
                0.50,
            )
        assert isinstance(hypotheses, list)
        assert isinstance(gated, int)

    def test_unknown_mode_skipped(self) -> None:
        from src.discovery.stage16 import _generate_all_hypotheses

        seed = {"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []}
        hypotheses, gated = _generate_all_hypotheses("python_automation", ["unknown"], seed, 0.50)
        assert hypotheses == []
        assert gated == 0

    def test_generate_all_empty_modes(self) -> None:
        from src.discovery.stage16 import _generate_all_hypotheses

        seed = {"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []}
        hypotheses, gated = _generate_all_hypotheses("python_automation", [], seed, 0.50)
        assert hypotheses == []
        assert gated == 0

    def test_generate_all_returns_list_int(self) -> None:
        from src.discovery.stage16 import _generate_all_hypotheses

        seed = {"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []}
        hypotheses, gated = _generate_all_hypotheses("python_automation", ["adjacent_keyword"], seed, 0.50)
        assert isinstance(hypotheses, list)
        assert isinstance(gated, int)


class TestRunDiscoveryCycle:
    def test_returns_discovery_cycle_log(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        mock_log = MagicMock()
        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={"total_hypotheses": 0}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=mock_log),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            result = run_discovery_cycle(db, RUN_ID)
        assert result is mock_log
        db.commit.assert_called_once()

    def test_commit_called_once(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, RUN_ID)
        db.commit.assert_called_once()

    def test_generates_run_id_if_not_provided(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": "auto", "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, run_id=None)
        assert isinstance(log_kwargs.get("run_id"), str)
        assert str(log_kwargs["run_id"]).startswith("discovery-")

    def test_cycle_log_contains_modes(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, RUN_ID)
        modes = json.loads(str(log_kwargs.get("modes_run", "[]")))
        assert isinstance(modes, list) and len(modes) >= 3

    def test_cycle_log_hypotheses_accepted_matches_insert_result(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 5, "skipped": 2, "run_id": RUN_ID, "keyword_ids": [1, 2, 3, 4, 5]},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch(
                "src.discovery.stage16._generate_all_hypotheses",
                return_value=([MagicMock(accepted=True, specificity_score=0.72)] * 7, 0),
            ),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, RUN_ID)
        assert log_kwargs["hypotheses_accepted"] == 5

    def test_evaluate_results_failure_is_non_fatal(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        with (
            patch("src.discovery.stage16.evaluate_discovery_results", side_effect=Exception("DB error")),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, RUN_ID)

    def test_feedback_summary_failure_uses_fallback(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", side_effect=Exception("fail")),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, RUN_ID)
        stored = json.loads(str(log_kwargs["feedback_summary"]))
        assert "note" in stored or "total_hypotheses" in stored

    def test_cost_usd_is_zero(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, RUN_ID)
        assert log_kwargs["total_cost_usd"] == 0.0

    def test_run_cycle_calls_feedback_once(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        called: list[bool] = []
        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", side_effect=lambda session: called.append(True) or {}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": "r", "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, "r")
        assert len(called) == 1

    def test_hypotheses_generated_count_correct(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        hypotheses = [MagicMock(accepted=True, specificity_score=0.72) for _ in range(8)]
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 8, "skipped": 0, "run_id": "c", "keyword_ids": list(range(8))},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=(hypotheses, 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, "c")
        assert log_kwargs["hypotheses_generated"] == 8
        assert log_kwargs["hypotheses_accepted"] == 8

    def test_run_cycle_custom_config(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        config = {"discovery": {"min_hypothesis_confidence": 0.70, "max_hypotheses_per_run": 5}}
        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": "c", "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, "c", config=config)

    def test_run_discovery_cycle_returns_object(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        mock_log = MagicMock()
        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": "r", "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=mock_log),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            result = run_discovery_cycle(db, "r")
        assert result is mock_log

    def test_process_called_with_accepted_only(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        accepted = [MagicMock(accepted=True, specificity_score=0.72) for _ in range(3)]
        rejected = [MagicMock(accepted=False, specificity_score=0.30) for _ in range(5)]
        process_args: list[MagicMock] = []

        def process_capture(hypotheses: list[MagicMock], *_args: object, **_kwargs: object) -> dict[str, object]:
            process_args.extend(hypotheses)
            return {"inserted": len(hypotheses), "skipped": 0, "run_id": "filter-test", "keyword_ids": []}

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch("src.discovery.stage16.process_accepted_hypotheses", side_effect=process_capture),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=(accepted + rejected, 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, "filter-test")
        assert all(getattr(item, "accepted", False) for item in process_args)

    def test_feedback_summary_stored_in_log(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        feedback = {"total_hypotheses": 5, "hits": 3, "hit_rate_pct": 60.0}
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value=feedback),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                return_value={"inserted": 0, "skipped": 0, "run_id": "fb", "keyword_ids": []},
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, "fb")
        stored = json.loads(str(log_kwargs["feedback_summary"]))
        assert stored["total_hypotheses"] == 5

    def test_gated_count_reflects_low_confidence(self) -> None:
        from src.discovery.stage16 import run_discovery_cycle

        db = _mock_db()
        high = [MagicMock(accepted=True, specificity_score=0.80) for _ in range(3)]
        low = [MagicMock(accepted=True, specificity_score=0.20) for _ in range(5)]
        log_kwargs: dict[str, object] = {}

        def capture(**kwargs: object) -> MagicMock:
            log_kwargs.update(kwargs)
            return MagicMock()

        with (
            patch("src.discovery.stage16.evaluate_discovery_results"),
            patch("src.discovery.stage16.build_feedback_summary", return_value={}),
            patch(
                "src.discovery.stage16.process_accepted_hypotheses",
                side_effect=lambda hypotheses, run_id, db: {
                    "inserted": len(hypotheses),
                    "skipped": 0,
                    "run_id": run_id,
                    "keyword_ids": list(range(len(hypotheses))),
                },
            ),
            patch("src.discovery.stage16._build_seed_data", return_value={}),
            patch("src.discovery.stage16._generate_all_hypotheses", return_value=(high + low, 0)),
            patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
            patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
        ):
            run_discovery_cycle(db, "gated")
        assert log_kwargs["hypotheses_gated"] == 5


def test_stage16_no_circular() -> None:
    import src.discovery.stage16 as stage16

    assert stage16.run_discovery_cycle is not None


def test_s78_coexists_with_wave9() -> None:
    from src.discovery.stage16 import run_discovery_cycle
    from src.pricing import analyze_price_distribution, calculate_new_seller_pricing

    assert run_discovery_cycle is not None
    assert analyze_price_distribution is not None
    assert calculate_new_seller_pricing is not None


def test_complete_s78_integration_chain() -> None:
    from src.discovery.feedback import build_feedback_summary
    from src.discovery.integration import process_accepted_hypotheses
    from src.discovery.stage16 import DEFAULT_MIN_CONFIDENCE, _select_modes, run_discovery_cycle
    from src.models import DiscoveryCycleLog

    modes = _select_modes()
    assert len(modes) >= 3
    assert DEFAULT_MIN_CONFIDENCE == 0.50
    assert run_discovery_cycle is not None
    assert process_accepted_hypotheses is not None
    assert build_feedback_summary is not None
    assert DiscoveryCycleLog is not None


def test_file_contains_30_plus_tests() -> None:
    tree = ast.parse(open("tests/unit/test_discovery_stage16.py", encoding="utf-8").read())
    test_names = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    assert len(test_names) >= 30


def test_budget_cap_enforced() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    many_hypotheses = [MagicMock(accepted=True, specificity_score=0.72) for _ in range(20)]
    config = {"discovery": {"max_hypotheses_per_run": 15}}
    inserted_hypotheses: list[MagicMock] = []

    def mock_process(hypotheses: list[MagicMock], run_id: str, db_session: MagicMock, **kwargs: object) -> dict[str, object]:
        del db_session, kwargs
        inserted_hypotheses.extend(hypotheses)
        return {
            "inserted": len(hypotheses),
            "skipped": 0,
            "run_id": run_id,
            "keyword_ids": list(range(len(hypotheses))),
        }

    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch("src.discovery.stage16.process_accepted_hypotheses", side_effect=mock_process),
        patch("src.discovery.stage16._generate_all_hypotheses", return_value=(many_hypotheses, 0)),
        patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
    ):
        run_discovery_cycle(db, "cap-test", config)
    assert len(inserted_hypotheses) <= 15


def test_select_modes_run_3_has_adj_niche() -> None:
    from src.discovery.stage16 import _select_modes

    modes = _select_modes(run_number=3)
    assert "adjacent_niche" in modes
    assert "adjacent_keyword" in modes
    assert "gap_exploit" in modes
    assert "trend_chase" in modes
    assert len(modes) == 4


def test_select_modes_run_1_no_adj_niche() -> None:
    from src.discovery.stage16 import _select_modes

    modes = _select_modes(run_number=1)
    assert "adjacent_niche" not in modes
    assert len(modes) == 3


def test_all_below_confidence_gated() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    low_conf = [MagicMock(accepted=True, specificity_score=0.20) for _ in range(5)]
    config = {"discovery": {"min_hypothesis_confidence": 0.50}}
    log_kwargs: dict[str, object] = {}

    def capture(**kwargs: object) -> MagicMock:
        log_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 5, "run_id": "low", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", return_value=(low_conf, 0)),
        patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
    ):
        run_discovery_cycle(db, "low-conf", config)
    assert log_kwargs.get("hypotheses_accepted") == 0


def test_cycle_log_created_even_with_zero() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 0, "run_id": "zero", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
    ):
        with patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()):
            run_discovery_cycle(db, "zero")
    db.add.assert_called()
    db.commit.assert_called_once()


def test_multiple_niches_all_called() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    generate_calls: list[str] = []

    def mock_generate(
        niche_id: str | None = None,
        modes: list[str] | None = None,
        seed_data: dict[str, object] | None = None,
        min_conf: float | None = None,
        **kwargs: object,
    ) -> tuple[list[MagicMock], int]:
        del modes, seed_data, min_conf, kwargs
        generate_calls.append(niche_id)
        return [], 0

    fake_niches = {"niche_a": {}, "niche_b": {}, "niche_c": {}}
    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 0, "run_id": "multi", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", side_effect=mock_generate),
        patch(
            "src.discovery.stage16._build_seed_data",
            return_value={"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []},
        ),
        patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", fake_niches),
    ):
        run_discovery_cycle(db, "multi")
    assert set(generate_calls) == set(fake_niches.keys())


def test_feedback_summary_stored_as_json() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    feedback_data = {"total_hypotheses": 5, "hits": 3, "hit_rate_pct": 60.0}
    log_kwargs: dict[str, object] = {}

    def capture(**kwargs: object) -> MagicMock:
        log_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value=feedback_data),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 0, "run_id": "fb", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
        patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
    ):
        run_discovery_cycle(db, "fb")
    stored = json.loads(str(log_kwargs.get("feedback_summary", "{}")))
    assert stored.get("total_hypotheses") == 5
    assert stored.get("hit_rate_pct") == 60.0


def test_stage16_module_size() -> None:
    n = len(open("src/discovery/stage16.py", encoding="utf-8").readlines())
    assert 100 <= n <= 500


def test_complete_s78_smoke() -> None:
    from src.discovery.feedback import build_feedback_summary
    from src.discovery.integration import process_accepted_hypotheses
    from src.discovery.stage16 import DEFAULT_MAX_HYPOTHESES, DEFAULT_MIN_CONFIDENCE, _select_modes, run_discovery_cycle
    from src.models import DiscoveryCycleLog

    modes = _select_modes()
    assert len(modes) >= 3
    assert DEFAULT_MIN_CONFIDENCE == 0.50
    assert DEFAULT_MAX_HYPOTHESES == 15
    assert run_discovery_cycle is not None
    assert process_accepted_hypotheses is not None
    assert build_feedback_summary is not None
    assert DiscoveryCycleLog is not None


def test_mode_count_run_0() -> None:
    from src.discovery.stage16 import _select_modes

    modes = _select_modes(run_number=0)
    assert len(modes) == 4


def test_config_none_uses_defaults() -> None:
    from src.discovery.stage16 import _select_modes

    modes = _select_modes(config=None, run_number=1)
    assert len(modes) == 3


def test_stage16_coexists_with_s76() -> None:
    from src.discovery.feedback import GOLD_THRESHOLD, build_feedback_summary
    from src.discovery.stage16 import _select_modes, run_discovery_cycle

    assert GOLD_THRESHOLD == 85.0
    assert len(_select_modes()) >= 3
    assert run_discovery_cycle is not None
    assert build_feedback_summary is not None


def test_stage16_coexists_with_s77() -> None:
    from src.discovery.integration import insert_discovery_keyword, process_accepted_hypotheses
    from src.discovery.stage16 import run_discovery_cycle

    db = MagicMock()
    result = process_accepted_hypotheses([], "coexist-run", db)
    assert result["inserted"] == 0
    assert run_discovery_cycle is not None
    assert insert_discovery_keyword is not None


def test_wave9_coexists_with_s78() -> None:
    from src.discovery.stage16 import run_discovery_cycle
    from src.pricing import analyze_price_distribution, calculate_new_seller_pricing

    assert run_discovery_cycle is not None
    assert analyze_price_distribution is not None
    assert calculate_new_seller_pricing is not None


def test_select_modes_empty_enabled_list() -> None:
    from src.discovery.stage16 import _select_modes

    config = {"discovery": {"enabled_modes": []}}
    modes = _select_modes(config=config, run_number=1)
    assert isinstance(modes, list)


def test_generate_all_gap_exploit() -> None:
    from src.discovery.stage16 import _generate_all_hypotheses

    seed = {
        "seed_keywords": [],
        "existing_kw_texts": [],
        "gap_signals": [
            {
                "keyword": "test_kw",
                "demand_score": 0.80,
                "competition_score": 0.15,
                "opportunity_score": 0.88,
            }
        ],
        "trend_signals": [],
    }
    hypotheses, gated = _generate_all_hypotheses("python_automation", ["gap_exploit"], seed, 0.50)
    assert isinstance(hypotheses, list)
    assert isinstance(gated, int)


def test_generate_all_trend_chase() -> None:
    from src.discovery.stage16 import _generate_all_hypotheses

    seed = {
        "seed_keywords": [],
        "existing_kw_texts": [],
        "gap_signals": [],
        "trend_signals": [
            {
                "keyword": "ai_auto",
                "trend_score": 0.85,
                "trend_velocity": 0.72,
                "opportunity_score": 0.82,
            }
        ],
    }
    hypotheses, gated = _generate_all_hypotheses("python_automation", ["trend_chase"], seed, 0.50)
    assert isinstance(hypotheses, list)
    assert isinstance(gated, int)


def test_default_budget_config() -> None:
    from src.discovery.stage16 import DEFAULT_MAX_HYPOTHESES, DEFAULT_MIN_CONFIDENCE

    assert DEFAULT_MIN_CONFIDENCE == 0.50
    assert DEFAULT_MAX_HYPOTHESES == 15


def test_modes_run_valid_json() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    kw: dict[str, object] = {}

    def capture(**kwargs: object) -> MagicMock:
        kw.update(kwargs)
        return MagicMock()

    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 0, "run_id": "j", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
        patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
    ):
        run_discovery_cycle(db, "j")
    modes = json.loads(str(kw.get("modes_run", "[]")))
    assert isinstance(modes, list)
    assert len(modes) > 0


def test_constants_present() -> None:
    import src.discovery.stage16 as stage16

    assert hasattr(stage16, "DEFAULT_MIN_CONFIDENCE")
    assert hasattr(stage16, "DEFAULT_MAX_HYPOTHESES")
    assert stage16.DEFAULT_MIN_CONFIDENCE > 0.0
    assert stage16.DEFAULT_MAX_HYPOTHESES > 0


def test_cycle_at_is_datetime() -> None:
    from datetime import datetime
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    kw: dict[str, object] = {}

    def capture(**kwargs: object) -> MagicMock:
        kw.update(kwargs)
        return MagicMock()

    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 0, "run_id": "dt", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", return_value=([], 0)),
        patch("src.discovery.stage16.DiscoveryCycleLog", side_effect=capture),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", {"python_automation": {}}),
    ):
        run_discovery_cycle(db, "dt")
    assert isinstance(kw.get("cycle_at"), datetime)


def test_select_modes_run_9() -> None:
    from src.discovery.stage16 import _select_modes

    modes = _select_modes(run_number=9)
    assert "adjacent_niche" in modes
    assert len(modes) == 4


def test_select_modes_run_5() -> None:
    from src.discovery.stage16 import _select_modes

    modes = _select_modes(run_number=5)
    assert "adjacent_niche" not in modes
    assert len(modes) == 3


def test_generate_all_adj_niche_failure_nonfatal() -> None:
    from src.discovery.stage16 import _generate_all_hypotheses

    seed = {"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []}
    with patch(
        "src.discovery.stage16.generate_adjacent_niche_hypotheses",
        side_effect=Exception("adj_niche error"),
    ):
        hypotheses, gated = _generate_all_hypotheses("python_automation", ["adjacent_niche"], seed, 0.50)
    assert isinstance(hypotheses, list)
    assert isinstance(gated, int)


def test_run_all_niches_called() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    fake = {"a": {}, "b": {}, "c": {}}
    calls: list[str] = []

    def mock_gen(
        niche_id: str | None = None,
        modes: list[str] | None = None,
        seed_data: dict[str, object] | None = None,
        min_conf: float | None = None,
        **kwargs: object,
    ) -> tuple[list[MagicMock], int]:
        del modes, seed_data, min_conf, kwargs
        calls.append(niche_id)
        return [], 0

    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch(
            "src.discovery.stage16.process_accepted_hypotheses",
            return_value={"inserted": 0, "skipped": 0, "run_id": "all", "keyword_ids": []},
        ),
        patch("src.discovery.stage16._generate_all_hypotheses", side_effect=mock_gen),
        patch(
            "src.discovery.stage16._build_seed_data",
            return_value={"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []},
        ),
        patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", fake),
    ):
        run_discovery_cycle(db, "all")
    assert set(calls) == set(fake.keys())


def test_budget_cap_across_niches() -> None:
    from src.discovery.stage16 import run_discovery_cycle

    db = _mock_db()
    per_niche = [MagicMock(accepted=True, specificity_score=0.75) for _ in range(10)]
    inserted: list[MagicMock] = []

    def mock_gen(
        niche_id: str | None = None,
        modes: list[str] | None = None,
        seed_data: dict[str, object] | None = None,
        min_conf: float | None = None,
        **kwargs: object,
    ) -> tuple[list[MagicMock], int]:
        del niche_id, modes, seed_data, min_conf, kwargs
        return per_niche, 0

    def mock_process(hypotheses: list[MagicMock], run_id: str, db_session: MagicMock) -> dict[str, object]:
        del db_session
        inserted.extend(hypotheses)
        return {
            "inserted": len(hypotheses),
            "skipped": 0,
            "run_id": run_id,
            "keyword_ids": list(range(len(hypotheses))),
        }

    fake = {"a": {}, "b": {}, "c": {}}
    config = {"discovery": {"max_hypotheses_per_run": 15}}
    with (
        patch("src.discovery.stage16.evaluate_discovery_results"),
        patch("src.discovery.stage16.build_feedback_summary", return_value={}),
        patch("src.discovery.stage16.process_accepted_hypotheses", side_effect=mock_process),
        patch("src.discovery.stage16._generate_all_hypotheses", side_effect=mock_gen),
        patch(
            "src.discovery.stage16._build_seed_data",
            return_value={"seed_keywords": [], "gap_signals": [], "trend_signals": [], "existing_kw_texts": []},
        ),
        patch("src.discovery.stage16.DiscoveryCycleLog", return_value=MagicMock()),
        patch("src.discovery.stage16.NICHE_VALIDATION_CONFIG", fake),
    ):
        run_discovery_cycle(db, "cap3", config)
    assert len(inserted) <= 15


def test_stage16_module_docstring() -> None:
    tree = ast.parse(open("src/discovery/stage16.py", encoding="utf-8").read())
    doc = ast.get_docstring(tree)
    assert doc
    assert "discovery" in doc.lower()


def test_stage16_not_async() -> None:
    import re

    content = open("src/discovery/stage16.py", encoding="utf-8").read()
    async_fns = re.findall(r"async def (\\w+)", content)
    assert "run_discovery_cycle" not in async_fns


def test_wave10_complete_smoke() -> None:
    from src.discovery.contracts import HypothesisMode
    from src.discovery.feedback import GOLD_THRESHOLD, build_feedback_summary
    from src.discovery.hypothesis import (
        generate_adjacent_keyword_hypotheses,
        generate_gap_exploit_hypotheses,
        generate_trend_chase_hypotheses,
    )
    from src.discovery.integration import process_accepted_hypotheses
    from src.discovery.stage16 import _select_modes, run_discovery_cycle
    from src.models import DiscoveryCycleLog

    modes = sorted([e.value for e in HypothesisMode])
    assert modes == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]
    assert GOLD_THRESHOLD == 85.0
    assert run_discovery_cycle is not None
    assert _select_modes is not None
    assert process_accepted_hypotheses is not None
    assert build_feedback_summary is not None
    assert generate_adjacent_keyword_hypotheses is not None
    assert generate_gap_exploit_hypotheses is not None
    assert generate_trend_chase_hypotheses is not None
    assert DiscoveryCycleLog is not None
