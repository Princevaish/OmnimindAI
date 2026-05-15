"""
Graph executor: sole entry point for running the compiled LangGraph pipeline.

Output formatting rules:
    Short-circuit path (router resolved the query):
        → return final_answer directly — no plan or pipeline ran.

    Full pipeline path (planner + researcher + critic all ran):
        → return "Plan:\\n{plan}\\n\\nAnswer:\\n{final_answer}"

Short-circuit detection:
    final_answer is non-empty AND plan is empty.
    This is a reliable invariant: planner_node always writes a non-empty
    plan string when it runs, so an empty plan means the router exited early.
"""

from app.models.state_model import AgentState
from app.graph.graph_builder import compiled_graph


def _was_short_circuited(state: AgentState) -> bool:
    """
    Determine whether the graph exited via the router without running the pipeline.

    Args:
        state: Final pipeline state after graph completion.

    Returns:
        True if router resolved the query directly; False if full pipeline ran.
    """
    has_answer: bool = bool(state.get("final_answer", "").strip())
    has_plan: bool = bool(state.get("plan", "").strip())
    return has_answer and not has_plan


async def run_graph(query: str) -> str:
    """
    Initialise pipeline state, execute the compiled graph, return formatted output.

    Output:
        Short-circuit : "{final_answer}"
        Full pipeline : "Plan:\\n{plan}\\n\\nAnswer:\\n{final_answer}"

    Args:
        query: Raw user input string from the service layer.

    Returns:
        Formatted string output appropriate to the execution path taken.

    Raises:
        Exception: Propagates any node-level or LLM errors to the caller.
    """
    initial_state: AgentState = {
        "user_query": query,
        "plan": "",
        "answer": "",
        "final_answer": "",
    }

    final_state: AgentState = await compiled_graph.ainvoke(initial_state)

    plan: str = final_state.get("plan", "").strip()
    final_answer: str = final_state.get("final_answer", "").strip()

    if _was_short_circuited(final_state):
        return final_answer

    return f"Plan:\n{plan}\n\nAnswer:\n{final_answer}"