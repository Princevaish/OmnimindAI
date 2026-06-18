"""
Web search tool backed by the Tavily Search API via langchain-tavily.

Requires: pip install langchain-tavily
"""

from langchain_tavily import TavilySearch
from app.core.config import get_settings
from app.exceptions.custom_exceptions import ToolException
from app.utils.logger import get_logger

logger = get_logger(__name__)

_settings = get_settings()

_tavily: TavilySearch = TavilySearch(
    tavily_api_key=_settings.TAVILY_API_KEY,
    max_results=5,
    search_depth="advanced",
    include_answer=False,
    include_raw_content=False,
)


def _format_result(item: dict) -> str | None:
    title: str = (item.get("title") or "").strip()
    content: str = (item.get("content") or "").strip()
    if not title and not content:
        return None
    if title and content:
        return f"Title: {title} | Content: {content}"
    return title or content


def web_search(query: str, max_results: int = 5) -> list[str]:
    """
    Search the web via Tavily and return a list of clean text snippets.
    """
    logger.info("web_search START — query: %r  max_results=%d", query, max_results)
    snippets: list[str] = []

    try:
        raw_response = _tavily.invoke({"query": query})
        # TavilySearch.invoke() returns a dict: {"results": [...], "query": ..., ...}
        raw: list[dict] = raw_response.get("results", []) if isinstance(raw_response, dict) else raw_response
        logger.info("web_search — Tavily raw result count: %d", len(raw))

        for item in raw[:max_results]:
            formatted = _format_result(item)
            if formatted:
                snippets.append(formatted)

        logger.info("web_search — usable snippets: %d", len(snippets))

    except ToolException:
        raise
    except Exception as exc:
        logger.error("web_search FAILED — query: %r | error: %s", query, str(exc), exc_info=True)
        raise ToolException(
            message=f"Web search failed: {exc}",
            details={"query": query, "error_type": type(exc).__name__},
        ) from exc

    if not snippets:
        logger.warning("web_search — no usable snippets returned for query: %r", query)

    return snippets