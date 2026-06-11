"""
secret_guard.py — Scan staged/changed files for secrets before commit.
Blocks commits containing .env values, tokens, private keys, or browser sessions.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path("C:/Fiverr/Fiverr")

# File patterns that should never be committed
DANGEROUS_FILE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"storage_state\.json",
    r"playwright/\.auth",
    r"\.pem$",
    r"\.key$",
    r"private_key",
    r"client_secret",
    r"serviceaccount.*\.json",
    r"data/.*\.db$",
    r"coverage\.xml$",
    r"\.sqlite$",
    r"playwright-state",
]

# Content patterns that indicate secrets inside files
SECRET_CONTENT_PATTERNS = [
    (r"ANTHROPIC_API_KEY\s*=\s*sk-", "Anthropic API key value"),
    (r"api_key\s*=\s*['\"][a-zA-Z0-9_\-]{20,}", "API key value"),
    (r"password\s*=\s*['\"][^'\"]{8,}", "password value"),
    (r"secret\s*=\s*['\"][^'\"]{8,}", "secret value"),
    (r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----", "private key"),
    (r"gh[pousr]_[A-Za-z0-9]{36}", "GitHub token"),
    (r"xoxb-|xoxp-|xoxa-", "Slack token"),
    (r"JIRA_API_TOKEN\s*=\s*[A-Za-z0-9]{20,}", "Jira API token value"),
]


@dataclass
class SecretGuardResult:
    passed: bool = True
    findings: list[str] = field(default_factory=list)
    dangerous_files: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return "SECRET GUARD PASS - no secrets detected"
        lines = ["SECRET GUARD FAIL:"]
        for f in self.dangerous_files:
            lines.append(f"  DANGEROUS FILE: {f}")
        for f in self.findings:
            lines.append(f"  FINDING: {f}")
        return "\n".join(lines)


def scan_staged(cwd: Path = REPO_ROOT) -> SecretGuardResult:
    """Scan all staged files for dangerous patterns."""
    result = SecretGuardResult()

    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(cwd), capture_output=True, text=True
    )
    staged_files = [f.strip() for f in r.stdout.splitlines() if f.strip()]

    for fname in staged_files:
        # Check filename patterns
        for pattern in DANGEROUS_FILE_PATTERNS:
            if re.search(pattern, fname, re.IGNORECASE):
                result.dangerous_files.append(fname)
                result.passed = False
                break

    # Check file contents for secret values
    for fname in staged_files:
        if fname in result.dangerous_files:
            continue
        try:
            full = cwd / fname
            if full.exists() and full.stat().st_size < 500_000:  # skip large files
                content = full.read_text(encoding="utf-8", errors="replace")
                for pattern, desc in SECRET_CONTENT_PATTERNS:
                    if re.search(pattern, content):
                        result.findings.append(f"{fname}: {desc}")
                        result.passed = False
        except Exception:
            pass

    return result


def scan_working_tree(cwd: Path = REPO_ROOT) -> SecretGuardResult:
    """Scan all tracked+modified files (not just staged)."""
    result = SecretGuardResult()
    r = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(cwd), capture_output=True, text=True
    )
    for line in r.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            fname = parts[1].strip()
            for pattern in DANGEROUS_FILE_PATTERNS:
                if re.search(pattern, fname, re.IGNORECASE):
                    result.dangerous_files.append(fname)
                    result.passed = False
    return result
