# Seed Data Guide

This guide documents seed payload expectations for `src/playbook/seed_guidance.py`.
`config.yaml` remains the source of truth for enabled niches and runtime settings.

## Required shape

- `niche_id`: lowercase slug using only `a-z`, `0-9`, and `_`
- `keywords`: list of non-empty strings
- Minimum keyword count: `6`
- Duplicate keywords are rejected (case-insensitive, trimmed)

## Valid payload example

```yaml
niche_id: prd_ai_saas
keywords:
  - product requirements document
  - ai saas prd
  - startup prd writer
  - mvp roadmap planning
  - feature prioritization consultant
  - product strategy documentation
```

## Common invalid payloads

Invalid: bad `niche_id` characters:

```yaml
niche_id: PRD-AI-SAAS
keywords:
  - one
  - two
  - three
  - four
  - five
  - six
```

Invalid: duplicate keywords (case-insensitive):

```yaml
niche_id: prd_ai_saas
keywords:
  - product requirements document
  - Product Requirements Document
  - startup prd writer
  - mvp roadmap planning
  - feature prioritization consultant
  - product strategy documentation
```

Invalid: too few keywords:

```yaml
niche_id: prd_ai_saas
keywords:
  - one
  - two
  - three
```

## Relationship to config.yaml

- Seed payloads should reference niche identifiers that align with the configured niche taxonomy.
- Seed payload validation does not modify `config.yaml`.
- Database import of seeds is intentionally not implemented in this foundation cycle.
