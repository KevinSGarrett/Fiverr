"""Item 0.5 -- Persistent scheduled driver + watchdog (host-plane), version-controlled.

These are PURE TEXT assertions over the version-controlled ``host/*.ps1`` scripts.
They do NOT execute PowerShell -- they read each script as text and assert the
required, audited properties hold. "What runs == what's audited": the scripts
live in the repo so CI can re-enforce these invariants forever.

Covered scripts (under repo ``host/``):
  * start_controller.ps1  -- continuous driver (start-autopilot, NOT bare tick),
    branch-pin (develop + pull --ff-only), refuses main/detached.
  * watchdog.ps1          -- stuck/spinning detection (age AND progress/repeat),
    relaunches the driver directly (not schtasks /Run on a logon task),
    honors the pause sentinel.
  * register_driver.ps1   -- non-interactive (run whether logged on or not / S4U),
    RunLevel Highest, restart-on-failure, at-startup trigger, deletes duplicate
    tasks, guarded (default does not register without -Execute/-Confirm).
  * deploy_host_scripts.ps1 -- default dry-run; requires -Execute to copy.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# Repo root: tests/unit/<this file> -> parents[2] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_DIR = REPO_ROOT / "host"


def _read(name: str) -> str:
    p = HOST_DIR / name
    assert p.exists(), f"expected host script missing: {p}"
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures -- read each script once.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def start_controller() -> str:
    return _read("start_controller.ps1")


@pytest.fixture(scope="module")
def watchdog() -> str:
    return _read("watchdog.ps1")


@pytest.fixture(scope="module")
def register_driver() -> str:
    return _read("register_driver.ps1")


@pytest.fixture(scope="module")
def deploy_scripts() -> str:
    return _read("deploy_host_scripts.ps1")


# ---------------------------------------------------------------------------
# All four host scripts must exist.
# ---------------------------------------------------------------------------
def test_all_host_scripts_exist() -> None:
    for name in (
        "start_controller.ps1",
        "watchdog.ps1",
        "register_driver.ps1",
        "deploy_host_scripts.ps1",
    ):
        assert (HOST_DIR / name).exists(), f"missing host/{name}"


# ---------------------------------------------------------------------------
# start_controller.ps1
# ---------------------------------------------------------------------------
def test_start_controller_runs_continuous_autopilot(start_controller: str) -> None:
    # Runs the CONTINUOUS driver.
    assert "start-autopilot" in start_controller


def test_start_controller_does_not_run_bare_tick(start_controller: str) -> None:
    # Must NOT invoke the single-shot `tick` command as the driver. We look for
    # `ai_cycle_controller.py tick` (with optional .py path) -- the broken legacy
    # behavior -- and assert it is absent.
    assert not re.search(
        r"ai_cycle_controller\.py\s+tick\b", start_controller
    ), "start_controller.ps1 must run start-autopilot (continuous), not single-shot tick"


def test_start_controller_branch_pin(start_controller: str) -> None:
    # Branch-pin to develop with a fast-forward-only pull.
    assert "develop" in start_controller
    assert "--ff-only" in start_controller
    assert "fetch" in start_controller


def test_start_controller_refuses_main(start_controller: str) -> None:
    # Must refuse to run on main (and ideally detached HEAD).
    lowered = start_controller.lower()
    assert "main" in start_controller
    # An explicit refusal/exit tied to main.
    assert "refus" in lowered or "exit 1" in lowered


def test_start_controller_verifies_remote(start_controller: str) -> None:
    assert "KevinSGarrett/Fiverr" in start_controller


def test_start_controller_loads_secrets_and_utf8(start_controller: str) -> None:
    assert "runner.env" in start_controller
    assert "PYTHONIOENCODING" in start_controller
    assert "PYTHONUTF8" in start_controller


def test_start_controller_deploy_header_comment(start_controller: str) -> None:
    # Clear header noting it is deployed to C:\AI_Runner\scripts via deploy script.
    assert "deploy_host_scripts.ps1" in start_controller
    assert r"C:\AI_Runner\scripts" in start_controller


# ---------------------------------------------------------------------------
# watchdog.ps1
# ---------------------------------------------------------------------------
def test_watchdog_heartbeat_age_check(watchdog: str) -> None:
    # Heartbeat-age (dead) detection.
    assert "heartbeat" in watchdog.lower()
    assert re.search(r"age", watchdog, re.IGNORECASE)


def test_watchdog_stuck_spinning_detection(watchdog: str) -> None:
    # Stuck/spinning detection: a persisted progress file tracking repeat count,
    # plus a state+cycle comparison across checks.
    assert "watchdog_progress.json" in watchdog
    lowered = watchdog.lower()
    assert "repeat" in lowered, "watchdog must track a repeat count for stuck detection"
    assert "stuck" in lowered or "spinning" in lowered
    # Must reference both heartbeat state and cycle to detect no-progress.
    assert "state" in lowered
    assert "cycle" in lowered


def test_watchdog_relaunches_directly_not_schtasks_run(watchdog: str) -> None:
    # Must relaunch the driver DIRECTLY -- not `schtasks /Run` on a logon task.
    assert not re.search(
        r"schtasks\s+/run", watchdog, re.IGNORECASE
    ), "watchdog must NOT use `schtasks /Run` on a logon-bound task"
    # Direct relaunch: Start-ScheduledTask or running start_controller.ps1 directly.
    assert ("Start-ScheduledTask" in watchdog) or ("start_controller.ps1" in watchdog)


def test_watchdog_honors_pause_sentinel(watchdog: str) -> None:
    assert "autopilot_paused.json" in watchdog
    lowered = watchdog.lower()
    assert "pause" in lowered


def test_watchdog_emits_incident(watchdog: str) -> None:
    assert "incidents" in watchdog.lower()


def test_watchdog_restarts_runner_service(watchdog: str) -> None:
    # Preserve existing GitHub Actions runner-service restart behavior.
    assert "actions.runner" in watchdog
    assert "Start-Service" in watchdog


# ---------------------------------------------------------------------------
# register_driver.ps1
# ---------------------------------------------------------------------------
def test_register_driver_non_interactive(register_driver: str) -> None:
    # "Run whether logged on or not" == S4U / explicit LogonType.
    lowered = register_driver.lower()
    assert ("s4u" in lowered) or ("logontype" in lowered), (
        "register_driver must configure non-interactive (S4U / LogonType) -- "
        "run whether logged on or not"
    )
    assert "whether logged on or not" in lowered


def test_register_driver_run_level_highest(register_driver: str) -> None:
    assert "RunLevel Highest" in register_driver


def test_register_driver_restart_on_failure(register_driver: str) -> None:
    assert "RestartCount" in register_driver
    assert "RestartInterval" in register_driver


def test_register_driver_at_startup_trigger(register_driver: str) -> None:
    assert "-AtStartup" in register_driver


def test_register_driver_execution_time_limit_unlimited(register_driver: str) -> None:
    assert "ExecutionTimeLimit" in register_driver


def test_register_driver_battery_settings(register_driver: str) -> None:
    # Correct New-ScheduledTaskSettingsSet switch names (Codex P1 on #111).
    assert "-AllowStartIfOnBatteries" in register_driver
    assert "-DontStopIfGoingOnBatteries" in register_driver
    assert "StartWhenAvailable" in register_driver
    # invalid param names gone (leading dash avoids DontStop... substring match)
    assert "-DisallowStartIfOnBatteries" not in register_driver
    assert "-StopIfGoingOnBatteries" not in register_driver


def test_register_driver_deletes_duplicate_tasks(register_driver: str) -> None:
    assert "Unregister-ScheduledTask" in register_driver
    lowered = register_driver.lower()
    assert "duplicate" in lowered
    # The named legacy duplicates the spec calls out.
    assert "WatchdogRunner" in register_driver


def test_register_driver_registers_one_watchdog(register_driver: str) -> None:
    # Watchdog task registered every 5 minutes.
    assert "Register-ScheduledTask" in register_driver
    assert re.search(r"Minutes\s+5", register_driver)


def test_register_driver_configures_power(register_driver: str) -> None:
    assert "powercfg" in register_driver
    assert "standby-timeout-ac" in register_driver
    assert "hibernate-timeout-ac" in register_driver


def test_register_driver_is_guarded(register_driver: str) -> None:
    # Default = dry-run; requires -Execute / -Confirm to actually register.
    assert re.search(r"\[switch\]\s*\$Execute", register_driver)
    lowered = register_driver.lower()
    assert "dry-run" in lowered or "dry run" in lowered
    # There must be a gate variable controlling whether actions actually run.
    assert "$DoIt" in register_driver or "$Execute" in register_driver


def test_register_driver_uses_settings_set(register_driver: str) -> None:
    assert "New-ScheduledTaskSettingsSet" in register_driver
    assert "New-ScheduledTaskPrincipal" in register_driver


# ---------------------------------------------------------------------------
# deploy_host_scripts.ps1
# ---------------------------------------------------------------------------
def test_deploy_default_dry_run(deploy_scripts: str) -> None:
    assert re.search(r"\[switch\]\s*\$Execute", deploy_scripts)
    lowered = deploy_scripts.lower()
    assert "dry-run" in lowered or "dry run" in lowered


def test_deploy_requires_execute_to_copy(deploy_scripts: str) -> None:
    # Copy guarded behind the -Execute switch.
    assert "Copy-Item" in deploy_scripts
    assert "$DoIt" in deploy_scripts or "$Execute" in deploy_scripts


def test_deploy_backs_up_existing(deploy_scripts: str) -> None:
    lowered = deploy_scripts.lower()
    assert "back" in lowered  # backup/back up
    assert r"C:\AI_Runner\scripts" in deploy_scripts


def test_deploy_targets_all_host_scripts(deploy_scripts: str) -> None:
    for name in (
        "start_controller.ps1",
        "watchdog.ps1",
        "register_driver.ps1",
    ):
        assert name in deploy_scripts


# ── Codex P1 regressions (PR #111) ─────────────────────────────────────────
def test_watchdog_stops_before_start(watchdog: str) -> None:
    """Watchdog must Stop the hung IgnoreNew instance before demand-starting it (Codex P1).

    Uses the actionable code strings (with -TaskName) so a comment mentioning
    Start-ScheduledTask does not create a false ordering.
    """
    stop_i = watchdog.find("Stop-ScheduledTask -TaskName $DriverTaskName")
    start_i = watchdog.find("Start-ScheduledTask -TaskName $DriverTaskName")
    assert stop_i != -1, "watchdog must Stop the driver task in the relaunch path"
    assert start_i != -1, "watchdog must Start the driver task in the relaunch path"
    assert stop_i < start_i, "Stop-ScheduledTask must precede Start-ScheduledTask in relaunch"
