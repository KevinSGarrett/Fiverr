"""Audit rank-7: the COMPILED/PLANNING → plan-cycle retry must be BOUNDED.

plan-cycle calls Claude to author prompts, so re-running it every tick on a persistently
failing generator burns Claude quota forever — and the tick "succeeds" (exit 0) each time
so neither the tick hard-timeout (not hung, just failing) nor the circuit breaker (no
failed tick) ever catches it. _handle_plan_cycle_result caps the retries and then holds in
the cheap PROMPT_REGEN_EXHAUSTED state (re-validation only, no Claude calls), with periodic
auto-retry so a transient failure still self-heals with no operator.
"""
from __future__ import annotations

import automation.ai_cycle_controller as ctrl


def _capture_state(monkeypatch):
    written = []
    import automation.state_writer as sw
    monkeypatch.setattr(sw, "write_controller_state",
                        lambda status, **kw: written.append(status))
    # neutralize tick-counter persistence side effects but keep counting semantics:
    counts: dict[str, int] = {}
    def _tc(key, *, increment=False, reset=False):
        if reset:
            counts[key] = 0
            return 0
        if increment:
            counts[key] = counts.get(key, 0) + 1
            return counts[key]
        return counts.get(key, 0)
    monkeypatch.setattr(ctrl, "_tick_counter", _tc)
    return written, counts


def test_success_routes_to_planned_and_resets(monkeypatch):
    written, counts = _capture_state(monkeypatch)
    counts["planning_retry_84"] = 3  # pretend prior failures
    ctrl._handle_plan_cycle_result(0, "ok", 84)
    assert written == ["PLANNED"]
    assert counts["planning_retry_84"] == 0, "a success resets the retry counter"


def test_failure_under_cap_retries_planning(monkeypatch):
    written, counts = _capture_state(monkeypatch)
    monkeypatch.setenv("AUTOPILOT_PLANNING_MAX", "5")
    for _ in range(5):
        ctrl._handle_plan_cycle_result(1, "boom", 84)
    assert written == ["PLANNING"] * 5, "under the cap, keep retrying via PLANNING"


def test_failure_over_cap_holds_exhausted_no_more_claude(monkeypatch):
    written, counts = _capture_state(monkeypatch)
    monkeypatch.setenv("AUTOPILOT_PLANNING_MAX", "3")
    # neutralize notify
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked", lambda *a, **k: None, raising=False)
    seq = []
    for _ in range(4):  # 1,2,3 = PLANNING; 4 > cap → EXHAUSTED
        ctrl._handle_plan_cycle_result(1, "boom", 84)
        seq.append(written[-1])
    assert seq == ["PLANNING", "PLANNING", "PLANNING", "PROMPT_REGEN_EXHAUSTED"]
    assert counts["planning_retry_84"] == 0, "counter reset on escalation so retry window restarts"


def test_handler_stops_burning_claude_past_cap():
    """Source guard: past the cap the handler must route to PROMPT_REGEN_EXHAUSTED (a state
    whose handler does NOT call plan-cycle) — i.e. it stops invoking Claude."""
    import inspect
    src = inspect.getsource(ctrl._handle_plan_cycle_result)
    assert "AUTOPILOT_PLANNING_MAX" in src
    assert 'PROMPT_REGEN_EXHAUSTED' in src
    # the handler itself never SPAWNS plan-cycle (no subprocess) — it only routes state;
    # only the COMPILED/PLANNING state handlers invoke _run_shell_command.
    assert "_run_shell_command" not in src


def test_exhausted_has_periodic_auto_retry():
    """rank-7: PROMPT_REGEN_EXHAUSTED must periodically route back to COMPILED so a
    transient failure self-heals without an operator (not a permanent dead-end)."""
    import inspect
    src = inspect.getsource(ctrl.cmd_tick.callback)
    i = src.index('status == "PROMPT_REGEN_EXHAUSTED"')
    seg = src[i:i + 3000]
    assert "AUTOPILOT_PROMPT_REGEN_RETRY_TICKS" in seg
    assert "prompt_regen_hold_" in seg
    assert 'write_controller_state("COMPILED"' in seg
