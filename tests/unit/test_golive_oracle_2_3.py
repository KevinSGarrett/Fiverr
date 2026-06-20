"""Item 2.3: the staged go-live oracle must NOT fabricate PASS.

Stages 4/6/7 previously returned hardcoded PASS (Stage 7 passed even with 0
daily reports), so the system could "prove" 24/7 readiness without measuring
anything. They now return NOT_MEASURED until real measurement (item 5.7), and
NOT_MEASURED never advances the go-live gate.
"""
from __future__ import annotations

from automation.stage_executor import StageExecutor


def _ex() -> StageExecutor:
    return StageExecutor(controller=None, config={})


def test_stage_4_not_measured():
    r = _ex()._execute_stage_4()
    assert r["status"] == "NOT_MEASURED"
    assert r["status"] != "PASS"


def test_stage_6_not_measured():
    assert _ex()._execute_stage_6()["status"] == "NOT_MEASURED"


def test_stage_7_not_measured_even_with_zero_reports():
    r = _ex()._execute_stage_7()
    assert r["status"] == "NOT_MEASURED"
    # The real daily-report count is surfaced (here 0 in the isolated runner root)
    # but it must NOT be used to fabricate a PASS.
    assert r["daily_reports_collected"] == 0
    assert r["status"] != "PASS"


def test_not_measured_does_not_advance_gate(monkeypatch):
    ex = _ex()
    monkeypatch.setattr(ex, "get_current_stage", lambda: 4)
    assert ex.advance_if_ready() is False  # NOT_MEASURED stage must not advance
