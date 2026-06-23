"""Unit tests for the autonomous Codex review-thread resolver (audit BLOCKER 2).

The resolver drives a bounded fix→re-review loop so a cycle PR can clear the
reviewer's findings WITHOUT a human (the manual GraphQL resolveReviewThread step
done ~10× this session). These tests pin the pure logic (no real gh/git/cursor):
fix-don't-dismiss, fail-closed on read/repair error, escalate after the budget,
and the "Codex has reviewed" race-closer.
"""
from __future__ import annotations

import automation.codex_thread_resolver as ctr
from automation.codex_thread_reader import CodexDispositionResult, CodexThread, codex_has_reviewed


def _thread(tid="T1", resolved=False, outdated=False, author="chatgpt-codex-connector",
            body="P1: null deref in foo.py:10") -> CodexThread:
    return CodexThread(thread_id=tid, is_resolved=resolved, is_outdated=outdated,
                       author=author, body=body)


def _disp(threads, read_error="") -> CodexDispositionResult:
    r = CodexDispositionResult(pr_number=1, threads=list(threads))
    r.read_error = read_error
    return r


# ── pure helpers ──────────────────────────────────────────────────────────────
def test_actionable_excludes_resolved_outdated_and_other_authors():
    threads = [
        _thread("a", resolved=True),
        _thread("b", outdated=True),
        _thread("c", author="some-human"),       # not a recognized reviewer
        _thread("d"),                              # actionable
        _thread("e", author=""),                   # empty author still actionable
    ]
    ids = {t.thread_id for t in ctr._actionable(threads)}
    assert ids == {"d", "e"}


def test_build_repair_prompt_includes_findings_and_report_path():
    prompt = ctr.build_codex_repair_prompt(84, [_thread(body="Fix the off-by-one in bar.py:7")])
    assert "CYCLE 084" in prompt
    assert "Fix the off-by-one in bar.py:7" in prompt
    assert "docs/cycle_reports/CYCLE_084_AGENT_B.md" in prompt
    assert "Do NOT dismiss" in prompt


def test_build_repair_prompt_includes_location():
    # Codex P2: a finding whose body does not name the file must still give the agent
    # the file:line so it can target the edit (it was dropped before).
    t = CodexThread(thread_id="T9", is_resolved=False, is_outdated=False,
                    author="chatgpt-codex-connector", body="Null deref here",
                    path="src/foo.py", line=42)
    prompt = ctr.build_codex_repair_prompt(84, [t])
    assert "**Location:** `src/foo.py:42`" in prompt
    assert "Null deref here" in prompt


# ── bounded resolve loop ────────────────────────────────────────────────────────
def test_no_threads_resolves_immediately():
    res = ctr.resolve_pr_codex_threads(
        84, 1, "cycle/084/integration",
        reader=lambda pr: _disp([]),
        outdated_resolver=lambda threads: 0,
        dispatch_repair=lambda *a: (_ for _ in ()).throw(AssertionError("should not repair")),
    )
    assert res.resolved is True and res.escalate is False
    assert res.repaired_rounds == 0


def test_read_error_escalates_fail_closed():
    res = ctr.resolve_pr_codex_threads(
        84, 1, "b",
        reader=lambda pr: _disp([], read_error="gh down"),
        outdated_resolver=lambda threads: 0,
        dispatch_repair=lambda *a: True,
    )
    assert res.resolved is False and res.escalate is True
    assert "read_error" in res.reason


def test_missing_dispatcher_escalates():
    res = ctr.resolve_pr_codex_threads(
        84, 1, "b",
        reader=lambda pr: _disp([_thread()]),
        outdated_resolver=lambda threads: 0,
        dispatch_repair=None,
    )
    assert res.escalate is True and res.remaining == 1


def test_repair_then_clean_resolves():
    # The finding persists until a repair is dispatched; after the repair "lands",
    # the thread is gone (GitHub outdated it + the outdated_resolver resolved it).
    state = {"repaired": False}

    def reader(pr):
        return _disp([]) if state["repaired"] else _disp([_thread()])

    def repair(c, br, p):
        state["repaired"] = True
        return True

    res = ctr.resolve_pr_codex_threads(
        84, 1, "b", max_rounds=2,
        reader=reader,
        outdated_resolver=lambda threads: 0,
        dispatch_repair=repair,
    )
    assert res.resolved is True
    assert res.repaired_rounds == 1


def test_repair_failure_escalates():
    res = ctr.resolve_pr_codex_threads(
        84, 1, "b", max_rounds=2,
        reader=lambda pr: _disp([_thread()]),
        outdated_resolver=lambda threads: 0,
        dispatch_repair=lambda c, br, p: False,
    )
    assert res.escalate is True
    assert "repair dispatch failed" in res.reason


def test_unresolved_after_budget_escalates():
    # Findings never clear; after max_rounds the loop escalates rather than looping forever.
    res = ctr.resolve_pr_codex_threads(
        84, 1, "b", max_rounds=2,
        reader=lambda pr: _disp([_thread()]),
        outdated_resolver=lambda threads: 0,
        dispatch_repair=lambda c, br, p: True,
    )
    assert res.resolved is False and res.escalate is True
    assert res.remaining == 1
    assert res.repaired_rounds == 2  # one repair per round, bounded


# ── codex_has_reviewed (race-closer) ────────────────────────────────────────────
def test_codex_has_reviewed_true_on_codex_review(monkeypatch):
    import automation.codex_thread_reader as reader

    class _R:
        returncode = 0
        stdout = ('{"data":{"repository":{"pullRequest":{'
                  '"reviews":{"nodes":[{"author":{"login":"chatgpt-codex-connector"}}]},'
                  '"reviewThreads":{"nodes":[]}}}}}')
    monkeypatch.setattr(reader.subprocess, "run", lambda *a, **k: _R())
    assert codex_has_reviewed(1) is True


def test_codex_has_reviewed_false_when_only_humans(monkeypatch):
    import automation.codex_thread_reader as reader

    class _R:
        returncode = 0
        stdout = ('{"data":{"repository":{"pullRequest":{'
                  '"reviews":{"nodes":[{"author":{"login":"some-human"}}]},'
                  '"reviewThreads":{"nodes":[]}}}}}')
    monkeypatch.setattr(reader.subprocess, "run", lambda *a, **k: _R())
    assert codex_has_reviewed(1) is False


def test_codex_has_reviewed_none_on_error(monkeypatch):
    import automation.codex_thread_reader as reader

    class _R:
        returncode = 1
        stdout = ""
    monkeypatch.setattr(reader.subprocess, "run", lambda *a, **k: _R())
    assert codex_has_reviewed(1) is None
