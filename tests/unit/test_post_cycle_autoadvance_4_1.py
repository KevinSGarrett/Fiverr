"""ITEM 4.1 — Fix the post-cycle dead-end (auto-advance).

POST_AGENT review ALWAYS returns DRAFT_UNMERGED_PREVIEW (never "PASS"), so the
old `grade == "PASS"` gate dead-ended EVERY clean cycle at POST_CYCLE_FAIL. The
fix makes `not result.blocks_dispatch` the SINGLE advance predicate, shared by
the AGENT_COMPLETE and POST_CYCLE_PENDING tick branches (4.1-T1/T2).

These tests use a REAL PostCycleReviewResult + PostCycleFacts so the genuine
fact-based `blocks_dispatch` property is exercised (not a mocked bool).
"""
from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from automation import runner_paths
from automation.ai_cycle_controller import cli
from automation.post_cycle_review import (
    PostCycleFacts,
    PostCycleReviewResult,
    ReviewMode,
    ReviewResult,
)
from automation.state_writer import write_controller_state


@pytest.fixture(autouse=True)
def _clean_state():
    def _wipe():
        for n in ("controller_state.json", "tick_counters.json"):
            try:
                (runner_paths.state_dir() / n).unlink()
            except OSError:
                pass
    _wipe()
    yield
    _wipe()


@pytest.fixture
def no_drift(monkeypatch):
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": None})
    return monkeypatch


def _clean_facts(cycle: int) -> PostCycleFacts:
    return PostCycleFacts(
        cycle=cycle, mode=ReviewMode.POST_AGENT,
        local_ruff=True, local_mypy=True, local_pytest=True,
        ci_passed=True, local_coverage_pct=85.0,
        github_health_score=100, pr_expected=False,
    )


def _blocking_facts(cycle: int) -> PostCycleFacts:
    f = _clean_facts(cycle)
    f.local_pytest = False  # one hard-red fact -> blocks_dispatch True
    return f


def _review(cycle: int, *, blocking: bool,
            result: ReviewResult = ReviewResult.DRAFT_UNMERGED_PREVIEW) -> PostCycleReviewResult:
    facts = _blocking_facts(cycle) if blocking else _clean_facts(cycle)
    return PostCycleReviewResult(
        cycle=cycle, mode=ReviewMode.POST_AGENT, result=result, facts=facts,
    )


def _patch_review(monkeypatch, review: PostCycleReviewResult):
    import automation.post_cycle_review as pcr
    monkeypatch.setattr(pcr, "run_review",
                        lambda cycle, mode, **kwargs: review)


def _state() -> dict:
    return json.loads((runner_paths.state_dir() / "controller_state.json").read_text())


# ── core 4.1: clean POST_AGENT (DRAFT_UNMERGED_PREVIEW) advances ──────────────
def test_clean_post_agent_advances_when_no_pr(no_drift, monkeypatch):
    rev = _review(500, blocking=False)
    assert rev.blocks_dispatch is False  # real property, clean facts
    _patch_review(monkeypatch, rev)
    write_controller_state("AGENT_COMPLETE", cycle=500)  # no active_pr
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    # Old grade=="PASS" gate would have FAILed (grade is DRAFT_UNMERGED_PREVIEW).
    assert _state()["status"] == "POST_CYCLE_PASS"


def test_clean_post_agent_with_pr_goes_awaiting_ci(no_drift, monkeypatch):
    rev = _review(501, blocking=False)
    _patch_review(monkeypatch, rev)
    write_controller_state("AGENT_COMPLETE", cycle=501, pr=1501)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "AWAITING_CI_GREEN"  # 3.2 handoff, reached via 4.1


def test_hard_errors_block_even_with_clean_facts(no_drift, monkeypatch):
    # Codex P1: GATE 6/7 errors (baseline tampered / ScrapFly enabled) append to
    # result.errors without early-return; with clean facts the POST_AGENT fact
    # checks would otherwise pass. blocks_dispatch must honor errors -> FAIL.
    rev = _review(507, blocking=False)
    rev.errors.append("cycle037_live.db mtime changed — baseline tampered")
    assert rev.blocks_dispatch is True  # real property now honors errors
    _patch_review(monkeypatch, rev)
    write_controller_state("AGENT_COMPLETE", cycle=507, pr=1507)  # PR open
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    # Must NOT advance to the merge path despite the open PR + clean facts.
    assert _state()["status"] == "POST_CYCLE_FAIL"


def test_blocking_review_does_not_advance(no_drift, monkeypatch):
    rev = _review(502, blocking=True)
    assert rev.blocks_dispatch is True  # real property, red pytest
    _patch_review(monkeypatch, rev)
    write_controller_state("AGENT_COMPLETE", cycle=502)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "POST_CYCLE_FAIL"


def test_predicate_is_blocks_dispatch_not_grade(no_drift, monkeypatch):
    # Regression guard: a non-"PASS" grade with blocks_dispatch=False MUST advance
    # (the whole point of 4.1). If anyone reverts to grade-based gating, this fails.
    rev = _review(503, blocking=False, result=ReviewResult.DRAFT_UNMERGED_PREVIEW)
    assert rev.result.value != "PASS"
    assert rev.blocks_dispatch is False
    _patch_review(monkeypatch, rev)
    write_controller_state("AGENT_COMPLETE", cycle=503)
    CliRunner().invoke(cli, ["tick"])
    assert _state()["status"] == "POST_CYCLE_PASS"


# ── 4.2 Codex P2: skip local validation ONLY when a PR exists ─────────────────
@pytest.mark.parametrize("status", ["AGENT_COMPLETE", "POST_CYCLE_PENDING"])
def test_skip_local_validation_conditional_on_pr(no_drift, status, monkeypatch):
    import automation.post_cycle_review as pcr
    captured = {}

    def _fake(cycle, mode, pr_number=None, skip_local_validation=False):
        captured["pr"] = pr_number
        captured["skip"] = skip_local_validation
        return PostCycleReviewResult(cycle=cycle, mode=mode,
                                     result=ReviewResult.DRAFT_UNMERGED_PREVIEW,
                                     facts=_clean_facts(cycle))

    monkeypatch.setattr(pcr, "run_review", _fake)

    # With a PR: skip the local suite (CI gates downstream).
    write_controller_state(status, cycle=520, pr=1520)
    CliRunner().invoke(cli, ["tick"])
    assert captured["skip"] is True and captured["pr"] == 1520

    # With NO PR: must NOT skip (run the local suite — no downstream CI to gate).
    captured.clear()
    (runner_paths.state_dir() / "controller_state.json").unlink()
    write_controller_state(status, cycle=521)
    CliRunner().invoke(cli, ["tick"])
    assert captured["skip"] is False and not captured["pr"]


# ── 4.1-T2: POST_CYCLE_PENDING branch uses the SAME predicate ─────────────────
def test_post_cycle_pending_clean_advances(no_drift, monkeypatch):
    rev = _review(504, blocking=False)
    _patch_review(monkeypatch, rev)
    write_controller_state("POST_CYCLE_PENDING", cycle=504)
    CliRunner().invoke(cli, ["tick"])
    assert _state()["status"] == "POST_CYCLE_PASS"


def test_post_cycle_pending_with_pr_goes_awaiting_ci(no_drift, monkeypatch):
    rev = _review(505, blocking=False)
    _patch_review(monkeypatch, rev)
    write_controller_state("POST_CYCLE_PENDING", cycle=505, pr=1505)
    CliRunner().invoke(cli, ["tick"])
    assert _state()["status"] == "AWAITING_CI_GREEN"


def test_post_cycle_pending_blocking_fails(no_drift, monkeypatch):
    rev = _review(506, blocking=True)
    _patch_review(monkeypatch, rev)
    write_controller_state("POST_CYCLE_PENDING", cycle=506)
    CliRunner().invoke(cli, ["tick"])
    assert _state()["status"] == "POST_CYCLE_FAIL"
