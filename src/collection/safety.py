"""Read-only safety guardrails for future collection actions."""

from __future__ import annotations

SAFE_COLLECTION_MODES = {
    "manual_snapshot",
    "operator_review",
    "authenticated_read_only",
    "unauthenticated_read_only",
}

FORBIDDEN_COLLECTION_ACTIONS = {
    "purchase",
    "message_seller",
    "click_order_button",
    "submit_form",
    "mutate_account",
}


def validate_collection_action(action_name: str) -> bool:
    """Validate that an action is safe for read-only collection flows."""
    normalized_name = action_name.strip().lower()
    if not normalized_name:
        raise ValueError("Collection action name must not be empty.")

    if normalized_name in FORBIDDEN_COLLECTION_ACTIONS:
        raise ValueError(
            f"Forbidden collection action '{action_name}' blocked by read-only safety policy."
        )
    return True
