"""
LangGraph graph builder with intelligent entry routing and conditional retry.

Graph topology:

    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   START → router_node ──[final_answer set]──→ END       │
    │                    │                                    │
    │                    └──[no final_answer]──→ planner       │
    │                                              │          │
    │                                          researcher      │
    │                                              │          │
    │                                           critic ──→ END │
    │                                              │          │
    │                                 [empty final_answer]     │
    │                                              └──→ researcher
    └─────────────────────────────────────────────────────────┘

Conditional edges:
    after router_node : routes to END or planner based on final_answer presence.
    after critic_node : routes to END or researcher based on final_answer content.
"""

from langgraph.graph import StateGraph, START, END
from app.models.state_model import AgentState
from app.graph.nodes import (
    router_node,
    planner_node,
    research_node,
    critic_node,
)

# ---------------------------------------------------------------------------
# Routing sentinels — string keys must match registered node names exactly
# ---------------------------------------------------------------------------
_ROUTE_END = "__end__"           # LangGraph's internal END sentinel string
_ROUTE_PLANNER = "planner"
_ROUTE_RESEARCHER = "researcher"


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _route_after_router(state: AgentState) -> str:
    """
    Decide where to go after router_node.

    Condition:
        final_answer is non-empty → END   (short-circuit: tool query resolved)
        final_answer is empty     → planner (full pipeline required)

    Args:
        state: Pipeline state after router_node has run.

    Returns:
        Node name string or END sentinel.
    """
    if state.get("final_answer", "").strip():
        return _ROUTE_END
    return _ROUTE_PLANNER


def _route_after_critic(state: AgentState) -> str:
    """
    Decide where to go after critic_node.

    Condition:
        final_answer is non-empty → END        (success path)
        final_answer is empty     → researcher  (retry path)

    Args:
        state: Pipeline state after critic_node has run.

    Returns:
        Node name string or END sentinel.
    """
    if state.get("final_answer", "").strip():
        return _ROUTE_END
    return _ROUTE_RESEARCHER


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Construct and compile the multi-agent LangGraph pipeline.

    Returns:
        A compiled LangGraph instance ready for async invocation.
    """
    builder = StateGraph(AgentState)

    # --- Register nodes ---
    builder.add_node("router", router_node)
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", research_node)
    builder.add_node("critic", critic_node)

    # --- Static entry edge ---
    builder.add_edge(START, "router")

    # --- Conditional edge: router → END or planner ---
    builder.add_conditional_edges(
        "router",
        _route_after_router,
        {
            _ROUTE_END: END,
            _ROUTE_PLANNER: "planner",
        },
    )

    # --- Static edges: full pipeline ---
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "critic")

    # --- Conditional edge: critic → END or retry researcher ---
    builder.add_conditional_edges(
        "critic",
        _route_after_critic,
        {
            _ROUTE_END: END,
            _ROUTE_RESEARCHER: "researcher",
        },
    )

    return builder.compile()


# Module-level singleton — compiled once at import time, reused per request.
compiled_graph = build_graph()