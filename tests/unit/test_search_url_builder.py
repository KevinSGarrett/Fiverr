"""Unit tests for SRDI R1 search URL builder and strictness handling."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from src.collection.search_url_builder import (
    NICHE_CATEGORY_MAP,
    PRODUCTION_NICHES,
    SEARCH_STRICTNESS_COLUMN,
    UNCONSTRAINED_DEMAND_DEDUCTION,
    UNCONSTRAINED_NOTE,
    SearchStrictness,
    build_search_url,
    check_category_mapping_freshness,
    get_niche_mapping,
    run_validation_sweep,
    search_with_fallback,
)
from src.models import Keyword, Niche, SearchResult
from src.models.database import initialize_database
from src.scoring.demand import DemandScoreCalculator


def _build_session(tmp_path: Path, name: str):
    engine = initialize_database(database_url=f"sqlite:///{(tmp_path / name).as_posix()}")
    from sqlalchemy.orm import Session

    return Session(bind=engine)


def _seed_keyword(session, *, slug: str = "support_kb_readiness") -> int:
    niche = Niche(slug=slug, name=slug, category_path="programming-tech/search")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword=f"{slug} keyword",
        normalized_keyword=f"{slug} keyword",
    )
    session.add(keyword)
    session.commit()
    return keyword.id


@pytest.mark.parametrize("niche", PRODUCTION_NICHES)
def test_fiverr_search_url_always_includes_category_filter_for_production_niches(niche: str) -> None:
    mapping = NICHE_CATEGORY_MAP[niche]
    subcategory_url = build_search_url("test keyword", niche, SearchStrictness.SUBCATEGORY)
    category_url = build_search_url("test keyword", niche, SearchStrictness.CATEGORY)
    none_url = build_search_url("test keyword", niche, SearchStrictness.NONE)

    assert f"category_id={mapping.fiverr_category_id}" in subcategory_url
    assert f"sub_category={mapping.search_url_param.split('sub_category=')[1]}" in subcategory_url
    assert f"category_id={mapping.fallback_category_id}" in category_url
    assert "sub_category=" not in category_url
    assert "category_id=" not in none_url
    assert "sub_category=" not in none_url


def test_build_search_url_unknown_niche_returns_none_and_warns(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        url = build_search_url("kw", "not_a_real_niche", SearchStrictness.SUBCATEGORY)
    assert "category_id=" not in url
    assert "sub_category=" not in url
    assert any("niche" in record.message.lower() for record in caplog.records)


def test_build_search_url_treats_empty_or_none_niche_as_unknown(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        empty_url = build_search_url("kw", "", SearchStrictness.SUBCATEGORY)
        none_url = build_search_url("kw", None, SearchStrictness.SUBCATEGORY)
    assert "category_id=" not in empty_url
    assert "category_id=" not in none_url
    assert len(caplog.records) >= 2


@pytest.mark.parametrize("page,expected_offset", [(1, 0), (2, 16), (3, 32)])
def test_build_search_url_page_offset(page: int, expected_offset: int) -> None:
    url = build_search_url("kw", "python_automation", SearchStrictness.SUBCATEGORY, page=page)
    assert f"offset={expected_offset}" in url


@pytest.mark.parametrize(
    "keyword,encoded_fragment",
    [
        ("n8n & python", "n8n%20%26%20python"),
        ("c++/node.js", "c%2B%2B%2Fnode.js"),
        ("100% done", "100%25%20done"),
        ("naive cafe", "naive%20cafe"),
        ("", "query="),
    ],
)
def test_build_search_url_keyword_encoding(keyword: str, encoded_fragment: str) -> None:
    url = build_search_url(keyword, "python_automation", SearchStrictness.NONE)
    assert encoded_fragment in url


def test_build_search_url_accepts_very_long_keyword() -> None:
    keyword = "automation " * 200
    url = build_search_url(keyword, "python_automation", SearchStrictness.SUBCATEGORY)
    assert "query=" in url
    assert len(url) > 100


def test_search_with_fallback_returns_subcategory_when_threshold_met() -> None:
    calls: list[str] = []

    def collect_fn(url: str) -> list[str]:
        calls.append(url)
        return ["a", "b", "c", "d", "e"]

    results, strictness = search_with_fallback("kw", "python_automation", {}, collect_fn)
    assert strictness == SearchStrictness.SUBCATEGORY
    assert len(results) == 5
    assert len(calls) == 1


def test_search_with_fallback_returns_category_after_subcategory_shortfall() -> None:
    calls = {"count": 0}

    def collect_fn(_url: str) -> list[str]:
        calls["count"] += 1
        if calls["count"] == 1:
            return ["one"]
        return ["a", "b", "c", "d", "e"]

    results, strictness = search_with_fallback("kw", "python_automation", {}, collect_fn)
    assert strictness == SearchStrictness.CATEGORY
    assert len(results) == 5
    assert calls["count"] == 2


def test_search_with_fallback_degrades_to_none_when_needed() -> None:
    calls = {"count": 0}

    def collect_fn(_url: str) -> list[str]:
        calls["count"] += 1
        return [] if calls["count"] < 3 else ["a", "b", "c", "d", "e"]

    results, strictness = search_with_fallback("kw", "python_automation", {}, collect_fn)
    assert strictness == SearchStrictness.NONE
    assert len(results) == 5
    assert calls["count"] == 3


def test_search_with_fallback_honors_custom_threshold() -> None:
    def collect_fn(_url: str) -> list[str]:
        return ["a", "b", "c"]

    results, strictness = search_with_fallback(
        "kw",
        "python_automation",
        {"min_result_threshold": 3},
        collect_fn,
    )
    assert strictness == SearchStrictness.SUBCATEGORY
    assert len(results) == 3


def test_search_with_fallback_empty_everywhere_returns_none() -> None:
    def collect_fn(_url: str) -> list[str]:
        return []

    results, strictness = search_with_fallback("kw", "python_automation", {}, collect_fn)
    assert strictness == SearchStrictness.NONE
    assert results == []


def test_search_with_fallback_collect_errors_continue_to_next_tier() -> None:
    calls = {"count": 0}

    def collect_fn(_url: str) -> list[str]:
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("temporary fetch error")
        return ["a", "b", "c", "d", "e"]

    results, strictness = search_with_fallback("kw", "python_automation", {}, collect_fn)
    assert strictness == SearchStrictness.NONE
    assert len(results) == 5


def test_check_category_mapping_freshness_before_due(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.collection.search_url_builder as builder

    monkeypatch.setattr(builder, "_today", lambda: date(2026, 6, 1))
    assert check_category_mapping_freshness() is False


def test_today_helper_returns_date_instance() -> None:
    import src.collection.search_url_builder as builder

    assert isinstance(builder._today(), date)


def test_check_category_mapping_freshness_due_logs_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import src.collection.search_url_builder as builder

    monkeypatch.setattr(builder, "_today", lambda: date(2026, 9, 1))
    with caplog.at_level(logging.WARNING):
        assert check_category_mapping_freshness() is True
    assert any("validation is due" in record.message.lower() for record in caplog.records)


def test_get_niche_mapping_returns_none_for_unknown() -> None:
    assert get_niche_mapping("missing") is None


def test_niche_category_map_contains_all_expected_niches() -> None:
    assert len(PRODUCTION_NICHES) == 9
    for niche in PRODUCTION_NICHES:
        mapping = NICHE_CATEGORY_MAP[niche]
        assert mapping.fiverr_category_id
        assert mapping.fiverr_subcategory_id
        assert "category_id=" in mapping.search_url_param
        assert mapping.fallback_category_id


def test_sweep_cli_reports_recommendation_per_niche(capsys: pytest.CaptureFixture[str]) -> None:
    def collector(url: str) -> int:
        return 8 if "sub_category=" in url else 10

    rows = run_validation_sweep(("python_automation",), count_collector=collector)
    captured = capsys.readouterr().out
    assert len(rows) == 1
    assert rows[0]["recommended_strictness"] == SearchStrictness.SUBCATEGORY.value
    assert "python_automation" in captured
    assert "DL-207 sweep summary complete" in captured


def test_sweep_skips_unknown_niche_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        rows = run_validation_sweep(("unknown_niche",), count_collector=lambda _url: 1)
    assert rows == []
    assert any("skipping unknown niche" in record.message.lower() for record in caplog.records)


def test_default_collector_uses_total_result_count_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.collection.search_url_builder as builder

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"<html></html>"

    class _Parsed:
        total_result_count = 77
        gig_cards = [1, 2]

    monkeypatch.setattr(builder, "urlopen", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(builder, "parse_search_results_from_html", lambda _html: _Parsed())
    assert builder._default_count_collector("https://example.com") == 77


def test_default_collector_falls_back_to_gig_card_count(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.collection.search_url_builder as builder

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"<html></html>"

    class _Parsed:
        total_result_count = None
        gig_cards = [1, 2, 3]

    monkeypatch.setattr(builder, "urlopen", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(builder, "parse_search_results_from_html", lambda _html: _Parsed())
    assert builder._default_count_collector("https://example.com") == 3


def test_build_session_opener_primes_session_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.collection.search_url_builder as builder

    calls: dict[str, int] = {"open": 0, "install": 0}

    class _Ctx:
        def __enter__(self) -> _Ctx:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    class _Opener:
        def open(self, _request: object, timeout: int = 30) -> _Ctx:
            calls["open"] += 1
            assert timeout == 30
            return _Ctx()

    opener = _Opener()
    monkeypatch.setattr(builder, "build_opener", lambda *_args, **_kwargs: opener)
    monkeypatch.setattr(builder, "install_opener", lambda _opener: calls.__setitem__("install", calls["install"] + 1))

    built = builder._build_session_opener()
    assert built is opener
    assert calls["open"] == 1
    assert calls["install"] == 1


def test_run_validation_sweep_logs_both_collector_failures(caplog: pytest.LogCaptureFixture) -> None:
    def collector(url: str) -> int:
        if "sub_category=" in url:
            raise RuntimeError("forced constrained failure")
        raise RuntimeError("forced unconstrained failure")

    with caplog.at_level(logging.WARNING):
        rows = run_validation_sweep(("python_automation",), count_collector=collector)

    assert len(rows) == 1
    row = rows[0]
    assert row["constrained_count"] == 0
    assert row["unconstrained_count"] == 0
    assert row["recommended_strictness"] == SearchStrictness.NONE.value
    assert any("sweep constrained fetch failed" in record.message.lower() for record in caplog.records)
    assert any("sweep unconstrained fetch failed" in record.message.lower() for record in caplog.records)


def test_resolve_threshold_defaults_for_invalid_inputs() -> None:
    import src.collection.search_url_builder as builder

    assert builder._resolve_threshold(None) == 5
    assert builder._resolve_threshold({"min_result_threshold": "invalid"}) == 5


def test_main_noop_without_sweep(capsys: pytest.CaptureFixture[str]) -> None:
    import src.collection.search_url_builder as builder

    assert builder.main([]) == 0
    assert "No action specified. Use --sweep." in capsys.readouterr().out


def test_main_sweep_single_niche(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.collection.search_url_builder as builder

    captured: dict[str, tuple[str, ...]] = {}

    def _fake_sweep(niches: tuple[str, ...], **_kwargs: object) -> list[dict[str, object]]:
        captured["niches"] = niches
        return []

    monkeypatch.setattr(builder, "run_validation_sweep", _fake_sweep)
    assert builder.main(["--sweep", "--niches", "python_automation"]) == 0
    assert captured["niches"] == ("python_automation",)


def test_main_sweep_all_niches(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.collection.search_url_builder as builder

    captured: dict[str, tuple[str, ...]] = {}

    def _fake_sweep(niches: tuple[str, ...], **_kwargs: object) -> list[dict[str, object]]:
        captured["niches"] = niches
        return []

    monkeypatch.setattr(builder, "run_validation_sweep", _fake_sweep)
    assert builder.main(["--sweep", "--niches", "all"]) == 0
    assert captured["niches"] == builder.PRODUCTION_NICHES


def test_search_strictness_used_persisted_on_new_searchresult(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_strictness_persist.db")
    try:
        keyword_id = _seed_keyword(session)
        row = SearchResult(
            keyword_id=keyword_id,
            run_id="run-r1-new",
            page_collected=1,
            total_result_count=42,
            search_strictness_used=SearchStrictness.CATEGORY.value,
        )
        session.add(row)
        session.commit()
        fetched = session.query(SearchResult).filter_by(run_id="run-r1-new").one()
        assert fetched.search_strictness_used == SearchStrictness.CATEGORY.value
    finally:
        session.close()


def test_legacy_searchresult_strictness_remains_null(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_strictness_legacy.db")
    try:
        keyword_id = _seed_keyword(session, slug="python_automation")
        row = SearchResult(
            keyword_id=keyword_id,
            run_id="run-legacy",
            page_collected=1,
            total_result_count=10,
            search_strictness_used=None,
        )
        session.add(row)
        session.commit()
        fetched = session.query(SearchResult).filter_by(run_id="run-legacy").one()
        assert fetched.search_strictness_used is None
    finally:
        session.close()


def test_unconstrained_search_result_applies_demand_confidence_deduction(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "demand_unconstrained.db")
    try:
        keyword_id = _seed_keyword(session, slug="support_kb_readiness")
        session.add(
            SearchResult(
                keyword_id=keyword_id,
                run_id="run-post-r1-none",
                page_collected=1,
                total_result_count=120,
                search_strictness_used=SearchStrictness.NONE.value,
            )
        )
        session.commit()

        result = DemandScoreCalculator().calculate(keyword_id=keyword_id, db=session)

        assert result.confidence_breakdown["unconstrained_search"] == UNCONSTRAINED_DEMAND_DEDUCTION
        assert SEARCH_STRICTNESS_COLUMN in " ".join(result.source_evidence)
        component = result.score_components["unconstrained_search"]
        assert component.note == UNCONSTRAINED_NOTE
    finally:
        session.close()


def test_unconstrained_deduction_exempt_for_legacy_null_and_constrained_rows(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "demand_legacy_constrained.db")
    try:
        legacy_keyword_id = _seed_keyword(session, slug="python_automation")
        constrained_keyword_id = _seed_keyword(session, slug="mcp_ai_agent")

        session.add(
            SearchResult(
                keyword_id=legacy_keyword_id,
                run_id="run-legacy-null",
                page_collected=1,
                total_result_count=95,
                search_strictness_used=None,
            )
        )
        session.add(
            SearchResult(
                keyword_id=constrained_keyword_id,
                run_id="run-constrained-subcategory",
                page_collected=1,
                total_result_count=95,
                search_strictness_used=SearchStrictness.SUBCATEGORY.value,
            )
        )
        session.commit()

        legacy_result = DemandScoreCalculator().calculate(keyword_id=legacy_keyword_id, db=session)
        constrained_result = DemandScoreCalculator().calculate(keyword_id=constrained_keyword_id, db=session)

        assert "unconstrained_search" not in legacy_result.confidence_breakdown
        assert "unconstrained_search" not in constrained_result.confidence_breakdown
    finally:
        session.close()


def test_demand_deduction_isolated_from_non_demand_components() -> None:
    calculator = DemandScoreCalculator()
    payload: dict[int, dict[str, Any]] = {
        999: {
            "total_result_count": 1000,
            "autocomplete_position": 2,
            "trends_12mo_score": 50,
            "reddit_demand_intent_score": 7,
            SEARCH_STRICTNESS_COLUMN: SearchStrictness.NONE.value,
        }
    }

    class _DB:
        def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
            return payload[keyword_id]

    result = calculator.calculate(999, _DB())
    assert result.score_components["fiverr_count"].weight == 0.50
    assert result.score_components["autocomplete"].weight == 0.20
    assert result.score_components["google_trends"].weight == 0.20
    assert result.score_components["reddit_intent"].weight == 0.10
    assert result.confidence_breakdown["unconstrained_search"] == UNCONSTRAINED_DEMAND_DEDUCTION
