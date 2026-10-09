"""
Google News RSS and company news fetcher with 7-day TTL.

Extracts dated headlines, dates, and sources from Google News RSS feeds
without any external API keys or authentication.
"""

import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.http import DEFAULT_TIMEOUT
from app.ingestion.security import sanitize_text

logger = logging.getLogger("career_os.ingestion.news")

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


async def fetch_company_news_rss(
    company_name: str,
    max_items: int = 5,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch recent dated news items from Google News RSS.
    Returns list of dicts: [{"title": ..., "date": ..., "source": ..., "url": ...}]
    """
    if not company_name:
        return []

    query = f"{company_name} engineering OR technology OR software"
    params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}

    try:
        async with client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as c:
            resp = await c.get(GOOGLE_NEWS_RSS_URL, params=params)
            if resp.status_code != 200:
                logger.warning(
                    "Google News RSS returned status %d for '%s'",
                    resp.status_code,
                    company_name,
                )
                return []
            content = resp.text

        root = ET.fromstring(content)
        channel = root.find("channel")
        if channel is None:
            return []

        news_items: list[dict[str, Any]] = []
        for item in channel.findall("item")[:max_items]:
            raw_title = item.findtext("title", "")
            raw_pub_date = item.findtext("pubDate", "")
            raw_link = item.findtext("link", "")
            source_elem = item.find("source")
            source_name = (
                source_elem.text
                if source_elem is not None and source_elem.text
                else "Google News"
            )

            # Strip html and sanitize title
            clean_title = sanitize_text(html.unescape(raw_title))
            # Often Google News title ends with " - Source"
            clean_title = re.sub(r"\s+-\s+[^-]+$", "", clean_title)

            # Format publication date
            formatted_date = ""
            if raw_pub_date:
                try:
                    # e.g., 'Mon, 05 Oct 2026 14:00:00 GMT'
                    dt = datetime.strptime(
                        raw_pub_date[:25].strip(), "%a, %d %b %Y %H:%M:%S"
                    )
                    formatted_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = raw_pub_date

            if clean_title:
                news_items.append(
                    {
                        "title": clean_title,
                        "date": formatted_date
                        or datetime.now(UTC).strftime("%Y-%m-%d"),
                        "source": sanitize_text(source_name),
                        "url": raw_link,
                    }
                )

        return news_items

    except Exception as e:
        logger.warning(
            "Failed to fetch Google News RSS for '%s': %s",
            company_name,
            e,
        )
        return []
