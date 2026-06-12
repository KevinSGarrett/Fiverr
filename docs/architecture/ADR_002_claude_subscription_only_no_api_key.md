# ADR-002 Claude Subscription Only, No API Key

## Status
ACCEPTED

## Context
PM review could use API-key billing or subscription-backed access.

## Decision
Use subscription-only access; block API-key mode for PM review.

## Rationale
This keeps billing and identity aligned with human PM usage and reduces unmanaged token risk.

## Consequences
Subscription limits can pause review throughput. EC2-based PM review requires separate subscription verification before use.

