# Cycle 013 Corrective Rules

Cycle 013 preserves the improved Cycle 012 Cursor prompt quality. The next cycle must not regress to short prompts or PR-first planning.

## Active rule set

- Planning starts from Jira and source AC/DoD.
- PR #10 blockers are resolved before broad new feature work.
- Cursor agents may perform Jira operations when assigned.
- Per-agent work must include at least 20 substantive tasks, target 24-32, maximum 40.
- Every substantive task should include at least 100 words of implementation detail in generated prompts.
- Each agent prompt should be at least 6,000 words unless a task-count and prompt-detail waiver is explicitly documented.
- Product story Done is prohibited unless full source AC/DoD is complete.
- `.env` and generated artifacts must never be committed.

## Cycle 013 gate

PR #10 has green CI and Codecov project status, but it has unresolved Codex review threads. Therefore Cycle 013 starts as a PR #10 correction and reconciliation cycle.
