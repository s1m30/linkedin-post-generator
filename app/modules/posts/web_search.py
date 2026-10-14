import logging
from typing import List

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def search_web(query: str, max_results: int = 7) -> List[str]:
    """
    Searches the Brave Search API for a query and returns a list of result URLs.
    Best-effort: callers should treat auto-fetched sources as optional and
    proceed without them if the search fails or no key is configured.
    """
    if not settings.BRAVE_API_KEY:
        logger.warning("BRAVE_API_KEY is not set; skipping auto web search for query '%s'", query)
        return []

    try:
        response = httpx.get(
            BRAVE_SEARCH_URL,
            params={"q": query, "count": max_results},
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": settings.BRAVE_API_KEY,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        results = response.json().get("web", {}).get("results", [])
        return [r["url"] for r in results if r.get("url")][:max_results]
    except Exception as e:
        logger.warning("Brave web search failed for query '%s': %s", query, e)
        return []
