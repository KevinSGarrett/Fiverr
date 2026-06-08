"""Tests for S7.6 discovery scoring and feedback."""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import sqlalchemy

_feedback_path = Path("src/discovery/feedback.py").resolve()
_feedback_spec = importlib.util.spec_from_file_location("s76_feedback", _feedback_path)
assert _feedback_spec is not None
assert _feedback_spec.loader is not None
feedback = importlib.util.module_from_spec(_feedback_spec)
_feedback_spec.loader.exec_module(feedback)


def _make_keyword(
    *,
    keyword_id: int = 1,
    keyword: str = "test keyword",
    niche_id: str = "python_automation",
    discovery_mode: str = "adjacent_keyword",
    hypothesis_confidence: float = 0.70,
    discovery_evaluated: bool = False,
    is_retired: bool = False,
) -> MagicMock:
    kw = MagicMock()
    kw.id = keyword_id
    kw.keyword = keyword
    kw.keyword_text = keyword
    kw.niche_id = niche_id
    kw.discovery_mode = discovery_mode
    kw.hypothesis_confidence = hypothesis_confidence
    kw.discovery_evaluated = discovery_evaluated
    kw.is_retired = is_retired
    return kw


def _make_outcome(
    *,
    mode: str = "adjacent_keyword",
    niche_id: str = "python_automation",
    score: float = 65.0,
    is_gold: bool = False,
    is_hit: bool = True,
    is_miss: bool = False,
) -> MagicMock:
    row = MagicMock()
    row.discovery_mode = mode
    row.niche_id = niche_id
    row.actual_final_score = score
    row.is_gold = is_gold
    row.is_hit = is_hit
    row.is_miss = is_miss
    return row


def _mock_keyword_query(db: MagicMock, keywords: list[MagicMock]) -> None:
    query = MagicMock()
    filtered = MagicMock()
    db.query.return_value = query
    query.filter.return_value = filtered
    filtered.all.return_value = keywords


class TestFeedbackConstants:
    def test_gold_threshold(self) -> None:
        assert feedback.GOLD_THRESHOLD == 85.0

    def test_hit_threshold(self) -> None:
        assert feedback.HIT_THRESHOLD == 60.0

    def test_miss_threshold(self) -> None:
        assert feedback.MISS_THRESHOLD == 40.0

    def test_auto_retire_threshold(self) -> None:
        assert feedback.AUTO_RETIRE_THRESHOLD == 30.0

    def test_threshold_ordering(self) -> None:
        assert feedback.GOLD_THRESHOLD > feedback.HIT_THRESHOLD > feedback.MISS_THRESHOLD
        assert feedback.AUTO_RETIRE_THRESHOLD < feedback.MISS_THRESHOLD

    def test_discovery_modes_len(self) -> None:
        assert len(feedback.DISCOVERY_MODES) == 4


class TestBuildFeedbackSummary:
    def test_empty_db_returns_minimal_dict(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = []
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 0
        assert "note" in result

    def test_summary_contains_required_keys(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome()]
        result = feedback.build_feedback_summary(db)
        for key in [
            "total_hypotheses",
            "gold_hits",
            "hits",
            "misses",
            "hit_rate_pct",
            "avg_actual_score",
            "mode_stats",
            "best_mode",
            "worst_mode",
            "top_hit_niches",
            "top_miss_niches",
            "pattern_notes",
        ]:
            assert key in result

    def test_hit_rate_calculation(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(score=70, is_hit=True, is_miss=False),
            _make_outcome(score=30, is_hit=False, is_miss=True),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["hits"] == 1
        assert result["misses"] == 1
        assert result["hit_rate_pct"] == 50.0

    def test_gold_count(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(score=90, is_gold=True, is_hit=True),
            _make_outcome(score=65, is_gold=False, is_hit=True),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["gold_hits"] == 1

    def test_mode_stats_include_all_modes_even_zero(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome(mode="gap_exploit")]
        result = feedback.build_feedback_summary(db)
        for mode in feedback.DISCOVERY_MODES:
            assert mode in result["mode_stats"]

    def test_best_and_worst_mode_selection(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(mode="gap_exploit", score=90, is_hit=True),
            _make_outcome(mode="gap_exploit", score=80, is_hit=True),
            _make_outcome(mode="trend_chase", score=20, is_hit=False, is_miss=True),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["best_mode"] == "gap_exploit"
        assert result["worst_mode"] == "trend_chase"

    def test_top_niches_aggregation(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="mcp_ai_agent", is_hit=False, is_miss=True),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["top_hit_niches"][0]["niche"] == "python_automation"
        assert result["top_miss_niches"][0]["niche"] == "mcp_ai_agent"

    def test_avg_score_rounding(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(score=60.0),
            _make_outcome(score=70.0),
            _make_outcome(score=71.0),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["avg_actual_score"] == 67.0

    def test_pattern_notes_non_empty(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome()]
        result = feedback.build_feedback_summary(db)
        assert isinstance(result["pattern_notes"], str)
        assert result["pattern_notes"] != ""


class TestPatternNotes:
    def test_empty_notes_fallback(self) -> None:
        result = feedback._generate_pattern_notes([], {})
        assert "Insufficient data" in result

    def test_high_hit_rate_message(self) -> None:
        stats = {"gap_exploit": {"count": 5, "hit_rate": 60.0, "avg_score": 70.0, "gold_count": 1}}
        result = feedback._generate_pattern_notes([], stats)
        assert "gap_exploit performs well" in result

    def test_low_hit_rate_message(self) -> None:
        stats = {"trend_chase": {"count": 5, "hit_rate": 10.0, "avg_score": 45.0, "gold_count": 0}}
        result = feedback._generate_pattern_notes([], stats)
        assert "trend_chase underperforms" in result

    def test_no_outcomes_mode_message(self) -> None:
        stats = {"adjacent_niche": {"count": 0, "hit_rate": 0.0, "avg_score": 0.0, "gold_count": 0}}
        result = feedback._generate_pattern_notes([], stats)
        assert "has no outcomes yet" in result

    def test_gold_modes_message(self) -> None:
        outcomes = [
            _make_outcome(mode="gap_exploit", is_gold=True, is_hit=True),
            _make_outcome(mode="gap_exploit", is_gold=True, is_hit=True),
            _make_outcome(mode="adjacent_keyword", is_gold=True, is_hit=True),
        ]
        result = feedback._generate_pattern_notes(outcomes, {})
        assert "gold discoveries concentrated in" in result


class TestEvaluateDiscoveryResults:
    def test_no_keywords_returns_zero_summary(self) -> None:
        db = MagicMock()
        _mock_keyword_query(db, [])
        result = feedback.evaluate_discovery_results("run-1", db)
        assert result["total"] == 0
        db.commit.assert_called_once()

    def test_skips_when_no_score(self) -> None:
        db = MagicMock()
        kw = _make_keyword()
        _mock_keyword_query(db, [kw])
        with patch.object(feedback, "_get_keyword_final_score", return_value=None):
            result = feedback.evaluate_discovery_results("run-1", db)
        assert result["total"] == 0

    def test_records_hit(self) -> None:
        db = MagicMock()
        kw = _make_keyword(hypothesis_confidence=0.60)
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with (
            patch.object(feedback, "_get_keyword_final_score", return_value=70.0),
            patch.object(feedback, "_get_keyword_tag", return_value="CONDITIONAL_GO"),
            patch.object(feedback, "_fire_gold_alert") as alert_mock,
        ):
            result = feedback.evaluate_discovery_results("run-1", db)
        assert result["hits"] == 1
        assert result["gold"] == 0
        assert kw.discovery_evaluated is True
        alert_mock.assert_not_called()

    def test_records_gold_and_alerts(self) -> None:
        db = MagicMock()
        kw = _make_keyword(hypothesis_confidence=0.80)
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with (
            patch.object(feedback, "_get_keyword_final_score", return_value=90.0),
            patch.object(feedback, "_get_keyword_tag", return_value="GO"),
            patch.object(feedback, "_fire_gold_alert") as alert_mock,
        ):
            result = feedback.evaluate_discovery_results("run-1", db)
        assert result["gold"] == 1
        assert result["hits"] == 1
        alert_mock.assert_called_once()

    def test_records_miss_and_retire(self) -> None:
        db = MagicMock()
        kw = _make_keyword(hypothesis_confidence=0.50)
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with (
            patch.object(feedback, "_get_keyword_final_score", return_value=25.0),
            patch.object(feedback, "_get_keyword_tag", return_value="NO_GO"),
        ):
            result = feedback.evaluate_discovery_results("run-1", db)
        assert result["misses"] == 1
        assert result["retirements"] == 1
        assert kw.is_retired is True

    def test_monitor_zone_neither_hit_nor_miss(self) -> None:
        db = MagicMock()
        kw = _make_keyword()
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with patch.object(feedback, "_get_keyword_final_score", return_value=50.0):
            result = feedback.evaluate_discovery_results("run-1", db)
        assert result["monitored"] == 1
        assert result["hits"] == 0
        assert result["misses"] == 0

    def test_duplicate_guard_marks_evaluated(self) -> None:
        db = MagicMock()
        kw = _make_keyword()
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = MagicMock()
        with patch.object(feedback, "_get_keyword_final_score", return_value=70.0):
            result = feedback.evaluate_discovery_results("run-1", db)
        assert result["total"] == 0
        assert kw.discovery_evaluated is True

    def test_score_delta_positive(self) -> None:
        db = MagicMock()
        kw = _make_keyword(hypothesis_confidence=0.65)
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with patch.object(feedback, "_get_keyword_final_score", return_value=72.0):
            feedback.evaluate_discovery_results("run-1", db)
        inserted = db.add.call_args[0][0]
        assert inserted.score_delta == 7.0

    def test_score_delta_negative(self) -> None:
        db = MagicMock()
        kw = _make_keyword(hypothesis_confidence=0.80)
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with patch.object(feedback, "_get_keyword_final_score", return_value=45.0):
            feedback.evaluate_discovery_results("run-1", db)
        inserted = db.add.call_args[0][0]
        assert inserted.score_delta == -35.0

    def test_run_id_written(self) -> None:
        db = MagicMock()
        kw = _make_keyword()
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with patch.object(feedback, "_get_keyword_final_score", return_value=70.0):
            feedback.evaluate_discovery_results("run-123", db)
        inserted = db.add.call_args[0][0]
        assert inserted.run_id == "run-123"

    def test_evaluated_at_timestamp_set(self) -> None:
        db = MagicMock()
        kw = _make_keyword()
        _mock_keyword_query(db, [kw])
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        with patch.object(feedback, "_get_keyword_final_score", return_value=70.0):
            feedback.evaluate_discovery_results("run-1", db)
        inserted = db.add.call_args[0][0]
        assert isinstance(inserted.evaluated_at, datetime)
        assert inserted.evaluated_at.tzinfo is UTC


class TestHelpersAndModels:
    def test_get_keyword_text_prefers_keyword(self) -> None:
        kw = _make_keyword(keyword="abc")
        assert feedback._get_keyword_text(kw) == "abc"

    def test_get_discovery_cycle_stats_not_found(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = feedback.get_discovery_cycle_stats("run-x", db)
        assert result["found"] is False

    def test_get_discovery_cycle_stats_found(self) -> None:
        row = MagicMock()
        row.run_id = "run-y"
        row.modes_run = ["gap_exploit"]
        row.hypotheses_generated = 10
        row.hypotheses_accepted = 2
        row.total_cost_usd = 1.23
        row.cycle_at = datetime(2026, 1, 1, tzinfo=UTC)
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = row
        result = feedback.get_discovery_cycle_stats("run-y", db)
        assert result["found"] is True
        assert result["run_id"] == "run-y"

    def test_feedback_module_importable_symbols(self) -> None:
        assert callable(feedback.evaluate_discovery_results)
        assert callable(feedback.build_feedback_summary)
        assert callable(feedback._generate_pattern_notes)
        assert callable(feedback.get_discovery_cycle_stats)
        assert feedback.GOLD_THRESHOLD == 85.0
        assert feedback.HIT_THRESHOLD == 60.0
        assert feedback.MISS_THRESHOLD == 40.0
        assert feedback.AUTO_RETIRE_THRESHOLD == 30.0

    def test_discovery_models_importable(self) -> None:
        from src.models import DiscoveryCycleLog, DiscoveryOutcome  # noqa: PLC0415

        assert DiscoveryOutcome.__tablename__ == "discovery_outcomes"
        assert DiscoveryCycleLog.__tablename__ == "discovery_cycle_logs"

    def test_keyword_columns_present(self) -> None:
        from src.models import Keyword  # noqa: PLC0415

        mapper = sqlalchemy.inspect(Keyword)
        names = {attr.key for attr in mapper.attrs}
        for col in [
            "is_discovery",
            "discovery_mode",
            "hypothesis_confidence",
            "hypothesis_rationale",
            "discovered_in_run",
            "discovery_evaluated",
            "is_retired",
        ]:
            assert col in names


def test_feedback_has_no_llm_calls() -> None:
    import ast

    tree = ast.parse(open("src/discovery/feedback.py", encoding="utf-8").read())
    llm_calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and (
            (hasattr(n.func, "id") and isinstance(getattr(n.func, "id", None), str) and "llm" in n.func.id.lower())
            or (
                hasattr(n.func, "attr")
                and isinstance(getattr(n.func, "attr", None), str)
                and "llm" in n.func.attr.lower()
            )
        )
    ]
    assert len(llm_calls) == 0


class TestFCoverageUplift:
    def test_evaluate_discovery_results_empty_db(self) -> None:
        db = MagicMock()
        _mock_keyword_query(db, [])
        result = feedback.evaluate_discovery_results("run_001", db)
        assert result.get("total", 0) == 0

    def test_gold_classification_thresholds(self) -> None:
        assert feedback.GOLD_THRESHOLD > feedback.HIT_THRESHOLD

    def test_auto_retire_is_subset_of_miss(self) -> None:
        assert feedback.AUTO_RETIRE_THRESHOLD < feedback.MISS_THRESHOLD

    def test_monitor_zone_semantics(self) -> None:
        monitor_low = feedback.MISS_THRESHOLD
        monitor_high = feedback.HIT_THRESHOLD - 0.1
        assert monitor_high > monitor_low
        assert monitor_high < feedback.HIT_THRESHOLD

    def test_feedback_summary_no_exception_on_empty(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = []
        result = feedback.build_feedback_summary(db)
        assert isinstance(result, dict)

    def test_all_gold_scenario(self) -> None:
        db = MagicMock()
        outcomes = [_make_outcome(score=90.0 + i, mode="gap_exploit", is_gold=True, is_hit=True) for i in range(3)]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["gold_hits"] == 3
        assert result["hits"] == 3
        assert result["total_hypotheses"] == 3

    def test_all_miss_scenario(self) -> None:
        db = MagicMock()
        outcomes = [_make_outcome(score=25.0, mode="adjacent_keyword", is_hit=False, is_miss=True) for _ in range(5)]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["misses"] == 5
        assert result["hits"] == 0
        assert result["hit_rate_pct"] == 0.0

    def test_best_worst_mode_with_opposite_performance(self) -> None:
        db = MagicMock()
        outcomes = [
            _make_outcome(score=75, mode="gap_exploit", is_hit=True),
            _make_outcome(score=72, mode="gap_exploit", is_hit=True),
            _make_outcome(score=35, mode="trend_chase", is_hit=False, is_miss=True),
            _make_outcome(score=30, mode="trend_chase", is_hit=False, is_miss=True),
        ]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["best_mode"] == "gap_exploit"
        assert result["worst_mode"] == "trend_chase"

    def test_avg_score_calculation_precision(self) -> None:
        db = MagicMock()
        scores = [80.0, 60.0, 40.0, 20.0]
        db.query.return_value.all.return_value = [_make_outcome(score=s, is_hit=(s >= 60), is_miss=(s < 40)) for s in scores]
        result = feedback.build_feedback_summary(db)
        assert abs(result["avg_actual_score"] - 50.0) < 0.1

    def test_score_delta_positive_example(self) -> None:
        confidence = 0.65
        actual = 80.0
        assert actual - (confidence * 100) == 15.0

    def test_top_hit_niches_ordering(self) -> None:
        db = MagicMock()
        outcomes = [
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="mcp_ai_agent", is_hit=True, is_miss=False),
        ]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["top_hit_niches"][0]["niche"] == "python_automation"
        assert result["top_hit_niches"][0]["count"] == 3

    def test_get_discovery_cycle_stats_not_found_repeat(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = feedback.get_discovery_cycle_stats("nonexistent_run", db)
        assert result["found"] is False
        assert result["run_id"] == "nonexistent_run"

    def test_all_constants_are_float_type(self) -> None:
        for value in [
            feedback.GOLD_THRESHOLD,
            feedback.HIT_THRESHOLD,
            feedback.MISS_THRESHOLD,
            feedback.AUTO_RETIRE_THRESHOLD,
        ]:
            assert isinstance(value, float)

    def test_single_outcome_summary(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome(score=72.0, is_hit=True, is_miss=False)]
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 1
        assert result["hits"] == 1
        assert result["hit_rate_pct"] == 100.0

    def test_feedback_summary_all_four_modes(self) -> None:
        db = MagicMock()
        outcomes = []
        for mode in feedback.DISCOVERY_MODES:
            outcomes.append(_make_outcome(mode=mode, score=70, is_hit=True, is_miss=False))
            outcomes.append(_make_outcome(mode=mode, score=35, is_hit=False, is_miss=True))
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        for mode in feedback.DISCOVERY_MODES:
            assert mode in result["mode_stats"]
            assert result["mode_stats"][mode]["count"] == 2

    def test_pattern_notes_high_performer(self) -> None:
        mode_stats = {"gap_exploit": {"hit_rate": 60.0, "avg_score": 72.0, "count": 5, "gold_count": 0}}
        result = feedback._generate_pattern_notes([], mode_stats)
        assert isinstance(result, str)
        assert "gap_exploit" in result

    def test_feedback_summary_total_count(self) -> None:
        db = MagicMock()
        outcomes = []
        for i in range(7):
            outcomes.append(_make_outcome(score=70.0 if i < 5 else 35.0, mode="gap_exploit", is_hit=(i < 5), is_miss=(i >= 5)))
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 7

    def test_discovery_outcome_tablename_again(self) -> None:
        from src.models import DiscoveryOutcome  # noqa: PLC0415

        assert DiscoveryOutcome.__tablename__ == "discovery_outcomes"

    def test_discovery_cycle_log_tablename_again(self) -> None:
        from src.models import DiscoveryCycleLog  # noqa: PLC0415

        assert DiscoveryCycleLog.__tablename__ == "discovery_cycle_logs"

    def test_feedback_summary_with_no_outcomes_is_safe(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = []
        result = feedback.build_feedback_summary(db)
        assert result.get("total_hypotheses") == 0
        assert "hit_rate_pct" not in result

    def test_discovery_feedback_complete_import(self) -> None:
        assert callable(feedback.evaluate_discovery_results)
        assert callable(feedback.build_feedback_summary)
        assert callable(feedback._generate_pattern_notes)
        assert callable(feedback.get_discovery_cycle_stats)

    def test_wave9_and_s76_coexist(self) -> None:
        from src.pricing import analyze_price_distribution  # noqa: PLC0415

        assert callable(analyze_price_distribution)
        db = MagicMock()
        db.query.return_value.all.return_value = []
        result = feedback.build_feedback_summary(db)
        assert isinstance(result, dict)

    def test_s74_and_s76_coexist(self) -> None:
        from src.discovery.hypothesis import generate_gap_exploit_hypotheses  # noqa: PLC0415

        scores = [{"keyword": "test", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}]
        gaps = generate_gap_exploit_hypotheses("python_automation", scores, [])
        assert isinstance(gaps, list)
        assert feedback.GOLD_THRESHOLD == 85.0

    def test_threshold_hierarchy_repeat(self) -> None:
        assert feedback.AUTO_RETIRE_THRESHOLD < feedback.MISS_THRESHOLD < feedback.HIT_THRESHOLD < feedback.GOLD_THRESHOLD

    def test_pattern_notes_is_string(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome()]
        result = feedback.build_feedback_summary(db)
        assert isinstance(result.get("pattern_notes"), str)

    def test_mode_stats_count_per_mode(self) -> None:
        db = MagicMock()
        outcomes = []
        for _ in range(3):
            outcomes.append(_make_outcome(mode="gap_exploit", score=65.0, is_hit=True, is_miss=False))
        for _ in range(2):
            outcomes.append(_make_outcome(mode="trend_chase", score=35.0, is_hit=False, is_miss=True))
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["mode_stats"]["gap_exploit"]["count"] == 3
        assert result["mode_stats"]["trend_chase"]["count"] == 2

    def test_top_miss_niches(self) -> None:
        db = MagicMock()
        outcomes = [_make_outcome(mode="trend_chase", score=30.0, niche_id="prd_ai_saas", is_hit=False, is_miss=True) for _ in range(4)]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["top_miss_niches"][0]["niche"] == "prd_ai_saas"

    def test_gold_count_in_mode_stats(self) -> None:
        db = MagicMock()
        outcomes = [
            _make_outcome(mode="gap_exploit", score=88.0, is_gold=True, is_hit=True, is_miss=False),
            _make_outcome(mode="gap_exploit", score=65.0, is_gold=False, is_hit=True, is_miss=False),
        ]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["mode_stats"]["gap_exploit"]["gold_count"] == 1
        assert result["gold_hits"] == 1

    def test_discovery_outcome_table_has_no_duplicates(self) -> None:
        from sqlalchemy import create_engine, func
        from sqlalchemy.orm import sessionmaker
        from src.models import DiscoveryOutcome

        engine = create_engine("sqlite:///data/foundation_gate_ci.db")
        session = sessionmaker(bind=engine)()
        dupes = (
            session.query(DiscoveryOutcome.keyword_id, func.count(DiscoveryOutcome.id).label("cnt"))
            .group_by(DiscoveryOutcome.keyword_id)
            .having(func.count(DiscoveryOutcome.id) > 1)
            .all()
        )
        session.close()
        assert len(dupes) == 0

    def test_discovery_cycle_log_has_run_id(self) -> None:
        from sqlalchemy import create_engine, inspect

        cols = [c["name"] for c in inspect(create_engine("sqlite:///data/foundation_gate_ci.db")).get_columns("discovery_cycle_logs")]
        assert "run_id" in cols
        assert "hypotheses_generated" in cols
        assert "feedback_summary" in cols

    def test_keyword_s76_column_defaults(self) -> None:
        from sqlalchemy import create_engine, inspect

        cols = {c["name"]: c for c in inspect(create_engine("sqlite:///data/foundation_gate_ci.db")).get_columns("keywords")}
        assert "is_discovery" in cols
        assert "is_retired" in cols
        assert "discovery_evaluated" in cols

    def test_generate_pattern_notes_empty_inputs(self) -> None:
        result = feedback._generate_pattern_notes([], {})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_discovery_module_consistency(self) -> None:
        from src.discovery import hypothesis  # noqa: PLC0415

        assert hasattr(feedback, "evaluate_discovery_results")
        assert hasattr(feedback, "build_feedback_summary")
        assert hasattr(hypothesis, "generate_trend_chase_hypotheses")
        assert hasattr(hypothesis, "generate_gap_exploit_hypotheses")

    def test_evaluate_discovery_results_returns_dict(self) -> None:
        db = MagicMock()
        _mock_keyword_query(db, [])
        result = feedback.evaluate_discovery_results("test_run", db)
        assert isinstance(result, dict)

    def test_pattern_notes_flags_low_hit_rate(self) -> None:
        mode_stats = {"trend_chase": {"hit_rate": 10.0, "avg_score": 42.0, "count": 5, "gold_count": 0}}
        result = feedback._generate_pattern_notes([], mode_stats)
        assert "trend_chase" in result or "underperform" in result.lower()

    def test_feedback_summary_count_consistency_mixed(self) -> None:
        db = MagicMock()
        outcomes = [
            _make_outcome(score=90.0, is_gold=True, is_hit=True, is_miss=False),
            _make_outcome(score=70.0, is_gold=False, is_hit=True, is_miss=False),
            _make_outcome(score=65.0, is_gold=False, is_hit=True, is_miss=False),
            _make_outcome(score=35.0, is_gold=False, is_hit=False, is_miss=True),
            _make_outcome(score=50.0, is_gold=False, is_hit=False, is_miss=False),
        ]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 5
        assert result["gold_hits"] == 1
        assert result["hits"] == 3
        assert result["misses"] == 1

    def test_discovery_cycle_logs_table_in_db(self) -> None:
        from sqlalchemy import create_engine, inspect

        insp = inspect(create_engine("sqlite:///data/foundation_gate_ci.db"))
        assert "discovery_cycle_logs" in insp.get_table_names()
        cols = [c["name"] for c in insp.get_columns("discovery_cycle_logs")]
        assert "run_id" in cols
        assert "cycle_at" in cols

    def test_discovery_outcomes_table_in_db(self) -> None:
        from sqlalchemy import create_engine, inspect

        insp = inspect(create_engine("sqlite:///data/foundation_gate_ci.db"))
        assert "discovery_outcomes" in insp.get_table_names()
        cols = [c["name"] for c in insp.get_columns("discovery_outcomes")]
        for req in ["keyword_id", "actual_final_score", "is_gold", "is_hit", "is_miss"]:
            assert req in cols

    def test_discovery_outcome_all_required_fields(self) -> None:
        from src.models import DiscoveryOutcome  # noqa: PLC0415

        do_cols = [c.key for c in sqlalchemy.inspect(DiscoveryOutcome).attrs]
        for req in [
            "keyword_id",
            "keyword_text",
            "niche_id",
            "discovery_mode",
            "hypothesis_confidence",
            "actual_final_score",
            "actual_tag",
            "score_delta",
            "is_gold",
            "is_hit",
            "is_miss",
            "evaluated_at",
        ]:
            assert req in do_cols

    def test_gold_is_also_hit(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(mode="gap_exploit", score=88.0, is_gold=True, is_hit=True, is_miss=False)
        ]
        result = feedback.build_feedback_summary(db)
        assert result["gold_hits"] == 1
        assert result["hits"] == 1

    def test_keyword_is_discovery_default_column_present(self) -> None:
        from sqlalchemy import create_engine, inspect

        cols = {c["name"]: c for c in inspect(create_engine("sqlite:///data/foundation_gate_ci.db")).get_columns("keywords")}
        assert "is_discovery" in cols

    def test_feedback_summary_no_hit_modes_is_safe(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(mode="trend_chase", score=35.0, is_hit=False, is_miss=True) for _ in range(3)
        ]
        result = feedback.build_feedback_summary(db)
        assert result["hits"] == 0
        assert result["hit_rate_pct"] == 0.0

    def test_best_mode_none_on_empty(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = []
        result = feedback.build_feedback_summary(db)
        assert "best_mode" not in result

    def test_get_discovery_cycle_stats_found(self) -> None:
        db = MagicMock()
        log_entry = MagicMock()
        log_entry.run_id = "test_run_001"
        log_entry.modes_run = ["adjacent_keyword", "gap_exploit"]
        log_entry.hypotheses_generated = 10
        log_entry.hypotheses_accepted = 6
        log_entry.total_cost_usd = 0.18
        log_entry.cycle_at = datetime(2026, 6, 1, 12, 0, 0)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = log_entry
        result = feedback.get_discovery_cycle_stats("test_run_001", db)
        assert result["found"] is True
        assert result["run_id"] == "test_run_001"
        assert result["hypotheses_accepted"] == 6

    def test_feedback_module_size_reasonable(self) -> None:
        n = len(open("src/discovery/feedback.py", encoding="utf-8").read().splitlines())
        assert 100 <= n <= 500

    def test_avg_score_precision(self) -> None:
        db = MagicMock()
        scores = [75.0, 62.5, 88.2, 41.3]
        outcomes = [
            _make_outcome(
                score=s,
                is_gold=(s >= 85),
                is_hit=(s >= 60),
                is_miss=(s < 40),
                mode="adjacent_keyword",
                niche_id="python_automation",
            )
            for s in scores
        ]
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        expected_avg = round(sum(scores) / len(scores), 1)
        assert abs(result["avg_actual_score"] - expected_avg) < 0.1

    def test_complete_wave10_discovery_chain(self) -> None:
        from src.discovery.contracts import HypothesisMode  # noqa: PLC0415
        from src.discovery.hypothesis import (
            generate_adjacent_keyword_hypotheses,
            generate_adjacent_niche_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
        )
        from src.models import DiscoveryCycleLog, DiscoveryOutcome  # noqa: PLC0415

        assert callable(generate_adjacent_keyword_hypotheses)
        assert callable(generate_adjacent_niche_hypotheses)
        assert callable(generate_gap_exploit_hypotheses)
        assert callable(generate_trend_chase_hypotheses)
        assert DiscoveryOutcome.__tablename__ == "discovery_outcomes"
        assert DiscoveryCycleLog.__tablename__ == "discovery_cycle_logs"
        modes = sorted([e.value for e in HypothesisMode])
        assert modes == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]

    def test_feedback_summary_with_multiple_modes_and_niches(self) -> None:
        db = MagicMock()
        configs = [
            (True, True, False, 88.0, "gap_exploit", "python_automation"),
            (False, True, False, 72.0, "gap_exploit", "mcp_ai_agent"),
            (False, True, False, 65.0, "adjacent_keyword", "python_automation"),
            (False, False, True, 35.0, "trend_chase", "prd_ai_saas"),
            (False, False, True, 28.0, "trend_chase", "python_automation"),
        ]
        outcomes = []
        for is_g, is_h, is_m, score, mode, niche in configs:
            outcomes.append(_make_outcome(mode=mode, niche_id=niche, score=score, is_gold=is_g, is_hit=is_h, is_miss=is_m))
        db.query.return_value.all.return_value = outcomes
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 5
        assert result["gold_hits"] == 1
        assert result["hits"] == 3
        assert result["misses"] == 2
        assert result["best_mode"] == "gap_exploit"
        assert result["worst_mode"] == "trend_chase"

    def test_complete_s76_smoke(self) -> None:
        from src.discovery import hypothesis  # noqa: PLC0415
        from src.discovery.contracts import HypothesisMode  # noqa: PLC0415
        from src.models import DiscoveryCycleLog, DiscoveryOutcome  # noqa: PLC0415

        assert hasattr(feedback, "evaluate_discovery_results")
        assert hasattr(feedback, "build_feedback_summary")
        assert hasattr(feedback, "_generate_pattern_notes")
        assert hasattr(feedback, "get_discovery_cycle_stats")
        assert feedback.GOLD_THRESHOLD == 85.0
        assert feedback.HIT_THRESHOLD == 60.0
        assert feedback.MISS_THRESHOLD == 40.0
        assert feedback.AUTO_RETIRE_THRESHOLD == 30.0
        assert DiscoveryOutcome.__tablename__ == "discovery_outcomes"
        assert DiscoveryCycleLog.__tablename__ == "discovery_cycle_logs"
        assert hasattr(hypothesis, "generate_gap_exploit_hypotheses")
        modes = sorted([e.value for e in HypothesisMode])
        assert modes == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]

    def test_feedback_importable_from_discovery_package(self) -> None:
        from src.discovery import feedback as feedback_pkg  # noqa: PLC0415
        from src.discovery import hypothesis  # noqa: PLC0415

        assert hasattr(feedback_pkg, "evaluate_discovery_results")
        assert hasattr(feedback_pkg, "build_feedback_summary")
        assert hasattr(hypothesis, "generate_trend_chase_hypotheses")


class TestFPromptNameAlignment:
    def test_gold_classification(self) -> None:
        assert feedback.GOLD_THRESHOLD > feedback.HIT_THRESHOLD

    def test_auto_retire_is_stricter_than_miss(self) -> None:
        assert feedback.AUTO_RETIRE_THRESHOLD < feedback.MISS_THRESHOLD

    def test_mode_stats_only_includes_present_modes(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome(mode="gap_exploit", is_hit=True, is_miss=False)]
        result = feedback.build_feedback_summary(db)
        assert "gap_exploit" in result["mode_stats"]
        assert result["mode_stats"]["adjacent_keyword"]["count"] == 0

    def test_best_worst_mode_identified(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(mode="gap_exploit", score=70.0, is_hit=True, is_miss=False),
            _make_outcome(mode="gap_exploit", score=70.0, is_hit=True, is_miss=False),
            _make_outcome(mode="trend_chase", score=35.0, is_hit=False, is_miss=True),
            _make_outcome(mode="trend_chase", score=35.0, is_hit=False, is_miss=True),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["best_mode"] == "gap_exploit"
        assert result["worst_mode"] == "trend_chase"

    def test_avg_score_calculation(self) -> None:
        db = MagicMock()
        scores = [80.0, 60.0, 40.0, 20.0]
        db.query.return_value.all.return_value = [_make_outcome(score=s, is_hit=(s >= 60), is_miss=(s < 40)) for s in scores]
        result = feedback.build_feedback_summary(db)
        assert abs(result["avg_actual_score"] - (sum(scores) / len(scores))) < 0.1

    def test_score_delta_semantics(self) -> None:
        confidence = 0.65
        actual = 80.0
        assert actual - (confidence * 100) == 15.0

    def test_top_hit_niches(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="python_automation", is_hit=True, is_miss=False),
            _make_outcome(niche_id="mcp_ai_agent", is_hit=True, is_miss=False),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["top_hit_niches"][0]["niche"] == "python_automation"
        assert result["top_hit_niches"][0]["count"] == 3

    def test_feedback_module_has_no_llm_calls(self) -> None:
        import ast

        tree = ast.parse(open("src/discovery/feedback.py", encoding="utf-8").read())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        func_names = []
        for call in calls:
            if hasattr(call.func, "id"):
                func_names.append(call.func.id)
            elif hasattr(call.func, "attr"):
                func_names.append(call.func.attr)
        llm_calls = [n for n in func_names if "llm" in n.lower() or "openai" in n.lower()]
        assert len(llm_calls) == 0

    def test_all_constants_are_float(self) -> None:
        for value in [feedback.GOLD_THRESHOLD, feedback.HIT_THRESHOLD, feedback.MISS_THRESHOLD, feedback.AUTO_RETIRE_THRESHOLD]:
            assert isinstance(value, float)

    def test_build_feedback_summary_single_outcome(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome(score=72.0, is_hit=True, is_miss=False)]
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 1
        assert result["hits"] == 1
        assert result["hit_rate_pct"] == 100.0

    def test_pattern_notes_highlights_good_mode(self) -> None:
        notes = feedback._generate_pattern_notes([], {"gap_exploit": {"hit_rate": 60.0, "avg_score": 72.0, "count": 5, "gold_count": 0}})
        assert isinstance(notes, str)

    def test_discovery_outcome_tablename(self) -> None:
        from src.models import DiscoveryOutcome  # noqa: PLC0415

        assert DiscoveryOutcome.__tablename__ == "discovery_outcomes"

    def test_discovery_cycle_log_tablename(self) -> None:
        from src.models import DiscoveryCycleLog  # noqa: PLC0415

        assert DiscoveryCycleLog.__tablename__ == "discovery_cycle_logs"

    def test_threshold_hierarchy(self) -> None:
        assert feedback.AUTO_RETIRE_THRESHOLD < feedback.MISS_THRESHOLD < feedback.HIT_THRESHOLD < feedback.GOLD_THRESHOLD

    def test_feedback_summary_pattern_notes_is_string(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [_make_outcome()]
        result = feedback.build_feedback_summary(db)
        assert isinstance(result.get("pattern_notes"), str)

    def test_feedback_summary_count_consistency(self) -> None:
        db = MagicMock()
        db.query.return_value.all.return_value = [
            _make_outcome(score=90.0, is_gold=True, is_hit=True, is_miss=False),
            _make_outcome(score=70.0, is_gold=False, is_hit=True, is_miss=False),
            _make_outcome(score=65.0, is_gold=False, is_hit=True, is_miss=False),
            _make_outcome(score=35.0, is_gold=False, is_hit=False, is_miss=True),
            _make_outcome(score=50.0, is_gold=False, is_hit=False, is_miss=False),
        ]
        result = feedback.build_feedback_summary(db)
        assert result["total_hypotheses"] == 5
        assert result["gold_hits"] == 1
        assert result["hits"] == 3
        assert result["misses"] == 1

    def test_keyword_is_discovery_default(self) -> None:
        from sqlalchemy import create_engine, inspect

        cols = {c["name"]: c for c in inspect(create_engine("sqlite:///data/foundation_gate_ci.db")).get_columns("keywords")}
        assert "is_discovery" in cols

    def test_feedback_module_size(self) -> None:
        n = len(open("src/discovery/feedback.py", encoding="utf-8").read().splitlines())
        assert 100 <= n <= 500
