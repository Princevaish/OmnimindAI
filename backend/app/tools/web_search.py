"""
Web search tool backed by the Tavily Search API via LangChain.

All print() statements replaced with structured logger calls so output
is captured by the centralised logging system and carries consistent
timestamps, levels, and module names.
"""

from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.config import get_settings
from app.exceptions.custom_exceptions import ToolException
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Initialisation — resolved through the central settings singleton
# ---------------------------------------------------------------------------

_settings = get_settings()

_tavily: TavilySearchResults = TavilySearchResults(
    tavily_api_key=_settings.TAVILY_API_KEY,
    max_results=5,
    search_depth="advanced",
    include_answer=False,
    include_raw_content=False,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_result(item: dict) -> str | None:
    """
    Extract and format a single Tavily result dict into a readable string.

    Args:
        item: Result dict with "title" and "content" keys.

    Returns:
        "Title: … | Content: …" string, or None if both fields are empty.
    """
    title: str = (item.get("title") or "").strip()
    content: str = (item.get("content") or "").strip()

    if not title and not content:
        return None
    if title and content:
        return f"Title: {title} | Content: {content}"
    return title or content


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def web_search(query: str, max_results: int = 5) -> list[str]:
    """
    Search the web via Tavily and return a list of clean text snippets.

    Args:
        query:       The search query string.
        max_results: Maximum number of results to return. Defaults to 5.

    Returns:
        List of non-empty formatted strings.

    Raises:
        ToolException: if Tavily raises an unrecoverable error.
    """
    logger.info("web_search START — query: %r  max_results=%d", query, max_results)

    snippets: list[str] = []

    try:
        raw: list[dict] = _tavily.invoke({"query": query})
        logger.info("web_search — Tavily raw result count: %d", len(raw))

        for item in raw[:max_results]:
            formatted = _format_result(item)
            if formatted:
                snippets.append(formatted)

        logger.info("web_search — usable snippets: %d", len(snippets))

    except ToolException:
        raise                                   # already typed, don't rewrap

    except Exception as exc:
        logger.error(
            "web_search FAILED — query: %r | error: %s",
            query,
            str(exc),
            exc_info=True,
        )
        raise ToolException(
            message=f"Web search failed: {exc}",
            details={"query": query, "error_type": type(exc).__name__},
        ) from exc

    if not snippets:
        logger.warning("web_search — no usable snippets returned for query: %r", query)

    return snippets