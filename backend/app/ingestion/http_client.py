"""
HTTP client utilities for ingestion pipelines and adapters.
"""

from app.core.http import DEFAULT_TIMEOUT, execute_with_retry, resolve_async_client

__all__ = ["DEFAULT_TIMEOUT", "execute_with_retry", "resolve_async_client"]

