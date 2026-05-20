# PM Corrective Rules — Cycle 019

## What This Covers

Rules derived from audit findings and remediation in Cycle 019. These correct recurring errors and add new standards.

---

## CR-019-01: Label Format Change

**OLD (deprecated):** agent:A, agent:B, agent:C, agent:D
**NEW (required):** agent:1-infrastructure, agent:2-collection, agent:3-analysis, agent:4-dashboard

All new Jira tickets and PRs must use the new label format. Old format labels still exist on historical tickets — do not retroactively update them unless they are actively being worked.

---

## CR-019-02: PR Title Hard Constraints

PR titles MUST satisfy ALL of these or pr-checks.yml will block the merge:
1. ≤72 characters total
2. Match regex: `^(feat|fix|refactor|test|docs|chore|style|perf|ci|build|release|hotfix|revert)(\([a-z0-9-]+\))?: .+$`
3. No em-dash (—) — ASCII hyphen (-) only
4. No trailing period
5. Scope in parentheses must be lowercase alphanumeric with hyphens only

The PM is responsible for specifying the correct PR title in the cycle reply. Agents do not choose their own PR title.

---

## CR-019-03: Large-PR Override Required for Batch PRs

Any PR exceeding 1000 lines changed requires the `override:large-pr` label to be applied BEFORE the PR is opened (or before CI re-runs on it). The PM must instruct the operator to add this label. Agents cannot self-authorize this override.

---

## CR-019-04: Jira Sprint Assignment is Mandatory

Every story worked in a cycle MUST be assigned to the active sprint in Jira before agent work begins. The PM must explicitly call out the sprint assignment in the cycle reply. "Assign SCRUM-136 to sprint Cycle 020" is a required action, not optional.

---

## CR-019-05: Verify GitHub Development Panel After Merge

After every merge, the PM must verify that Jira stories show linked PRs and commits in their Development panel. If the Development panel is empty:
1. Check that the branch/commit contained the Jira key
2. Check integration health at: https://kevinsgarrett.atlassian.net/jira/settings/apps/github
3. Report the gap if the integration is broken

---

## CR-019-06: Both Jira Transitions AND GitHub Evidence Required

When marking a story Done in Jira, BOTH of these must exist:
1. Jira status = Done
2. GitHub Development panel shows at least one linked commit or PR

Text comments in Jira are NOT sufficient evidence alone. The Development panel link is the primary evidence artifact for any story with merged code.

---

## CR-019-07: Dependabot PRs Are Never Mixed with Cycle Work

Dependabot PRs (weekly automatic dependency updates) must NEVER be merged into a cycle integration branch. They are always handled as standalone PRs. The PM must check for open Dependabot PRs after every cycle merge and handle them separately per DEPENDABOT_PROTOCOL.md.
