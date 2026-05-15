# Seller Profile Optimization
# Fiverr Research System — Wave 11

**Document Status:** Complete
**Wave:** 11 — Gig Creation Playbook
**Purpose:** Competitor profile element analysis, profile-to-authority correlation, new seller profile checklist, LLM profile optimization task, and integration into RecommendationOutput.

---

## Profile Elements Analyzed

Every seller profile scraped in Stage 5 (Seller Profile Scrape) already captures basic data. This module extends that analysis to extract what makes SUCCESSFUL seller profiles work:

### Data Already Collected (Wave 4)

| Element | Source | Field |
|---|---|---|
| Username | sellers | seller_username |
| Level | sellers | seller_level |
| Country | sellers | country |
| Member since | sellers | member_since |
| Response time | sellers | avg_response_time |
| Response rate | sellers | response_rate |
| Total reviews | sellers | total_reviews |
| Rating | sellers | rating |
| Bio/Description | sellers | bio_text |
| Languages | sellers | languages |

### New Elements to Collect (Stage 5 Enhancement)

```python
# New selectors added to fiverr_selectors.py

SELLER_PROFILE_SKILLS       = "[data-testid='skills-list'] span, .seller-skills .skill-tag"
SELLER_PROFILE_EDUCATION    = "[data-testid='education-section'], .seller-education"
SELLER_PROFILE_CERTS        = "[data-testid='certifications'], .seller-certifications"
SELLER_PROFILE_PORTFOLIO    = "[data-testid='portfolio-items'], .portfolio-item"
SELLER_PROFILE_PORTFOLIO_COUNT = "[data-testid='portfolio-count'], .portfolio-count"
SELLER_PROFILE_SOCIAL_LINKS = "[data-testid='social-links'] a, .seller-social a"
SELLER_PROFILE_AVATAR       = "[data-testid='seller-avatar'] img, .profile-image img"
SELLER_PROFILE_ONLINE_STATUS = "[data-testid='online-indicator'], .online-indicator"
SELLER_PROFILE_SKILL_TESTS  = "[data-testid='skill-tests'], .skill-test-item"

# New fields to extract during Stage 5
NEW_PROFILE_FIELDS = {
    "skills_listed": "list[str]",        # ["Python", "AI", "Machine Learning"]
    "skill_test_count": "int",           # Number of Fiverr skill tests passed
    "skill_test_names": "list[str]",     # ["Python 3", "Data Analysis"]
    "education_entries": "list[dict]",   # [{"institution": "...", "degree": "..."}]
    "certification_count": "int",
    "certification_names": "list[str]",
    "portfolio_count": "int",
    "has_social_links": "bool",
    "social_platforms": "list[str]",     # ["linkedin", "github", "twitter"]
    "avatar_type": "str",               # "headshot" | "logo" | "illustration" | "none"
    "is_online": "bool",
    "bio_word_count": "int",
    "bio_has_credentials": "bool",       # Mentions years of experience, clients, etc.
    "bio_has_specialization": "bool",    # Mentions specific tools, technologies
    "bio_has_proof_elements": "bool",    # Mentions client count, projects delivered
}
```

---

## Profile-to-Authority Correlation

Which profile elements actually correlate with higher authority_score and more reviews?

```python
# src/analysis/profile_optimization.py

def analyze_profile_patterns(niche_id: str, db) -> dict:
    """
    Correlates profile elements with seller success metrics.
    Returns patterns showing which profile elements matter most.
    """
    sellers = get_sellers_for_niche(niche_id, db)
    if len(sellers) < 10:
        return {"status": "insufficient_data"}

    # Split into top 25% and bottom 25% by authority_score
    sorted_sellers = sorted(sellers, key=lambda s: get_authority_score(s.id, db) or 0, reverse=True)
    top_quartile = sorted_sellers[:len(sorted_sellers) // 4]
    bottom_quartile = sorted_sellers[-(len(sorted_sellers) // 4):]

    def pct(group, field_check):
        if not group:
            return 0
        return round(sum(1 for s in group if field_check(s)) / len(group) * 100, 1)

    def avg(group, field_getter):
        values = [field_getter(s) for s in group if field_getter(s) is not None]
        return round(sum(values) / len(values), 1) if values else 0

    patterns = {
        "niche_id": niche_id,
        "sellers_analyzed": len(sellers),
        "elements": {},
    }

    # Bio analysis
    patterns["elements"]["bio"] = {
        "top_avg_word_count": avg(top_quartile, lambda s: s.bio_word_count),
        "bottom_avg_word_count": avg(bottom_quartile, lambda s: s.bio_word_count),
        "top_has_credentials_pct": pct(top_quartile, lambda s: s.bio_has_credentials),
        "bottom_has_credentials_pct": pct(bottom_quartile, lambda s: s.bio_has_credentials),
        "top_has_specialization_pct": pct(top_quartile, lambda s: s.bio_has_specialization),
        "top_has_proof_pct": pct(top_quartile, lambda s: s.bio_has_proof_elements),
    }

    # Avatar
    patterns["elements"]["avatar"] = {
        "top_headshot_pct": pct(top_quartile, lambda s: s.avatar_type == "headshot"),
        "bottom_headshot_pct": pct(bottom_quartile, lambda s: s.avatar_type == "headshot"),
        "top_logo_pct": pct(top_quartile, lambda s: s.avatar_type == "logo"),
    }

    # Portfolio
    patterns["elements"]["portfolio"] = {
        "top_avg_count": avg(top_quartile, lambda s: s.portfolio_count),
        "bottom_avg_count": avg(bottom_quartile, lambda s: s.portfolio_count),
    }

    # Skills and tests
    patterns["elements"]["skills"] = {
        "top_avg_skills": avg(top_quartile, lambda s: len(s.skills_listed or [])),
        "bottom_avg_skills": avg(bottom_quartile, lambda s: len(s.skills_listed or [])),
        "top_avg_tests": avg(top_quartile, lambda s: s.skill_test_count),
        "bottom_avg_tests": avg(bottom_quartile, lambda s: s.skill_test_count),
        "most_common_tests_top": _most_common_tests(top_quartile),
    }

    # Social links
    patterns["elements"]["social"] = {
        "top_has_social_pct": pct(top_quartile, lambda s: s.has_social_links),
        "bottom_has_social_pct": pct(bottom_quartile, lambda s: s.has_social_links),
        "most_common_platforms": _most_common_platforms(top_quartile),
    }

    # Response metrics
    patterns["elements"]["responsiveness"] = {
        "top_avg_response_time_hours": avg(top_quartile, lambda s: s.avg_response_time),
        "bottom_avg_response_time_hours": avg(bottom_quartile, lambda s: s.avg_response_time),
        "top_response_rate_pct": avg(top_quartile, lambda s: s.response_rate),
    }

    # Languages
    patterns["elements"]["languages"] = {
        "top_avg_languages": avg(top_quartile, lambda s: len(s.languages or [])),
        "most_common_languages": _most_common_languages(top_quartile),
    }

    # Calculate impact scores (which elements have the biggest gap between top and bottom)
    impact_scores = []
    for element, data in patterns["elements"].items():
        for key, value in data.items():
            if key.startswith("top_") and key.replace("top_", "bottom_") in data:
                bottom_val = data[key.replace("top_", "bottom_")]
                gap = abs(value - bottom_val) if isinstance(value, (int, float)) else 0
                if gap > 10:
                    impact_scores.append({
                        "element": element,
                        "metric": key,
                        "top_value": value,
                        "bottom_value": bottom_val,
                        "gap": gap,
                    })

    impact_scores.sort(key=lambda x: x["gap"], reverse=True)
    patterns["highest_impact_elements"] = impact_scores[:5]

    return patterns
```

---

## New Seller Profile Checklist

Ordered list of profile setup actions with priority:

```python
def generate_profile_checklist(
    niche_id: str,
    profile_patterns: dict,
) -> list[dict]:
    """
    Generates a prioritized profile setup checklist for a new seller.
    Based on what separates top performers from bottom performers in this niche.
    """
    checklist = []
    elements = profile_patterns.get("elements", {})

    # Always-include items (regardless of pattern data)
    checklist.append({
        "priority": 1,
        "category": "avatar",
        "action": "Upload a professional headshot as your profile picture",
        "detail": ("Use a well-lit, high-resolution photo with a neutral or simple background. "
                   "Face the camera, smile naturally. "
                   f"Top sellers in this niche: {elements.get('avatar', {}).get('top_headshot_pct', 'N/A')}% use headshots."),
        "impact": "HIGH",
        "time_estimate": "10 minutes",
    })

    checklist.append({
        "priority": 2,
        "category": "bio",
        "action": "Write a credential-rich bio",
        "detail": (f"Top sellers average {elements.get('bio', {}).get('top_avg_word_count', 150)} words. "
                   f"{elements.get('bio', {}).get('top_has_credentials_pct', 80)}% mention specific credentials. "
                   "Structure: lead with specialization → credentials → proof (client count/projects) → CTA."),
        "impact": "HIGH",
        "time_estimate": "30 minutes",
    })

    checklist.append({
        "priority": 3,
        "category": "response_time",
        "action": "Enable notifications and respond within 1 hour",
        "detail": (f"Top sellers in this niche respond in "
                   f"{elements.get('responsiveness', {}).get('top_avg_response_time_hours', 2)} hours average. "
                   "Fiverr's algorithm rewards fast response times with better search placement."),
        "impact": "HIGH",
        "time_estimate": "5 minutes (ongoing)",
    })

    # Portfolio
    portfolio_data = elements.get("portfolio", {})
    top_count = portfolio_data.get("top_avg_count", 5)
    checklist.append({
        "priority": 4,
        "category": "portfolio",
        "action": f"Add {max(3, round(top_count))} portfolio items",
        "detail": ("Each item should showcase a real or sample deliverable relevant to your gig. "
                   "Include descriptions explaining the problem solved and approach taken. "
                   f"Top sellers average {top_count} portfolio items."),
        "impact": "HIGH",
        "time_estimate": "1-2 hours",
    })

    # Skill tests
    skills_data = elements.get("skills", {})
    top_tests = skills_data.get("most_common_tests_top", [])
    if top_tests:
        checklist.append({
            "priority": 5,
            "category": "skill_tests",
            "action": f"Take Fiverr skill tests: {', '.join(top_tests[:3])}",
            "detail": (f"Top sellers average {skills_data.get('top_avg_tests', 2)} passed tests. "
                       "Most common among top performers: " + ", ".join(top_tests[:3])),
            "impact": "MEDIUM",
            "time_estimate": "1-2 hours",
        })

    # Skills listed
    checklist.append({
        "priority": 6,
        "category": "skills",
        "action": f"List {max(5, round(skills_data.get('top_avg_skills', 5)))} relevant skills",
        "detail": "Add skills that match your gig keywords and niche. Include both broad and specific skills.",
        "impact": "MEDIUM",
        "time_estimate": "10 minutes",
    })

    # Social links
    social_data = elements.get("social", {})
    if social_data.get("top_has_social_pct", 0) > 40:
        platforms = social_data.get("most_common_platforms", ["linkedin", "github"])
        checklist.append({
            "priority": 7,
            "category": "social",
            "action": f"Link social profiles: {', '.join(platforms[:3])}",
            "detail": (f"{social_data.get('top_has_social_pct', 50)}% of top sellers have social links. "
                       "Adds credibility and allows buyers to verify your expertise."),
            "impact": "LOW",
            "time_estimate": "5 minutes",
        })

    # Languages
    languages_data = elements.get("languages", {})
    checklist.append({
        "priority": 8,
        "category": "languages",
        "action": "List all languages you speak with proficiency levels",
        "detail": "Buyers filter by language. Including multiple languages expands your buyer reach.",
        "impact": "LOW",
        "time_estimate": "5 minutes",
    })

    return sorted(checklist, key=lambda x: x["priority"])
```

---

## LLM Profile Optimization Task — Task #13

New LLM task added to the recommendation pipeline:

```python
# LLM Task 13: Profile optimization recommendations
# Model: gpt-4o-mini (lower complexity than gig content tasks)
# Input: profile_patterns + niche_config + existing bio structure
# Output: personalized profile recommendations
```

### Prompt Template — profile_optimization.j2

```jinja2
You are a Fiverr profile optimization specialist for NEW SELLERS.

NICHE: {{ niche_name }}
KEYWORD: "{{ keyword_text }}"

PROFILE PATTERNS FROM TOP SELLERS IN THIS NICHE:
- Bio: top sellers average {{ profile_patterns.elements.bio.top_avg_word_count }} words
  (bottom sellers: {{ profile_patterns.elements.bio.bottom_avg_word_count }})
- {{ profile_patterns.elements.bio.top_has_credentials_pct }}% of top sellers mention credentials
- {{ profile_patterns.elements.bio.top_has_specialization_pct }}% mention specific specializations
- Avatar: {{ profile_patterns.elements.avatar.top_headshot_pct }}% use professional headshots
- Portfolio: top sellers average {{ profile_patterns.elements.portfolio.top_avg_count }} items
- Skill tests: top sellers average {{ profile_patterns.elements.skills.top_avg_tests }} passed tests
  {% if profile_patterns.elements.skills.most_common_tests_top %}
  Most common: {{ profile_patterns.elements.skills.most_common_tests_top | join(", ") }}
  {% endif %}
- Response time: top sellers respond in {{ profile_patterns.elements.responsiveness.top_avg_response_time_hours }}h
- Response rate: {{ profile_patterns.elements.responsiveness.top_response_rate_pct }}%

SELLER'S SKILLS: {{ skill_profile.primary_skills | join(", ") }}
TOOLS: {{ skill_profile.tools | join(", ") }}

Generate personalized profile setup recommendations for this new seller.

Return JSON only:

{
  "bio_template": {
    "structure": ["opening_hook", "specialization", "credentials", "proof_elements", "cta"],
    "opening_hook": "string (1-2 sentences to start the bio — benefit-led)",
    "specialization_section": "string (what to write about your expertise)",
    "credentials_to_mention": ["list of credentials/experience to highlight"],
    "proof_elements": ["list of proof points to include — even if estimated"],
    "cta": "string (closing call-to-action)",
    "estimated_word_count": integer,
    "tone": "string (professional/friendly/technical)"
  },
  "avatar_recommendation": {
    "type": "headshot|logo",
    "guidance": "string (specific guidance for the photo/image)",
    "examples_description": "string (describe what good examples look like)"
  },
  "portfolio_recommendations": [
    {
      "item_type": "string (sample_project|case_study|screenshot|template)",
      "description": "string (what to create for this portfolio item)",
      "priority": integer
    }
  ],
  "skill_tests_to_take": ["list of specific Fiverr skill test names"],
  "response_strategy": "string (how to maintain fast response times)"
}
```

### Output Schema

```python
class BioTemplate(BaseModel):
    structure: list[str]
    opening_hook: str = Field(..., min_length=20, max_length=200)
    specialization_section: str = Field(..., min_length=20, max_length=300)
    credentials_to_mention: list[str] = Field(..., min_items=2, max_items=6)
    proof_elements: list[str] = Field(..., min_items=1, max_items=5)
    cta: str = Field(..., min_length=10, max_length=100)
    estimated_word_count: int = Field(..., ge=50, le=500)
    tone: str

class AvatarRecommendation(BaseModel):
    type: str  # headshot | logo
    guidance: str = Field(..., min_length=20, max_length=200)
    examples_description: str = Field(..., min_length=20, max_length=200)

class PortfolioItem(BaseModel):
    item_type: str
    description: str = Field(..., min_length=20, max_length=200)
    priority: int = Field(..., ge=1, le=10)

class ProfileOptimization(BaseModel):
    bio_template: BioTemplate
    avatar_recommendation: AvatarRecommendation
    portfolio_recommendations: list[PortfolioItem] = Field(..., min_items=2, max_items=6)
    skill_tests_to_take: list[str] = Field(default_factory=list, max_items=5)
    response_strategy: str = Field(..., min_length=20, max_length=200)
```

---

## Integration into RecommendationOutput

```python
class RecommendationOutput(BaseModel):
    # ... existing 12 fields (including pricing_strategy from Wave 9) ...

    # NEW — Wave 11
    profile_optimization: Optional[ProfileOptimization] = None
    visual_recommendations: Optional[dict] = None  # From visual pattern analysis

    def completeness_ratio(self) -> float:
        fields = [
            self.gig_titles, self.tag_sets, self.package_structure,
            self.description_outline, self.faq_entries, self.differentiation_angle,
            self.buyer_persona, self.thumbnail_direction, self.upsell_structure,
            self.red_flags, self.niche_viability_assessment,
            self.pricing_strategy,
            self.profile_optimization,   # NEW — 14 fields now
            self.visual_recommendations, # NEW
        ]
        present = sum(1 for f in fields if f is not None)
        return present / len(fields)
```

Updated asyncio.gather() now runs 14 concurrent tasks (11 original + pricing + profile + visual).

---

## Dashboard — Profile Tab (New)

Added to recommendation cards:

```python
with tab_profile:  # New tab: "👤 Profile"
    if rec.profile_optimization:
        po = rec.profile_optimization

        st.markdown("### Bio Template")
        st.markdown(f"**Structure:** {' → '.join(po['bio_template']['structure'])}")
        st.markdown(f"**Opening:** _{po['bio_template']['opening_hook']}_")
        st.markdown(f"**Credentials to mention:** {', '.join(po['bio_template']['credentials_to_mention'])}")
        st.markdown(f"**Proof elements:** {', '.join(po['bio_template']['proof_elements'])}")
        st.markdown(f"**CTA:** _{po['bio_template']['cta']}_")
        st.caption(f"Tone: {po['bio_template']['tone']} | ~{po['bio_template']['estimated_word_count']} words")

        st.markdown("### Avatar")
        st.markdown(f"**Type:** {po['avatar_recommendation']['type']}")
        st.markdown(po['avatar_recommendation']['guidance'])

        st.markdown("### Portfolio Items to Create")
        for item in sorted(po['portfolio_recommendations'], key=lambda x: x['priority']):
            st.markdown(f"{item['priority']}. **{item['item_type']}:** {item['description']}")

        if po.get('skill_tests_to_take'):
            st.markdown("### Skill Tests")
            for test in po['skill_tests_to_take']:
                st.markdown(f"✅ {test}")

        st.markdown(f"### Response Strategy")
        st.markdown(po['response_strategy'])
```

---

## Cost Impact

| Task | Model | Est. Cost/Keyword |
|---|---|---|
| Task 13: Profile optimization | gpt-4o-mini | ~$0.002 |
| Visual classification (top 10 gigs) | gpt-4o vision | ~$0.03 |
| **Total Wave 11 addition** | | **~$0.032/keyword** |

Updated total per recommendation: ~$0.157/keyword (was $0.125 after Wave 9).
With cache: ~$0.08–0.11 effective.
