"""Central selector registry for read-only collection workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SelectorEntry:
    """Selector definition with fallback metadata."""

    name: str
    css_candidates: tuple[str, ...]
    xpath_candidates: tuple[str, ...] = ()
    description: str = ""
    required: bool = False
    fallback_priority: int = 0
    verified: bool = False

    def has_candidates(self) -> bool:
        return bool(self.css_candidates or self.xpath_candidates)


SELECTOR_REGISTRY: dict[str, tuple[SelectorEntry, ...]] = {
    "search_results": (
        SelectorEntry(
            name="search_result_cards",
            css_candidates=(
                "article[data-testid='gig-card']",
                "div[data-testid='gig-card']",
                "section[data-gig-id]",
            ),
            description="Search result cards shown in keyword result pages.",
            required=True,
            fallback_priority=1,
            verified=False,
        ),
        SelectorEntry(
            name="search_result_title_link",
            css_candidates=("a[href*='/services/']", "a[data-testid='gig-title-link']"),
            description="Primary title anchor that opens gig details.",
            required=True,
            fallback_priority=2,
            verified=False,
        ),
    ),
    "gig_detail": (
        SelectorEntry(
            name="gig_title",
            css_candidates=("h1[data-testid='gig-title']", "h1"),
            description="Gig detail page title heading.",
            required=True,
            fallback_priority=1,
            verified=False,
        ),
        SelectorEntry(
            name="gig_description",
            css_candidates=("div[data-testid='gig-description']", "section[data-testid='description']"),
            description="Gig detail description text container.",
            required=False,
            fallback_priority=2,
            verified=False,
        ),
    ),
    "seller_profile": (
        SelectorEntry(
            name="seller_name",
            css_candidates=("h1[data-testid='seller-name']", "h1[class*='seller']"),
            description="Seller display name on profile pages.",
            required=True,
            fallback_priority=1,
            verified=False,
        ),
        SelectorEntry(
            name="seller_level",
            css_candidates=("span[data-testid='seller-level']", "div[class*='level']"),
            description="Seller level badge text.",
            required=False,
            fallback_priority=2,
            verified=False,
        ),
    ),
    "autocomplete": (
        SelectorEntry(
            name="search_input",
            css_candidates=("input[role='combobox']", "input[name='query']"),
            description="Search input used for autocomplete suggestions.",
            required=True,
            fallback_priority=1,
            verified=False,
        ),
        SelectorEntry(
            name="autocomplete_list_items",
            css_candidates=("ul[role='listbox'] li", "div[data-testid='autocomplete-option']"),
            description="Autocomplete suggestion rows.",
            required=True,
            fallback_priority=2,
            verified=False,
        ),
    ),
    "navigation": (
        SelectorEntry(
            name="next_page_button",
            css_candidates=("a[aria-label='Next']", "button[aria-label='Next page']"),
            xpath_candidates=("//a[contains(@aria-label, 'Next')]",),
            description="Pagination next-page control.",
            required=True,
            fallback_priority=1,
            verified=False,
        ),
        SelectorEntry(
            name="breadcrumb_root",
            css_candidates=("nav[aria-label='Breadcrumb']", "ol.breadcrumb"),
            description="Generic breadcrumb navigation region.",
            required=False,
            fallback_priority=2,
            verified=False,
        ),
    ),
}


def list_selector_groups() -> list[str]:
    """Return all selector group names sorted alphabetically."""

    return sorted(SELECTOR_REGISTRY)


def get_selector_group(group_name: str) -> tuple[SelectorEntry, ...]:
    """Return selector entries for a group."""

    if group_name not in SELECTOR_REGISTRY:
        raise KeyError(f"Unknown selector group: {group_name}")
    return SELECTOR_REGISTRY[group_name]


def explain_missing_required_selectors(
    registry: Mapping[str, Sequence[SelectorEntry]] | None = None,
) -> list[str]:
    """Describe required selector issues in a registry."""

    active_registry = registry or SELECTOR_REGISTRY
    messages: list[str] = []
    for group_name, entries in active_registry.items():
        required_entries = [entry for entry in entries if entry.required]
        if not required_entries:
            messages.append(f"Group '{group_name}' has no required selectors.")
            continue
        for entry in required_entries:
            if not entry.has_candidates():
                messages.append(
                    f"Required selector '{entry.name}' in '{group_name}' has no candidates."
                )
    return messages


def validate_selector_registry(
    registry: Mapping[str, Sequence[SelectorEntry]] | None = None,
) -> list[str]:
    """Validate selector registry structure and fallback metadata."""

    active_registry = registry or SELECTOR_REGISTRY
    messages: list[str] = []
    if not active_registry:
        return ["Selector registry is empty."]

    for group_name, entries in active_registry.items():
        if not entries:
            messages.append(f"Group '{group_name}' is empty.")
            continue
        seen_names: set[str] = set()
        for entry in entries:
            if entry.name in seen_names:
                messages.append(f"Group '{group_name}' has duplicate selector '{entry.name}'.")
            seen_names.add(entry.name)
            if entry.fallback_priority < 0:
                messages.append(
                    f"Selector '{entry.name}' in '{group_name}' has negative fallback priority."
                )
            if not entry.has_candidates():
                messages.append(f"Selector '{entry.name}' in '{group_name}' has no candidates.")

    messages.extend(explain_missing_required_selectors(active_registry))
    return messages
