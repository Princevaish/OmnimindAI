"""
Planner agent responsible for decomposing user queries into step-by-step reasoning.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.utils.prompt_templates import PLANNER_PROMPT

_prompt = PromptTemplate(
    input_variables=["query"],
    template=PLANNER_PROMPT,
)


class PlannerAgent(BaseAgent):
    """Agent that generates a structured reasoning plan for a given user query."""

    async def run(self, input_text: str) -> str:
        """
        Format the query with the planner prompt and invoke the LLM.

        Args:
            input_text: Raw user query to be decomposed into a plan.

        Returns:
            Step-by-step reasoning plan as a string.
        """
        formatted_prompt: str = _prompt.format(query=input_text)
        messages = [HumanMessage(content=formatted_prompt)]
        response = await self.llm.ainvoke(messages)
        return response.content