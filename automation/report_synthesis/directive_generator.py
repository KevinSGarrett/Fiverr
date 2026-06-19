"""
automation/report_synthesis/directive_generator.py
RSF-39, RSF-39.1, RSF-40, RSF-41, RSF-42, RSF-43:
Generate next-cycle directives from a CycleSynthesis.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from automation.report_synthesis.schemas import AgentVerdict, CycleSynthesis

log = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[2]

# ── Directive decision matrix ─────────────────────────────────────────────────
# (verdict, discrepancy_flag) → (action, corrective_gate)
_MATRIX: dict[str, tuple[str, str]] = {
    AgentVerdict.CLAIMED_ONLY.value: (
        "re-dispatch with commit gate",
        "end AGENT_INCOMPLETE unless git log shows your SHA and files in diff",
    ),
    AgentVerdict.PARTIAL.value: ("carry unmet items", "deliver missing items + re-run full test suite"),
    AgentVerdict.FAILED.value: ("fix-first before new scope", "fix root cause + green suite before dispatch"),
    AgentVerdict.BLOCKED.value: ("unblock dependency", "confirm dependency resolved before re-dispatch"),
    AgentVerdict.NO_REPORT.value: ("require report", "write ARSF-conforming report before scoring"),
    "COMPLETION_CLAIMED_NO_COMMIT": (
        "require commit/push",
        "end AGENT_INCOMPLETE unless git log shows your SHA and files in diff",
    ),
    "TESTS_CLAIMED_PASS_CI_RED": (
        "fix CI",
        "CI must be green before claiming validation pass",
    ),
    "CLAIMED_FILES_NOT_IN_DIFF": (
        "verify file delivery",
        "confirm claimed files exist in git diff before marking done",
    ),
    "AC_CLAIMED_MET_DETERMINISTIC_UNMET": (
        "re-deliver AC with evidence",
        "provide deterministic evidence (test path or artifact) for each claimed AC",
    ),
    "JIRA_TRANSITION_CLAIMED_NOT_FOUND": (
        "verify Jira transition",
        "confirm transition via Jira API history before claiming",
    ),
}


@dataclass
class Directive:
    agent: str = ""
    task: str = ""
    priority: str = "P1"
    corrective_gate: str = ""
    origin: str = ""
    from_cycle: int = 0
    is_stuck: bool = False


@dataclass
class NextCycleDirectives:
    from_cycle: int = 0
    directives: list[Directive] = field(default_factory=list)
    build_sequence_advance: bool = False
    build_sequence_reason: str = ""
    stuck_items: list[str] = field(default_factory=list)
    pm_markdown: str = ""


# ── Public API ────────────────────────────────────────────────────────────────

def generate_directives(
    cs: CycleSynthesis,
    prev_directives: NextCycleDirectives | None = None,
) -> NextCycleDirectives:
    """Produce NextCycleDirectives from a CycleSynthesis (RSF-39)."""
    nd = NextCycleDirectives(from_cycle=cs.cycle)

    for agent, synth in cs.agents.items():
        # Verdict-based directive
        if synth.verdict != AgentVerdict.DELIVERED.value:
            action, gate = _MATRIX.get(synth.verdict, ("investigate", "review agent report"))
            task_text = f"{action}: re-target {'; '.join(synth.carryover[:3]) or 'last-cycle scope'}"
            nd.directives.append(Directive(
                agent=agent, task=task_text, priority="P0" if synth.verdict == AgentVerdict.CLAIMED_ONLY.value else "P1",
                corrective_gate=gate,
                origin=f"verdict={synth.verdict}",
                from_cycle=cs.cycle,
            ))

        # Per-discrepancy corrective directives
        for disc in synth.discrepancies:
            for flag, (action, gate) in _MATRIX.items():
                if flag in disc:
                    nd.directives.append(Directive(
                        agent=agent,
                        task=f"{action} ({disc[:80]})",
                        priority="P0",
                        corrective_gate=gate,
                        origin=f"discrepancy: {flag}",
                        from_cycle=cs.cycle,
                    ))
                    break

    # RSF-39.1: build-sequence advance
    wave_delivered = all(
        s.verdict == AgentVerdict.DELIVERED.value
        for s in cs.agents.values()
        if s.carryover
    )
    if wave_delivered and not cs.top_risks:
        nd.build_sequence_advance = True
        nd.build_sequence_reason = "All wave stories delivered with evidence"
    else:
        nd.build_sequence_advance = False
        nd.build_sequence_reason = f"Undelivered: {'; '.join(cs.top_risks[:3])}" if cs.top_risks else "Carryover items present"

    # RSF-43: stuck items (carried ≥2 cycles)
    if prev_directives:
        prev_tasks = {d.task for d in prev_directives.directives}
        for d in nd.directives:
            if d.task in prev_tasks:
                d.is_stuck = True
                nd.stuck_items.append(f"Agent {d.agent}: {d.task[:80]}")

    nd.pm_markdown = _render_directives_md(nd)
    return nd


def persist_directives(nd: NextCycleDirectives, runs_dir: Path | None = None) -> None:
    """RSF-40: Write JSON + MD artifacts."""
    cycle = nd.from_cycle
    runs_dir = runs_dir or (REPO_ROOT / "runs" / f"CYCLE_{cycle:03d}")
    runs_dir.mkdir(parents=True, exist_ok=True)

    json_path = runs_dir / f"CYCLE_{cycle:03d}_NEXT_CYCLE_DIRECTIVES.json"
    json_path.write_text(json.dumps(_directives_to_dict(nd), indent=2), encoding="utf-8")

    md_path = REPO_ROOT / "docs/cycle_reports" / f"CYCLE_{cycle:03d}_NEXT_CYCLE_DIRECTIVES.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(nd.pm_markdown, encoding="utf-8")


def load_next_cycle_directives(cycle: int, runs_dir: Path | None = None) -> NextCycleDirectives | None:
    """RSF-41: Load NEXT_CYCLE_DIRECTIVES.json → object; None if absent."""
    runs_dir = runs_dir or (REPO_ROOT / "runs" / f"CYCLE_{cycle:03d}")
    json_path = runs_dir / f"CYCLE_{cycle:03d}_NEXT_CYCLE_DIRECTIVES.json"
    if not json_path.exists():
        return None
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return _directives_from_dict(data)
    except Exception as exc:
        log.warning("load_next_cycle_directives(%d): %s", cycle, exc)
        return None


# ── Serialization ─────────────────────────────────────────────────────────────

def _directives_to_dict(nd: NextCycleDirectives) -> dict:
    return {
        "from_cycle": nd.from_cycle,
        "build_sequence_advance": nd.build_sequence_advance,
        "build_sequence_reason": nd.build_sequence_reason,
        "stuck_items": nd.stuck_items,
        "pm_markdown": nd.pm_markdown,
        "directives": [
            {
                "agent": d.agent, "task": d.task, "priority": d.priority,
                "corrective_gate": d.corrective_gate, "origin": d.origin,
                "from_cycle": d.from_cycle, "is_stuck": d.is_stuck,
            }
            for d in nd.directives
        ],
    }


def _directives_from_dict(data: dict) -> NextCycleDirectives:
    nd = NextCycleDirectives(
        from_cycle=int(data.get("from_cycle", 0)),
        build_sequence_advance=bool(data.get("build_sequence_advance", False)),
        build_sequence_reason=data.get("build_sequence_reason", ""),
        stuck_items=list(data.get("stuck_items", [])),
        pm_markdown=data.get("pm_markdown", ""),
    )
    for d in data.get("directives", []):
        nd.directives.append(Directive(
            agent=d.get("agent", ""), task=d.get("task", ""),
            priority=d.get("priority", "P1"), corrective_gate=d.get("corrective_gate", ""),
            origin=d.get("origin", ""), from_cycle=int(d.get("from_cycle", 0)),
            is_stuck=bool(d.get("is_stuck", False)),
        ))
    return nd


def _render_directives_md(nd: NextCycleDirectives) -> str:
    lines = [
        f"# CYCLE_{nd.from_cycle:03d}_NEXT_CYCLE_DIRECTIVES",
        "",
        f"Build-sequence advance: **{nd.build_sequence_advance}** — {nd.build_sequence_reason}",
        "",
    ]
    if nd.stuck_items:
        lines += ["## Stuck items (carried ≥2 cycles)", ""] + [f"- {s}" for s in nd.stuck_items] + [""]
    lines += ["## Directives", "", "| Agent | Priority | Task | Corrective gate | Origin |", "|---|---|---|---|---|"]
    for d in nd.directives:
        lines.append(f"| {d.agent} | {d.priority} | {d.task[:70]} | {d.corrective_gate[:60]} | {d.origin[:50]} |")
    return "\n".join(lines) + "\n"
