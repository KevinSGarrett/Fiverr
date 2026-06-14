"""Verify exported ZIP artifacts are sanitized from sensitive content."""

from __future__ import annotations

import argparse
import sys
import zipfile

SENSITIVE_PATTERNS = [
    ".env",
    "runner.env",
    ".credentials",
    "storage_state",
    ".runner",
    "anthropic_api_key=",
    "jira_api_token=",
    "gh_automation_token=",
]


def verify_zip(zip_path: str) -> tuple[bool, list[str]]:
    """Return (clean, violations) for the provided zip file path."""
    violations: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            lower = name.lower()
            for pat in SENSITIVE_PATTERNS:
                if pat in lower:
                    violations.append(f"Sensitive path: {name} (matched: {pat})")
    return len(violations) == 0, violations


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify evidence export zip has no sensitive entries.")
    parser.add_argument("zip_path", nargs="?", help="Path to ZIP file to verify")
    parser.add_argument("--zip", dest="zip_flag", help="Path to ZIP file to verify (flag form)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    zip_path = args.zip_flag or args.zip_path
    if not zip_path:
        print("Usage: python automation/export_sanitizer_verify.py <zip_path>")
        return 1
    clean, violations = verify_zip(zip_path)
    if clean:
        print(f"PASS: {zip_path} is clean")
        return 0
    print(f"FAIL: {zip_path} contains sensitive content:")
    for violation in violations:
        print(f"  - {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
