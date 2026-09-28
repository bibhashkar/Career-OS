"""
Intel agent node executing web research and company dossier synthesis.

A generic resume and boilerplate interview prep fail when applying to
competitive engineering organizations. The intel node conducts targeted research
on the target employer — extracting their verified tech stack, recent product
launches, business model, and engineering culture.

Downstream Dependencies:
  - ``tailor_node`` uses the gathered tech stack and domain notes to align the
    candidate's professional summary with the employer's architecture.
  - ``coach_node`` grounds mock interview questions directly in the company's
    active engineering technologies.
"""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.company_intel import fetch_company_intel


async def intel_node(state: AgentState) -> dict[str, Any]:
    """
    Gather intelligence on company tech stacks, recent news, and business model.

    Reads:
      - ``job_details``: Identifies target company name.

    Writes:
      - ``company_dossier``: Researched tech stack, news, culture, and model.
      - ``status``: Set to ``"intel_gathered"``.
      - ``messages``: System log summarizing identified core technologies.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update containing the synthesized company dossier.
    """
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
