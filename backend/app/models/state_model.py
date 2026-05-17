"""
LangGraph shared state schema.

Every field is written by exactly one node and read by downstream nodes.
The separation between `answer` (raw research output) and `final_answer`
(critic-refined output) is deliberate — it preserves the intermediate
result for debugging without conflating the two.
"""

from typing import TypedDict


class AgentState(TypedDict):
    # ── Inputs ──────────────────────────────────────────────────────────────
    user_query: str            # Original user input — never mutated

    # ── Routing metadata (set by router_node) ───────────────────────────────
    requires_web_search: bool  # True  → research_node MUST call web_search()
    requires_rag: bool         # True  → research_node MUST call retriever_tool()
    requires_math: bool        # True  → router short-circuits to calculator
    tools_used: list[str]      # Accumulates tool keys for the response badge

    # ── Per-stage outputs ───────────────────────────────────────────────────
    plan: str                  # Written by planner_node — internal only
    thinking_steps: list[str]  # UI-friendly step labels derived from the plan
    answer: str                # Written by research_node
    final_answer: str          # Written by critic_node (or router short-circuit)