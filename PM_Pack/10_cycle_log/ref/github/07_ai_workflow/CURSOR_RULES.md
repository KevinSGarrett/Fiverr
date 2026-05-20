# CURSOR RULES — DEPLOYED STATE
# Updated: Cycle 019

---

## Status

`.cursorrules` is deployed at the repo root (`C:\Fiverr\Fiverr\.cursorrules`). This file is automatically loaded by Cursor IDE for all agents working in the project.

---

## Key Rules from Deployed .cursorrules

### Code Style
- Line length: **100 characters** (not 120 — see DL-029)
- Formatter: Ruff
- Type checker: Mypy (strict mode)
- All public functions must have complete type annotations
- Docstrings required for all public functions and classes

### File Organization
- New DB models: one model per new file (existing consolidated files accepted per DL-025)
- New collection workflows: class files in `src/collection/workflows/`
- New utility functions: add to appropriate `src/utils/{module}.py`
- New Jinja2 templates: operational templates in `src/llm/prompts/` (no renaming of existing)

### Jinja2 Templates (DL-026)
Two sets coexist — do NOT rename or delete either set:
- **Set 1 (19 operational templates):** Used by E02/E03/E06/E07 stages
- **Set 2 (13 E05 spec-named templates):** Used by recommendation engine (gig_titles.j2, tag_sets.j2, package_structure.j2, description_outline.j2, faq_entries.j2, differentiation_angle.j2, buyer_persona.j2, thumbnail_direction.j2, upsell_structure.j2, red_flags.j2, niche_viability.j2, pricing_strategy.j2, profile_optimization.j2)

### Testing
- Every new module must have a corresponding test file in `tests/unit/`
- Minimum 80% coverage on any new module
- All tests must pass locally before committing
- Use fixtures from `tests/conftest.py` — no manual DB sessions in tests

### Git / Branch
- Commit format: `{type}({scope}): {description} [Agent {N}]`
- Integration branches: `cycle/{NNN}/integration` — scope is `cycle-{NNN}`
- Story branches: `feature/epic{NN}/SCRUM-{key}-{slug}` — scope is module name
- Always include Jira key in story branch names and commit messages

### Agent-Specific Directory Ownership
- Agent A (Infrastructure): src/config/, src/models/, src/utils/, src/recommendations/, .github/
- Agent B (Collection): src/collection/ (all subdirs)
- Agent C (Analysis): src/analysis/, src/scoring/, src/llm/, src/pricing/, src/discovery/
- Agent D (Dashboard): src/dashboard/, src/playbook/, src/reports/, src/exports/

---

## Updating .cursorrules

If a rule needs to change:
1. Create a decision log entry (DL-XXX) documenting the change and rationale
2. Update the `.cursorrules` file in the repo
3. Update this file to match
4. Inform all agents of the change in the next cycle prompt

Never change `.cursorrules` without a corresponding decision log entry.
