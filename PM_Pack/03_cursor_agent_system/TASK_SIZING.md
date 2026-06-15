# TASK SIZING — Work Volume Per Agent Per Cycle

Version: Cycle 079 governance alignment

---

## Binding Rule: Prompt Depth and Task Volume

Legacy 5-8 and 10-20 guidance is historical only. Active cycles must use the six-lane, 55-task governance floor.

## Required Per-Agent Task Volume

| Metric | Minimum | Target | Maximum |
|---|---:|---:|---:|
| Substantive tasks per agent | 55 | 55-70 | No hard cap with quality |
| Total substantive tasks per 6-agent cycle | 330 | 330-420 | No hard cap with quality |
| Agent prompt word count | 6,000 | 8,000-12,000 | No hard cap if organized |
| New/modified files per agent (when coding) | 8 | 12-30 | 50 |
| Jira operations per Jira-assigned agent | 5 | 8-20 | 40 |
| AC/DoD bullets referenced per agent | 20 | 30-60 | As needed |

## Substantive Task Definition (Required)

A task counts as substantive only if it contains all of the following:

1. Exact objective with measurable completion language.
2. Exact Jira key(s), or explicit `not_applicable_reason`.
3. Exact acceptance criteria and/or DoD bullet(s) being advanced.
4. Exact file paths or a clearly bounded Jira-only scope.
5. Deterministic implementation instructions (no guesswork language).
6. Validation expectation (test command, lint/type check, or Jira evidence action).
7. Final report expectation (what evidence must be written and where).

If any required element is missing, the item does not count.

## Excluded from Task Counts

The following do not count as standalone substantive tasks:

- one-line reminders or placeholders;
- "update relevant tickets" style directives;
- single formatting/comment-only edits without acceptance evidence;
- duplicated checklist bullets split out to inflate count;
- pure status notes that do not change source, docs, or Jira state.

These may appear as sub-steps under a substantive task, but never as separate countable tasks.

## Invalid Prompt Conditions

A prompt is invalid if any agent receives fewer than 55 substantive tasks unless both waivers are present and justified:

- `TASK-COUNT WAIVER`
- `PROMPT-DETAIL WAIVER`

A prompt is also invalid if it relies on vague instructions such as:

- "update Jira as needed";
- "continue previous work";
- "handle tests";
- "fix issues";
- "make improvements";
- "same as last cycle".

## Waiver Protocol (Both Waivers Required)

Waivers are permitted only for:

- emergency production hotfix;
- single blocking security incident;
- single blocking CI failure;
- single confirmed Codex blocker where more work increases risk;
- PM-declared safety cycle with explicit risk rationale.

### `TASK-COUNT WAIVER` must include:

1. Why 55+ substantive tasks are unsafe for this cycle.
2. Exact reduced count approved per agent.
3. Risk of normal scope versus reduced scope.
4. Named backfill cycle where deferred scope will be restored.

### `PROMPT-DETAIL WAIVER` must include:

1. Why 6,000+ words would reduce safety or clarity in this case.
2. Exact approved shortened range.
3. Section-by-section proof that AC/DoD, Jira, files, tests, and report requirements remain explicit.
4. PM sign-off statement that reduced prompt depth is temporary.

If either waiver block is missing, incomplete, or not cycle-specific, the prompt is rejected.

## Historical Language Handling

Any legacy references to 5-8 tasks, 10-20 tasks, or 20-40 tasks in PM Pack files must be updated or explicitly labeled as historical/non-binding context.
