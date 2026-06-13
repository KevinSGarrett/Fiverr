# Daily Report Format

Daily report generator output path:

`C:\AI_Runner\reports\daily\DAILY_YYYY-MM-DD.md`

Command source: `automation/ai_cycle_controller.py daily-report`

## Required Sections

## 1) Date and Status

Include date, controller status, active cycle, frozen state, and health level. This section answers, "what is the runner doing right now?"

## 2) Development Activity

List all build/modification activity for the day: commit SHAs, changed files, and test outcomes tied to those changes.

## 3) Validation Results

Summarize `ruff`, `mypy`, and `pytest` status with coverage percentage and floor compliance.

## 4) Jira Updates

Document issue comments, transitions, and created items. Include keys and intent so PM can audit flow quickly.

## 5) Repairs

Record repair loops triggered, what was repaired, and final disposition.

## 6) Incidents

List incidents written that day (`STUCK`, `DRIFT`, `DIRTY_REPO`, etc.), with severity and resolution state.

## 7) Model Status

Capture Cursor model verification state, Codex 5.3 confirmation, freshness age, and Claude status.

## 8) Post-Cycle Review Status

State last post-cycle review result and elapsed time since that review.

## 9) Next 24 Hours

List planned actions by agent/cycle/go-live stage with concrete command intent where possible.

## 10) Metrics

Include cumulative metrics:

- total cycles completed
- total PRs merged
- total incidents
- total repairs

## Idle-Day Rule (Mandatory)

A daily report must still be generated on idle days. Use `status = IDLE` and explicitly state "no development activity today" rather than skipping report generation. This preserves operational continuity and prevents false outage interpretation when the system is intentionally paused.

## Formatting Rules

- Use one heading per required section in fixed order.
- Keep all timestamps in UTC with ISO format.
- Include direct file paths for artifacts and evidence.
- Include command snippets only when relevant to explain validation or recovery.
- Mark unknown values as `NOT_AVAILABLE` rather than leaving blanks.

## Minimum Content Expectations

Each daily report should be readable by a PM without opening additional files. Include enough detail to answer:

1. What changed today?
2. Was the system healthy?
3. Were there incidents or repairs?
4. What happens next?

This ensures idle days are still informative and active days remain auditable.

