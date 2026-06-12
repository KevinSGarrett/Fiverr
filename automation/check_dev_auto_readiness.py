"""
check_dev_auto_readiness.py â€” V6-GOLIVE-002 gate script.
Checks whether all P0 items have been resolved before dev_auto can be enabled.
Usage: python automation/check_dev_auto_readiness.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
RUNNER_ROOT = Path("C:/AI_Runner")


def check_all() -> dict:
    checks: list[dict] = []
    passed = 0
    failed = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal passed, failed
        checks.append({"gate": name, "passed": ok, "detail": detail})
        if ok:
            passed += 1
        else:
            failed += 1

    # 1. Freeze must be OFF
    freeze_path = REPO_ROOT / "PM_Pack/automation/policies/autonomy_freeze.yml"
    if freeze_path.exists():
        import yaml
        fp = yaml.safe_load(freeze_path.read_text()) or {}
        gate("FREEZE_OFF", not fp.get("frozen", True),
             f"frozen={fp.get('frozen')} reason={fp.get('reason', '')}")
    else:
        gate("FREEZE_OFF", False, "autonomy_freeze.yml missing")

    # 2. pm-pack-audit must PASS
    r = subprocess.run(
        [str(REPO_ROOT / ".venv/Scripts/python.exe"),
         "automation/ai_cycle_controller.py", "pm-pack-audit"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    gate("PM_PACK_AUDIT", "PM_PACK_AUDIT PASS" in r.stdout,
         r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[:100])

    # 3. brain-check must PASS
    r = subprocess.run(
        [str(REPO_ROOT / ".venv/Scripts/python.exe"),
         "automation/ai_cycle_controller.py", "brain-check"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    gate("BRAIN_CHECK", "BRAIN CHECK PASS" in r.stdout,
         "PASS" if "BRAIN CHECK PASS" in r.stdout else "FAIL")

    # 4. Cursor model state VERIFIED and not expired
    model_state = RUNNER_ROOT / "state/cursor_model_state.json"
    if model_state.exists():
        ms = json.loads(model_state.read_text())
        verified = ms.get("status") == "VERIFIED"
        valid_until = ms.get("valid_until", "")
        not_expired = True
        if valid_until:
            try:
                exp = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                not_expired = exp > datetime.now(UTC)
            except Exception:
                not_expired = False
        gate("CURSOR_MODEL_VERIFIED", verified and not_expired,
             f"status={ms.get('status')} valid_until={valid_until}")
    else:
        gate("CURSOR_MODEL_VERIFIED", False, "cursor_model_state.json missing")

    # 5. ANTHROPIC_API_KEY must be absent
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    gate("NO_ANTHROPIC_API_KEY", not api_key,
         "absent" if not api_key else f"PRESENT (length {len(api_key)})")

    # 6. Repo must be clean
    r = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    dirty = r.stdout.strip()
    gate("REPO_CLEAN", not dirty, "clean" if not dirty else dirty[:100])

    # 7. Ruff must pass on automation/
    r = subprocess.run(
        [str(REPO_ROOT / ".venv/Scripts/python.exe"), "-m", "ruff", "check", "automation/"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    gate("RUFF_PASS", r.returncode == 0,
         "0 errors" if r.returncode == 0 else r.stdout[:100])

    # 8. Sanitizer self-test
    r = subprocess.run(
        ["powershell", "-File", r"C:\Fiverr\Fiverr\scripts\sanitize_repo_export.ps1",
         "-SelfTest"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    gate("SANITIZER_PASS", "PASS" in r.stdout,
         "PASS" if "PASS" in r.stdout else "FAIL")

    # 9. State machine policy exists
    sm = REPO_ROOT / "PM_Pack/automation/state_machine_policy.yml"
    gate("STATE_MACHINE_POLICY", sm.exists(), str(sm))

    # 10. Go-live stage gate exists
    glsg = REPO_ROOT / "PM_Pack/automation/go_live_stage_gate.yml"
    gate("GO_LIVE_STAGE_GATE", glsg.exists(), str(glsg))

    result = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "ready_for_dev_auto": failed == 0,
        "checks_passed": passed,
        "checks_failed": failed,
        "checks": checks,
    }

    # Save
    out = RUNNER_ROOT / "reports/validation/dev_auto_readiness.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    result = check_all()
    print(f"\n{'=' * 60}")
    print(f"DEV_AUTO READINESS CHECK â€” {result['evaluated_at']}")
    print(f"{'=' * 60}")
    for c in result["checks"]:
        icon = "PASS" if c["passed"] else "FAIL"
        print(f"  [{icon}] {c['gate']}: {c['detail']}")
    print()
    if result["ready_for_dev_auto"]:
        print("READY FOR DEV_AUTO (all gates pass)")
    else:
        print(f"NOT READY: {result['checks_failed']} gate(s) failing")
        print("Resolve all FAIL items before setting frozen: false")
    sys.exit(0 if result["ready_for_dev_auto"] else 1)
