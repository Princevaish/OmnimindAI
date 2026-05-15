"""
API route definitions.

Endpoints:
    POST /ask              — run the full multi-agent pipeline.
    GET  /debug/websearch  — test the web search tool in isolation.
"""

from fastapi import APIRouter, HTTPException
from app.api.schemas import QueryRequest, QueryResponse
from app.services.agent_service import run_agent_pipeline
from app.tools.web_search import web_search
from app.exceptions.custom_exceptions import AgentException
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest) -> QueryResponse:
    """
    Accept a user query, run the multi-agent pipeline, return the result.

    Args:
        request: QueryRequest with a non-empty query string.

    Returns:
        QueryResponse containing the pipeline's final answer.

    Raises:
        HTTPException 400: propagated AgentException from the pipeline.
        HTTPException 500: any other unexpected failure.
    """
    logger.info("POST /ask — query: %r", request.query)

    try:
        result: str = await run_agent_pipeline(request.query)
        logger.info("POST /ask — completed successfully")
        return QueryResponse(response=result)

    except AgentException as exc:
        logger.warning("POST /ask — AgentException: %s | details=%s", exc.message, exc.details)
        raise HTTPException(status_code=400, detail=exc.message) from exc

    except Exception as exc:
        logger.error("POST /ask — unexpected error: %s", str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Pipeline failed unexpectedly.") from exc


@router.get("/debug/websearch")
async def debug_websearch(q: str = "latest AI news") -> dict:
    """
    Debug endpoint: run web_search in isolation and return raw snippets.

    Usage:
        GET /api/v1/debug/websearch?q=your+query+here

    Args:
        q: Search query string. Defaults to "latest AI news".

    Returns:
        Dict with query, result count, and list of snippets.
    """
    logger.info("GET /debug/websearch — query: %r", q)

    try:
        snippets: list[str] = web_search(q)
        logger.info("GET /debug/websearch — returned %d snippet(s)", len(snippets))
        return {"query": q, "count": len(snippets), "results": snippets}

    except Exception as exc:
        logger.error("GET /debug/websearch — error: %s", str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Web search failed.") from exc