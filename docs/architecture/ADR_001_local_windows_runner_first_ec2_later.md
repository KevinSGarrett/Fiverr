# ADR-001 Local Windows Runner First, EC2 Later

## Status
ACCEPTED

## Context
The autonomous runner needed an execution host with immediate compatibility for existing paths, scripts, and authentication.

## Decision
Use local Windows runner first; add EC2 as future failover.

## Rationale
Current PM_Pack and scripts assume `C:\Fiverr\Fiverr`, PowerShell tooling, and local Cursor Desktop authentication. This minimizes migration cost and avoids early AWS spend.

## Consequences
The local machine must remain online and healthy. Until EC2 failover exists, this is a single-point-of-failure risk.

