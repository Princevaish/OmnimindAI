"""
Critic agent responsible for evaluating and improving agent-generated answers.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.utils.prompt_templates import CRITIC_PROMPT

_prompt = PromptTemplate(
    input_variables=["answer"],
    template=CRITIC_PROMPT,
)


class CriticAgent(BaseAgent):
    """Agent that critiques and optionally improves a previously generated answer."""

    async def run(self, input_text: str) -> str:
        """
        Evaluate and optionally improve the provided answer.

        Args:
            input_text: Candidate answer to evaluate.

        Returns:
            Improved answer, or the original if no improvement is needed.
        """
        formatted_prompt: str = _prompt.format(answer=input_text)
        messages = [HumanMessage(content=formatted_prompt)]
        response = await self.llm.ainvoke(messages)
        return response.content