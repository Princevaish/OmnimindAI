"""
Graph executor — entry point for the service layer.

Returns a structured dict that the service layer packages into QueryResponse.
The plan and thinking_steps are metadata only — never mixed with the answer.
"""

from app.models.state_model import AgentState
from app.graph.graph_builder import compiled_graph
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_THINKING = ["Analyzing query", "Processing request", "Generating answer"]


async def run_graph(query: str) -> dict:
    """
    Execute the compiled LangGraph pipeline and return structured output.

    Returns:
        {
            "response":       str,        # clean final answer only
            "thinking_steps": list[str],  # UI animation labels
            "tools_used":     list[str],  # badge keys
            "plan":           str,        # internal — not for chat bubbles
        }
    """
    logger.info("run_graph — START  query=%r", query)

    initial_state: AgentState = {
        "user_query":          query,
        "requires_web_search": False,
        "requires_rag":        False,
        "requires_math":       False,
        "tools_used":          [],
        "plan":                "",
        "thinking_steps":      [],
        "answer":              "",
        "final_answer":        "",
    }

    final_state: AgentState = await compiled_graph.ainvoke(initial_state)

    final_answer    = final_state.get("final_answer", "").strip()
    plan            = final_state.get("plan", "").strip()
    thinking_steps  = final_state.get("thinking_steps") or _DEFAULT_THINKING
    tools_used      = final_state.get("tools_used") or []

    logger.info(
        "run_graph — DONE  answer_len=%d tools=%s steps=%s",
        len(final_answer), tools_used, thinking_steps,
    )

    return {
        "response":       final_answer,
        "thinking_steps": thinking_steps,
        "tools_used":     tools_used,
        "plan":           plan,           # metadata only — frontend must not render this
    }