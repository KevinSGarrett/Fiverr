# Gig Visual Analysis
# Fiverr Research System — Wave 11

**Document Status:** Complete
**Wave:** 11 — Gig Creation Playbook
**Purpose:** Thumbnail and gallery image classification, competitor visual pattern detection, image-to-conversion correlation analysis, LLM vision analysis of competitor screenshots, and visual best practices engine.

---

## The Problem This Solves

The recommendation engine (Wave 7) tells you WHAT to write in your gig. But a buyer's first impression is VISUAL — the thumbnail, gallery images, and overall presentation quality. This module analyzes what makes top sellers' gigs LOOK successful and translates those patterns into actionable creative direction.

---

## Visual Data Collection — Stage 4 Enhancement

During Stage 4 (Gig Detail Scrape), Playwright already visits each gig page. This module adds screenshot capture:

```python
# Addition to gig detail collection workflow

async def capture_gig_visuals(page, gig_id: int, db):
    """
    Captures visual data from a gig page during Stage 4 collection.
    Called after all text data has been scraped.
    """
    visuals = {}

    # 1. Screenshot the gig card as it appears in search results
    #    (captured during Stage 3 instead — search result screenshots)

    # 2. Screenshot the thumbnail (first gallery image)
    thumbnail_el = await page.query_selector(GIG_DETAIL_THUMBNAIL)
    if thumbnail_el:
        thumb_path = f"data/screenshots/thumbs/{gig_id}.png"
        await thumbnail_el.screenshot(path=thumb_path)
        visuals["thumbnail_path"] = thumb_path

    # 3. Count gallery images
    gallery_items = await page.query_selector_all(GIG_DETAIL_GALLERY_ITEM)
    visuals["gallery_count"] = len(gallery_items)

    # 4. Check for video in gallery
    video_indicator = await page.query_selector(GIG_DETAIL_VIDEO_INDICATOR)
    visuals["has_video"] = video_indicator is not None

    # 5. Extract thumbnail dominant color (from CSS background or img src)
    # Lightweight — just record the URL for later analysis
    thumb_img = await page.query_selector(f"{GIG_DETAIL_THUMBNAIL} img")
    if thumb_img:
        visuals["thumbnail_url"] = await thumb_img.get_attribute("src")

    return visuals
```

**New selectors added to fiverr_selectors.py:**

```python
# ─── Gig visuals ──────────────────────────────────────────────────────
GIG_DETAIL_THUMBNAIL       = "[data-testid='gallery-thumbnail'], .gallery-thumbnail, .gig-gallery img:first-child"
GIG_DETAIL_GALLERY_ITEM    = "[data-testid='gallery-item'], .gallery-item"
GIG_DETAIL_VIDEO_INDICATOR = "[data-testid='video-badge'], .video-badge, .gallery-video"
GIG_DETAIL_SELLER_AVATAR   = "[data-testid='seller-avatar'], .seller-avatar img"
```

---

## Thumbnail Classification System

Every competitor thumbnail is classified across 6 dimensions:

```python
# src/analysis/visual_analysis.py

from pydantic import BaseModel
from enum import Enum

class ImageType(str, Enum):
    MOCKUP = "mockup"           # Device/screen mockup showing deliverable
    SCREENSHOT = "screenshot"    # Actual screenshot of work
    TEXT_HEAVY = "text_heavy"    # Mostly text/typography
    PHOTO = "photo"             # Real photography
    ILLUSTRATION = "illustration" # Custom illustration/graphic
    ABSTRACT = "abstract"        # Abstract/gradient/pattern
    STOCK = "stock_photo"        # Generic stock photography
    AI_GENERATED = "ai_generated" # Visibly AI-generated imagery
    VIDEO_THUMB = "video_thumbnail" # Video play button overlay
    TEMPLATE = "template"        # Obvious Canva/template design

class ColorScheme(str, Enum):
    DARK = "dark"               # Dark background (#000–#333)
    LIGHT = "light"             # Light/white background
    BRANDED = "branded"         # Consistent brand colors
    COLORFUL = "colorful"       # Multiple bright colors
    MONOCHROME = "monochrome"   # Single color + variations
    GRADIENT = "gradient"       # Gradient background

class TextPresence(str, Enum):
    NONE = "none"               # No text overlay
    KEYWORD_OVERLAY = "keyword" # Keyword/service name text
    HEADLINE = "headline"       # Marketing headline
    FEATURE_LIST = "feature_list" # List of features/deliverables
    PRICE_CALLOUT = "price"     # Price or "starting at $X"

class PeoplePresence(str, Enum):
    NONE = "none"
    HEADSHOT = "headshot"       # Professional headshot of seller
    TEAM = "team"               # Multiple people
    STOCK_PEOPLE = "stock"      # Generic stock photo people
    AVATAR = "avatar"           # Illustrated/cartoon avatar

class QualityIndicator(str, Enum):
    PROFESSIONAL = "professional"   # Clean, polished, high-res
    COMPETENT = "competent"         # Decent but not exceptional
    AMATEUR = "amateur"             # Low quality, poor composition
    AI_STYLE = "ai_generated"       # Visibly AI-generated artifacts
    TEMPLATE_STYLE = "template"     # Obvious template/Canva


class ThumbnailClassification(BaseModel):
    """Complete classification of a competitor's gig thumbnail."""
    gig_id: int
    image_type: ImageType
    color_scheme: ColorScheme
    text_presence: TextPresence
    people_presence: PeoplePresence
    quality: QualityIndicator
    has_logo_or_brand: bool
    has_border_or_frame: bool
    gallery_count: int
    has_video: bool
    classification_method: str  # "llm_vision" or "rule_based"
    classification_confidence: float  # 0-1
```

---

## LLM Vision Classification (gpt-4o with Vision)

For top-performing gigs (top 10 per keyword), use gpt-4o vision to classify thumbnails:

```python
async def classify_thumbnail_with_vision(
    screenshot_path: str,
    gig_id: int,
    llm_client,
    cache,
) -> ThumbnailClassification:
    """
    Uses gpt-4o vision to classify a gig thumbnail screenshot.
    Only called for top 10 gigs per keyword (cost management).
    """
    import base64

    # Read screenshot as base64
    with open(screenshot_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    prompt = """Classify this Fiverr gig thumbnail image across these dimensions.
Return JSON only.

{
  "image_type": "mockup|screenshot|text_heavy|photo|illustration|abstract|stock_photo|ai_generated|video_thumbnail|template",
  "color_scheme": "dark|light|branded|colorful|monochrome|gradient",
  "text_presence": "none|keyword|headline|feature_list|price",
  "people_presence": "none|headshot|team|stock|avatar",
  "quality": "professional|competent|amateur|ai_generated|template",
  "has_logo_or_brand": boolean,
  "has_border_or_frame": boolean,
  "text_content": "string (any text visible in the image, empty if none)",
  "dominant_colors": ["color1", "color2"],
  "standout_elements": ["list of what makes this thumbnail notable"]
}"""

    # Cache check
    cache_key = build_cache_key("gpt-4o-vision", 0.1, f"thumb_{gig_id}")
    cached = cache.get(cache_key)
    if cached:
        return ThumbnailClassification(**cached, gig_id=gig_id,
                                        classification_method="llm_vision",
                                        classification_confidence=0.85)

    result = await llm_client.complete(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_b64}",
                    "detail": "low",  # Low detail = cheaper
                }},
            ],
        }],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    parsed = json.loads(result.content)
    cache.set(cache_key, parsed, ttl_hours=168)  # 7-day cache for images

    return ThumbnailClassification(
        gig_id=gig_id,
        image_type=parsed.get("image_type", "unknown"),
        color_scheme=parsed.get("color_scheme", "unknown"),
        text_presence=parsed.get("text_presence", "none"),
        people_presence=parsed.get("people_presence", "none"),
        quality=parsed.get("quality", "competent"),
        has_logo_or_brand=parsed.get("has_logo_or_brand", False),
        has_border_or_frame=parsed.get("has_border_or_frame", False),
        gallery_count=0,  # Set separately
        has_video=False,  # Set separately
        classification_method="llm_vision",
        classification_confidence=0.85,
    )
```

**Cost per thumbnail classification:** ~$0.003 (gpt-4o vision at low detail)
**Per keyword (top 10):** ~$0.03
**Per niche (20 keywords × 10 gigs):** ~$0.60
**Full run (9 niches):** ~$5.40 (with caching, effective ~$1–2 after first run)

---

## Visual Pattern Correlation

Which visual patterns correlate with high performance?

```python
def analyze_visual_patterns(keyword_id: int, db) -> dict:
    """
    Correlates thumbnail classifications with gig performance metrics.
    Answers: which visual patterns are top sellers using?
    """
    gigs = get_gigs_for_keyword(keyword_id, db)
    classifications = get_thumbnail_classifications(keyword_id, db)

    if len(classifications) < 5:
        return {"status": "insufficient_data"}

    # Split into high-performers (top 25%) and rest
    sorted_gigs = sorted(gigs, key=lambda g: g.detail_review_count or 0, reverse=True)
    cutoff = len(sorted_gigs) // 4
    top_gigs = set(g.id for g in sorted_gigs[:max(cutoff, 3)])

    top_classifications = [c for c in classifications if c.gig_id in top_gigs]
    all_classifications = classifications

    # Distribution analysis per dimension
    def distribution(items, field):
        from collections import Counter
        values = [getattr(c, field) for c in items if hasattr(c, field)]
        counts = Counter(values)
        total = len(values)
        return {str(k): round(v / total * 100, 1) for k, v in counts.most_common()}

    patterns = {
        "top_performers": {
            "image_type": distribution(top_classifications, "image_type"),
            "color_scheme": distribution(top_classifications, "color_scheme"),
            "text_presence": distribution(top_classifications, "text_presence"),
            "people_presence": distribution(top_classifications, "people_presence"),
            "quality": distribution(top_classifications, "quality"),
            "has_video_pct": round(
                sum(1 for c in top_classifications if c.has_video) / max(1, len(top_classifications)) * 100, 1
            ),
            "has_logo_pct": round(
                sum(1 for c in top_classifications if c.has_logo_or_brand) / max(1, len(top_classifications)) * 100, 1
            ),
            "avg_gallery_count": round(
                sum(c.gallery_count for c in top_classifications) / max(1, len(top_classifications)), 1
            ),
        },
        "all_sellers": {
            "image_type": distribution(all_classifications, "image_type"),
            "color_scheme": distribution(all_classifications, "color_scheme"),
            "text_presence": distribution(all_classifications, "text_presence"),
            "quality": distribution(all_classifications, "quality"),
        },
        "differentiation_opportunities": [],
    }

    # Find where top performers differ from the field
    for dim in ["image_type", "color_scheme", "text_presence"]:
        top_dist = patterns["top_performers"][dim]
        all_dist = patterns["all_sellers"][dim]
        for value, top_pct in top_dist.items():
            all_pct = all_dist.get(value, 0)
            if top_pct > all_pct + 15:
                patterns["differentiation_opportunities"].append({
                    "dimension": dim,
                    "value": value,
                    "top_pct": top_pct,
                    "all_pct": all_pct,
                    "insight": f"Top performers use {value} {dim} {top_pct - all_pct:.0f}% more than average"
                })

    # Underused approaches (things NO top performer does — potential blue ocean)
    for dim in ["image_type", "color_scheme"]:
        all_values = set(patterns["all_sellers"][dim].keys())
        top_values = set(patterns["top_performers"][dim].keys())
        unused_by_top = all_values - top_values
        for value in unused_by_top:
            patterns["differentiation_opportunities"].append({
                "dimension": dim,
                "value": value,
                "top_pct": 0,
                "all_pct": patterns["all_sellers"][dim].get(value, 0),
                "insight": f"No top performer uses {value} {dim} — could differentiate OR could indicate it doesn't convert"
            })

    return patterns
```

---

## Visual Best Practices Engine

Generates per-keyword visual recommendations based on pattern analysis:

```python
def generate_visual_recommendations(
    keyword_id: int,
    visual_patterns: dict,
    existing_thumbnail_direction: dict | None,
    db,
) -> dict:
    """
    Combines pattern analysis with existing thumbnail_direction (Wave 7 Task 8)
    to produce enhanced visual recommendations.
    """
    recommendations = {
        "thumbnail": {},
        "gallery": {},
        "profile_image": {},
    }

    top = visual_patterns.get("top_performers", {})
    opps = visual_patterns.get("differentiation_opportunities", [])

    # Thumbnail recommendations
    # Dominant image type among top performers
    top_image_type = max(top.get("image_type", {}).items(),
                          key=lambda x: x[1], default=("mockup", 50))
    recommendations["thumbnail"]["recommended_image_type"] = top_image_type[0]
    recommendations["thumbnail"]["image_type_reasoning"] = (
        f"{top_image_type[1]:.0f}% of top performers use {top_image_type[0]} style"
    )

    # Color scheme
    top_color = max(top.get("color_scheme", {}).items(),
                     key=lambda x: x[1], default=("dark", 50))
    recommendations["thumbnail"]["recommended_color_scheme"] = top_color[0]

    # Text strategy
    top_text = max(top.get("text_presence", {}).items(),
                    key=lambda x: x[1], default=("keyword", 50))
    recommendations["thumbnail"]["recommended_text_approach"] = top_text[0]

    # Gallery count
    avg_gallery = top.get("avg_gallery_count", 3)
    recommendations["gallery"]["recommended_count"] = max(3, round(avg_gallery))
    recommendations["gallery"]["has_video_recommended"] = top.get("has_video_pct", 0) > 40

    # Gallery composition
    recommendations["gallery"]["suggested_images"] = [
        {"position": 1, "type": "primary_thumbnail", "description": "Main gig thumbnail — follows recommended style above"},
        {"position": 2, "type": "deliverable_preview", "description": "Screenshot or mockup of actual deliverable"},
        {"position": 3, "type": "process_overview", "description": "Visual showing your process or methodology"},
    ]
    if recommendations["gallery"]["recommended_count"] >= 4:
        recommendations["gallery"]["suggested_images"].append(
            {"position": 4, "type": "social_proof", "description": "Testimonial screenshot or portfolio sample"}
        )
    if recommendations["gallery"]["has_video_recommended"]:
        recommendations["gallery"]["suggested_images"].append(
            {"position": 5, "type": "intro_video", "description": "30-60 second intro video explaining your service"}
        )

    # Differentiation notes from pattern analysis
    recommendations["differentiation_notes"] = []
    for opp in opps[:3]:
        recommendations["differentiation_notes"].append(opp["insight"])

    # Merge with existing thumbnail_direction from Wave 7
    if existing_thumbnail_direction:
        recommendations["thumbnail"]["wave7_concept"] = existing_thumbnail_direction.get("concept")
        recommendations["thumbnail"]["wave7_elements_include"] = existing_thumbnail_direction.get("elements_to_include")
        recommendations["thumbnail"]["wave7_elements_avoid"] = existing_thumbnail_direction.get("elements_to_avoid")

    return recommendations
```

---

## Storage Schema

```python
class GigVisualAnalysis(Base):
    """Thumbnail and gallery visual classification per gig."""
    __tablename__ = "gig_visual_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gig_id = Column(Integer, ForeignKey("gigs.id"), nullable=False, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=False)

    # Thumbnail classification
    image_type = Column(String)
    color_scheme = Column(String)
    text_presence = Column(String)
    people_presence = Column(String)
    quality = Column(String)
    has_logo_or_brand = Column(Boolean)
    has_border_or_frame = Column(Boolean)
    classification_method = Column(String)  # llm_vision | rule_based
    classification_confidence = Column(Float)

    # Gallery data
    gallery_count = Column(Integer)
    has_video = Column(Boolean)

    # Screenshot reference
    thumbnail_screenshot_path = Column(String, nullable=True)

    analyzed_at = Column(DateTime, default=datetime.utcnow)
```

**No raw images stored in the database.** Screenshots are saved to `data/screenshots/thumbs/` as PNG files. Only classification metadata is in the DB. Screenshots can be cleaned up after analysis (configurable retention).

---

## Dashboard Integration

### Recommendations Page — Visual Tab (New)

Added as a tab in each recommendation card:

```python
with tab_visual:  # New tab: "🎨 Visuals"
    visual_recs = get_visual_recommendations(rec.keyword_id, db)
    if visual_recs:
        st.markdown("### Thumbnail")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Style:** {visual_recs['thumbnail']['recommended_image_type']}")
            st.markdown(f"**Colors:** {visual_recs['thumbnail']['recommended_color_scheme']}")
            st.markdown(f"**Text:** {visual_recs['thumbnail']['recommended_text_approach']}")
        with col2:
            st.markdown(f"_{visual_recs['thumbnail']['image_type_reasoning']}_")
            if visual_recs['thumbnail'].get('wave7_concept'):
                st.markdown(f"**Concept:** {visual_recs['thumbnail']['wave7_concept']}")

        st.markdown("### Gallery")
        st.markdown(f"**Recommended images:** {visual_recs['gallery']['recommended_count']}")
        if visual_recs['gallery']['has_video_recommended']:
            st.info("📹 Video recommended — 40%+ of top performers have gallery video")
        for img in visual_recs['gallery']['suggested_images']:
            st.markdown(f"{img['position']}. **{img['type']}:** {img['description']}")

        if visual_recs.get('differentiation_notes'):
            st.markdown("### Differentiation Insights")
            for note in visual_recs['differentiation_notes']:
                st.markdown(f"→ {note}")
```

### Competitors Page — Visual Distribution (New Widget)

```python
def render_visual_distribution(niche_id: str, db):
    """Pie charts showing thumbnail classification distribution for a niche."""
    classifications = get_all_classifications_for_niche(niche_id, db)
    if not classifications:
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(
            values=[c[1] for c in Counter(c.image_type for c in classifications).most_common()],
            names=[c[0] for c in Counter(c.image_type for c in classifications).most_common()],
            title="Thumbnail Image Types",
            hole=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(
            values=[c[1] for c in Counter(c.quality for c in classifications).most_common()],
            names=[c[0] for c in Counter(c.quality for c in classifications).most_common()],
            title="Thumbnail Quality",
            hole=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)
```

---

## Cost Management

| Operation | Model | Per Gig | Per Keyword (10 gigs) | Notes |
|---|---|---|---|---|
| Vision classification | gpt-4o (low detail) | $0.003 | $0.03 | Only top 10 gigs per keyword |
| Full niche (20 kw) | | | $0.60 | First run only — cached 7 days |
| Full system (9 niches) | | | $5.40 | Effective ~$1-2 with cache |

**Depth-tier behavior:**
- `full`: Vision classification for top 20 gigs per keyword
- `standard`: Vision classification for top 10 gigs per keyword
- `feasibility`: Vision classification for top 5 gigs
- `keyword_only`: No visual analysis

**Cost optimization:** Screenshots and classifications are cached for 7 days. Only re-analyze when gig data is refreshed.
