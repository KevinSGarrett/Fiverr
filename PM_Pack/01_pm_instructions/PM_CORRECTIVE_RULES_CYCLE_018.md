# PM Corrective Rules — Cycle 018

## Board-Audited Product Planning

Cycle 018 must use the board audit as a planning guardrail. The PM and Cursor agents must not treat starter issues, duplicate/noncanonical historical epics, or future To Do stories as current sprint work unless the prompt explicitly selects them.

## Canonical Board Control

- Canonical product epics: SCRUM-16 through SCRUM-25.
- Starter/sample issues SCRUM-1 through SCRUM-4 are not product planning sources.
- Duplicate/noncanonical Done issues SCRUM-27 through SCRUM-42 should not be active parents.
- Duplicate Done dashboard stories SCRUM-217, SCRUM-221, and SCRUM-222 require audit handling through SCRUM-257, not blind reopening or blind closure.
- Future scopes such as Scoring, Recommendation, Pricing, Discovery, and Playbook remain future backlog unless explicitly selected.

## Product-Forward Constraint

Cycle 018 may include board reconciliation, but only as a controlled substream. The main cycle remains product-forward: merge PR #14 if safe, then advance runtime dashboard acceptance, integration validation, data integrity, resilience, performance, all-9-niche config validation, first-run readiness, logging/monitoring, and security/data hygiene.

## Prompt Quality Gate

Every generated agent prompt must include at least 20 substantive tasks and 6,000+ words unless a formal waiver is documented. Each task must include Jira scope, AC/DoD mapping, implementation detail, validation expectations, and report/Jira evidence instructions.
