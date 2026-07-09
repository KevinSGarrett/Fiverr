"""Targeted coverage tests for confidence score modifier helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Keyword, KeywordScore, Niche, NicheConfigRecord, ResultSetValidation
from src.scoring.confidence import ConfidenceScoreModifier, compute_confidence_score


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_confidence_load_context_from_provider_and_mapping() -> None:
    calculator = ConfidenceScoreModifier()

    class _Provider:
        @staticmethod
        def get_confidence_inputs(_keyword_id: int) -> dict[str, Any]:
            return {"data_completeness_ratio": 0.75}

    loaded = calculator._load_context(11, None, _Provider())  # pylint: disable=protected-access
    assert loaded["data_completeness_ratio"] == 0.75

    mapping_loaded = calculator._load_context(11, None, {11: {"mode": "keyword_only"}})  # pylint: disable=protected-access
    assert mapping_loaded["mode"] == "keyword_only"

    empty_loaded = calculator._load_context(11, None, {11: "invalid"})  # pylint: disable=protected-access
    assert empty_loaded == {}


def test_confidence_signal_load_uses_niche_depth_from_config_record() -> None:
    session = _session()
    try:
        niche = Niche(slug="confidence-niche", name="Confidence Niche", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()

        keyword = Keyword(
            niche_id=niche.id,
            keyword="confidence keyword",
            normalized_keyword="confidence keyword",
        )
        session.add(keyword)
        session.flush()

        session.add(
            NicheConfigRecord(
                niche_id=str(niche.id),
                name="Confidence Config",
                category_path="Programming & Tech > AI",
                depth="feasibility",
            )
        )
        session.commit()

        signals = ConfidenceScoreModifier()._load_signals_from_db(keyword.id, session)  # pylint: disable=protected-access
        assert signals["mode"] == "feasibility"
    finally:
        session.close()


def test_confidence_parsers_cover_none_invalid_and_string_booleans() -> None:
    calculator = ConfidenceScoreModifier()

    assert calculator._as_float(None, 0.5) == 0.5  # pylint: disable=protected-access
    assert calculator._as_float("not-a-float", 0.7) == 0.7  # pylint: disable=protected-access
    assert calculator._as_bool(None, True) is True  # pylint: disable=protected-access
    assert calculator._as_bool("yes", False) is True  # pylint: disable=protected-access
    assert calculator._as_bool("0", True) is False  # pylint: disable=protected-access
    assert calculator._as_bool("unparsed", False) is False  # pylint: disable=protected-access


def test_confidence_latest_timestamp_returns_none_when_no_sources() -> None:
    session = _session()
    try:
        newest = ConfidenceScoreModifier()._latest_timestamp(  # pylint: disable=protected-access
            keyword=None,
            top_results=[],
            keyword_id=999,
            session=session,
        )
        assert newest is None
    finally:
        session.close()


def test_compute_confidence_score_prefers_latest_persisted_modifier() -> None:
    session = _session()
    try:
        niche = Niche(slug="persisted-score", name="Persisted Score", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        keyword = Keyword(
            niche_id=niche.id,
            keyword="persisted keyword",
            normalized_keyword="persisted keyword",
        )
        session.add(keyword)
        session.flush()

        session.add(
            KeywordScore(
                keyword_id=keyword.id,
                scored_at=datetime.now(UTC) - timedelta(minutes=1),
                final_score=35.0,
                confidence_modifier=0.62,
                tag="CAUTION",
                score_components={},
            )
        )
        session.add(
            KeywordScore(
                keyword_id=keyword.id,
                scored_at=datetime.now(UTC),
                final_score=38.0,
                confidence_modifier=0.75,
                tag="CAUTION",
                score_components={},
            )
        )
        session.commit()

        modifier = compute_confidence_score(keyword_id=keyword.id, db=session)
        assert modifier == 0.75
    finally:
        session.close()


def test_compute_confidence_score_uses_run_context_when_provided() -> None:
    session = _session()
    try:
        modifier = compute_confidence_score(
            keyword_id=999,
            db=session,
            run_context={
                "data_completeness_ratio": 1.0,
                "data_freshness_score": 1.0,
                "source_diversity_score": 1.0,
                "llm_analysis_completion_ratio": 1.0,
                "google_trends_available": True,
                "gig_detail_collected": True,
                "seller_profiles_collected": True,
                "reddit_signals_available": True,
            },
        )
        assert modifier == 1.0
    finally:
        session.close()


def test_confidence_modifier_uses_current_run_context_not_none() -> None:
    session = _session()
    try:
        niche = Niche(slug="context-priority", name="Context Priority", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        keyword = Keyword(
            niche_id=niche.id,
            keyword="context priority keyword",
            normalized_keyword="context priority keyword",
        )
        session.add(keyword)
        session.commit()

        calculator = ConfidenceScoreModifier()
        explicit_context = {
            "data_completeness_ratio": 1.0,
            "data_freshness_score": 1.0,
            "source_diversity_score": 1.0,
            "llm_analysis_completion_ratio": 1.0,
            "google_trends_available": True,
            "gig_detail_collected": True,
            "seller_profiles_collected": True,
            "reddit_signals_available": True,
            "llm_gig_quality_incomplete_count": 0.0,
            "llm_competitor_synthesis_failed": False,
            "mode": "standard",
        }

        modifier_with_context, _ = calculator.calculate_with_breakdown(
            keyword_id=keyword.id,
            run_context=explicit_context,
            db=session,
        )
        modifier_without_context, _ = calculator.calculate_with_breakdown(
            keyword_id=keyword.id,
            run_context=None,
            db=session,
        )

        assert modifier_with_context == 1.0
        assert modifier_with_context > modifier_without_context
    finally:
        session.close()


def test_confidence_modifier_improves_when_signals_present() -> None:
    calculator = ConfidenceScoreModifier()
    base_context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": False,
        "llm_gig_quality_incomplete_count": 2.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    low_modifier, _ = calculator.calculate_with_breakdown(keyword_id=1, run_context=base_context, db=None)

    improved_context = dict(base_context)
    improved_context["reddit_signals_available"] = True
    improved_context["llm_gig_quality_incomplete_count"] = 0.0
    high_modifier, breakdown = calculator.calculate_with_breakdown(
        keyword_id=1,
        run_context=improved_context,
        db=None,
    )

    assert low_modifier < high_modifier
    assert high_modifier == 1.0
    assert "missing_reddit_signals" not in breakdown
    assert "llm_gig_quality_incomplete" not in breakdown


def test_external_signal_quality_not_blended_without_signal_context() -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": False,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
        "external_signals_enabled": True,
        "signal_age_days": 0,
        "signal_relevance_score": 1.0,
        "external_signal_context_present": False,
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=1, run_context=context, db=None)
    assert "freshness_relevance_quality" not in breakdown
    assert modifier == pytest.approx(0.95, abs=1e-4)


def test_external_signal_quality_blended_when_signal_context_present() -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": False,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
        "external_signals_enabled": True,
        "signal_age_days": 0,
        "signal_relevance_score": 1.0,
        "external_signal_context_present": True,
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=1, run_context=context, db=None)
    assert breakdown["freshness_relevance_quality"] == pytest.approx(1.0, abs=1e-4)
    assert modifier == pytest.approx(0.965, abs=1e-4)


@pytest.mark.parametrize(
    ("raw_value", "default_value", "expected"),
    [
        (None, 0.0, 0.0),
        ("1", 0.0, 1.0),
        ("1.25", 0.0, 1.25),
        ("-2", 0.0, -2.0),
        ("nan", 5.0, float("nan")),
        ("inf", 1.0, float("inf")),
        ("-inf", 1.0, float("-inf")),
        ("0", 9.0, 0.0),
        ("0.5", 1.0, 0.5),
        ("42", 1.0, 42.0),
        (3.14, 0.0, 3.14),
        (10, 0.0, 10.0),
        (True, 0.0, 1.0),
        (False, 0.0, 0.0),
        (" 7 ", 0.0, 7.0),
        ("not-a-number", 2.5, 2.5),
        ({}, 4.0, 4.0),
        ([], 6.0, 6.0),
        ((), 8.0, 8.0),
        ("", 3.0, 3.0),
        ("+12", 0.0, 12.0),
        ("-0.25", 0.0, -0.25),
        ("1e2", 0.0, 100.0),
        ("-1e-2", 0.0, -0.01),
        ("3.1415926535", 0.0, 3.1415926535),
        ("2.0", 5.0, 2.0),
        ("  0.75  ", 9.0, 0.75),
        ("5e-1", 9.0, 0.5),
        (0, 9.0, 0.0),
        (1, 9.0, 1.0),
    ],
)
def test_confidence_as_float_parametrized(raw_value: Any, default_value: float, expected: float) -> None:
    calculator = ConfidenceScoreModifier()
    actual = calculator._as_float(raw_value, default_value)  # pylint: disable=protected-access
    if expected != expected:  # NaN check
        assert actual != actual
    else:
        assert actual == expected


@pytest.mark.parametrize(
    ("raw_value", "default_value", "expected"),
    [
        (None, True, True),
        (None, False, False),
        (True, False, True),
        (False, True, False),
        ("true", False, True),
        ("TRUE", False, True),
        ("True", False, True),
        ("  true  ", False, True),
        ("1", False, True),
        ("yes", False, True),
        ("YES", False, True),
        ("false", True, False),
        ("FALSE", True, False),
        ("False", True, False),
        ("  false  ", True, False),
        ("0", True, False),
        ("no", True, False),
        ("NO", True, False),
        ("y", True, True),
        ("n", False, False),
        ("t", True, True),
        ("f", False, False),
        ("enabled", True, True),
        ("disabled", False, False),
        ("", True, True),
        ("", False, False),
        (0, True, True),
        (1, False, False),
        ({}, True, True),
        ([], False, False),
    ],
)
def test_confidence_as_bool_parametrized(raw_value: Any, default_value: bool, expected: bool) -> None:
    calculator = ConfidenceScoreModifier()
    actual = calculator._as_bool(raw_value, default_value)  # pylint: disable=protected-access
    assert actual is expected


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (-10.0, 0.0),
        (-5.0, 0.0),
        (-1.0, 0.0),
        (-0.5, 0.0),
        (-0.0001, 0.0),
        (0.0, 0.0),
        (0.0001, 0.0001),
        (0.01, 0.01),
        (0.1, 0.1),
        (0.2, 0.2),
        (0.25, 0.25),
        (0.3333, 0.3333),
        (0.5, 0.5),
        (0.6667, 0.6667),
        (0.75, 0.75),
        (0.9, 0.9),
        (0.99, 0.99),
        (0.9999, 0.9999),
        (1.0, 1.0),
        (1.0001, 1.0),
        (1.1, 1.0),
        (2.0, 1.0),
        (5.0, 1.0),
        (10.0, 1.0),
    ],
)
def test_confidence_clamp_0_1_parametrized(raw_value: float, expected: float) -> None:
    calculator = ConfidenceScoreModifier()
    actual = calculator._clamp_0_1(raw_value)  # pylint: disable=protected-access
    assert actual == expected


@pytest.mark.parametrize(
    ("incomplete_count", "expected_penalty"),
    [
        (-5.0, 0.0),
        (-1.0, 0.0),
        (-0.5, 0.0),
        (0.0, 0.0),
        (0.01, -0.0008),
        (0.25, -0.02),
        (0.5, -0.04),
        (1.0, -0.08),
        (1.5, -0.12),
        (2.0, -0.16),
        (2.5, -0.2),
        (3.0, -0.2),
        (5.0, -0.2),
        (10.0, -0.2),
        (100.0, -0.2),
        (1000.0, -0.2),
    ],
)
def test_confidence_llm_gig_quality_penalty_cap(
    incomplete_count: float,
    expected_penalty: float,
) -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": incomplete_count,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=1, run_context=context, db=None)

    if expected_penalty == 0.0:
        assert "llm_gig_quality_incomplete" not in breakdown
    else:
        assert breakdown["llm_gig_quality_incomplete"] == pytest.approx(expected_penalty, abs=1e-4)
    assert modifier == pytest.approx(1.0 + expected_penalty, abs=1e-4)


@pytest.mark.parametrize(
    ("age_hours", "ttl_hours", "expect_stale_penalty"),
    [
        (0.0, 168.0, False),
        (10.0, 168.0, False),
        (100.0, 168.0, False),
        (335.9999, 168.0, False),
        (336.0, 168.0, False),
        (336.0001, 168.0, True),
        (500.0, 168.0, True),
        (1000.0, 168.0, True),
        (1.0, 0.0, False),
        (999.0, 0.0, False),
        (999.0, -1.0, False),
        (-1.0, 168.0, False),
        (48.0, 24.0, False),
        (48.0001, 24.0, True),
        (2.0, 1.0, False),
        (2.0001, 1.0, True),
    ],
)
def test_confidence_stale_data_threshold_logic(
    age_hours: float,
    ttl_hours: float,
    expect_stale_penalty: bool,
) -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "data_age_hours": age_hours,
        "data_ttl_hours": ttl_hours,
        "mode": "standard",
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=2, run_context=context, db=None)

    if expect_stale_penalty:
        assert breakdown["data_stale_over_2x_ttl"] == -0.15
        assert modifier == pytest.approx(0.85, abs=1e-4)
    else:
        assert "data_stale_over_2x_ttl" not in breakdown
        assert modifier == pytest.approx(1.0, abs=1e-4)


@pytest.mark.parametrize(
    ("mode_value", "expect_mode_penalty"),
    [
        ("standard", False),
        ("STANDARD", False),
        (" standard ", False),
        ("keyword_only", True),
        ("KEYWORD_ONLY", True),
        (" keyword_only ", True),
        ("feasibility", True),
        ("FEASIBILITY", True),
        (" feasibility ", True),
        ("full", False),
        ("production", False),
        ("keyword only", False),
        ("", False),
        ("   ", False),
        (None, False),
        ("research", False),
    ],
)
def test_confidence_partial_depth_mode_penalty(mode_value: str | None, expect_mode_penalty: bool) -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": mode_value,
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=3, run_context=context, db=None)

    if expect_mode_penalty:
        assert breakdown["partial_depth_mode"] == -0.25
        assert modifier == pytest.approx(0.75, abs=1e-4)
    else:
        assert "partial_depth_mode" not in breakdown
        assert modifier == pytest.approx(1.0, abs=1e-4)


def test_confidence_kw3_cm_matches_expected_with_full_data() -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=3, run_context=context, db=None)
    assert modifier == 1.0
    assert breakdown["deduction_total"] == 0.0
    assert breakdown["remaining_modifier"] == 1.0


def test_confidence_base_modifier_does_not_collapse_on_llm_hiccup() -> None:
    """PM_Pack/ref/project_plan/05_scoring/CONFIDENCE_SCORE.md specifies base_modifier
    as an ADDITIVE weighted sum (0.30/0.30/0.20/0.20) of completeness, freshness,
    diversity, and llm_completion - NOT llm_completion multiplicatively gating the
    other three. A transient LLM hiccup (llm_analysis_completion_ratio=0.0) with
    otherwise-perfect data must land at the spec's floor of 0.80, not collapse the
    entire base modifier to 0.0."""
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 0.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=3, run_context=context, db=None)
    assert breakdown["base_modifier"] == pytest.approx(0.80)
    assert modifier == pytest.approx(0.80)


def test_confidence_base_modifier_weights_all_four_inputs_additively() -> None:
    """Locks in the spec's exact 0.30/0.30/0.20/0.20 weight split (not the old,
    incorrect 0.50/0.30/0.20 multiplicative split) by varying each input
    independently against non-uniform values for the other three."""
    calculator = ConfidenceScoreModifier()
    base_context = {
        "data_completeness_ratio": 0.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    _, breakdown = calculator.calculate_with_breakdown(keyword_id=3, run_context=base_context, db=None)
    # completeness=0.0: 0*0.30 + 1*0.30 + 1*0.20 + 1*0.20 = 0.70 (spec), not 0.50
    # (the old multiplicative formula's (0*0.50+1*0.30+1*0.20)*1 result).
    assert breakdown["base_modifier"] == pytest.approx(0.70)

    freshness_zero = dict(base_context, data_completeness_ratio=1.0, data_freshness_score=0.0)
    _, breakdown = calculator.calculate_with_breakdown(keyword_id=3, run_context=freshness_zero, db=None)
    assert breakdown["base_modifier"] == pytest.approx(0.70)

    diversity_zero = dict(base_context, data_completeness_ratio=1.0, source_diversity_score=0.0)
    _, breakdown = calculator.calculate_with_breakdown(keyword_id=3, run_context=diversity_zero, db=None)
    assert breakdown["base_modifier"] == pytest.approx(0.80)


def test_confidence_reddit_deduction_removed_when_signal_present() -> None:
    calculator = ConfidenceScoreModifier()
    base_context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": False,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    modifier_missing, breakdown_missing = calculator.calculate_with_breakdown(
        keyword_id=3,
        run_context=base_context,
        db=None,
    )
    assert breakdown_missing["missing_reddit_signals"] == -0.05

    with_reddit = dict(base_context)
    with_reddit["reddit_signals_available"] = True
    modifier_present, breakdown_present = calculator.calculate_with_breakdown(
        keyword_id=3,
        run_context=with_reddit,
        db=None,
    )
    assert "missing_reddit_signals" not in breakdown_present
    assert modifier_present == pytest.approx(modifier_missing + 0.05, abs=1e-4)
    assert modifier_present == 1.0


def test_confidence_seller_profiles_deduction_removed_when_collected() -> None:
    calculator = ConfidenceScoreModifier()
    base_context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": False,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0.0,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    modifier_missing, breakdown_missing = calculator.calculate_with_breakdown(
        keyword_id=3,
        run_context=base_context,
        db=None,
    )
    assert breakdown_missing["missing_seller_profiles"] == -0.1

    with_seller_profiles = dict(base_context)
    with_seller_profiles["seller_profiles_collected"] = True
    modifier_present, breakdown_present = calculator.calculate_with_breakdown(
        keyword_id=3,
        run_context=with_seller_profiles,
        db=None,
    )
    assert "missing_seller_profiles" not in breakdown_present
    assert modifier_present == pytest.approx(modifier_missing + 0.1, abs=1e-4)
    assert modifier_present == 1.0


_CM_SIGNAL_DEDUCTION_MATRIX = [
    pytest.param(
        google_trends_available,
        gig_detail_collected,
        seller_profiles_collected,
        reddit_signals_available,
        incomplete_count,
        id=(
            f"trends_{google_trends_available}_detail_{gig_detail_collected}_"
            f"seller_{seller_profiles_collected}_reddit_{reddit_signals_available}_"
            f"incomplete_{incomplete_count}"
        ),
    )
    for google_trends_available in (True, False)
    for gig_detail_collected in (True, False)
    for seller_profiles_collected in (True, False)
    for reddit_signals_available in (True, False)
    for incomplete_count in (0.0, 0.5, 1.0, 2.5, 5.0)
]


@pytest.mark.parametrize(
    (
        "google_trends_available",
        "gig_detail_collected",
        "seller_profiles_collected",
        "reddit_signals_available",
        "incomplete_count",
    ),
    _CM_SIGNAL_DEDUCTION_MATRIX,
)
def test_confidence_deduction_matrix_matches_expected(
    google_trends_available: bool,
    gig_detail_collected: bool,
    seller_profiles_collected: bool,
    reddit_signals_available: bool,
    incomplete_count: float,
) -> None:
    calculator = ConfidenceScoreModifier()
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": google_trends_available,
        "gig_detail_collected": gig_detail_collected,
        "seller_profiles_collected": seller_profiles_collected,
        "reddit_signals_available": reddit_signals_available,
        "llm_gig_quality_incomplete_count": incomplete_count,
        "llm_competitor_synthesis_failed": False,
        "mode": "standard",
    }
    modifier, breakdown = calculator.calculate_with_breakdown(keyword_id=7, run_context=context, db=None)

    expected_deduction = 0.0
    if not google_trends_available:
        expected_deduction -= 0.15
    if not gig_detail_collected:
        expected_deduction -= 0.20
    if not seller_profiles_collected:
        expected_deduction -= 0.10
    if not reddit_signals_available:
        expected_deduction -= 0.05

    expected_llm_penalty = max(-0.20, -(max(0.0, incomplete_count) * 0.08))
    if expected_llm_penalty < 0.0:
        expected_deduction += expected_llm_penalty
        assert breakdown["llm_gig_quality_incomplete"] == pytest.approx(expected_llm_penalty, abs=1e-4)
    else:
        assert "llm_gig_quality_incomplete" not in breakdown

    expected_modifier = max(0.0, min(1.0, 1.0 + expected_deduction))
    assert breakdown["deduction_total"] == pytest.approx(expected_deduction, abs=1e-4)
    assert modifier == pytest.approx(expected_modifier, abs=1e-4)


def test_confidence_zombie_concentration_high_minus_0_10() -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "mode": "standard",
        "enable_zombie_filter": True,
        "zombie_fraction": 0.50,
    }
    modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(1, context, None)
    assert breakdown["zombie_concentration_high"] == -0.10
    assert modifier == pytest.approx(0.90, abs=1e-4)


def test_confidence_zombie_concentration_moderate_minus_0_05() -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "mode": "standard",
        "enable_zombie_filter": True,
        "zombie_fraction": 0.30,
    }
    modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(1, context, None)
    assert breakdown["zombie_concentration_moderate"] == -0.05
    assert modifier == pytest.approx(0.95, abs=1e-4)


def test_confidence_no_zombie_key_when_below_threshold() -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "mode": "standard",
        "enable_zombie_filter": True,
        "zombie_fraction": 0.24,
    }
    _modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(1, context, None)
    assert "zombie_concentration_high" not in breakdown
    assert "zombie_concentration_moderate" not in breakdown


def test_confidence_ghost_applies_minus_050() -> None:
    session = _session()
    try:
        niche = Niche(slug="ghost-niche", name="Ghost Niche", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        keyword = Keyword(niche_id=niche.id, keyword="ghost keyword", normalized_keyword="ghost keyword")
        session.add(keyword)
        session.flush()
        session.add(
            ResultSetValidation(
                keyword_id=keyword.id,
                run_id="r1",
                ghost_market_flag=True,
                relevance_deduction=-0.15,
            )
        )
        session.commit()
        modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(
            keyword.id,
            {
                "data_completeness_ratio": 1.0,
                "data_freshness_score": 1.0,
                "source_diversity_score": 1.0,
                "llm_analysis_completion_ratio": 1.0,
                "google_trends_available": True,
                "gig_detail_collected": True,
                "seller_profiles_collected": True,
                "reddit_signals_available": True,
            },
            session,
        )
        assert breakdown["ghost_market"] == -0.50
        assert modifier == pytest.approx(0.5, abs=1e-4)
    finally:
        session.close()


def test_confidence_moderate_applies_relevance_deduction() -> None:
    session = _session()
    try:
        niche = Niche(slug="rsv-niche", name="RSV Niche", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        keyword = Keyword(niche_id=niche.id, keyword="rsv keyword", normalized_keyword="rsv keyword")
        session.add(keyword)
        session.flush()
        session.add(
            ResultSetValidation(
                keyword_id=keyword.id,
                run_id="r1",
                ghost_market_flag=False,
                relevance_deduction=-0.15,
            )
        )
        session.commit()
        modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(
            keyword.id,
            {
                "data_completeness_ratio": 1.0,
                "data_freshness_score": 1.0,
                "source_diversity_score": 1.0,
                "llm_analysis_completion_ratio": 1.0,
                "google_trends_available": True,
                "gig_detail_collected": True,
                "seller_profiles_collected": True,
                "reddit_signals_available": True,
            },
            session,
        )
        assert breakdown["result_set_relevance"] == -0.15
        assert modifier == pytest.approx(0.85, abs=1e-4)
    finally:
        session.close()


def test_confidence_no_rsv_is_baseline() -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
    }
    modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(123, context, None)
    assert modifier == 1.0
    assert "result_set_relevance" not in breakdown


def test_confidence_no_rsv_equals_baseline() -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
    }
    modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(8080, context, None)
    assert modifier == 1.0
    assert "ghost_market" not in breakdown
    assert "result_set_relevance" not in breakdown


def test_confidence_deduction_reaches_final_value() -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
    }
    baseline, _ = ConfidenceScoreModifier().calculate_with_breakdown(101, context, None)

    session = _session()
    try:
        niche = Niche(slug="deduct-niche", name="Deduct Niche", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        keyword = Keyword(niche_id=niche.id, keyword="deduct keyword", normalized_keyword="deduct keyword")
        session.add(keyword)
        session.flush()
        session.add(ResultSetValidation(keyword_id=keyword.id, run_id="r1", ghost_market_flag=False, relevance_deduction=-0.15))
        session.commit()
        with_deduction, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(keyword.id, context, session)
        assert breakdown["result_set_relevance"] == -0.15
        assert with_deduction == pytest.approx(baseline - 0.15, abs=1e-4)
    finally:
        session.close()


def test_confidence_uses_shared_rsv_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def _fake_get_result_set_validation(keyword_id: int, _db: Any) -> Any:  # type: ignore[no-untyped-def]
        calls.append(keyword_id)
        return None

    monkeypatch.setattr("src.scoring.confidence.get_result_set_validation", _fake_get_result_set_validation)
    ConfidenceScoreModifier().calculate_with_breakdown(
        4242,
        {
            "data_completeness_ratio": 1.0,
            "data_freshness_score": 1.0,
            "source_diversity_score": 1.0,
            "llm_analysis_completion_ratio": 1.0,
            "google_trends_available": True,
            "gig_detail_collected": True,
            "seller_profiles_collected": True,
            "reddit_signals_available": True,
        },
        db=object(),
    )
    assert calls == [4242]
