"""
automation/report_synthesis/synthesizer.py
RSF-13, RSF-13.1, RSF-14, RSF-15, RSF-17, RSF-19, RSF-21, RSF-22:
Orchestrate synthesis for a full cycle.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from automation.report_synthesis.schemas import (
    AgentReportSynthesis,
    AgentVerdict,
    CycleSynthesis,
)
from automation.report_synthesis.report_parser import parse_report
from automation.report_synthesis.evidence_crosscheck import crosscheck_agent
from automation.report_synthesis.pm_formatter import format_for_pm

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_ORDER = ["A", "B", "E", "C", "F", "D"]

_CYCLE_VERDICT_RANK = {
    AgentVerdict.DELIVERED.value: 5,
    AgentVerdict.PARTIAL.value: 4,
    AgentVerdict.CLAIMED_ONLY.value: 3,
    AgentVerdict.FAILED.value: 2,
    AgentVerdict.BLOCKED.value: 1,
    AgentVerdict.NO_REPORT.value: 0,
}


# ── Public API ────────────────────────────────────────────────────────────────

def synthesize_cycle(
    cycle: int,
    *,
    reports_dir: Path | None = None,
    runs_dir: Path | None = None,
    _git_adapter=None,
    _ci_reader=None,
    _jira_client=None,
) -> CycleSynthesis:
    """
    Locate 6 agent reports, parse+crosscheck each, build CycleSynthesis,
    persist artifacts, return the object.
    Non-blocking: any failure → partial synthesis, never raises.
    """
    if os.environ.get("ARSF_DISABLED", "").lower() in ("1", "true", "yes"):
        log.info("ARSF: synthesize_cycle skipped (ARSF_DISABLED).")
        cs = CycleSynthesis(cycle=cycle)
        cs.cycle_verdict = "DISABLED"
        return cs

    reports_dir = reports_dir or (REPO_ROOT / "docs/cycle_reports")
    runs_dir = runs_dir or (REPO_ROOT / "runs" / f"CYCLE_{cycle:03d}")

    cs = CycleSynthesis(cycle=cycle)

    for agent in AGENT_ORDER:
        try:
            synth = _synthesize_agent(
                cycle, agent, reports_dir,
                _git_adapter=_git_adapter,
                _ci_reader=_ci_reader,
                _jira_client=_jira_client,
            )
        except Exception as exc:  # RSF-33: never crash the cycle
            log.warning("ARSF: agent %s synthesis failed: %s", agent, exc)
            synth = AgentReportSynthesis(agent=agent, verdict=AgentVerdict.NO_REPORT.value)

        cs.agents[agent] = synth

        # RSF-22: fold ICV outcomes if present
        _fold_icv(cs, agent, synth)

    # RSF-14: aggregate fields
    _aggregate(cs)

    # RSF-16: render PM markdown
    cs.pm_markdown = format_for_pm(cs)

    # RSF-15: persist artifacts
    try:
        _persist(cs, runs_dir)
    except Exception as exc:
        log.warning("ARSF: persist failed: %s", exc)

    # RSF-21: terminal banner + live_events
    _emit_banner(cs)

    return cs


def load_cycle_synthesis(cycle: int, runs_dir: Path | None = None) -> CycleSynthesis | None:
    """RSF-17: Load CYCLE_NNN_SYNTHESIS.json → CycleSynthesis; None if absent."""
    runs_dir = runs_dir or (REPO_ROOT / "runs" / f"CYCLE_{cycle:03d}")
    json_path = runs_dir / f"CYCLE_{cycle:03d}_SYNTHESIS.json"
    if not json_path.exists():
        return None
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return _synthesis_from_dict(data)
    except Exception as exc:
        log.warning("load_cycle_synthesis(%d): %s", cycle, exc)
        return None


# ── Per-agent synthesis ───────────────────────────────────────────────────────

def _synthesize_agent(cycle, agent, reports_dir, **kwargs) -> AgentReportSynthesis:
    report_path = reports_dir / f"CYCLE_{cycle:03d}_AGENT_{agent}.md"
    claimed = parse_report(report_path)
    claimed.agent = claimed.agent or agent
    claimed.cycle = claimed.cycle or cycle
    synth = crosscheck_agent(claimed, cycle, **kwargs)
    synth.summary_for_pm = _make_summary(agent, synth)
    return synth


# ── Summary for PM (RSF-13.1) ────────────────────────────────────────────────

def _make_summary(agent: str, synth: AgentReportSynthesis) -> str:
    lines = [f"Agent {agent}: {synth.verdict}"]
    if synth.discrepancies:
        lines.append(f"  Key discrepancy: {synth.discrepancies[0]}")
    if synth.carryover:
        lines.append(f"  Carryover: {'; '.join(synth.carryover[:3])}")
    if synth.claimed and synth.claimed.non_claims:
        lines.append(f"  Explicit non-claims: {synth.claimed.non_claims[0]}")
    return "\n".join(lines)


# ── Aggregation (RSF-14) ──────────────────────────────────────────────────────

def _aggregate(cs: CycleSynthesis) -> None:
    verdicts = [s.verdict for s in cs.agents.values()]
    # cycle_verdict = lowest-ranked individual verdict
    min_rank = min((_CYCLE_VERDICT_RANK.get(v, 0) for v in verdicts), default=0)
    cs.cycle_verdict = next(
        (v for v, r in _CYCLE_VERDICT_RANK.items() if r == min_rank),
        AgentVerdict.NO_REPORT.value,
    )
    # carryover: union of per-agent carryover
    seen: set[str] = set()
    for s in cs.agents.values():
        for item in s.carryover:
            if item not in seen:
                cs.carryover.append(item)
                seen.add(item)
    # top_risks: CLAIMED_ONLY and FAILED agents
    cs.top_risks = [
        f"Agent {a} = {s.verdict}"
        for a, s in cs.agents.items()
        if s.verdict in (AgentVerdict.CLAIMED_ONLY.value, AgentVerdict.FAILED.value)
    ]
    # format_health: how many reports have no MANIFEST violation
    conforming = sum(
        1 for s in cs.agents.values()
        if s.claimed and not any("MANIFEST" in v for v in s.claimed.format_violations)
    )
    cs.format_health = f"{conforming}/{len(cs.agents)}"


# ── ICV fold (RSF-22) ────────────────────────────────────────────────────────

def _fold_icv(cs: CycleSynthesis, agent: str, synth: AgentReportSynthesis) -> None:
    """If the controller stored ICV outcomes, copy them into the synthesis."""
    try:
        icv_path = REPO_ROOT / "C:/AI_Runner/state/icv_outcomes.json"
        if not icv_path.exists():
            return
        outcomes = json.loads(icv_path.read_text())
        key = f"CYCLE_{cs.cycle:03d}_AGENT_{agent}"
        if key in outcomes:
            synth.icv_status = str(outcomes[key].get("status", ""))
            synth.icv_score = float(outcomes[key].get("score", 0.0))
    except Exception:
        pass


# ── Persistence (RSF-15) ─────────────────────────────────────────────────────

def _persist(cs: CycleSynthesis, runs_dir: Path) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)

    # JSON (machine)
    json_path = runs_dir / f"CYCLE_{cs.cycle:03d}_SYNTHESIS.json"
    json_path.write_text(json.dumps(_synthesis_to_dict(cs), indent=2), encoding="utf-8")

    # Markdown (human)
    md_path = REPO_ROOT / "docs/cycle_reports" / f"CYCLE_{cs.cycle:03d}_SYNTHESIS.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_synthesis_to_md(cs), encoding="utf-8")

    log.info("ARSF: persisted synthesis for cycle %d", cs.cycle)


# ── Banner / events (RSF-21) ─────────────────────────────────────────────────

def _emit_banner(cs: CycleSynthesis) -> None:
    delivered = sum(1 for s in cs.agents.values() if s.verdict == AgentVerdict.DELIVERED.value)
    claimed_only = [a for a, s in cs.agents.items() if s.verdict == AgentVerdict.CLAIMED_ONLY.value]
    banner = (
        f"ARSF: cycle {cs.cycle:03d} → {delivered}/6 DELIVERED"
        + (f", {','.join(claimed_only)}=CLAIMED_ONLY" if claimed_only else "")
        + f"; reports {cs.format_health} conform"
    )
    print(banner)
    log.info(banner)
    try:
        from automation.live_events import emit
        emit("ARSF", {
            "cycle": cs.cycle,
            "cycle_verdict": cs.cycle_verdict,
            "delivered": delivered,
            "claimed_only": claimed_only,
            "format_health": cs.format_health,
        })
    except Exception:
        pass


# ── Serialization helpers ────────────────────────────────────────────────────

def _synthesis_to_dict(cs: CycleSynthesis) -> dict:
    return {
        "cycle": cs.cycle,
        "cycle_verdict": cs.cycle_verdict,
        "format_health": cs.format_health,
        "carryover": cs.carryover,
        "top_risks": cs.top_risks,
        "pm_markdown": cs.pm_markdown,
        "agents": {
            a: {
                "verdict": s.verdict,
                "discrepancies": s.discrepancies,
                "actual_commits": s.actual_commits,
                "actual_files": s.actual_files,
                "ci_status": s.ci_status,
                "unmet_ac": s.unmet_ac,
                "carryover": s.carryover,
                "summary_for_pm": s.summary_for_pm,
                "icv_status": s.icv_status,
                "icv_score": s.icv_score,
            }
            for a, s in cs.agents.items()
        },
    }


def _synthesis_from_dict(data: dict) -> CycleSynthesis:
    from automation.report_synthesis.schemas import AgentReportSynthesis as ARS
    cs = CycleSynthesis(
        cycle=int(data.get("cycle", 0)),
        cycle_verdict=data.get("cycle_verdict", ""),
        format_health=data.get("format_health", ""),
        carryover=list(data.get("carryover", [])),
        top_risks=list(data.get("top_risks", [])),
        pm_markdown=data.get("pm_markdown", ""),
    )
    for agent, ad in data.get("agents", {}).items():
        s = ARS(
            agent=agent,
            verdict=ad.get("verdict", ""),
            discrepancies=list(ad.get("discrepancies", [])),
            actual_commits=list(ad.get("actual_commits", [])),
            actual_files=list(ad.get("actual_files", [])),
            ci_status=ad.get("ci_status", "unknown"),
            unmet_ac=list(ad.get("unmet_ac", [])),
            carryover=list(ad.get("carryover", [])),
            summary_for_pm=ad.get("summary_for_pm", ""),
            icv_status=ad.get("icv_status", ""),
            icv_score=float(ad.get("icv_score", 0.0)),
        )
        cs.agents[agent] = s
    return cs


def _synthesis_to_md(cs: CycleSynthesis) -> str:
    lines = [
        f"# CYCLE_{cs.cycle:03d}_SYNTHESIS",
        "",
        f"**Cycle verdict:** {cs.cycle_verdict}  ",
        f"**Format health:** {cs.format_health}  ",
        "",
        "## Per-agent summary",
        "",
        "| Agent | Verdict | Discrepancies | Carryover |",
        "|---|---|---|---|",
    ]
    for agent in AGENT_ORDER:
        s = cs.agents.get(agent, AgentReportSynthesis(agent=agent, verdict=AgentVerdict.NO_REPORT.value))
        lines.append(
            f"| {agent} | {s.verdict} | "
            f"{'; '.join(s.discrepancies[:2]) or '—'} | "
            f"{'; '.join(s.carryover[:3]) or '—'} |"
        )
    if cs.top_risks:
        lines += ["", "## Top risks", ""] + [f"- {r}" for r in cs.top_risks]
    if cs.carryover:
        lines += ["", "## Carryover", ""] + [f"- {c}" for c in cs.carryover]
    return "\n".join(lines) + "\n"
