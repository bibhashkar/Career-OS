"""Intel agent node executing web scraping and company intelligence research."""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.company_intel import fetch_company_intel


async def intel_node(state: AgentState) -> dict[str, Any]:
    """Gather company intelligence on tech stacks, recent news, and model."""
    job_details = state.get("job_details") or {}
    company_name = job_details.get("company_name", "NexusAI Labs")

    dossier = await fetch_company_intel(company_name)
    top_stack = ", ".join(dossier.get("tech_stack", [])[:4])

    return {
        "company_dossier": dossier,
        "status": "intel_gathered",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Intel node gathered intelligence on '{company_name}'. "
                    f"Identified core tech stack: {top_stack}."
                ),
            }
        ],
    }
