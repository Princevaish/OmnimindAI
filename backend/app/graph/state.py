"""
LangGraph-compatible state schema for the multi-agent graph pipeline.
Defines the shared state structure passed between graph nodes.
"""

from typing import TypedDict


class AgentState(TypedDict):
    """
    Shared state object passed through the LangGraph agent graph.

    Attributes:
        user_query:   The original input from the user.
        plan:         The step-by-step reasoning plan produced by PlannerAgent.
        final_answer: The conclusive answer produced at the end of the pipeline.
    """

    user_query: str
    plan: str
    final_answer: str