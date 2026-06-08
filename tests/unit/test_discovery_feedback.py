"""Tests for S7.6 discovery scoring and feedback."""

from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
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
