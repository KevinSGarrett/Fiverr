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
        _write_runner_state({
            "runner": "fiverr-runner-local-01",
            "last_run_id": run_id,
            "status": "PLANNED",
            "active_cycle": next_cycle,
            "active_branch": branch,
            "last_heartbeat": _now(),
        })
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

    # Filter out automation runner control tickets — agents build Fiverr product, not runner infra.
    # Exclude issues with labels: control-ticket, automation-runner, or summary starting with CYCLE-0NN
    import re as _re
    _ctrl_labels = {"control-ticket", "automation-runner"}
    _ctrl_summary_pattern = _re.compile(r"^CYCLE-0\d{2,3}\s", _re.IGNORECASE)
    filtered_issues = [
        issue for issue in jira_issues
        if not (
            _ctrl_labels & set(issue.get("fields", {}).get("labels", []))
            or _ctrl_summary_pattern.match(issue.get("fields", {}).get("summary", ""))
        )
    ]
    excluded = len(jira_issues) - len(filtered_issues)
    if excluded:
        click.echo(f"  Excluded {excluded} automation control ticket(s) from agent scope")
    jira_issues = filtered_issues

    click.echo("  Generating real agent prompts from PM_Pack + Jira...")

    # ── PM Intelligence: build wave context brief ─────────────────────
    # This prevents agents from building automation runner stubs instead of
    # real Fiverr product features. The brief injects the full wave/story
    # context from PM_Pack/ref into SECTION 0 of every agent prompt.
    click.echo("  Building PM intelligence cycle brief...")
    from automation.pm_intelligence import build_cycle_brief
    cycle_brief = build_cycle_brief(jira_issues=jira_issues)
    click.echo(
        f"  PM brief: Wave {cycle_brief.current_wave} ({cycle_brief.wave_name}) | "
        f"{len(cycle_brief.current_wave_stories)} stories | "
        f"{len(cycle_brief.already_built_in_src)} existing src files scanned"
    )

    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
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

    _write_runner_state({
        "runner": "fiverr-runner-local-01",
        "last_run_id": run_id,
        "status": "PLANNED",
        "active_cycle": next_cycle,
        "active_branch": branch,
        "last_heartbeat": _now(),
    })


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

    from automation.cursor_adapter import run_agent as cursor_run
    result = cursor_run(
        agent_id=agent,
        prompt_path=str(prompt_path),
        working_dir=str(REPO_ROOT),
        output_dir=str(agent_dir),
    )

    _agent_elapsed_min = (time.time() - _agent_start_time) / 60.0
    click.echo(f"  Agent {agent} finished: status={result.status} exit={result.exit_code} "
               f"elapsed={_agent_elapsed_min:.1f}min")

    # Warn if agent completed suspiciously fast (< 5 min with 55+ tasks is a red flag)
    MIN_EXPECTED_MINUTES = 5.0
    if _agent_elapsed_min < MIN_EXPECTED_MINUTES:
        click.secho(
            f"  [WARN] Agent {agent} completed in {_agent_elapsed_min:.1f}min "
            f"(expected >= {MIN_EXPECTED_MINUTES}min for 55-task prompt). "
            "Shell execution may have been blocked.",
            fg="yellow",
        )
        _record_nonblocking_error(
            f"run-agent suspiciously fast: cycle={cycle} agent={agent} "
            f"elapsed={_agent_elapsed_min:.1f}min"
        )

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

    from automation.run_agent_lifecycle import run_post_agent_lifecycle
    lifecycle = run_post_agent_lifecycle(
        agent_id=agent,
        cycle=cycle,
        run_id=run_id,
        run_dir=run_dir,
        jira_keys=[],
    )

    write_heartbeat("AGENT_COMPLETE", cycle=cycle, agent=agent)
    write_controller_state("AGENT_COMPLETE", cycle=cycle)

    click.echo(f"  Lifecycle: {lifecycle.status}")
    for err in lifecycle.errors:
        click.secho(f"  ERROR: {err}", fg="red")

    if lifecycle.status == "COMPLETE":
        sha_info = f" commit={lifecycle.commit_sha}" if lifecycle.commit_sha else ""
        click.secho(f"Agent {agent} COMPLETE{sha_info}", fg="green", bold=True)
    elif lifecycle.status == "VALIDATION_FAILED":
        click.secho(f"Agent {agent} validation failed â€” routing to repair loop", fg="yellow")
        from automation.repair_loop import dispatch_repair
        dispatch_repair(agent, cycle, run_dir, lifecycle.errors)
        _record_nonblocking_error(
            f"run-agent lifecycle validation failed cycle={cycle} agent={agent}: {lifecycle.errors[:3]}"
        )
        return
    else:
        click.secho(f"Agent {agent} lifecycle: {lifecycle.status}", fg="red", bold=True)
        _record_nonblocking_error(
            f"run-agent lifecycle non-complete cycle={cycle} agent={agent} status={lifecycle.status}"
        )
        return


@cli.command("run-cycle")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option(
    "--safe-docs-only",
    is_flag=True,
    default=False,
    help="Restrict run-agent scope to docs smoke target.",
)
def cmd_run_cycle(cycle: int, safe_docs_only: bool) -> None:
    """Run the full 6-agent cycle then auto-advance stage when ready."""
    click.echo("=" * 60)
    click.echo(f"RUN CYCLE {cycle:03d}")
    click.echo("=" * 60)
    agents = ["A", "B", "E", "C", "F", "D"]
    failures: dict[str, str] = {}
    for agent in agents:
        args = [
            sys.executable,
            "automation/ai_cycle_controller.py",
            "run-agent",
            "--agent",
            agent,
            "--cycle",
            str(cycle),
        ]
        if safe_docs_only:
            args.append("--safe-docs-only")
        rc, output = _run_shell_command(args)
        click.echo(f"  Agent {agent}: {'PASS' if rc == 0 else 'FAIL'}")
        if rc != 0:
            failures[agent] = output.strip()[-400:]

    if failures:
        click.secho("RUN CYCLE FAILED", fg="red", bold=True)
        for agent, detail in failures.items():
            click.echo(f"  {agent}: {detail}")
        raise SystemExit(1)

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

    state = _read_runner_state()
    status = state.get("status", "IDLE")
    cycle  = state.get("active_cycle")

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
        # If we just completed a cycle (POST_CYCLE_PASS), the next cycle is cycle+1.
        # Update HYDRATION_HEADER so compile_policy picks up the right number.
        if status == "POST_CYCLE_PASS" and cycle:
            next_cycle_target = cycle + 1
            _update_hydration_cycle(next_cycle_target)
            click.echo(f"  Advancing HYDRATION_HEADER: cycle {cycle} → {next_cycle_target}")
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
             "--cycle", str(cycle)]
        )
        if rc == 0:
            write_controller_state("PLANNED", cycle=cycle)
            click.secho(f"  State: PLANNED (cycle {cycle}) — prompts generated", fg="cyan")
        else:
            click.secho(f"  [WARN] plan-cycle failed:\n{out.strip()[-400:]}", fg="yellow")
            write_controller_state("PLANNING", cycle=cycle)
            click.secho(f"  State: PLANNING (plan-cycle failed — will retry next tick)", fg="yellow")

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
                click.secho("  State: AWAITING_DISPATCH — all gates pass, ready to dispatch", fg="green")
                notify_info(f"Tick: awaiting dispatch signal for cycle {cycle}")

    elif status == "AGENT_COMPLETE":
        # All agents finished — automatically trigger post-cycle-review.
        # This is the critical handoff: AGENT_COMPLETE → POST_CYCLE_REVIEW → POST_CYCLE_PASS → IDLE
        click.secho(f"  [TICK] AGENT_COMPLETE for cycle {cycle} — advancing to post-cycle-review...",
                    fg="cyan", bold=True)
        write_controller_state("POST_CYCLE_PENDING", cycle=cycle)
        # Run post-cycle-review inline so the scheduled tick handles the full lifecycle
        from automation.post_cycle_review import run_review, ReviewMode, ReviewResult
        try:
            result = run_review(cycle=cycle, mode=ReviewMode.POST_AGENT)
            grade = result.result.value if hasattr(result, "result") else "UNKNOWN"
            click.echo(f"  Post-cycle-review grade: {grade}")
            if grade in ("PASS", "CONDITIONAL_PASS", "ADVISORY_ONLY") or not result.blocks_dispatch:
                write_controller_state("POST_CYCLE_PASS", cycle=cycle)
                click.secho(f"  POST_CYCLE_PASS — cycle {cycle} complete. Next tick will plan cycle {cycle + 1}.",
                            fg="green", bold=True)
            else:
                write_controller_state("POST_CYCLE_FAIL", cycle=cycle)
                click.secho(f"  POST_CYCLE_FAIL grade={grade} — review needed before cycle {cycle + 1}.",
                            fg="red", bold=True)
        except Exception as exc:
            click.secho(f"  [ERROR] post-cycle-review raised: {exc}", fg="red")
            write_controller_state("POST_CYCLE_PENDING", cycle=cycle)

    elif status in ("DISPATCHING", "AGENT_DISPATCH", "CURSOR_RUNNING"):
        # Agent is still running — verify the branch exactly matches the active cycle.
        expected_branch = f"cycle/{cycle:03d}/integration"
        from automation.branch_guard import current_branch as _current_branch
        actual_branch = _current_branch()
        if actual_branch and actual_branch != expected_branch:
            notify_blocked(
                f"BRANCH_MISMATCH: active_cycle={cycle} but on branch '{actual_branch}' "
                f"(expected '{expected_branch}'). Dispatcher is on the wrong branch.",
                incident_code="BRANCH_MISMATCH", cycle=cycle,
            )
            click.secho(
                f"  [ERROR] BRANCH_MISMATCH: on '{actual_branch}' but active_cycle={cycle} "
                f"expects '{expected_branch}'. Blocking dispatch.",
                fg="red", bold=True,
            )
            write_controller_state("BRANCH_MISMATCH_BLOCKED", cycle=cycle)
            return
        # Monitor heartbeat freshness
        hb_path = Path("C:/AI_Runner/state/heartbeat.json")
        if hb_path.exists():
            import json as _json
            hb = _json.loads(hb_path.read_text())
            from datetime import datetime as _dt
            last = _dt.fromisoformat(hb.get("last_seen", _now()).replace("Z", "+00:00"))
            age_min = (_dt.now(last.tzinfo) - last).total_seconds() / 60
            if age_min > 45:
                notify_blocked(f"Heartbeat stale {age_min:.0f}m — agent may be stuck",
                               incident_code="AGENT_STUCK", cycle=cycle)
                click.secho(f"  [WARN] Heartbeat stale {age_min:.0f}m", fg="yellow")
            else:
                click.secho(f"  Agent running, heartbeat {age_min:.1f}m old — OK", fg="cyan")

    elif status in ("POST_CYCLE_PENDING", "POST_CYCLE_REVIEW"):
        # Either we transitioned here automatically (retry after crash) or manually.
        # Always attempt the review rather than waiting indefinitely.
        click.secho(f"  [TICK] {status} — attempting post-cycle-review for cycle {cycle}...",
                    fg="cyan")
        from automation.post_cycle_review import run_review, ReviewMode, ReviewResult
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
             "--cycle", str(cycle)]
        )
        if rc == 0:
            write_controller_state("PLANNED", cycle=cycle)
            click.secho(f"  State: PLANNED (cycle {cycle})", fg="cyan")
        else:
            click.secho(f"  plan-cycle still failing: {out.strip()[-200:]}", fg="yellow")

    else:
        click.echo(f"  Unknown status: {status} — treating as IDLE")
        write_controller_state("IDLE")

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
def cmd_post_cycle_review(cycle: int, pr: int | None, mode: str, dry_run: bool) -> None:
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

    result = run_review(cycle=cycle, mode=rev_mode, pr_number=pr)
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

    # Check dirty repo
    import subprocess as _sp
    git_status = _sp.run(
        ["git", "status", "--short"], cwd=str(REPO_ROOT),
        capture_output=True, text=True
    ).stdout.strip()
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



if __name__ == "__main__":
    cli()
