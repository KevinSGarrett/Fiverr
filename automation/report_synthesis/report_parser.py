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

def parse_report(path: Path | str, prompt_task_ids: list[str] | None = None) -> ClaimedAgentReport:
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


def _try_manifest_parse(raw: str) -> ClaimedAgentReport | None:
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

# Section-header families seen in REAL agent reports (free-form markdown). The
# header text varies ("Summary", "Summary of Completed Work", "Files Created or
# Modified (Full Paths)", "Files Created/Modified This Cycle (Summary)", …) so we
# match on the leading keyword rather than an exact numbered header.
_SUMMARY_HEADER_RE = re.compile(
    r"^#{1,4}\s+\d*\.?\s*"
    r"(?:summary\b|overview\b|execution\s+outcome\b|work\s+completed\b"
    r"|deliverables\b|outcome\b)"
    r".*$",
    re.IGNORECASE | re.MULTILINE,
)
_FILES_HEADER_RE = re.compile(
    r"^#{1,4}\s+\d*\.?\s*(?:files\b.*?(?:created|modified|changed|added)"
    r"|(?:created|modified|changed|added)\b.*?files\b).*$",
    re.IGNORECASE | re.MULTILINE,
)
_NEXT_HEADER_RE = re.compile(r"^#{1,4}\s+\S", re.MULTILINE)

# Known repo top-level dirs — used to anchor stripping of an absolute prefix.
_REPO_DIR_PREFIXES = (
    "src/", "tests/", "automation/", "docs/", "PM_Pack/", "data/", "scripts/",
    ".github/", "host/",
)

# The repo-root directory name (".../Fiverr/Fiverr" → "Fiverr/Fiverr"), used to
# strip a "C:/Fiverr/Fiverr/<path>" absolute prefix that lands on a dir not in
# _REPO_DIR_PREFIXES. Computed once from this module's location.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPO_TAIL = "/".join(_REPO_ROOT.parts[-2:]).replace("\\", "/") if len(_REPO_ROOT.parts) >= 2 else _REPO_ROOT.name


def _section_body(raw: str, header_re: re.Pattern[str]) -> str:
    """Return the text between the FIRST match of ``header_re`` and the next
    markdown header (any level), or end-of-text. Empty string when not found."""
    m = header_re.search(raw)
    if not m:
        return ""
    start = m.end()
    nxt = _NEXT_HEADER_RE.search(raw, start)
    end = nxt.start() if nxt else len(raw)
    return raw[start:end].strip()


def _normalize_repo_path(token: str) -> str:
    """Normalize a claimed file token → repo-relative posix path.

    Strips surrounding backticks/quotes/whitespace, a trailing
    ``(created)``/``(modified)``/``(deleted)`` suffix, converts ``\\`` to ``/``,
    and removes an absolute repo prefix (``C:/Fiverr/Fiverr/`` or any path up to
    a known repo top-level dir). Returns "" for non-path noise.
    """
    s = token.strip().strip("`'\"").strip()
    # Drop a trailing "(created)"/"(modified)"/"(deleted)" annotation.
    s = re.sub(r"\s*\((?:created|modified|deleted|new|updated)[^)]*\)\s*$", "", s, flags=re.IGNORECASE)
    s = s.strip().strip("`'\"").strip()
    if not s:
        return ""
    s = s.replace("\\", "/")
    # Strip an absolute repo prefix by anchoring on a known top-level dir.
    for prefix in _REPO_DIR_PREFIXES:
        idx = s.find("/" + prefix)
        if idx != -1:
            s = s[idx + 1:]
            break
        if s.startswith(prefix):
            break
    else:
        # No known repo dir found. Drop a Windows/posix absolute drive prefix,
        # then take what follows the report's CANONICAL repo root "Fiverr/Fiverr"
        # (independent of the current checkout path) so root-level files
        # (.github/..., config.yaml, pyproject.toml, run.py) normalize to
        # repo-relative even when CI checked the repo out elsewhere (Codex P2 #116).
        s = re.sub(r"^[A-Za-z]:/", "", s)
        m_root = re.search(r"(?:^|/)Fiverr/Fiverr/(.+)$", s)
        if m_root:
            s = m_root.group(1)
        elif _REPO_TAIL and (s.startswith(_REPO_TAIL + "/") or s == _REPO_TAIL):
            s = s[len(_REPO_TAIL):]
    s = s.lstrip("/")
    # Reject obvious non-paths (no slash and no file extension, or contains spaces).
    if " " in s:
        return ""
    if "/" not in s and "." not in s:
        return ""
    return s


def _parse_file_bullets(body: str) -> tuple[list[str], list[str]]:
    """Parse a 'Files Created or Modified' section body → (created, modified).

    Handles two shapes:
      - bullet lines: ``- `path` (created)`` / ``- `path` (modified)``
      - pipe table rows: ``| created | `path` |``
    An unannotated path bullet defaults to 'modified'.
    """
    created: list[str] = []
    modified: list[str] = []
    for line in body.splitlines():
        ls = line.strip()
        if not ls:
            continue
        # Pipe-table row: | created | `path` |
        m_tab = re.match(r"\|\s*(created|modified|deleted)\s*\|\s*`?([^`|]+)`?\s*\|", ls, re.IGNORECASE)
        if m_tab:
            action = m_tab.group(1).lower()
            norm = _normalize_repo_path(m_tab.group(2))
            if norm:
                (created if action == "created" else modified).append(norm)
            continue
        # Bullet line (-, *, +) carrying a path, optionally with (created)/(modified).
        if ls[0] in "-*+":
            content = ls[1:].strip()
            action_m = re.search(r"\((created|modified|deleted|new|updated)[^)]*\)\s*$", content, re.IGNORECASE)
            action = (action_m.group(1).lower() if action_m else "")
            norm = _normalize_repo_path(content)
            if not norm:
                continue
            if action in ("created", "new"):
                created.append(norm)
            else:
                modified.append(norm)
    # De-dup while preserving order.
    created = list(dict.fromkeys(created))
    modified = list(dict.fromkeys(modified))
    return created, modified


_INLINE_PATH_RE = re.compile(r"`([^`\n]+)`")
_FILE_EXT_RE = re.compile(r"\.[A-Za-z0-9]{1,6}$")


def _scan_inline_paths(raw: str) -> list[str]:
    """Collect backtick-quoted tokens that look like repo files anchored on a
    known top-level dir (src/, tests/, automation/, docs/, …) and carry a file
    extension. Conservative: anything else (commands, prose) is rejected."""
    found: list[str] = []
    for tok in _INLINE_PATH_RE.findall(raw):
        if " " in tok.strip():
            continue  # commands / prose, not a bare path
        norm = _normalize_repo_path(tok)
        if not norm:
            continue
        if not norm.startswith(_REPO_DIR_PREFIXES):
            continue
        if not _FILE_EXT_RE.search(norm):
            continue
        found.append(norm)
    return list(dict.fromkeys(found))


def _markdown_fallback_parse(raw: str) -> ClaimedAgentReport:
    r = ClaimedAgentReport()

    # Verdict from a numbered "Final verdict" section if present (template form).
    m = re.search(r"##\s*1\..*?verdict.*?\n.*?`([^`]+)`", raw, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
        for vv in _VALID_VERDICTS:
            if vv in text.upper():
                r.verdict = vv
                break
    if not r.verdict:
        # Real free-form reports rarely carry a manifest verdict. An
        # AGENT_COMPLETE sign-off is a self-reported "ran to completion" signal,
        # recorded as PARTIAL so the report is not mistaken for empty/NO_REPORT.
        # We deliberately do NOT set self_status=COMPLETE here: that would assert
        # full completion and let the no-commit check escalate every report to
        # CLAIMED_ONLY purely on the presence of the marker. The evidence
        # cross-check still flags real discrepancies (claimed files not in diff,
        # CI red, etc.).
        if re.search(r"\bAGENT_COMPLETE\b", raw):
            r.verdict = "PARTIAL"
        else:
            for vv in ["PASS", "PARTIAL", "FAIL", "BLOCKED"]:
                if re.search(rf"\b{vv}\b", raw[:500]):
                    r.verdict = vv
                    break

    # Summary section (free-form). Capture as a single collapsed string.
    summary_body = _section_body(raw, _SUMMARY_HEADER_RE)
    if summary_body:
        r.summary = " ".join(summary_body.split())[:2000]

    # Committed / no commit admission
    if re.search(r"No\s+git\s+commit", raw, re.IGNORECASE) or \
       re.search(r'"committed":\s*false', raw):
        r.committed = False
    if re.search(r'"committed":\s*true', raw):
        r.committed = True

    # Files created/modified — prefer the dedicated section; fall back to a
    # repo-wide scan of pipe-table rows (legacy template form).
    files_body = _section_body(raw, _FILES_HEADER_RE)
    if files_body:
        created, modified = _parse_file_bullets(files_body)
        r.files_created.extend(created)
        r.files_modified.extend(modified)
    if not (r.files_created or r.files_modified):
        for act, fpath in re.findall(
            r"\|\s*(created|modified|deleted)\s*\|\s*`([^`]+)`", raw, re.IGNORECASE
        ):
            norm = _normalize_repo_path(fpath)
            if not norm:
                continue
            if act.lower() == "created":
                r.files_created.append(norm)
            else:
                r.files_modified.append(norm)
        r.files_created = list(dict.fromkeys(r.files_created))
        r.files_modified = list(dict.fromkeys(r.files_modified))
    # NOTE (Codex P2 #116): we deliberately do NOT harvest arbitrary inline
    # backticked paths as file-change claims. Reports without a dedicated Files
    # section often list repo paths under "Evidence Files Reviewed" / "Key
    # Implementation Notes" as READ-ONLY references; treating those as "modified"
    # produced false CLAIMED_FILES_NOT_IN_DIFF downgrades. AGENT_COMPLETE / a
    # parsed summary already prevents NO_REPORT, so only dedicated file sections
    # and explicit `| created | path |` tables count as file-change claims.

    # Commits — §4 / "Git & commit attribution"
    r.commits = re.findall(r"`([0-9a-f]{7,40})`\s*[—–-]", raw)

    # Validation signals (free-form): pytest/ruff pass + coverage.
    if re.search(r"pytest.*pass", raw, re.IGNORECASE):
        r.validation["pytest_status"] = "pass"
    if re.search(r"ruff.*pass", raw, re.IGNORECASE):
        r.validation["ruff"] = "pass"
    if m2 := re.search(r"(\d+)\s*passed.*?coverage[:\s]+(\d+\.?\d*)%", raw, re.IGNORECASE):
        r.validation["pytest_passed"] = int(m2.group(1))
        r.validation["coverage_pct"] = float(m2.group(2))

    # Blockers — numbered §11 OR a free-form "Blockers" section.
    blockers_body = _section_body(
        raw, re.compile(r"^#{1,4}\s+(?:\d+\.?\s*)?.*blockers?\b.*$", re.IGNORECASE | re.MULTILINE)
    )
    if blockers_body:
        for line in blockers_body.splitlines():
            s = line.strip("- *\t")
            if s and len(s) > 6:
                r.blockers.append(s)

    # Non-claims — explicit deferral language anywhere in the report.
    for nc in re.findall(r"(?i)(?:not done|deferred|capped|explicit non-claim)[:\s]+(.+)", raw):
        r.non_claims.append(nc.strip())

    # Stories from any SCRUM-NNN pattern
    r.carryover = list(dict.fromkeys(re.findall(r"SCRUM-\d+", raw)))[:20]

    return r


# ── Violation detection (RSF-5) ───────────────────────────────────────────────

def _detect_violations(r: ClaimedAgentReport, raw: str, prompt_task_ids: list[str] | None) -> None:
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
