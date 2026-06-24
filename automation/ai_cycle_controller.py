"""
ai_cycle_controller.py — Main CLI entrypoint for the Autonomous Development Runner.

Usage:
  python automation/ai_cycle_controller.py brain-check
  python automation/ai_cycle_controller.py compile-policy
  python automation/ai_cycle_controller.py jira-inventory [--dry-run]
  python automation/ai_cycle_controller.py plan-cycle [--dry-run] [--cycle N]
  python automation/ai_cycle_controller.py cursor-smoke
  python automation/ai_cycle_controller.py status
  python automation/ai_cycle_controller.py tick
  python automation/ai_cycle_controller.py recover
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import click
import yaml

# Ensure repo root on sys.path when run as a script
_here = Path(__file__).parent
_repo_root = _here.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from automation import runner_paths  # noqa: E402
from automation.config_loader import get_secret  # noqa: E402
from automation.pm_pack_loader import brain_check  # noqa: E402
from automation.policy_compiler import compile_policy  # noqa: E402

REPO_ROOT = _repo_root
RUNNER_STATE = runner_paths.state_dir() / "controller_state.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _pause_file_path() -> Path:
    """Resolve the autopilot pause sentinel path (lazy — honours test redirection)."""
    return runner_paths.state_dir() / "autopilot_paused.json"


def _autonomy_freeze_path() -> Path:
    """Resolve the autonomy-freeze policy path (repo-root-relative).

    NOTE: the policy lives under ``PM_Pack/automation/policies/`` — not the path
    some older docs list. Reuse ``REPO_ROOT`` so it tracks the runner's checkout.
    """
    return REPO_ROOT / "PM_Pack/automation/policies/autonomy_freeze.yml"


def _is_frozen() -> tuple[bool, str]:
    """SAFE-01 kill-switch: read ``autonomy_freeze.yml`` and report frozen state.

    Returns ``(frozen, reason)``. Fail-safe: a missing/unreadable/malformed
    policy is treated as NOT frozen (returns ``(False, ...)``) but logs a
    warning. We never BLOCK on a missing policy — only an explicit
    ``frozen: true`` freezes the runner.
    """
    p = _autonomy_freeze_path()
    if not p.exists():
        try:
            click.secho(
                f"  [WARN] autonomy_freeze policy missing at {p} — treating as NOT frozen",
                fg="yellow",
            )
        except Exception:
            pass
        return False, "policy_missing"
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        try:
            click.secho(
                f"  [WARN] autonomy_freeze policy unreadable ({exc}) — treating as NOT frozen",
                fg="yellow",
            )
        except Exception:
            pass
        return False, "policy_unreadable"
    if not isinstance(data, dict):
        return False, "policy_malformed"
    frozen = bool(data.get("frozen", False))
    reason = str(data.get("reason") or "no_reason_recorded")
    return frozen, reason


def _refuse_if_leaked_pytest() -> bool:
    """Fail-closed ENTRY GUARD against a leaked ``PYTEST_CURRENT_TEST`` var.

    A real runner sets NEITHER ``PYTEST_CURRENT_TEST`` nor
    ``AUTOPILOT_TEST_HARNESS`` → returns False (proceed normally).
    The test harness (conftest) sets ``AUTOPILOT_TEST_HARNESS=1`` so the suite
    can still exercise tick/run-cycle → returns False.
    A leaked ``PYTEST_CURRENT_TEST`` with NO harness → prints a [REFUSE] line
    and returns True so the caller fails closed (refuses live dispatch) rather
    than silently no-op'ing.
    """
    import os as _os_guard

    if _os_guard.environ.get("PYTEST_CURRENT_TEST") and not _os_guard.environ.get(
        "AUTOPILOT_TEST_HARNESS"
    ):
        click.secho(
            "[REFUSE] PYTEST_CURRENT_TEST present without test harness — "
            "refusing live dispatch (fail-closed)",
            fg="red",
            bold=True,
        )
        return True
    return False


def _write_autonomy_freeze(frozen: bool, reason: str | None) -> Path:
    """Atomically rewrite ``autonomy_freeze.yml`` setting ``frozen: true/false``.

    Preserves all other keys; updates ``frozen``/``reason`` plus
    ``frozen_at``/``frozen_by`` (when freezing) or
    ``unfrozen_at``/``unfrozen_by`` (when unfreezing). Atomic via temp+os.replace.
    """
    import os as _os_fz

    p = _autonomy_freeze_path()
    data: dict[str, object] = {}
    if p.exists():
        try:
            loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}
    data["frozen"] = frozen
    if reason:
        data["reason"] = reason
    today = datetime.now(UTC).date().isoformat()
    if frozen:
        data["frozen_at"] = today
        data["frozen_by"] = "ai_cycle_controller freeze CLI"
    else:
        data["unfrozen_at"] = today
        data["unfrozen_by"] = "ai_cycle_controller unfreeze CLI"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".yml.tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    _os_fz.replace(tmp, p)
    return p


def _write_pause(reason: str, detail: str | None = None) -> None:
    """Write the autopilot pause sentinel (atomic) with paused:true + reason + ts.

    Item 0.2 kill-switch: writers MUST go through here so the sentinel always
    carries ``paused: true``. The reader pauses on file existence regardless,
    but keeping ``paused: true`` preserves backward compatibility.
    """
    import json as _json
    import os as _os

    p = _pause_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {"paused": True, "reason": reason, "ts": _now()}
    if detail:
        payload["detail"] = detail[:200]
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(_json.dumps(payload, indent=2), encoding="utf-8")
    _os.replace(tmp, p)

    # Off-box alert hook (interim until 5.3): best-effort ERROR-level notification.
    try:
        from automation.notification_router import notify as _notify
        _notify("BLOCKED", "AUTOPILOT_PAUSED", f"reason={reason}",
                incident_code="AUTOPILOT_PAUSED")
    except Exception:
        # Notification must never block or fail the pause itself.
        try:
            click.secho(f"  [ALERT] AUTOPILOT_PAUSED reason={reason}", fg="red", bold=True)
        except Exception:
            pass


def _update_hydration_cycle(new_cycle: int) -> None:
    """Update CYCLE_CURRENT and related fields in HYDRATION_HEADER.md when advancing cycles.
    Called when transitioning POST_CYCLE_PASS → COMPILED to ensure compile_policy
    picks up the new cycle number rather than the completed one.
    """
    header = REPO_ROOT / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    if not header.exists():
        return
    import re as _re
    text = header.read_text(encoding="utf-8", errors="replace")
    prev_cycle = new_cycle - 1
    # Update CYCLE_CURRENT
    text = _re.sub(r"(CYCLE_CURRENT:\s*)\d+", rf"\g<1>{new_cycle:03d}", text)
    # Update Active cycle
    text = _re.sub(r"(Active cycle:\s*)\d+", rf"\g<1>{new_cycle}", text)
    # Update Branch
    text = _re.sub(r"(Branch:\s*)cycle/\d{3}/integration",
                   rf"\g<1>cycle/{new_cycle:03d}/integration", text)
    # Update LAST_COMPLETED
    text = _re.sub(r"(LAST_COMPLETED:\s*)C\d+", rf"\g<1>C{prev_cycle:03d}", text)
    # Update the header timestamp
    from datetime import date as _date
    today = _date.today().isoformat()
    text = _re.sub(r"(## Updated:)[^\n]+", rf"\1 {today} | Cycle {new_cycle:03d} autonomous run", text)
    header.write_text(text, encoding="utf-8")


def _write_runner_state(state: dict) -> None:
    RUNNER_STATE.parent.mkdir(parents=True, exist_ok=True)
    RUNNER_STATE.write_text(json.dumps(state, indent=2))


def _read_runner_state() -> dict:
    try:
        return json.loads(RUNNER_STATE.read_text()) if RUNNER_STATE.exists() else {}
    except Exception:
        return {}


def _tick_counter(key: str, *, increment: bool = False, reset: bool = False) -> int:
    """Small persistent per-key tick counter (item 3.2: bounded CI-wait / merge
    retry across ticks). Stored under the runner state dir so it is test-isolated
    via ``AUTOPILOT_RUNNER_ROOT``. Returns the current count.
    """
    from automation import runner_paths
    path = runner_paths.state_dir() / "tick_counters.json"
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        data = {}
    n = int(data.get(key, 0))
    if reset:
        data.pop(key, None)
        n = 0
    elif increment:
        n += 1
        data[key] = n
    if increment or reset:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
        except Exception:
            pass
    return n


def _finalize_post_cycle_pass(cycle: int | None) -> str:
    """ITEM 3.2: single decision point for a PASSing post-cycle review.

    If a PR is open (active_pr set) the cycle must NOT be marked complete — hand
    off to AWAITING_CI_GREEN so the runner waits for CI and merges via the gate,
    advancing only after a verified merge. With no open PR, fall back to the
    legacy POST_CYCLE_PASS. Used by BOTH the AGENT_COMPLETE and POST_CYCLE_PENDING
    tick branches so they can never diverge (an open PR must never be bypassed).

    Returns the status that was written.
    """
    from automation.state_writer import write_controller_state as _w
    active_pr = (_read_runner_state() or {}).get("active_pr")
    if active_pr:
        _w("AWAITING_CI_GREEN", cycle=cycle)
        return "AWAITING_CI_GREEN"
    _w("POST_CYCLE_PASS", cycle=cycle)
    return "POST_CYCLE_PASS"


def _attempt_merge(cycle: int | None, pr_int: int) -> str:
    """ITEM 3.2: run the merge gate (execute) for an open PR and transition state.

    Shared by the AWAITING_CI_GREEN green-path and the MERGING crash-recovery
    branch. Idempotent — ``merge_gate.run`` treats an already-merged PR as success
    (``merged`` flag), so re-invoking after a crash between the MERGING write and
    the MERGED/MERGE_BLOCKED write resolves cleanly rather than double-merging.
    Returns the new status written (``MERGED`` or ``MERGE_BLOCKED``).
    """
    import automation.autopilot_logger as L
    from automation.notification_router import notify_blocked, notify_info
    from automation.state_writer import write_controller_state as _w
    try:
        from automation.pr_builder import _ensure_gh_token
        _ensure_gh_token()
    except Exception:
        pass
    from automation.merge_gate import run as _gate_run
    mg = _gate_run(pr_number=pr_int, dry_run=False, execute=True)
    if mg.passed and (mg.merged or mg.merge_sha or mg.already_merged):
        _tick_counter(f"ci_wait_pr{pr_int}", reset=True)
        _tick_counter(f"merge_retry_pr{pr_int}", reset=True)
        _w("MERGED", cycle=cycle)
        L.ok(f"PR #{pr_int} MERGED {mg.merge_sha or '(already merged)'} "
             f"— cycle {cycle} advances next tick")
        notify_info(f"Cycle {cycle} merged PR #{pr_int}")
        return "MERGED"
    _w("MERGE_BLOCKED", cycle=cycle)
    fails = ", ".join(c.name for c in mg.failed_checks()) or "unknown"
    L.error(f"Merge gate FAILED for PR #{pr_int}: {fails}")
    notify_blocked(
        f"Cycle {cycle} merge gate failed (PR #{pr_int})",
        body=f"Blocking failures: {fails}",
        incident_code="MERGE_BLOCKED", cycle=cycle,
    )
    return "MERGE_BLOCKED"


def _update_pr_branch_if_behind(pr_int: int) -> bool:
    """If the PR head is BEHIND its base (develop moved under it), update it via
    ``gh pr update-branch`` so CI re-runs on the merged result. Returns True iff an
    update was performed.

    Audit BLOCKER #2: branch protection requires up-to-date branches, so once any
    cycle merges to develop, every OTHER open cycle PR becomes BEHIND and
    ``gh pr merge`` fails identically every retry → the gate dead-ends → operator.
    This is routine in a multi-cycle run (each cycle advances develop). Idempotent +
    fail-safe: only updates when state is exactly ``BEHIND``; never raises.
    """
    import json as _json
    import subprocess as _sp
    try:
        from automation.pr_builder import _ensure_gh_token
        _ensure_gh_token()
    except Exception:
        pass
    try:
        view = _sp.run(
            ["gh", "pr", "view", str(pr_int), "--repo", "KevinSGarrett/Fiverr",
             "--json", "mergeStateStatus,headRefName"],
            capture_output=True, text=True, timeout=30,
        )
        if view.returncode != 0:
            return False
        _vd = _json.loads(view.stdout or "{}")
        if _vd.get("mergeStateStatus", "") != "BEHIND":
            return False
        branch = _vd.get("headRefName", "") or ""
        upd = _sp.run(
            ["gh", "pr", "update-branch", str(pr_int), "--repo", "KevinSGarrett/Fiverr"],
            capture_output=True, text=True, timeout=60,
        )
        if upd.returncode != 0:
            return False
        # Codex P2 (#143): update-branch advanced the REMOTE head, but the LOCAL cycle
        # branch is now stale. A later _dispatch_codex_repair commits locally then
        # `git push origin branch` — which would be REJECTED non-fast-forward, escalating
        # the repair. Align the local branch to the refreshed remote head. The per-cycle
        # branch's source of truth IS the remote PR, so a hard align is correct here.
        if branch:
            _sp.run(["git", "fetch", "origin", branch],
                    cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60)
            _cur = _sp.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=str(REPO_ROOT), capture_output=True, text=True).stdout.strip()
            if _cur == branch:
                _sp.run(["git", "reset", "--hard", f"origin/{branch}"],
                        cwd=str(REPO_ROOT), capture_output=True, text=True)
            else:
                # Move the local branch ref to the remote head without a checkout.
                _sp.run(["git", "branch", "-f", branch, f"origin/{branch}"],
                        cwd=str(REPO_ROOT), capture_output=True, text=True)
        return True
    except Exception:
        return False


def _codex_dirty_now() -> set[str]:
    """Tree-wide uncommitted+untracked paths (mirror of the dispatch _dirty_now), so a
    codex repair attributes only the files IT changed."""
    _u = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    _s = subprocess.run(
        ["git", "status", "--short", "-uall"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    paths = {ln.strip().replace("\\", "/") for ln in _u.stdout.splitlines() if ln.strip()}
    paths |= {
        ln[3:].strip().replace("\\", "/")
        for ln in _s.stdout.splitlines() if ln.startswith("?? ")
    }
    return paths


def _dispatch_codex_repair(cycle: int, prompt: str) -> bool:
    """Run a scoped Cursor repair addressing Codex review findings, commit, and push.

    Returns True iff the repair produced a NEW commit pushed to the cycle branch (so
    CI + Codex re-run on the fix). Fix-don't-dismiss: we change code to ADDRESS the
    findings; GitHub then outdates the threads and the disposition step resolves them.
    The Controller stays the sole git authority (G1): the commit + push live here.
    """
    from automation.cursor_adapter import run_agent as cursor_run
    from automation.run_agent_lifecycle import _commit_agent_work, _get_changed_files

    import automation.autopilot_logger as L

    branch = f"cycle/{cycle:03d}/integration"
    # Codex P1: AWAITING_CI_GREEN has no branch guard, so the checkout could be on
    # develop or a detached HEAD. cursor_run + _commit_agent_work commit to the
    # CURRENT HEAD, but we push the named `branch` ref — if they differ, the commit
    # lands on the wrong branch and `git push origin branch` (a no-op) returns 0 →
    # we'd falsely report REPAIRING. Pin to the cycle branch first; bail if we can't.
    _cur = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    ).stdout.strip()
    if _cur != branch:
        _co = subprocess.run(
            ["git", "checkout", branch], cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        if _co.returncode != 0:
            L.error(
                f"codex repair: not on {branch} (HEAD={_cur}) and checkout failed "
                f"({_co.stderr.strip()[-160:]}) — refusing to commit to the wrong branch"
            )
            return False

    repair_dir = REPO_ROOT / "PM_Pack" / "automation" / "runs" / f"cycle_{cycle:03d}" / "codex_repair"
    repair_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = repair_dir / "codex_repair_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    pre_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True
    ).stdout.strip()
    pre_dirty = _codex_dirty_now()
    report = REPO_ROOT / f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_B.md"
    try:
        cursor_run(
            agent_id="B",
            prompt_path=str(prompt_path),
            working_dir=str(REPO_ROOT),
            output_dir=str(repair_dir),
            completion_marker=str(report),
        )
    except Exception as exc:  # pragma: no cover - defensive
        L.error(f"codex repair cursor run raised: {exc}")
        return False

    changed = _get_changed_files(pre_sha, pre_dirty)
    if not changed:
        return False
    sha = _commit_agent_work("B", cycle, changed)
    if not sha:
        return False
    push = subprocess.run(
        ["git", "push", "origin", branch], cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return push.returncode == 0


def _maybe_dispatch_codex_repair(cycle: int | None, pr_int: int) -> str:
    """CODEX_DISPOSITION (audit BLOCKER 2): before merge, autonomously address
    unresolved Codex review threads instead of dead-ending at MERGE_BLOCKED → operator.

    One round per tick (the cursor repair is minutes-long; the push re-triggers CI),
    bounded by ``CODEX_REPAIR_MAX_ROUNDS``. Returns:
      ``CLEAN``     — no actionable threads; safe to evaluate CI + merge.
      ``REPAIRING`` — dispatched a fix + pushed; stay AWAITING_CI_GREEN (CI re-runs).
      ``ESCALATE``  — round budget exhausted with findings still open → MERGE_BLOCKED.
      ``ERROR``     — transient read/dispatch error; caller retries next tick (BUT a
                      persistent read error escalates after CODEX_READ_ERROR_MAX_TICKS
                      so an auth/rate-limit/schema failure can't loop forever).
    """
    from automation.codex_thread_reader import codex_has_reviewed, read_threads
    from automation.codex_thread_resolver import (
        _actionable,
        _resolve_already_fixed,
        build_codex_repair_prompt,
    )

    def _on_read_error() -> str:
        # Codex P2: a persistent gh/GraphQL read error (auth/rate-limit/schema) would
        # otherwise loop forever on ERROR (the tick only logs + stays). Count it; after
        # the cap, escalate to MERGE_BLOCKED for operator handling like the other paths.
        _errs = _tick_counter(f"codex_read_error_pr{pr_int}", increment=True)
        _cap = int(os.environ.get("CODEX_READ_ERROR_MAX_TICKS", "10"))
        return "ESCALATE" if _errs > _cap else "ERROR"

    disp = read_threads(pr_int)
    if disp.read_error:
        return _on_read_error()
    # Resolve any threads GitHub already outdated (a prior fix landed) before deciding.
    _resolve_already_fixed(disp.threads)
    disp = read_threads(pr_int)
    if disp.read_error:
        return _on_read_error()
    _tick_counter(f"codex_read_error_pr{pr_int}", reset=True)  # a clean read resets it
    actionable = _actionable(disp.threads)
    if not actionable:
        # Empty thread set is "clean" ONLY if Codex has actually reviewed; otherwise
        # this is "review pending" and merging would ship unreviewed code. Wait
        # (bounded) rather than letting _attempt_merge fail-closed prematurely.
        if codex_has_reviewed(pr_int) is not True:
            waited = _tick_counter(f"codex_review_wait_pr{pr_int}", increment=True)
            cap = int(os.environ.get("CODEX_REVIEW_WAIT_MAX_TICKS", "30"))
            return "ESCALATE" if waited > cap else "AWAIT_REVIEW"
        _tick_counter(f"codex_review_wait_pr{pr_int}", reset=True)
        _tick_counter(f"codex_repair_pr{pr_int}", reset=True)
        return "CLEAN"

    rounds = _tick_counter(f"codex_repair_pr{pr_int}", increment=True)
    cap = int(os.environ.get("CODEX_REPAIR_MAX_ROUNDS", "3"))
    if rounds > cap:
        return "ESCALATE"
    prompt = build_codex_repair_prompt(cycle or 0, actionable)
    ok = _dispatch_codex_repair(cycle or 0, prompt)
    return "REPAIRING" if ok else "ERROR"


def _run_and_stream(args: list[str], label: str = "") -> tuple[int, str]:
    """Run subprocess streaming stdout live to terminal line by line.

    SAFE/0.3: this function ALWAYS spawns the real subprocess. There is NO
    ``PYTEST_CURRENT_TEST`` short-circuit — a leaked env var must never turn a
    live dispatch into a silent no-op. Tests inject a fake implementation via the
    autouse fixture in ``tests/conftest.py`` (monkeypatching this symbol) rather
    than relying on an in-process env-var branch.
    """
    output_lines: list[str] = []
    try:
        proc = subprocess.Popen(
            args,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            clean = line.rstrip()
            if clean:
                prefix = f"  [{label}] " if label else "  "
                click.echo(f"{prefix}{clean}")
            output_lines.append(clean)
        proc.wait()
        return proc.returncode, "\n".join(output_lines[-80:])
    except Exception as exc:
        return 1, str(exc)


def _run_shell_command(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


# ── Item 5.4 (determinism): integration branch must contain current develop ──
# Root cause of the 2026-06-21 stale-code milestone run: when a cycle is RESUMED,
# the tick checks out cycle/NNN/integration AS-IS (or recreates it from its own
# stale remote tip) and never advances it onto current origin/develop. A branch
# that predates merged develop commits therefore runs OLD code. This guard makes
# "what runs == what's on develop" true before any prompt-gen or dispatch.
_SYNC_MAX_TRANSIENT = 5   # transient git/network retries (in place) before blocking
_SYNC_MAX_RECOVER = 10    # DEVELOP_SYNC_BLOCKED recovery attempts before operator escalation


class BranchSyncError(RuntimeError):
    """Integration branch could not be made current with origin/develop.

    ``transient`` True  -> a git/network failure worth retrying in place (the prior
                           state is kept so validated prompts are NOT discarded).
    ``transient`` False -> a real merge CONFLICT needing human resolution.
    Fail-closed signal: the caller MUST NOT generate prompts or dispatch agents.
    """

    def __init__(self, message: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


def _git_cmd(args: list[str]) -> tuple[int, str]:
    """Uniform git invocation (cwd=REPO_ROOT) for the branch-sync helper."""
    return _run_shell_command(["git", *args])


def _parse_git_count(output: str, what: str) -> int:
    """Extract a `git rev-list --count` integer, tolerant of warning/advice text.

    _run_shell_command concatenates stdout+stderr, and git may emit a warning/advice
    line on stderr (rc still 0) — e.g. an ambiguous-refname warning — which would make
    a bare int() raise ValueError and (uncaught) crash the tick before the lock
    release. The count is the first all-digit token (stdout precedes stderr). Raise a
    TRANSIENT BranchSyncError if no integer is present (retry in place, fail-closed)."""
    for tok in (output or "").split():
        if tok.isdigit():
            return int(tok)
    raise BranchSyncError(
        f"could not parse {what} count from git output: {(output or '').strip()[-200:]}",
        transient=True,
    )


def ensure_integration_branch_current(cycle: int) -> dict:
    """Guarantee cycle/NNN/integration exists and contains current origin/develop.

    Cases, all fail-closed:
      (a) FRESH (branch absent local+remote)  -> create from origin/develop.
      (b) RESUME, 0 commits ahead of develop  -> hard-align to origin/develop.
      (c) RESUME with agent commits           -> merge origin/develop IN (--no-ff),
                                                  preserving the agent work.
      (d) merge CONFLICT                       -> abort + raise (transient=False).
      transient git/network error             -> raise (transient=True).

    Dirty tree: PARKED in a named recovery stash (--include-untracked) rather than
    failing closed (matches the runner's stash-before-work pattern) — the sync then
    proceeds on a clean tree. The work is NOT silently lost: the stash is named
    ``BSYNC-RESUME-cycle-NNN`` (deliberately NOT matching repo_janitor's stale-stash
    GC patterns) and is logged + recoverable via ``git stash list``. It is NOT
    auto-reapplied (popping onto a reset/merged tree could conflict); recover it
    manually if a crashed agent left real work. Idempotent: behind==0 -> no-op.
    Skipped under PYTEST_CURRENT_TEST.
    """
    import os as _os
    if _os.environ.get("PYTEST_CURRENT_TEST"):
        return {"action": "skipped_pytest", "behind": 0, "ahead": 0, "stashed": False}

    branch = f"cycle/{cycle:03d}/integration"
    info: dict = {"branch": branch, "action": None, "behind": None,
                  "ahead": None, "stashed": False}

    # 0. Detect a dirty tree, but DEFER stashing until we actually MUTATE the branch.
    #    Codex P1: at READY_TO_DISPATCH the dirty tree is the freshly-generated,
    #    validated prompts (plan-cycle writes PM_Pack/automation/prompts/CYCLE_* and
    #    does NOT commit them). The normal behind==0 path must leave them untouched,
    #    so we only stash on a reset/merge/create-from-develop path (where the
    #    uncommitted work is stale relative to the incoming develop anyway).
    rc, dirty = _git_cmd(["status", "--porcelain"])
    if rc != 0:
        raise BranchSyncError(f"git status failed: {dirty.strip()[-300:]}", transient=True)
    _tree_dirty = bool(dirty.strip())

    def _park_dirty() -> None:
        """Stash uncommitted work ONCE into a recovery stash that does NOT match any
        repo_janitor STALE_STASH_PATTERNS fragment (so it is not GC'd); recoverable
        via ``git stash list``, NOT auto-reapplied. Called only on a mutating path."""
        if not _tree_dirty or info["stashed"]:
            return
        _name = f"BSYNC-RESUME-cycle-{cycle:03d}"
        rc2, out2 = _git_cmd(["stash", "push", "--include-untracked", "-m", _name])
        if rc2 != 0:
            raise BranchSyncError(f"stash dirty tree failed: {out2.strip()[-300:]}", transient=True)
        info["stashed"] = True
        info["stash_name"] = _name
        click.secho(
            f"  [SYNC] parked uncommitted work in stash '{_name}' before branch "
            f"mutation (recoverable: git stash list | grep {_name}; NOT auto-reapplied).",
            fg="yellow",
        )

    # 1. Fetch the AUTHORITATIVE base; pin its SHA (a name could move under us).
    rc, out = _git_cmd(["fetch", "--prune", "origin", "develop"])
    if rc != 0:
        raise BranchSyncError(f"git fetch origin develop failed: {out.strip()[-300:]}", transient=True)
    rc, dev_sha = _git_cmd(["rev-parse", "--verify", "origin/develop"])
    if rc != 0:
        raise BranchSyncError("origin/develop not found after fetch", transient=True)
    dev_sha = dev_sha.strip()

    # 2. Ensure the integration branch exists and is checked out.
    rc_local, _ = _git_cmd(["rev-parse", "--verify", f"refs/heads/{branch}"])
    if rc_local != 0:
        _git_cmd(["fetch", "origin", branch, "--quiet"])
        rc_remote, _ = _git_cmd(["rev-parse", "--verify", f"refs/remotes/origin/{branch}"])
        if rc_remote == 0:
            _park_dirty()  # checkout -B resets the working tree → preserve first
            rc, out = _git_cmd(["checkout", "-B", branch, f"origin/{branch}"])
            if rc != 0:
                raise BranchSyncError(f"checkout remote {branch} failed: {out.strip()[-300:]}", transient=True)
            info["action"] = "resumed_from_remote"
        else:
            _park_dirty()
            rc, out = _git_cmd(["checkout", "-B", branch, "origin/develop"])
            if rc != 0:
                raise BranchSyncError(f"create {branch} from develop failed: {out.strip()[-300:]}", transient=True)
            info.update(action="created_from_develop", behind=0, ahead=0)
            return info  # cut from develop ⇒ already current
    else:
        # Local branch exists. If we are ALREADY on it (the READY_TO_DISPATCH case),
        # the checkout is a no-op that must NOT disturb the dirty tree — those are the
        # freshly-validated prompts (Codex P1), so do not stash. If we must SWITCH to
        # it (e.g. COMPILED, coming from develop or the prior cycle's branch), park any
        # dirty/untracked tree FIRST — otherwise a leftover untracked file (e.g. an old
        # cycle-log) fails the checkout with "untracked working tree files would be
        # overwritten by checkout" (observed live on the cycle-84 run).
        rc_cur, cur = _git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
        if rc_cur == 0 and cur.strip() != branch:
            _park_dirty()
        rc, out = _git_cmd(["checkout", branch])
        if rc != 0:
            raise BranchSyncError(f"checkout {branch} failed: {out.strip()[-300:]}", transient=True)

    # 3. Measure behind/ahead against the pinned develop SHA (exact, cheap).
    rc, behind = _git_cmd(["rev-list", "--count", f"HEAD..{dev_sha}"])
    if rc != 0:
        raise BranchSyncError(f"rev-list behind failed: {behind.strip()[-200:]}", transient=True)
    rc, ahead = _git_cmd(["rev-list", "--count", f"{dev_sha}..HEAD"])
    if rc != 0:
        raise BranchSyncError(f"rev-list ahead failed: {ahead.strip()[-200:]}", transient=True)
    behind_n = _parse_git_count(behind, "behind")
    ahead_n = _parse_git_count(ahead, "ahead")
    info["behind"], info["ahead"] = behind_n, ahead_n

    # 4. Idempotent: already current — return WITHOUT stashing (P1: leave the
    #    freshly-generated/validated prompts in the worktree untouched).
    if behind_n == 0:
        info["action"] = info["action"] or "already_current"
        return info

    # 5. (b) behind, no agent work -> hard-align. ahead==0 ⇒ no committed work to lose;
    #    _park_dirty() preserves any uncommitted work before the hard reset.
    if ahead_n == 0:
        _park_dirty()
        rc, out = _git_cmd(["reset", "--hard", dev_sha])
        if rc != 0:
            raise BranchSyncError(f"reset --hard to develop failed: {out.strip()[-300:]}", transient=True)
        info["action"] = "fast_forwarded"
        return info

    # 6. (c) behind WITH agent work -> merge develop in (preserve work); abort+block on conflict.
    _park_dirty()
    rc, out = _git_cmd(["-c", "user.name=ai-runner", "-c", "user.email=ai-runner@local",
                        "merge", "--no-ff", "--no-edit", dev_sha])
    if rc != 0:
        _git_cmd(["merge", "--abort"])
        raise BranchSyncError(
            f"merge origin/develop into {branch} CONFLICTED (ahead={ahead_n}); "
            f"manual resolution required:\n{out.strip()[-400:]}", transient=False)
    info["action"] = "merged_develop"
    return info


def _sync_or_block(cycle: int, phase: str) -> str | None:
    """Make the integration branch current before consuming code; fail closed.

    Returns the sync ACTION string on success (truthy: "already_current",
    "fast_forwarded", "merged_develop", "created_from_develop", "resumed_from_remote",
    "skipped_pytest"), or None when the caller must NOT proceed (transient retry or a
    DEVELOP_SYNC_BLOCKED conflict). On a TRANSIENT git/network failure the prior status
    is left UNCHANGED (the same tick re-runs next time, so validated prompts are
    preserved) until ``_SYNC_MAX_TRANSIENT`` retries are exhausted; a merge CONFLICT
    (or exhausted transients) writes the recoverable DEVELOP_SYNC_BLOCKED state. The
    action lets a caller (READY_TO_DISPATCH) detect that the branch actually advanced
    and regenerate prompts before dispatching (never dispatch stale-for-new-code).
    """
    key = f"develop_sync_retry_{cycle}"
    try:
        res = ensure_integration_branch_current(cycle)
        _tick_counter(key, reset=True)
        action = res.get("action") or "already_current"
        if action not in ("already_current", "skipped_pytest"):
            click.secho(
                f"  [SYNC] {res['branch']} <- origin/develop ({action}; "
                f"behind={res.get('behind')} ahead={res.get('ahead')}"
                f"{'; parked dirty tree' if res.get('stashed') else ''})",
                fg="cyan",
            )
        return action
    except Exception as exc:
        # Catch EVERYTHING (not just BranchSyncError): an unexpected error must NOT
        # escape this guard and crash cmd_tick before the tick.lock release (which
        # would leak the lock for the full stale window). Unexpected errors are
        # treated as TRANSIENT (retry in place, then block) — always fail-closed.
        from automation.notification_router import notify_blocked
        from automation.state_writer import write_controller_state
        transient = getattr(exc, "transient", True)  # non-BranchSyncError -> transient
        if not isinstance(exc, BranchSyncError):
            click.secho(
                f"  [SYNC] UNEXPECTED error before {phase} (fail-closed, treated "
                f"transient): {exc!r}", fg="red",
            )
        if transient:
            n = _tick_counter(key, increment=True)
            if n < _SYNC_MAX_TRANSIENT:
                click.secho(
                    f"  [SYNC] transient failure before {phase} "
                    f"(retry {n}/{_SYNC_MAX_TRANSIENT} in place, prompts preserved): {exc}",
                    fg="yellow",
                )
                return None  # status UNCHANGED → next tick re-enters and retries
            click.secho(f"  [SYNC] transient failures exhausted ({n}) — blocking", fg="red")
        # Entering the recoverable BLOCKED state — reset the transient counter so the
        # recovery arm's retries start fresh (the recovery ceiling is the real bound).
        _tick_counter(key, reset=True)
        write_controller_state("DEVELOP_SYNC_BLOCKED", cycle=cycle)
        notify_blocked(
            f"Integration branch could not be made current with origin/develop "
            f"before {phase}: {exc}",
            incident_code="DEVELOP_SYNC_BLOCKED", cycle=cycle,
        )
        click.secho(
            f"  State: DEVELOP_SYNC_BLOCKED — refusing to {phase} on stale/conflicted "
            f"branch.\n  {exc}",
            fg="red", bold=True,
        )
        return None


def _current_repo_touched_files() -> set[str]:
    changed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip().splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip().splitlines()
    return {name for name in changed + untracked if name}


def _record_nonblocking_error(message: str) -> None:
    path = runner_paths.reports_dir() / "nonblocking_errors.json"
    payload: dict[str, object] = {"errors": []}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"errors": []}
    errors = payload.get("errors", [])
    if not isinstance(errors, list):
        errors = []
    errors.append({"timestamp": _now(), "message": message})
    payload["errors"] = errors[-500:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _stage_state_path() -> Path:
    return runner_paths.state_dir() / "stage_state.json"


def _read_stage_state() -> dict:
    path = _stage_state_path()
    if not path.exists():
        return {"current_stage": 2}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"current_stage": 2}


def _write_stage_state(payload: dict) -> None:
    payload["updated_at"] = _now()
    path = _stage_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ── Item 1.2: bounded prompt-regeneration state ───────────────────────────────
# Persisted attempt counter that stops the PROMPT_VALIDATION_FAILED self-heal
# from wedging the loop forever. The 1.3 quality gate now fails degenerate
# prompts, so re-validating the SAME bytes can never recover on its own — we need
# a bounded edge back to regeneration, then fail-closed once exhausted.

# Standard six-agent set used by plan-cycle / validate paths.
_STD_AGENT_SET = ["A", "B", "E", "C", "F", "D"]


def _prompt_regen_state_path() -> Path:
    """Resolve the persisted prompt-regeneration attempt-counter path."""
    return runner_paths.state_dir() / "prompt_regen_state.json"


def _prompt_regen_max_attempts() -> int:
    """Env-tunable max regenerate attempts per cycle (default 3)."""
    raw = os.environ.get("PROMPT_REGEN_MAX_ATTEMPTS")
    if raw is None or raw.strip() == "":
        return 3
    try:
        value = int(raw)
        return value if value >= 0 else 3
    except (TypeError, ValueError):
        return 3


def _prompt_regen_backoff_s() -> float:
    """Env-tunable in-tick backoff seconds (default 0).

    The tick cadence already spaces attempts, so no long in-tick sleep is needed.
    Kept env-tunable so an operator may add spacing without code edits.
    """
    raw = os.environ.get("PROMPT_REGEN_BACKOFF_S")
    if raw is None or raw.strip() == "":
        return 0.0
    try:
        value = float(raw)
        return value if value >= 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _read_prompt_regen_state(cycle: int | None) -> dict:
    """Read the regen attempt counter, resetting attempts when the cycle changes.

    Returns ``{"cycle": int|None, "attempts": int, "last_ts": str}``. A counter
    recorded for a different cycle is treated as 0 attempts (fresh cycle starts
    with a clean budget).
    """
    path = _prompt_regen_state_path()
    default = {"cycle": cycle, "attempts": 0, "last_ts": ""}
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default
    if not isinstance(data, dict):
        return default
    if data.get("cycle") != cycle:
        # Cycle changed → reset the attempt budget for the new cycle.
        return default
    try:
        attempts = int(data.get("attempts", 0))
    except (TypeError, ValueError):
        attempts = 0
    return {
        "cycle": cycle,
        "attempts": max(0, attempts),
        "last_ts": str(data.get("last_ts", "")),
    }


def _write_prompt_regen_state(cycle: int | None, attempts: int) -> None:
    """Persist the regen attempt counter for ``cycle`` atomically-ish."""
    path = _prompt_regen_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cycle": cycle, "attempts": max(0, int(attempts)), "last_ts": _now()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _reset_prompt_regen_state(cycle: int | None = None) -> None:
    """Reset the attempt counter to 0 (used by recover and the heal path)."""
    _write_prompt_regen_state(cycle, 0)


def _quarantine_failing_prompts(cycle: int, failing_agents: list[str]) -> list[str]:
    """Move each failing agent's prompt file into a ``.rejected/`` subdir.

    Removing the rejected bytes from the canonical location is what unblocks the
    resume-from-partial gate in ``claude_prompt_creator`` — otherwise it would
    happily REUSE the rejected prompt (it is "substantial" enough to pass the
    size check) and regeneration would be a no-op, leaving the wedge intact.

    Returns the list of agents whose prompt was actually moved (existing files).

    The rejected copies are archived UNDER THE RUNNER STATE ROOT (outside the
    repo worktree), not under PM_Pack/automation/prompts, so quarantining never
    leaves untracked files in the working tree (which would otherwise trip the
    dirty-repo guard / status-tick BLOCKED_DIRTY_REPO — Codex P2 on #114).
    """
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    rejected_dir = runner_paths.state_dir() / "rejected_prompts" / f"CYCLE_{cycle:03d}"
    moved: list[str] = []
    for agent in failing_agents:
        src = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent}_PROMPT.md"
        if not src.exists():
            continue
        rejected_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        dst = rejected_dir / f"{src.stem}_{ts}.md"
        try:
            src.rename(dst)
            moved.append(agent)
        except OSError:
            # Last resort: unlink so the rejected bytes cannot be reused.
            try:
                src.unlink()
                moved.append(agent)
            except OSError:
                pass
    return moved


def _force_regenerate_failing_prompts(cycle: int, failing_agents: list[str]) -> int:
    """Force regeneration of only the FAILING agents and return the rc.

    Reuses the 1.1 generation path: it quarantines the rejected prompts (so the
    resume-from-partial gate cannot reuse them) and then shells out to the
    canonical ``plan-cycle --live`` sub-command — the same pattern the
    COMPILED / PLANNING / BLOCKED_STAGE2 self-heal branches use. ``plan-cycle``
    re-validates every agent, but only the agents whose prompt we just moved
    aside are actually regenerated (the rest are cheaply reused), so this is a
    targeted regeneration of the failing agents while reusing the full path.

    Mocked in tests so no real Claude is invoked.
    """
    moved = _quarantine_failing_prompts(cycle, failing_agents)
    click.secho(
        f"  Quarantined rejected prompts for agents {moved or failing_agents} "
        "→ runner-state rejected_prompts/ (out of worktree; resume cannot reuse them)",
        fg="yellow",
    )
    rc, out = _run_shell_command(
        [sys.executable, "automation/ai_cycle_controller.py", "plan-cycle",
         "--live", "--cycle", str(cycle)]
    )
    if rc != 0:
        click.secho(f"  plan-cycle (regen) rc={rc}: {out.strip()[-200:]}", fg="yellow")
    return rc


@click.group()
def cli() -> None:
    """Fiverr Research System — Autonomous Development Runner."""
    pass


@cli.command("brain-check")
def cmd_brain_check() -> None:
    """Load all PM_Pack brain files and verify they exist and are readable."""
    click.echo("=" * 60)
    click.echo("BRAIN CHECK - Fiverr Autonomous Runner")
    click.echo("=" * 60)

    result = brain_check(REPO_ROOT)

    for msg in result.passed:
        click.echo(f"  [PASS] {msg}")
    for msg in result.warnings:
        click.secho(f"  [WARN] {msg}", fg="yellow")
    for msg in result.failed:
        click.secho(f"  [FAIL] {msg}", fg="red")

    click.echo()
    if result.cycle_detected:
        click.echo(f"  Cycle detected  : {result.cycle_detected}")
    if result.wave_detected:
        click.echo(f"  Wave detected   : {result.wave_detected}")
    if result.blockers_detected:
        click.echo(f"  Blockers        : {', '.join(result.blockers_detected[:3])}")
    click.echo(f"  Cursor model    : {result.cursor_model_status}")
    click.echo(f"  Claude billing  : {result.claude_model_status}")
    click.echo(f"  Post-cycle prompt: {'OK' if result.post_cycle_prompt_present else 'MISSING'}")

    # CLAUDE-SUB-002/004: API key absence check
    from automation.claude_sub_gate import check_api_key_absent
    api_check = check_api_key_absent()
    if not api_check["passed"]:
        click.secho(f"  [WARN] ANTHROPIC_API_KEY detected -- run: {api_check.get('report', 'see report')}", fg="yellow")
    else:
        click.echo("  CLAUDE-SUB      : API key absent (subscription-only confirmed)")
    claude_state_path = runner_paths.state_dir() / "claude_model_state.json"
    if claude_state_path.exists():
        try:
            claude_state = json.loads(claude_state_path.read_text(encoding="utf-8"))
            if claude_state.get("status") == "VERIFIED":
                click.echo(
                    "  PASS [claude-sub-006]: Claude Sonnet 4.6 medium adaptive thinking confirmed"
                )
            else:
                click.secho(
                    "  WARN [claude-sub-006]: claude_model_state.json present but status != VERIFIED",
                    fg="yellow",
                )
        except json.JSONDecodeError:
            click.secho(
                "  WARN [claude-sub-006]: claude_model_state.json unreadable (non-blocking)",
                fg="yellow",
            )
    else:
        click.secho(
            "  WARN [claude-sub-006]: claude_model_state.json not found (non-blocking)",
            fg="yellow",
        )

    click.echo()

    if result.ok:
        click.secho("BRAIN CHECK PASS", fg="green", bold=True)
        raise SystemExit(0)
    else:
        click.secho(f"BRAIN CHECK FAIL — {len(result.failed)} missing file(s)", fg="red", bold=True)
        raise SystemExit(1)


@cli.command("compile-policy")
def cmd_compile_policy() -> None:
    """Compile PM_Pack rules into current_policy_snapshot.json."""
    click.echo("=" * 60)
    click.echo("COMPILE POLICY")
    click.echo("=" * 60)

    snapshot = compile_policy(REPO_ROOT)
    out = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
    click.echo(f"  Cycle   : {snapshot.get('cycle_current')}")
    click.echo(f"  Wave    : {snapshot.get('active_wave')}")
    click.echo(f"  E2E     : {snapshot.get('e2e_score_pct')}%")
    click.echo(f"  Agents  : {snapshot.get('active_agent_lanes')}")
    click.echo(f"  Cursor  : {snapshot.get('cursor_model', {}).get('status')}")
    click.echo()
    click.secho(f"Policy snapshot written to: {out}", fg="green")


@cli.command("jira-inventory")
@click.option("--dry-run", is_flag=True, default=False, help="No Jira writes.")
@click.option("--project", default="SCRUM", help="Jira project key.")
def cmd_jira_inventory(dry_run: bool, project: str) -> None:
    """Fetch Jira board inventory — all non-Done issues."""
    click.echo("=" * 60)
    click.echo(f"JIRA BOARD INVENTORY {'[DRY RUN]' if dry_run else ''}")
    click.echo("=" * 60)

    jira_token = get_secret("JIRA_API_TOKEN")
    if not jira_token or jira_token in ("DO_NOT_COMMIT", "FILL_IN_BEFORE_USE"):
        click.secho("  Jira credentials not set. Add JIRA_EMAIL and JIRA_API_TOKEN", fg="yellow")
        click.secho("  to C:\\AI_Runner\\secrets\\runner.env before running.", fg="yellow")
        click.echo()
        click.secho("  SKIPPED — no credentials", fg="yellow")
        raise SystemExit(0)

    from automation.jira_client import board_inventory
    try:
        inv = board_inventory(project)
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        out_dir = REPO_ROOT / f"PM_Pack/automation/runs/{run_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "board_inventory.json"
        out_path.write_text(json.dumps(inv, indent=2))

        click.echo(f"  Total non-Done issues : {inv['total']}")
        for issue in inv["issues"][:10]:
            click.echo(f"    [{issue['status']}] {issue['key']} — {issue['summary'][:60]}")
        fiverr_matches = [
            issue
            for issue in inv["issues"]
            if "fiverr" in issue.get("summary", "").lower()
            or "fiverr-e" in issue.get("summary", "").lower()
            or any("fiverr" in str(label).lower() for label in issue.get("labels", []))
        ]
        if fiverr_matches:
            click.echo(f"  Fiverr-related issues in inventory: {len(fiverr_matches)}")
            for issue in fiverr_matches[:5]:
                click.echo(f"    [FIVERR] {issue['key']} — {issue['summary'][:60]}")
        if inv["total"] > 10:
            click.echo(f"    ... and {inv['total'] - 10} more")
        click.echo()
        if dry_run:
            click.secho(f"DRY RUN — board_inventory.json written to {out_path}", fg="green")
        else:
            click.secho(f"Board inventory written to {out_path}", fg="green")
    except Exception as exc:
        click.secho(f"  Jira inventory failed: {exc}", fg="red")
        raise SystemExit(1) from exc


@cli.command("jira-hydrate")
@click.option("--file", "epics_file", default=None, type=click.Path(exists=True), help="Epic seed markdown file.")
def cmd_jira_hydrate(epics_file: str | None) -> None:
    """Hydrate Jira epics from a markdown seed file (best-effort, non-blocking)."""
    epic_keys = [f"FIVERR-E{i}" for i in range(1, 7)]
    if epics_file:
        click.echo(f"Jira hydrate source: {epics_file}")
    click.echo("Hydration mode: documentation-first fallback (no direct Jira write in this command).")
    click.echo("Epic keys:")
    for key in epic_keys:
        click.echo(f"  - {key}")
    click.secho("JIRA_HYDRATE_COMPLETE (fallback)", fg="green")


@cli.command("status")
def cmd_status() -> None:
    """Show current controller and runner state."""
    click.echo("=" * 60)
    click.echo("CONTROLLER STATUS")
    click.echo("=" * 60)

    state = _read_runner_state()
    if state:
        click.echo(f"  Runner          : {state.get('runner')}")
        click.echo(f"  Active cycle    : {state.get('active_cycle')}")
        click.echo(f"  Active branch   : {state.get('active_branch')}")
        click.echo(f"  Active PR       : {state.get('active_pr')}")
        click.echo(f"  Status          : {state.get('status')}")
        click.echo(f"  Last heartbeat  : {state.get('last_heartbeat')}")
        click.echo(f"  Last run ID     : {state.get('last_run_id')}")
    else:
        click.echo("  No controller state found — controller has not run yet.")

    # Show model states
    cursor_state_path = runner_paths.state_dir() / "cursor_model_state.json"
    if cursor_state_path.exists():
        cs = json.loads(cursor_state_path.read_text())
        click.echo(f"  Cursor model    : {cs.get('observed_model')} [{cs.get('status')}]")

    # Show GitHub runner service
    import subprocess
    svc = subprocess.run(
        ["powershell", "-Command",
         "Get-Service 'actions.runner.*' | Select-Object -First 1 | ForEach-Object { $_.Status }"],
        capture_output=True, text=True
    )
    svc_status = svc.stdout.strip() or "unknown"
    click.echo(f"  GitHub runner   : {svc_status}")

    # Show snapshot if present
    snap = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
    if snap.exists():
        s = json.loads(snap.read_text())
        click.echo(f"  Policy snapshot : cycle={s.get('cycle_current')} wave={s.get('active_wave')}")
    else:
        click.secho("  Policy snapshot : not yet compiled (run compile-policy)", fg="yellow")


@cli.command("plan-cycle")
@click.option("--dry-run", is_flag=True, default=False,
              help="Generate manifest only, do not generate real prompts.")
@click.option("--live", is_flag=True, default=False,
              help="Generate real prompts from PM_Pack + Jira (requires pm-pack-audit PASS).")
@click.option("--cycle", default=None, type=int, help="Cycle number override.")
@click.option("--agents", "agents_csv", default=None,
              help="Comma-separated agent subset (e.g. 'B') to (re)generate. "
                   "Default = all active lanes. Use to regenerate a single agent's "
                   "prompt without redoing the others, or for a single-agent canary.")
def cmd_plan_cycle(dry_run: bool, live: bool, cycle: int | None,
                   agents_csv: str | None) -> None:
    """Plan next cycle.

    --dry-run: Generates only a manifest and stub placeholders (safe).
    --live: Generates real prompts from PM_Pack + Jira (requires pm-pack-audit PASS + unfrozen).
    --agents: optional comma-separated subset (e.g. 'B') to (re)generate only those.

    Default behavior (no flags): dry-run mode for safety.
    """
    # Default to dry-run if neither flag is set
    if not dry_run and not live:
        dry_run = True
    click.echo("=" * 60)
    click.echo(f"PLAN CYCLE {'[DRY RUN]' if dry_run else '[LIVE]'}")
    click.echo("=" * 60)

    # Get current cycle from policy snapshot
    snap_path = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
    if not snap_path.exists():
        click.secho("  Run compile-policy first.", fg="red")
        raise SystemExit(1)

    snap = json.loads(snap_path.read_text())
    # CYCLE_CURRENT in HYDRATION_HEADER means the cycle we are about to work on.
    # Do NOT add +1 — it is already the target cycle.
    current_cycle = snap.get("cycle_current", 75)
    next_cycle = cycle if cycle is not None else current_cycle
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    branch = f"cycle/{next_cycle:03d}/integration"

    out_dir = REPO_ROOT / f"PM_Pack/automation/runs/{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "cycle": next_cycle,
        "branch": branch,
        "base_branch": "develop",
        "agents": snap.get("active_agent_lanes", ["A", "B", "E", "C", "F", "D"]),
        "dry_run": dry_run,
        # placeholder; possibly narrowed by --agents just below
    }
    # --agents subset: regenerate only the named agents (e.g. a single-agent canary).
    if agents_csv:
        _subset = [a.strip().upper() for a in agents_csv.split(",") if a.strip()]
        _valid = [a for a in _subset if a in manifest["agents"]]
        if not _valid:
            click.secho(
                f"  --agents {agents_csv!r} matched no active lanes "
                f"{manifest['agents']}; nothing to do.", fg="red")
            raise SystemExit(1)
        click.secho(f"  Agent subset (--agents): {_valid}", fg="cyan")
        manifest["agents"] = _valid
    manifest.update({
        "planned_at": _now(),
        "quality_gates": snap.get("quality_gates", {}),
        "jira_policy": snap.get("jira_policy", {}),
        "status": "PLANNED_DRY_RUN" if dry_run else "PLANNED",
    })

    manifest_path = out_dir / f"CYCLE_{next_cycle:03d}_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Write stub prompt files for each agent
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for agent in manifest["agents"]:
        stub_path = prompts_dir / f"CYCLE_{next_cycle:03d}_AGENT_{agent}_PROMPT.md"
        if not stub_path.exists():
            stub_path.write_text(
                f"# Cycle {next_cycle:03d} Agent {agent} Prompt\n\n"
                f"[STUB — populate from PM_Pack PROMPT_TEMPLATE.md + Jira board inventory]\n\n"
                f"Branch: {branch}\n"
                f"Generated: {_now()}\n"
            )

    if dry_run:
        click.echo(f"  Cycle           : {next_cycle:03d}")
        click.echo(f"  Branch          : {branch}")
        click.echo(f"  Agents          : {manifest['agents']}")
        click.echo(f"  Run ID          : {run_id}")
        click.echo()
        click.echo(f"  Manifest        : {manifest_path}")
        click.echo(f"  Prompt stubs    : PM_Pack/automation/prompts/CYCLE_{next_cycle:03d}_AGENT_*.md")
        click.echo()
        click.secho("PLAN CYCLE DRY RUN COMPLETE", fg="green", bold=True)
        # M-STATE-1 FIX: use write_controller_state (read-merge-write) not raw _write_runner_state
        from automation.state_writer import write_controller_state as _wcs
        _wcs("PLANNED", cycle=next_cycle, branch=branch, run_id=run_id)
        return

    # ── LIVE: Generate real prompts from PM_Pack + Jira ──────────────
    click.echo("  Fetching Jira board inventory...")
    from automation.jira_client import board_inventory

    try:
        inv = board_inventory()
        jira_issues = inv.get("issues", [])
        click.echo(f"  Jira issues loaded: {len(jira_issues)}")
    except Exception as e:
        click.secho(f"  [WARN] Jira inventory failed: {e}", fg="yellow")
        jira_issues = []

    # Fetch all issues (including Done) separately for the PM brief so that
    # already-completed Wave 11 stories (e.g. SCRUM-207) are correctly shown
    # as Done in the brief — preventing agents from rebuilding completed work.
    # (Codex review thread PRRT_kwDOSbqwNc6KA22z — addressed here)
    try:
        from automation.jira_client import board_inventory_all
        all_inv = board_inventory_all()
        all_jira_issues = all_inv.get("issues", [])
    except Exception:
        all_jira_issues = jira_issues  # fallback to non-Done list

    # Filter 1: automation runner control tickets
    import re as _re
    _ctrl_labels = {"control-ticket", "automation-runner"}
    _ctrl_summary_pattern = _re.compile(r"^CYCLE-0\d{2,3}\s", _re.IGNORECASE)
    # Filter 2: [JIRA] admin import tasks (e.g. "[JIRA] Prepare Wave 20 product task...")
    _jira_admin_pattern = _re.compile(r"^\s*\[JIRA\]", _re.IGNORECASE)

    filtered_issues = [
        issue for issue in jira_issues
        if not (
            _ctrl_labels & set(issue.get("labels", []))
            or _ctrl_labels & set(issue.get("fields", {}).get("labels", []))
            or _ctrl_summary_pattern.match(issue.get("summary", ""))
            or _ctrl_summary_pattern.match(issue.get("fields", {}).get("summary", ""))
            or _jira_admin_pattern.match(issue.get("summary", ""))
            or _jira_admin_pattern.match(issue.get("fields", {}).get("summary", ""))
        )
    ]
    excluded = len(jira_issues) - len(filtered_issues)
    if excluded:
        click.echo(f"  Excluded {excluded} control/admin ticket(s) from agent scope")
    jira_issues = filtered_issues

    # Filter 3: When Wave 11 stories exist and are open, prioritise them.
    # Check for open Wave 11 [PLAYBOOK] stories — if any exist, put them first.
    _playbook_stories = [i for i in jira_issues
                         if "[PLAYBOOK]" in (i.get("summary", "") or
                                             i.get("fields", {}).get("summary", ""))]
    _other_stories    = [i for i in jira_issues if i not in _playbook_stories]

    if _playbook_stories:
        # Agents should focus on Wave 11 playbook first, then supplemental context
        jira_issues = _playbook_stories + _other_stories
        click.echo(f"  Priority ordering: {len(_playbook_stories)} [PLAYBOOK] stories first")

    click.echo("  Generating real agent prompts from PM_Pack + Jira...")

    # ── PM Intelligence: build wave context brief ─────────────────────
    # Pass all_jira_issues (incl. Done) so the brief correctly marks SCRUM-207
    # and other Done stories, while jira_issues (non-Done only) drives task selection.
    click.echo("  Building PM intelligence cycle brief...")
    from automation.pm_intelligence import build_cycle_brief
    cycle_brief = build_cycle_brief(jira_issues=all_jira_issues)
    _snap = cycle_brief.snapshot
    click.echo(
        f"  PM brief: Wave {_snap.current_wave} ({_snap.wave_name}) | "
        f"{len(_snap.current_stories)} stories | "
        f"{len(_snap.existing_src)} existing src files scanned"
    )

    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"

    # ── Claude-as-PM: generate prompts via Claude subscription ────────
    # Claude acts as the intelligent Project Manager — reads all project plans,
    # Jira AC/DOD, wave state, and generates rich context-aware agent prompts.
    # This is the PRIMARY prompt generation path (matches original architecture).
    # Falls back to template-based prompt_generator.py if Claude is unavailable.
    written: dict[str, Path] | None = None
    from automation.claude_prompt_creator import create_agent_prompts_via_claude

    # PQ-4 FIX: Live subscription probe BEFORE attempting generation.
    # Previously _verify_claude_subscription() only checked env vars and a flag file
    # -- never actually invoked the CLI. A broken/logged-out/rate-limited subscription
    # passed preflight then silently failed and fell back to templates.
    click.echo("  [1/3] Probing Claude subscription (live liveness check)...")
    import time as _tm
    _probe_start = _tm.time()
    try:
        from automation.claude_prompt_creator import _find_claude_binary
        _claude_bin = _find_claude_binary()
        if not _claude_bin:
            raise RuntimeError("claude binary not found — check installation")
        import subprocess as _sub
        # Use only flags supported by the Claude subscription CLI
        # --trust and --force are Cursor-specific flags; claude.EXE does not support them
        _probe = _sub.run(
            [_claude_bin, "--print", "-p", "Reply OK"],
            capture_output=True, text=True, timeout=30,
        )
        _probe_latency_ms = int((_tm.time() - _probe_start) * 1000)
        _probe_ok = _probe.returncode == 0 and len((_probe.stdout or "").strip()) > 0
        if _probe_ok:
            click.secho(
                f"  CLAUDE SUBSCRIPTION: OK  (latency={_probe_latency_ms}ms, "
                f"binary={_claude_bin})",
                fg="green", bold=True,
            )
        else:
            raise RuntimeError(
                f"probe returned rc={_probe.returncode} "
                f"stdout={(_probe.stdout or '').strip()[:100]} "
                f"stderr={(_probe.stderr or '').strip()[:100]}"
            )
    except Exception as _probe_exc:
        click.secho(
            f"  CLAUDE SUBSCRIPTION: FAIL — {_probe_exc}",
            fg="red", bold=True,
        )
        click.secho(
            "  PQ-4: Claude subscription probe failed. Prompts will NOT be generated "
            "via Claude. Marking cycle as DEGRADED and halting plan-cycle.",
            fg="red",
        )
        # Pause the autopilot so the operator sees this and can investigate
        _write_pause("CLAUDE_SUBSCRIPTION_FAIL", detail=str(_probe_exc))
        raise SystemExit(1) from _probe_exc

    click.echo("  [2/3] Attempting Claude-as-PM prompt generation (primary path)...")
    # Audit [D]: render the PM intelligence brief (SECTION 0 — built/done/next +
    # existing src) ONCE and inject it into every agent prompt so agents don't rebuild
    # completed work. Previously the brief was built (cycle_brief) then DISCARDED.
    try:
        _brief_section = cycle_brief.to_prompt_section()
    except Exception as _bexc:
        click.secho(f"  [WARN] cycle_brief.to_prompt_section failed ({_bexc}) — no SECTION 0", fg="yellow")
        _brief_section = ""
    try:
        written = create_agent_prompts_via_claude(
            cycle=next_cycle,
            branch=branch,
            jira_issues=jira_issues,
            agents=manifest["agents"],
            prompts_dir=prompts_dir,
            wave=_snap.current_wave,
            brief_section=_brief_section,
        )
        if written and set(written.keys()) == set(manifest["agents"]):
            click.secho(
                f"  Claude PM: ALL {len(written)}/{len(manifest['agents'])} agent prompts generated via Claude subscription",
                fg="green", bold=True,
            )
        elif written:
            # Partial: some agents failed -- still a hard failure
            missing = set(manifest["agents"]) - set(written.keys())
            click.secho(
                f"  CLAUDE PM PARTIAL: {len(written)}/{len(manifest['agents'])} agents OK, "
                f"missing: {sorted(missing)}. Claude is a hard dependency -- all agents required. "
                "Autopilot PAUSED.", fg="red", bold=True,
            )
            _write_pause("CLAUDE_PM_PARTIAL", detail=f"missing: {sorted(missing)}")
            raise SystemExit(1) from None
        else:
            click.secho(
                "  CLAUDE PM UNAVAILABLE -- Claude returned None (timeout/short-output/error). "
                r"Autopilot PAUSED. Check C:\AI_Runner\tmp\claude_pm_agent_*.err",
                fg="red", bold=True,
            )
            _write_pause("CLAUDE_PM_RETURNED_NONE")
            raise SystemExit(1) from None
    except SystemExit:
        raise
    except Exception as e:
        click.secho(
            f"  ⚠  CLAUDE PM EXCEPTION: {e}\n"
            "  Autopilot PAUSED. Investigate before resuming.",
            fg="red", bold=True,
        )
        _write_pause("CLAUDE_PM_EXCEPTION", detail=str(e))
        raise SystemExit(1) from e

    click.echo("  [3/3] Prompts generated via Claude subscription ✓")
    # NOTE: There is NO template fallback. Claude is a hard dependency.
    # If Claude is unavailable, the probe above already raised SystemExit(1)
    # and paused the autopilot. If written is falsy, SystemExit(1) was also
    # raised. This fallback block was removed to make that explicit.

    click.echo(f"  Cycle           : {next_cycle:03d}")
    click.echo(f"  Branch          : {branch}")
    click.echo(f"  Agents          : {manifest['agents']}")
    click.echo(f"  Run ID          : {run_id}")
    click.echo()
    for agent_id, path in written.items():
        size = path.stat().st_size
        click.echo(f"  Prompt Agent {agent_id}: {path} ({size} bytes)")
    click.echo()
    click.secho("PLAN CYCLE COMPLETE — prompts generated from PM_Pack + Jira", fg="green", bold=True)

    # M-STATE-1 FIX: use write_controller_state (read-merge-write) not raw _write_runner_state
    from automation.state_writer import write_controller_state as _wcs2
    _wcs2("PLANNED", cycle=next_cycle, branch=branch, run_id=run_id)


@cli.command("validate-prompts")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--agents", default="A,B,E,C,F,D", help="Comma-separated agent list.")
def cmd_validate_prompts(cycle: int, agents: str) -> None:
    """Validate generated prompt files for a cycle before dispatch."""
    click.echo("=" * 60)
    click.echo(f"VALIDATE PROMPTS — Cycle {cycle:03d}")
    click.echo("=" * 60)

    from automation.prompt_validator import validate_all
    agent_list = [a.strip() for a in agents.split(",")]
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    validated_dir = prompts_dir / "validated"
    if cycle == 81:
        cycle_marker = f"{cycle:03d}"
        validated_hits = list(validated_dir.glob(f"*{cycle_marker}*")) if validated_dir.exists() else []
        prompt_hits = list(prompts_dir.glob(f"CYCLE_{cycle_marker}_AGENT_*_PROMPT.md"))
        if not validated_hits and not prompt_hits:
            click.secho(
                "No Cycle 081 prompts found in validated/ — Agent E will create them",
                fg="yellow",
            )
            return
    results = validate_all(prompts_dir, cycle, agent_list)

    all_pass = True
    for agent, r in results.items():
        icon = "PASS" if r.passed else "FAIL"
        click.echo(f"  [{icon}] Agent {agent}: {r.prompt_path}")
        for e in r.errors:
            click.secho(f"         ERROR: {e}", fg="red")
        for w in r.warnings:
            click.secho(f"         WARN : {w}", fg="yellow")
        if not r.passed:
            all_pass = False

    click.echo()
    if all_pass:
        click.secho("PROMPT VALIDATION PASS", fg="green", bold=True)
    else:
        click.secho("PROMPT VALIDATION FAIL", fg="red", bold=True)
        raise SystemExit(1)


@cli.command("run-agent")
@click.option("--agent", required=True, help="Agent ID (A/B/E/C/F/D).")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--safe-docs-only", is_flag=True, default=False,
              help="Docs-only test — skips MODEL_GATE hard-fail, warns only.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print what would run without executing Cursor.")
def cmd_run_agent(agent: str, cycle: int, safe_docs_only: bool, dry_run: bool) -> None:
    """Run a single Cursor agent with MODEL_GATE + validation + commit."""
    # ENTRY GUARDS (0.3): direct run-agent also dispatches real Cursor work, so it
    # must honor the same fail-closed pytest-leak guard + autonomy-freeze as the
    # loop (Codex P1 on #110). Skipped for --dry-run (non-dispatching; dry-run
    # paths are permitted while frozen).
    if not dry_run:
        if _refuse_if_leaked_pytest():
            raise SystemExit(1)
        _frozen, _freeze_reason = _is_frozen()
        if _frozen:
            click.secho(
                f"[FROZEN] reason={_freeze_reason}. Autonomy freeze active — "
                "refusing run-agent dispatch. Run 'unfreeze' once cleared.",
                fg="red", bold=True,
            )
            raise SystemExit(1)

    click.echo("=" * 60)
    click.echo(f"RUN AGENT {agent} — Cycle {cycle:03d} {'[DRY RUN]' if dry_run else ''}")
    click.echo("=" * 60)

    from automation.model_gate import check as model_gate_check
    from automation.state_writer import make_run_dir, write_controller_state, write_heartbeat

    # --- MODEL_GATE ---
    click.echo("  [1/5] MODEL_GATE check...")
    gate = model_gate_check(repo_root=REPO_ROOT, cycle=cycle, agent=agent)
    click.echo(gate.summary())
    if not gate.passed:
        if safe_docs_only:
            click.secho("  MODEL_GATE failed but --safe-docs-only set, continuing with warning.", fg="yellow")
        else:
            click.secho("  MODEL_GATE FAILED — aborting dispatch.", fg="red", bold=True)
            write_controller_state("MODEL_BLOCKED", cycle=cycle)
            _record_nonblocking_error(f"run-agent model gate failed cycle={cycle} agent={agent}")
            raise SystemExit(1)

    write_heartbeat("MODEL_GATE_PASSED", cycle=cycle, agent=agent)
    write_controller_state("AGENT_DISPATCH", cycle=cycle)

    # --- Locate prompt ---
    click.echo("  [2/5] Locating prompt...")
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    prompt_path = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent}_PROMPT.md"
    if not prompt_path.exists():
        click.secho(f"  Prompt not found: {prompt_path}", fg="red")
        _record_nonblocking_error(f"run-agent prompt missing cycle={cycle} agent={agent}")
        raise SystemExit(1)
    click.echo(f"  Prompt: {prompt_path}")
    docs_smoke_target = "PM_Pack/automation/prompts/smoke/cursor_docs_smoke_target.md"
    if safe_docs_only:
        docs_target_path = REPO_ROOT / docs_smoke_target
        docs_target_path.parent.mkdir(parents=True, exist_ok=True)
        if not docs_target_path.exists():
            docs_target_path.write_text(
                "# Cursor Docs Smoke Target\n\n"
                "This file is the only safe-docs-only write target.\n",
                encoding="utf-8",
            )
    touched_before = _current_repo_touched_files() if safe_docs_only else set()

    # --- Validate prompt ---
    click.echo("  [3/5] Validating prompt...")
    from automation.prompt_validator import validate as validate_prompt
    pv = validate_prompt(prompt_path, agent, cycle)
    if not pv.passed and not safe_docs_only:
        click.secho(pv.summary(), fg="red")
        _record_nonblocking_error(f"run-agent prompt validation failed cycle={cycle} agent={agent}")
        raise SystemExit(1)
    elif not pv.passed:
        click.secho("  Prompt validation warnings (--safe-docs-only, continuing):", fg="yellow")
        click.echo(pv.summary())
    else:
        click.secho("  Prompt validation PASS", fg="green")

    if dry_run:
        click.echo()
        click.secho(f"  DRY RUN: Would dispatch Cursor with: {prompt_path}", fg="cyan")
        click.secho(f"  DRY RUN: Working dir: {REPO_ROOT}", fg="cyan")
        click.secho("RUN AGENT DRY RUN COMPLETE", fg="green", bold=True)
        return

    # --- Dispatch Cursor ---
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    run_dir = make_run_dir(cycle, run_id)
    agent_dir = run_dir / "agent_runs" / agent

    click.echo(f"  [4/5] Dispatching Cursor agent {agent}...")
    write_heartbeat("CURSOR_RUNNING", cycle=cycle, agent=agent)
    # OBS-14: display provider routing + daily budget before dispatch
    import os as _os_obs14
    if not _os_obs14.environ.get("PYTEST_CURRENT_TEST"):
        try:
            import automation.autopilot_logger as _L_obs14
            _L_obs14.print_provider_budget(cycle=cycle)
        except Exception:
            pass
    _agent_start_time = time.time()

    # OBS-2: update current_activity so the operator can see which agent is running
    import automation.autopilot_logger as _L_obs
    _L_obs.set_activity("AGENT-RUN", cycle=cycle, agent=agent)
    _L_obs.print_stage_matrix(current="AGENT-RUN", agents=["A", "B", "E", "C", "F", "D"])

    # C1 FIX: snapshot HEAD before dispatching Cursor so the post-agent
    # lifecycle ownership check covers only files changed by THIS agent,
    # not accumulated leftovers from prior failed agents/cycles.
    import subprocess as _subprocess_c1
    import os as _os_c1
    _pre_sha_r = _subprocess_c1.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    pre_dispatch_sha = _pre_sha_r.stdout.strip() or None

    # C1.2: Stash any uncommitted leftovers before dispatch so the working tree is
    # clean and the agent starts from a known state.
    #   Fix #3 (prompt-clobber): EXCLUDE the prompts dir from the stash. The current
    #     cycle's prompt is untracked at dispatch (plan-cycle writes but does not
    #     commit it — the Codex-P1 invariant); a plain `--include-untracked` would
    #     stash the agent's own input prompt away BEFORE cursor_run reads it -> empty
    #     dispatch -> 0 commits.
    #   Fix #2 (fail-closed): a non-zero stash means the tree is NOT clean; abort this
    #     dispatch instead of silently running the agent on a dirty tree.
    # Fix #1: pre_existing_dirty is the dirty set (uncommitted+untracked) AFTER the
    # stash and BEFORE the agent runs — i.e. the input prompt plus anything the stash
    # legitimately left. The lifecycle subtracts it so only the agent's own deltas are
    # attributed for the ownership check (correct even if the stash is skipped/fails).
    pre_existing_dirty: set[str] = set()
    if not _os_c1.environ.get("PYTEST_CURRENT_TEST"):
        _stash_r = _subprocess_c1.run(
            ["git", "stash", "push", "--include-untracked",
             "-m", f"pre-agent-{agent}-cycle{cycle:03d}",
             "--", ".", ":(exclude)PM_Pack/automation/prompts/"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
        _stash_out = (_stash_r.stdout or "") + (_stash_r.stderr or "")
        if _stash_r.returncode != 0:
            click.secho(
                f"  [C1.2] git stash FAILED before agent {agent} dispatch — aborting "
                f"(fail-closed; working tree not clean): {_stash_out.strip()[-200:]}",
                fg="red", bold=True,
            )
            _record_nonblocking_error(
                f"run-agent stash-fail cycle={cycle} agent={agent}: {_stash_out.strip()[-200:]}"
            )
            raise SystemExit(1)
        if "No local changes" not in _stash_out:
            click.secho(
                f"  [C1.2] Stashed working-tree leftovers before agent {agent} dispatch "
                "(prompt dir preserved)",
                fg="yellow",
            )

        def _dirty_now() -> set[str]:
            _u = _subprocess_c1.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
            _s = _subprocess_c1.run(
                ["git", "status", "--short", "-uall"],  # list untracked individually (no dir collapse)
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
            paths = {ln.strip().replace("\\", "/") for ln in _u.stdout.splitlines() if ln.strip()}
            paths |= {
                ln[3:].strip().replace("\\", "/")
                for ln in _s.stdout.splitlines() if ln.startswith("?? ")
            }
            return paths

        pre_existing_dirty = _dirty_now()

    from automation.cursor_adapter import run_agent as cursor_run
    # OBS-6: heartbeat thread keeps terminal alive during long Cursor runs
    with _L_obs.HeartbeatThread(f"AGENT-RUN agent={agent} cycle={cycle}", interval=60.0):
        result = cursor_run(
            agent_id=agent,
            prompt_path=str(prompt_path),
            working_dir=str(REPO_ROOT),
            output_dir=str(agent_dir),
            # End the run promptly once the agent writes its AGENT_COMPLETE report,
            # instead of idling until the no-output watchdog (cursor-agent often does
            # not exit cleanly in --print mode after finishing).
            completion_marker=str(
                REPO_ROOT / f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent}.md"
            ),
        )

    _agent_elapsed_min = (time.time() - _agent_start_time) / 60.0
    click.echo(f"  Agent {agent} finished: status={result.status} exit={result.exit_code} "
               f"elapsed={_agent_elapsed_min:.1f}min")

    # H4 FIX: treat suspiciously fast runs as a FAILED dispatch, not just a warning.
    # Sub-5-min completions mean --force was missing (shell blocked) or auth failed.
    # Evidence: ledger shows 0.3-4.8 min across all agents repeatedly -- no real work.
    # PYTEST guard: skip this check in test environments (fake Cursor completes in 0s).
    import os as _os
    MIN_EXPECTED_MINUTES = 5.0
    if (_agent_elapsed_min < MIN_EXPECTED_MINUTES
            and result.exit_code == 0
            and not _os.environ.get("PYTEST_CURRENT_TEST")):
        click.secho(
            f"  [FAIL] Agent {agent} completed in {_agent_elapsed_min:.1f}min "
            f"(floor: {MIN_EXPECTED_MINUTES}min for a real multi-task build). "
            "Treating as failed dispatch — shell execution was likely blocked. "
            "Verify --print --force --trust flags and Cursor auth.",
            fg="red", bold=True,
        )
        _record_nonblocking_error(
            f"run-agent fast-fail: cycle={cycle} agent={agent} "
            f"elapsed={_agent_elapsed_min:.1f}min < {MIN_EXPECTED_MINUTES}min floor"
        )
        # H4 FIX: exit non-zero so run-cycle counts this as a failure, not done
        raise SystemExit(1)

    # Audit #7: "complete" is the ONLY success status (cursor_adapter: complete|timeout|
    # no_output|error|model_blocked). A non-complete status means cursor was TERMINATED
    # before finishing (hard timeout, no-output watchdog kill, spawn error, model gate) —
    # the agent did NOT finish its work/report. Running the post-agent lifecycle on a
    # killed run mislabels it (NO_REPORT / spurious OWNERSHIP) and buries the real cause,
    # with no retry. Fail CLEANLY here so run-cycle counts a failed agent (→ bounded
    # re-dispatch via POST_CYCLE_FAIL recovery) instead of a misleading lifecycle verdict.
    if (str(getattr(result, "status", "")).lower() != "complete"
            and not _os.environ.get("PYTEST_CURRENT_TEST")):
        # Codex P1: a killed agent may have left STAGED/dirty files — run the secret
        # guard BEFORE failing, else the next dispatch could STASH the dirty tree and
        # hide an unsafe artifact. A secret-like file routes to BLOCKED_EXPORT_SECRETS
        # (operator halt) exactly like the normal lifecycle path; otherwise fail clean.
        try:
            _chg = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            ).stdout
            _changed_paths = []
            for _ln in _chg.splitlines():
                _p = _ln[3:].strip() if len(_ln) > 3 else ""
                if " -> " in _p:  # rename entry — scan the destination path
                    _p = _p.split(" -> ", 1)[1].strip()
                if _p:
                    _changed_paths.append(_p)
            from automation import export_sanitizer_verify
            from automation.export_sanitizer_verify import ExportSecretError
            export_sanitizer_verify.verify_staged_files(_changed_paths)
        except ExportSecretError as _sec:
            write_controller_state("BLOCKED_EXPORT_SECRETS", cycle=cycle)
            click.secho(
                f"  BLOCKED_EXPORT_SECRETS: killed agent {agent} left secret-like file(s): {_sec}",
                fg="red", bold=True,
            )
            _record_nonblocking_error(
                f"run-agent killed-agent export-secret block cycle={cycle} agent={agent}: {_sec}"
            )
            return
        except Exception:
            pass  # scanner unavailable — fall through to the clean fail
        click.secho(
            f"  [FAIL] Agent {agent} did NOT complete: status={result.status} "
            f"(exit={result.exit_code}). Terminated before finishing — failing the "
            "dispatch (skipping lifecycle to avoid a misleading NO_REPORT verdict).",
            fg="red", bold=True,
        )
        _record_nonblocking_error(
            f"run-agent non-complete cycle={cycle} agent={agent} "
            f"status={result.status} exit={result.exit_code}"
        )
        raise SystemExit(1)

    if result.stdout_tail:
        click.echo(f"  stdout tail:\n{result.stdout_tail[-300:]}")
    if result.error_message:
        click.secho(f"  Error: {result.error_message}", fg="red")
    if safe_docs_only:
        touched_after = _current_repo_touched_files()
        new_touched = sorted(touched_after - touched_before)
        disallowed = [name for name in new_touched if name != docs_smoke_target]
        if disallowed:
            click.secho("  BLOCKED_SAFE_DOCS_SCOPE: non-docs file changes detected", fg="red", bold=True)
            for name in disallowed[:20]:
                click.echo(f"    - {name}")
            _record_nonblocking_error(
                f"run-agent docs scope violation cycle={cycle} agent={agent} files={disallowed[:5]}"
            )
            return

    # --- Post-agent lifecycle (FINDING-009 fix) ---
    # Ownership check, secret guard, report required, full validation, commit, Jira, record
    click.echo("  [5/5] Running post-agent lifecycle...")
    staged_files = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip().splitlines()
    try:
        from automation import export_sanitizer_verify
        from automation.export_sanitizer_verify import ExportSecretError
    except ImportError:
        click.secho(
            "  [WARN] export_sanitizer_verify not importable; skipping staged export sanitizer check.",
            fg="yellow",
        )
    else:
        try:
            export_sanitizer_verify.verify_staged_files(staged_files)
        except ExportSecretError as exc:
            write_controller_state("BLOCKED_EXPORT_SECRETS", cycle=cycle)
            click.secho(f"  BLOCKED_EXPORT_SECRETS: {exc}", fg="red", bold=True)
            _record_nonblocking_error(f"run-agent export secret block cycle={cycle} agent={agent}: {exc}")
            return

    # H5 FIX: Load the agent's contract and pass it to the lifecycle.
    # Previously called with no contract (jira_keys=[], contract=None) so the
    # AgentLifecycle.run's contract.validation_commands block was ALWAYS skipped.
    # PM_Pack/automation/prompt_contracts/CYCLE_NNN_AGENT_X.contract.json
    _contract: dict | None = None
    try:
        import json as _json_h5
        _contract_path = (
            REPO_ROOT / f"PM_Pack/automation/prompt_contracts/"
            f"CYCLE_{cycle:03d}_AGENT_{agent}.contract.json"
        )
        if _contract_path.exists():
            _contract = _json_h5.loads(_contract_path.read_text(encoding="utf-8"))
            click.echo(f"  Contract loaded: {_contract_path.name}")
        else:
            click.secho(
                f"  [WARN] No contract found at {_contract_path} — "
                "validation_commands will be skipped for this agent.",
                fg="yellow",
            )
    except Exception as _cexc:
        click.secho(f"  [WARN] Contract load error: {_cexc}", fg="yellow")

    from automation.run_agent_lifecycle import run_post_agent_lifecycle
    lifecycle = run_post_agent_lifecycle(
        agent_id=agent,
        cycle=cycle,
        run_id=run_id,
        run_dir=run_dir,
        jira_keys=[],
        contract=_contract,                 # H5 FIX: pass loaded contract
        pre_dispatch_sha=pre_dispatch_sha,  # C1 FIX: scope ownership to this run
        pre_existing_dirty=pre_existing_dirty,  # Fix #1: don't attribute leftovers/prompt
    )

    write_heartbeat("AGENT_COMPLETE", cycle=cycle, agent=agent)
    # C2 FIX: do NOT write AGENT_COMPLETE state here -- only write it after
    # confirming lifecycle.status == "COMPLETE" below.

    click.echo(f"  Lifecycle: {lifecycle.status}")
    for err in lifecycle.errors:
        click.secho(f"  ERROR: {err}", fg="red")

    # RSF-28: validate the agent's report against the report standard (warn mode)
    try:
        from automation.report_validator import validate_report
        report_path = (
            Path(__file__).resolve().parents[1]
            / "docs/cycle_reports"
            / f"CYCLE_{cycle:03d}_AGENT_{agent}.md"
        )
        if report_path.exists():
            rpt_violations = validate_report(report_path, agent_role=agent)
            if rpt_violations:
                click.secho(
                    f"  [ARSF WARN] Agent {agent} report violations: {rpt_violations}",
                    fg="yellow",
                )
            else:
                click.secho(f"  [ARSF] Agent {agent} report: conforming", fg="cyan")
    except Exception as _rve:
        click.secho(f"  [ARSF WARN] report validation error: {_rve}", fg="yellow")

    if lifecycle.status == "COMPLETE":
        # Only write AGENT_COMPLETE when an agent actually committed real work.
        write_controller_state("AGENT_COMPLETE", cycle=cycle)
        sha_info = f" commit={lifecycle.commit_sha}" if lifecycle.commit_sha else ""
        click.secho(f"Agent {agent} COMPLETE{sha_info}", fg="green", bold=True)
    elif lifecycle.status == "NO_WORK":
        # ITEM 2.1: the agent ran clean but committed nothing and is not a
        # justified no-op. This is NOT a hard failure — exit 0 so the run-cycle
        # loop's work-proof cross-check (which reads the empty commit_sha from the
        # run-record) classifies it as NO_WORK rather than FAILED. Do NOT write
        # AGENT_COMPLETE here — a no-work agent has not earned completion.
        click.secho(
            f"Agent {agent} NO_WORK — rc=0 but committed nothing "
            "(work-proof gate will hold the cycle)",
            fg="yellow", bold=True,
        )
        _record_nonblocking_error(
            f"run-agent NO_WORK cycle={cycle} agent={agent}: empty commit_sha, no justified-no-op"
        )
        raise SystemExit(0)
    elif lifecycle.status == "VALIDATION_FAILED":
        click.secho(f"Agent {agent} validation failed â€” routing to repair loop", fg="yellow")
        from automation.repair_loop import dispatch_repair
        repair = dispatch_repair(agent, cycle, run_dir, lifecycle.errors)
        # HIGH-5: HONOR a SUCCESSFUL repair. dispatch_repair re-runs validation AND
        # commits the fix on REPAIRED, so the old unconditional SystemExit(1) routed a
        # genuinely-FIXED cycle to POST_CYCLE_FAIL (the repair loop's whole point was
        # being thrown away). A REPAIRED agent has earned completion.
        if getattr(repair, "status", "") == "REPAIRED":
            write_controller_state("AGENT_COMPLETE", cycle=cycle)
            _rsha = f" commit={repair.commit_sha}" if getattr(repair, "commit_sha", "") else ""
            click.secho(
                f"Agent {agent} REPAIRED{_rsha} — validation now passes", fg="green", bold=True
            )
        else:
            _record_nonblocking_error(
                f"run-agent lifecycle validation failed cycle={cycle} agent={agent} "
                f"repair={getattr(repair, 'status', '?')}: {lifecycle.errors[:3]}"
            )
            # exit non-zero so run-cycle counts this as failed, not done
            raise SystemExit(1)
    else:
        click.secho(
            f"Agent {agent} lifecycle FAILED: {lifecycle.status} (errors: {lifecycle.errors[:3]})",
            fg="red", bold=True,
        )
        _record_nonblocking_error(
            f"run-agent lifecycle non-complete cycle={cycle} agent={agent} status={lifecycle.status}"
        )
        # C2 FIX: OWNERSHIP_VIOLATION/NO_REPORT/SECRET_FOUND must NOT exit 0.
        # Previously this returned (exit 0) making run-cycle count failures as DONE.
        raise SystemExit(1)


@cli.command("run-cycle")
@click.option("--cycle", required=False, type=int, default=None,
              help="Cycle number (auto-detected from controller state if omitted).")
@click.option(
    "--safe-docs-only",
    is_flag=True,
    default=False,
    help="Restrict run-agent scope to docs smoke target.",
)
def cmd_run_cycle(cycle: int | None, safe_docs_only: bool) -> None:
    """Run the full 6-agent cycle then auto-advance stage when ready."""
    # ENTRY GUARD (0.3 / fail-closed): refuse if PYTEST_CURRENT_TEST leaked in
    # without the test harness (a real runner sets neither var → proceeds).
    if _refuse_if_leaked_pytest():
        raise SystemExit(1)

    # SAFE-01 autonomy-freeze kill-switch — fail closed before any dispatch.
    _frozen, _freeze_reason = _is_frozen()
    if _frozen:
        click.secho(
            f"[FROZEN] reason={_freeze_reason}. Autonomy freeze active — "
            "refusing run-cycle. Run 'unfreeze' once freeze conditions are cleared.",
            fg="red",
            bold=True,
        )
        raise SystemExit(1)

    if cycle is None:
        cycle = int(_read_runner_state().get("active_cycle", 0))
        if not cycle:
            click.secho("ERROR: no active_cycle in controller state — run plan-cycle first", fg="red")
            raise SystemExit(1)
        click.echo(f"  (auto-detected cycle={cycle} from controller state)")

    import automation.autopilot_logger as L
    from automation.live_events import emit as _ev, clear as _ev_clear

    _ev_clear()
    L.banner(f"RUN CYCLE {cycle:03d}")
    _ev("CYCLE", f"RUN CYCLE {cycle:03d} started -- 6 agents queued", cycle=cycle)
    agents = ["A", "B", "E", "C", "F", "D"]
    failures: dict[str, str] = {}

    import time as _t
    import json as _json
    _progress_path = runner_paths.state_dir() / "agent_progress.json"
    _progress_path.parent.mkdir(parents=True, exist_ok=True)
    _cycle_start = _t.time()

    def _write_progress(current_agent: str, completed: list, failed: list, agent_elapsed: float = 0.0) -> None:
        """Write agent progress so tick can show live status."""
        prog = {
            "cycle": cycle,
            "current_agent": current_agent,
            "agent_num": agents.index(current_agent) + 1 if current_agent in agents else 0,
            "total_agents": len(agents),
            "completed": completed,
            "failed": failed,
            "agent_elapsed_s": round(agent_elapsed),
            "cycle_elapsed_s": round(_t.time() - _cycle_start),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        _progress_path.write_text(_json.dumps(prog, indent=2))

    completed_agents: list[str] = []
    _agent_outcomes: dict[str, dict] = {}  # OBS-7
    # ITEM 2.1: work-proof tracking — agents that committed real work (non-empty commit_sha).
    _committed_agents: list[str] = []

    for idx, agent in enumerate(agents, 1):
        prompt_path = REPO_ROOT / f"PM_Pack/automation/prompts/CYCLE_{cycle:03d}_AGENT_{agent}_PROMPT.md"
        prompt_bytes = prompt_path.stat().st_size if prompt_path.exists() else 0
        _ev("AGENT", f"Agent {agent} STARTING [{idx}/{len(agents)}] -- {prompt_bytes//1024}KB prompt", agent=agent, cycle=cycle, status="RUNNING")
        L.agent_start(agent, cycle, prompt_bytes, idx, len(agents))
        # OBS-13: show stage matrix so operator sees which agent is running
        L.print_stage_matrix(current=agent, agents=agents)
        _write_progress(agent, completed_agents, list(failures.keys()))

        args = [
            sys.executable, "automation/ai_cycle_controller.py",
            "run-agent", "--agent", agent, "--cycle", str(cycle),
        ]
        if safe_docs_only:
            args.append("--safe-docs-only")

        t0 = _t.time()
        rc, output = _run_and_stream(args, label=f"Agent {agent}")
        elapsed = _t.time() - t0

        L.agent_done(agent, elapsed, rc == 0, idx, len(agents))
        # OBS-7: accumulate per-agent outcome
        _agent_outcomes[agent] = {
            "status": "COMPLETE" if rc == 0 else "FAILED",
            "elapsed": elapsed,
            "exit_code": rc,
        }
        # C2.2 + ITEM 2.1: Cross-check rc=0 against lifecycle run-record for true
        # completion status AND hard work-proof. This runs ALWAYS (incl. under
        # tests) — the PYTEST_CURRENT_TEST guard was removed so the work-proof
        # gate actually fires and is testable. A no-op cycle must never be
        # silently reported as COMPLETE.
        _effective_rc = rc
        _agent_committed = False  # ITEM 2.1: did THIS agent commit real work?
        _agent_no_work = False    # ITEM 2.1: rc==0 but zero committed work + no justified no-op
        if rc == 0:
            try:
                # Codex P1 (#115): search the WHOLE per-cycle dir, not a fixed
                # agent_runs/<agent> subpath. A real run-agent dispatch writes the
                # record under runs/CYCLE_NNN/<run_id>/ (make_run_dir), so rglob the
                # cycle root (most-recent wins) — else a genuinely-committed cycle
                # would be misread as zero-commit → wrongly marked CYCLE_NO_WORK.
                _rr_dir = runner_paths.runs_dir() / f"CYCLE_{cycle:03d}"
                # Glob the REAL filename written by run_agent_lifecycle._write_record
                # (agent_<agent>_run_record.json). The old `run_record.json` glob
                # matched NOTHING → dead cross-check.
                _rr_candidates = sorted(
                    _rr_dir.rglob(f"agent_{agent}_run_record.json"),
                    key=lambda p: p.stat().st_mtime, reverse=True,
                )
                if not _rr_candidates:
                    # Fall back to any agent run-record in the dir.
                    _rr_candidates = sorted(
                        _rr_dir.rglob("agent_*_run_record.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True,
                    )
                if _rr_candidates:
                    import json as _json_c22
                    _rr = _json_c22.loads(_rr_candidates[0].read_text(encoding="utf-8"))
                    _rr_status = _rr.get("lifecycle_status", _rr.get("status", ""))
                    if _rr_status in ("OWNERSHIP_VIOLATION", "SECRET_FOUND", "NO_REPORT", "VALIDATION_FAILED"):
                        L.warn(f"C2.2: rc=0 but lifecycle record says {_rr_status} -- treating as FAILED")
                        _effective_rc = 1
                    else:
                        # ITEM 2.1: hard work-proof. An agent that produced ZERO
                        # file changes (empty commit_sha) is NOT complete unless it
                        # carries an explicit justified-no-op flag.
                        _commit_sha = str(_rr.get("commit_sha", "") or "").strip()
                        _justified = bool(
                            _rr.get("justified_no_op")
                            or _rr.get("no_work_justified")
                        )
                        if _commit_sha:
                            _agent_committed = True
                        elif not _justified:
                            _agent_no_work = True
                            _effective_rc = 1
            except Exception:
                pass  # run-record missing is fine; trust rc

        if _agent_no_work:
            # ITEM 2.1: rc==0 but no committed work and no justified no-op → NO_WORK.
            # Distinct from FAILED; NOT appended to completed_agents.
            _agent_outcomes[agent]["status"] = "NO_WORK"
            L.warn(
                f"ITEM 2.1: Agent {agent} reported rc=0 but committed NO work "
                f"(empty commit_sha, no justified-no-op flag) -- recording NO_WORK"
            )
            _ev("AGENT", f"Agent {agent} NO_WORK ({elapsed:.0f}s) [{idx}/{len(agents)}]",
                agent=agent, cycle=cycle, status="NO_WORK")
            _write_progress(agent, completed_agents, list(failures.keys()), elapsed)
            continue

        if _effective_rc == 0:
            completed_agents.append(agent)
            if _agent_committed:
                _committed_agents.append(agent)
            _ev("AGENT", f"Agent {agent} DONE ({elapsed:.0f}s) [{idx}/{len(agents)}]", agent=agent, cycle=cycle, status="OK")

            # C3 FIX: Completion gate -- verify AC items in agent report after each COMPLETE run.
            # If AC items are missing, log a warning and attempt ONE re-dispatch (capped).
            _C3_MAX_RETRIES = 1
            try:
                from automation.claude_prompt_creator import verify_jira_ac_completion
                from automation.jira_client import board_inventory as _bi
                _cycle_issues = _bi().get("issues", [])
                _report_path = (REPO_ROOT / f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent}.md")
                _report_text = _report_path.read_text(encoding="utf-8") if _report_path.exists() else ""
                _missing_stories = []
                for issue in _cycle_issues[:30]:
                    ac_result = verify_jira_ac_completion(issue, _report_text)
                    if not ac_result.get("passed") and ac_result.get("missing"):
                        _missing_stories.append(ac_result["key"])

                import os as _os_c3
                if _missing_stories and not _os_c3.environ.get("PYTEST_CURRENT_TEST"):
                    L.warn(
                        f"C3: Agent {agent} — {len(_missing_stories)} stories have unsatisfied AC: "
                        f"{_missing_stories[:5]}"
                    )
                    _ev("AC_GATE", f"Agent {agent} missing AC for: {_missing_stories[:5]}",
                        agent=agent, cycle=cycle, status="WARN")

                    if _agent_outcomes[agent].get("c3_retry_count", 0) < _C3_MAX_RETRIES:
                        L.warn(f"C3: Re-dispatching Agent {agent} (attempt 2/{_C3_MAX_RETRIES + 1})")
                        _retry_args = [
                            sys.executable, "automation/ai_cycle_controller.py",
                            "run-agent", "--agent", agent, "--cycle", str(cycle),
                        ]
                        if safe_docs_only:
                            _retry_args.append("--safe-docs-only")
                        _t0_retry = _t.time()
                        _rc_retry, _out_retry = _run_and_stream(_retry_args, label=f"Agent {agent} [C3-retry]")
                        _elapsed_retry = _t.time() - _t0_retry
                        _agent_outcomes[agent]["c3_retry_count"] = 1
                        _agent_outcomes[agent]["c3_retry_exit_code"] = _rc_retry
                        if _rc_retry != 0:
                            L.warn(f"C3 re-dispatch of Agent {agent} also failed (rc={_rc_retry})")
                        else:
                            L.ok(f"C3 re-dispatch of Agent {agent} succeeded ({_elapsed_retry:.0f}s)")
            except Exception as _c3_exc:
                L.warn(f"C3 AC-gate check failed (non-blocking): {_c3_exc}")
        else:
            failures[agent] = output.strip()
            _ev("AGENT", f"Agent {agent} FAILED ({elapsed:.0f}s)", agent=agent, cycle=cycle, status="FAIL")
            L.agent_fail_detail(agent, output)
            # PQ-5: Surface failure detail to structured log
            if rc != 0:
                L.warn(f"PQ-5: Agent {agent} exit_code={rc} output_tail={output.strip()[-200:]!r}")

        # ICV: verify and repair after each agent (gated by ICV_DISABLED env var)
        import os as _os_icv
        if _effective_rc == 0 and not _os_icv.environ.get("ICV_DISABLED") and not _os_icv.environ.get("PYTEST_CURRENT_TEST"):
            try:
                from automation.codex_verifier import verify_and_repair_agent as _icv_verify
                _contract_path = (
                    REPO_ROOT / f"PM_Pack/automation/prompt_contracts/"
                    f"CYCLE_{cycle:03d}_AGENT_{agent}.contract.json"
                )
                _icv_outcome = _icv_verify(
                    cycle=cycle,
                    agent=agent,
                    prompt_path=str(prompt_path),
                    contract_path=str(_contract_path) if _contract_path.exists() else None,
                    run_dir=str(runner_paths.runs_dir() / f"CYCLE_{cycle:03d}" / "agent_runs" / agent),
                    dispatch_result=None,
                    pre_dispatch_sha=None,
                )
                _agent_outcomes[agent]["icv_status"] = _icv_outcome.status.value
                _agent_outcomes[agent]["icv_score"] = _icv_outcome.completion_score
                L.info(
                    f"ICV outcome for agent {agent}: "
                    f"{_icv_outcome.status.value} score={_icv_outcome.completion_score:.2f}"
                )
            except Exception as _icv_exc:
                L.warn(f"ICV skipped for agent {agent} (non-blocking): {_icv_exc}")

        _write_progress(agent, completed_agents, list(failures.keys()), elapsed)

    # ITEM 2.1 — HARD WORK-PROOF GATE.
    # All agents finished without an outright failure. Before writing
    # AGENT_COMPLETE we require PROOF that at least one agent committed real
    # work (non-empty commit_sha). A cycle in which every agent changed nothing
    # (all NO_WORK) must NEVER report AGENTS_COMPLETE — it must be surfaced as a
    # recoverable CYCLE_NO_WORK state so a later tick can re-run real work.
    from automation.state_writer import write_controller_state as _wcs, write_heartbeat as _wh
    if not failures and not _committed_agents:
        _no_work_agents = [
            ag for ag, outc in _agent_outcomes.items()
            if outc.get("status") == "NO_WORK"
        ] or agents
        L.error(
            f"ITEM 2.1: RUN CYCLE {cycle:03d} produced NO committed work "
            f"({len(_no_work_agents)} agent(s) NO_WORK, 0 commits) -- "
            "refusing AGENT_COMPLETE; writing recoverable CYCLE_NO_WORK"
        )
        # Recoverable state: do NOT advance a do-nothing cycle. Preserve the
        # authoritative active_cycle (omit cycle arg, same as AGENT_COMPLETE).
        _wcs("CYCLE_NO_WORK")
        _wh("CYCLE_NO_WORK", cycle=cycle)
        try:
            from automation.notification_router import notify_blocked
            notify_blocked(
                f"Cycle {cycle:03d} produced no committed work",
                body=(
                    f"All agents reported success (rc=0) but committed nothing. "
                    f"NO_WORK agents: {_no_work_agents}. Cycle was NOT advanced; "
                    "re-run with real work to proceed."
                ),
                incident_code="CYCLE_NO_WORK",
                cycle=cycle,
            )
        except Exception as _nw_exc:
            L.warn(f"CYCLE_NO_WORK notification failed (non-blocking): {_nw_exc}")
        _ev("CYCLE", f"RUN CYCLE {cycle:03d} NO_WORK -- 0 commits, not advancing",
            cycle=cycle, status="FAIL")
        _progress_path.write_text(_json.dumps({
            "cycle": cycle, "current_agent": "DONE",
            "completed": completed_agents, "failed": list(failures.keys()),
            "no_work": _no_work_agents,
            "cycle_elapsed_s": round(_t.time() - _cycle_start),
            "updated_at": datetime.now(UTC).isoformat(),
        }, indent=2))
        L.newline()
        L.cycle_summary(cycle=cycle, agent_outcomes=_agent_outcomes,
                        gate_result="NO_WORK", blocker_name="no_committed_work")
        raise SystemExit(1)

    # All agents done — write AGENT_COMPLETE so tick advances to post-cycle review.
    # Do NOT re-stamp the cycle number here: omitting the `cycle` arg lets the
    # read-merge-write preserve the existing authoritative active_cycle and stops
    # the post-run re-stamp that drove the 82<->84 oscillation.
    _wcs("AGENT_COMPLETE")
    _wh("AGENT_COMPLETE", cycle=cycle)

    # Audit C (zero-intervention): the agents just ran successfully with the FORCED
    # --model codex-5.3 and committed real work — proof the model works. Refresh the
    # model-gate freshness so a continuously-cycling 24/7 runner never trips the 7-day
    # verification expiry (no weekly human re-verification). Safe: only bumps the
    # timestamp when the state is ALREADY a passing VERIFIED config; never false-verifies.
    if _committed_agents:
        try:
            from automation.model_gate import refresh_verified_at_if_verified
            if refresh_verified_at_if_verified():
                L.info("Model-gate freshness refreshed after successful forced-model dispatch")
        except Exception as _mgexc:  # pragma: no cover - non-blocking
            L.warn(f"model-gate freshness refresh failed (non-blocking): {_mgexc}")

    # RSF-19: synthesize agent reports (non-blocking, ARSF_DISABLED-gated)
    import os as _os_arsf19
    if not _os_arsf19.environ.get("PYTEST_CURRENT_TEST"):
        try:
            from automation.report_synthesis import synthesize_cycle as _arsf_synth
            _cs = _arsf_synth(cycle)
            L.info(f"ARSF: cycle {cycle:03d} verdict={_cs.cycle_verdict} format_health={_cs.format_health}")
        except Exception as _arsf_exc:
            L.warn(f"ARSF synthesis failed (non-blocking): {_arsf_exc}")
    # ITEM 3.1 — DETERMINISTIC AUTONOMOUS PR-CREATE.
    # Real committed work exists (_committed_agents non-empty; the CYCLE_NO_WORK
    # path already SystemExit(1)'d above). The Controller is the sole git
    # authority (G1) — open exactly ONE GitHub-verified PR from the cycle branch
    # to develop. open_cycle_pr is idempotent (dup-guard) so a retry tick never
    # double-opens. On ANY failure (no token / push fail / not verified) we FAIL
    # CLOSED: write a recoverable PR_CREATE_FAILED + notify, and SystemExit(1) —
    # never silently proceed to post-cycle without a PR.
    # Gate on `not failures` (Codex P1 #118): if an earlier agent committed but a
    # LATER agent failed, we must NOT publish a PR for a partial/failed cycle —
    # fall through to the failure branch below (which SystemExit(1)s).
    if _committed_agents and not failures:
        from automation import pr_builder
        _pr = pr_builder.open_cycle_pr(cycle)
        _pr_ok = bool(_pr.get("created")) or bool(_pr.get("existing"))
        if _pr_ok:
            _pr_num = _pr.get("pr_number")
            _pr_url = _pr.get("url", "")
            _pr_word = "exists" if _pr.get("existing") else "opened"
            L.ok(
                f"PR {_pr_word} for cycle {cycle:03d}: "
                f"#{_pr_num} {_pr_url}".rstrip()
            )
            _ev("CYCLE", f"PR {_pr_word} #{_pr_num} for cycle {cycle:03d}",
                cycle=cycle, status="OK")
            # Record the PR in controller_state (active_pr) without re-stamping
            # the cycle (preserve the monotonic active_cycle; keep AGENT_COMPLETE).
            if _pr_num:
                _wcs("AGENT_COMPLETE", pr=int(_pr_num))
        else:
            _pr_err = _pr.get("error") or "unknown PR-create failure"
            L.error(
                f"ITEM 3.1: PR-create FAILED for cycle {cycle:03d} ({_pr_err}) "
                "-- failing closed (PR_CREATE_FAILED); not advancing to post-cycle"
            )
            _wcs("PR_CREATE_FAILED")
            _wh("PR_CREATE_FAILED", cycle=cycle)
            try:
                from automation.notification_router import notify_blocked
                notify_blocked(
                    f"Cycle {cycle:03d} PR-create failed",
                    body=(
                        f"open_cycle_pr did not produce a verified PR: {_pr_err}. "
                        "Committed work exists but no PR was opened; a retry tick "
                        "will re-attempt (idempotent dup-guard)."
                    ),
                    incident_code="PR_CREATE_FAILED",
                    cycle=cycle,
                )
            except Exception as _pr_nexc:
                L.warn(f"PR_CREATE_FAILED notification failed (non-blocking): {_pr_nexc}")
            _ev("CYCLE", f"PR-create FAILED for cycle {cycle:03d} -- {_pr_err}",
                cycle=cycle, status="FAIL")
            raise SystemExit(1)

    _progress_path.write_text(_json.dumps({
        "cycle": cycle, "current_agent": "DONE",
        "completed": completed_agents, "failed": list(failures.keys()),
        "cycle_elapsed_s": round(_t.time() - _cycle_start),
        "updated_at": datetime.now(UTC).isoformat(),
    }, indent=2))

    L.newline()
    if failures:
        L.error(f"RUN CYCLE {cycle:03d} FAILED — {len(failures)}/{len(agents)} agents failed: {list(failures.keys())}")
        for agent, detail in failures.items():
            L.info(f"Agent {agent} last output: {detail[-200:]}")
        # OBS-7: summary even on failure
        L.cycle_summary(cycle=cycle, agent_outcomes=_agent_outcomes, gate_result="FAILED",
                        blocker_name=f"agents={list(failures.keys())}")
        raise SystemExit(1)

    # OBS-7: summary on success (gate determined by post-cycle review later)
    L.cycle_summary(cycle=cycle, agent_outcomes=_agent_outcomes, gate_result="AGENTS_COMPLETE")

    from automation.stage_executor import StageExecutor

    executor = StageExecutor(controller=None, config={"cycle": cycle})
    advanced = executor.advance_if_ready()
    if advanced:
        click.echo(f"Stage advanced automatically to {executor.get_current_stage()}")
    else:
        click.echo(f"Stage remains at {executor.get_current_stage()}")
    click.secho("RUN CYCLE COMPLETE", fg="green", bold=True)
    raise SystemExit(0)


@cli.command("cursor-smoke")
def cmd_cursor_smoke() -> None:
    """Run a no-write Cursor smoke test (reads context only)."""
    click.echo("=" * 60)
    click.echo("CURSOR CLI SMOKE TEST")
    click.echo("=" * 60)

    from automation.cursor_adapter import check_version, discover
    discover()
    version = check_version()
    click.echo(f"  Cursor version  : {version}")
    click.echo("  Discovery log   : C:/AI_Runner/logs/cursor_cli_discovery.txt")

    # Write a no-write smoke prompt
    smoke_prompt = (
        "You are running a smoke test only. Do NOT modify any files.\n"
        "Print the current working directory, list top-level files, "
        "and confirm PM_Pack exists. Do not write or commit anything.\n"
    )
    prompt_path = REPO_ROOT / "PM_Pack/automation/prompts/cursor_smoke_test.md"
    prompt_path.write_text(smoke_prompt)
    click.echo(f"  Smoke prompt    : {prompt_path}")
    click.echo()
    click.secho("Cursor CLI is reachable. Model and headless dispatch verified in Wave 04.", fg="green")


@cli.command("cursor-docs-smoke")
def cmd_cursor_docs_smoke() -> None:
    """Run a docs-only smoke command surface check."""
    click.echo("=" * 60)
    click.echo("CURSOR DOCS SMOKE TEST")
    click.echo("=" * 60)
    click.echo("  Command is registered and available.")
    click.echo("  Use this as a lightweight command-surface verification gate.")
    click.secho("CURSOR DOCS SMOKE PASS", fg="green")


@cli.command("validate-routes")
def cmd_validate_routes() -> None:
    """Validate provider policy routes via ProviderRouter."""
    import yaml

    from automation.provider_router import ProviderRouter

    router = ProviderRouter()
    result = router.validate_policy()
    provider_statuses: dict[str, str] = {
        "cursor_cli": "UNKNOWN",
        "claude_subscription": "UNKNOWN",
        "openai_api": "UNKNOWN",
        "codex_subscription": "UNKNOWN",
    }
    policy_path = REPO_ROOT / "PM_Pack/automation/provider_policy.yml"
    if policy_path.exists():
        payload = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
        providers = payload.get("providers", {}) if isinstance(payload, dict) else {}
        if isinstance(providers, dict):
            for provider_name in provider_statuses:
                provider_payload = providers.get(provider_name, {})
                if provider_name == "cursor_cli" and not isinstance(provider_payload, dict):
                    provider_payload = providers.get("cursorcli", {})
                if isinstance(provider_payload, dict):
                    provider_statuses[provider_name] = str(
                        provider_payload.get("status", "ACTIVE" if provider_payload.get("enabled") else "UNKNOWN")
                    ).upper()
    for provider_name, status in provider_statuses.items():
        click.echo(f"{provider_name}: {status}")
    click.echo(f"advisory_only_mode: {router.advisory_only_mode}")
    click.echo(f"advisory_confirm_mode: {router.advisory_confirm_mode}")
    click.echo(str(result))
    raise SystemExit(0 if result.passed else 1)


@cli.command("provider-route-dry-run")
@click.option("--task-type", default="prompt_lint", help="Task type to route.")
@click.option("--cycle", default="080", help="Cycle number to stamp in decision.")
def cmd_provider_route_dry_run(task_type: str, cycle: str) -> None:
    """Run provider router dry-run and print selected route."""
    from automation.provider_router import ProviderRouter

    payload = ProviderRouter().route_dry_run(task_type, cycle=cycle)
    click.echo(str(payload))
    raise SystemExit(0)


@cli.command("routing-advisory-report")
@click.option("--cycle", required=True, type=int, help="Cycle number to report.")
def cmd_routing_advisory_report(cycle: int) -> None:
    """Summarize provider routing decisions and write advisory markdown report."""
    decisions_dir = REPO_ROOT / "PM_Pack/automation/provider_decisions"
    artifacts = sorted(decisions_dir.glob("PROVIDER_DECISION_*.json"))

    provider_counts: dict[str, int] = {}
    task_counts: dict[str, int] = {}
    considered = 0
    cycle_id = f"{cycle:03d}"
    for artifact in artifacts:
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        considered += 1
        provider = str(payload.get("selectedprovider") or payload.get("selected_provider") or "unknown")
        task_type = str(payload.get("tasktype") or payload.get("task_type") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        task_counts[task_type] = task_counts.get(task_type, 0) + 1

    click.echo(f"Routing Advisory — Cycle {cycle_id}")
    click.echo(f"Total decisions: {considered}")
    click.echo("")
    click.echo("By provider:")
    for provider in sorted(provider_counts):
        click.echo(f"  {provider:30} {provider_counts[provider]}")
    click.echo("By task type:")
    for task_type in sorted(task_counts):
        click.echo(f"  {task_type:30} {task_counts[task_type]}")

    out_dir = runner_paths.reports_dir() / "provider_usage"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"CYCLE_{cycle_id}_ROUTING_ADVISORY.md"
    lines = [
        f"# Cycle {cycle_id} Provider Routing Advisory",
        f"Generated: {_now()}",
        "",
        f"Total decisions: {considered}",
        "",
        "## Counts by provider",
    ]
    if provider_counts:
        lines.extend([f"- {provider}: {provider_counts[provider]}" for provider in sorted(provider_counts)])
    else:
        lines.append("- No decisions recorded for this cycle.")
    lines.extend(["", "## Counts by task type"])
    if task_counts:
        lines.extend([f"- {task_type}: {task_counts[task_type]}" for task_type in sorted(task_counts)])
    else:
        lines.append("- No task decisions recorded for this cycle.")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    click.echo("")
    click.secho(f"Routing advisory report written: {out_path}", fg="green")


@cli.command("provider-usage-summary")
def cmd_provider_usage_summary() -> None:
    """Print provider usage spend summary table (daily/weekly/monthly)."""
    from automation.provider_usage_ledger import get_ledger_summary

    summary = get_ledger_summary()
    click.echo("Provider Usage Summary")
    click.echo(f"{'provider':<22} {'daily':>10} {'weekly':>10} {'monthly':>10}")
    for provider, totals in summary.items():
        click.echo(
            f"{provider:<22} "
            f"{float(totals.get('daily', 0.0)):>10.2f} "
            f"{float(totals.get('weekly', 0.0)):>10.2f} "
            f"{float(totals.get('monthly', 0.0)):>10.2f}"
        )


@cli.command("stage2-readiness-check")
def cmd_stage2_readiness_check() -> None:
    """Validate Stage 2 dispatch prerequisites from ADR 027."""
    checks: list[tuple[str, bool, str]] = []
    cycle = int(_read_runner_state().get("active_cycle", 81))

    from automation.model_gate import check as model_gate_check

    gate = model_gate_check(repo_root=REPO_ROOT, cycle=cycle, agent="STAGE2")
    checks.append(("MODELGATE PASS", bool(gate.passed), gate.summary()))

    rc, out = _run_shell_command([sys.executable, "automation/ai_cycle_controller.py", "pm-pack-audit"])
    checks.append(("pm-pack-audit PASS", rc == 0 and "PASS" in out, out.strip().splitlines()[-1] if out else ""))

    rc, out = _run_shell_command(
        [sys.executable, "automation/ai_cycle_controller.py", "validate-prompts", "--cycle", str(cycle)]
    )
    checks.append(
        (
            f"validate-prompts --cycle {cycle:03d} PASS 6/6",
            rc == 0 and "PROMPT VALIDATION PASS" in out,
            out.strip().splitlines()[-1] if out else "",
        )
    )

    manifest_path = REPO_ROOT / "PM_Pack/automation/prompt_package_manifest.json"
    manifest_ok = False
    manifest_detail = "manifest missing"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_ok = manifest.get("status") == "READY" and str(manifest.get("cycle")) == f"{cycle:03d}"
            manifest_detail = f"cycle={manifest.get('cycle')} status={manifest.get('status')}"
        except json.JSONDecodeError:
            manifest_detail = "manifest unreadable JSON"
    checks.append(("prompt_package_manifest READY", manifest_ok, manifest_detail))

    policy_ok = False
    policy_detail = "policy missing"
    policy_path = REPO_ROOT / "PM_Pack/automation/provider_policy.yml"
    if policy_path.exists():
        payload = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        global_rules = payload.get("global_rules", {}) if isinstance(payload, dict) else {}
        advisory_only = bool(global_rules.get("advisory_only_provider_routing", True))
        policy_ok = advisory_only is False
        policy_detail = f"advisory_only={global_rules.get('advisory_only_provider_routing')}"
    checks.append(("provider_policy unrestricted autonomous routing", policy_ok, policy_detail))

    provider_health_path = runner_paths.state_dir() / "provider_health.json"
    provider_ok = False
    provider_detail = "provider health missing"
    if provider_health_path.exists():
        try:
            provider_payload = json.loads(provider_health_path.read_text(encoding="utf-8"))
            cursor_entry = provider_payload.get("cursor_cli") or provider_payload.get("cursorcli") or {}
            provider_ok = str(cursor_entry.get("status", "")).upper() == "READY"
            provider_detail = f"cursor_cli.status={cursor_entry.get('status', 'UNKNOWN')}"
        except json.JSONDecodeError:
            provider_detail = "provider health unreadable JSON"
    checks.append(("cursor_cli status=READY in provider_health", provider_ok, provider_detail))

    click.echo("Stage 2 Readiness Check")
    click.echo(f"{'check':<48} {'result':<6} details")
    for label, passed, detail in checks:
        click.echo(f"{label:<48} {('PASS' if passed else 'FAIL'):<6} {detail}")

    all_passed = all(item[1] for item in checks)
    raise SystemExit(0 if all_passed else 1)


@cli.command("recover")
@click.option("--regen", "--reset-prompts", "regen", is_flag=True,
              help="Reset the prompt-regenerate attempt counter and clear "
                   "PROMPT_REGEN_EXHAUSTED back to COMPILED so the next tick "
                   "re-attempts generation.")
def cmd_recover(regen: bool) -> None:
    """Attempt safe recovery from stale lock or interrupted run."""
    click.echo("=" * 60)
    click.echo("RECOVER")
    click.echo("=" * 60)
    lock_dir = REPO_ROOT / "PM_Pack/automation/locks"
    if lock_dir.exists():
        locks = list(lock_dir.glob("*.lock"))
        if locks:
            for lf in locks:
                click.secho(f"  Found lock: {lf.name} — moving to stale_locks/", fg="yellow")
                stale_dir = lock_dir / "stale_locks"
                stale_dir.mkdir(exist_ok=True)
                from datetime import datetime as dt
                ts = dt.now(UTC).strftime("%Y%m%d_%H%M%S")
                lf.rename(stale_dir / f"{lf.stem}_{ts}.lock")
        else:
            click.echo("  No active locks found.")

    # ── Item 1.2: reset the bounded prompt-regenerate edge ─────────────────
    if regen:
        from automation.state_writer import write_controller_state
        state = _read_runner_state()
        cycle = state.get("active_cycle")
        _reset_prompt_regen_state(cycle)
        click.secho(
            f"  Prompt-regenerate attempt counter reset to 0 (cycle {cycle}).",
            fg="green",
        )
        if state.get("status") == "PROMPT_REGEN_EXHAUSTED":
            write_controller_state("COMPILED", cycle=cycle)
            click.secho(
                "  Cleared PROMPT_REGEN_EXHAUSTED → COMPILED — next tick re-attempts "
                "generation.",
                fg="green",
            )
        else:
            click.secho(
                f"  State is {state.get('status', 'UNKNOWN')} (not PROMPT_REGEN_EXHAUSTED) "
                "— attempts reset only.",
                fg="cyan",
            )

    click.echo("  Run brain-check and compile-policy before restarting.")
    click.secho("RECOVER COMPLETE", fg="green")


@cli.command("stage-status")
def cmd_stage_status() -> None:
    """Print stage state table for stages 2-7."""
    state = _read_stage_state()
    click.echo("Stage Status")
    click.echo(f"{'stage':<8} {'status':<10} {'completed_at':<30} evidence_path")
    for stage in range(2, 8):
        key = f"stage_{stage}"
        entry = state.get(key, {})
        if not isinstance(entry, dict):
            entry = {}
        click.echo(
            f"{stage:<8} {str(entry.get('status', 'UNKNOWN')):<10} "
            f"{str(entry.get('completed_at', '-')):<30} {entry.get('evidence_path', '-')}"
        )


@cli.command("stage-advance")
@click.option("--stage", "stage_num", required=True, type=int, help="Stage number to evaluate.")
def cmd_stage_advance(stage_num: int) -> None:
    """Advance stage based on stage-specific evidence gates."""
    if stage_num < 2 or stage_num > 7:
        click.secho("stage must be between 2 and 7", fg="red")
        raise SystemExit(1)

    evidence_path = runner_paths.reports_dir() / "stages" / f"STAGE{stage_num}_EVIDENCE.json"
    if not evidence_path.exists():
        click.secho(f"Missing evidence file: {evidence_path}", fg="red")
        raise SystemExit(1)

    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        click.secho(f"Unreadable evidence JSON: {evidence_path}", fg="red")
        raise SystemExit(1) from exc

    evidence_status = str(evidence.get("status", "")).upper()
    should_advance = evidence_status == "PASS"
    fail_reason = f"Stage {stage_num} evidence status={evidence_status}; not advancing."
    if stage_num == 2:
        cursor_invoked = bool(evidence.get("cursor_invoked", False))
        should_advance = cursor_invoked
        if not should_advance:
            fail_reason = "Stage 2 requires cursor_invoked=true in evidence."
    elif stage_num == 3:
        pipeline_complete = bool(evidence.get("all_fiverr_pipeline_complete", False))
        pr_opened = bool(evidence.get("pr_opened", False))
        should_advance = pipeline_complete and pr_opened
        if not should_advance:
            fail_reason = (
                "Stage 3 requires all_fiverr_pipeline_complete=true and pr_opened=true in evidence."
            )
    if not should_advance:
        click.secho(fail_reason, fg="yellow")
        raise SystemExit(1)

    stage_state = _read_stage_state()
    stage_key = f"stage_{stage_num}"
    stage_entry = stage_state.get(stage_key, {})
    if not isinstance(stage_entry, dict):
        stage_entry = {}
    stage_entry["status"] = "PASS"
    stage_entry["completed_at"] = stage_entry.get("completed_at") or _now()
    stage_entry["evidence_path"] = str(evidence_path)
    stage_state[stage_key] = stage_entry

    next_stage = stage_num + 1
    if next_stage <= 7:
        next_key = f"stage_{next_stage}"
        next_entry = stage_state.get(next_key, {})
        if not isinstance(next_entry, dict):
            next_entry = {}
        if next_entry.get("status") == "LOCKED":
            next_entry["status"] = "PENDING"
        stage_state[next_key] = next_entry
        stage_state["current_stage"] = next_stage
    else:
        stage_state["current_stage"] = stage_num
    _write_stage_state(stage_state)
    click.secho(f"Stage {stage_num} advanced successfully.", fg="green")
    raise SystemExit(0)


def _release_tick_lock(lock_file: Path) -> None:
    """Release the tick lock. MUST run on EVERY exit path from cmd_tick.

    Audit BLOCKER (cluster A): the release in the tick epilogue is NOT inside a
    ``finally``, so any early ``return`` between lock-acquire and the epilogue skips
    it and LEAKS the lock — every subsequent tick then hits the held-lock guard and
    exits for up to ``_lock_stale_s`` (600s), freezing the state machine. Call this
    immediately before any early return. Best-effort; never raises.
    """
    try:
        if lock_file.exists():
            lock_file.unlink()
    except Exception:
        pass


@cli.command("tick")
def cmd_tick() -> None:
    """
    Tick — real state machine that decides what to do next.

    States and transitions:
      IDLE              → compile-policy, then → PLANNED
      PLANNED           → validate-prompts, then → READY_TO_DISPATCH
      READY_TO_DISPATCH → check post-cycle gate; if clear → DISPATCHING
      DISPATCHING       → agents running (managed externally)
      AGENT_COMPLETE    → run post-cycle-review → POST_CYCLE_REVIEW
      POST_CYCLE_REVIEW → if PASS → IDLE (next cycle)
      POST_CYCLE_PENDING → block dispatch; surface to operator
      MODEL_BLOCKED     → block dispatch; alert model gate failure
    """
    from automation.notification_router import notify_blocked, notify_info
    from automation.state_writer import write_controller_state, write_heartbeat

    # ENTRY GUARD (0.3 / fail-closed): a leaked PYTEST_CURRENT_TEST without the
    # test harness must REFUSE to run rather than silently no-op. A real runner
    # sets neither var → proceeds. Done before pause/lock so a leak never even
    # touches the sentinel or lock.
    if _refuse_if_leaked_pytest():
        return

    # Check pause flag FIRST — before acquiring the run lock, so a paused tick
    # never acquires (and thus never leaks) tick.lock. Item 0.2 kill-switch fix:
    # the PRESENCE of the sentinel pauses the loop. We read it only to surface
    # the reason; a missing/legacy "paused" key or a corrupt file must STILL
    # pause (fail-safe — presence means paused).
    import os as _os_c7
    import time as _time_c7
    _pause_flag = _pause_file_path()
    if _pause_flag.exists():
        import json as _pj
        _reason = "unknown"
        try:
            _pdata = _pj.loads(_pause_flag.read_text(encoding="utf-8-sig"))
            _reason = str(_pdata.get("reason") or _pdata.get("paused") or "unknown")
        except Exception:
            _reason = "corrupt_pause_file"
        click.secho(
            f"[TICK PAUSED] reason={_reason}. "
            "Run 'resume-autopilot' (or delete the autopilot_paused.json sentinel) to resume.",
            fg="yellow",
        )
        return

    # SAFE-01 autonomy-freeze kill-switch — checked right after pause, BEFORE the
    # run lock. If frozen, fail closed: no dispatch, no lock acquired, return.
    _frozen, _freeze_reason = _is_frozen()
    if _frozen:
        click.secho(
            f"[FROZEN] reason={_freeze_reason}. Autonomy freeze active — "
            "no dispatch. Run 'unfreeze' once the freeze conditions are cleared.",
            fg="red",
            bold=True,
        )
        return

    # C7 FIX: Global run lock — prevents GHA cron + local Scheduled Task running simultaneously.
    # Both write to the same controller_state.json; concurrent ticks corrupt it.
    # Lock file: C:\AI_Runner\locks\tick.lock (PID + start timestamp).
    # If lock is stale (>10 min old), clear it and acquire fresh.
    _lock_dir = runner_paths.locks_dir()
    _lock_dir.mkdir(parents=True, exist_ok=True)
    _lock_file = _lock_dir / "tick.lock"
    _lock_stale_s = 600  # 10 min
    try:
        if _lock_file.exists():
            _ldata = json.loads(_lock_file.read_text())
            _lage = _time_c7.time() - _ldata.get("ts", 0)
            if _lage < _lock_stale_s:
                click.secho(
                    f"  [C7] Tick lock held by PID={_ldata.get('pid','?')} "
                    f"({_lage:.0f}s old) — exiting to prevent concurrent execution.",
                    fg="yellow",
                )
                return
            click.secho(f"  [C7] Stale lock cleared (age={_lage:.0f}s).", fg="yellow")
        _lock_file.write_text(
            json.dumps({"pid": _os_c7.getpid(), "ts": _time_c7.time(), "started": _now()}),
            encoding="utf-8",
        )
    except Exception as _lock_exc:
        click.secho(f"  [C7] Lock error ({_lock_exc}), proceeding without lock.", fg="yellow")

    state = _read_runner_state()
    status = state.get("status", "IDLE")
    cycle  = state.get("active_cycle")

    # ── Cycle integrity check BEFORE any transitions ──────────────────
    # If the cycle in controller_state is wrong (stale CI run, regression, etc.)
    # correct it NOW and ABORT this tick. The next tick will start with the
    # correct cycle and run the right state machine transitions.
    try:
        from automation.cycle_authority import reconcile as _ca_pre
        _pre_rpt = _ca_pre(verbose=False)
        if "CORRECTED" in str(_pre_rpt.get("action", "")):
            correct_cycle = _pre_rpt["consensus"]
            write_controller_state(status, cycle=correct_cycle)
            click.secho(
                f"[CYCLE GUARD] Cycle corrected {cycle} -> {correct_cycle} "
                f"(confidence={_pre_rpt.get('confidence','?')}). "
                f"Aborting tick — next tick will use corrected cycle.",
                fg="yellow", bold=True,
            )
            _release_tick_lock(_lock_file)  # cluster A: never leak the lock on early return
            click.echo("[TICK COMPLETE]")
            return  # ABORT — don't run any state transitions with wrong cycle
    except Exception:
        pass

    click.echo(f"[TICK] {_now()}  status={status}  cycle={cycle}")

    # Always write fresh heartbeat
    write_heartbeat(status, cycle=cycle)

    # ── State machine transitions ─────────────────────────────────────
    if status in ("IDLE", "POST_CYCLE_PASS", "INITIAL"):
        # OPS-030: stage2 readiness check runs automatically at cycle start.
        rc, out = _run_shell_command([sys.executable, "automation/ai_cycle_controller.py", "stage2-readiness-check"])
        if rc != 0:
            _record_nonblocking_error(f"stage2-readiness-check failed: {out.strip()[:500]}")
            try:
                from automation.daily_report_generator import generate_daily_stage_report
                generate_daily_stage_report()
            except Exception as exc:  # pragma: no cover - non-blocking
                _record_nonblocking_error(f"daily-stage-report update failed after readiness error: {exc}")
            write_controller_state("BLOCKED_STAGE2_READINESS", cycle=cycle)
            click.secho("  State: BLOCKED_STAGE2_READINESS — dispatch paused, report updated", fg="yellow")
            _release_tick_lock(_lock_file)  # cluster A: never leak the lock on early return
            click.echo("[TICK COMPLETE]")
            return
        # Ready for next cycle — compile policy to get current cycle.
        # If we just completed a cycle (POST_CYCLE_PASS), advance cycle via CycleAuthority
        # This logs the advance permanently in cycle_ledger.json
        if status == "POST_CYCLE_PASS" and cycle:
            from automation.cycle_authority import advance as _ca_advance, force_set as _ca_force_set
            try:
                next_cycle_target = _ca_advance(cycle, reason="post_cycle_pass")
                _update_hydration_cycle(next_cycle_target)
                click.secho(
                    f"  CYCLE ADVANCE: {cycle} -> {next_cycle_target} (logged in cycle_ledger.json)",
                    fg="green", bold=True,
                )
            except ValueError as _adv_err:
                click.secho(f"  [CYCLE] advance() raised: {_adv_err} — using cycle+1", fg="yellow")
                next_cycle_target = cycle + 1
                _ca_force_set(next_cycle_target, reason=f"advance_fallback: {_adv_err}", operator="tick")
                _update_hydration_cycle(next_cycle_target)
        else:
            next_cycle_target = None
        click.echo("  → Running compile-policy...")
        snap = compile_policy(REPO_ROOT)
        next_cycle = snap.get("cycle_current", 75)
        write_controller_state("COMPILED", cycle=next_cycle)
        notify_info(f"Tick: policy compiled, cycle={next_cycle}")
        click.secho(f"  State: COMPILED (cycle {next_cycle})", fg="cyan")

    elif status == "COMPILED":
        # Item 5.4 determinism: plan-cycle's prompt generator reads the working
        # tree, so the integration branch MUST contain current origin/develop FIRST
        # (else a resumed stale branch regenerates prompts with old code). On a sync
        # block/transient-retry, fall through (status already handled) to the lock
        # release — do NOT early-return (that would leak tick.lock).
        if (not cycle) or _sync_or_block(cycle, "generate prompts"):
            # Auto-run plan-cycle to generate prompts — no manual intervention needed
            click.echo(f"  → Auto-running plan-cycle for cycle {cycle}...")
            rc, out = _run_shell_command(
                [sys.executable, "automation/ai_cycle_controller.py", "plan-cycle",
                 "--live", "--cycle", str(cycle)]
            )
            if rc == 0:
                write_controller_state("PLANNED", cycle=cycle)
                click.secho(f"  State: PLANNED (cycle {cycle}) — prompts generated", fg="cyan")
            else:
                click.secho(f"  [WARN] plan-cycle failed:\n{out.strip()[-400:]}", fg="yellow")
                write_controller_state("PLANNING", cycle=cycle)
                click.secho("  State: PLANNING (plan-cycle failed — will retry next tick)", fg="yellow")

    elif status == "PLANNED":
        # Validate prompts
        if cycle:
            from automation.prompt_validator import validate_all
            prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
            agents = ["A", "B", "E", "C", "F", "D"]
            results = validate_all(prompts_dir, cycle, agents)
            all_valid = all(r.passed for r in results.values())
            if all_valid:
                write_controller_state("READY_TO_DISPATCH", cycle=cycle)
                click.secho("  State: READY_TO_DISPATCH (all prompts valid)", fg="green")
            else:
                failed_agents = [a for a, r in results.items() if not r.passed]
                write_controller_state("PROMPT_VALIDATION_FAILED", cycle=cycle)
                notify_blocked(f"Prompts invalid for agents: {failed_agents}",
                               incident_code="PROMPT_VALIDATION_FAILED", cycle=cycle)
                click.secho(f"  State: PROMPT_VALIDATION_FAILED agents={failed_agents}", fg="red")
        else:
            click.secho("  No active cycle — run plan-cycle first", fg="yellow")

    elif status == "READY_TO_DISPATCH":
        # Item 5.4 determinism: re-assert the integration branch is current with
        # origin/develop immediately before dispatch (idempotent; also catches a
        # develop advance since COMPILED). On a sync block/transient-retry, do NOT
        # dispatch and fall through to the lock release (no early-return → no lock leak).
        _act = _sync_or_block(cycle, "dispatch agents") if cycle else "already_current"
        if _act is None:
            click.echo("  [SYNC] dispatch deferred this tick (branch sync blocked/retrying)")
        elif _act not in ("already_current", "skipped_pytest"):
            # Codex P2: the branch advanced onto newer develop AFTER prompts were
            # generated/validated — they are now stale for the new code state.
            # Regenerate before dispatching rather than run agents on stale instructions.
            write_controller_state("COMPILED", cycle=cycle)
            click.secho(
                f"  [SYNC] branch advanced ({_act}) after prompt-gen — returning to "
                "COMPILED to regenerate prompts on fresh develop.", fg="yellow",
            )
        else:
            # Check model gate
            from automation.model_gate import check as model_gate_check
            gate = model_gate_check(repo_root=REPO_ROOT, cycle=cycle, agent="PRE_DISPATCH")
            if not gate.passed:
                write_controller_state("MODEL_BLOCKED", cycle=cycle)
                notify_blocked("Model gate failed before dispatch", incident_code="MODEL_BLOCKED", cycle=cycle)
                click.secho(f"  State: MODEL_BLOCKED — {gate.summary()}", fg="red")
            else:
                # Check ANTHROPIC_API_KEY absent
                from automation.claude_sub_gate import check_api_key_absent
                api = check_api_key_absent()
                if not api["passed"]:
                    write_controller_state("CLAUDE_API_KEY_BLOCKED", cycle=cycle)
                    notify_blocked("ANTHROPIC_API_KEY detected", incident_code="BLOCKED_CLAUDE_API_KEY_PRESENT")
                    click.secho("  State: CLAUDE_API_KEY_BLOCKED", fg="red")
                else:
                    write_controller_state("AWAITING_DISPATCH", cycle=cycle)
                    click.secho("  All gates pass — dispatching agents now...", fg="green")
                    notify_info(f"Tick: dispatching cycle {cycle}")
                    # ── DISPATCH: call run-cycle directly ────────────────
                    write_controller_state("DISPATCHING", cycle=cycle)
                    rc, out = _run_shell_command(
                        [sys.executable, "automation/ai_cycle_controller.py",
                         "run-cycle", "--cycle", str(cycle)]
                    )
                    if rc == 0:
                        click.secho(f"  Cycle {cycle} dispatched and complete.", fg="green", bold=True)
                    else:
                        click.secho(f"  [WARN] run-cycle exited {rc}: {out.strip()[-300:]}", fg="yellow")
                        # Codex P1 #118: run-cycle may have deliberately set a
                        # recoverable state (PR_CREATE_FAILED / CYCLE_NO_WORK) before
                        # exiting non-zero. Do NOT clobber those with PLANNED — that
                        # would bypass their dedicated tick-recovery branches and
                        # redispatch the whole cycle. Only reset for generic failures.
                        _post_status = (_read_runner_state().get("status") or "")
                        if _post_status in (
                            "PR_CREATE_FAILED", "CYCLE_NO_WORK",
                            # ITEM 3.2: merge-path states are recoverable by their own
                            # tick branches — never clobber them into a full re-dispatch.
                            "AWAITING_CI_GREEN", "MERGING", "MERGED", "MERGE_BLOCKED",
                        ):
                            click.secho(
                                f"  Preserving {_post_status} for its recovery branch.",
                                fg="yellow",
                            )
                        else:
                            write_controller_state("PLANNED", cycle=cycle)  # reset for retry

    elif status == "AGENT_COMPLETE":
        import automation.autopilot_logger as L
        L.section(f"AGENT_COMPLETE — Cycle {cycle} — Running post-cycle review")
        write_controller_state("POST_CYCLE_PENDING", cycle=cycle)
        from automation.post_cycle_review import run_review, ReviewMode
        try:
            with L.Spinner("Post-cycle review (Jira sync + invariants; CI gated at merge)"):
                # ITEM 4.2: skip the ~13-min local suite ONLY when a PR exists —
                # then AWAITING_CI_GREEN gates the PR CI downstream. With NO PR
                # (Codex P2: no downstream CI to compensate) run the local suite
                # so local validation still gates the advance. pr_number satisfies
                # the pr_expected invariant when a PR is present.
                _ac_pr = (state or {}).get("active_pr")
                result = run_review(
                    cycle=cycle, mode=ReviewMode.POST_AGENT,
                    pr_number=_ac_pr,
                    skip_local_validation=bool(_ac_pr))
            grade = result.result.value if hasattr(result, "result") else "UNKNOWN"
            # Show every check so operator sees exactly what passed/failed
            L.newline()
            facts = result.facts if hasattr(result, "facts") else None
            from automation.live_events import emit as _ev2
            if facts:
                L.section("Post-cycle check results")
                L.post_cycle_check("Lint (ruff)", facts.local_ruff)
                L.post_cycle_check("Type check (mypy)", facts.local_mypy)
                L.post_cycle_check("Tests (pytest)", facts.local_pytest,
                                   f"{facts.local_coverage_pct:.0f}% coverage" if facts.local_coverage_pct else "")
                L.post_cycle_check("CI on develop", facts.ci_passed)
                L.post_cycle_check("Codecov project gate", facts.codecov_project != "FAIL",
                                   facts.codecov_project)
                L.post_cycle_check("Jira cycle control Done", facts.cycle_control_done)
                gh_score = getattr(facts, "github_health_score", None)
                if gh_score is not None:
                    L.post_cycle_check("GitHub health", gh_score >= 60, f"score={gh_score}/100")
                blockers = getattr(facts, "github_blockers", [])
                for b in blockers[:3]:
                    L.warn(f"GitHub blocker: {b}")
                cov = f"{facts.local_coverage_pct:.0f}%" if facts.local_coverage_pct else "?"
                _ev2("REVIEW", f"lint={'OK' if facts.local_ruff else 'FAIL'} tests={'OK' if facts.local_pytest else 'FAIL'} cov={cov} CI={'OK' if facts.ci_passed else 'FAIL'} jira={'OK' if facts.cycle_control_done else 'PEND'}", cycle=cycle)
            L.post_cycle_grade(grade, cycle)
            # ITEM 4.1: advance on `not result.blocks_dispatch` — the SINGLE,
            # consistent predicate shared with the POST_CYCLE_PENDING branch (4.1-T2).
            # POST_AGENT review ALWAYS returns DRAFT_UNMERGED_PREVIEW (never "PASS"),
            # so the old `grade == "PASS"` gate dead-ended EVERY clean cycle at
            # POST_CYCLE_FAIL. blocks_dispatch is the trustworthy signal here: for
            # POST_AGENT it is fact-based (ruff/mypy/pytest/CI/coverage/health/ICV),
            # and POST_AGENT never yields ADVISORY_ONLY, so the C4/H7
            # anti-fabrication concern (ADVISORY_ONLY defaulting) does not apply to
            # this path. A genuinely broken cycle still blocks (blocks_dispatch=True).
            if not result.blocks_dispatch:
                # If a PR is open the cycle must NOT advance yet — _finalize routes
                # to AWAITING_CI_GREEN (merge path) vs POST_CYCLE_PASS (no PR).
                _new = _finalize_post_cycle_pass(cycle)
                if _new == "AWAITING_CI_GREEN":
                    L.ok(f"Cycle {cycle} local review clean ({grade}) — PR open; "
                         "waiting for CI to go green before merge")
                else:
                    L.ok(f"Cycle {cycle} COMPLETE ({grade}) — next tick plans Cycle {cycle + 1}")
                # OBS-7: emit end-of-cycle summary
                L.cycle_summary(cycle=cycle, agent_outcomes={}, gate_result=grade)
                L.clear_activity()
            else:
                write_controller_state("POST_CYCLE_FAIL", cycle=cycle)
                L.error(
                    f"POST_CYCLE_FAIL grade={grade} blocks_dispatch={result.blocks_dispatch} "
                    f"— review issues before advancing to Cycle {cycle + 1}"
                )
                L.cycle_summary(cycle=cycle, agent_outcomes={}, gate_result=f"FAIL:{grade}")
        except Exception as exc:
            L.error(f"post-cycle-review raised: {exc}")
            import traceback
            L.info(traceback.format_exc()[-400:])
            write_controller_state("POST_CYCLE_PENDING", cycle=cycle)

    elif status in ("DISPATCHING", "AGENT_DISPATCH", "CURSOR_RUNNING"):
        import automation.autopilot_logger as L
        import json as _json

        # Auto-fix branch mismatch
        expected_branch = f"cycle/{cycle:03d}/integration"
        from automation.branch_guard import current_branch as _current_branch
        actual_branch = _current_branch()
        if actual_branch and actual_branch != expected_branch:
            click.secho(f"  [BRANCH] on '{actual_branch}' — switching to '{expected_branch}'...", fg="yellow")
            rc_sw, _ = _run_shell_command(["git", "checkout", expected_branch])
            if rc_sw != 0:
                _run_shell_command(["git", "fetch", "origin", expected_branch, "--quiet"])
                _run_shell_command(["git", "checkout", "-b", expected_branch, f"origin/{expected_branch}"])

        # ── Read agent progress file ──────────────────────────────────
        prog_path = runner_paths.state_dir() / "agent_progress.json"
        prog: dict = {}
        if prog_path.exists():
            try:
                prog = _json.loads(prog_path.read_text())
            except Exception:
                pass

        all_agents = ["A", "B", "E", "C", "F", "D"]
        current = prog.get("current_agent", "?")
        completed = prog.get("completed", [])
        failed = prog.get("failed", [])
        total_agents = prog.get("total_agents", 6)
        agent_elapsed = prog.get("agent_elapsed_s", 0)
        cycle_elapsed = prog.get("cycle_elapsed_s", 0)
        prog_cycle = prog.get("cycle", cycle)

        # Show Cursor process count
        cursor_count = "?"
        try:
            import subprocess as _sp
            cr = _sp.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-Process -Name Cursor -ErrorAction SilentlyContinue).Count"],
                capture_output=True, text=True, timeout=5,
            )
            cursor_count = (cr.stdout or "0").strip()
        except Exception:
            pass

        # ── Display ───────────────────────────────────────────────────
        if prog and prog_cycle == cycle and current != "DONE":
            # We have live progress data
            mins_cycle = cycle_elapsed // 60
            secs_cycle = cycle_elapsed % 60
            cycle_time = f"{mins_cycle}m{secs_cycle:02d}s" if mins_cycle else f"{secs_cycle}s"
            click.echo(f"\n  Cycle {cycle:03d} agent progress — elapsed {cycle_time}")
            click.echo(f"  {cursor_count} Cursor process(es) active")
            click.echo("")
            for i, ag in enumerate(all_agents, 1):
                if ag in completed:
                    icon = click.style("  DONE  ", fg="green")
                    label = click.style(f"Agent {ag}", fg="green")
                elif ag in failed:
                    icon = click.style("  FAIL  ", fg="red", bold=True)
                    label = click.style(f"Agent {ag}", fg="red", bold=True)
                elif ag == current:
                    mins_a = agent_elapsed // 60
                    secs_a = agent_elapsed % 60
                    t = f"{mins_a}m{secs_a:02d}s" if mins_a else f"{secs_a}s"
                    icon = click.style("  RUN   ", fg="yellow", bold=True)
                    label = click.style(f"Agent {ag}  (running {t})", fg="yellow", bold=True)
                else:
                    icon = click.style("  WAIT  ", fg="bright_black")
                    label = click.style(f"Agent {ag}", fg="bright_black")
                role = {"A": "Planning+Jira", "B": "Implementation", "E": "Review+Tests",
                        "C": "Integration", "F": "Docs+Coverage", "D": "PR+Merge"}.get(ag, "")
                click.echo(f"  [{i}/{total_agents}]{icon}{label}  {click.style(role, fg='bright_black')}")
        elif prog and current == "DONE":
            # run-cycle finished but state not yet AGENT_COMPLETE — write it now
            click.secho(f"  All {len(completed)}/{total_agents} agents complete — advancing to review...", fg="green")
            write_controller_state("AGENT_COMPLETE", cycle=cycle)
        else:
            # No progress file -- agents running with old code or dispatch just started
            if cursor_count and cursor_count not in ("0", "?"):
                click.secho(f"  Agents running ({cursor_count} Cursor processes active)", fg="cyan")
                click.secho("  Per-agent progress board available next cycle", fg="bright_black")
            else:
                click.secho("  Agents dispatched -- waiting for Cursor to start...", fg="cyan")

        # ── Show what's being built (from prompt) ─────────────────────
        click.echo("")
        prompt_a = REPO_ROOT / f"PM_Pack/automation/prompts/CYCLE_{cycle:03d}_AGENT_A_PROMPT.md"
        if prompt_a.exists():
            lines = prompt_a.read_text(encoding="utf-8", errors="replace").splitlines()
            # Find target stories line
            for ln in lines[:80]:
                if "SCRUM-" in ln and ("TO DO" in ln.upper() or "BUILD" in ln.upper() or "🔨" in ln):
                    click.secho(f"  Target: {ln.strip()[:80]}", fg="bright_black")
                    break

        # ── Show files changed (committed + uncommitted) ─────────────
        # Agents work in Cursor and may not commit until end of their run
        rc_diff, diff_out = _run_shell_command(["git", "diff", "--stat", "HEAD"])
        rc_diff3, diff_out3 = _run_shell_command(
            ["git", "diff", "origin/develop..HEAD", "--stat"]
        )
        combined = "\n".join(filter(None, [diff_out.strip(), diff_out3.strip()]))
        # Strip git warning lines (CRLF warnings etc) — only keep stat lines
        stat_lines = [
            ln for ln in combined.splitlines()
            if ln.strip()
            and not ln.startswith("warning:")
            and not ln.startswith("hint:")
            and not ln.startswith("error:")
        ]
        if stat_lines:
            file_lines = [ln for ln in stat_lines if "|" in ln][-8:]
            summary = [ln for ln in stat_lines if "changed" in ln]
            click.echo("")
            click.secho("  Code changes in progress:", fg="bright_black")
            for ln in file_lines:
                click.secho(f"    {ln.strip()}", fg="bright_black")
            if summary:
                click.secho(f"    {summary[-1].strip()}", fg="cyan")

        # ── Heartbeat staleness check ─────────────────────────────────
        hb_path = runner_paths.state_dir() / "heartbeat.json"
        if hb_path.exists():
            try:
                hb = _json.loads(hb_path.read_text())
                from datetime import datetime as _dt
                last = _dt.fromisoformat(hb.get("last_seen", _now()).replace("Z", "+00:00"))
                age_min = (_dt.now(last.tzinfo) - last).total_seconds() / 60
                if age_min > 45:
                    notify_blocked(f"Heartbeat stale {age_min:.0f}m — agents may be stuck",
                                   incident_code="AGENT_STUCK", cycle=cycle)
                    L.warn(f"Heartbeat stale {age_min:.0f}m — agents may be stuck!")
            except Exception:
                pass

    elif status in ("POST_CYCLE_PENDING", "POST_CYCLE_REVIEW"):
        # Either we transitioned here automatically (retry after crash) or manually.
        # Always attempt the review rather than waiting indefinitely.
        click.secho(f"  [TICK] {status} — attempting post-cycle-review for cycle {cycle}...",
                    fg="cyan")
        from automation.post_cycle_review import run_review, ReviewMode
        try:
            # ITEM 4.2: same merge-aware review as AGENT_COMPLETE — skip the local
            # suite ONLY when a PR exists (CI gates downstream); with no PR, run
            # the local suite so validation still gates (Codex P2).
            _pc_pr = (state or {}).get("active_pr")
            result = run_review(
                cycle=cycle, mode=ReviewMode.POST_AGENT,
                pr_number=_pc_pr,
                skip_local_validation=bool(_pc_pr))
            grade = result.result.value if hasattr(result, "result") else "UNKNOWN"
            click.echo(f"  Post-cycle-review grade: {grade}")
            if not result.blocks_dispatch:
                # ITEM 3.2: same merge-aware finalize as the AGENT_COMPLETE branch
                # — an open PR routes to AWAITING_CI_GREEN, never straight to
                # POST_CYCLE_PASS (which would advance the cycle past an unmerged
                # PR and bypass the merge gate).
                _new = _finalize_post_cycle_pass(cycle)
                if _new == "AWAITING_CI_GREEN":
                    click.secho(f"  PR open — cycle {cycle} waiting for CI green before merge.",
                                fg="cyan", bold=True)
                else:
                    click.secho(f"  POST_CYCLE_PASS — cycle {cycle} complete. Next tick plans cycle {cycle + 1}.",
                                fg="green", bold=True)
            else:
                write_controller_state("POST_CYCLE_FAIL", cycle=cycle)
                click.secho(f"  POST_CYCLE_FAIL grade={grade}", fg="red", bold=True)
        except Exception as exc:
            click.secho(f"  [ERROR] post-cycle-review raised: {exc} — staying in {status}", fg="red")

    elif status in (
        "MODEL_BLOCKED", "CLAUDE_API_KEY_BLOCKED",
        "PROMPT_VALIDATION_FAILED", "PROMPT_REGEN_EXHAUSTED",
    ):
        # Re-check the gate before staying blocked — self-heal if it now passes
        if status == "MODEL_BLOCKED":
            from automation.cursor_adapter import check_model_gate_freshness
            gate = check_model_gate_freshness()
            if gate.get("passed"):
                click.secho("  MODEL gate now PASSES — auto-clearing MODEL_BLOCKED", fg="green")
                write_controller_state("PLANNED", cycle=cycle)
                click.secho("  Advanced to PLANNED — will dispatch on next tick", fg="green")
            else:
                reason = gate.get("reason", "model gate failed")
                click.secho(f"  BLOCKED ({status}): {reason} — resolve and run recover to reset", fg="red")
        elif status == "PROMPT_VALIDATION_FAILED":
            # ── Item 1.2: bounded regenerate edge (stop the wedge) ────────
            # (a) Re-validate the current prompts. If ALL pass (e.g. an external
            #     fix landed) → PLANNED and reset the attempt counter.
            # (b) Else, if under the per-cycle attempt budget, FORCE regeneration
            #     of the failing agents (the rejected prompt bytes are moved aside
            #     so resume-from-partial can't reuse them), re-validate, and either
            #     heal to PLANNED or stay PROMPT_VALIDATION_FAILED (next tick
            #     retries — bounded).
            # (c) Else (budget exhausted) → fail closed to PROMPT_REGEN_EXHAUSTED
            #     with an alert. No infinite auto-retry.
            import automation.autopilot_logger as _L12
            from automation.prompt_validator import validate_all
            _agents = list(_STD_AGENT_SET)  # standard agent set
            prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
            try:
                vr = validate_all(prompts_dir, cycle=cycle, agents=_agents)
                if vr and all(getattr(r, "passed", False) for r in vr.values()):
                    click.secho("  Prompts now PASS — auto-clearing PROMPT_VALIDATION_FAILED", fg="green")
                    _reset_prompt_regen_state(cycle)
                    write_controller_state("PLANNED", cycle=cycle)
                    _L12.ok(f"Cycle {cycle} prompts auto-healed → PLANNED (external fix)")
                else:
                    failing = [a for a, r in (vr or {}).items()
                               if not getattr(r, "passed", False)]
                    regen_state = _read_prompt_regen_state(cycle)
                    attempts = regen_state["attempts"]
                    max_attempts = _prompt_regen_max_attempts()
                    if attempts < max_attempts:
                        next_attempt = attempts + 1
                        click.secho(
                            f"  REGENERATE attempt {next_attempt}/{max_attempts} "
                            f"for agents {failing}",
                            fg="yellow", bold=True,
                        )
                        _L12.info(
                            f"PROMPT regenerate attempt {next_attempt}/{max_attempts} "
                            f"for agents {failing} (cycle {cycle})"
                        )
                        notify_info(
                            f"Prompt regenerate attempt {next_attempt}/{max_attempts} "
                            f"for agents {failing}",
                            cycle=cycle,
                        )
                        _backoff = _prompt_regen_backoff_s()
                        if _backoff > 0:
                            time.sleep(_backoff)
                        # Persist the incremented counter BEFORE the (mockable)
                        # regen call so a crash mid-regen still consumes budget
                        # (fail-closed — never an unbounded retry).
                        _write_prompt_regen_state(cycle, next_attempt)
                        _force_regenerate_failing_prompts(cycle, failing)
                        # Re-validate after regeneration.
                        vr2 = validate_all(prompts_dir, cycle=cycle, agents=_agents)
                        if vr2 and all(getattr(r, "passed", False) for r in vr2.values()):
                            click.secho(
                                "  Prompts now PASS after regenerate — advancing to PLANNED",
                                fg="green",
                            )
                            _reset_prompt_regen_state(cycle)
                            write_controller_state("PLANNED", cycle=cycle)
                        else:
                            still = [a for a, r in (vr2 or {}).items()
                                     if not getattr(r, "passed", False)]
                            click.secho(
                                f"  Still failing after regenerate (agents {still}) — "
                                f"staying PROMPT_VALIDATION_FAILED (attempt "
                                f"{next_attempt}/{max_attempts}, next tick retries)",
                                fg="yellow",
                            )
                            write_controller_state("PROMPT_VALIDATION_FAILED", cycle=cycle)
                    else:
                        # Budget exhausted → fail closed, alert, no further retry.
                        click.secho(
                            f"  PROMPT_REGEN_EXHAUSTED — {attempts}/{max_attempts} "
                            f"regenerate attempts used for cycle {cycle}, agents "
                            f"still failing {failing}. Failing closed.",
                            fg="red", bold=True,
                        )
                        write_controller_state("PROMPT_REGEN_EXHAUSTED", cycle=cycle)
                        notify_blocked(
                            f"Prompt regeneration exhausted after {max_attempts} "
                            f"attempts (agents {failing})",
                            incident_code="PROMPT_REGEN_EXHAUSTED", cycle=cycle,
                        )
                        _L12.error(
                            f"Cycle {cycle} PROMPT_REGEN_EXHAUSTED after {max_attempts} "
                            "attempts — run 'recover --regen' or fix the generator."
                        )
            except Exception as _ve:
                click.secho(
                    f"  BLOCKED ({status}) — regenerate path raised: {_ve} — "
                    "resolve and run recover to reset",
                    fg="red",
                )
        elif status == "PROMPT_REGEN_EXHAUSTED":
            # Fail-closed terminal-ish state: surfaced to the operator. Still
            # auto-heal if a manual/external fix now makes validation pass.
            import automation.autopilot_logger as _L12x
            from automation.prompt_validator import validate_all
            _agents = list(_STD_AGENT_SET)
            prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
            try:
                vr = validate_all(prompts_dir, cycle=cycle, agents=_agents)
                if vr and all(getattr(r, "passed", False) for r in vr.values()):
                    click.secho(
                        "  Prompts now PASS — auto-clearing PROMPT_REGEN_EXHAUSTED",
                        fg="green",
                    )
                    _reset_prompt_regen_state(cycle)
                    write_controller_state("PLANNED", cycle=cycle)
                    _L12x.ok(f"Cycle {cycle} recovered from PROMPT_REGEN_EXHAUSTED (external fix)")
                else:
                    click.secho(
                        f"  BLOCKED ({status}) — regenerate budget exhausted. "
                        "Run 'recover --regen' (resets attempts) or fix the prompt "
                        "generator, then the next tick re-attempts.",
                        fg="red",
                    )
            except Exception as _ve:
                click.secho(f"  BLOCKED ({status}) — resolve and run recover to reset", fg="red")
        else:
            click.secho(f"  BLOCKED ({status}) — resolve and run recover to reset", fg="red")

    elif status == "BLOCKED_STAGE2_READINESS":
        # Retry readiness check — if prompts now exist (generated in a previous tick), should pass
        click.echo("  Retrying stage2-readiness-check...")
        rc, out = _run_shell_command([sys.executable, "automation/ai_cycle_controller.py", "stage2-readiness-check"])
        if rc == 0:
            write_controller_state("COMPILED", cycle=cycle)
            click.secho(f"  Stage2 now passes — advancing to COMPILED (cycle {cycle})", fg="green")
        else:
            click.secho(f"  Still blocked: {out.strip()[-200:]}", fg="yellow")

    elif status == "PLANNING":
        # plan-cycle failed or is in progress — retry
        click.echo(f"  Retrying plan-cycle for cycle {cycle}...")
        rc, out = _run_shell_command(
            [sys.executable, "automation/ai_cycle_controller.py", "plan-cycle",
             "--live", "--cycle", str(cycle)]
        )
        if rc == 0:
            write_controller_state("PLANNED", cycle=cycle)
            click.secho(f"  State: PLANNED (cycle {cycle})", fg="cyan")
        else:
            click.secho(f"  plan-cycle still failing: {out.strip()[-200:]}", fg="yellow")

    elif status == "POST_CYCLE_FAIL":
        # BLOCKER 3: a genuinely-broken cycle (post-cycle review found blocking gate
        # failures: ruff/mypy/pytest/CI/coverage/health). The prior M-TICK-1 fix kept
        # this from the 'Unknown status -> IDLE' silent reset, but it then DEAD-ENDED
        # waiting for an operator — defeating unattended 24/7 autonomy. Now: BOUNDED
        # re-dispatch so the agents get another attempt to produce passing work (a
        # transient gate flake or a repair can self-heal), then escalate to the
        # operator after the cap and halt auto-retry. Mirrors the MERGE_BLOCKED /
        # DEVELOP_SYNC_BLOCKED recovery pattern; falls through to the lock-release
        # epilogue (never returns).
        import automation.autopilot_logger as L
        _pcf = _tick_counter(f"post_cycle_fail_recover_{cycle}", increment=True)
        _pcf_cap = int(os.environ.get("AUTOPILOT_POST_CYCLE_FAIL_MAX", "3"))
        if _pcf <= _pcf_cap:
            L.warn(
                f"POST_CYCLE_FAIL recovery {_pcf}/{_pcf_cap} (cycle {cycle}) — review gate "
                "blocked dispatch; re-dispatching for another attempt at passing work"
            )
            write_controller_state("READY_TO_DISPATCH", cycle=cycle)
            click.secho(
                f"  POST_CYCLE_FAIL → READY_TO_DISPATCH (recovery {_pcf}/{_pcf_cap})",
                fg="yellow",
            )
        else:
            L.error(
                f"POST_CYCLE_FAIL persistent ({_pcf} > {_pcf_cap}) on cycle {cycle} — "
                "the cycle's gates still fail after bounded re-dispatch; operator action "
                "required (auto-retry halted)."
            )
            notify_blocked(
                f"Cycle {cycle} post-cycle review persistently failing",
                body=(
                    f"{_pcf - 1} recovery re-dispatches exhausted; gates "
                    "(ruff/mypy/pytest/CI/coverage) still fail. Check post_cycle_reviews/ "
                    "and either fix the issues or force-advance via "
                    "'force-state --status IDLE'."
                ),
                incident_code="POST_CYCLE_FAIL", cycle=cycle,
            )
            click.secho(
                f"  POST_CYCLE_FAIL persistent (cycle {cycle}) — operator action required",
                fg="red", bold=True,
            )
        # Stay-or-redispatch decided above; fall through to the epilogue.

    elif status == "CYCLE_NO_WORK":
        # ITEM 2.1: the previous run-cycle produced ZERO committed work. The
        # cycle was NOT advanced (fail-closed). Surface it and route back to
        # READY_TO_DISPATCH so a subsequent tick re-runs the model gate and can
        # re-dispatch a real run. This is recoverable — a later real run proceeds.
        import automation.autopilot_logger as L
        L.warn(
            f"CYCLE_NO_WORK (cycle {cycle}) — last run committed nothing. "
            "Re-dispatching: routing to READY_TO_DISPATCH for a fresh run."
        )
        notify_blocked(
            f"Cycle {cycle:03d} no-work — re-dispatching",
            body="Previous run-cycle committed nothing; routing to READY_TO_DISPATCH.",
            incident_code="CYCLE_NO_WORK",
            cycle=cycle,
        )
        write_controller_state("READY_TO_DISPATCH", cycle=cycle)

    elif status == "AWAITING_CI_GREEN":
        # ITEM 3.2: a verified PR is open (active_pr) and local post-cycle review
        # already PASSed. Poll the PR's required CI ONCE per tick (non-blocking —
        # never wait_for_ci, which would hold the tick up to 30 min). All required
        # checks green -> merge via the merge gate. Fail-closed to MERGE_BLOCKED on
        # CI failure / missing PR / bounded wait timeout (all recoverable).
        import automation.autopilot_logger as L
        _active_pr = (state or {}).get("active_pr")
        if not _active_pr:
            L.error("AWAITING_CI_GREEN but no active_pr — failing closed (MERGE_BLOCKED)")
            write_controller_state("MERGE_BLOCKED", cycle=cycle)
            notify_blocked(
                f"Cycle {cycle} merge blocked: no active_pr in AWAITING_CI_GREEN",
                incident_code="MERGE_BLOCKED", cycle=cycle,
            )
        else:
            from automation import required_checks as _rc
            from automation.ci_status_reader import read_pr_ci_status
            _pr_int = int(_active_pr)
            # CODEX_DISPOSITION (BLOCKER 2): before evaluating CI/merge, autonomously
            # address unresolved Codex review threads (fix-don't-dismiss). A fresh P1/P2
            # finding would otherwise fail the required codex-review-gate → MERGE_BLOCKED
            # → operator. One repair round per tick; the push re-triggers CI.
            try:
                _codex = _maybe_dispatch_codex_repair(cycle, _pr_int)
            except Exception as _exc:  # pragma: no cover - defensive; never crash the tick
                L.warn(f"codex disposition raised ({_exc}) — retrying next tick")
                _codex = "ERROR"
            # NOTE: every branch below must FALL THROUGH to the tick epilogue (which
            # releases the tick lock) — never `return` from here, or the lock leaks and
            # all future ticks deadlock. Non-CLEAN dispositions skip the merge logic.
            if _codex == "REPAIRING":
                click.secho(
                    f"  PR #{_active_pr}: dispatched Codex-finding repair + pushed — "
                    "staying AWAITING_CI_GREEN (CI re-runs on the fix)",
                    fg="yellow",
                )
            elif _codex == "ESCALATE":
                write_controller_state("MERGE_BLOCKED", cycle=cycle)
                L.error(f"Codex threads unresolved after repair budget on PR #{_active_pr}")
                notify_blocked(
                    f"Cycle {cycle} Codex review threads unresolved after auto-repair budget "
                    f"(PR #{_active_pr})",
                    body="Auto-repair could not clear the reviewer's findings; operator review needed.",
                    incident_code="MERGE_BLOCKED", cycle=cycle,
                )
            elif _codex == "AWAIT_REVIEW":
                click.secho(
                    f"  PR #{_active_pr}: Codex has not reviewed yet — waiting "
                    "(bounded) before merge so we never ship unreviewed code",
                    fg="yellow",
                )
            elif _codex == "ERROR":
                click.secho(
                    f"  PR #{_active_pr}: Codex thread read/dispatch transient error — "
                    "retrying next tick",
                    fg="yellow",
                )
            else:
                # _codex == CLEAN — no actionable Codex threads; evaluate CI + merge.
                cs = read_pr_ci_status(_pr_int)
                disp = cs.disposition(_rc.get_required_contexts()) if cs.gh_ok else "PENDING"
                click.secho(f"  PR #{_active_pr} required-CI disposition: {disp}", fg="cyan")
                if disp == "GREEN":
                    # Required CI is green — merge via the gate (squash, no --admin).
                    # Persist MERGING first so a crash mid-merge is recoverable by the
                    # MERGING branch (idempotent re-invocation), then attempt the merge.
                    write_controller_state("MERGING", cycle=cycle)
                    _attempt_merge(cycle, _pr_int)
                elif disp == "FAILED":
                    write_controller_state("MERGE_BLOCKED", cycle=cycle)
                    L.error(f"Required CI FAILED on PR #{_active_pr} — MERGE_BLOCKED")
                    notify_blocked(
                        f"Cycle {cycle} CI failed on PR #{_active_pr}",
                        body="A required check concluded non-success; a new push is needed.",
                        incident_code="MERGE_BLOCKED", cycle=cycle,
                    )
                else:  # PENDING (incl. gh read error) — bounded wait across ticks
                    _waited = _tick_counter(f"ci_wait_pr{_pr_int}", increment=True)
                    _cap = int(os.environ.get("AUTOPILOT_CI_WAIT_MAX_TICKS", "60"))
                    if _waited >= _cap:
                        write_controller_state("MERGE_BLOCKED", cycle=cycle)
                        L.error(f"CI still pending after {_waited} ticks (cap {_cap}) on "
                                f"PR #{_active_pr} — MERGE_BLOCKED")
                        notify_blocked(
                            f"Cycle {cycle} CI-wait timeout on PR #{_active_pr}",
                            incident_code="MERGE_BLOCKED", cycle=cycle,
                        )
                    else:
                        click.secho(
                            f"  CI pending (tick {_waited}/{_cap}) — staying AWAITING_CI_GREEN",
                            fg="yellow",
                        )

    elif status == "MERGING":
        # ITEM 3.2: a previous tick wrote MERGING then crashed/was killed before
        # recording the outcome (MERGED/MERGE_BLOCKED). Recover crash-safely:
        # re-attempt the merge (idempotent — an already-merged PR resolves to
        # MERGED) or fail-closed to MERGE_BLOCKED if the PR is gone.
        import automation.autopilot_logger as L
        _active_pr = (state or {}).get("active_pr")
        if not _active_pr:
            L.error("MERGING with no active_pr — failing closed (MERGE_BLOCKED)")
            write_controller_state("MERGE_BLOCKED", cycle=cycle)
            notify_blocked(
                f"Cycle {cycle} stuck in MERGING with no active_pr",
                incident_code="MERGE_BLOCKED", cycle=cycle,
            )
        else:
            L.warn(f"Recovering from MERGING — re-attempting merge of PR #{_active_pr} (idempotent)")
            _attempt_merge(cycle, int(_active_pr))

    elif status == "MERGED":
        # ITEM 3.2: the PR merged. This is the ONLY state allowed to advance the
        # cycle. Clear active_pr and route into the existing POST_CYCLE_PASS
        # advance machinery (handled by the IDLE/POST_CYCLE_PASS branch next tick).
        import automation.autopilot_logger as L
        _active_pr = (state or {}).get("active_pr")
        if _active_pr:
            _tick_counter(f"ci_wait_pr{int(_active_pr)}", reset=True)
            _tick_counter(f"merge_retry_pr{int(_active_pr)}", reset=True)
        # Audit [B]: the PR merged — converge the Jira board so cycle N+1 plans NEW work
        # instead of re-planning this cycle's stories. Build the per-story AC-verification
        # feed from the cycle's agent-report evidence and pass it to on_cycle_merged, which
        # is AC-GATED + empty-AC-safe (#146): it marks Done ONLY stories whose AC are all
        # verified in the evidence; ambiguous ones stay In Review and are re-checked next
        # cycle (conservative — never false-Done). BEST-EFFORT: a Jira/verify failure must
        # never block the post-merge advance (we're past the irreversible merge); the next
        # cycle's call re-checks still-open stories (self-healing).
        try:
            from automation.jira_sync import (
                build_ac_verification_for_cycle as _bacv,
                on_cycle_merged as _ocm,
            )
            _merge_sha = ""
            if _active_pr:
                try:
                    from automation.merge_gate import _read_receipt as _rr
                    _merge_sha = (_rr(int(_active_pr)) or {}).get("merge_sha", "") or ""
                except Exception:
                    pass
            # Codex P1: derive the cycle's ACTUAL Jira scope from the board — the stories
            # the runner moved to In Progress (on_cycle_planned) / In Review (on_pr_opened)
            # — NOT a hard-coded wave set. Otherwise a non-Wave-11 cycle (e.g. SCRUM-1088)
            # would skip the very stories it just merged. on_cycle_merged AC-gates each, so
            # passing the active set is safe (only AC-verified stories close).
            from automation import jira_client as _jc
            _active_status = {"In Progress", "In Review"}
            try:
                _board = (_jc.board_inventory_all().get("issues", [])) or []
            except Exception:
                _board = []
            _keys = [i.get("key") for i in _board
                     if i.get("status") in _active_status and i.get("key")]
            if _keys and cycle:
                # Evidence = the cycle's agent-report files (what each agent reported building).
                _ev_parts = []
                for _rep in sorted((REPO_ROOT / "docs" / "cycle_reports").glob(
                        f"CYCLE_{cycle:03d}_AGENT_*.md")):
                    try:
                        _ev_parts.append(_rep.read_text(encoding="utf-8", errors="replace"))
                    except Exception:
                        pass
                _evidence = "\n\n".join(_ev_parts)
                _ac = _bacv(_keys, _evidence)
                _res = _ocm(cycle, _merge_sha, _keys, ac_verification_results=_ac)
                _doneN = sum(1 for r in _res if r.get("status") == "ok")
                L.ok(f"Jira sync (cycle {cycle}): {_doneN}/{len(_keys)} stories -> Done "
                     "(AC-verified against agent evidence); rest held for re-check")
        except Exception as _jx:
            L.warn(f"Jira Done-sync after merge failed (non-blocking; retried next cycle): {_jx}")
        write_controller_state("POST_CYCLE_PASS", cycle=cycle, clear_pr=True)
        L.ok(f"Cycle {cycle} MERGED — advancing; next tick plans Cycle {cycle + 1}")

    elif status == "MERGE_BLOCKED":
        # ITEM 3.2: a merge attempt was blocked (CI failed / gate failed / wait
        # timeout / missing PR). RECOVERABLE: re-enter AWAITING_CI_GREEN after a
        # bounded number of retries so a transient red/pending self-heals; a
        # persistent failure stays blocked + notifies (NEVER advances with an
        # open PR). Idempotent: merge_gate treats an already-merged PR as success.
        import automation.autopilot_logger as L
        _active_pr = (state or {}).get("active_pr")
        if not _active_pr:
            L.error("MERGE_BLOCKED with no active_pr — operator action required")
            click.secho("  MERGE_BLOCKED (no active_pr) — staying blocked", fg="red")
        else:
            _pr_int = int(_active_pr)
            _retries = _tick_counter(f"merge_retry_pr{_pr_int}", increment=True)
            _cap = int(os.environ.get("AUTOPILOT_MERGE_RETRY_MAX", "5"))
            if _retries <= _cap:
                # Audit #2: if develop moved under the PR (BEHIND), the merge keeps
                # failing "not up to date" every retry. Update the branch so CI re-runs
                # on the merged result — otherwise the gate dead-ends here. Routine in a
                # multi-cycle run (every prior merge advances develop).
                if _update_pr_branch_if_behind(_pr_int):
                    L.warn(f"PR #{_active_pr} was BEHIND develop — updated branch; CI will re-run")
                L.warn(f"MERGE_BLOCKED retry {_retries}/{_cap} — re-checking CI on PR #{_active_pr}")
                # Reset the CI-wait counter so the re-entered AWAITING_CI_GREEN
                # gets a fresh bounded wait window (a transient pending/red can
                # then self-heal instead of immediately re-timing-out).
                _tick_counter(f"ci_wait_pr{_pr_int}", reset=True)
                write_controller_state("AWAITING_CI_GREEN", cycle=cycle)
            else:
                L.error(f"MERGE_BLOCKED persistent ({_retries} > {_cap}) on PR #{_active_pr} "
                        "— operator action required")
                notify_blocked(
                    f"Cycle {cycle} merge persistently blocked (PR #{_active_pr})",
                    body=f"{_retries} retries exhausted; operator must resolve CI/gate.",
                    incident_code="MERGE_BLOCKED", cycle=cycle,
                )

    elif status == "PR_CREATE_FAILED":
        # ITEM 3.1: the previous run-cycle committed real work but the PR-create
        # failed (no token / push fail / not verified). This is RECOVERABLE: the
        # work is committed, only the PR is missing. Re-attempt open_cycle_pr —
        # idempotent dup-guard means a half-created PR is found (existing) rather
        # than double-opened. On success advance to AGENT_COMPLETE so the next
        # tick runs the post-cycle review; on failure stay PR_CREATE_FAILED.
        import automation.autopilot_logger as L
        from automation import pr_builder
        # Audit #5: BOUND the retry. Previously this re-attempted open_cycle_pr EVERY
        # tick with no cap — an expired GH token returns the same 401 forever (no PR,
        # no CI, no escalation). Mirror the DEVELOP_SYNC_BLOCKED bounded-recovery: after
        # the cap, escalate once + halt auto-retry (operator must refresh the token).
        _pcf_n = _tick_counter(f"pr_create_retry_{cycle}", increment=True)
        _pcf_cap = int(os.environ.get("AUTOPILOT_PR_CREATE_RETRY_MAX", "5"))
        if _pcf_n > _pcf_cap:
            if _pcf_n == _pcf_cap + 1:
                notify_blocked(
                    f"Cycle {cycle:03d} PR-create persistently failing after {_pcf_cap} retries",
                    body="open_cycle_pr keeps failing (likely an expired/invalid GH token). "
                         "Operator must refresh GH_AUTOMATION_TOKEN; auto-retry halted.",
                    incident_code="PR_CREATE_FAILED_PERSISTENT", cycle=cycle,
                )
            click.secho(
                f"  PR_CREATE_FAILED persistent (cycle {cycle}) — operator action required; "
                "auto-retry halted.", fg="red", bold=True,
            )
        else:
            L.warn(
                f"PR_CREATE_FAILED recovery {_pcf_n}/{_pcf_cap} (cycle {cycle}) — "
                "re-attempting open_cycle_pr (idempotent dup-guard)."
            )
            _pr_retry = pr_builder.open_cycle_pr(cycle) if cycle else {"created": False, "error": "no cycle"}
            if _pr_retry.get("created") or _pr_retry.get("existing"):
                _pr_num = _pr_retry.get("pr_number")
                _word = "exists" if _pr_retry.get("existing") else "opened"
                L.ok(f"PR {_word} on retry: #{_pr_num} {_pr_retry.get('url','')}".rstrip())
                _tick_counter(f"pr_create_retry_{cycle}", reset=True)
                if _pr_num:
                    write_controller_state("AGENT_COMPLETE", cycle=cycle, pr=int(_pr_num))
                else:
                    write_controller_state("AGENT_COMPLETE", cycle=cycle)
                click.secho(f"  State: AGENT_COMPLETE — PR #{_pr_num} ({_word})", fg="green")
            else:
                _err = _pr_retry.get("error") or "unknown"
                L.error(f"PR-create retry still failing ({_err}) — staying PR_CREATE_FAILED")
                notify_blocked(
                    f"Cycle {cycle:03d} PR-create still failing",
                    body=f"open_cycle_pr retry failed: {_err}. Operator action may be required.",
                    incident_code="PR_CREATE_FAILED",
                    cycle=cycle,
                )
                click.secho(f"  PR_CREATE_FAILED (cycle {cycle}) — retry failed: {_err}", fg="red")

    elif status == "DEVELOP_SYNC_BLOCKED":
        # Item 5.4: bounded recovery from a failed develop-sync. Retry the sync; on
        # success, return to COMPILED so prompts regenerate on fresh develop. A
        # transient git/network error retries in place inside _sync_or_block; a
        # persistent conflict escalates to the operator after _SYNC_MAX_RECOVER
        # attempts (auto-retry halted — no infinite loop, notify exactly once).
        _rec = _tick_counter(f"develop_sync_recover_{cycle}", increment=True)
        if _rec > _SYNC_MAX_RECOVER:
            if _rec == _SYNC_MAX_RECOVER + 1:
                from automation.notification_router import notify_blocked as _nb_persist
                _nb_persist(
                    f"DEVELOP_SYNC_BLOCKED persists after {_SYNC_MAX_RECOVER} recovery "
                    f"attempts (cycle {cycle}) — operator must resolve the develop "
                    "divergence/conflict; auto-retry halted.",
                    incident_code="DEVELOP_SYNC_BLOCKED_PERSISTENT", cycle=cycle,
                )
                click.secho(
                    "  DEVELOP_SYNC_BLOCKED persistent — operator action required; "
                    "auto-retry halted.", fg="red", bold=True,
                )
            else:
                click.secho(
                    "  DEVELOP_SYNC_BLOCKED — awaiting operator (auto-retry halted).",
                    fg="yellow",
                )
        elif (not cycle) or _sync_or_block(cycle, "resync"):
            _tick_counter(f"develop_sync_recover_{cycle}", reset=True)
            write_controller_state("COMPILED", cycle=cycle)
            click.secho(
                "  Sync recovered — back to COMPILED (regenerate prompts on fresh develop).",
                fg="green",
            )

    elif status == "BLOCKED_EXPORT_SECRETS":
        # Audit #16 (security): run-agent writes this when a staged file would export
        # secrets. There was NO handler → it fell to the `else` → silent reset to IDLE
        # → re-dispatch WITH the secret still staged + no alert. HOLD here (do NOT
        # auto-clear): notify once, stay blocked until an operator removes the staged
        # secret and force-advances. Never auto-resets to IDLE.
        import automation.autopilot_logger as L
        if _tick_counter(f"export_secret_block_{cycle}", increment=True) == 1:
            notify_blocked(
                f"Cycle {cycle} BLOCKED_EXPORT_SECRETS — staged file would export a secret",
                body="A staged file tripped the export-sanitizer. Auto-dispatch is halted "
                     "to avoid committing the secret. Operator: scrub the staged file, then "
                     "force-advance. The runner will NOT auto-clear this state.",
                incident_code="BLOCKED_EXPORT_SECRETS", cycle=cycle,
            )
        L.error(f"BLOCKED_EXPORT_SECRETS (cycle {cycle}) — held for operator; not re-dispatching")
        click.secho(
            f"  BLOCKED_EXPORT_SECRETS (cycle {cycle}) — operator must scrub staged secret",
            fg="red", bold=True,
        )

    elif status == "AWAITING_DISPATCH":
        # Audit #21: a transient state written immediately before DISPATCHING; a crash
        # in that microsecond window would leave it with no handler → `else` → IDLE
        # re-plan. Treat it as DISPATCHING-equivalent: route to READY_TO_DISPATCH so the
        # next tick re-runs the model gate and dispatches cleanly (recoverable, bounded
        # by the normal dispatch path).
        import automation.autopilot_logger as L
        L.warn(f"AWAITING_DISPATCH (cycle {cycle}) — recovering to READY_TO_DISPATCH")
        write_controller_state("READY_TO_DISPATCH", cycle=cycle)

    else:
        click.echo(f"  Unknown status: {status} — treating as IDLE")
        write_controller_state("IDLE")

    # ── Post-transition cycle reconciliation ──────────────────────────
    # Runs AFTER every state machine transition to catch and correct any
    # cycle number drift before it propagates to the next tick.
    try:
        from automation.cycle_authority import reconcile as _ca_reconcile_post
        _rpt2 = _ca_reconcile_post(verbose=False)
        if "CORRECTED" in str(_rpt2.get("action", "")):
            state_now = _read_runner_state()
            write_controller_state(state_now.get("status", "IDLE"), cycle=_rpt2["consensus"])
            click.secho(
                f"  [CYCLE GUARD] Post-transition reconcile: {_rpt2['action']} "
                f"(confidence={_rpt2.get('confidence','?')})",
                fg="yellow",
            )
    except Exception:
        pass

    # M-STATUS-1 FIX: Regenerate current_status.md on every tick.
    # Was: last updated 2026-06-11 showing "Active Cycle 075 / PLANNED" while on 082-084.
    # Now: always reflects the current state so operator dashboards can be trusted.
    try:
        _st = _read_runner_state()
        _status_dir = runner_paths.status_dir()
        _status_dir.mkdir(parents=True, exist_ok=True)
        _status_file = _status_dir / "current_status.md"
        _status_file.write_text(
            f"# Fiverr Research System — Autonomous Runner Status\n\n"
            f"**Active Cycle:** {_st.get('active_cycle', '?')}\n"
            f"**Status:** {_st.get('status', '?')}\n"
            f"**Branch:** {_st.get('active_branch', 'unknown')}\n"
            f"**Last Updated:** {_now()}\n"
            f"**Last Heartbeat:** {_st.get('last_heartbeat', '?')}\n\n"
            f"> Auto-generated by tick — regenerated every 60 seconds.\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    # C7: Release tick lock (cluster A: shared helper used on every exit path)
    _release_tick_lock(_lock_file)

    click.echo("[TICK COMPLETE]")


@cli.command("pause-autopilot")
@click.option("--reason", default=None, help="Why the autopilot is being paused.")
def cmd_pause_autopilot(reason: str | None) -> None:
    """Pause the autopilot loop (item 0.2 kill-switch).

    Writes the autopilot_paused.json sentinel with paused:true. The next tick
    detects the sentinel by existence and returns without dispatching.
    """
    _write_pause(reason or "manual_operator")
    click.secho(
        f"AUTOPILOT PAUSED — sentinel written: {_pause_file_path()} "
        f"(reason={reason or 'manual_operator'}). Run 'resume-autopilot' to resume.",
        fg="yellow", bold=True,
    )


@cli.command("freeze")
@click.option("--reason", default=None, help="Why autonomy is being frozen.")
def cmd_freeze(reason: str | None) -> None:
    """Engage the SAFE-01 autonomy freeze (sets frozen: true).

    Rewrites autonomy_freeze.yml atomically. While frozen, tick and run-cycle
    fail closed and refuse to dispatch.
    """
    p = _write_autonomy_freeze(True, reason or "manual_operator_freeze")
    click.secho(
        f"AUTONOMY FROZEN — policy updated: {p} "
        f"(reason={reason or 'manual_operator_freeze'}). Run 'unfreeze' to lift.",
        fg="red", bold=True,
    )


@cli.command("unfreeze")
@click.option("--reason", default=None, help="Why autonomy is being unfrozen.")
def cmd_unfreeze(reason: str | None) -> None:
    """Lift the SAFE-01 autonomy freeze (sets frozen: false).

    Rewrites autonomy_freeze.yml atomically, preserving other keys.
    """
    p = _write_autonomy_freeze(False, reason or "manual_operator_unfreeze")
    click.secho(
        f"AUTONOMY UNFROZEN — policy updated: {p} "
        f"(reason={reason or 'manual_operator_unfreeze'}). Dispatch re-enabled.",
        fg="green", bold=True,
    )


@cli.command("resume-autopilot")
def cmd_resume_autopilot() -> None:
    """Resume the autopilot loop by removing the pause sentinel (idempotent)."""
    p = _pause_file_path()
    existed = p.exists()
    p.unlink(missing_ok=True)
    if existed:
        click.secho(f"AUTOPILOT RESUMED — sentinel removed: {p}", fg="green", bold=True)
    else:
        click.secho(
            f"AUTOPILOT already running — no pause sentinel present at {p}.",
            fg="green",
        )


@cli.command("daily-report")
@click.option("--cycle", default=None, type=int)
def cmd_daily_report(cycle: int | None) -> None:
    """Generate daily status report (OPS-022)."""
    from automation.report_generator import generate_daily_report
    path = generate_daily_report(cycle=cycle)
    click.secho(f"Daily report written: {path}", fg="green")


@cli.command("daily-stage-report")
def cmd_daily_stage_report() -> None:
    """Generate DAILY_STAGE_REPORT.json for Claude PM stage review."""
    from automation.daily_report_generator import generate_daily_stage_report

    try:
        path = generate_daily_stage_report()
        click.secho(f"Daily stage report written: {path}", fg="green")
    except Exception as exc:  # pragma: no cover - defensive no-blocking behavior
        _record_nonblocking_error(f"daily-stage-report failed: {exc}")
        fallback_path = runner_paths.reports_dir() / "DAILY_STAGE_REPORT.json"
        fallback_payload = {
            "generated_at": _now(),
            "current_stage": 2,
            "stage_states": {},
            "last_cycle": {
                "cycle_number": _read_runner_state().get("active_cycle", 82),
                "all_agents_complete": False,
                "test_suite_result": "FAIL",
                "pr_status": "FAILED",
                "ci_status": "FAIL",
                "repair_loop_triggered": False,
                "errors": [f"daily-stage-report generation error: {exc}"],
            },
            "health": {
                "heartbeat_age_minutes": -1,
                "model_gate_status": "FAIL",
                "runner_service_status": "STOPPED",
                "last_error": str(exc),
            },
            "claude_assessment_prompt": (
                "Review this report and respond with: STAGE_N_PASS (if everything looks good) "
                "or BLOCKED_<REASON> (if something needs attention)."
            ),
            "next_action": "WAIT_FOR_CLAUDE_REVIEW",
        }
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        fallback_path.write_text(json.dumps(fallback_payload, indent=2), encoding="utf-8")
        click.secho(f"Daily stage report fallback written: {fallback_path}", fg="yellow")
    raise SystemExit(0)


@cli.command("weekly-report")
def cmd_weekly_report() -> None:
    """Generate weekly autonomy review (OPS-023)."""
    from automation.report_generator import generate_weekly_report
    path = generate_weekly_report()
    click.secho(f"Weekly report written: {path}", fg="green")


@cli.command("post-cycle-review")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--pr", default=None, type=int, help="PR number (if known).")
@click.option("--mode", default="POST_CYCLE_PM_REVIEW",
              type=click.Choice(["POST_CYCLE_PM_REVIEW", "POST_AGENT_CYCLE_REVIEW"]),
              help="Review mode.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Collect facts only, do not write artifacts.")
@click.option("--skip-local-validation", is_flag=True, default=False,
              help="Skip local ruff/pytest run (use when CI is already green and tests are confirmed passing).")
def cmd_post_cycle_review(cycle: int, pr: int | None, mode: str, dry_run: bool,
                          skip_local_validation: bool) -> None:
    """Run post-cycle PM review. Blocks next dispatch until PASS."""
    click.echo("=" * 60)
    click.echo(f"POST-CYCLE REVIEW -- Cycle {cycle:03d} [{mode}]")
    click.echo("=" * 60)

    from automation.post_cycle_review import ReviewMode, ReviewResult, collect_facts, run_review

    rev_mode = ReviewMode.POST_MERGE if mode == "POST_CYCLE_PM_REVIEW" else ReviewMode.POST_AGENT

    if dry_run:
        click.echo("  Collecting facts (dry-run, no artifacts written)...")
        facts = collect_facts(cycle, rev_mode, pr)
        click.echo(f"  PR merged        : {facts.pr_merged}")
        click.echo(f"  CI passed        : {facts.ci_passed}")
        click.echo(f"  Codecov project  : {facts.codecov_project}")
        click.echo(f"  Baseline DB ok   : {facts.baseline_db_mtime_unchanged}")
        click.echo(f"  ScrapFly off     : {facts.scrapfly_enabled_false}")
        click.echo(f"  Agent reports    : {facts.agent_reports_present}")
        click.secho("DRY RUN COMPLETE", fg="cyan")
        return

    result = run_review(cycle=cycle, mode=rev_mode, pr_number=pr,
                        skip_local_validation=skip_local_validation)
    click.echo(result.summary())
    click.echo()
    for path in result.artifact_paths:
        click.echo(f"  Artifact: {path}")

    if result.result == ReviewResult.PASS:
        click.secho("POST-CYCLE REVIEW PASS -- next dispatch unlocked", fg="green", bold=True)
        from automation.stage_executor import StageExecutor
        from automation.state_writer import write_controller_state, write_heartbeat
        write_heartbeat("POST_CYCLE_PASS", cycle=cycle)
        write_controller_state("POST_CYCLE_PASS", cycle=cycle)
        try:
            advanced = StageExecutor(None, {}).advance_if_ready()
            click.echo(f"  StageExecutor advance_if_ready: {advanced}")
        except Exception as exc:  # pragma: no cover - defensive
            _record_nonblocking_error(f"stage advance hook failed: {exc}")
    elif result.result == ReviewResult.ADVISORY_ONLY:
        # Hard gates passed; scoring corrections are advisory — treat as conditional PASS
        click.secho("POST-CYCLE REVIEW ADVISORY_ONLY (conditional PASS) -- dispatch unlocked with advisory warnings",
                    fg="yellow", bold=True)
        from automation.stage_executor import StageExecutor
        from automation.state_writer import write_controller_state, write_heartbeat
        write_heartbeat("POST_CYCLE_PASS", cycle=cycle)
        write_controller_state("POST_CYCLE_PASS", cycle=cycle)
        try:
            advanced = StageExecutor(None, {}).advance_if_ready()
            click.echo(f"  StageExecutor advance_if_ready: {advanced}")
        except Exception as exc:  # pragma: no cover - defensive
            _record_nonblocking_error(f"stage advance hook failed: {exc}")
    else:
        click.secho(f"POST-CYCLE REVIEW {result.result.value}", fg="yellow", bold=True)
        if result.blocks_dispatch:
            click.secho("DISPATCH BLOCKED -- resolve errors before next cycle", fg="red")
            raise SystemExit(1)


@cli.command("merge-gate")
@click.option("--pr", required=True, type=int, help="PR number.")
@click.option("--dry-run", "do_dry_run", is_flag=True, default=True,
              help="Check gates only, do not merge (default: True).")
@click.option("--execute-merge", is_flag=True, default=False,
              help="Actually merge if all gates pass.")
def cmd_merge_gate(pr: int, do_dry_run: bool, execute_merge: bool) -> None:
    """Run full merge gate check for a PR. Safe by default (dry-run)."""
    click.echo("=" * 60)
    live = not do_dry_run or execute_merge
    click.echo(f"MERGE GATE - PR #{pr} {'[LIVE]' if live else '[DRY RUN]'}")
    click.echo("=" * 60)
    from automation.merge_gate import run as gate_run
    # Item 3.2: run() is safe-by-default; the actual merge requires execute=True.
    result = gate_run(pr_number=pr, dry_run=(not execute_merge), execute=execute_merge)
    click.echo(result.summary())
    click.echo()
    if result.passed:
        if execute_merge and (result.merge_sha or result.already_merged):
            click.secho(f"MERGED to develop: {result.merge_sha or '(already merged)'}", fg="green", bold=True)
        else:
            click.secho("MERGE GATE PASS - run with --execute-merge to merge", fg="green", bold=True)
    else:
        fails = len(result.failed_checks())
        click.secho(f"MERGE GATE FAIL - {fails} blocking failures", fg="red", bold=True)
        raise SystemExit(1)


@cli.command("create-labels")
def cmd_create_labels() -> None:
    """Create all required GitHub labels for the autonomous runner."""
    click.echo("=" * 60)
    click.echo("CREATE GITHUB LABELS")
    click.echo("=" * 60)
    import subprocess
    labels = [
        ("ai-runner", "0052cc", "Managed by autonomous AI runner"),
        ("type:feature", "0075ca", "Feature work"),
        ("type:fix", "e4e669", "Bug fix"),
        ("type:test", "c2e0c6", "Test additions"),
        ("type:chore", "ededed", "Chore/housekeeping"),
        ("risk:low", "c2e0c6", "Low risk change"),
        ("risk:medium", "fbca04", "Medium risk change"),
        ("risk:high", "e11d48", "High risk change"),
        ("risk:critical", "b60205", "Critical risk change"),
        ("agent:A", "1d76db", "Agent A work"),
        ("agent:B", "0e8a16", "Agent B work"),
        ("agent:C", "5319e7", "Agent C work"),
        ("agent:D", "e4e669", "Agent D work"),
        ("agent:E", "d93f0b", "Agent E work"),
        ("agent:F", "0075ca", "Agent F work"),
        ("status:ai-running", "0052cc", "AI runner actively working"),
        ("status:ai-repairing", "fbca04", "AI runner in repair loop"),
        ("status:merge-gate-pass", "0e8a16", "Merge gate passed"),
        ("status:merge-gate-blocked", "e11d48", "Merge gate blocked"),
        ("needs:jira-sync", "ededed", "Needs Jira sync"),
        ("needs:codex-disposition", "ededed", "Needs Codex review disposition"),
        ("needs:coverage-repair", "fbca04", "Needs coverage repair"),
    ]
    created, failed = 0, 0
    for name, color, desc in labels:
        r = subprocess.run(
            ["gh", "label", "create", name,
             "--repo", "KevinSGarrett/Fiverr",
             "--color", color, "--description", desc, "--force"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            click.secho(f"  [OK] {name}", fg="green")
            created += 1
        else:
            click.secho(f"  [FAIL] {name}: {r.stderr.strip()[:60]}", fg="red")
            failed += 1
    click.echo()
    click.echo(f"Created/updated: {created}  Failed: {failed}")
    if failed == 0:
        click.secho("LABELS COMPLETE", fg="green", bold=True)

def _porcelain_paths(line: str) -> list[str]:
    """All file paths a ``git status --porcelain`` (v1) line refers to.

    Item 5.4: the previous parse — ``line.strip().lstrip("?! MAD")`` — was a
    character-SET strip, so it ate leading filename characters that happen to be in
    {?,!,space,M,A,D} (e.g. ``" M Makefile"`` -> ``"akefile"``), and the upstream
    ``.stdout.strip()`` destroyed the first line's leading status column. Porcelain
    v1 has a FIXED layout — two status columns + one space, then the path — so the
    path always begins at column 3. A rename/copy renders as ``old -> new`` and
    touches BOTH paths (the source is a tracked non-artifact file that moved), so we
    return both; otherwise a single path. Empty/short lines -> ``[]``.
    """
    if len(line) < 4:
        return []
    rest = line[3:]
    if " -> " in rest:
        old, new = rest.split(" -> ", 1)
        return [p for p in (old.strip(), new.strip()) if p]
    rest = rest.strip()
    return [rest] if rest else []


def _porcelain_status_path(line: str) -> str:
    """Destination (last) path of a porcelain line; ``""`` if none. For a rename this
    is the new path; for a plain change it is the only path."""
    paths = _porcelain_paths(line)
    return paths[-1] if paths else ""


def _porcelain_is_artifact_only(line: str, prefixes: tuple[str, ...]) -> bool:
    """True iff EVERY path the line touches is under a runtime-artifact prefix.

    A rename whose source is a real (non-artifact) file is NOT artifact-only — its
    moved source must still trip the dirty-repo gate (Codex review on #127), so the
    line is suppressed only when both sides live under artifact prefixes."""
    paths = _porcelain_paths(line)
    return bool(paths) and all(
        any(p.startswith(pref) for pref in prefixes) for p in paths
    )


def _dirty_blocking_lines(git_status_raw: str, prefixes: tuple[str, ...]) -> list[str]:
    """Item 5.4-T5: the porcelain lines that should BLOCK dispatch = any change (tracked
    OR untracked) whose path is NOT a runtime artifact. Exemption is by PATH, not by
    tracked-status: an artifact-path line (logs/runs/drafts/cycle-log) is exempt whether
    tracked-modified or untracked, but an untracked NON-artifact SOURCE file (e.g.
    ``?? src/new_feature.py``) STILL blocks — a new uncommitted source file must not be
    hidden from the guard (Codex review on #130). The runner's known artifact outputs
    (cycle logs, synthesis json) are additionally gitignored so they never reach
    porcelain; this filter is the backstop for tracked artifact mods + the line that
    keeps real source changes blocking."""
    return [
        line for line in git_status_raw.splitlines()
        if line.strip() and not _porcelain_is_artifact_only(line, prefixes)
    ]


@cli.command("status-tick")
def cmd_status_tick() -> None:
    """Status-only tick — reads state and writes next_action_decision.json.

    Unlike tick, status-tick NEVER advances state machine or dispatches anything.
    V6-TICK-001/003: every tick writes next_action_decision.json explaining why
    it did/did not dispatch. status-tick is safe to call at any time.
    """
    from automation.state_writer import write_heartbeat

    state = _read_runner_state()
    status = state.get("status", "IDLE")
    cycle  = state.get("active_cycle")
    now = _now()

    write_heartbeat(status, cycle=cycle)

    # Check freeze
    from automation.freeze_gate import is_frozen
    frozen = is_frozen(REPO_ROOT)

    # Check dirty repo — M-STATE-2 FIX: exclude known runtime artifact paths
    # that the loop itself writes into the working tree, so we don't block
    # ourselves with BLOCKED_DIRTY_REPO on every cycle.
    import subprocess as _sp
    # Item 5.4: use --porcelain (stable, documented format) and DO NOT strip the
    # raw output — a leading .strip() would destroy the first line's leading status
    # column ("XY path") and misalign the fixed-width parse below.
    git_status_raw = _sp.run(
        ["git", "status", "--porcelain"], cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    ).stdout

    # Tracked paths written by the runtime that should not block dispatch.
    # Item 5.4-T5: PM_Pack/10_cycle_log/ is per-cycle log output (also gitignored) —
    # exempt it so even a tracked-then-modified cycle-log file never blocks.
    _ARTIFACT_PREFIXES = (
        "PM_Pack/automation/post_cycle_reviews/",
        "PM_Pack/automation/runs/",
        "PM_Pack/automation/ref_catalogs/",
        "PM_Pack/automation/prompts/drafts/",
        "PM_Pack/automation/current_policy_snapshot.json",
        "PM_Pack/automation/prompt_package_manifest.json",
        "PM_Pack/10_cycle_log/",
    )
    # Item 5.4-T5: block ONLY on uncommitted tracked source — untracked output and
    # tracked artifact-path changes never wedge the runner. (Was: counted untracked
    # cycle-log/synthesis output as "dirty", refusing to run on the loop's own logs.)
    _dirty_lines = _dirty_blocking_lines(git_status_raw, _ARTIFACT_PREFIXES)
    git_status = "\n".join(_dirty_lines)
    repo_dirty = bool(git_status)

    # Determine next action
    if frozen:
        next_action = "BLOCKED_AUTONOMY_FROZEN"
        reason = "autonomy_freeze.yml has frozen: true"
    elif repo_dirty:
        next_action = "BLOCKED_DIRTY_REPO"
        reason = f"Repo has uncommitted changes: {git_status[:100]}"
    elif status in ("IDLE", "POST_CYCLE_PASS"):
        next_action = "PLAN_READY"
        reason = "Ready for next cycle — run compile-policy then plan-cycle"
    elif status == "PLANNED":
        next_action = "VALIDATE_PROMPTS"
        reason = "Prompts exist — run validate-prompts to check"
    elif status == "READY_TO_DISPATCH":
        next_action = "AWAITING_MODEL_GATE"
        reason = "Model gate check required before dispatch"
    elif status in ("DISPATCHING", "AGENT_DISPATCH", "CURSOR_RUNNING"):
        next_action = "MONITOR_AGENT"
        reason = "Agent currently running — monitor heartbeat"
    elif status == "CYCLE_NO_WORK":
        next_action = "REDISPATCH_NO_WORK"
        reason = "Last run committed nothing — re-dispatch a real run"
    elif status == "PR_CREATE_FAILED":
        next_action = "RETRY_PR_CREATE"
        reason = "Committed work but PR-create failed — re-attempt open_cycle_pr"
    elif status == "AWAITING_CI_GREEN":
        next_action = "WAIT_CI_GREEN"
        reason = "PR open — waiting for required CI to go green before merge"
    elif status == "MERGING":
        next_action = "MERGING"
        reason = "Required CI green — running merge gate to squash-merge the PR"
    elif status == "MERGED":
        next_action = "ADVANCE_CYCLE"
        reason = "PR merged — advancing to the next cycle"
    elif status == "MERGE_BLOCKED":
        next_action = "RETRY_OR_OPERATOR_MERGE"
        reason = "Merge blocked (CI/gate) — bounded retry then operator action"
    elif status == "POST_CYCLE_PENDING":
        next_action = "POST_CYCLE_REVIEW"
        reason = "Awaiting post-cycle review"
    elif status == "DEVELOP_SYNC_BLOCKED":
        next_action = "RESYNC_DEVELOP_OR_OPERATOR"
        reason = ("Integration branch could not be made current with origin/develop "
                  "(conflict or git error) — bounded auto-retry, then operator")
    else:
        next_action = f"UNKNOWN_STATUS_{status}"
        reason = "Unknown status — check controller_state.json"

    # Write decision artifact (V6-TICK-003)
    decision = {
        "evaluated_at": now,
        "current_status": status,
        "active_cycle": cycle,
        "frozen": frozen,
        "repo_dirty": repo_dirty,
        "next_action": next_action,
        "reason": reason,
        "source": "status-tick (read-only)",
    }
    decision_path = runner_paths.state_dir() / "next_action_decision.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    decision_path.write_text(_json.dumps(decision, indent=2))

    click.echo(f"[STATUS-TICK] {now}")
    click.echo(f"  Status     : {status}")
    click.echo(f"  Cycle      : {cycle}")
    click.echo(f"  Frozen     : {frozen}")
    click.echo(f"  Repo dirty : {repo_dirty}")
    click.echo(f"  Next action: {next_action}")
    click.echo(f"  Reason     : {reason}")
    click.echo(f"  Decision   : {decision_path}")


@cli.command("pm-pack-audit")
def cmd_pm_pack_audit() -> None:
    """PM_Pack consistency audit — validates semantic agreement across all state files.

    Checks: HYDRATION_HEADER vs controller_state vs current_status vs policy_snapshot.
    Required by V6-PM-013. Must PASS before plan-cycle --live is allowed.
    """
    from automation.pm_pack_consistency_audit import run_audit
    result = run_audit()
    click.echo(result.summary())
    if result.sources:
        click.echo("")
        click.echo("  State sources:")
        for k, v in result.sources.items():
            click.echo(f"    {k}: {v!r}")
    if not result.passed:
        click.secho("PM_PACK_AUDIT BLOCKED — resolve conflicts before running plan-cycle",
                    fg="red", bold=True)
        raise SystemExit(1)
    click.secho("PM_PACK_AUDIT PASS", fg="green", bold=True)


# ---------------------------------------------------------------------------
# 24/7 AUTOPILOT — single terminal command to run the full system forever
# ---------------------------------------------------------------------------

@cli.command("start-autopilot")
@click.option("--interval", default=60, show_default=True,
              help="Seconds between ticks.")
@click.option("--max-cycles", default=0, show_default=True,
              help="Stop after N cycles complete (0 = run until Ctrl+C).")
def cmd_start_autopilot(interval: int, max_cycles: int) -> None:
    """Run the autonomous build loop in this terminal until Ctrl+C.

    Each iteration:
      1. Runs tick (auto-dispatches Cursor agents when prompts are ready)
      2. Agents write code, open PRs, pass CI
      3. Claude PM reviews the work and grades the cycle
      4. Next cycle is planned and the loop repeats

    \b
    Usage:
        python automation/ai_cycle_controller.py start-autopilot
        python automation/ai_cycle_controller.py start-autopilot --interval 30
        python automation/ai_cycle_controller.py start-autopilot --max-cycles 5
    """
    import signal

    stop_flag = {"stop": False}
    cycles_completed = 0
    last_completed_cycle = None

    def _on_stop(sig: int, _frame: object) -> None:
        click.secho(
            "\n\n  [AUTOPILOT] Ctrl+C — stopping after this tick completes...",
            fg="yellow", bold=True,
        )
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, _on_stop)
    signal.signal(signal.SIGTERM, _on_stop)

    click.secho("\n" + "=" * 62, fg="cyan", bold=True)
    click.secho("  FIVERR RESEARCH SYSTEM — 24/7 AUTONOMOUS BUILD MODE", fg="cyan", bold=True)
    click.secho("=" * 62, fg="cyan", bold=True)
    click.secho(f"  Tick interval : every {interval}s", fg="cyan")
    click.secho(f"  Max cycles    : {'unlimited (Ctrl+C to stop)' if max_cycles == 0 else max_cycles}", fg="cyan")
    click.secho("=" * 62 + "\n", fg="cyan", bold=True)

    tick_count = 0
    # HIGH-7: circuit breaker. A tick that fails (non-zero exit or exception) every
    # iteration would otherwise spin forever every `interval`s, burning the Cursor/
    # Claude quota and hammering GitHub with no human ever noticing. Count CONSECUTIVE
    # failed ticks; after the cap, engage the SAFE-01 autonomy freeze (so a scheduled-
    # task restart won't just resume the runaway) and stop. A single success resets it.
    consecutive_tick_failures = 0
    _breaker_cap = int(os.environ.get("AUTOPILOT_MAX_CONSECUTIVE_TICK_FAILURES", "10"))

    while not stop_flag["stop"]:
        tick_count += 1
        state = _read_runner_state()
        status = state.get("status", "IDLE")
        cycle  = state.get("active_cycle", 0)

        import automation.autopilot_logger as L
        L.tick_header(tick_count, status, cycle)

        # Explain what each status means so operator is never confused
        _STATUS_EXPLANATION = {
            "PLANNED": "Prompts exist — validating before dispatch",
            "READY_TO_DISPATCH": "All gates pass — dispatching Cursor agents now",
            "DISPATCHING": "Launching run-cycle (6 Cursor agents)",
            "AGENT_DISPATCH": "Cursor agents are writing code (10-40 min — this is normal)",
            "AGENT_COMPLETE": "All agents done — running post-cycle review",
            "POST_CYCLE_PENDING": "Running lint + tests + Jira sync + Claude PM review",
            "POST_CYCLE_PASS": "Cycle passed — planning next cycle",
            "POST_CYCLE_FAIL": "Cycle FAILED review — check details above",
            "CYCLE_NO_WORK": "Cycle produced no committed work — re-dispatching real work",
            "PR_CREATE_FAILED": "PR-create failed (token/push/verify) — re-attempting open_cycle_pr",
            "AWAITING_CI_GREEN": "PR open — waiting for required CI to go green before merge",
            "MERGING": "Required CI green — merge gate squash-merging the PR",
            "MERGED": "PR merged — advancing to the next cycle",
            "MERGE_BLOCKED": "Merge blocked (CI/gate) — bounded retry, then operator action",
            "IDLE": "Idle — will compile policy and plan next cycle",
            "MODEL_BLOCKED": "Cursor model gate failed — re-checking...",
            "BRANCH_MISMATCH_BLOCKED": "Wrong git branch — auto-fixing...",
            "PROMPT_VALIDATION_FAILED": "Prompts invalid — bounded regenerate + re-validate...",
            "PROMPT_REGEN_EXHAUSTED": "Prompt regeneration exhausted — run 'recover --regen' or fix the generator",
        }
        explanation = _STATUS_EXPLANATION.get(status, f"Status: {status}")
        L.info(explanation)

        # Detect a cycle just completing
        if status in ("POST_CYCLE_PASS",) and last_completed_cycle != cycle:
            last_completed_cycle = cycle
            cycles_completed += 1
            L.ok(f"CYCLE {cycle:03d} COMPLETE  (session total: {cycles_completed})")
            if max_cycles > 0 and cycles_completed >= max_cycles:
                L.warn(f"Reached max-cycles={max_cycles}. Stopping.")
                break

        # Execute tick with live streaming (not capture) so all output appears immediately
        import subprocess as _subp
        try:
            _proc = _subp.Popen(
                [sys.executable, "automation/ai_cycle_controller.py", "tick"],
                stdout=_subp.PIPE, stderr=_subp.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                cwd=str(REPO_ROOT),
            )
            for _line in _proc.stdout:
                _stripped = _line.rstrip()
                if _stripped:
                    click.echo(f"  {_stripped}")
            _proc.wait()
            if _proc.returncode != 0:
                L.error(f"Tick exited with code {_proc.returncode}")
                consecutive_tick_failures += 1
            else:
                consecutive_tick_failures = 0  # a clean tick resets the breaker
        except Exception as exc:
            L.error(f"Tick raised exception: {exc}")
            import traceback
            L.info(traceback.format_exc()[-300:])
            consecutive_tick_failures += 1

        # HIGH-7 circuit breaker: too many CONSECUTIVE failed ticks → freeze + stop.
        if consecutive_tick_failures >= _breaker_cap:
            L.error(
                f"CIRCUIT BREAKER: {consecutive_tick_failures} consecutive failed ticks "
                f"(cap {_breaker_cap}) — engaging autonomy freeze and stopping autopilot"
            )
            try:
                _write_autonomy_freeze(
                    True,
                    f"circuit_breaker: {consecutive_tick_failures} consecutive failed ticks",
                )
            except Exception as _frz_exc:  # pragma: no cover - defensive
                L.warn(f"freeze-write failed in circuit breaker: {_frz_exc}")
            try:
                from automation.notification_router import notify_blocked as _nb_cb
                _nb_cb(
                    "Autopilot circuit breaker tripped — autonomy frozen",
                    body=(
                        f"{consecutive_tick_failures} consecutive ticks failed. Autonomy "
                        "is now frozen (run 'unfreeze' after fixing the root cause). "
                        "Autopilot stopped to avoid a runaway loop."
                    ),
                    incident_code="AUTOPILOT_CIRCUIT_BREAKER",
                )
            except Exception as _nb_exc:  # pragma: no cover - defensive
                L.warn(f"circuit-breaker notification failed: {_nb_exc}")
            break

        # Show live event feed (events written by all stages across subprocess boundaries)
        from automation.live_events import recent as _ev_recent
        _events = _ev_recent(n=12)
        if _events:
            click.echo("")
            click.secho("  ---- Pipeline events ----", fg="blue")
            for _ev in _events:
                _stage = _ev.get("stage", "?")
                _msg = _ev.get("msg", "")
                _ts = _ev.get("ts", "")
                _agent = _ev.get("agent", "")
                _st = _ev.get("status", "INFO")
                _agent_str = f" [Agent {_agent}]" if _agent else ""
                _color = {"OK": "green", "FAIL": "red", "WARN": "yellow", "RUNNING": "cyan"}.get(_st, "white")
                click.secho(
                    f"  {_ts}  {_stage:<10}{_agent_str:<10}  {_msg}",
                    fg=_color
                )

        if stop_flag["stop"]:
            break

        # Countdown to next tick — use newline (not \r) since \r doesn't work in PowerShell
        import time as _time2
        _time2.sleep(interval)
        click.echo("")  # newline after countdown

    # Summary on exit
    state = _read_runner_state()
    click.secho("\n" + "=" * 62, fg="cyan", bold=True)
    click.secho("  AUTOPILOT STOPPED", fg="cyan", bold=True)
    click.secho(f"  Total ticks run     : {tick_count}", fg="cyan")
    click.secho(f"  Cycles completed    : {cycles_completed}", fg="cyan")
    click.secho(
        f"  Final state         : {state.get('status')}  cycle={state.get('active_cycle')}",
        fg="cyan",
    )
    click.secho("=" * 62 + "\n", fg="cyan", bold=True)


if __name__ == "__main__":
    cli()
