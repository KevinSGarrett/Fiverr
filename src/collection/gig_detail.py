"""Fixture-backed parser for Fiverr gig detail HTML."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any

from src.collection.selectors import get_selector

_TAG_RE = re.compile(r"<[^>]+>")
_PRICE_RE = re.compile(r"([$\u20ac\u00a3])\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
_DELIVERY_RE = re.compile(r"(\d{1,2})\s*day", flags=re.IGNORECASE)
_REVIEW_RE = re.compile(r"([0-9][0-9,]*)")
_RATING_RE = re.compile(r"([0-5](?:\.[0-9])?)")


@dataclass(frozen=True, slots=True)
class GigPackage:
    """Parsed package-level details."""

    name: str
    price: str | None
    price_cents: int | None
    delivery_days: int | None


@dataclass(frozen=True, slots=True)
class GigDetailParseResult:
    """Parsed gig detail payload from fixture HTML."""

    title: str | None
    seller_name: str | None
    packages: list[GigPackage] = field(default_factory=list)
    description: str | None = None
    has_faq: bool = False
    faq_text: str | None = None
    tags: list[str] | None = None
    video_present: bool | None = None
    rating: float | None = None
    review_count: int | None = None
    image_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _clean_text(value: str) -> str:
    return " ".join(_TAG_RE.sub(" ", value).split())


def _extract_text(html: str, test_id: str) -> str | None:
    # Intentional boundary: we deterministically keep the first matching data-testid node.
    # This avoids over-parsing unstable duplicate markup in fixture HTML snapshots.
    class _DataTestIdTextParser(HTMLParser):
        def __init__(self, target_test_id: str) -> None:
            super().__init__(convert_charrefs=True)
            self._target_test_id = target_test_id
            self._collect_depth = 0
            self._chunks: list[str] = []
            self.result: str | None = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attrs_dict = dict(attrs)
            if self.result is not None:
                return
            if self._collect_depth > 0:
                self._collect_depth += 1
                return
            if attrs_dict.get("data-testid") == self._target_test_id:
                self._collect_depth = 1

        def handle_endtag(self, tag: str) -> None:
            del tag
            if self.result is not None or self._collect_depth == 0:
                return
            self._collect_depth -= 1
            if self._collect_depth == 0:
                cleaned = _clean_text("".join(self._chunks))
                self.result = cleaned or None

        def handle_data(self, data: str) -> None:
            if self.result is None and self._collect_depth > 0:
                self._chunks.append(data)

        def close(self) -> None:
            # Recover text from malformed HTML when target node never closes.
            if self.result is None and self._collect_depth > 0:
                cleaned = _clean_text("".join(self._chunks))
                self.result = cleaned or None
            super().close()

    parser = _DataTestIdTextParser(test_id)
    parser.feed(html)
    parser.close()
    return parser.result


def _extract_first_by_tag(html: str, tag: str) -> str | None:
    match = re.search(fr"<{tag}\b[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = _clean_text(match.group(1))
    return text or None


def _normalize_price_to_cents(price_text: str | None) -> int | None:
    if not price_text:
        return None
    match = _PRICE_RE.search(price_text)
    if not match:
        return None
    raw_amount = match.group(2).replace(",", "")
    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        return None
    return int((amount * 100).quantize(Decimal("1")))


def _extract_review_count(value: str | None) -> int | None:
    if not value:
        return None
    match = _REVIEW_RE.search(value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _extract_rating(value: str | None) -> float | None:
    if not value:
        return None
    match = _RATING_RE.search(value)
    if not match:
        return None
    return float(match.group(1))


def _extract_delivery_days(value: str | None) -> int | None:
    if not value:
        return None
    match = _DELIVERY_RE.search(value)
    if not match:
        return None
    return int(match.group(1))


def _extract_json_ld_objects(html: str) -> list[dict[str, Any]]:
    matches = re.findall(
        r"<script[^>]*type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    parsed: list[dict[str, Any]] = []
    for block in matches:
        text = block.strip()
        if not text:
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            parsed.append(value)
            graph = value.get("@graph")
            if isinstance(graph, list):
                parsed.extend([entry for entry in graph if isinstance(entry, dict)])
        elif isinstance(value, list):
            parsed.extend([entry for entry in value if isinstance(entry, dict)])
    return parsed


def _extract_next_data_payload(html: str) -> dict[str, Any] | None:
    match = re.search(
        r"<script[^>]*id=['\"]__NEXT_DATA__['\"][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    payload = match.group(1).strip()
    if not payload:
        return None
    try:
        value = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _walk_json_dicts(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(value, dict):
        items.append(value)
        for nested in value.values():
            items.extend(_walk_json_dicts(nested))
    elif isinstance(value, list):
        for nested in value:
            items.extend(_walk_json_dicts(nested))
    return items


def _coerce_price_text(raw_price: Any, currency: Any) -> str | None:
    if raw_price is None:
        return None
    if isinstance(raw_price, int | float):
        number_text = str(int(raw_price)) if isinstance(raw_price, int) else str(raw_price)
    elif isinstance(raw_price, str):
        number_text = raw_price.strip()
    else:
        return None
    if not number_text:
        return None
    if any(symbol in number_text for symbol in ("$", "\u20ac", "\u00a3")):
        return number_text
    currency_symbol = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3"}.get(str(currency or "").upper(), "$")
    return f"{currency_symbol}{number_text}"


def _extract_price_text_from_payload(pkg: dict[str, Any]) -> str | None:
    for key in (
        "price",
        "amount",
        "startingPrice",
        "priceValue",
        "price_text",
        "lowPrice",
        "minPrice",
        "highPrice",
        "maxPrice",
    ):
        if key not in pkg:
            continue
        raw_value = pkg.get(key)
        if isinstance(raw_value, dict):
            continue
        coerced = _coerce_price_text(raw_value, pkg.get("currency") or pkg.get("priceCurrency"))
        if coerced is not None:
            return coerced

    nested_candidates: list[dict[str, Any]] = []
    for nested_key in ("price", "priceRange", "priceSpecification"):
        nested_value = pkg.get(nested_key)
        if isinstance(nested_value, dict):
            nested_candidates.append(nested_value)
        elif isinstance(nested_value, list):
            nested_candidates.extend(
                [candidate for candidate in nested_value if isinstance(candidate, dict)]
            )

    nested_value_keys = ("amount", "value", "price", "min", "lowPrice", "minPrice", "max", "highPrice")
    for nested in nested_candidates:
        raw_nested_price: Any = None
        for nested_value_key in nested_value_keys:
            if nested_value_key in nested:
                raw_nested_price = nested.get(nested_value_key)
                break
        if raw_nested_price is None:
            continue
        coerced = _coerce_price_text(
            raw_nested_price,
            nested.get("currency")
            or nested.get("currencyCode")
            or nested.get("priceCurrency")
            or pkg.get("currency")
            or pkg.get("priceCurrency"),
        )
        if coerced is not None:
            return coerced
    return None


def _extract_packages_from_json(value: Any) -> list[GigPackage]:
    if not isinstance(value, list):
        return []
    packages: list[GigPackage] = []
    for idx, raw in enumerate(value, start=1):
        if not isinstance(raw, dict):
            continue
        name = (
            raw.get("name")
            or raw.get("title")
            or raw.get("packageName")
            or raw.get("tier")
            or f"Package {idx}"
        )
        delivery_days = _extract_delivery_days(
            raw.get("deliveryTime")
            if isinstance(raw.get("deliveryTime"), str)
            else raw.get("delivery_days") if isinstance(raw.get("delivery_days"), str) else None
        )
        if delivery_days is None and isinstance(raw.get("deliveryDays"), int):
            delivery_days = raw.get("deliveryDays")
        price_text = _extract_price_text_from_payload(raw)
        packages.append(
            GigPackage(
                name=str(name).strip() if str(name).strip() else f"Package {idx}",
                price=price_text,
                price_cents=_normalize_price_to_cents(price_text),
                delivery_days=delivery_days,
            )
        )
    return packages


def _extract_from_json_ld(html: str) -> dict[str, Any]:
    title: str | None = None
    seller_name: str | None = None
    description: str | None = None
    rating: float | None = None
    review_count: int | None = None
    packages: list[GigPackage] = []
    image_count: int | None = None

    for obj in _extract_json_ld_objects(html):
        if title is None and isinstance(obj.get("name"), str):
            title = _clean_text(obj.get("name") or "")
        if description is None and isinstance(obj.get("description"), str):
            description = _clean_text(obj.get("description") or "")
        if seller_name is None:
            provider = obj.get("provider") or obj.get("brand") or obj.get("seller")
            if isinstance(provider, dict) and isinstance(provider.get("name"), str):
                seller_name = _clean_text(provider.get("name") or "")
        if rating is None and isinstance(obj.get("aggregateRating"), dict):
            rating = _extract_rating(str(obj["aggregateRating"].get("ratingValue")))
            review_count = _extract_review_count(str(obj["aggregateRating"].get("reviewCount")))
        if not packages:
            offers = obj.get("offers")
            if isinstance(offers, dict):
                offers = [offers]
            packages = _extract_packages_from_json(offers) if isinstance(offers, list) else []
        if image_count is None:
            images = obj.get("image")
            if isinstance(images, list):
                image_count = len([item for item in images if isinstance(item, str)])

    return {
        "title": title,
        "seller_name": seller_name,
        "description": description,
        "rating": rating,
        "review_count": review_count,
        "packages": packages,
        "image_count": image_count,
    }


def _extract_from_next_data(html: str) -> dict[str, Any]:
    payload = _extract_next_data_payload(html)
    if payload is None:
        return {}

    title: str | None = None
    seller_name: str | None = None
    description: str | None = None
    rating: float | None = None
    review_count: int | None = None
    packages: list[GigPackage] = []

    for entry in _walk_json_dicts(payload):
        if title is None:
            for key in ("gigTitle", "title", "seoTitle", "name"):
                if isinstance(entry.get(key), str) and entry.get(key):
                    title = _clean_text(entry.get(key) or "")
                    break
        if description is None:
            for key in ("description", "descriptionText", "seoDescription"):
                if isinstance(entry.get(key), str) and entry.get(key):
                    description = _clean_text(entry.get(key) or "")
                    break
        if seller_name is None:
            for key in ("sellerName", "seller_username", "username", "displayName"):
                if isinstance(entry.get(key), str) and entry.get(key):
                    seller_name = _clean_text(entry.get(key) or "")
                    break
        if rating is None:
            for key in ("rating", "averageRating", "gigRating"):
                if entry.get(key) is not None:
                    rating = _extract_rating(str(entry.get(key)))
                    if rating is not None:
                        break
        if review_count is None:
            for key in ("reviewCount", "reviewsCount", "totalReviews"):
                if entry.get(key) is not None:
                    review_count = _extract_review_count(str(entry.get(key)))
                    if review_count is not None:
                        break
        if not packages:
            for key in ("packages", "packageTiers", "tiers", "offerPackages"):
                maybe_packages = _extract_packages_from_json(entry.get(key))
                if maybe_packages:
                    packages = maybe_packages
                    break

    return {
        "title": title,
        "seller_name": seller_name,
        "description": description,
        "rating": rating,
        "review_count": review_count,
        "packages": packages,
    }


# ---------------------------------------------------------------------------
# perseus-initial-props JSON extraction
#
# Fiverr's gig detail SPA embeds the full page payload (title, seller identity,
# real description, packages, tags, FAQ, gallery, per-gig reviews) as JSON in a
# `perseus-initial-props` script tag — the same authoritative data source used
# by the search-results page (see search_result_parser.py). The JSON-LD /
# __NEXT_DATA__ / data-testid fallback chain below produces materially wrong
# values on real 2026 Fiverr pages (generic "Fiverr" seller name, boilerplate
# schema.org description, image_count inflated by every unrelated <img> tag on
# the page) — verified against real ScrapFly-fetched gig pages.
# ---------------------------------------------------------------------------

_PERSEUS_SCRIPT_RE = re.compile(
    r'<script[^>]*\bid=["\']perseus-initial-props["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _extract_perseus_gig_props(html: str) -> dict[str, Any] | None:
    """Locate and parse the perseus-initial-props JSON blob. Never raises."""
    match = _PERSEUS_SCRIPT_RE.search(html)
    if not match:
        return None
    try:
        props = json.loads(match.group(1).strip())
    except (ValueError, TypeError):
        return None
    return props if isinstance(props, dict) else None


def _perseus_gig_packages(props: dict[str, Any]) -> list[GigPackage]:
    packages_obj = props.get("packages")
    package_list = packages_obj.get("packageList") if isinstance(packages_obj, dict) else None
    if not isinstance(package_list, list):
        return []

    packages: list[GigPackage] = []
    for entry in package_list:
        if not isinstance(entry, dict):
            continue
        price_cents = entry.get("price")
        price_text = f"${price_cents / 100:.2f}" if isinstance(price_cents, int | float) else None
        duration_hours = entry.get("duration")
        delivery_days = (
            int(duration_hours) // 24 if isinstance(duration_hours, int | float) and duration_hours else None
        )
        name = entry.get("title")
        packages.append(
            GigPackage(
                name=name if isinstance(name, str) and name else "Unnamed package",
                price=price_text,
                price_cents=int(price_cents) if isinstance(price_cents, int | float) else None,
                delivery_days=delivery_days,
            )
        )
    return packages


def _perseus_faq_text(qa_pairs: list[Any]) -> str | None:
    entries = []
    for qa in qa_pairs:
        if not isinstance(qa, dict):
            continue
        question = qa.get("question")
        answer = qa.get("answer")
        if isinstance(question, str) and isinstance(answer, str) and question.strip() and answer.strip():
            entries.append(f"Q: {question.strip()}\nA: {answer.strip()}")
    return "\n\n".join(entries) if entries else None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_gig_detail_from_perseus(props: dict[str, Any]) -> GigDetailParseResult | None:
    general = _as_dict(props.get("general"))
    open_graph = _as_dict(props.get("openGraph"))
    seller = _as_dict(props.get("seller"))
    seller_user = _as_dict(seller.get("user"))
    description_obj = _as_dict(props.get("description"))
    reviews = _as_dict(props.get("reviews"))
    tags_obj = _as_dict(props.get("tags"))
    faq_obj = _as_dict(props.get("faq"))
    gallery = _as_dict(props.get("gallery"))

    title = general.get("gigTitle") or open_graph.get("title")
    if not isinstance(title, str) or not title.strip():
        return None  # not a real gig-detail perseus payload — fall back to legacy chain

    seller_name = seller_user.get("name")
    raw_description = description_obj.get("content") or open_graph.get("description")
    description = _clean_text(raw_description) if isinstance(raw_description, str) else None

    qa_pairs = faq_obj.get("questionsAndAnswers")
    qa_list = qa_pairs if isinstance(qa_pairs, list) else []
    faq_text = _perseus_faq_text(qa_list)
    has_faq = bool(qa_list)

    tag_list = tags_obj.get("tagsGigList")
    tags = (
        [tag["name"] for tag in tag_list if isinstance(tag, dict) and isinstance(tag.get("name"), str)]
        if isinstance(tag_list, list)
        else []
    ) or None

    video_present = bool(open_graph.get("video"))

    rating_value = reviews.get("average_valuation")
    rating = float(rating_value) if isinstance(rating_value, int | float) else None
    review_count_value = reviews.get("total_count")
    review_count = int(review_count_value) if isinstance(review_count_value, int | float) else None

    slides = gallery.get("slides")
    image_count = 0
    if isinstance(slides, list):
        for entry in slides:
            slide = entry.get("slide") if isinstance(entry, dict) else None
            if isinstance(slide, dict) and slide.get("typeImage"):
                image_count += 1

    return GigDetailParseResult(
        title=title.strip(),
        seller_name=seller_name if isinstance(seller_name, str) and seller_name else None,
        packages=_perseus_gig_packages(props),
        description=description,
        has_faq=has_faq,
        faq_text=faq_text,
        tags=tags,
        video_present=video_present,
        rating=rating,
        review_count=review_count,
        image_count=image_count,
        warnings=[],
        errors=[],
        metadata={"mode": "perseus", "gig_id": general.get("gigId")},
    )


def parse_gig_detail_from_html(html: str) -> GigDetailParseResult:
    """Parse gig detail fixture HTML with safe warnings and no side effects."""

    perseus_props = _extract_perseus_gig_props(html)
    if perseus_props is not None:
        perseus_result = _parse_gig_detail_from_perseus(perseus_props)
        if perseus_result is not None:
            return perseus_result

    warnings: list[str] = []
    errors: list[str] = []

    # Safe selector-registry boundary to keep parser aligned with Cycle 003 registry.
    _ = get_selector("gig_detail", "gig_detail_title")

    if "<" not in html or ">" not in html:
        return GigDetailParseResult(
            title=None,
            seller_name=None,
            warnings=["Gig detail HTML appears malformed; no tags detected."],
            errors=["malformed_html"],
            metadata={"mode": "fixture", "parsed": False},
        )

    json_ld = _extract_from_json_ld(html)
    next_data = _extract_from_next_data(html)

    title = (
        _extract_text(html, "gig-title")
        or _extract_first_by_tag(html, "h1")
        or next_data.get("title")
        or json_ld.get("title")
    )
    if not title:
        warnings.append("Gig title was not found.")

    seller_name = _extract_text(html, "seller-name") or next_data.get("seller_name") or json_ld.get("seller_name")
    if not seller_name:
        warnings.append("Seller name was not found.")

    description = _extract_text(html, "gig-description") or next_data.get("description") or json_ld.get("description")
    if not description:
        warnings.append("Gig description was not found.")

    has_faq = bool(_extract_text(html, "faq-section") or re.search(r"\bfaq\b", html, flags=re.IGNORECASE))
    rating = _extract_rating(_extract_text(html, "gig-rating")) or next_data.get("rating") or json_ld.get("rating")
    review_count = _extract_review_count(_extract_text(html, "gig-review-count"))
    if review_count is None:
        review_count = next_data.get("review_count")
    if review_count is None:
        review_count = json_ld.get("review_count")

    package_blocks = re.findall(
        r"<(?:div|section)\b[^>]*data-testid=['\"]package-card['\"][^>]*>(.*?)</(?:div|section)>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    packages: list[GigPackage] = []
    for block in package_blocks:
        package_name = _extract_text(block, "package-name") or _extract_first_by_tag(block, "h3") or "Unnamed package"
        package_price_text = _extract_text(block, "package-price")
        if not package_price_text:
            price_match = _PRICE_RE.search(block)
            package_price_text = price_match.group(0) if price_match else None
        package_delivery_text = _extract_text(block, "delivery-days")
        packages.append(
            GigPackage(
                name=package_name,
                price=package_price_text,
                price_cents=_normalize_price_to_cents(package_price_text),
                delivery_days=_extract_delivery_days(package_delivery_text),
            )
        )

    if not packages:
        packages = next_data.get("packages") or json_ld.get("packages") or []

    if not packages:
        warnings.append("No package cards were found in gig detail fixture.")

    image_count = len(re.findall(r"<img\b", html, flags=re.IGNORECASE))
    if image_count == 0 and isinstance(json_ld.get("image_count"), int):
        image_count = json_ld["image_count"]
    if image_count == 0:
        warnings.append("No images were detected in gig detail fixture.")

    return GigDetailParseResult(
        title=title,
        seller_name=seller_name,
        packages=packages,
        description=description,
        has_faq=has_faq,
        rating=rating,
        review_count=review_count,
        image_count=image_count,
        warnings=warnings,
        errors=errors,
        metadata={
            "mode": "fixture",
            "selector_group": "gig_detail",
            "package_count": len(packages),
        },
    )
