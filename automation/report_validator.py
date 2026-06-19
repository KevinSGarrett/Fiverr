"""
automation/report_validator.py
RSF-27, RSF-29: Validate an agent report against the ARSF standard.

Usage:
    from automation.report_validator import validate_report
    violations = validate_report(path, prompt_task_ids=["TASK 1", "TASK 2"])
"""
from __future__ import annotations

import re
from pathlib import Path

from automation.report_synthesis.report_parser import (
    V_NO_NON_CLAIMS, V_MISSING_HEADERS,
    REQUIRED_HEADERS, parse_report,
)

# ── Role-addendum required sections ──────────────────────────────────────────
_ROLE_ADDENDA: dict[str, list[str]] = {
    "A": ["## A1.", "## A2.", "## A3.", "## A4."],
    "B": ["## B1.", "## B2.", "## B3."],
    "C": ["## C1.", "## C2."],
    "D": ["## D1.", "## D2.", "## D3.", "## D4.", "## D5."],
    "E": ["## E1.", "## E2."],
    "F": ["## F1.", "## F2."],
}

_ALLOWED_VERDICTS = {"PASS", "PARTIAL", "FAIL", "BLOCKED",
                     "DELIVERED", "CLAIMED_ONLY", "FAILED", "NO_REPORT"}


def validate_report(
    path: Path | str,
    prompt_task_ids: list[str] | None = None,
    agent_role: str | None = None,
) -> list[str]:
    """
    Validate a report. Returns a list of violation strings (empty = clean).
    Passes a conforming (gold-standard) report with 0 violations.
    """
    path = Path(path)
    if not path.exists():
        return [f"REPORT_MISSING: {path}"]

    raw = path.read_text(encoding="utf-8", errors="replace")
    violations: list[str] = []
    raw_lower = raw.lower()

    # ── 1. Manifest valid JSON ────────────────────────────────────────────────
    parsed = parse_report(path, prompt_task_ids)
    manifest_violations = [v for v in parsed.format_violations if "MANIFEST" in v]
    if manifest_violations:
        violations.extend(manifest_violations)

    # ── 2. Required headers ───────────────────────────────────────────────────
    missing_hdr = [h for h in REQUIRED_HEADERS if h.lower() not in raw_lower]
    if missing_hdr:
        violations.append(f"{V_MISSING_HEADERS}: {missing_hdr}")

    # ── 3. Task ledger vs prompt task IDs ─────────────────────────────────────
    if prompt_task_ids:
        ledger_violations = [v for v in parsed.format_violations if "LEDGER" in v]
        violations.extend(ledger_violations)

    # ── 4. §11 non-claims present ─────────────────────────────────────────────
    if not re.search(r"##\s*11\.", raw, re.IGNORECASE):
        violations.append(V_NO_NON_CLAIMS)

    # ── 5. Verdict in allowed set + qualified ─────────────────────────────────
    verdict_raw = parsed.verdict or ""
    if verdict_raw.upper() not in _ALLOWED_VERDICTS:
        violations.append(f"INVALID_VERDICT: '{verdict_raw}'")

    # Qualifier should be non-empty (at least "none")
    if parsed.verdict_qualifier is not None and parsed.verdict_qualifier.strip() == "":
        violations.append("VERDICT_QUALIFIER_MISSING")

    # ── 6. Role-addendum sections (RSF-29) ────────────────────────────────────
    if agent_role and agent_role.upper() in _ROLE_ADDENDA:
        required_addendum = _ROLE_ADDENDA[agent_role.upper()]
        missing_add = [sec for sec in required_addendum if sec.lower() not in raw_lower]
        if missing_add:
            violations.append(f"ROLE_ADDENDUM_MISSING (agent {agent_role}): {missing_add}")

    return violations
