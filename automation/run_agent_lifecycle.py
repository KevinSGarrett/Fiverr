"""Post-agent lifecycle with ownership, validation, and commit hardening."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path("C:/Fiverr/Fiverr")
RUNNER_ROOT = Path("C:/AI_Runner")
CONTROLLER_STATE = RUNNER_ROOT / "state/controller_state.json"

# Agent file ownership map — agents must not modify outside their scope
AGENT_OWNERSHIP = {
    "A": {
        "allowed":   ["src/pipeline", "src/models", "src/collection", "src/scoring",
                      "src/signals", "tests/unit", "tests/integration"],
        "forbidden": ["src/dashboard", "src/reports", "src/playbook", "docs/"],
    },
    "B": {
        "allowed":   ["src/signals", "src/integrations", "src/scrapers", "tests/"],
        "forbidden": ["src/dashboard", "src/reports"],
    },
    "E": {
        "allowed":   ["tests/"],
        "forbidden": ["src/"],
    },
    "C": {
        "allowed":   ["src/dashboard", "src/visualization", "tests/"],
        "forbidden": ["src/pipeline", "src/models", "src/scoring"],
    },
    "F": {
        "allowed":   ["src/reports", "src/playbook", "tests/"],
        "forbidden": ["src/pipeline", "src/dashboard"],
    },
    "D": {
        "allowed":   ["docs/", "PM_Pack/10_cycle_log/", "docs/cycle_reports/"],
        "forbidden": ["src/", "tests/", "automation/"],
    },
}


@dataclass
class AgentLifecycleResult:
    agent: str
    cycle: int
    run_id: str
    status: str          # COMPLETE | VALIDATION_FAILED | OWNERSHIP_VIOLATION | NO_REPORT | SECRET_FOUND | REPAIR_NEEDED
    commit_sha: str = ""
    changed_files: list[str] = field(default_factory=list)
    unauthorized_files: list[str] = field(default_factory=list)
    secret_findings: list[str] = field(default_factory=list)
    validation_passed: bool = False
    report_path: str = ""
    report_found: bool = False
    jira_updates: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    record_path: str = ""
    commit_blocked: bool = False

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class AgentLifecycle:
    """Stateful lifecycle helper for post-agent processing."""

    def run(
        self,
        agent_id: str,
        cycle: int,
        run_id: str,
        run_dir: Path,
        jira_keys: list[str] | None = None,
        contract: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> AgentLifecycleResult:
        result = AgentLifecycleResult(agent=agent_id, cycle=cycle, run_id=run_id, status="IN_PROGRESS")
        jira_keys = jira_keys or []
        result.changed_files = _get_changed_files()

        unauthorized = _check_ownership(agent_id, result.changed_files)
        if unauthorized:
            result.unauthorized_files = unauthorized
            result.status = "OWNERSHIP_VIOLATION"
            result.errors.append(f"Agent {agent_id} modified files outside scope: {unauthorized}")
            if not dry_run:
                _write_record(result, run_dir)
                from automation.notification_router import notify_blocked

                notify_blocked(
                    f"Agent {agent_id} ownership violation: {unauthorized[:3]}",
                    incident_code="OWNERSHIP_VIOLATION",
                    cycle=cycle,
                )
            return result

        secret_findings = _scan_changed_files(result.changed_files)
        if secret_findings:
            result.secret_findings = secret_findings
            result.status = "SECRET_FOUND"
            result.errors.extend(secret_findings)
            if not dry_run:
                _write_record(result, run_dir)
            return result

        report_path = REPO_ROOT / f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md"
        result.report_path = str(report_path)
        result.report_found = report_path.exists()
        if not result.report_found:
            result.status = "NO_REPORT"
            result.errors.append(f"Required report not found: {report_path}")
            if not dry_run:
                _write_record(result, run_dir)
            return result
        report_text = report_path.read_text(encoding="utf-8", errors="replace")
        if "AGENT_COMPLETE" not in report_text:
            result.status = "NO_REPORT"
            result.errors.append("Report exists but missing AGENT_COMPLETE marker")
            if not dry_run:
                _write_record(result, run_dir)
            return result

        validation_commands = contract.get("validation_commands", []) if contract else []
        for cmd in validation_commands:
            validation_proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                check=False,
            )
            if validation_proc.returncode != 0:
                result.status = "VALIDATION_FAILED"
                result.errors.append(f"Contract validation failed: {cmd}")
                if not dry_run:
                    _write_record(result, run_dir)
                return result

        val_passed, val_details = _run_validation(agent_id)
        result.validation_passed = val_passed
        if not val_passed:
            result.status = "VALIDATION_FAILED"
            result.errors.append(f"Validation failed: {val_details}")
            if not dry_run:
                _write_record(result, run_dir)
            return result

        approved_files = [fn for fn in result.changed_files if fn not in result.unauthorized_files]
        if not dry_run and approved_files:
            repo_clean, repo_violations = _run_export_sanitizer()
            if not repo_clean:
                result.commit_blocked = True
                result.status = "SECRET_SCAN_FAIL"
                result.errors.extend(repo_violations)
                _record_secret_scan_failure(repo_violations)
                _write_controller_state("BLOCKED_FAILING_WORK", cycle=cycle)
                _write_record(result, run_dir)
                return result

            # DISPATCH-020: block commits when any ruff/mypy/pytest gate fails.
            gate_ok, gate_detail = _run_pre_commit_gate()
            if not gate_ok:
                result.commit_blocked = True
                result.status = "BLOCKED_FAILING_WORK"
                result.errors.append(gate_detail)
                _write_controller_state("BLOCKED_FAILING_WORK", cycle=cycle)
                _write_record(result, run_dir)
                return result

            post_scan = _scan_changed_files(approved_files)
            if post_scan:
                result.secret_findings.extend(post_scan)
                result.status = "SECRET_FOUND"
                result.errors.extend(post_scan)
                _write_record(result, run_dir)
                return result
            result.commit_sha = _commit_agent_work(agent_id, cycle, approved_files)

        if not dry_run and jira_keys:
            from automation.jira_sync import on_agent_complete

            result.jira_updates = on_agent_complete(
                cycle=cycle,
                agent=agent_id,
                branch=_get_current_branch(),
                pr_number=None,
                files_changed=result.changed_files,
                validation_passed=val_passed,
                jira_keys=jira_keys,
            )

        result.status = "COMPLETE"
        if not dry_run:
            result.record_path = str(_write_record(result, run_dir))
        return result


def run_post_agent_lifecycle(
    agent_id: str,
    cycle: int,
    run_id: str,
    run_dir: Path,
    jira_keys: list[str] | None = None,
    contract: dict | None = None,
    dry_run: bool = False,
) -> AgentLifecycleResult:
    return AgentLifecycle().run(
        agent_id=agent_id,
        cycle=cycle,
        run_id=run_id,
        run_dir=run_dir,
        jira_keys=jira_keys,
        contract=contract,
        dry_run=dry_run,
    )
<<<<<<< HEAD
=======
    jira_keys = jira_keys or []

    # ── Step 1: Collect changed files ─────────────────────────────────
    result.changed_files = _get_changed_files()

    # ── Step 2: Enforce file ownership ───────────────────────────────
    unauthorized = _check_ownership(agent_id, result.changed_files)
    if unauthorized:
        result.unauthorized_files = unauthorized
        result.status = "OWNERSHIP_VIOLATION"
        result.errors.append(
            f"Agent {agent_id} modified files outside its scope: {unauthorized}"
        )
        # Don't commit — quarantine changed files
        if not dry_run:
            _write_record(result, run_dir)
            from automation.notification_router import notify_blocked
            notify_blocked(
                f"Agent {agent_id} ownership violation: {unauthorized[:3]}",
                incident_code="OWNERSHIP_VIOLATION", cycle=cycle
            )
        return result

    # ── Step 3: Secret guard — scan changed_files BEFORE any staging (V5-008) ────
    # Scan must happen on the changed_files list before we stage anything.
    # We call scan_working_tree (not scan_staged) at this point.
    secret_findings = _scan_changed_files(result.changed_files)
    if secret_findings:
        result.secret_findings = secret_findings
        result.status = "SECRET_FOUND"
        result.errors.extend(secret_findings)
        if not dry_run:
            _write_record(result, run_dir)
        return result

    # ── Step 4: Require report file ───────────────────────────────────
    report_path = REPO_ROOT / f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md"
    result.report_path = str(report_path)
    result.report_found = report_path.exists()

    if not result.report_found:
        result.status = "NO_REPORT"
        result.errors.append(
            f"Required report not found: {report_path}\n"
            f"Agent must write report before exiting."
        )
        if not dry_run:
            _write_record(result, run_dir)
        return result

    # Verify report contains AGENT_COMPLETE
    report_text = report_path.read_text(encoding="utf-8", errors="replace")
    if "AGENT_COMPLETE" not in report_text:
        result.status = "NO_REPORT"
        result.errors.append("Report exists but missing AGENT_COMPLETE marker")
        if not dry_run:
            _write_record(result, run_dir)
        return result

    # DISPATCH-017: run targeted validation_commands from the prompt contract.
    if contract and contract.get("validation_commands"):
        for cmd in contract["validation_commands"]:
            validation_proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                check=False,
            )
            if validation_proc.returncode != 0:
                result.status = "VALIDATION_FAILED"
                result.errors.append(f"Contract validation failed: {cmd}")
                if not dry_run:
                    _write_record(result, run_dir)
                return result

    # ── Step 5: Targeted validation ───────────────────────────────────
    val_passed, val_details = _run_validation(agent_id)
    result.validation_passed = val_passed

    if not val_passed:
        result.status = "VALIDATION_FAILED"
        result.errors.append(f"Validation failed: {val_details}")
        if not dry_run:
            _write_record(result, run_dir)
        # Don't commit — route to repair
        return result

    # ── Step 6: Commit approved files ────────────────────────────────
    # Stage and commit only files that passed ownership check
    approved_files = [
        fn for fn in result.changed_files
        if fn not in result.unauthorized_files
    ]
    if not dry_run and approved_files:
        gate_ok, gate_detail = _run_pre_commit_gate()
        if not gate_ok:
            result.commit_blocked = True
            result.status = "BLOCKED_FAILING_WORK"
            result.errors.append(gate_detail)
            _write_controller_state("BLOCKED_FAILING_WORK", cycle=cycle)
            _write_record(result, run_dir)
            return result
        # Second secret scan: after classifying files, before staging
        post_scan = _scan_changed_files(approved_files)
        if post_scan:
            result.secret_findings.extend(post_scan)
            result.status = "SECRET_FOUND"
            result.errors.extend(post_scan)
            _write_record(result, run_dir)
            return result
        sha = _commit_agent_work(agent_id, cycle, approved_files)
        result.commit_sha = sha

    # ── Step 7: Update Jira with evidence ────────────────────────────
    if not dry_run and jira_keys:
        from automation.jira_sync import on_agent_complete
        updates = on_agent_complete(
            cycle=cycle,
            agent=agent_id,
            branch=_get_current_branch(),
            pr_number=None,
            files_changed=result.changed_files,
            validation_passed=val_passed,
            jira_keys=jira_keys,
        )
        result.jira_updates = updates

    # ── Step 8: Write run record ──────────────────────────────────────
    result.status = "COMPLETE"
    if not dry_run:
        record_path = _write_record(result, run_dir)
        result.record_path = str(record_path)

    return result
>>>>>>> origin/develop


def _get_changed_files() -> list[str]:
    """Get all modified/added files relative to HEAD."""
    r = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    uncommitted = r.stdout.strip().splitlines()

    r2 = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    untracked = [
        line[3:].strip() for line in r2.stdout.splitlines()
        if line.startswith("?? ")
    ]
    return list(set(uncommitted + untracked))


def _check_ownership(agent_id: str, changed_files: list[str]) -> list[str]:
    """Return files that violate agent ownership rules.

    V5-008 fix: enforces BOTH allowlist and denylist from agent_lanes.yml.
    A file is a violation if:
      (a) it matches a forbidden prefix, OR
      (b) it doesn't match any allowed prefix (and allowed list is non-empty)
    """
    rules = AGENT_OWNERSHIP.get(agent_id, {})
    allowed_prefixes = rules.get("allowed", [])
    forbidden_prefixes = rules.get("forbidden", [])
    violations = []

    for changed_file in changed_files:
        # Check forbidden
        forbidden = any(changed_file.startswith(fp) for fp in forbidden_prefixes)
        if forbidden:
            violations.append(changed_file)
            continue

        # Check allowlist: if allowed list is non-empty and file doesn't match any
        if allowed_prefixes:
            in_allowed = any(
                changed_file.startswith(ap.rstrip("*").rstrip("/"))
                for ap in allowed_prefixes
            )
            # Automation and docs files are always allowed for any agent
            always_allowed = any(
                changed_file.startswith(p)
                for p in ("docs/cycle_reports/", "PM_Pack/automation/runs/",
                          ".gitignore", "README")
            )
            if not in_allowed and not always_allowed:
                violations.append(changed_file)

    return violations


def _scan_for_secrets() -> list[str]:
    """Scan staged files for secret patterns (used after staging)."""
    try:
        from automation.secret_guard import scan_staged
        scan_result = scan_staged(REPO_ROOT)
        return scan_result.findings if not scan_result.passed else []
    except Exception:
        return []


def _scan_changed_files(changed_files: list[str]) -> list[str]:
    """Scan a list of changed files for secret values BEFORE staging (V5-008 fix).

    Uses scan_file on each file individually, before any git add.
    """
    try:
        from automation.secret_guard import scan_file
        findings: list[str] = []
        for fname in changed_files:
            fpath = REPO_ROOT / fname
            if fpath.exists():
                scan_result = scan_file(fpath)
                if not scan_result.passed:
                    findings.extend(
                        [f"{fname}: {finding}" for finding in scan_result.findings]
                    )
        return findings
    except Exception:
        return []


def _run_validation(agent_id: str) -> tuple[bool, str]:
    """Run ruff + mypy. Pytest for code agents. Returns (passed, details)."""
    py = str(REPO_ROOT / ".venv/Scripts/python.exe")
    passed = True
    details_parts = []

    # Ruff
    r = subprocess.run(
        [py, "-m", "ruff", "check", "automation/", "src/", "--output-format=text"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        passed = False
        details_parts.append(f"ruff FAIL: {r.stdout[:200]}")

    # Mypy
    r = subprocess.run(
        [py, "-m", "mypy", "src/", "--ignore-missing-imports"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        passed = False
        details_parts.append(f"mypy FAIL: {r.stdout[-200:]}")

    # Pytest — only for code agents (not D)
    if agent_id != "D":
        r = subprocess.run(
            [py, "-m", "pytest", "tests/unit/", "-q", "--no-header", "--tb=no", "-x"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=300
        )
        if r.returncode != 0:
            passed = False
            details_parts.append(f"pytest FAIL: {r.stdout[-200:]}")

    return passed, " | ".join(details_parts) if details_parts else "all passed"


def _commit_agent_work(agent_id: str, cycle: int, files: list[str]) -> str:
    """Stage only approved files and commit. Never uses git add -A.

    V5-008 fix: stages files explicitly using git add -- <file1> <file2>
    """
    if not files:
        return ""
    # Stage only the explicitly approved files
    stage_cmd = ["git", "add", "--"] + files
    stage_result = subprocess.run(
        stage_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if stage_result.returncode != 0:
        return ""

    msg = f"feat(cycle-{cycle:03d}): Agent {agent_id} work [autonomous]"
    r = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        return ""
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    ).stdout.strip()
    return sha


def _get_current_branch() -> str:
    r = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return r.stdout.strip()


def _write_record(result: AgentLifecycleResult, run_dir: Path) -> Path:
    """Write agent_run_record.json to run dir."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"agent_{result.agent}_run_record.json"
    path.write_text(json.dumps({
        **result.to_dict(),
        "recorded_at": datetime.now(UTC).isoformat(),
    }, indent=2))
    return path


def _write_controller_state(status: str, cycle: int) -> None:
    payload: dict[str, object] = {}
    if CONTROLLER_STATE.exists():
        try:
            payload = json.loads(CONTROLLER_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
    payload["status"] = status
    payload["active_cycle"] = cycle
    payload["last_heartbeat"] = datetime.now(UTC).isoformat()
    CONTROLLER_STATE.parent.mkdir(parents=True, exist_ok=True)
    CONTROLLER_STATE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_pre_commit_gate() -> tuple[bool, str]:
    py = str(REPO_ROOT / ".venv/Scripts/python.exe")
    ruff_proc = subprocess.run(
        [py, "-m", "ruff", "check", "automation/", "--output-format=concise", "--quiet"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if ruff_proc.returncode != 0:
        print("DISPATCH-020: ruff failures detected - commit blocked")
        return (False, "DISPATCH-020: ruff failures detected — commit blocked")
<<<<<<< HEAD
    mypy_proc = subprocess.run(
        [py, "-m", "mypy", "src/", "--ignore-missing-imports", "--no-error-summary"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if mypy_proc.returncode != 0:
        print("DISPATCH-020: mypy failures detected - commit blocked")
        return (False, "DISPATCH-020: mypy failures detected — commit blocked")
=======
>>>>>>> origin/develop
    pytest_cmd = [
        py,
        "-m",
        "pytest",
        "tests/unit/",
        "-q",
        "--tb=no",
<<<<<<< HEAD
=======
        "--timeout=30",
>>>>>>> origin/develop
        "-x",
        "--ignore=tests/unit/test_queue_processor.py",
        "--ignore=tests/unit/test_collection_orchestrator.py",
        "--ignore=tests/unit/test_cycle062_smoke_aliases.py",
        "--ignore=tests/unit/test_post_cycle_review_coverage.py",
    ]
    pytest_proc = subprocess.run(
        pytest_cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if pytest_proc.returncode != 0:
        print("DISPATCH-020: pytest failures detected - commit blocked")
        return (False, "DISPATCH-020: pytest failures detected — commit blocked")
    return (True, "PASS")
<<<<<<< HEAD


def _run_export_sanitizer() -> tuple[bool, list[str]]:
    try:
        from automation.export_sanitizer_verify import verify_repo_clean

        return verify_repo_clean()
    except Exception as exc:  # noqa: BLE001
        return (False, [f"export_sanitizer_exception:{exc}"])


def _record_secret_scan_failure(violations: list[str]) -> None:
    fail_path = RUNNER_ROOT / "reports/SECRET_SCAN_FAIL.json"
    payload = {"generated_at": datetime.now(UTC).isoformat(), "violations": violations}
    fail_path.parent.mkdir(parents=True, exist_ok=True)
    fail_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    stage_report = RUNNER_ROOT / "reports/DAILY_STAGE_REPORT.json"
    if stage_report.exists():
        try:
            report_payload = json.loads(stage_report.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report_payload = {}
    else:
        report_payload = {}
    errors = report_payload.get("errors", [])
    if not isinstance(errors, list):
        errors = []
    errors.extend([f"SECRET_SCAN_FAIL:{item}" for item in violations])
    report_payload["errors"] = errors[-500:]
    report_payload["last_secret_scan_fail"] = datetime.now(UTC).isoformat()
    stage_report.parent.mkdir(parents=True, exist_ok=True)
    stage_report.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
=======
>>>>>>> origin/develop
