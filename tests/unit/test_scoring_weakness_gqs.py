"""Unit tests for GigQualityScore supplementation in weakness signals."""

from __future__ import annotations

import builtins
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    Gig,
    GigQualityAnalysis,
    GigQualityScore,
    Keyword,
    KeywordScore,
    Niche,
    SearchResult,
)
from src.scoring.weakness import (
    GigQualityWeaknessScoreCalculator,
    compute_weakness_penalty_from_flags,
    get_gig_quality_weakness_input,
)


def _new_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _seed_keyword(
    session: Session,
    *,
    fallback_video: list[bool] | None = None,
    fallback_portfolio: list[bool] | None = None,
) -> int:
    fallback_video = fallback_video or ([True] * 10)
    fallback_portfolio = fallback_portfolio or ([True] * 10)

    niche = Niche(slug="weakness-niche", name="Weakness Niche", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="weakness keyword",
        normalized_keyword="weakness keyword",
    )
    session.add(keyword)
    session.flush()

    for idx in range(10):
        gig = Gig(
            gig_url=f"https://www.fiverr.com/gigs/{idx + 1}",
            seller_username=f"seller_{idx + 1}",
            metadata_json={
                "has_video": fallback_video[idx],
                "has_portfolio": fallback_portfolio[idx],
            },
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                rank=idx + 1,
                gig_id=gig.id,
                title=f"Gig {idx + 1}",
            )
        )

    session.commit()
    return keyword.id


def _insert_gqs_rows(
    session: Session,
    keyword_id: int,
    rows: list[tuple[bool | None, int | None, bool]],
    *,
    gig_urls: list[str] | None = None,
    run_id: str = "legacy",
) -> None:
    resolved_urls = gig_urls or [f"https://www.fiverr.com/gigs/{idx}" for idx in range(1, len(rows) + 1)]
    for idx, (video_present, portfolio_count, analysis_complete) in enumerate(rows, start=1):
        session.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=resolved_urls[idx - 1],
                run_id=run_id,
                video_present=video_present,
                portfolio_count=portfolio_count,
                analysis_complete=analysis_complete,
            )
        )
    session.commit()


def test_weakness_gqs_no_rows() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
        assert signals["portfolio_absence_rate"] == 0.0
        assert "gig_quality_score_available" not in signals
    finally:
        session.close()


def test_weakness_gqs_video_present_all() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(True, 1, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
    finally:
        session.close()


def test_weakness_gqs_video_absent_all() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(False, 1, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 1.0
    finally:
        session.close()


def test_weakness_gqs_video_mixed() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        rows = [(True, 1, True)] * 3 + [(False, 1, True)] * 7
        _insert_gqs_rows(session, keyword_id, rows)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.7
    finally:
        session.close()


def test_weakness_gqs_portfolio_zero_all() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(True, 0, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["portfolio_absence_rate"] == 1.0
    finally:
        session.close()


def test_weakness_gqs_portfolio_nonzero() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(True, 2, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["portfolio_absence_rate"] == 0.0
    finally:
        session.close()


def test_weakness_gqs_overrides_visual_analysis() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session, fallback_video=[True] * 10, fallback_portfolio=[True] * 10)
        _insert_gqs_rows(session, keyword_id, [(False, 0, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 1.0
        assert signals["portfolio_absence_rate"] == 1.0
        assert signals["top10_has_video"] == [False] * 10
    finally:
        session.close()


def test_weakness_gqs_exception_safe(monkeypatch) -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        original_import = builtins.__import__

        def _raise_on_gqs(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            if name == "src.models.gig_quality_score":
                raise ImportError("forced import failure")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _raise_on_gqs)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
        assert signals["portfolio_absence_rate"] == 0.0
    finally:
        session.close()


def test_weakness_gqs_analysis_complete() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        rows = [(True, 1, False)] * 9 + [(True, 1, True)]
        _insert_gqs_rows(session, keyword_id, rows)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["gig_quality_score_available"] is True
    finally:
        session.close()


def test_weakness_gqs_none_video_skipped() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        rows = [
            (None, 1, True),
            (None, 1, True),
            (False, 1, True),
            (True, 1, True),
        ]
        _insert_gqs_rows(session, keyword_id, rows)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.5
        assert signals["top10_has_video"] == [False, True]
    finally:
        session.close()


def test_weakness_gqs_ignores_rows_outside_current_top10() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session, fallback_video=[True] * 10, fallback_portfolio=[True] * 10)
        rows = [(False, 0, True), (False, 0, True)]
        _insert_gqs_rows(
            session,
            keyword_id,
            rows,
            gig_urls=[
                "https://www.fiverr.com/gigs/999",
                "https://www.fiverr.com/gigs/1000",
            ],
        )
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
        assert signals["portfolio_absence_rate"] == 0.0
        assert "gig_quality_score_available" not in signals
    finally:
        session.close()


def test_scoring_reads_gig_quality_analysis_output() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session, fallback_video=[True] * 10, fallback_portfolio=[True] * 10)
        for idx in range(1, 11):
            session.add(
                GigQualityAnalysis(
                    gig_url=f"https://www.fiverr.com/gigs/{idx}",
                    niche_id="weakness-niche",
                    run_id="legacy",
                    rubric_score=60.0,
                    video_absent=idx <= 6,
                    portfolio_absent=False,
                    description_thin=False,
                    faq_absent=False,
                    thumbnail_quality_flag=False,
                    weakness_flags=["video_absent"] if idx <= 6 else [],
                )
            )
        session.commit()

        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.6
        assert signals["portfolio_absence_rate"] == 0.0
        assert signals["gig_quality_analysis_available"] is True
    finally:
        session.close()


def _seed_run_scoped_keyword(
    session: Session,
    *,
    active_run_id: str = "active-run",
    gig_url: str = "https://www.fiverr.com/gigs/fallback-target",
    card_url: str | None = None,
    metadata_json: dict[str, object] | None = None,
) -> tuple[int, str]:
    niche = Niche(
        slug="run-fallback-niche",
        name="Run Fallback Niche",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="run fallback keyword",
        normalized_keyword="run fallback keyword",
    )
    session.add(keyword)
    session.flush()

    gig = Gig(
        gig_url=gig_url,
        keyword_id=keyword.id,
        run_id=active_run_id,
        seller_username="run_fallback_seller",
        metadata_json=metadata_json or {},
    )
    session.add(gig)
    session.flush()

    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id=active_run_id,
            rank=1,
            gig_id=gig.id,
            title="Run fallback result",
            gig_cards=[{"gig_url": card_url or gig_url, "position": 1}],
        )
    )
    session.commit()
    return keyword.id, gig_url


def _insert_gqa_row(
    session: Session,
    *,
    gig_url: str,
    run_id: str,
    rubric_score: float,
    analyzed_at: datetime | None = None,
    weakness_flags: list[str] | None = None,
) -> None:
    session.add(
        GigQualityAnalysis(
            gig_url=gig_url,
            niche_id="run-fallback-niche",
            run_id=run_id,
            rubric_score=rubric_score,
            video_absent=False,
            portfolio_absent=False,
            description_thin=False,
            faq_absent=False,
            thumbnail_quality_flag=False,
            weakness_flags=weakness_flags or [],
            analyzed_at=analyzed_at or datetime.now(UTC),
        )
    )
    session.commit()


def test_weakness_uses_fallback_run_id_when_active_run_has_no_gqa_rows() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-run")
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="fallback-run",
            rubric_score=30.0,
            weakness_flags=["NO_VIDEO"],
        )

        calculator = GigQualityWeaknessScoreCalculator()
        signals = calculator._load_signals_from_db(keyword_id, session)

        assert signals["overall_weakness_score_avg"] == 7.0
        assert signals["gig_quality_analysis_available"] is True
    finally:
        session.close()


def test_weakness_returns_none_when_no_gqa_rows_in_any_run() -> None:
    session = _new_session()
    try:
        keyword_id, _ = _seed_run_scoped_keyword(
            session,
            active_run_id="active-run",
            metadata_json={},
        )
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is None
    finally:
        session.close()


def test_weakness_prefers_active_run_over_fallback_when_both_have_rows() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-run")
        _insert_gqa_row(session, gig_url=gig_url, run_id="active-run", rubric_score=20.0)
        _insert_gqa_row(session, gig_url=gig_url, run_id="fallback-run", rubric_score=90.0)

        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 8.0
    finally:
        session.close()


def test_weakness_fallback_selects_most_recent_available_run() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-run")
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="older-run",
            rubric_score=90.0,
            analyzed_at=datetime.now(UTC) - timedelta(days=2),
        )
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="newer-run",
            rubric_score=40.0,
            analyzed_at=datetime.now(UTC) - timedelta(days=1),
        )

        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 6.0
    finally:
        session.close()


def test_weakness_kw3_equivalent_gets_weakness_with_fallback() -> None:
    session = _new_session()
    try:
        canonical_url = "https://www.fiverr.com/gigs/fallback-target"
        keyword_id, gig_url = _seed_run_scoped_keyword(
            session,
            active_run_id="active-run",
            gig_url=canonical_url,
            card_url=f"{canonical_url}?source=search",
            metadata_json={},
        )
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="stage11-run",
            rubric_score=35.0,
            weakness_flags=["NO_FAQ"],
        )

        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_components["overall_weakness_score"].value == 65.0
    finally:
        session.close()


def test_weakness_does_not_regress_kw96_behavior_after_fallback_added() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="kw96-run")
        _insert_gqa_row(session, gig_url=gig_url, run_id="kw96-run", rubric_score=46.48)
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="newer-run",
            rubric_score=10.0,
            analyzed_at=datetime.now(UTC) + timedelta(minutes=1),
        )

        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 5.35
    finally:
        session.close()


def test_weakness_prefers_active_run_when_no_top_card_identities() -> None:
    session = _new_session()
    try:
        keyword_id, _ = _seed_run_scoped_keyword(
            session,
            active_run_id="active-empty-cards",
            card_url="",
        )
        row = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).first()
        assert row is not None
        row.gig_cards = []
        session.commit()

        resolved_run = GigQualityWeaknessScoreCalculator()._resolve_weakness_input_run_id(
            session,
            active_run_id="active-empty-cards",
            top_card_urls=[],
            top_results=[],
        )
        assert resolved_run == "active-empty-cards"
    finally:
        session.close()


def test_weakness_uses_historical_fallback_when_signal_weight_insufficient() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(
            session,
            fallback_video=[True] * 10,
            fallback_portfolio=[None] * 10,  # type: ignore[list-item]
        )
        session.add(
            KeywordScore(
                keyword_id=keyword_id,
                final_score=50.0,
                score_components={
                    "weakness_score": {
                        "value": 53.52,
                        "effective_value": 53.52,
                        "weight": 0.2,
                        "contribution": 10.7,
                    }
                },
                tag="PASS",
            )
        )
        session.commit()

        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value == 53.52
        assert "historical_weakness_fallback" in result.score_components
    finally:
        session.close()


def test_weakness_uses_analysis_when_available() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        gig_url = "https://www.fiverr.com/gigs/1"
        session.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=gig_url,
                run_id="legacy",
                video_present=True,
                portfolio_count=2,
                analysis_complete=True,
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id="weakness-niche",
                run_id="legacy",
                rubric_score=20.0,
                video_absent=True,
                portfolio_absent=True,
                description_thin=True,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=["NO_VIDEO", "NO_PORTFOLIO", "THIN_DESCRIPTION"],
            )
        )
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url=gig_url,
            niche_id="weakness-niche",
            run_id="legacy",
            db=session,
        )
        assert payload["source"] == "gig_quality_analysis"
        assert payload["video_absent"] is True
        assert payload["portfolio_absent"] is True
    finally:
        session.close()


def test_weakness_falls_back_to_gqs_when_no_analysis() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        gig_url = "https://www.fiverr.com/gigs/1"
        session.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=gig_url,
                run_id="legacy",
                video_present=False,
                portfolio_count=0,
                analysis_complete=True,
            )
        )
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url=gig_url,
            niche_id="weakness-niche",
            run_id="legacy",
            db=session,
        )
        assert payload["source"] == "gig_quality_score"
        assert payload["video_absent"] is True
        assert payload["portfolio_absent"] is True
    finally:
        session.close()


def test_weakness_returns_defaults_when_neither_present() -> None:
    session = _new_session()
    try:
        _seed_keyword(session)
        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/gigs/1",
            niche_id="weakness-niche",
            run_id="legacy",
            db=session,
        )
        assert payload == {}
    finally:
        session.close()


def test_weakness_first_class_outranks_legacy_path() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        gig_url = "https://www.fiverr.com/gigs/1"
        session.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=gig_url,
                run_id="legacy",
                video_present=False,
                portfolio_count=0,
                analysis_complete=True,
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id="weakness-niche",
                run_id="legacy",
                rubric_score=95.0,
                video_absent=False,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=[],
            )
        )
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url=gig_url,
            niche_id="weakness-niche",
            run_id="legacy",
            db=session,
        )
        assert payload["source"] == "gig_quality_analysis"
        assert payload["video_absent"] is False
        assert payload["portfolio_absent"] is False
    finally:
        session.close()


def test_weakness_does_not_use_analysis_from_different_run() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        gig_url = "https://www.fiverr.com/gigs/1"
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id="weakness-niche",
                run_id="older-run",
                rubric_score=95.0,
                video_absent=False,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=[],
            )
        )
        session.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=gig_url,
                run_id="current-run",
                video_present=False,
                portfolio_count=0,
                analysis_complete=True,
            )
        )
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url=gig_url,
            niche_id="weakness-niche",
            run_id="current-run",
            db=session,
        )
        assert payload["source"] == "gig_quality_score"
        assert payload["video_absent"] is True
        assert payload["portfolio_absent"] is True
    finally:
        session.close()


def test_weakness_returns_empty_when_requested_run_has_no_rows() -> None:
    session = _new_session()
    try:
        _seed_keyword(session)
        session.add(
            GigQualityAnalysis(
                gig_url="https://www.fiverr.com/gigs/1",
                niche_id="weakness-niche",
                run_id="older-run",
                rubric_score=85.0,
                video_absent=True,
                portfolio_absent=True,
                description_thin=False,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=["NO_VIDEO", "NO_PORTFOLIO"],
            )
        )
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/gigs/1",
            niche_id="weakness-niche",
            run_id="current-run",
            db=session,
        )
        assert payload == {}
    finally:
        session.close()


def test_weakness_uses_niche_fallback_when_run_id_not_provided() -> None:
    session = _new_session()
    try:
        _seed_keyword(session)
        session.add(
            GigQualityAnalysis(
                gig_url="https://www.fiverr.com/gigs/1",
                niche_id="weakness-niche",
                run_id="run-stage11",
                rubric_score=74.0,
                video_absent=True,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=True,
                thumbnail_quality_flag=False,
                weakness_flags=["NO_VIDEO", "NO_FAQ"],
            )
        )
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/gigs/1",
            niche_id="weakness-niche",
            run_id="",
            db=session,
        )
        assert payload["source"] == "gig_quality_analysis"
        assert payload["weakness_penalty_score"] == 45.0
    finally:
        session.close()


def test_weakness_helper_returns_empty_for_blank_url_or_non_session_db() -> None:
    session = _new_session()
    try:
        assert get_gig_quality_weakness_input("", "weakness-niche", "legacy", session) == {}
    finally:
        session.close()
    assert get_gig_quality_weakness_input("https://www.fiverr.com/gigs/1", "weakness-niche", "legacy", {}) == {}


def test_resolve_weakness_flags_penalty_prefers_explicit_and_clamps() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    assert calculator._resolve_weakness_flags_penalty({"weakness_flag_penalty": 120.0}) == 100.0
    assert calculator._resolve_weakness_flags_penalty({"weakness_flag_penalty": -5.0}) == 0.0


def test_resolve_weakness_flags_penalty_averages_per_gig_flags() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    value = calculator._resolve_weakness_flags_penalty(
        {
            "weakness_flags_by_gig": [
                ["NO_VIDEO"],
                ["NO_PORTFOLIO", "NO_FAQ"],
            ]
        }
    )
    assert value == 32.5
    assert calculator._resolve_weakness_flags_penalty({"weakness_flags": ["NO_FAQ"]}) == 20.0


def test_penalty_no_flags_returns_zero() -> None:
    assert compute_weakness_penalty_from_flags([]) == 0.0


def test_penalty_normalizes_aliases_and_deduplicates() -> None:
    assert compute_weakness_penalty_from_flags(["video absent", "VIDEO_MISSING", "no-faq"]) == 45.0


def test_penalty_all_flags_returns_max() -> None:
    assert compute_weakness_penalty_from_flags(["NO_VIDEO", "NO_PORTFOLIO", "THIN_DESCRIPTION", "NO_FAQ"]) == 100.0


def test_penalty_single_flag_returns_correct_weight() -> None:
    assert compute_weakness_penalty_from_flags(["NO_PORTFOLIO"]) == 20.0
