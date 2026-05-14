# Seed Data Guide

This guide documents seed payload expectations for `src/playbook/seed_guidance.py`.
`config.yaml` remains the source of truth for enabled niches and runtime settings.
Seed payloads preserve keyword lineage, and the database stores imported records.

## Required shape

- `niche_id`: lowercase slug using only `a-z`, `0-9`, and `_`
- `keywords`: list of non-empty strings
- `source_lineage`: mapping with non-empty `source` and `method`
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
source_lineage:
  source: config_seed
  method: manual_curation
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
source_lineage:
  source: config_seed
  method: manual_curation
```

## Relationship to config.yaml

- `config.yaml` stores niche configuration and runtime settings.
- Seed payloads should reference configured `niche_id` values and include lineage context.
- Seed payload validation does not modify `config.yaml`.
- Database import of seeds is intentionally not implemented in this foundation cycle.

Configured niche IDs in `config.yaml` (Cycle 003):

- `prd_ai_saas`
- `support_kb_readiness`
- `gumloop_lindy_workflow`
- `mcp_ai_agent`
- `python_automation`
- `ai_tool_llm_integration`
- `ai_agent_development`
- `workflow_automation`
- `python_web_scraping`
