"""Codex P1 (closed #144) — on_cycle_merged must NOT mark stories Done without real
per-story AC verification.

The old default path read the Jira description and set `unverified=[]` ("assume all
AC met if tests pass"), so any key passed was transitioned to Done regardless of
whether its acceptance criteria were actually met. A passing CI run is NOT per-story
AC verification. Now: no real verification result → SKIP (never transition).
"""
from __future__ import annotations

import automation.jira_client as jc
import automation.jira_sync as js


def _spy(monkeypatch):
    calls = {"transition": 0, "comment": 0}
    monkeypatch.setattr(jc, "transition_issue",
                        lambda *a, **k: calls.__setitem__("transition", calls["transition"] + 1))
    monkeypatch.setattr(jc, "add_comment",
                        lambda *a, **k: calls.__setitem__("comment", calls["comment"] + 1))
    return calls


def test_skips_done_when_no_ac_verification(monkeypatch):
    calls = _spy(monkeypatch)
    res = js.on_cycle_merged(84, "sha123", ["SCRUM-1", "SCRUM-2"])  # NO ac_verification_results
    assert [r["status"] for r in res] == ["skipped", "skipped"]
    assert all(r["action"] == "skip_no_ac_verification" for r in res)
    assert calls["transition"] == 0, "must NEVER transition Done without real AC verification"


def test_transitions_done_with_explicit_verified(monkeypatch):
    calls = _spy(monkeypatch)
    res = js.on_cycle_merged(84, "sha123", ["SCRUM-1"],
                             ac_verification_results={"SCRUM-1": {"verified": ["AC1", "AC2"], "unverified": []}})
    assert res[0]["status"] == "ok" and res[0]["action"] == "done_transition"
    assert calls["transition"] == 1  # explicit verification → real transition


def test_blocks_done_with_unverified(monkeypatch):
    calls = _spy(monkeypatch)
    res = js.on_cycle_merged(84, "sha123", ["SCRUM-1"],
                             ac_verification_results={"SCRUM-1": {"verified": [], "unverified": ["AC1"]}})
    assert res[0]["status"] == "blocked"
    assert calls["transition"] == 0  # unverified AC → blocked, not transitioned


def test_skips_when_ac_result_is_empty(monkeypatch):
    # Codex P2: {"verified": [], "unverified": []} (verify_ac_against_evidence with NO
    # extracted AC) is a truthy dict that slips past the `not ac_result` guard. An empty
    # `unverified` must NOT be read as "0 AC → all verified" and close the story.
    calls = _spy(monkeypatch)
    res = js.on_cycle_merged(84, "sha123", ["SCRUM-1"],
                             ac_verification_results={"SCRUM-1": {"verified": [], "unverified": []}})
    assert res[0]["status"] == "skipped"
    assert calls["transition"] == 0, "a story with zero confirmed AC must NOT be marked Done"
