"""
LangGraph StateGraph assembly.

Graph topology:
    START → router_node
                │
    ┌───────────┴────────────────────────────────────┐
    │ _route_after_router()                          │
    │                                               │
    │  final_answer set → END  (date/math)          │
    │  otherwise        → planner_node              │
    └───────────────────────────────────────────────┘
                              │
                         planner_node
                              │
                         research_node  ←──────────┐
                              │                    │
                          critic_node              │
                              │                    │
    ┌─────────────────────────┴────────────────┐   │
    │ _route_after_critic()                    │   │
    │                                         │   │
    │  final_answer non-empty → END           │   │
    │  final_answer empty     → research_node ────┘
    └─────────────────────────────────────────┘
"""

from langgraph.graph import StateGraph, START, END
from app.models.state_model import AgentState
from app.graph.nodes import router_node, planner_node, research_node, critic_node


def _route_after_router(state: AgentState) -> str:
    if state.get("final_answer", "").strip():
        return "__end__"
    return "planner"


def _route_after_critic(state: AgentState) -> str:
    if state.get("final_answer", "").strip():
        return "__end__"
    return "researcher"


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("router",     router_node)
    builder.add_node("planner",    planner_node)
    builder.add_node("researcher", research_node)
    builder.add_node("critic",     critic_node)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        _route_after_router,
        {"__end__": END, "planner": "planner"},
    )

    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "critic")

    builder.add_conditional_edges(
        "critic",
        _route_after_critic,
        {"__end__": END, "researcher": "researcher"},
    )

    return builder.compile()


compiled_graph = build_graph()