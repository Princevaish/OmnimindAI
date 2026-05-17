"""
Planner agent — task decomposition and tool routing.

ROLE CONTRACT
─────────────
The Planner does NOT answer queries. It outputs a JSON routing decision
that tells the LangGraph graph which tools the Research node must invoke.

Output format (parsed by planner_node in nodes.py):
{
  "requires_web_search": bool,
  "requires_rag": bool,
  "requires_math": bool,
  "plan": str,
  "thinking_steps": list[str]
}
"""

import json
import re
from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.utils.prompt_templates import PLANNER_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Fallback thinking steps when JSON parsing fails
_DEFAULT_THINKING = ["Analyzing query", "Routing tools", "Processing request", "Refining answer"]


class PlannerAgent(BaseAgent):
    """
    Decomposes the user query into a routing decision.
    Returns a dict (not a string) so the node can update AgentState directly.
    """

    async def run(self, input_text: str) -> dict:
        """
        Analyze the query and return a routing decision dict.

        Args:
            input_text: Raw user query.

        Returns:
            Dict with keys: requires_web_search, requires_rag, requires_math,
            plan, thinking_steps.
        """
        logger.info("PlannerAgent — analyzing query: %r", input_text)

        formatted = PLANNER_PROMPT.format(query=input_text)
        messages = [HumanMessage(content=formatted)]

        try:
            response = await self.llm.ainvoke(messages)
            raw = response.content.strip()
            logger.debug("PlannerAgent — raw response: %s", raw)

            # Strip markdown fences if the LLM wraps in ```json ... ```
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

            decision = json.loads(raw)

            # Sanitize and apply defaults
            result = {
                "requires_web_search": bool(decision.get("requires_web_search", False)),
                "requires_rag":        bool(decision.get("requires_rag", False)),
                "requires_math":       bool(decision.get("requires_math", False)),
                "plan":                str(decision.get("plan", "Executing pipeline")),
                "thinking_steps":      decision.get("thinking_steps", _DEFAULT_THINKING),
            }

            logger.info(
                "PlannerAgent — routing: web=%s rag=%s math=%s",
                result["requires_web_search"],
                result["requires_rag"],
                result["requires_math"],
            )
            return result

        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("PlannerAgent — JSON parse failed (%s), using fallback routing", exc)
            # Fallback: if unsure, try web search
            return {
                "requires_web_search": True,
                "requires_rag": False,
                "requires_math": False,
                "plan": "Searching for information to answer the query",
                "thinking_steps": _DEFAULT_THINKING,
            }