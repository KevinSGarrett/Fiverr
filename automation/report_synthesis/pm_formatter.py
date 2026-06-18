"""
automation/report_synthesis/pm_formatter.py
RSF-16: Render a CycleSynthesis → capped markdown for _build_pm_context.
"""
from __future__ import annotations

from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis, AgentVerdict

DEFAULT_MAX_CHARS = 8000
_AGENT_ORDER = ["A", "B", "E", "C", "F", "D"]


def format_for_pm(synth: CycleSynthesis, max_pm_block_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Render CycleSynthesis → a human-readable PM section (capped)."""
    lines: list[str] = []
    lines.append(f"**Cycle {synth.cycle:03d} — synthesis verdict: {synth.cycle_verdict}**")
    lines.append(f"Format health: {synth.format_health}")
    if synth.top_risks:
        lines.append("Top risks: " + "; ".join(synth.top_risks[:3]))
    lines.append("")

    # Sort agents: discrepancy-heavy first (most important for PM)
    def _priority(agent_key: str) -> tuple:
        a: AgentReportSynthesis = synth.agents.get(agent_key, AgentReportSynthesis())
        verdict_rank = {
            AgentVerdict.CLAIMED_ONLY.value: 0,
            AgentVerdict.FAILED.value: 1,
            AgentVerdict.BLOCKED.value: 2,
            AgentVerdict.PARTIAL.value: 3,
            AgentVerdict.NO_REPORT.value: 4,
            AgentVerdict.DELIVERED.value: 5,
        }.get(a.verdict, 6)
        return (verdict_rank, agent_key)

    sorted_agents = sorted(synth.agents.keys(), key=_priority)

    # Build per-agent blocks, truncate lowest-priority first if over cap
    blocks: list[str] = []
    for agent_key in sorted_agents:
        a = synth.agents[agent_key]
        b = _render_agent_block(agent_key, a)
        blocks.append(b)

    full = "\n".join(lines) + "\n\n" + "\n\n".join(blocks)
    if len(full) <= max_pm_block_chars:
        return full

    # Trim from the end (lowest-priority agents first)
    while blocks and len("\n".join(lines) + "\n\n" + "\n\n".join(blocks)) > max_pm_block_chars:
        blocks.pop()
    blocks.append("*(additional agents truncated to fit PM context cap)*")
    return "\n".join(lines) + "\n\n" + "\n\n".join(blocks)


def _render_agent_block(agent_key: str, a: AgentReportSynthesis) -> str:
    parts = [f"### Agent {agent_key}: {a.verdict}"]
    if a.discrepancies:
        parts.append("Discrepancies: " + "; ".join(a.discrepancies[:3]))
    if a.unmet_ac:
        parts.append("Unmet AC: " + ", ".join(a.unmet_ac[:5]))
    if a.carryover:
        parts.append("Carryover: " + "; ".join(a.carryover[:5]))
    if a.claimed and a.claimed.verdict_qualifier:
        parts.append(f"Qualifier: {a.claimed.verdict_qualifier}")
    return "\n".join(parts)
