"""
Agent service layer — thin orchestration wrapper.

Converts run_graph() output into a QueryResponse.
The service layer is the last place plan text could leak to the API —
it explicitly excludes plan from the response body in production,
but preserves it in the QueryResponse.plan field for debugging.
"""

from app.graph.executor import run_graph
from app.api.schemas import QueryResponse
from app.exceptions.custom_exceptions import AgentException
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_agent_pipeline(query: str) -> QueryResponse:
    """
    Run the full multi-agent pipeline and return a structured QueryResponse.

    Args:
        query: Raw user input.

    Returns:
        QueryResponse with response, thinking_steps, tools_used, and plan.

    Raises:
        AgentException on pipeline failure.
    """
    logger.info("run_agent_pipeline — START  query=%r", query)

    try:
        result = await run_graph(query)
        logger.info(
            "run_agent_pipeline — COMPLETE  tools=%s  steps=%s",
            result["tools_used"], result["thinking_steps"],
        )
        return QueryResponse(
            response=result["response"],
            thinking_steps=result["thinking_steps"],
            tools_used=result["tools_used"],
            plan=result["plan"],      # kept for /debug endpoints; frontend ignores
        )
    except AgentException:
        raise
    except Exception as exc:
        logger.error("run_agent_pipeline — FAILED: %s", exc, exc_info=True)
        raise AgentException(
            message=f"Pipeline failed: {exc}",
            details={"query": query, "error_type": type(exc).__name__},
        ) from exc