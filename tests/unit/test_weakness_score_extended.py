"""Extended weakness score coverage tests for Cycle 047."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from sqlalchemy.orm import Session
from src.models import Gig, GigQualityAnalysis, Keyword, Niche, SearchResult, Seller
from src.scoring.weakness import (
    GigQualityWeaknessScoreCalculator,
    _normalize_weakness_flags,
    compute_weakness_penalty_from_flags,
    get_gig_quality_weakness_input,
)
from tests.unit.test_scoring_db_integration import (
    _seed_keyword_data_with_unlinked_page_cards,
    _seed_keyword_data_without_search_links,
    _session,
)


def _seed_keyword_with_stage11_rows(session: Session) -> int:
    niche = Niche(slug="weakness-stage11", name="Weakness Stage11", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="weakness stage11 keyword",
        normalized_keyword="weakness stage11 keyword",
    )
    session.add(keyword)
    session.flush()

    urls = [
        "https://www.fiverr.com/weakness/stage11-one",
        "https://www.fiverr.com/weakness/stage11-two",
        "https://www.fiverr.com/weakness/stage11-three",
    ]
    ows_values = [2.0, 8.0, 9.0]
    flags = [
        ["video_absent"],
        ["video_absent", "faq_absent"],
        ["video_absent", "faq_absent", "portfolio_absent"],
    ]

    for idx, (gig_url, rubric_ows, weakness_flags) in enumerate(zip(urls, ows_values, flags, strict=True), start=1):
        seller = Seller(seller_handle=f"weakness_ext_seller_{idx}", level="Level 1")
        session.add(seller)
        session.flush()
        gig = Gig(
            gig_url=gig_url,
            keyword_id=keyword.id,
            run_id="weakness-stage11-run",
            seller_id=seller.id,
            seller_username=seller.seller_handle,
            title=f"Weakness Stage11 Gig {idx}",
            normalized_title=f"weakness stage11 gig {idx}",
            position=idx,
            starting_price=40.0 + idx,
            review_count=5 + idx,
            metadata_json={"has_video": idx != 1, "has_portfolio": idx == 3},
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="weakness-stage11-run",
                rank=idx,
                gig_id=gig.id,
                title=f"Stage11 Result {idx}",
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id=niche.slug,
                run_id="weakness-stage11-run",
                rubric_score=100.0 - (rubric_ows * 10.0),
                video_absent="video_absent" in weakness_flags,
                portfolio_absent="portfolio_absent" in weakness_flags,
                description_thin=False,
                faq_absent="faq_absent" in weakness_flags,
                thumbnail_quality_flag=False,
                weakness_flags=weakness_flags,
            )
        )

    session.commit()
    return keyword.id


def test_weakness_video_absence_rate_computation_with_multiple_top_cards() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_unlinked_page_cards(session)
    try:
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["top10_has_video"] == [False, True]
        assert signals["video_absence_rate"] == 0.5
    finally:
        session.close()


def test_weakness_portfolio_absence_detection_for_all_missing() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(
        9901,
        {9901: {"top10_has_video": [True, True, True], "top10_has_portfolio": [False, False, False]}},
    )
    assert result.score_components["portfolio_absence_rate"].value == 100.0


def test_weakness_flag_penalty_calculation_with_known_flags() -> None:
    penalty = compute_weakness_penalty_from_flags(["video_absent", "faq_absent", "portfolio_absent"])
    assert penalty == 65.0


def test_weakness_overall_weakness_score_aggregation_from_stage11() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_with_stage11_rows(session)
    try:
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 6.3333
    finally:
        session.close()


def test_weakness_red_flag_boost_from_high_severity_flags() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_with_stage11_rows(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_components["weakness_flags_penalty"].value > 0.0
    finally:
        session.close()


def test_weakness_exploitable_distribution_when_variance_high() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_with_stage11_rows(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        # High variance OWS values should produce a non-trivial weakness score.
        assert result.score_value >= 50.0
    finally:
        session.close()


def test_weakness_graceful_fallback_when_zero_stage11_rows() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
    finally:
        session.close()


def test_weakness_graceful_fallback_when_zero_linked_gigs() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_unlinked_page_cards(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.source_evidence
    finally:
        session.close()


def test_weakness_normalize_flags_handles_non_list_and_non_string_entries() -> None:
    assert _normalize_weakness_flags("bad-input") == []
    assert _normalize_weakness_flags(["video_absent", 1, None]) == ["NO_VIDEO"]


def test_weakness_get_input_uses_unscoped_query_when_no_run_or_niche() -> None:
    session = next(_session())
    try:
        niche = Niche(slug="weakness-unscoped", name="Weakness Unscoped", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        row = GigQualityAnalysis(
            gig_url="https://www.fiverr.com/weakness/unscoped",
            niche_id=niche.slug,
            run_id="any-run",
            rubric_score=70.0,
            video_absent=True,
            portfolio_absent=False,
            description_thin=False,
            faq_absent=False,
            thumbnail_quality_flag=False,
            weakness_flags=["video_absent"],
        )
        session.add(row)
        session.commit()

        payload = get_gig_quality_weakness_input(
            gig_url="https://www.fiverr.com/weakness/unscoped",
            niche_id="",
            run_id="",
            db=session,
        )
        assert payload["source"] == "gig_quality_analysis"
    finally:
        session.close()


def test_weakness_helper_paths_for_async_text_and_float_failures() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    assert calculator._as_float("not-a-number") is None
    assert calculator._extract_llm_text("plain-response") == "plain-response"
    assert calculator._normalize_gig_url_identity(123) is None
    assert calculator._normalize_gig_url_identity("   ") is None
    assert calculator._normalize_gig_url_identity("https://www.fiverr.com?x=1") == "https://www.fiverr.com"


def test_weakness_run_async_works_when_event_loop_already_running() -> None:
    calculator = GigQualityWeaknessScoreCalculator()

    async def _inside() -> float | None:
        return calculator._run_async(calculator._get_llm_numeric_score("prompt", "gpt-4o", _FakeLLM("6.5"), None))

    assert asyncio.run(_inside()) == 6.5


def test_weakness_numeric_and_absence_resolvers_cover_edge_paths() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    assert calculator._normalize_weakness_count(0.0) == 0.0
    assert calculator._absence_rate_from_presence([None, None]) is None
    assert calculator._resolve_absence_rate({"top10_has_video": [None, None]}, "video_absence_rate", "top10_has_video") is None


def test_weakness_complete_with_optional_cache_falls_back_on_type_error() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    payload = calculator._complete_with_optional_cache(_LegacyLLM(), "prompt", "gpt-4o", cache={})
    assert payload.text == "5.0"


class _FakeLLM:
    def __init__(self, text: str) -> None:
        self._text = text

    def complete(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(text=self._text)


class _LegacyLLM:
    @staticmethod
    def complete(prompt: str, model: str) -> SimpleNamespace:
        del prompt, model
        return SimpleNamespace(text="5.0")


def test_weakness_fallback_run_id_path_is_exercised() -> None:
    from tests.unit.test_scoring_weakness_gqs import (
        _insert_gqa_row,
        _new_session,
        _seed_run_scoped_keyword,
    )

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
    from tests.unit.test_scoring_weakness_gqs import (
        _insert_gqa_row,
        _new_session,
        _seed_run_scoped_keyword,
    )

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
    from tests.unit.test_scoring_weakness_gqs import (
        _insert_gqa_row,
        _new_session,
        _seed_run_scoped_keyword,
    )

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


def test_weakness_kw3_niche_gets_weakness_score_via_fallback_run_id() -> None:
    """kw=3-equivalent: active run has no GQA; older run has Stage 11 rows."""
    from tests.unit.test_scoring_weakness_gqs import (
        _insert_gqa_row,
        _new_session,
        _seed_run_scoped_keyword,
    )

    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(
            session,
            active_run_id="cycle041_agentb_live_stage34",
            gig_url="https://www.fiverr.com/gigs/6b7f9d9b-979b-4f0e-98b0-2ab3f326e72c",
        )
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="cycle038_agentb_live",
            rubric_score=20.0,
            weakness_flags=["video_absent", "portfolio_absent"],
        )
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value > 0.0
    finally:
        session.close()
