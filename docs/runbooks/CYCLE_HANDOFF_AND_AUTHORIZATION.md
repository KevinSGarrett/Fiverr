# Cycle Handoff And Authorization Runbook

## Purpose

This runbook explains how Agent A authorizes downstream execution and how handoff evidence must be captured. It ensures authorization is based on verified prerequisites, not assumptions.

## Authorization Preconditions

Before authorizing B and E, confirm:
- Stage 1 evidence is complete
- all six prompts pass validation
- mandatory floor counts satisfy threshold
- cycle report includes truthful status for completed, partial, and blocked items

Authorization must not proceed when critical prerequisites are unresolved.

## Handoff Contents

A valid handoff includes branch state, validation command outcomes, unresolved blockers, and exact evidence file paths. Avoid broad statements like “all done” without artifact links.

## Truth-State Rules

If an item is externally blocked (missing secret, invalid key, unavailable issue key), label it blocked and include exact command output. If item ran but did not meet content criteria, label it partial. This prevents downstream agents from inheriting false assumptions.

## AGENT_COMPLETE Usage

`AGENT_COMPLETE` indicates the report is final for Agent A, not that every upstream objective is globally complete. The report must separate completed and unresolved work clearly to preserve governance integrity.

## Transition To Parallel Agents

Once preconditions pass, B and E may start in parallel according to cycle execution order. Any unresolved blockers that affect B/E scope must be explicitly called out to avoid duplicate investigation effort.

## Escalation

Escalate when authorization preconditions cannot be met due missing credentials, policy conflicts, or environment inconsistencies that require operator intervention.
