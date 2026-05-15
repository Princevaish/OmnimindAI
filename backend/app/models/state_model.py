"""
Shared state schema for the LangGraph multi-agent pipeline.
Passed between every node in the graph; each node reads and writes its slice.
"""

from typing import TypedDict


class AgentState(TypedDict):
    """
    Canonical state object threaded through the LangGraph pipeline.

    Attributes:
        user_query:   Original raw input from the user.
        plan:         Step-by-step reasoning plan produced by PlannerAgent.
        answer:       Grounded research answer produced by ResearchAgent.
        final_answer: Refined answer produced by CriticAgent.
    """

    user_query: str
    plan: str
    answer: str
    final_answer: str