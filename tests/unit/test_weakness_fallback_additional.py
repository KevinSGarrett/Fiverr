"""Additional weakness fallback and helper coverage for Cycle 048 Agent F."""

from __future__ import annotations

from types import SimpleNamespace

from src.models import GigQualityAnalysis, GigQualityScore
from src.scoring.weakness import GigQualityWeaknessScoreCalculator, get_gig_quality_weakness_input
from tests.unit.test_scoring_weakness_gqs import (
    _insert_gqa_row,
    _new_session,
    _seed_run_scoped_keyword,
)


def test_weakness_fallback_run_id_path_is_exercised() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-run")
        _insert_gqa_row(session, gig_url=gig_url, run_id="fallback-run", rubric_score=10.0)
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value > 0.0
    finally:
        session.close()


def test_weakness_fallback_selects_correct_run_when_multiple_available() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-run")
        _insert_gqa_row(session, gig_url=gig_url, run_id="older-run", rubric_score=90.0)
        _insert_gqa_row(session, gig_url=gig_url, run_id="newer-run", rubric_score=40.0)
        resolved = GigQualityWeaknessScoreCalculator()._resolve_weakness_input_run_id(  # pylint: disable=protected-access
            session,
            active_run_id="active-run",
            top_card_urls=[gig_url],
            top_results=[],
        )
        assert resolved == "newer-run"
    finally:
        session.close()


def test_weakness_active_run_takes_precedence_over_fallback() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-run")
        _insert_gqa_row(session, gig_url=gig_url, run_id="active-run", rubric_score=60.0)
        _insert_gqa_row(session, gig_url=gig_url, run_id="fallback-run", rubric_score=5.0)
        resolved = GigQualityWeaknessScoreCalculator()._resolve_weakness_input_run_id(  # pylint: disable=protected-access
            session,
            active_run_id="active-run",
            top_card_urls=[gig_url],
            top_results=[],
        )
        assert resolved == "active-run"
    finally:
        session.close()


def test_weakness_extract_top_card_urls_skips_invalid_entries_and_caps_limit() -> None:
    top_results = [
        SimpleNamespace(
            gig_cards=[
                {"position": 2, "gig_url": "https://fiverr.com/a"},
                {"position": 1, "gig_url": "https://fiverr.com/b"},
                {"position": "3", "gig_url": "https://fiverr.com/c"},
                {"position": 4, "gig_url": 123},
                "bad-card",
                {"position": 5, "gig_url": "https://fiverr.com/d"},
            ]
        )
    ]
    urls = GigQualityWeaknessScoreCalculator()._extract_top_card_urls(top_results, limit=3)  # pylint: disable=protected-access
    assert urls == ["https://fiverr.com/b", "https://fiverr.com/a", "https://fiverr.com/c"]


def test_weakness_load_signals_none_db_returns_empty_dict() -> None:
    assert GigQualityWeaknessScoreCalculator()._load_signals(100, None) == {}  # pylint: disable=protected-access


def test_weakness_input_uses_niche_identity_fallback_when_run_missing() -> None:
    session = _new_session()
    try:
        session.add(
            GigQualityAnalysis(
                gig_url="https://www.fiverr.com/services/same-path?utm=1",
                niche_id="run-fallback-niche",
                run_id="run-x",
                rubric_score=55.0,
                video_absent=True,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=["video_absent"],
            )
        )
        session.commit()
        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/services/same-path?ref=abc",
            niche_id="run-fallback-niche",
            run_id="",
            db=session,
        )
        assert payload["source"] == "gig_quality_analysis"
        assert payload["run_id"] == "run-x"
    finally:
        session.close()


def test_weakness_input_uses_global_identity_fallback_without_niche_or_run() -> None:
    session = _new_session()
    try:
        session.add(
            GigQualityAnalysis(
                gig_url="https://www.fiverr.com/services/global-path?utm=1",
                niche_id="other-niche",
                run_id="run-y",
                rubric_score=40.0,
                video_absent=True,
                portfolio_absent=True,
                description_thin=False,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=["video_absent", "portfolio_absent"],
            )
        )
        session.commit()
        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/services/global-path?src=zzz",
            niche_id="",
            run_id="",
            db=session,
        )
        assert payload["source"] == "gig_quality_analysis"
    finally:
        session.close()


def test_weakness_input_uses_legacy_gqs_identity_fallback_without_run() -> None:
    session = _new_session()
    try:
        session.add(
            GigQualityScore(
                keyword_id=1,
                gig_url="https://www.fiverr.com/services/gqs-path?old=1",
                run_id="legacy-run",
                video_present=False,
                portfolio_count=0,
                analysis_complete=True,
            )
        )
        session.commit()
        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/services/gqs-path?new=1",
            niche_id="",
            run_id="",
            db=session,
        )
        assert payload["source"] == "gig_quality_score"
        assert payload["run_id"] == "legacy-run"
    finally:
        session.close()


def test_weakness_resolve_run_id_returns_active_when_no_target_urls() -> None:
    session = _new_session()
    try:
        resolved = GigQualityWeaknessScoreCalculator()._resolve_weakness_input_run_id(  # pylint: disable=protected-access
            session,
            active_run_id="active-run",
            top_card_urls=[],
            top_results=[],
        )
        assert resolved == "active-run"
    finally:
        session.close()
