"""
Agent service layer — orchestrates the full LangGraph multi-agent pipeline.

Wraps every stage in structured logging and converts all unhandled
exceptions into AgentException so the API layer receives a typed,
loggable error rather than a raw LLM stack trace.
"""

from app.graph.executor import run_graph
from app.exceptions.custom_exceptions import AgentException
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_agent_pipeline(query: str) -> str:
    """
    Execute the full multi-agent pipeline for a given user query.

    Stages (orchestrated inside run_graph via LangGraph):
        1. router_node   — tool short-circuit check
        2. planner_node  — step-by-step reasoning plan
        3. research_node — grounded answer via RAG + web search
        4. critic_node   — reflection and answer improvement

    Args:
        query: Raw user input string from the API layer.

    Returns:
        Formatted pipeline output:
            "Plan:\\n{plan}\\n\\nAnswer:\\n{final_answer}"
            or just "{final_answer}" for router short-circuits.

    Raises:
        AgentException: wraps any exception raised during graph execution,
            preserving the original message and query as structured details.
    """
    logger.info("Pipeline START — query: %r", query)

    try:
        logger.info("Stage: router_node — evaluating query intent")
        result: str = await run_graph(query)
        logger.info("Pipeline COMPLETE — output length: %d chars", len(result))
        logger.debug("Pipeline output: %s", result)
        return result

    except AgentException:
        # Already typed — re-raise without wrapping
        raise

    except Exception as exc:
        logger.error(
            "Pipeline FAILED — query: %r | error: %s",
            query,
            str(exc),
            exc_info=True,
        )
        raise AgentException(
            message=f"Agent pipeline failed: {exc}",
            details={"query": query, "error_type": type(exc).__name__},
        ) from exc