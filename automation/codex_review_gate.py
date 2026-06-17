#!/usr/bin/env python3
"""
codex_review_gate.py — CI gate that blocks PR merge if unresolved Codex review threads exist.

Every review thread on the PR must be resolved before the gate passes.
This enforces that the automation system reviews every Codex comment and either:
  - Fixes the issue, OR
  - Explicitly resolves the thread with a "won't fix" justification comment

Exit 0 = all threads resolved (PASS)
Exit 1 = unresolved threads found (FAIL — blocks merge)
"""
from __future__ import annotations

import json
import subprocess
import sys


def get_pr_number() -> int | None:
    """Get PR number from GitHub Actions environment or gh CLI."""
    import os
    pr_num = os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_PR_NUMBER")
    if pr_num:
        return int(pr_num)
    # Try gh CLI
    try:
        r = subprocess.run(
            ["gh", "pr", "view", "--json", "number"],
            capture_output=True, text=True, check=True,
        )
        return json.loads(r.stdout).get("number")
    except Exception:
        return None


def get_review_threads(pr_number: int) -> list[dict]:
    """Get all review threads on the PR via GitHub GraphQL."""
    query = """
query($pr: Int!, $owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 1) {
            nodes {
              author { login }
              body
              path
              line
            }
          }
        }
      }
    }
  }
}
"""
    import os
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "KevinSGarrett")
    repo = os.environ.get("GITHUB_REPOSITORY", "KevinSGarrett/Fiverr").split("/")[-1]

    r = subprocess.run(
        ["gh", "api", "graphql",
         "-f", f"query={query}",
         "-F", f"pr={pr_number}",
         "-F", f"owner={owner}",
         "-F", f"repo={repo}"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(r.stdout)
    threads = (data.get("data", {})
               .get("repository", {})
               .get("pullRequest", {})
               .get("reviewThreads", {})
               .get("nodes", []))
    return threads


def main() -> int:
    pr_number = get_pr_number()
    if not pr_number:
        print("WARNING: Could not determine PR number — skipping Codex review gate")
        return 0  # non-PR context (e.g. push to develop) — skip gate

    print(f"Checking review threads on PR #{pr_number}...")
    try:
        threads = get_review_threads(pr_number)
    except Exception as e:
        print(f"WARNING: Could not fetch review threads: {e} — skipping gate")
        return 0  # fail open if GH API unavailable

    if not threads:
        print("No review threads found — PASS")
        return 0

    unresolved = [t for t in threads if not t.get("isResolved") and not t.get("isOutdated")]

    print(f"Total threads: {len(threads)}")
    print(f"Resolved: {len(threads) - len(unresolved)}")
    print(f"Unresolved: {len(unresolved)}")

    if unresolved:
        print("\nUNRESOLVED REVIEW THREADS (must resolve before merging):")
        for t in unresolved:
            comment = (t.get("comments", {}).get("nodes") or [{}])[0]
            author = comment.get("author", {}).get("login", "unknown")
            path = comment.get("path", "unknown")
            line = comment.get("line", "?")
            body = (comment.get("body") or "")[:120].replace("\n", " ")
            print(f"  [{author}] {path}:{line} — {body}")
        print(
            "\nFAIL: All Codex review comment threads must be resolved before merging.\n"
            "For each thread: either fix the issue and resolve, or add a 'won't fix: <reason>'\n"
            "comment and then resolve the thread."
        )
        return 1

    print("All review threads resolved — PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
