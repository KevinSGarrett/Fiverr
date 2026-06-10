# SECTION_BUILDERS_ACCEPTANCE_CRITERIA

## `build_account_setup_section`
- AC-1 returns dict with `steps` containing exactly 7 items.
- AC-2 `steps[0].priority` contains `CRITICAL`.
- AC-3 supports empty niche id with fallback naming.

## `build_gig_creation_section`
- AC-1 returns dict with `steps` containing exactly 8 items.
- AC-2 `steps[7].checklist` is a list.
- AC-3 supports `None` recommendation safely.

## `build_first_5_orders_section`
- AC-1 returns dict with `strategies` containing exactly 4 items.
- AC-2 `strategies[0].type == "PRIMARY"`.
- AC-3 `delivery_excellence_tips` list length >= 4.
- AC-4 works with empty pricing dict.

## `build_review_strategy_section`
- AC-1 returns dict with `strategies` containing exactly 3 items.
- AC-2 first strategy has `template` with length > 20.
- AC-3 accepts any niche id string.

## `build_ongoing_optimization_section`
- AC-1 returns dict with `milestones` containing exactly 4 items.
- AC-2 each milestone has `actions` list length >= 1.
- AC-3 handles empty pricing dict without `KeyError`.

## `get_niche_name`
- AC-1 maps all 9 production niche ids to display names.
- AC-2 unknown niche fallback returns non-empty string.

## `generate_playbook`
- AC-1 never raises across empty/None/error input combos.
- AC-2 always returns dict with exactly 5 sections.
- AC-3 `has_full_data=True` only when recommendation exists.

## Test Mapping Requirement
Every AC above must map to a named test in `tests/unit/test_playbook_generator.py`.
