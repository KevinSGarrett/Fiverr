# Destructive Actions Policy

This policy defines actions that are permanently blocked or conditionally blocked in autonomous operation. The purpose is to protect source history, operational evidence, and in-flight work from irreversible loss.

## Forever Blocked Actions

1. `git reset --hard` on shared branches.
2. `git checkout -- .` mass discard.
3. `git clean -fd` blind cleanup.
4. force push to `main` or protected branches.
5. deleting incident evidence to hide failures.
6. broad process kills that impact unrelated workloads (for example, killing all `node.exe` processes).

## Conditionally Restricted Actions

- File-level discard (`git checkout -- <file>`) is allowed only after classification and evidence capture.
- Branch deletion is allowed only for merged ephemeral branches, never active cycle branches.
- Runner/service restarts are allowed when incidents are documented.

## Required Pre-Action Checks

Before any potentially destructive action:

1. run `git status --short`
2. run `git diff --stat HEAD`
3. classify changed files (AGENTWORK, UNEXPECTED, CRASHRESIDUE, INTENTIONAL)
4. capture incident evidence if state is suspicious

## Recovery-First Principle

If unsure, preserve first:

- stash with explicit label
- copy suspicious files to incident folder
- document decision rationale

## Enforcement and Escalation

Any attempt to bypass this policy should block autonomous progression and raise a governance incident. Repeated violations trigger manual control mode until operator review confirms stability and compliance.

