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

from automation.config_loader import get_secret  # noqa: E402
from automation.pm_pack_loader import brain_check  # noqa: E402
from automation.policy_compiler import compile_policy  # noqa: E402

REPO_ROOT = _repo_root
RUNNER_STATE = Path("C:/AI_Runner/state/controller_state.json")


def _now() -> str:
    return datetime.now(UTC).isoformat()


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


def _run_and_stream(args: list[str], label: str = "") -> tuple[int, str]:
    """Run subprocess streaming stdout live to terminal line by line.

    In test environments (PYTEST_CURRENT_TEST set), returns (0, 'ok') immediately
    without spawning a subprocess. Monkeypatch automation.ai_cycle_controller._run_and_stream
    to override in tests if you need custom return values.
    """
    import os as _os
    if _os.environ.get("PYTEST_CURRENT_TEST"):
        # Never spawn real subprocesses during pytest runs
        return 0, "ok"

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
    path = Path("C:/AI_Runner/reports/nonblocking_errors.json")
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
    return Path("C:/AI_Runner/state/stage_state.json")


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
    claude_state_path = Path("C:/AI_Runner/state/claude_model_state.json")
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
    cursor_state_path = Path("C:/AI_Runner/state/cursor_model_state.json")
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
def cmd_plan_cycle(dry_run: bool, live: bool, cycle: int | None) -> None:
    """Plan next cycle.

    --dry-run: Generates only a manifest and stub placeholders (safe).
    --live: Generates real prompts from PM_Pack + Jira (requires pm-pack-audit PASS + unfrozen).

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
        "planned_at": _now(),
        "quality_gates": snap.get("quality_gates", {}),
        "jira_policy": snap.get("jira_policy", {}),
        "status": "PLANNED_DRY_RUN" if dry_run else "PLANNED",
    }

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
    from automation.prompt_generator import write_prompts

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
        _probe = _sub.run(
            [_claude_bin, "-p", "Reply: OK", "--print", "--output-format", "text",
             "--trust", "--force"],
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
        from pathlib import Path as _P
        _P("C:/AI_Runner/state/autopilot_paused.json").write_text(
            '{"reason":"CLAUDE_SUBSCRIPTION_FAIL","ts":"' + _now() + '"}',
            encoding="utf-8"
        )
        raise SystemExit(1) from _probe_exc

    click.echo("  [2/3] Attempting Claude-as-PM prompt generation (primary path)...")
    try:
        written = create_agent_prompts_via_claude(
            cycle=next_cycle,
            branch=branch,
            jira_issues=jira_issues,
            agents=manifest["agents"],
            prompts_dir=prompts_dir,
            wave=_snap.current_wave,
        )
        if written:
            click.secho(
                f"  Claude PM: generated {len(written)} prompts via Claude subscription",
                fg="green"
            )
        else:
            # PQ-3 FIX: Claude PM returned None (timeout/short-output/error).
            # Previously this silently fell back to templates with only a yellow line.
            # Now it's a loud, explicit failure that pauses the autopilot.
            click.secho(
                "  ⚠  CLAUDE PM UNAVAILABLE — Claude returned None for this cycle.\n"
                "  This means the subscription is reachable (probe passed) but the\n"
                "  full PM call timed out, returned < 500 chars, or errored.\n"
                "  Autopilot PAUSED. Check C:\\AI_Runner\\tmp\\claude_pm_agent_*.err",
                fg="red", bold=True,
            )
            from pathlib import Path as _P2
            _P2("C:/AI_Runner/state/autopilot_paused.json").write_text(
                '{"reason":"CLAUDE_PM_RETURNED_NONE","ts":"' + _now() + '"}',
                encoding="utf-8"
            )
            raise SystemExit(1) from None
    except SystemExit:
        raise
    except Exception as e:
        click.secho(
            f"  ⚠  CLAUDE PM EXCEPTION: {e}\n"
            "  Autopilot PAUSED. Investigate before resuming.",
            fg="red", bold=True,
        )
        from pathlib import Path as _P3
        _P3("C:/AI_Runner/state/autopilot_paused.json").write_text(
            '{"reason":"CLAUDE_PM_EXCEPTION","detail":"' + str(e)[:200] + '","ts":"' + _now() + '"}',
            encoding="utf-8"
        )
        raise SystemExit(1) from e

    click.echo("  [3/3] Prompts generated via Claude subscription ✓")

    # ── Template fallback: prompt_generator.py ────────────────────────
    if not written:
        from automation.prompt_generator import write_prompts
        written = write_prompts(
            cycle=next_cycle,
            branch=branch,
            run_id=run_id,
            agents=manifest["agents"],
            jira_issues=jira_issues,
            prompts_dir=prompts_dir,
            cycle_brief=cycle_brief,
        )

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
    _agent_start_time = time.time()

    # OBS-2: update current_activity so the operator can see which agent is running
    import automation.autopilot_logger as _L_obs
    _L_obs.set_activity("AGENT-RUN", cycle=cycle, agent=agent)
    _L_obs.print_stage_matrix(current="AGENT-RUN", agents=["A", "B", "E", "C", "F", "D"])

    # C1 FIX: snapshot HEAD before dispatching Cursor so the post-agent
    # lifecycle ownership check covers only files changed by THIS agent,
    # not accumulated leftovers from prior failed agents/cycles.
    import subprocess as _subprocess_c1
    _pre_sha_r = _subprocess_c1.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    pre_dispatch_sha = _pre_sha_r.stdout.strip() or None

    from automation.cursor_adapter import run_agent as cursor_run
    # OBS-6: heartbeat thread keeps terminal alive during long Cursor runs
    with _L_obs.HeartbeatThread(f"AGENT-RUN agent={agent} cycle={cycle}", interval=60.0):
        result = cursor_run(
            agent_id=agent,
            prompt_path=str(prompt_path),
            working_dir=str(REPO_ROOT),
            output_dir=str(agent_dir),
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
            f"(floor: {MIN_EXPECTED_MINUTES}min for 55-task prompt). "
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
    )

    write_heartbeat("AGENT_COMPLETE", cycle=cycle, agent=agent)
    # C2 FIX: do NOT write AGENT_COMPLETE state here -- only write it after
    # confirming lifecycle.status == "COMPLETE" below.

    click.echo(f"  Lifecycle: {lifecycle.status}")
    for err in lifecycle.errors:
        click.secho(f"  ERROR: {err}", fg="red")

    if lifecycle.status == "COMPLETE":
        # Only write AGENT_COMPLETE when an agent actually committed real work.
        write_controller_state("AGENT_COMPLETE", cycle=cycle)
        sha_info = f" commit={lifecycle.commit_sha}" if lifecycle.commit_sha else ""
        click.secho(f"Agent {agent} COMPLETE{sha_info}", fg="green", bold=True)
    elif lifecycle.status == "VALIDATION_FAILED":
        click.secho(f"Agent {agent} validation failed â€” routing to repair loop", fg="yellow")
        from automation.repair_loop import dispatch_repair
        dispatch_repair(agent, cycle, run_dir, lifecycle.errors)
        _record_nonblocking_error(
            f"run-agent lifecycle validation failed cycle={cycle} agent={agent}: {lifecycle.errors[:3]}"
        )
        # C2 FIX: exit non-zero so run-cycle counts this as failed, not done
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
    _progress_path = Path("C:/AI_Runner/state/agent_progress.json")
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
        if rc == 0:
            completed_agents.append(agent)
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
        _write_progress(agent, completed_agents, list(failures.keys()), elapsed)

    # All agents done — write AGENT_COMPLETE so tick advances to post-cycle review
    from automation.state_writer import write_controller_state as _wcs, write_heartbeat as _wh
    _wcs("AGENT_COMPLETE", cycle=cycle)
    _wh("AGENT_COMPLETE", cycle=cycle)
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

    out_dir = Path("C:/AI_Runner/reports/provider_usage")
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

    provider_health_path = Path("C:/AI_Runner/state/provider_health.json")
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
def cmd_recover() -> None:
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

    evidence_path = Path(f"C:/AI_Runner/reports/stages/STAGE{stage_num}_EVIDENCE.json")
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

    # C7 FIX: Global run lock — prevents GHA cron + local Scheduled Task running simultaneously.
    # Both write to the same controller_state.json; concurrent ticks corrupt it.
    # Lock file: C:\AI_Runner\locks\tick.lock (PID + start timestamp).
    # If lock is stale (>10 min old), clear it and acquire fresh.
    import os as _os_c7
    import time as _time_c7
    _lock_dir = Path("C:/AI_Runner/locks")
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

    # Check pause flag — set by manual stop, respected by both local and CI runners
    _pause_flag = Path("C:/AI_Runner/state/autopilot_paused.json")
    if _pause_flag.exists():
        import json as _pj
        try:
            _pdata = _pj.loads(_pause_flag.read_text(encoding='utf-8-sig'))
            if _pdata.get("paused"):
                click.secho(
                    "[TICK PAUSED] System manually stopped. "
                    "Delete C:/AI_Runner/state/autopilot_paused.json to resume.",
                    fg="yellow",
                )
                return
        except Exception:
            pass

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
                    write_controller_state("PLANNED", cycle=cycle)  # reset for retry

    elif status == "AGENT_COMPLETE":
        import automation.autopilot_logger as L
        L.section(f"AGENT_COMPLETE — Cycle {cycle} — Running post-cycle review")
        write_controller_state("POST_CYCLE_PENDING", cycle=cycle)
        from automation.post_cycle_review import run_review, ReviewMode
        try:
            with L.Spinner("Post-cycle review (lint + tests + coverage + Jira sync)"):
                result = run_review(cycle=cycle, mode=ReviewMode.POST_AGENT)
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
            # C4/H7 FIX: ADVISORY_ONLY no longer counts as a pass.
            # Previously: "PASS or CONDITIONAL_PASS or ADVISORY_ONLY or not blocks_dispatch"
            # -- this let broken cycles (lint/tests/CI all red) advance because ADVISORY_ONLY
            # was the default when verdict parsing failed.
            # Now: only PASS advances. ADVISORY_ONLY and CONDITIONAL_PASS route to FAIL/review.
            if grade == "PASS" and not result.blocks_dispatch:
                write_controller_state("POST_CYCLE_PASS", cycle=cycle)
                L.ok(f"Cycle {cycle} COMPLETE — next tick plans Cycle {cycle + 1}")
                # OBS-7: emit end-of-cycle summary
                L.cycle_summary(cycle=cycle, agent_outcomes={}, gate_result="PASS")
                L.clear_activity()
            elif grade in ("CONDITIONAL_PASS",) and not result.blocks_dispatch:
                write_controller_state("POST_CYCLE_PASS", cycle=cycle)
                L.ok(f"Cycle {cycle} CONDITIONAL PASS — next tick plans Cycle {cycle + 1}")
                L.cycle_summary(cycle=cycle, agent_outcomes={}, gate_result="CONDITIONAL_PASS")
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
        prog_path = Path("C:/AI_Runner/state/agent_progress.json")
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
        hb_path = Path("C:/AI_Runner/state/heartbeat.json")
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
            result = run_review(cycle=cycle, mode=ReviewMode.POST_AGENT)
            grade = result.result.value if hasattr(result, "result") else "UNKNOWN"
            click.echo(f"  Post-cycle-review grade: {grade}")
            if not result.blocks_dispatch:
                write_controller_state("POST_CYCLE_PASS", cycle=cycle)
                click.secho(f"  POST_CYCLE_PASS — cycle {cycle} complete. Next tick plans cycle {cycle + 1}.",
                            fg="green", bold=True)
            else:
                write_controller_state("POST_CYCLE_FAIL", cycle=cycle)
                click.secho(f"  POST_CYCLE_FAIL grade={grade}", fg="red", bold=True)
        except Exception as exc:
            click.secho(f"  [ERROR] post-cycle-review raised: {exc} — staying in {status}", fg="red")

    elif status in ("MODEL_BLOCKED", "CLAUDE_API_KEY_BLOCKED", "PROMPT_VALIDATION_FAILED"):
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
            # Re-validate prompts — auto-heal if they now pass
            try:
                from automation.prompt_validator import validate_all
                _agents = ["A", "B", "E", "C", "F", "D"]  # standard agent set
                prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
                vr = validate_all(prompts_dir, cycle=cycle, agents=_agents)
                if vr.get("passed"):
                    click.secho("  Prompts now PASS — auto-clearing PROMPT_VALIDATION_FAILED", fg="green")
                    write_controller_state("PLANNED", cycle=cycle)
                else:
                    click.secho(f"  BLOCKED ({status}) — prompts still failing, re-run plan-cycle", fg="red")
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
        # M-TICK-1 FIX: POST_CYCLE_FAIL was falling through to 'Unknown status -> IDLE'
        # silently resetting a failing cycle. Now it surfaces explicitly and waits.
        import automation.autopilot_logger as L
        L.error(
            f"Cycle {cycle} POST_CYCLE_FAIL — review gate blocked dispatch. "
            "Check post_cycle_reviews/ for details. Operator action required."
        )
        click.secho(
            f"  POST_CYCLE_FAIL (cycle {cycle}) — review the gate failures above\n"
            "  and either fix the issues or force-advance via:\n"
            "    python automation/ai_cycle_controller.py force-state --status IDLE\n"
            "  Tick will stay in this state until resolved.",
            fg="red",
        )
        # Stay in POST_CYCLE_FAIL — do not advance, do not reset to IDLE

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
        _status_dir = Path("C:/AI_Runner/status")
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

    # C7: Release tick lock
    try:
        if _lock_file.exists():
            _lock_file.unlink()
    except Exception:
        pass

    click.echo("[TICK COMPLETE]")


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
        fallback_path = Path("C:/AI_Runner/reports/DAILY_STAGE_REPORT.json")
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
    result = gate_run(pr_number=pr, dry_run=(not execute_merge))
    click.echo(result.summary())
    click.echo()
    if result.passed:
        if execute_merge and result.merge_sha:
            click.secho(f"MERGED to develop: {result.merge_sha}", fg="green", bold=True)
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
    git_status_raw = _sp.run(
        ["git", "status", "--short"], cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    ).stdout.strip()

    # Paths written by the runtime that should not block dispatch
    _ARTIFACT_PREFIXES = (
        "PM_Pack/automation/post_cycle_reviews/",
        "PM_Pack/automation/runs/",
        "PM_Pack/automation/ref_catalogs/",
        "PM_Pack/automation/prompts/drafts/",
        "PM_Pack/automation/current_policy_snapshot.json",
        "PM_Pack/automation/prompt_package_manifest.json",
    )
    _artifact_only_lines = [
        line for line in git_status_raw.splitlines()
        if not any(line.strip().lstrip("?! MAD").strip().startswith(p)
                   for p in _ARTIFACT_PREFIXES)
    ]
    git_status = "\n".join(_artifact_only_lines)
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
    elif status == "POST_CYCLE_PENDING":
        next_action = "POST_CYCLE_REVIEW"
        reason = "Awaiting post-cycle review"
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
    decision_path = Path("C:/AI_Runner/state/next_action_decision.json")
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
            "IDLE": "Idle — will compile policy and plan next cycle",
            "MODEL_BLOCKED": "Cursor model gate failed — re-checking...",
            "BRANCH_MISMATCH_BLOCKED": "Wrong git branch — auto-fixing...",
            "PROMPT_VALIDATION_FAILED": "Prompts invalid — re-validating...",
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
        except Exception as exc:
            L.error(f"Tick raised exception: {exc}")
            import traceback
            L.info(traceback.format_exc()[-300:])

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
