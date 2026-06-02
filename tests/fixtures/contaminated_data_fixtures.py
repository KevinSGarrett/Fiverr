"""
Fixture factories for contaminated and rejection-band test data (R9.6, SCRUM-631).

All factories return plain Python dicts/lists. No DB session required.
"""
from __future__ import annotations


def make_contaminated_keyword_set(
    niche_id: str = "python_automation",
    count: int = 5,
    rsv_score: float = 0.30,
) -> list[dict[str, object]]:
    """Return keyword dicts with RSV-flagged contamination for integration tests."""
    return [
        {
            "keyword_text": f"contaminated_kw_{i}",
            "niche_id": niche_id,
            "rsv_score": rsv_score,
            "is_contaminated": True,
        }
        for i in range(count)
    ]


def make_rejection_band_dataset(
    total: int = 10,
    rejected: int = 3,
    niche_id: str = "python_automation",
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Return (candidates, expected_rejected) for rejection-band tests."""
    candidates: list[dict[str, object]] = [
        {"keyword_text": f"candidate_{i}", "niche_id": niche_id, "index": i}
        for i in range(total)
    ]
    expected_rejected = candidates[:rejected]
    return candidates, expected_rejected


def make_niche_validation_input(
    niche_id: str = "python_automation",
    ghost: bool = False,
) -> dict[str, object]:
    """Return synthetic gig-set input for validate_result_set() for a given niche."""
    on_topic: dict[str, list[str]] = {
        "python_automation": [
            "Python automation script",
            "Python bot development",
            "Automate tasks with Python",
            "Python workflow automation",
            "Python scripting service",
        ],
        "support_kb_readiness": [
            "Knowledge base setup",
            "Help center documentation",
            "Support wiki creation",
            "KB article writing",
            "Customer support docs",
        ],
        "gumloop_lindy_workflow": [
            "Gumloop workflow automation",
            "Lindy AI workflow",
            "No-code automation flow",
            "Gumloop integration",
            "Lindy AI assistant setup",
        ],
        "mcp_ai_agent": [
            "MCP AI agent development",
            "Model context protocol setup",
            "AI agent integration",
            "MCP server configuration",
            "AI agent orchestration",
        ],
        "python_web_scraping": [
            "Python web scraper",
            "Web scraping with Python",
            "Scrapy BeautifulSoup scraper",
            "Data extraction Python",
            "Python crawler",
        ],
        "ai_agent_development": [
            "AI agent development",
            "Autonomous AI agent",
            "LLM agent workflow",
            "Agent-based automation",
            "Multi-agent system",
        ],
        "workflow_automation": [
            "Workflow automation setup",
            "Process automation consulting",
            "Business workflow builder",
            "Automation consultant",
            "RPA workflow design",
        ],
        "prd_ai_saas": [
            "AI SaaS PRD writing",
            "Product requirements document AI",
            "SaaS feature specification",
            "AI product documentation",
            "PRD template AI product",
        ],
        "ai_tool_llm_integration": [
            "LLM API integration",
            "GPT integration service",
            "AI tool development",
            "LLM workflow setup",
            "OpenAI API integration",
        ],
    }
    off_topic = [
        "Logo design service",
        "Social media marketing",
        "Video editing professional",
        "SEO optimization service",
        "Graphic design logo",
    ]
    titles = off_topic if ghost else on_topic.get(niche_id, on_topic["python_automation"])
    keyword = f"{niche_id.replace('_', ' ')} service"
    return {"niche_id": niche_id, "keyword": keyword, "gig_titles": titles}
