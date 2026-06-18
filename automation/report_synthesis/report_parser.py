"""
automation/report_synthesis/report_parser.py
RSF-2, RSF-3, RSF-5: Parse an agent report → ClaimedAgentReport.

Preferred path: ARSF:MANIFEST JSON block.
Fallback: section-header scanning.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from automation.report_synthesis.schemas import (
    AgentVerdict,
    ClaimedAgentReport,
    GateClaim,
    JiraActionClaim,
    TaskClaim,
)

# ── Violation name constants ─────────────────────────────────────────────────
V_MANIFEST_MISSING = "MANIFEST_MISSING_OR_INVALID"
V_LEDGER_INCOMPLETE = "TASK_LEDGER_INCOMPLETE"
V_NO_NON_CLAIMS = "MISSING_NON_CLAIMS_SECTION"
V_MISSING_HEADERS = "MISSING_REQUIRED_HEADERS"

REQUIRED_HEADERS = [
    "## 1. Final verdict",
    "## 2. Task ledger",
    "## 3. Files created",
    "## 4. Git",
    "## 5. Validation",
    "## 6. Gate summary",
    "## 11. Open blockers",
]

_VALID_VERDICTS = {v.value for v in AgentVerdict}


# ── Public entry point ────────────────────────────────────────────────────────

def parse_report(path: Path | str, prompt_task_ids: Optional[list[str]] = None) -> ClaimedAgentReport:
    """Parse an agent cycle report file; always returns a ClaimedAgentReport."""
    path = Path(path)
    if not path.exists():
        r = ClaimedAgentReport()
        r.parse_source = "none"
        r.format_violations = [V_MANIFEST_MISSING]
        return r

    raw = path.read_text(encoding="utf-8", errors="replace")
    report = _try_manifest_parse(raw)
    if report is None:
        report = _markdown_fallback_parse(raw)
        report.format_violations.append(V_MANIFEST_MISSING)
        report.parse_source = "markdown"
    else:
        report.parse_source = "manifest"

    report.raw_text = raw
    _detect_violations(report, raw, prompt_task_ids)
    return report


# ── Manifest parse (RSF-2) ────────────────────────────────────────────────────

_MANIFEST_RE = re.compile(
    r"<!--\s*ARSF:MANIFEST\s+v1\s*-->\s*```json\s*(\{.*?\})\s*```",
    re.DOTALL,
)


def _try_manifest_parse(raw: str) -> Optional[ClaimedAgentReport]:
    m = _MANIFEST_RE.search(raw)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

    r = ClaimedAgentReport()
    r.cycle = int(data.get("cycle", 0))
    r.agent = data.get("agent", "")
    r.role = data.get("role", "")
    r.branch = data.get("branch", "")
    r.base_sha = data.get("base_sha", "")
    r.verdict = data.get("verdict", "")
    r.verdict_qualifier = data.get("verdict_qualifier", "")

    for t in data.get("tasks", []):
        r.tasks.append(TaskClaim(
            id=t.get("id", ""),
            status=t.get("status", ""),
            evidence=t.get("evidence", ""),
        ))

    r.tasks_total = int(data.get("tasks_total", len(r.tasks)))
    r.tasks_done = int(data.get("tasks_done", 0))
    r.tasks_partial = int(data.get("tasks_partial", 0))
    r.tasks_failed = int(data.get("tasks_failed", 0))
    r.files_created = list(data.get("files_created", []))
    r.files_modified = list(data.get("files_modified", []))
    r.commits = list(data.get("commits", []))
    r.committed = bool(data.get("committed", False))
    r.validation = dict(data.get("validation", {}))

    for g in data.get("gates", []):
        r.gates.append(GateClaim(
            id=g.get("id", ""),
            result=g.get("result", ""),
            evidence=g.get("evidence", ""),
        ))

    r.ac_status = list(data.get("ac_status", []))

    for j in data.get("jira_actions", []):
        r.jira_actions.append(JiraActionClaim(
            key=j.get("key", ""),
            comment=bool(j.get("comment", False)),
            worklog=j.get("worklog", "none"),
            transition=j.get("transition", "none"),
            transition_id=j.get("transition_id", "none"),
        ))

    r.governance_updates = list(data.get("governance_updates", []))
    r.blockers = list(data.get("blockers", []))
    r.non_claims = list(data.get("non_claims", []))
    r.carryover = list(data.get("carryover", []))
    r.self_status = data.get("self_status", "")
    return r


# ── Markdown fallback parse (RSF-3) ──────────────────────────────────────────

def _markdown_fallback_parse(raw: str) -> ClaimedAgentReport:
    r = ClaimedAgentReport()

    # Verdict from §1
    m = re.search(r"##\s*1\..*?verdict.*?\n.*?`([^`]+)`", raw, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
        for vv in _VALID_VERDICTS:
            if vv in text.upper():
                r.verdict = vv
                break
    if not r.verdict:
        # Try bare PASS/FAIL/PARTIAL in text
        for vv in ["PASS", "PARTIAL", "FAIL", "BLOCKED"]:
            if re.search(rf"\b{vv}\b", raw[:500]):
                r.verdict = vv
                break

    # Committed / no commit admission
    if re.search(r"No\s+git\s+commit", raw, re.IGNORECASE) or \
       re.search(r'"committed":\s*false', raw):
        r.committed = False
    if re.search(r'"committed":\s*true', raw):
        r.committed = True

    # Files table — §3
    for act, fpath in re.findall(r"\|\s*(created|modified|deleted)\s*\|\s*`([^`]+)`", raw, re.IGNORECASE):
        if act.lower() == "created":
            r.files_created.append(fpath)
        else:
            r.files_modified.append(fpath)

    # Commits — §4
    r.commits = re.findall(r"`([0-9a-f]{7,40})`\s*[—–-]", raw)

    # Validation block — §5.1
    if re.search(r"pytest.*pass", raw, re.IGNORECASE):
        r.validation["pytest_status"] = "pass"
    if re.search(r"ruff.*pass", raw, re.IGNORECASE):
        r.validation["ruff"] = "pass"
    if m2 := re.search(r"(\d+)\s*passed.*?coverage[:\s]+(\d+\.?\d*)%", raw, re.IGNORECASE):
        r.validation["pytest_passed"] = int(m2.group(1))
        r.validation["coverage_pct"] = float(m2.group(2))

    # Blockers — §11
    m_bl = re.search(r"##\s*11\..*?\n(.*?)(?=##|\Z)", raw, re.DOTALL | re.IGNORECASE)
    if m_bl:
        for line in m_bl.group(1).splitlines():
            s = line.strip("- *\t")
            if s and len(s) > 6:
                r.blockers.append(s)

    # Non-claims — also in §11
    for nc in re.findall(r"(?i)(?:not done|deferred|capped|explicit non-claim)[:\s]+(.+)", raw):
        r.non_claims.append(nc.strip())

    # Stories from any SCRUM-NNN pattern
    r.carryover = list(dict.fromkeys(re.findall(r"SCRUM-\d+", raw)))[:20]

    return r


# ── Violation detection (RSF-5) ───────────────────────────────────────────────

def _detect_violations(r: ClaimedAgentReport, raw: str, prompt_task_ids: Optional[list[str]]) -> None:
    # Missing required headers
    raw_lower = raw.lower()
    missing = [h for h in REQUIRED_HEADERS if h.lower() not in raw_lower]
    if missing:
        r.format_violations.append(f"{V_MISSING_HEADERS}: {missing}")

    # Task-ledger completeness vs prompt task IDs
    if prompt_task_ids:
        claimed_ids = {t.id for t in r.tasks}
        missing_tasks = [tid for tid in prompt_task_ids if tid not in claimed_ids]
        if missing_tasks:
            r.format_violations.append(f"{V_LEDGER_INCOMPLETE}: missing {missing_tasks}")

    # §11 non-claims must be present
    if not re.search(r"##\s*11\.", raw, re.IGNORECASE):
        if V_NO_NON_CLAIMS not in r.format_violations:
            r.format_violations.append(V_NO_NON_CLAIMS)
