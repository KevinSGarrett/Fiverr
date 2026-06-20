"""
required_checks.py — single source of truth for the required GitHub status checks
that gate a merge into ``develop`` (item 3.2).

Before this module the required-check set was triplicated and drifted
(ci_status_reader = 4, merge_gate = 4, post_cycle_review = 5), and every consumer
mis-parsed the GitHub ``statusCheckRollup`` casing: ``gh pr view --json
statusCheckRollup`` returns ``CheckRun`` objects whose ``conclusion`` is
UPPERCASE (e.g. ``"SUCCESS"``) with ``state == null``, and ``StatusContext``
objects whose ``state`` is UPPERCASE — so a ``conclusion == "success"``
(lowercase) test never matched and the gate could never see a green check.

This module centralizes:
  * ``REQUIRED_CONTEXTS`` — the known-required check-run names.
  * ``get_required_contexts`` — the union of ``REQUIRED_CONTEXTS`` with the live
    branch-protection contexts (so item 3.3's expansion auto-propagates and the
    runner gate is never *looser* than branch protection), fail-closed to the
    hardcoded set when GitHub is unreachable.
  * ``normalize_state`` / ``latest_by_name`` / ``required_check_disposition`` —
    casing-correct, typename-correct rollup parsing.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

REPO = "KevinSGarrett/Fiverr"

# The check-run NAMES GitHub reports on a develop PR (verified live). CI jobs are
# namespaced "CI / <job>"; security.yml and pr-checks.yml jobs report bare names.
REQUIRED_CONTEXTS: frozenset[str] = frozenset({
    "CI / lint",
    "CI / type-check",
    "CI / tests-coverage",
    "CI / smoke-gates",
    "CI / codex-review-gate",
    "Secret Scan",
    "Dependency Audit",
    "Validate PR",
})

# Conclusion / state values, normalized to UPPERCASE.
_SUCCESS_STATES = {"SUCCESS"}
# Terminal non-success conclusions/states — these will NOT self-heal without a
# new push, so the merge path treats them as FAILED (do not keep waiting).
_FAILED_STATES = {
    "FAILURE", "CANCELLED", "TIMED_OUT", "ERROR",
    "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE",
}
# Everything else (QUEUED, IN_PROGRESS, PENDING, EXPECTED, NEUTRAL, SKIPPED,
# "", None, or an absent required check) is PENDING — not green, not hard-failed,
# so the loop retries on the next tick rather than merging or giving up.


def _check_name(check: dict[str, Any]) -> str:
    """Name of a rollup entry — ``name`` for CheckRun, ``context`` for StatusContext."""
    return str(check.get("name") or check.get("context") or "")


def _raw_state(check: dict[str, Any]) -> str:
    """Best available status token for a rollup entry, UPPERCASED.

    CheckRun: ``conclusion`` once COMPLETED (SUCCESS/FAILURE/...); while running
    ``conclusion`` is null and ``status`` is QUEUED/IN_PROGRESS. StatusContext:
    ``state`` (SUCCESS/PENDING/FAILURE/ERROR/EXPECTED).
    """
    conclusion = (check.get("conclusion") or "").strip()
    if conclusion:
        return conclusion.upper()
    state = (check.get("state") or "").strip()
    if state:
        return state.upper()
    status = (check.get("status") or "").strip()  # CheckRun in-progress
    return status.upper()


def normalize_state(check: dict[str, Any]) -> str:
    """Classify one rollup entry as ``SUCCESS`` | ``FAILED`` | ``PENDING``."""
    token = _raw_state(check)
    if token in _SUCCESS_STATES:
        return "SUCCESS"
    if token in _FAILED_STATES:
        return "FAILED"
    return "PENDING"


def latest_by_name(rollup: list[dict[str, Any]] | None) -> dict[str, str]:
    """Map each check name to its normalized SUCCESS/FAILED/PENDING state.

    ``statusCheckRollup`` is already deduplicated to the latest run per check; if
    a name appears more than once the last occurrence wins.
    """
    out: dict[str, str] = {}
    for check in rollup or []:
        name = _check_name(check)
        if name:
            out[name] = normalize_state(check)
    return out


def required_check_disposition(
    rollup: list[dict[str, Any]] | None,
    required: set[str] | frozenset[str] | None = None,
) -> str:
    """Overall disposition of the REQUIRED checks: ``GREEN`` | ``PENDING`` | ``FAILED``.

    * FAILED  — at least one required check concluded non-success (terminal).
    * PENDING — no failures, but a required check is still running or has not yet
                reported (absent from the rollup). Fail-closed: never merge.
    * GREEN   — every required check reported SUCCESS.
    """
    req = set(required) if required is not None else set(REQUIRED_CONTEXTS)
    states = latest_by_name(rollup)
    any_failed = False
    any_pending = False
    for ctx in req:
        st = states.get(ctx)
        if st is None:
            any_pending = True  # required check not yet reported
        elif st == "FAILED":
            any_failed = True
        elif st != "SUCCESS":
            any_pending = True
    if any_failed:
        return "FAILED"
    if any_pending:
        return "PENDING"
    return "GREEN"


def get_required_contexts(repo: str = REPO, fetch_live: bool = True) -> set[str]:
    """Required-check set = union of ``REQUIRED_CONTEXTS`` and the live
    branch-protection contexts on ``develop``.

    Union (not replace) so the runner gate is never *looser* than the hardcoded
    floor even while item 3.3's branch-protection expansion is still a pending
    operator step, and so any future protection additions auto-propagate. On any
    gh failure (no token / no admin-read / offline) we fail closed to the
    hardcoded set — requiring all of it.
    """
    base = set(REQUIRED_CONTEXTS)
    if not fetch_live:
        return base
    try:
        r = subprocess.run(
            ["gh", "api",
             f"repos/{repo}/branches/develop/protection/required_status_checks/contexts"],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode == 0:
            live = json.loads(r.stdout)
            if isinstance(live, list):
                return base | {str(c) for c in live if c}
    except Exception:
        pass
    return base
