"""LLM wiring tests for feature-flagged scoring calculators."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from src.llm import LLMCache, LLMClient
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.demand import DemandScoreCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


class FakeScoringDB:
    def __init__(
        self,
        *,
        intent_inputs: dict[int, dict[str, Any]] | None = None,
        saturation_inputs: dict[int, dict[str, Any]] | None = None,
        weakness_inputs: dict[int, dict[str, Any]] | None = None,
        trend_inputs: dict[int, dict[str, Any]] | None = None,
        demand_inputs: dict[int, dict[str, Any]] | None = None,
        competition_inputs: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self._intent_inputs = intent_inputs or {}
        self._saturation_inputs = saturation_inputs or {}
        self._weakness_inputs = weakness_inputs or {}
        self._trend_inputs = trend_inputs or {}
        self._demand_inputs = demand_inputs or {}
        self._competition_inputs = competition_inputs or {}

    def get_intent_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._intent_inputs.get(keyword_id, {})

    def get_saturation_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._saturation_inputs.get(keyword_id, {})

    def get_weakness_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._weakness_inputs.get(keyword_id, {})

    def get_trend_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._trend_inputs.get(keyword_id, {})

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._demand_inputs.get(keyword_id, {})

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._competition_inputs.get(keyword_id, {})


def _base_intent_inputs() -> dict[str, Any]:
    return {
        "keyword": "hire python automation expert",
        "commercial_modifier_score": 0.8,
        "avg_review_count_top10": 220,
        "llm_buyer_intent_classification": None,
        "reddit_demand_intent_score": 7.1,
    }


def _base_saturation_inputs() -> dict[str, Any]:
    return {
        "keyword": "python automation",
        "total_gig_count": 5600,
        "title_duplication_rate": 0.55,
        "price_compression_signal": 0.62,
        "seller_portfolio_overlap_ratio": 0.47,
        "llm_saturation_assessment": None,
    }


def _base_weakness_inputs() -> dict[str, Any]:
    return {
        "keyword": "python automation",
        "video_absence_rate": 0.5,
        "portfolio_absence_rate": 0.4,
    }


def _base_trend_inputs() -> dict[str, Any]:
    return {
        "keyword": "python automation",
        "google_trends_slope": 10.0,
        "trends_3mo_avg": 72.0,
        "trends_12mo_avg": 60.0,
        "reddit_recent_post_volume": 30.0,
        "reddit_historical_post_volume": 20.0,
        "llm_trend_classification": None,
    }


def test_intent_with_llm_transactional() -> None:
    calculator = ConversionIntentScoreCalculator()
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="TRANSACTIONAL")
    result = calculator.calculate(
        601,
        FakeScoringDB(intent_inputs={601: _base_intent_inputs()}),
        llm_client=llm_client,
    )
    assert result.score_components["llm_buyer_intent"].value == 100.0


def test_intent_without_llm_uses_stub() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    result = calculator.calculate(601, FakeScoringDB(intent_inputs={601: inputs}))
    assert result.score_components["llm_buyer_intent"].value == 40.0
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)


def test_intent_llm_failure_graceful() -> None:
    calculator = ConversionIntentScoreCalculator()
    llm_client = Mock()
    llm_client.complete.side_effect = RuntimeError("boom")
    result = calculator.calculate(
        601,
        FakeScoringDB(intent_inputs={601: _base_intent_inputs()}),
        llm_client=llm_client,
    )
    assert result.score_value is not None
    assert any("llm_intent_failed" in warning for warning in result.missing_data_warnings)


def test_saturation_with_llm_score() -> None:
    calculator = SaturationScoreCalculator()
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="75")
    result = calculator.calculate(
        701,
        FakeScoringDB(saturation_inputs={701: _base_saturation_inputs()}),
        llm_client=llm_client,
    )
    assert result.score_components["llm_saturation_assessment"].value == 75.0


def test_saturation_without_llm_stub() -> None:
    calculator = SaturationScoreCalculator()
    result = calculator.calculate(701, FakeScoringDB(saturation_inputs={701: _base_saturation_inputs()}))
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)


def test_saturation_llm_invalid_response() -> None:
    calculator = SaturationScoreCalculator()
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="not a number")
    result = calculator.calculate(
        701,
        FakeScoringDB(saturation_inputs={701: _base_saturation_inputs()}),
        llm_client=llm_client,
    )
    assert any("llm_saturation_failed" in warning for warning in result.missing_data_warnings)


def test_weakness_collection_inputs_no_llm() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(801, FakeScoringDB(weakness_inputs={801: _base_weakness_inputs()}))
    assert "video_absence_rate" in result.score_components
    assert "portfolio_absence_rate" in result.score_components


def test_weakness_with_llm_description_quality() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    llm_client = Mock()
    llm_client.complete.side_effect = [
        SimpleNamespace(text="8.0"),
        SimpleNamespace(text="4.0"),
        SimpleNamespace(text="6.0"),
        SimpleNamespace(text="5.0"),
        SimpleNamespace(text="7.0"),
        SimpleNamespace(text="8.0"),
    ]
    result = calculator.calculate(
        801,
        FakeScoringDB(weakness_inputs={801: _base_weakness_inputs()}),
        llm_client=llm_client,
    )
    assert "description_quality_inverted" in result.score_components


def test_weakness_llm_partial_failure() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    llm_client = Mock()
    llm_client.complete.side_effect = [
        RuntimeError("nope"),
        SimpleNamespace(text="4.0"),
        RuntimeError("nope"),
        SimpleNamespace(text="5.0"),
        SimpleNamespace(text="7.0"),
        RuntimeError("nope"),
    ]
    result = calculator.calculate(
        801,
        FakeScoringDB(weakness_inputs={801: _base_weakness_inputs()}),
        llm_client=llm_client,
    )
    assert result.score_value is not None


def test_trend_with_llm_strongly_rising() -> None:
    calculator = TrendScoreCalculator()
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="STRONGLY_RISING")
    result = calculator.calculate(
        901,
        FakeScoringDB(trend_inputs={901: _base_trend_inputs()}),
        llm_client=llm_client,
    )
    assert result.score_components["llm_trend_classification"].value == 100.0


def test_trend_without_llm_uses_stable() -> None:
    calculator = TrendScoreCalculator()
    result = calculator.calculate(901, FakeScoringDB(trend_inputs={901: _base_trend_inputs()}))
    assert result.score_components["llm_trend_classification"].value == 50.0
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)


def test_trend_llm_unknown_classification() -> None:
    calculator = TrendScoreCalculator()
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="UNKNOWN")
    result = calculator.calculate(
        901,
        FakeScoringDB(trend_inputs={901: _base_trend_inputs()}),
        llm_client=llm_client,
    )
    assert result.score_components["llm_trend_classification"].value == 50.0
    assert any("llm_trend_failed" in warning for warning in result.missing_data_warnings)


def test_feature_flag_backward_compat_demand() -> None:
    calculator = DemandScoreCalculator()
    db = FakeScoringDB(demand_inputs={101: {"total_result_count": 1000, "autocomplete_position": 2}})
    result = calculator.calculate(101, db)
    assert result.score_value is not None


def test_feature_flag_backward_compat_competition() -> None:
    calculator = CompetitionScoreCalculator()
    db = FakeScoringDB(
        competition_inputs={
            201: {
                "total_result_count": 5000,
                "avg_review_count_top10": 300,
                "avg_seller_level_top10": "Level 2",
                "proportion_with_100_plus_reviews": 0.8,
                "pro_verified_presence_ratio": 0.2,
                "avg_starting_price_top10": 70,
                "llm_competitor_strength_rating": 7.0,
            }
        }
    )
    result = calculator.calculate(201, db)
    assert result.score_value is not None


def test_llm_cache_used_on_second_call() -> None:
    class Provider:
        def __init__(self) -> None:
            self.calls = 0
            self.provider_name = "test"

        def complete(self, prompt: str, model: str, temperature: float, response_format: Any = None) -> dict[str, Any]:
            self.calls += 1
            return {"text": "TRANSACTIONAL", "usage": {"prompt_tokens": 10, "completion_tokens": 2}}

    provider = Provider()
    llm_client = LLMClient(provider=provider, cache=LLMCache(db_path=None))
    calc = ConversionIntentScoreCalculator()
    db = FakeScoringDB(intent_inputs={601: _base_intent_inputs()})
    calc.calculate(601, db, llm_client=llm_client)
    calc.calculate(601, db, llm_client=llm_client)
    assert provider.calls == 1


def test_llm_client_none_no_crash_any_calculator() -> None:
    intent = ConversionIntentScoreCalculator().calculate(601, FakeScoringDB(intent_inputs={601: _base_intent_inputs()}))
    saturation = SaturationScoreCalculator().calculate(701, FakeScoringDB(saturation_inputs={701: _base_saturation_inputs()}))
    weakness = GigQualityWeaknessScoreCalculator().calculate(801, FakeScoringDB(weakness_inputs={801: _base_weakness_inputs()}))
    trend = TrendScoreCalculator().calculate(901, FakeScoringDB(trend_inputs={901: _base_trend_inputs()}))
    assert intent.score_value is not None
    assert saturation.score_value is not None
    assert weakness.score_value is not None
    assert trend.score_value is not None
