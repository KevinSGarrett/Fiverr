"""Tests for automation.required_checks (item 3.2).

Locks the casing/typename-correct rollup parsing (the original gate's
``conclusion == "success"`` never matched gh's uppercase ``SUCCESS``) and the
fail-closed required-context union.
"""
from __future__ import annotations

from automation import required_checks as rc


def _checkrun(name: str, conclusion: str | None = None, status: str = "COMPLETED") -> dict:
    return {"__typename": "CheckRun", "name": name, "conclusion": conclusion, "status": status}


def _all_green() -> list[dict]:
    return [_checkrun(n, "SUCCESS") for n in rc.REQUIRED_CONTEXTS]


def test_uppercase_success_is_green() -> None:
    # gh returns CheckRun.conclusion == "SUCCESS" (uppercase), state == null.
    assert rc.required_check_disposition(_all_green()) == "GREEN"


def test_lowercase_conclusion_still_success() -> None:
    low = [{"name": n, "conclusion": "success"} for n in rc.REQUIRED_CONTEXTS]
    assert rc.required_check_disposition(low) == "GREEN"


def test_statuscontext_state_field() -> None:
    sc = [{"__typename": "StatusContext", "context": n, "state": "SUCCESS"}
          for n in rc.REQUIRED_CONTEXTS]
    assert rc.required_check_disposition(sc) == "GREEN"


def test_running_check_is_pending() -> None:
    rollup = [_checkrun(n, "SUCCESS") for n in rc.REQUIRED_CONTEXTS if n != "Validate PR"]
    rollup.append(_checkrun("Validate PR", conclusion=None, status="IN_PROGRESS"))
    assert rc.required_check_disposition(rollup) == "PENDING"


def test_failed_required_check_is_failed() -> None:
    rollup = [_checkrun(n, ("FAILURE" if n == "CI / tests-coverage" else "SUCCESS"))
              for n in rc.REQUIRED_CONTEXTS]
    assert rc.required_check_disposition(rollup) == "FAILED"


def test_missing_required_check_is_pending() -> None:
    rollup = [_checkrun(n, "SUCCESS") for n in rc.REQUIRED_CONTEXTS if n != "Secret Scan"]
    assert rc.required_check_disposition(rollup) == "PENDING"


def test_empty_rollup_is_pending() -> None:
    assert rc.required_check_disposition([]) == "PENDING"
    assert rc.required_check_disposition(None) == "PENDING"


def test_extra_optional_failing_check_does_not_block() -> None:
    rollup = _all_green() + [_checkrun("some-optional-check", "FAILURE")]
    assert rc.required_check_disposition(rollup) == "GREEN"


def test_failed_precedence_over_pending() -> None:
    rollup = [_checkrun(n, "SUCCESS") for n in rc.REQUIRED_CONTEXTS
              if n not in ("Secret Scan", "Validate PR")]
    rollup.append(_checkrun("Secret Scan", conclusion=None, status="QUEUED"))  # pending
    rollup.append(_checkrun("Validate PR", "FAILURE"))                          # failed
    assert rc.required_check_disposition(rollup) == "FAILED"


def test_required_contexts_are_the_eight_live_names() -> None:
    assert rc.REQUIRED_CONTEXTS == frozenset({
        "CI / lint", "CI / type-check", "CI / tests-coverage", "CI / smoke-gates",
        "CI / codex-review-gate", "Secret Scan", "Dependency Audit", "Validate PR",
    })


def test_get_required_contexts_no_live_fetch_returns_known_set() -> None:
    assert rc.get_required_contexts(fetch_live=False) == set(rc.REQUIRED_CONTEXTS)


def test_get_required_contexts_unions_live(monkeypatch) -> None:
    class _R:
        returncode = 0
        stdout = '["CI / lint", "Brand New Check"]'
        stderr = ""

    monkeypatch.setattr(rc.subprocess, "run", lambda *a, **k: _R())
    got = rc.get_required_contexts()
    # Union: never looser than the known 8, plus any live additions.
    assert set(rc.REQUIRED_CONTEXTS).issubset(got)
    assert "Brand New Check" in got


def test_get_required_contexts_fails_closed_to_known_set(monkeypatch) -> None:
    class _R:
        returncode = 1
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(rc.subprocess, "run", lambda *a, **k: _R())
    assert rc.get_required_contexts() == set(rc.REQUIRED_CONTEXTS)


def test_normalize_state_buckets() -> None:
    assert rc.normalize_state({"conclusion": "SUCCESS"}) == "SUCCESS"
    assert rc.normalize_state({"conclusion": "FAILURE"}) == "FAILED"
    assert rc.normalize_state({"conclusion": "TIMED_OUT"}) == "FAILED"
    assert rc.normalize_state({"status": "IN_PROGRESS"}) == "PENDING"
    assert rc.normalize_state({"state": "PENDING"}) == "PENDING"
    assert rc.normalize_state({"conclusion": "SKIPPED"}) == "PENDING"
    assert rc.normalize_state({}) == "PENDING"
