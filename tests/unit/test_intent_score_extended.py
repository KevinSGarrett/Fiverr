"""Extended intent score tests for Cycle 047 coverage closure."""

from __future__ import annotations

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
