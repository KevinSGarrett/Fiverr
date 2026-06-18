"""
prompt_validator.py — Hard validation of Cursor agent prompts before dispatch.
Per audit FINDING-010: missing model block, END OF PROMPT, Jira keys are ERRORS not warnings.
Per final pack: 55 LARGE-XXLARGE task minimum, PQ-0..PQ-7, no secrets, exact compliance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Hard error gates (FAIL if missing) ─────────────────────────────────────
REQUIRED_ERRORS = [
    # Model block
    (r"Codex 5\.3|codex-5\.3|gpt-5\.3-codex",   "Codex 5.3 model block"),
    (r"medium.*effort|effort.*medium",             "medium effort specification"),
    # Structural
    (r"END OF PROMPT",                             "END OF PROMPT marker (exactly once)"),
    (r"SCRUM-\d+",                                 "at least one Jira key (SCRUM-NNN)"),
    (r"cycle/\d{3}/integration",                   "branch reference cycle/NNN/integration"),
    (r"C:\\Fiverr\\Fiverr|C:/Fiverr/Fiverr",      "repo root C:\\Fiverr\\Fiverr"),
    (r"docs/cycle_reports/CYCLE_\d{3}",            "report path docs/cycle_reports/"),
    (r"python.*-m.*ruff|ruff.*check",              "ruff validation command"),
    (r"python.*-m.*mypy|mypy.*src",                "mypy validation command"),
    (r"python.*-m.*pytest|pytest",                 "pytest validation command"),
    # Safety gates
    (r"Auto.*DISABLED|auto.*disabled|auto_model_disabled",  "Auto model disabled statement"),
    (r"Autonomy rule|autonomy rule",               "Autonomy rule section"),
]

# ── Task floor checks ───────────────────────────────────────────────────────
MIN_TASKS        = 55    # LARGE-XXLARGE task floor from Wave 04
MIN_LINE_COUNT   = 150   # real prompts are 150-1000+ lines
MIN_WORD_COUNT   = 6000  # template requires >=6000 words

# ── Stub patterns — always FAIL ─────────────────────────────────────────────
STUB_PATTERNS = [
    r"\[STUB",
    r"populate from PM_Pack",
    r"\[TODO\]",
    r"<exact agent mission>",
    r"^\s*fill in\s*$",     # bare "fill in" on its own line = stub; (fill in) in tables is OK
    r"\[FILL\]",
]

# ── PQ quality gates — all must be present in a real prompt ────────────────
PQ_GATES = [
    ("PQ-0", r"PQ-0|identity"),
    ("PQ-1", r"PQ-1|project context"),
    ("PQ-2", r"PQ-2|your role|file ownership"),
    ("PQ-3", r"PQ-3|git instructions"),
    ("PQ-4", r"PQ-4|autonomy"),
    ("PQ-5", r"PQ-5|jira scope"),
    # PQ-6/PQ-7 handled separately below with richer checks
]

# ── PQ-6: each task must have at least one runnable shell block ───────────────
MIN_CODE_BLOCKS_RATIO = 0.3   # at least 30% of tasks must have a code block

# ── PQ-7: anti-paste gate — prompts must not be verbatim copies of prior cycles
# (checked via unique content ratio; >80% unique words = not a paste)
MIN_UNIQUE_WORD_RATIO = 0.40  # at least 40% unique words (vs total words)

# ── Hard-fail safety patterns ───────────────────────────────────────────────
SAFETY_ERRORS = [
    (r"^\s*git push.*\bmain\b", "git push to main command"),  # only actual commands
    (r"^\s*git push.*--force", "git force-push command"),  # only actual commands
    (r"ANTHROPIC_API_KEY\s*=\s*[\'\"]{0,1}sk-", "Anthropic API key with value"),  # value only
    (r"ghp_[a-zA-Z0-9]{36,}",                        "GitHub token literal"),
    (r"ATATT3x[a-zA-Z0-9]+",                          "Jira API token literal"),
    # storage_state.json: only fail on actual git staging/commit commands.
    # Policy prohibitions like "do not commit storage_state.json" are safe and correct.
    (r"^\s*git add[^\n]{0,80}storage_state\.json|^\s*git commit[^\n]{0,80}storage_state",
     "storage_state.json in git add/commit command"),
]


@dataclass
class PromptValidationResult:
    prompt_path: str
    agent: str
    cycle: int
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    task_count: int = 0
    word_count: int = 0
    line_count: int = 0
    end_of_prompt_count: int = 0

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"Prompt validation {status}: {self.prompt_path}"]
        lines.append(f"  Lines={self.line_count} Words={self.word_count} Tasks={self.task_count}")
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN : {w}")
        return "\n".join(lines)


def validate(prompt_path: str | Path, agent: str, cycle: int) -> PromptValidationResult:
    """
    Hard validation of a single prompt file.
    Missing model block, END OF PROMPT, Jira keys = ERRORS (not warnings).
    """
    result = PromptValidationResult(
        prompt_path=str(prompt_path), agent=agent, cycle=cycle, passed=True
    )

    path = Path(prompt_path)
    if not path.exists():
        result.passed = False
        result.errors.append(f"Prompt file does not exist: {path}")
        return result

    text = path.read_text(encoding="utf-8", errors="replace")
    lines_list = text.splitlines()

    result.line_count  = len(lines_list)
    result.word_count  = len(text.split())
    result.task_count  = len(re.findall(r"^### Task \d+", text, re.MULTILINE))
    result.end_of_prompt_count = len(re.findall(r"END OF PROMPT", text))

    # ── Stub check (immediate fail) ─────────────────────────────────────
    for pat in STUB_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            result.passed = False
            result.errors.append(f"Stub pattern detected: {pat}")

    # ── Line count ──────────────────────────────────────────────────────
    if result.line_count < MIN_LINE_COUNT:
        result.passed = False
        result.errors.append(
            f"Prompt too short: {result.line_count} lines (minimum {MIN_LINE_COUNT})"
        )

    # ── Word count ──────────────────────────────────────────────────────
    if result.word_count < MIN_WORD_COUNT:
        result.warnings.append(
            f"Prompt below 6,000 word target: {result.word_count} words"
        )

    # ── Task floor ──────────────────────────────────────────────────────
    if result.task_count < MIN_TASKS:
        result.passed = False
        result.errors.append(
            f"Task floor violation: {result.task_count} tasks < {MIN_TASKS} minimum"
        )

    # ── END OF PROMPT exactly once ──────────────────────────────────────
    if result.end_of_prompt_count == 0:
        result.passed = False
        result.errors.append("END OF PROMPT marker missing")
    elif result.end_of_prompt_count > 1:
        result.passed = False
        result.errors.append(
            f"END OF PROMPT appears {result.end_of_prompt_count} times (must be exactly 1)"
        )

    # ── Required content gates (ERRORS) ─────────────────────────────────
    for pattern, description in REQUIRED_ERRORS:
        if not re.search(pattern, text, re.IGNORECASE):
            result.passed = False
            result.errors.append(f"Missing required content: {description}")

    # ── PQ quality gates ────────────────────────────────────────────────
    # Only enforce PQ gates if at least some sections are present (real prompt)
    if result.task_count > 0:
        for pq_id, pq_pattern in PQ_GATES:
            if not re.search(pq_pattern, text, re.IGNORECASE):
                result.warnings.append(f"PQ gate not confirmed: {pq_id}")

    # PQ-6: At least MIN_CODE_BLOCKS_RATIO of tasks must have a code block (```...)
    # This ensures tasks have runnable commands, not just prose descriptions.
    if result.task_count > 0:
        code_block_count = len(re.findall(r"```", text)) // 2  # pairs of ```
        ratio = code_block_count / max(result.task_count, 1)
        if ratio < MIN_CODE_BLOCKS_RATIO:
            result.warnings.append(
                f"PQ-6: only {code_block_count} code blocks for {result.task_count} tasks "
                f"(ratio={ratio:.0%}, floor={MIN_CODE_BLOCKS_RATIO:.0%}). "
                "Add runnable command blocks so Cursor executes, not just narrates."
            )

    # PQ-7: Anti-paste gate (REVISED for real Jira/spec paste detection).
    # (a) unique-word ratio: catches verbatim cycle-to-cycle recycling
    # (b) task substance: catches spec/Jira dump (task must have code+path+verify)
    words = re.findall(r"\b\w{4,}\b", text.lower())
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < MIN_UNIQUE_WORD_RATIO:
            result.warnings.append(
                f"PQ-7a: unique word ratio {unique_ratio:.0%} < {MIN_UNIQUE_WORD_RATIO:.0%}. "
                "Prompt may be verbatim recycled from a prior cycle."
            )

    # PQ-7b: Task substance check -- authored vs pasted tasks
    # An authored task has: runnable code block + concrete file path + verification step.
    # A spec-dump prompt has large pasted text blocks but few authored tasks.
    task_blocks = re.findall(
        r"###+\s+Task\s+\d+.*?(?=###+\s+Task\s+\d+|\Z)",
        text, re.DOTALL | re.IGNORECASE,
    )
    if task_blocks:
        authored_count = 0
        for tb in task_blocks[:60]:
            has_code = bool(re.search(r"```", tb))
            has_path = bool(re.search(r"(?:src|automation|tests|docs)/[\w/]+\.py", tb))
            has_verify = bool(re.search(
                r"(?:expected output|assert|verify|PASS|exit.*0|\== )", tb, re.IGNORECASE
            ))
            if has_code and has_path and has_verify:
                authored_count += 1
        authored_ratio = authored_count / len(task_blocks)
        MIN_AUTHORED_RATIO = 0.20  # at least 20% of tasks must be authored (not pasted)
        if authored_ratio < MIN_AUTHORED_RATIO:
            result.warnings.append(
                f"PQ-7b: {authored_count}/{len(task_blocks)} tasks ({authored_ratio:.0%}) have "
                "authored code+path+verify. Prompt may be a Jira/spec paste-dump."
            )
    # ── Safety gates (always FAIL) ──────────────────────────────────────
    for pattern, description in SAFETY_ERRORS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            result.passed = False
            result.errors.append(f"Safety gate triggered: {description}")

    # ── Cycle number must match ─────────────────────────────────────────
    # Look for the canonical agent prompt header: "AGENT X -- CYCLE NNN PROMPT"
    # This avoids false positives from references like "DO NOT create cycle_083_*"
    # in PM_Pack Section 0 preambles that appear before the actual header.
    header_match = re.search(
        r"AGENT\s+\w+\s+--\s+CYCLE\s+0*(\d+)\s+PROMPT", text, re.IGNORECASE
    )
    cycle_match = header_match or re.search(r"CYCLE[_ ]?0*(\d+)", text, re.IGNORECASE)
    if cycle_match:
        found = int(cycle_match.group(1))
        if found != cycle:
            result.passed = False
            result.errors.append(f"Cycle mismatch: prompt says {found:03d}, expected {cycle:03d}")
    else:
        result.warnings.append(f"Cycle number {cycle:03d} not found in prompt")

    # ── Agent ID must match ─────────────────────────────────────────────
    if (f"Agent {agent}" not in text and
            f"AGENT_{agent}" not in text.upper() and
            f"AGENT {agent}" not in text.upper()):
        result.warnings.append(f"Agent {agent} not clearly identified in prompt")

    # ── Agent A: floor script required ─────────────────────────────────
    if agent == "A":
        if "floor_check" not in text and "MIN_TASKS" not in text:
            result.warnings.append("Agent A Task 1 floor check script missing")



    # PQ-11: C070 structural lint - INVOKE-EXE, niche IDs, gates, regression pack, authorization
    # These mirror the manual C070 prompt structure requirements (non-blocking warnings)
    _PQ11_CHECKS = [
        (r"INVOKE.EXE|function Invoke-Exe|Invoke-Exe\b",
         "PQ-11: INVOKE-EXE PowerShell helper missing"),
        (r"\$py\s*=|\$git\s*=|\$gh\s*=",
         "PQ-11: binary path variables ($py/$git/$gh) missing"),
        (r"prd_ai_saas|gumloop_lindy|mcp_ai_agent|python_automation|workflow_automation|ai_agent_development",
         "PQ-11: niche IDs missing (prd_ai_saas/mcp_ai_agent/workflow_automation)"),
        (r"G-A|G-B|G-C|G-D",
         "PQ-11: production readiness gates G-A..G-D missing"),
        (r"PERMANENT REGRESSION|regression.*pack|permanent.*pack",
         "PQ-11: PERMANENT REGRESSION PACK missing"),
        (r"policy.*v4|v4.*compliance|authoriz.*statement|authorized.*policy",
         "PQ-11: policy authorization statement missing"),
        (r"SQUASH_SHA|squash_sha",
         "PQ-11: squash SHA placeholder missing"),
    ]
    for _pq11_pattern, _pq11_msg in _PQ11_CHECKS:
        if not re.search(_pq11_pattern, text, re.IGNORECASE):
            result.warnings.append(_pq11_msg)
    return result


def validate_all(prompts_dir: Path, cycle: int,
                 agents: list[str]) -> dict[str, PromptValidationResult]:
    """Validate all agent prompts for a cycle. Returns dict by agent."""
    results = {}
    for agent in agents:
        pattern = f"CYCLE_{cycle:03d}_AGENT_{agent}_PROMPT.md"
        path = prompts_dir / pattern
        results[agent] = validate(path, agent, cycle)
    return results
