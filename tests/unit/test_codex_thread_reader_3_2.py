"""Tests for the GraphQL reviewThreads rewrite of codex_thread_reader (item 3.2).

The old implementation read review SUBMISSIONS (--json reviews), which do not
contain the bot's inline findings, and silently passed. This now reads the actual
review THREADS (isResolved) and is fail-closed on a gh error.
"""
from __future__ import annotations

import json

from automation import codex_thread_reader as ctr


def _graphql(threads: list[dict]) -> str:
    return json.dumps({
        "data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": threads}}}}
    })


def _thread(tid: str, resolved: bool, outdated: bool = False,
            author: str = "chatgpt-codex-connector", body: str = "P1 issue") -> dict:
    return {
        "id": tid, "isResolved": resolved, "isOutdated": outdated,
        "comments": {"nodes": [{"author": {"login": author}, "body": body}]},
    }


class _R:
    def __init__(self, rc: int, out: str = "", err: str = "") -> None:
        self.returncode = rc
        self.stdout = out
        self.stderr = err


def test_all_resolved_not_blocked(monkeypatch) -> None:
    payload = _graphql([_thread("t1", True), _thread("t2", True, outdated=True)])
    monkeypatch.setattr(ctr.subprocess, "run", lambda *a, **k: _R(0, payload))
    res = ctr.read_threads(119, "KevinSGarrett/Fiverr")
    assert res.merge_blocked is False
    assert res.all_resolved is True
    assert res.read_error == ""
    assert len(res.threads) == 2


def test_unresolved_thread_blocks(monkeypatch) -> None:
    payload = _graphql([_thread("t1", True), _thread("t2", False)])
    monkeypatch.setattr(ctr.subprocess, "run", lambda *a, **k: _R(0, payload))
    res = ctr.read_threads(119)
    assert res.merge_blocked is True
    assert len(res.blockers) == 1
    assert res.blockers[0].thread_id == "t2"


def test_outdated_but_unresolved_still_blocks(monkeypatch) -> None:
    # GitHub's required_conversation_resolution blocks on any unresolved thread,
    # outdated or not.
    payload = _graphql([_thread("t1", False, outdated=True)])
    monkeypatch.setattr(ctr.subprocess, "run", lambda *a, **k: _R(0, payload))
    res = ctr.read_threads(119)
    assert res.merge_blocked is True


def test_no_threads_not_blocked(monkeypatch) -> None:
    monkeypatch.setattr(ctr.subprocess, "run", lambda *a, **k: _R(0, _graphql([])))
    res = ctr.read_threads(119)
    assert res.merge_blocked is False
    assert res.all_resolved is True


def test_gh_failure_is_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(ctr.subprocess, "run", lambda *a, **k: _R(1, "", "bad creds"))
    res = ctr.read_threads(119)
    assert res.merge_blocked is True
    assert res.read_error != ""


def test_exception_is_fail_closed(monkeypatch) -> None:
    def _boom(*a, **k):
        raise OSError("gh missing")

    monkeypatch.setattr(ctr.subprocess, "run", _boom)
    res = ctr.read_threads(119)
    assert res.merge_blocked is True
    assert res.read_error != ""


def test_uses_graphql_reviewthreads_query(monkeypatch) -> None:
    captured = {}

    def _capture(cmd, **k):
        captured["cmd"] = cmd
        return _R(0, _graphql([]))

    monkeypatch.setattr(ctr.subprocess, "run", _capture)
    ctr.read_threads(119, "KevinSGarrett/Fiverr")
    cmd = captured["cmd"]
    assert "graphql" in cmd
    joined = " ".join(cmd)
    assert "reviewThreads" in joined
    assert "isResolved" in joined
    # owner/name/number passed as variables
    assert any("owner=KevinSGarrett" in c for c in cmd)
    assert any("name=Fiverr" in c for c in cmd)
    assert any("number=119" in c for c in cmd)
