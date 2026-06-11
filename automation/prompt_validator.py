"""
prompt_validator.py — Validate generated Cursor agent prompts before dispatch.
A prompt that fails validation is never handed to Cursor.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Sections every prompt must contain
REQUIRED_SECTIONS = [
    "## 1. Identity",
    "## 2.",             # model requirement
    "## 3.",             # repo root
    "## 4.",             # branch
    "## 5.",             # PM_Pack files
    "## 6.",             # mission
    "## 7.",             # jira scope
    "## 9.",             # tasks
    "## 10.",            # validation commands
    "## 11.",            # stop conditions
    "## 13.",            # git instructions
    "## 14.",            # final report path
    "Autonomy rule",
]

# Patterns that indicate a stub / incomplete prompt
STUB_PATTERNS = [
    r"\[STUB",
    r"populate from PM_Pack",
    r"\[TODO\]",
    r"<exact agent mission>",
    r"<copy concise",
]

# Required content checks
REQUIRED_CONTENT = [
    (r"cycle/\d+/integration", "branch reference"),
    (r"C:\\\\Fiverr\\\\Fiverr|C:/Fiverr/Fiverr", "repo root"),
    (r"SCRUM-\d+|Jira|jira", "Jira reference"),
    (r"docs/cycle_reports/CYCLE_\d+", "report path"),
    (r"ruff|mypy|pytest", "validation commands"),
]

MIN_LINE_COUNT = 80   # prompts under this are likely stubs


@dataclass
class PromptValidationResult:
    prompt_path: str
    agent: str
    cycle: int
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"Prompt validation {status}: {self.prompt_path}"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN : {w}")
        return "\n".join(lines)


def validate(prompt_path: str | Path, agent: str, cycle: int) -> PromptValidationResult:
    """Validate a single prompt file. Returns PromptValidationResult."""
    result = PromptValidationResult(
        prompt_path=str(prompt_path), agent=agent, cycle=cycle, passed=True
    )

    path = Path(prompt_path)
    if not path.exists():
        result.passed = False
        result.errors.append(f"Prompt file does not exist: {path}")
        return result

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Line count gate
    if len(lines) < MIN_LINE_COUNT:
        result.passed = False
        result.errors.append(
            f"Prompt too short: {len(lines)} lines (minimum {MIN_LINE_COUNT})"
        )

    # Check for stub patterns
    for pat in STUB_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            result.passed = False
            result.errors.append(f"Stub pattern found: {pat}")

    # Required sections
    for section in REQUIRED_SECTIONS:
        if section not in text:
            result.warnings.append(f"Missing section: {section!r}")

    # Required content patterns
    for pattern, description in REQUIRED_CONTENT:
        if not re.search(pattern, text, re.IGNORECASE):
            result.warnings.append(f"Missing content: {description}")

    # Cycle number must match
    cycle_in_prompt = re.search(r"CYCLE[_ ]?(\d+)", text, re.IGNORECASE)
    if cycle_in_prompt:
        found_cycle = int(cycle_in_prompt.group(1))
        if found_cycle != cycle:
            result.passed = False
            result.errors.append(
                f"Cycle mismatch: prompt says {found_cycle}, expected {cycle}"
            )
    else:
        result.warnings.append("Could not detect cycle number in prompt")

    # Agent ID must match
    if f"Agent {agent}" not in text and f"AGENT_{agent}" not in text.upper():
        result.warnings.append(f"Agent {agent} not clearly identified in prompt")

    # Safety: no main branch
    if re.search(r"\bpush.*main\b|\bdeploy.*main\b", text, re.IGNORECASE):
        result.passed = False
        result.errors.append("Prompt contains push/deploy to main — blocked")

    # Safety: no secrets
    if re.search(r"api_key\s*=|secret\s*=|password\s*=|ANTHROPIC_API_KEY", text):
        result.passed = False
        result.errors.append("Potential secret value in prompt — blocked")

    # Degrade warnings to errors if too many
    if len(result.warnings) > 6:
        result.passed = False
        result.errors.append(
            f"{len(result.warnings)} warnings exceeded threshold — prompt likely incomplete"
        )

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
