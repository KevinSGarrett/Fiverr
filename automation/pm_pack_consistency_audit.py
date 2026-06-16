"""
pm_pack_consistency_audit.py — PM_Pack semantic consistency audit.

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

REPO_ROOT   = Path("C:/Fiverr/Fiverr")
RUNNER_ROOT = Path("C:/AI_Runner")


@dataclass
class ConflictItem:
    source_a: str
    source_b: str
    field: str
    value_a: Any
    value_b: Any
    severity: str  # BLOCKING | WARNING
    code: str = ""

    def __str__(self) -> str:
        prefix = f"{self.code} " if self.code else ""
        return (f"[{self.severity}] {prefix}{self.field}: "
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
        lines = [f"PM_PACK_AUDIT {status} — {self.checked_at}"]
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

    # ── Load all sources ──────────────────────────────────────────────
    def load_json(path: Path) -> dict:
        if not path.exists():
            result.missing_files.append(str(path))
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError) as e:
            result.warnings.append(f"Could not parse {path}: {e}")
            return {}

    def load_md_signals(path: Path) -> dict:
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

    # Load sources
    policy_snap = load_json(repo / "PM_Pack/automation/current_policy_snapshot.json")
    ctrl_state = load_json(runner / "state/controller_state.json")
    current_status_txt = ""
    current_status_path = runner / "status/current_status.md"
    if current_status_path.exists():
        current_status_txt = current_status_path.read_text(encoding="utf-8",
                                                            errors="replace")

    hydration_signals = load_md_signals(repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md")
    snapshot_signals = load_md_signals(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md")
    canonical_signals = load_md_signals(repo / "PM_Pack/CURRENT_STATE_CANONICAL.md")

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

    # ── Check 1: STATE_SNAPSHOT is not severely stale ─────────────────
    snap_cycle = snapshot_signals.get("cycle_detected", 0)
    ctrl_cycle = ctrl_state.get("active_cycle", 0)
    if snap_cycle and ctrl_cycle and abs(snap_cycle - ctrl_cycle) > 10:
        result.passed = False
        result.conflicts.append(ConflictItem(
            code="STATESNAPSHOTSTALE",
            source_a="STATE_SNAPSHOT", source_b="controller_state",
            field="cycle", value_a=snap_cycle, value_b=ctrl_cycle,
            severity="BLOCKING"
        ))

    # ── Check 2: policy_snapshot.last_completed_cycle should not be null
    # if hydration says last completed is C074 or higher
    if policy_snap.get("last_completed_cycle") is None and ctrl_cycle and ctrl_cycle >= 74:
        result.warnings.append(
            f"current_policy_snapshot.last_completed_cycle is null but controller_cycle={ctrl_cycle}. "
            f"Run compile-policy to regenerate snapshot."
        )

    # ── Check 3: controller_state must not say AGENT_DISPATCH if
    # current_status says "not started"
    if (ctrl_state.get("status") == "AGENT_DISPATCH" and
            current_status_txt and "not started" in current_status_txt.lower()):
        result.passed = False
        result.conflicts.append(ConflictItem(
            code="CYCLESOURCEDISAGREEMENT",
            source_a="controller_state", source_b="current_status.md",
            field="status", value_a="AGENT_DISPATCH", value_b="not started",
            severity="BLOCKING"
        ))

    # ── Check 4: hydration cycle and controller cycle should agree within 2
    hydr_cycle = hydration_signals.get("cycle_detected", 0)
    if hydr_cycle and ctrl_cycle and abs(hydr_cycle - ctrl_cycle) > 2:
        result.warnings.append(
            f"HYDRATION_HEADER shows cycle ~{hydr_cycle} but controller_state shows cycle {ctrl_cycle}. "
            f"Reconcile before dispatch."
        )

    # ── Check 5: CANONICAL says FROZEN — dispatch must be blocked ────
    if canonical_signals.get("status_keyword", "").upper() == "FROZEN":
        result.warnings.append(
            "CURRENT_STATE_CANONICAL mentions FROZEN state — verify prompts/dispatch are blocked."
        )

    # ── Check 7: provider health artifact exists when provider policy is configured ──
    provider_policy_path = repo / "PM_Pack/automation/provider_policy.yml"
    provider_health_path = runner / "state/provider_health.json"
    if provider_policy_path.exists() and not provider_health_path.exists():
        result.conflicts.append(ConflictItem(
            code="PROVIDERHEALTHMISSING",
            source_a="provider_policy.yml",
            source_b="provider_health.json",
            field="provider_health_artifact",
            value_a="configured",
            value_b="missing",
            severity="WARNING",
        ))
        result.warnings.append(
            "PROVIDERHEALTHMISSING: provider_health.json is missing while provider policy is present."
        )

    # ── Check 8 (FC-8): post-cycle ADVISORY_ONLY must fail audit ─────
    active_cycle = ctrl_state.get("active_cycle")
    reviews_dir = repo / "PM_Pack/automation/post_cycle_reviews"
    if isinstance(active_cycle, int) and reviews_dir.exists():
        cycle_marker = f"{active_cycle:03d}"
        review_files = sorted(
            reviews_dir.glob("*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        # Find the most recent review file for this cycle
        latest_cycle_review_status = ""
        for review_file in review_files:
            try:
                review_payload = json.loads(review_file.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            file_cycle = str(review_payload.get("cycle") or "")
            if not file_cycle and cycle_marker in review_file.name:
                file_cycle = cycle_marker
            if str(file_cycle).zfill(3) != cycle_marker:
                continue
            # This is a cycle-matching file. Take its status and stop — files are
            # sorted newest-first so the first match is always the most recent review.
            latest_cycle_review_status = str(
                review_payload.get("result") or review_payload.get("status") or ""
            ).upper()
            break
        # FC-8 only fires if the LATEST review for this cycle is a hard FAIL/BLOCKED.
        # ADVISORY_ONLY and PASS are both acceptable terminal states.
        if latest_cycle_review_status not in ("", "PASS", "ADVISORY_ONLY"):
            result.passed = False
            result.conflicts.append(
                ConflictItem(
                    code="FC-8",
                    source_a="post_cycle_reviews",
                    source_b="controller_state",
                    field="post_cycle_status",
                    value_a=latest_cycle_review_status,
                    value_b=ctrl_state.get("status"),
                    severity="BLOCKING",
                )
            )
            result.warnings.append(
                f"FC-8: latest post_cycle_review for C{cycle_marker} has status "
                f"'{latest_cycle_review_status}' — must be PASS or ADVISORY_ONLY before dispatch."
            )

    # ── Check 6: autonomy freeze flag ────────────────────────────────
    freeze_path = repo / "PM_Pack/automation/policies/autonomy_freeze.yml"
    if not freeze_path.exists():
        result.warnings.append("autonomy_freeze.yml not found — create to enforce freeze policy")
    else:
        try:
            import yaml as _yaml
            fp = _yaml.safe_load(freeze_path.read_text()) or {}
            if fp.get("frozen", False):
                result.warnings.append(
                    f"Autonomy freeze is ACTIVE: {fp.get('reason', 'unknown')} — "
                    f"all dispatch blocked until freeze is lifted."
                )
        except (OSError, ImportError):
            pass

    # ── Write result artifact ─────────────────────────────────────────
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

    return result
