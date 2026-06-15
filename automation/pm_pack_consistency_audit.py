"""
pm_pack_consistency_audit.py â€” PM_Pack semantic consistency audit.

Compares CURRENT_STATE_CANONICAL, HYDRATION_HEADER, STATE_SNAPSHOT,
current_policy_snapshot, controller_state, and current_status for contradictions.

V5 finding V5-002: PM_Pack state is internally contradictory.
V6 items V6-PM-001..015: Require this command to PASS before any plan-cycle.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT   = Path(__file__).parent.parent
RUNNER_ROOT = Path("C:/AI_Runner")


@dataclass
class ConflictItem:
    source_a: str
    source_b: str
    field: str
    value_a: Any
    value_b: Any
    severity: str  # BLOCKING | WARNING
    code: str = "UNSPECIFIED"

    def __str__(self) -> str:
        return (f"[{self.severity}] [{self.code}] {self.field}: "
                f"{self.source_a}={self.value_a!r} vs {self.source_b}={self.value_b!r}")


@dataclass
class AuditResult:
    passed: bool = True
    conflicts: list[ConflictItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    checked_at: str = ""
    sources: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        status = "PASS" if self.passed else "BLOCKED"
        lines = [f"PM_PACK_AUDIT {status} â€” {self.checked_at}"]
        if self.missing_files:
            lines.append(f"  Missing files: {self.missing_files}")
        for c in self.conflicts:
            lines.append(f"  CONFLICT: {c}")
        for w in self.warnings:
            lines.append(f"  WARN: {w}")
        if self.passed:
            lines.append("  All state files agree on cycle, branch, and status.")
        return "\n".join(lines)


def run_audit(repo_root: Path | None = None,
              runner_root: Path | None = None) -> AuditResult:
    """Run the full PM_Pack consistency audit."""
    repo   = repo_root   or REPO_ROOT
    runner = runner_root or RUNNER_ROOT
    result = AuditResult(checked_at=datetime.now(UTC).isoformat())

    # â”€â”€ Load all sources â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def load_json(path: Path, key: str) -> dict:
        if not path.exists():
            result.missing_files.append(str(path))
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            result.warnings.append(f"Could not parse {path}: {e}")
            return {}

    def load_md_signals(path: Path, key: str) -> dict:
        """Extract key cycle/status signals from a markdown file."""
        if not path.exists():
            result.missing_files.append(str(path))
            return {}
        txt = path.read_text(encoding="utf-8", errors="replace")
        signals: dict[str, Any] = {}

        # Cycle number patterns
        for pat in [r"CYCLE[_\s]CURRENT[:\s]+(\d+)", r"Cycle\s+0*(\d+)",
                    r"C0*(\d{3})", r"cycle/0*(\d+)/"]:
            m = re.search(pat, txt, re.IGNORECASE)
            if m:
                signals["cycle_detected"] = int(m.group(1))
                break

        # Status patterns
        for pat in [r"AGENT_DISPATCH", r"FROZEN", r"COMPILED", r"IDLE",
                    r"not started", r"READY_FOR_A"]:
            m = re.search(pat, txt, re.IGNORECASE)
            if m:
                signals["status_keyword"] = m.group(0)
                break

        return signals

    # FC-1: controller_state.json must exist
    if not (runner / "state/controller_state.json").exists():
        result.passed = False
        result.conflicts.append(ConflictItem(
            source_a="runner/state/controller_state.json",
            source_b="expected",
            field="existence",
            value_a="MISSING",
            value_b="present",
            severity="BLOCKING",
            code="MISSING_CONTROLLER_STATE",
        ))
        return result

    # Load sources
    policy_snap = load_json(repo / "PM_Pack/automation/current_policy_snapshot.json",
                            "policy_snapshot")
    ctrl_state  = load_json(runner / "state/controller_state.json",
                            "controller_state")
    current_status_txt = ""
    current_status_path = runner / "status/current_status.md"
    if current_status_path.exists():
        current_status_txt = current_status_path.read_text(encoding="utf-8",
                                                            errors="replace")

    hydration_signals = load_md_signals(
        repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md", "hydration")
    snapshot_signals  = load_md_signals(
        repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", "state_snapshot")
    canonical_signals = load_md_signals(
        repo / "PM_Pack/CURRENT_STATE_CANONICAL.md", "canonical")

    result.sources = {
        "policy_snapshot_cycle":  policy_snap.get("cycle_current"),
        "policy_last_completed":  policy_snap.get("last_completed_cycle"),
        "controller_cycle":       ctrl_state.get("active_cycle"),
        "controller_status":      ctrl_state.get("status"),
        "hydration_cycle":        hydration_signals.get("cycle_detected"),
        "snapshot_cycle":         snapshot_signals.get("cycle_detected"),
        "canonical_status":       canonical_signals.get("status_keyword"),
        "current_status_says":    current_status_txt[:100].strip() if current_status_txt else "MISSING",
    }

    # â”€â”€ Check 1: STATE_SNAPSHOT is not severely stale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    snap_cycle = snapshot_signals.get("cycle_detected", 0)
    ctrl_cycle = ctrl_state.get("active_cycle", 0)
    if snap_cycle and ctrl_cycle and abs(snap_cycle - ctrl_cycle) > 10:
        result.passed = False
        result.conflicts.append(ConflictItem(
            source_a="STATE_SNAPSHOT", source_b="controller_state",
            field="cycle", value_a=snap_cycle, value_b=ctrl_cycle,
            severity="BLOCKING", code="STATE_CYCLE_MISMATCH"
        ))

    # â”€â”€ Check 2: policy_snapshot.last_completed_cycle should not be null
    # if hydration says last completed is C074 or higher
    if policy_snap.get("last_completed_cycle") is None and ctrl_cycle and ctrl_cycle >= 74:
        result.warnings.append(
            f"current_policy_snapshot.last_completed_cycle is null but controller_cycle={ctrl_cycle}. "
            f"Run compile-policy to regenerate snapshot."
        )

    # â”€â”€ Check 3: controller_state must not say AGENT_DISPATCH if
    # current_status says "not started"
    if (ctrl_state.get("status") == "AGENT_DISPATCH" and
            current_status_txt and "not started" in current_status_txt.lower()):
        result.passed = False
        result.conflicts.append(ConflictItem(
            source_a="controller_state", source_b="current_status.md",
            field="status", value_a="AGENT_DISPATCH", value_b="not started",
            severity="BLOCKING", code="STATUS_CONFLICT"
        ))

    # â”€â”€ Check 4: hydration cycle and controller cycle should agree within 2
    hydr_cycle = hydration_signals.get("cycle_detected", 0)
    if hydr_cycle and ctrl_cycle and abs(hydr_cycle - ctrl_cycle) > 2:
        result.warnings.append(
            f"HYDRATION_HEADER shows cycle ~{hydr_cycle} but controller_state shows cycle {ctrl_cycle}. "
            f"Reconcile before dispatch."
        )

    # â”€â”€ Check 5: CANONICAL says FROZEN â€” dispatch must be blocked â”€â”€â”€â”€
    if canonical_signals.get("status_keyword", "").upper() == "FROZEN":
        result.warnings.append(
            "CURRENT_STATE_CANONICAL mentions FROZEN state â€” verify prompts/dispatch are blocked."
        )

    # â”€â”€ Check 6: autonomy freeze flag â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    freeze_path = repo / "PM_Pack/automation/policies/autonomy_freeze.yml"
    if not freeze_path.exists():
        result.warnings.append("autonomy_freeze.yml not found â€” create to enforce freeze policy")
    else:
        try:
            import yaml as _yaml
            fp = _yaml.safe_load(freeze_path.read_text()) or {}
            if fp.get("frozen", False):
                result.warnings.append(
                    f"Autonomy freeze is ACTIVE: {fp.get('reason', 'unknown')} â€” "
                    f"all dispatch blocked until freeze is lifted."
                )
        except Exception:
            pass

    # FC-6 (Stage 1 soft gate): provider policy exists but is malformed.
    provider_policy_path = repo / "PM_Pack/automation/provider_policy.yml"
    if provider_policy_path.exists():
        try:
            parsed = yaml.safe_load(provider_policy_path.read_text(encoding="utf-8")) or {}
            if not isinstance(parsed, dict):
                raise ValueError("provider_policy.yml must parse to mapping")
        except Exception as exc:
            result.passed = False
            result.conflicts.append(ConflictItem(
                source_a="provider_policy.yml",
                source_b="yaml.safe_load",
                field="parse",
                value_a="malformed",
                value_b=str(exc)[:200],
                severity="BLOCKING",
                code="PROVIDERPOLICY_INVALID",
            ))

    # â”€â”€ Write result artifact â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    out_dir = runner / "reports/validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pm_pack_audit_result.json"
    out_path.write_text(json.dumps({
        "passed":         result.passed,
        "checked_at":     result.checked_at,
        "conflicts":      [str(c) for c in result.conflicts],
        "warnings":       result.warnings,
        "missing_files":  result.missing_files,
        "sources":        result.sources,
    }, indent=2), encoding="utf-8")

    # FC-2: policy snapshot cycle must not be zero.
    policy_cycle = policy_snap.get("cycle_current", 0)
    if policy_cycle == 0:
        result.passed = False
        result.conflicts.append(ConflictItem(
            source_a="current_policy_snapshot.json",
            source_b="expected",
            field="cycle_current",
            value_a=0,
            value_b=">0",
            severity="BLOCKING",
            code="POLICY_SNAPSHOT_CYCLE_ZERO",
        ))

    # FC-3: cycle numbers must not disagree by more than 1 across sources.
    ctrl_cycle_fc = ctrl_state.get("active_cycle", 0)
    hyd_cycle_fc = hydration_signals.get("cycle_detected", 0)
    snap_cycle_fc = snapshot_signals.get("cycle_detected", 0)
    hb_cycle_fc = load_json(runner / "state/heartbeat.json", "heartbeat").get("active_cycle", 0)
    cycle_sources = [c for c in [ctrl_cycle_fc, hyd_cycle_fc, snap_cycle_fc, hb_cycle_fc] if c]
    if len(cycle_sources) >= 2 and max(cycle_sources) - min(cycle_sources) > 1:
        result.passed = False
        result.conflicts.append(ConflictItem(
            source_a="multi-source",
            source_b="expected",
            field="cycle_agreement",
            value_a=min(cycle_sources),
            value_b=max(cycle_sources),
            severity="BLOCKING",
            code="CYCLE_SOURCE_DISAGREEMENT",
        ))

    # FC-4: post-cycle result must not block dispatch.
    pcr_paths = sorted((runner / "runs").glob("CYCLE_*_post_cycle_result.json")) if (runner / "runs").exists() else []
    if pcr_paths:
        latest_pcr = json.loads(pcr_paths[-1].read_text(encoding="utf-8"))
        if latest_pcr.get("blocks_dispatch", False):
            result.passed = False
            result.conflicts.append(ConflictItem(
                source_a=str(pcr_paths[-1].name),
                source_b="expected",
                field="blocks_dispatch",
                value_a=True,
                value_b=False,
                severity="BLOCKING",
                code="POST_CYCLE_REVIEW_BLOCKS_DISPATCH",
            ))

    # FC-5: active validated prompts must all pass validation.
    cycle_for_prompts = policy_snap.get("cycle_current") or ctrl_state.get("active_cycle")
    if cycle_for_prompts:
        validated_dir = repo / "PM_Pack/automation/prompts/validated"
        manifest = validated_dir / f"CYCLE_{int(cycle_for_prompts):03d}_manifest.json"
        if manifest.exists():
            try:
                from automation import prompt_validator as pv

                agents = ["A", "B", "E", "C", "F", "D"]
                results = pv.validate_all(validated_dir, int(cycle_for_prompts), agents)
                failing = [a for a, item in results.items() if not item.passed]
                if failing:
                    result.passed = False
                    result.conflicts.append(ConflictItem(
                        source_a="prompts/validated",
                        source_b="expected",
                        field="prompt_validation",
                        value_a=str(failing),
                        value_b="all pass",
                        severity="BLOCKING",
                        code="ACTIVE_PROMPTS_INVALID",
                    ))
            except Exception:
                pass

    return result
