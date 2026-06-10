# GENERATE_PLAYBOOK_SPEC

## Core Function Contracts

### `generate_playbook(niche_id, db, config) -> dict`
Must return:
- `niche_id`, `niche_name`, `generated_at`, `keyword_used`, `has_full_data`, `sections`

Rules:
- `has_full_data=True` only when a completed recommendation exists.
- Sections order is fixed:
  1. `account_setup`
  2. `gig_creation`
  3. `first_5_orders`
  4. `review_acquisition`
  5. `ongoing_optimization`
- Never raises on empty DB/config or recommendation miss.

### `export_playbook_markdown(playbook) -> str`
- Starts with markdown heading (`#`).
- Includes all five section names.

### `export_playbook_pdf(playbook, output_path) -> None`
- Uses Jinja2 + WeasyPrint.
- Raises `ImportError` with install guidance if dependency missing.

### `render_playbook_section(niche_id, db)`
- Uses proper session management.
- Handles empty and populated data paths.

### `build_account_setup_section(...)`
- Exactly 7 steps.
- First step priority is `CRITICAL`.

### `build_gig_creation_section(...)`
- Exactly 8 steps.
- Step 8 has `checklist` list.

### `build_first_5_orders_section(...)`
- Exactly 4 strategies.
- First strategy `type == "PRIMARY"`.
- `delivery_excellence_tips` list length >= 4.

### `build_review_strategy_section(...)`
- Exactly 3 strategies.
- First strategy template string length > 20.

### `build_ongoing_optimization_section(...)`
- Exactly 4 milestones.
- Each milestone has non-empty `actions` list.
- Graceful behavior with empty pricing dict.

## Acceptance Criteria (9)
- One AC per function above.

## Test Requirement
- `test_playbook_generator.py` has 32+ tests across 5+ classes.

## Production Readiness
Implements Wave 11 S8.3 scaffolding and live `has_full_data` branch.
