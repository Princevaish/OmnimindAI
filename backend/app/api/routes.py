"""
API routes — accepts queries, returns structured QueryResponse.

The route returns the full QueryResponse JSON including thinking_steps and
tools_used. The frontend MUST NOT render the plan field in chat bubbles.
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
    Run the multi-agent pipeline for a user query.

    Returns a structured response — the frontend should:
      - Render only `response` in the chat bubble
      - Animate `thinking_steps` in ThinkingPipeline
      - Display `tools_used` as tool badges
      - Never render `plan` directly
    """
    logger.info("POST /ask — query: %r", request.query)
    try:
        result = await run_agent_pipeline(request.query)
        logger.info("POST /ask — OK  tools=%s", result.tools_used)
        return result
    except AgentException as exc:
        logger.warning("POST /ask — AgentException: %s", exc.message)
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        logger.error("POST /ask — unexpected: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Pipeline failed unexpectedly.") from exc


@router.get("/debug/websearch")
async def debug_websearch(q: str = "latest AI news") -> dict:
    """Test Tavily web search in isolation."""
    logger.info("GET /debug/websearch — q=%r", q)
    try:
        snippets = web_search(q)
        return {"query": q, "count": len(snippets), "results": snippets}
    except Exception as exc:
        logger.error("GET /debug/websearch — %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Web search failed.") from exc