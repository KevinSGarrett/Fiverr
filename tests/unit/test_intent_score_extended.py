"""Extended intent score tests for Cycle 047 coverage closure."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from src.scoring.intent import ConversionIntentScoreCalculator

# pylint: disable=protected-access


def test_intent_llm_classifier_accepts_valid_label() -> None:
    class FakeLLM:
        @staticmethod
        def complete(**_: object) -> SimpleNamespace:
            return SimpleNamespace(text="TRANSACTIONAL")

    label = ConversionIntentScoreCalculator()._run_async(
        ConversionIntentScoreCalculator()._get_llm_intent_class("hire python developer", FakeLLM(), None)
    )
    assert label == "TRANSACTIONAL"


def test_intent_llm_classifier_returns_none_for_unrecognized_label() -> None:
    class FakeLLM:
        @staticmethod
        def complete(**_: object) -> SimpleNamespace:
            return SimpleNamespace(text="RANDOM_CLASS")

    label = ConversionIntentScoreCalculator()._run_async(
        ConversionIntentScoreCalculator()._get_llm_intent_class("hire python developer", FakeLLM(), None)
    )
    assert label is None


def test_intent_commercial_modifier_score_branching() -> None:
    calculator = ConversionIntentScoreCalculator()
    assert calculator._resolve_commercial_modifier_score({"commercial_modifier_score": 0.75}, "ignored") == 75.0
    assert calculator._resolve_commercial_modifier_score({"commercial_modifier_score": 85.0}, "ignored") == 85.0
    assert calculator._resolve_commercial_modifier_score({}, "hire python developer") == 90.0
    assert calculator._resolve_commercial_modifier_score({}, "python") == 20.0


def test_intent_reddit_normalization_handles_ratio_and_score_inputs() -> None:
    calculator = ConversionIntentScoreCalculator()
    assert calculator._normalize_reddit_intent(7.2) == 72.0
    assert calculator._normalize_reddit_intent(78.0) == 78.0


def test_intent_calculate_defaults_unrecognized_llm_class_to_consideration() -> None:
    calculator = ConversionIntentScoreCalculator()
    result = calculator.calculate(
        keyword_id=1,
        db={
            1: {
                "keyword": "hire python developer",
                "avg_review_count_top10": 25,
                "llm_buyer_intent_classification": "not_in_map",
                "reddit_demand_intent_score": 0.7,
            }
        },
    )
    assert result.score_value is not None
    assert result.score_components["llm_buyer_intent"].value == 40.0
    assert "llm_intent_unrecognized" in result.confidence_breakdown


def test_intent_extract_llm_text_and_float_parse_failure_paths() -> None:
    calculator = ConversionIntentScoreCalculator()
    assert calculator._extract_llm_text("RAW-STRING") == "RAW-STRING"
    assert calculator._as_float("not-a-number") is None


def test_intent_run_async_works_when_event_loop_already_running() -> None:
    calculator = ConversionIntentScoreCalculator()

    async def _run_inside_loop() -> str:
        return calculator._run_async(calculator._get_llm_intent_class("hire python developer", _FakeLLM("TRANSACTIONAL"), None))

    assert asyncio.run(_run_inside_loop()) == "TRANSACTIONAL"


def test_intent_handles_missing_map_payload_and_nonpositive_reviews() -> None:
    calculator = ConversionIntentScoreCalculator()
    assert calculator._load_signals(42, {42: "not-a-mapping"}) == {}
    assert calculator._normalize_review_count(0.0) == 0.0


class _FakeLLM:
    def __init__(self, text: str) -> None:
        self._text = text

    def complete(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(text=self._text)
