# ADR-012: Six-Agent Execution Order A → B+E → C → F → D

## Status
Accepted

## Context
The autonomous runner dispatches six Cursor agents per cycle. The execution order must
balance parallelism with dependency requirements. Agents that produce code (B) must run
before agents that validate that code (C, F). Agent E needs B's first commit to work from.
Agent D needs all other agents complete to build the PR body and fact bundles.

## Decision
The canonical execution order is:
  A  → runs first, no dependencies (PM_Pack state, docs, governance)
  B  → runs after A AGENT_COMPLETE (primary implementation)
  E  → runs after B makes its first commit (live validation, evidence)
  C  → runs after both B and E AGENT_COMPLETE (integration validation)
  F  → runs after C AGENT_COMPLETE (test coverage)
  D  → runs last, after all 5 AGENT_COMPLETE (PR steward, Jira, merge gate)

B and E are effectively parallel with the constraint that E polls for B's first commit
before beginning substantive work.

## Consequences
- Human dispatcher must follow this order; automated dispatch must enforce it.
- B and E can be dispatched near-simultaneously, saving wall-clock time.
- Agent D is the only agent that creates or updates the PR and posts Jira comments.
- No other agent may push a PR or post Jira cycle comments.
