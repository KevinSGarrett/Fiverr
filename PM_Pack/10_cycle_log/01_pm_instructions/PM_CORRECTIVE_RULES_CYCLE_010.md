# PM Corrective Rules — Cycle 010

## New rule 1: Cursor agents may operate Jira when assigned

The operator confirmed that Cursor agents have full read/write/edit access to Jira. The PM Pack must treat Jira as an available execution surface for Cursor agents, not PM-only work.

When useful, agent prompts may assign:

- Jira read/audit tasks,
- Jira issue creation,
- Jira comments,
- Jira status transitions,
- Jira mapping evidence,
- Jira rework/bug ticket creation.

## New rule 2: Task volume is doubled

The prior target of 5-8 tasks per agent is superseded.

New normal task volume:

- Minimum: 10 substantive tasks per agent.
- Target: 12-16 substantive tasks per agent.
- Maximum: 20 substantive tasks per agent.

A prompt below 10 tasks requires a visible `TASK-COUNT WAIVER`.

## New rule 3: Jira authority does not loosen DOD rules

Cursor agents may update Jira, but must not over-close work:

- partial story work -> In Progress,
- PR-ready + checks passing -> In Review,
- full source DOD satisfied + merged -> Done,
- governance implementation completed -> Done only after merged or otherwise verified.

## New rule 4: Every prompt must name Jira responsibilities

Every agent prompt must say one of:

- "You must perform the following Jira operations..."
- "You may perform Jira operations only for blockers..."
- "Do not perform Jira operations; report required updates only."

No vague Jira instruction is allowed.
