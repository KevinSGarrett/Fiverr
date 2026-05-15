# PM Corrective Rules — Cycle 012

## Binding corrective finding

Cycle 012 audit confirms the operator concern was valid: Jira is being updated, but the workflow is still not fully board-first or acceptance-criteria/DoD-first across the full 250+ item SCRUM backlog. The prior process improved changed-file mapping, but it still allowed implementation to be planned from GitHub/PR deltas and then mapped back to Jira afterward.

## Non-negotiable correction

From Cycle 012 forward, Jira is the primary planning source before code work starts.

A cycle is incomplete unless it includes:

1. Broad Jira board inventory before agent work is assigned.
2. Issue-type and status summary for the board or the relevant backlog slice.
3. Exact Jira issues selected for the cycle before coding begins.
4. Acceptance Criteria and Definition of Done bullets copied into each agent task.
5. File ownership mapped to Jira issues before implementation.
6. Every touched Jira issue updated with AC/DoD progress after implementation.
7. Product stories updated alongside governance tickets.
8. Done status used only when full story DoD is satisfied.
9. PR body containing Jira mapping table and AC/DoD status table.
10. PM response containing Jira board audit summary, not only cycle-ticket updates.

## Binding Enforcement Rules

1. Every prompt must list exact Jira keys, AC bullets, DoD bullets, files, tests, and final report path.
2. Every task must embed AC/DoD bullets directly; top-level references alone are insufficient.
3. Every PM response must include board-audit findings or explicit scope-limit rationale.
4. Every cycle must check for uncommitted local work not represented in the live PR before merge.
5. Governance/cycle tickets may not replace product-story updates when product artifacts changed.
6. Cursor agents assigned Jira work may update Jira directly, but must cite exact keys and DoD status.
7. Any vague Jira instruction ("update relevant tickets", "handle Jira as needed") fails review.
8. Shallow prompts are rejected even if they superficially pass template formatting checks.

## Doubled task and prompt-depth rule

The Cycle 010 task sizing is superseded.

Normal Cursor-agent prompts must now use:

- Minimum: 20 substantive tasks per agent.
- Preferred target: 24–32 substantive tasks per agent.
- Maximum: 40 substantive tasks per agent.
- Minimum prompt length: 6,000 words per agent prompt.
- Preferred prompt length: 8,000–12,000 words per agent prompt.
- No hard cap when the prompt remains organized, navigable, and useful.

Any shorter prompt must include both:

- `TASK-COUNT WAIVER`
- `PROMPT-DETAIL WAIVER`

The waiver must explain why reduced scope is safer than the normal high-volume standard.

Both waiver blocks are mandatory for reduced prompts:

- `TASK-COUNT WAIVER`
- `PROMPT-DETAIL WAIVER`

If either waiver is missing, the cycle prompt fails corrective compliance.

## Cursor-agent Jira authority

Cursor agents may perform Jira work when explicitly assigned:

- search Jira issues;
- read issue details;
- create issues;
- comment on issues;
- transition issues;
- update issue fields where appropriate;
- maintain Jira mapping evidence;
- update AC/DoD ledgers.

They must still follow PM governance:

- never mark a broad product story Done for partial implementation;
- never close AC/DoD bullets without evidence;
- never update unrelated Jira issues;
- never use governance tickets as substitutes for product story updates.

## Cycle 012 merge-gate correction

PR #9 is open and green, but uploaded local archive contains uncommitted Agent C work not represented in live PR #9. Cycle 012 must reconcile this before merge.

The Integration/GitHub Steward must either:

1. commit/push the intended local Agent C work into PR #9 with validation and Jira mapping, or
2. document that the local changes are intentionally out of scope and safely discarded/stashed.

No PR #9 merge before this is resolved.
