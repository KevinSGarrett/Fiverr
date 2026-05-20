# JIRA-GITHUB INTEGRATION PROTOCOL
# Added: Cycle 019

---

## Overview

The Jira-GitHub integration is live and active. GitHub repository `KevinSGarrett/Fiverr` is connected to Jira project `SCRUM` at `kevinsgarrett.atlassian.net`. Backfill is complete from 2025-11-13.

**What this means:** Any branch, commit, or PR that contains a Jira key (e.g., `SCRUM-136`) will automatically appear in the Development panel on that Jira issue. No manual linking is required.

---

## How to Use the Integration

### Branch Names
Include the Jira key in the branch name:
```
feature/epic01/SCRUM-136-database-init     ← correct
cycle/019/integration                       ← correct (cycle branches, no key needed)
feature/db-init                             ← wrong — no Jira key
```

### Commit Messages
Include the Jira key anywhere in the commit message:
```
feat(models): SCRUM-136 add all 30 DB tables with FK constraints [Agent A]
fix(config): SCRUM-135 resolve validation error on empty niche list [Agent A]
```

### PR Titles and Bodies
Include Jira keys in the PR body under the "Jira Keys" section of the PR template. The integration will link the PR to all mentioned keys automatically.

---

## Verifying Links

1. Open any Jira story (e.g., SCRUM-136)
2. Look at the right sidebar — find the **Development** panel
3. You should see:
   - Branch names that include SCRUM-136
   - Commits with SCRUM-136 in their messages
   - PRs that mentioned SCRUM-136 in title or body
4. Click any item to jump directly to GitHub

---

## Integration Settings

| Setting | Value |
|---|---|
| Connection | GitHub Cloud |
| Organization | KevinSGarrett |
| Repository access | Only select repos — KevinSGarrett/Fiverr |
| Backfill status | Finished (from 2025-11-13) |
| Settings URL | https://kevinsgarrett.atlassian.net/jira/settings/apps/github |

---

## Rules for ChatGPT PM

1. Always specify Jira keys in branch naming conventions in agent prompts
2. Always include a "Jira Keys" section in every PR template instruction
3. After a PR merges, verify Development panel populated on key stories
4. If Development panel is empty despite correct key usage, check the integration health at the settings URL
5. Do NOT add manual PR links to Jira comments if the Development panel already shows the link — avoid duplication

---

## Rules for Cursor Agents

1. Always include the assigned story's Jira key in branch names you create
2. Always include the Jira key in commit messages for the story you are implementing
3. Do NOT rely solely on Jira comments for PR evidence — the Development panel is the primary link
4. After pushing a branch, verify it appears in the Development panel before reporting complete
