"""Audit [B] — cycle-to-cycle Jira convergence via a real AC-verification feed.

`build_ac_verification_for_cycle` computes per-story AC verification from the cycle's
agent-report evidence (conservative: a story converges only when ALL its AC are matched).
The MERGED tick branch feeds that to the AC-gated `on_cycle_merged` so the board converges
(cycle N+1 plans NEW work) WITHOUT ever false-closing unverified stories, and is
best-effort (a Jira/verify failure never blocks the post-merge advance).
"""
from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

import automation.jira_client as jc
import automation.jira_sync as js
from automation import runner_paths
from automation.ai_cycle_controller import cli
from automation.state_writer import write_controller_state


# ── the feed: build_ac_verification_for_cycle ──────────────────────────────────
def test_feed_all_ac_matched_in_evidence(monkeypatch):
    monkeypatch.setattr(jc, "get_issue", lambda k: {"fields": {"description":
        "- The scraper must collect gig data\n- Score niches across dimensions"}})
    res = js.build_ac_verification_for_cycle(
        ["SCRUM-1"], "the scraper collects gig data and scores niches across dimensions")
    assert res["SCRUM-1"]["unverified"] == []          # all AC matched
    assert len(res["SCRUM-1"]["verified"]) == 2


def test_feed_unmatched_ac_left_unverified(monkeypatch):
    monkeypatch.setattr(jc, "get_issue", lambda k: {"fields": {"description":
        "- The scraper must collect gig data\n- Render the Streamlit dashboard charts"}})
    res = js.build_ac_verification_for_cycle(
        ["SCRUM-1"], "the scraper collects gig data")  # 2nd AC NOT in evidence
    assert res["SCRUM-1"]["unverified"], "an unmatched AC must stay unverified (blocked)"


def test_feed_fail_closed_on_jira_error(monkeypatch):
    def _boom(k):
        raise RuntimeError("jira down")
    monkeypatch.setattr(jc, "get_issue", _boom)
    res = js.build_ac_verification_for_cycle(["SCRUM-1"], "evidence")
    assert res["SCRUM-1"]["verified"] == []
    assert res["SCRUM-1"]["unverified"], "fail-closed: a fetch error must NOT yield Done"


# ── the MERGED-branch wiring ───────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    def _wipe():
        for n in ("controller_state.json", "tick_counters.json"):
            try:
                (runner_paths.state_dir() / n).unlink()
            except OSError:
                pass
        try:
            (runner_paths.locks_dir() / "tick.lock").unlink()
        except OSError:
            pass
    _wipe()
    import automation.cycle_authority as ca
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked", lambda *a, **k: None)
    monkeypatch.setattr(nr, "notify_info", lambda *a, **k: None)
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": None})
    yield
    _wipe()


def _state() -> dict:
    return json.loads((runner_paths.state_dir() / "controller_state.json").read_text())


def test_merged_feeds_ac_results_then_advances(monkeypatch):
    import automation.jira_client as jc
    captured = {}
    # Codex P1: keys now come from the board's active (In Progress/In Review) stories,
    # NOT a hard-coded wave. Done stories are excluded; only active scope is synced.
    monkeypatch.setattr(jc, "board_inventory_all", lambda *a, **k: {"issues": [
        {"key": "SCRUM-1", "status": "In Review"},
        {"key": "SCRUM-2", "status": "Done"},        # excluded (not active)
        {"key": "SCRUM-3", "status": "To Do"},       # excluded (not active)
    ]})
    monkeypatch.setattr(js, "build_ac_verification_for_cycle",
                        lambda keys, ev: {"SCRUM-1": {"verified": ["AC1"], "unverified": []}})

    def _ocm(cycle, sha, keys, ac_verification_results=None):
        captured["ac"] = ac_verification_results
        captured["keys"] = list(keys)
        return [{"key": "SCRUM-1", "status": "ok"}]

    monkeypatch.setattr(js, "on_cycle_merged", _ocm)
    write_controller_state("MERGED", cycle=84, pr=1484)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    # The AC feed was passed through (not None) and the cycle advanced.
    assert captured["ac"] == {"SCRUM-1": {"verified": ["AC1"], "unverified": []}}
    assert captured["keys"] == ["SCRUM-1"]
    assert _state()["status"] == "POST_CYCLE_PASS"


def test_merged_advances_even_if_jira_raises(monkeypatch):
    import automation.jira_client as jc
    monkeypatch.setattr(jc, "board_inventory_all", lambda *a, **k: {"issues": [
        {"key": "SCRUM-9", "status": "In Progress"}]})
    monkeypatch.setattr(js, "build_ac_verification_for_cycle",
                        lambda keys, ev: {"SCRUM-9": {"verified": [], "unverified": ["AC1"]}})

    def _boom(*a, **k):
        raise RuntimeError("jira 503")
    monkeypatch.setattr(js, "on_cycle_merged", _boom)
    write_controller_state("MERGED", cycle=85, pr=1485)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "POST_CYCLE_PASS"  # best-effort: advanced despite the error
