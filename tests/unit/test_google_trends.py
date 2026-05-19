"""Unit tests for Workflow 6 Google Trends collection."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

import pandas as pd
import pytest
import src.collection.workflows.google_trends as google_trends_module
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models.market import Keyword
from src.models.niche import Niche


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


class _PacingStub:
    def __init__(self) -> None:
        self.wait = AsyncMock()
        self.pacing: dict[str, dict[str, float]] = {
            "google_trends": {
                "base_delay_seconds": 10.0,
                "rate_limit_pause_minutes": 10.0,
            }
        }


def _configure_workflow_mocks(
    monkeypatch: pytest.MonkeyPatch,
    *,
    dataframes: list[pd.DataFrame],
    errors: list[Exception | None] | None = None,
    keyword_ids: dict[str, int] | None = None,
) -> tuple[list[list[str]], list[dict[str, Any]], _PacingStub, AsyncMock]:
    payload_calls: list[list[str]] = []
    writes: list[dict[str, Any]] = []
    frame_queue = list(dataframes)
    error_queue = list(errors or [])

    class _FakeTrendReq:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def build_payload(self, *, kw_list: list[str], timeframe: str, geo: str) -> None:
            assert timeframe == "today 12-m"
            assert geo == ""
            payload_calls.append(list(kw_list))

        def interest_over_time(self) -> pd.DataFrame:
            if error_queue:
                next_error = error_queue.pop(0)
                if next_error is not None:
                    raise next_error
            if frame_queue:
                return frame_queue.pop(0)
            return pd.DataFrame()

        def related_queries(self) -> dict[str, Any]:
            return {}

        def related_topics(self) -> dict[str, Any]:
            return {}

    def _fake_write_external_signal(**kwargs: Any) -> None:
        writes.append(kwargs)

    def _fake_resolve(keyword_text: str, _db: Any) -> int | None:
        if keyword_ids is None:
            return 1
        return keyword_ids.get(keyword_text)

    sleep_mock = AsyncMock()
    pacing_manager = _PacingStub()

    monkeypatch.setattr(google_trends_module, "TrendReq", _FakeTrendReq)
    monkeypatch.setattr(google_trends_module, "write_external_signal", _fake_write_external_signal)
    monkeypatch.setattr(google_trends_module, "_resolve_keyword_id", _fake_resolve)
    monkeypatch.setattr(google_trends_module, "_write_trends_checkpoint", lambda **_kwargs: None)
    monkeypatch.setattr(google_trends_module.asyncio, "sleep", sleep_mock)

    return payload_calls, writes, pacing_manager, sleep_mock


def test_google_trends_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FailTrendReq:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise AssertionError("TrendReq should not be called in dry-run mode")

    monkeypatch.setattr(google_trends_module, "TrendReq", _FailTrendReq)

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-1",
            keywords=["one", "two"],
            run_id="run-1",
            db=None,
            pacing_manager=None,
            dry_run=True,
        )
    )

    assert result["dry_run"] is True
    assert result["keywords_processed"] == 0
    assert result["signals_written"] == 0


def test_google_trends_dry_run_default(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FailTrendReq:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise AssertionError("TrendReq should not be called when dry_run defaults to True")

    monkeypatch.setattr(google_trends_module, "TrendReq", _FailTrendReq)

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-1",
            keywords=["one"],
            run_id="run-2",
            db=None,
            pacing_manager=None,
        )
    )

    assert result["dry_run"] is True
    assert result["keywords_processed"] == 0


def test_google_trends_result_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [10, 20, 30]})],
        keyword_ids={"kw": 1},
    )

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-1",
            keywords=["kw"],
            run_id="run-3",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    required_keys = {
        "niche_id",
        "keywords_processed",
        "signals_written",
        "rate_limited",
        "dry_run",
    }
    assert required_keys.issubset(result.keys())


def test_google_trends_batches_keywords(monkeypatch: pytest.MonkeyPatch) -> None:
    keywords = [f"kw-{idx}" for idx in range(7)]
    first_df = pd.DataFrame({key: [10, 20, 30] for key in keywords[:5]})
    second_df = pd.DataFrame({key: [5, 15, 25] for key in keywords[5:]})
    keyword_ids = {key: idx + 1 for idx, key in enumerate(keywords)}

    payload_calls, _writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[first_df, second_df],
        keyword_ids=keyword_ids,
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-2",
            keywords=keywords,
            run_id="run-4",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert payload_calls == [keywords[:5], keywords[5:]]


def test_google_trends_empty_df(monkeypatch: pytest.MonkeyPatch) -> None:
    payload_calls, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame()],
        keyword_ids={"kw-a": 1, "kw-b": 2},
    )

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-3",
            keywords=["kw-a", "kw-b"],
            run_id="run-5",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert payload_calls == [["kw-a", "kw-b"]]
    assert result["signals_written"] == 2
    assert len(writes) == 2
    assert all(call["signal_value"] == 0.0 for call in writes)
    assert all(call["signal_json"]["no_data"] is True for call in writes)


def test_google_trends_writes_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [7, 14, 21]})],
        keyword_ids={"kw": 101},
    )

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-4",
            keywords=["kw"],
            run_id="run-6",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert result["signals_written"] == 1
    assert len(writes) == 1


def test_google_trends_signal_type(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [12, 24, 36]})],
        keyword_ids={"kw": 4},
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-5",
            keywords=["kw"],
            run_id="run-7",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert len(writes) == 1
    assert writes[0]["signal_type"] == google_trends_module.SIGNAL_GOOGLE_TRENDS


def test_google_trends_12mo_score_computed(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [10, 20, 30]})],
        keyword_ids={"kw": 8},
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-6",
            keywords=["kw"],
            run_id="run-8",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    call = writes[0]
    assert call["signal_value"] == pytest.approx(20.0)
    assert call["signal_json"]["trends_12mo_score"] == pytest.approx(20.0)


def test_google_trends_3mo_score_computed(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": list(range(1, 21))})],
        keyword_ids={"kw": 9},
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-7",
            keywords=["kw"],
            run_id="run-9",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert writes[0]["signal_json"]["trends_3mo_score"] == pytest.approx(14.0)


def test_google_trends_slope_rising(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [1, 3, 5, 7, 9]})],
        keyword_ids={"kw": 10},
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-8",
            keywords=["kw"],
            run_id="run-10",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert writes[0]["signal_json"]["trend_direction"] == "RISING"


def test_google_trends_slope_declining(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [9, 7, 5, 3, 1]})],
        keyword_ids={"kw": 11},
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-9",
            keywords=["kw"],
            run_id="run-11",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert writes[0]["signal_json"]["trend_direction"] == "DECLINING"


def test_google_trends_slope_flat(monkeypatch: pytest.MonkeyPatch) -> None:
    _, writes, pacing_manager, _ = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [5, 5, 5, 5, 5]})],
        keyword_ids={"kw": 12},
    )

    _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-10",
            keywords=["kw"],
            run_id="run-12",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert writes[0]["signal_json"]["trend_direction"] == "FLAT"


def test_google_trends_429_pauses(monkeypatch: pytest.MonkeyPatch) -> None:
    _payload_calls, _writes, pacing_manager, sleep_mock = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [1, 2, 3]})],
        errors=[RuntimeError("429 Too Many Requests"), None],
        keyword_ids={"kw": 13},
    )

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-11",
            keywords=["kw"],
            run_id="run-13",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert result["rate_limited"] is True
    assert result["rate_limit_count"] == 1
    assert sleep_mock.await_count == 1
    sleep_mock.assert_awaited_with(600.0)


def test_google_trends_429_three_times(monkeypatch: pytest.MonkeyPatch) -> None:
    _payload_calls, _writes, pacing_manager, sleep_mock = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[],
        errors=[
            RuntimeError("429 Too Many Requests"),
            RuntimeError("429 Too Many Requests"),
            RuntimeError("429 Too Many Requests"),
        ],
        keyword_ids={"kw-a": 21, "kw-b": 22, "kw-c": 23, "kw-d": 24, "kw-e": 25, "kw-f": 26},
    )

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-12",
            keywords=["kw-a", "kw-b", "kw-c", "kw-d", "kw-e", "kw-f"],
            run_id="run-14",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert result["rate_limited"] is True
    assert result["rate_limit_count"] == 3
    assert result["dead_lettered_batches"] >= 1
    assert sleep_mock.await_count == 2


def test_google_trends_missing_pytrends_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(google_trends_module, "TrendReq", None)

    with pytest.raises(RuntimeError):
        _run(
            google_trends_module.run_google_trends_collection(
                niche_id="niche-missing",
                keywords=["kw"],
                run_id="run-missing",
                db=None,
                pacing_manager=_PacingStub(),
                dry_run=False,
            )
        )


def test_google_trends_non_dataframe_and_missing_keyword_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _payload_calls, writes, pacing_manager, _sleep_mock = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame()],
        keyword_ids={"kw": None},
    )

    class _TrendReqNonFrame:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def build_payload(self, *, kw_list: list[str], timeframe: str, geo: str) -> None:
            _ = (kw_list, timeframe, geo)

        def interest_over_time(self) -> object:
            return object()

        def related_queries(self) -> dict[str, Any]:
            return {}

        def related_topics(self) -> dict[str, Any]:
            return {}

    monkeypatch.setattr(google_trends_module, "TrendReq", _TrendReqNonFrame)

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-no-id",
            keywords=["kw"],
            run_id="run-no-id",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert result["signals_written"] == 0
    assert writes == []


def test_google_trends_non_429_error_skips_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    _payload_calls, writes, pacing_manager, _sleep_mock = _configure_workflow_mocks(
        monkeypatch,
        dataframes=[pd.DataFrame({"kw": [1, 2, 3]})],
        errors=[RuntimeError("boom")],
        keyword_ids={"kw": 1},
    )

    result = _run(
        google_trends_module.run_google_trends_collection(
            niche_id="niche-error",
            keywords=["kw"],
            run_id="run-error",
            db=object(),
            pacing_manager=pacing_manager,
            dry_run=False,
        )
    )

    assert result["rate_limited"] is False
    assert result["signals_written"] == 0
    assert writes == []


def test_safe_pacing_wait_without_wait_fn() -> None:
    _run(google_trends_module._safe_pacing_wait(object(), "google_trends", dry_run=False))


def test_resolve_rate_limit_pause_minutes_from_getter() -> None:
    class _GetterPacing:
        def get_delay_config(self, _key: str) -> dict[str, Any]:
            return {"rate_limit_pause_minutes": 7}

    assert google_trends_module._resolve_rate_limit_pause_minutes(_GetterPacing()) == 7


def test_resolve_rate_limit_pause_minutes_default() -> None:
    assert google_trends_module._resolve_rate_limit_pause_minutes(object()) == 10


def test_increase_google_trends_delay_paths() -> None:
    class _NoMap:
        pacing = None

    class _WithMap:
        def __init__(self) -> None:
            self.pacing: dict[str, Any] = {}

    class _BadDelay:
        def __init__(self) -> None:
            self.pacing: dict[str, Any] = {"google_trends": {"base_delay_seconds": "invalid"}}

    google_trends_module._increase_google_trends_delay(_NoMap())

    with_map = _WithMap()
    google_trends_module._increase_google_trends_delay(with_map)
    assert with_map.pacing["google_trends"]["base_delay_seconds"] == pytest.approx(15.0)

    bad_delay = _BadDelay()
    google_trends_module._increase_google_trends_delay(bad_delay)
    assert bad_delay.pacing["google_trends"]["base_delay_seconds"] == pytest.approx(15.0)


def test_helper_timeout_slope_and_related_payload() -> None:
    assert google_trends_module._is_timeout_error(RuntimeError("request timeout")) is True
    assert google_trends_module._is_timeout_error(RuntimeError("other error")) is False
    assert google_trends_module._calculate_slope([1.0, 2.0]) == 0.0
    assert google_trends_module._safe_related_payload("invalid") == {}
    assert google_trends_module._extract_related_for_keyword({"kw": "invalid"}, "kw", top_limit=2) == []


def test_records_from_frame_variants() -> None:
    frame = pd.DataFrame([{"query": "q1", "value": 10}, {"query": "q2", "value": 20}])
    assert google_trends_module._records_from_frame(frame, limit=1) == [{"query": "q1", "value": 10}]

    class _BrokenFrame:
        def head(self, _limit: int) -> _BrokenFrame:
            raise RuntimeError("broken")

        def to_dict(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {}

    assert google_trends_module._records_from_frame(_BrokenFrame(), limit=2) == []
    assert google_trends_module._records_from_frame([{"a": 1}, {"b": 2}, "x"], limit=2) == [
        {"a": 1},
        {"b": 2},
    ]
    assert google_trends_module._records_from_frame("invalid", limit=2) == []


def test_write_trends_checkpoint_writes_file(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    google_trends_module._write_trends_checkpoint(
        run_id="run-checkpoint",
        niche_id="niche-checkpoint",
        batch_index=0,
        total_batches=2,
        keywords_total=9,
        keywords_complete=5,
        last_keyword="kw-last",
        signals_written=3,
        rate_limit_count=1,
    )

    checkpoint_path = (
        tmp_path
        / "data"
        / "checkpoints"
        / "run-checkpoint"
        / "stage06_trends_niche-checkpoint.json"
    )
    assert checkpoint_path.exists()
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert payload["stage"] == 6
    assert payload["signals_written"] == 3


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    maker = sessionmaker(bind=engine, future=True)
    return maker()


def test_resolve_keyword_id_found() -> None:
    db = _make_session()
    try:
        niche = Niche(slug="ai-agent", name="AI Agent", category_path="tech/ai")
        db.add(niche)
        db.commit()
        db.refresh(niche)

        keyword = Keyword(
            niche_id=int(niche.id),
            keyword="AI agent builder",
            normalized_keyword="ai agent builder",
        )
        db.add(keyword)
        db.commit()
        db.refresh(keyword)

        resolved = google_trends_module._resolve_keyword_id("AI agent builder", db)
        assert resolved == int(keyword.id)
    finally:
        db.close()


def test_resolve_keyword_id_missing() -> None:
    db = _make_session()
    try:
        niche = Niche(slug="ai-agent", name="AI Agent", category_path="tech/ai")
        db.add(niche)
        db.commit()

        resolved = google_trends_module._resolve_keyword_id("missing keyword", db)
        assert resolved is None
    finally:
        db.close()


def test_resolve_keyword_id_non_session_and_empty() -> None:
    assert google_trends_module._resolve_keyword_id("kw", object()) is None

    db = _make_session()
    try:
        assert google_trends_module._resolve_keyword_id("   ", db) is None
    finally:
        db.close()


def test_google_trends_workflow_wrapper_returns_external_module() -> None:
    workflow = google_trends_module.GoogleTrendsWorkflow()
    assert workflow.run() is google_trends_module._mod
