"""
External tool integration wrappers for agent nodes.

Each module wraps one external data provider (JSearch job board, Exa web
scraper, pgvector semantic search). All tools implement a hermetic offline
fallback so the full agent pipeline can run in CI without real API keys.
Real keys are injected at runtime through environment variables via Settings.
"""

from app.agents.tools.company_intel import fetch_company_intel
from app.agents.tools.job_search import search_jobs
from app.agents.tools.vector_search import search_cv_blocks

__all__ = ["fetch_company_intel", "search_cv_blocks", "search_jobs"]
