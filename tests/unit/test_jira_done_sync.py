"""Audit BLOCKER [B] — the MERGED branch marks the cycle's Jira stories Done.

`jira_sync.on_cycle_merged` was DEAD CODE (zero call sites): the board never
converged, so the next cycle re-planned In-Review stories → duplicate work. The
MERGED branch now calls it (AC-gated, so it can't close incomplete stories) and is
BEST-EFFORT (a Jira outage must NOT block the post-merge cycle advance).
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from automation import runner_paths
from automation.ai_cycle_controller import cli
from automation.state_writer import write_controller_state


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
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
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked", lambda *a, **k: None)
    monkeypatch.setattr(nr, "notify_info", lambda *a, **k: None)
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": None})
    yield
    _wipe()


def _state() -> dict:
    return json.loads((runner_paths.state_dir() / "controller_state.json").read_text())


def _fake_brief(stories):
    return SimpleNamespace(snapshot=SimpleNamespace(current_stories=stories))


def _story(key, status="In Progress"):
    return SimpleNamespace(jira_key=key, status=status)


def test_merged_calls_on_cycle_merged_then_advances(monkeypatch):
    import automation.jira_sync as js
    import automation.merge_gate as mg
    import automation.pm_intelligence as pmi
    captured = {}

    def _ocm(cycle, merge_sha, keys, *a, **k):
        captured["cycle"] = cycle
        captured["merge_sha"] = merge_sha
        captured["keys"] = list(keys)
        return [{"key": keys[0], "action": "done_transition", "status": "ok"}]

    monkeypatch.setattr(js, "on_cycle_merged", _ocm)
    monkeypatch.setattr(pmi, "build_cycle_brief",
                        lambda *a, **k: _fake_brief([_story("SCRUM-1"), _story("SCRUM-2", "Done")]))
    monkeypatch.setattr(mg, "_read_receipt", lambda pr: {"merge_sha": "abc123"})

    write_controller_state("MERGED", cycle=84, pr=1484)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    # Jira sync ran with the cycle's NON-Done story keys + the merge sha...
    assert captured["keys"] == ["SCRUM-1"]  # SCRUM-2 was Done → excluded
    assert captured["merge_sha"] == "abc123"
    assert captured["cycle"] == 84
    # ...and the cycle still advances.
    assert _state()["status"] == "POST_CYCLE_PASS"


def test_merged_advances_even_if_jira_sync_raises(monkeypatch):
    # BEST-EFFORT: a Jira failure must NEVER block the post-merge advance.
    import automation.jira_sync as js
    import automation.pm_intelligence as pmi

    def _boom(*a, **k):
        raise RuntimeError("jira 503")

    monkeypatch.setattr(pmi, "build_cycle_brief",
                        lambda *a, **k: _fake_brief([_story("SCRUM-9")]))
    monkeypatch.setattr(js, "on_cycle_merged", _boom)
    write_controller_state("MERGED", cycle=85, pr=1485)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "POST_CYCLE_PASS"  # advanced despite the Jira error
