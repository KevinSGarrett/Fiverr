"""Agent F branch-coverage supplements for weakness scoring."""

from __future__ import annotations

import builtins
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from src.models import Gig, GigQualityAnalysis, KeywordScore, SearchResult
from src.scoring import weakness as weakness_module
from src.scoring.weakness import (
    GigQualityWeaknessScoreCalculator,
    aggregate_overall_weakness_scores,
)
from tests.unit.test_scoring_weakness_gqs import (
    _insert_gqa_row,
    _new_session,
    _seed_run_scoped_keyword,
)


def test_aggregate_overall_weakness_scores_empty_returns_none() -> None:
    assert aggregate_overall_weakness_scores([]) is None


def test_load_signals_mapping_non_mapping_payload_returns_empty() -> None:
    class _WeirdMapping(Mapping):
        def __getitem__(self, key: object) -> object:
            raise KeyError(key)

        def __iter__(self):  # type: ignore[no-untyped-def]
            return iter(())

        def __len__(self) -> int:
            return 0

        def get(self, _key: object, _default: object = None) -> object:  # type: ignore[override]
            return 123

    calculator = GigQualityWeaknessScoreCalculator()
    assert calculator._load_signals(42, _WeirdMapping()) == {}


def test_extract_top_card_urls_skips_invalid_cards() -> None:
    top_results = [
        type("Row", (), {"gig_cards": [{"gig_url": "  ", "position": 1}, {"gig_url": "https://a", "position": "2"}]})(),
        type("Row", (), {"gig_cards": [{"gig_url": "https://b", "position": "bad"}]})(),
    ]
    urls = GigQualityWeaknessScoreCalculator._extract_top_card_urls(top_results, 10)
    assert urls == ["https://a", "https://b"]


def test_load_signals_uses_active_run_when_rank_rows_missing() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-no-rank")
        row = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).first()
        assert row is not None
        row.rank = None
        row.created_at = datetime.now(UTC)
        session.commit()
        _insert_gqa_row(session, gig_url=gig_url, run_id="active-no-rank", rubric_score=52.0)

        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 4.8
    finally:
        session.close()


def test_load_signals_uses_keyword_niche_id_when_slug_missing() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="niche-id-fallback")
        keyword = (
            session.query(weakness_module.Keyword)
            .filter(weakness_module.Keyword.id == keyword_id)
            .first()
        )
        assert keyword is not None and keyword.niche is not None
        keyword.niche.slug = " "
        session.commit()

        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="niche-id-fallback",
            rubric_score=40.0,
            weakness_flags=["NO_FAQ"],
        )
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value > 0.0
    finally:
        session.close()


def test_load_signals_skips_duplicate_and_empty_inputs() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="dup-inputs")
        row = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).first()
        assert row is not None
        row.gig_cards = [
            {"gig_url": gig_url, "position": 1},
            {"gig_url": gig_url, "position": 2},
            {"gig_url": " ", "position": 3},
        ]
        session.commit()

        _insert_gqa_row(session, gig_url=gig_url, run_id="dup-inputs", rubric_score=35.0)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 6.5
    finally:
        session.close()


def test_load_signals_swallows_weakness_input_exception(monkeypatch) -> None:
    session = _new_session()
    try:
        keyword_id, _ = _seed_run_scoped_keyword(session, active_run_id="except-path")

        def _boom(*_args: object, **_kwargs: object) -> dict[str, object]:
            raise RuntimeError("forced weakness input failure")

        monkeypatch.setattr(weakness_module, "get_gig_quality_weakness_input", _boom)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert "overall_weakness_score_avg" not in signals
    finally:
        session.close()


def test_resolve_weakness_input_run_id_import_failure_returns_active(monkeypatch) -> None:
    session = _new_session()
    try:
        _seed_run_scoped_keyword(session, active_run_id="import-fail-run")
        calculator = GigQualityWeaknessScoreCalculator()
        original_import = builtins.__import__

        def _patched_import(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            if name == "src.models.market":
                raise ImportError("forced import failure")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _patched_import)
        resolved = calculator._resolve_weakness_input_run_id(
            session,
            active_run_id="import-fail-run",
            top_card_urls=["https://www.fiverr.com/gigs/anything"],
            top_results=[],
        )
        assert resolved == "import-fail-run"
    finally:
        session.close()


def test_historical_weakness_uses_stable_prior_when_latest_extreme() -> None:
    session = _new_session()
    try:
        keyword_id, _ = _seed_run_scoped_keyword(session, active_run_id="hist-extreme")
        session.add(
            KeywordScore(
                keyword_id=keyword_id,
                final_score=50.0,
                weakness_score=100.0,
                score_components={},
                tag="MONITOR",
                scored_at=datetime.now(UTC) + timedelta(seconds=1),
            )
        )
        session.add(
            KeywordScore(
                keyword_id=keyword_id,
                final_score=50.0,
                weakness_score=53.52,
                score_components={},
                tag="MONITOR",
                scored_at=datetime.now(UTC),
            )
        )
        session.commit()

        resolved = GigQualityWeaknessScoreCalculator._resolve_historical_weakness_score(keyword_id, session)
        assert resolved == 53.52
    finally:
        session.close()


def test_resolve_weakness_input_run_id_skips_non_matching_rows() -> None:
    session = _new_session()
    try:
        keyword_id, _ = _seed_run_scoped_keyword(session, active_run_id="active-target")
        session.add(
            Gig(
                gig_url="https://www.fiverr.com/gigs/unrelated",
                keyword_id=keyword_id,
                run_id="unrelated-run",
                seller_username="unrelated_seller",
                metadata_json={},
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url="https://www.fiverr.com/gigs/unrelated",
                niche_id="run-fallback-niche",
                run_id="unrelated-run",
                rubric_score=45.0,
                video_absent=False,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=False,
                thumbnail_quality_flag=False,
                weakness_flags=[],
            )
        )
        session.commit()

        resolved = GigQualityWeaknessScoreCalculator()._resolve_weakness_input_run_id(
            session,
            active_run_id="active-target",
            top_card_urls=["https://www.fiverr.com/gigs/fallback-target"],
            top_results=[],
        )
        assert resolved == "active-target"
    finally:
        session.close()
