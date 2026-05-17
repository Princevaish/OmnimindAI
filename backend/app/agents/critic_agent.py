"""
Critic agent — answer evaluation and refinement.
Stays within its single responsibility: improve or pass through.
"""

from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.utils.prompt_templates import CRITIC_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CriticAgent(BaseAgent):
    """Evaluates and optionally improves the research answer."""

    async def run(self, input_text: str) -> str:
        """
        Args:
            input_text: The answer string produced by ResearchAgent.

        Returns:
            Improved or identical answer string.
        """
        logger.info("CriticAgent — evaluating answer (%d chars)", len(input_text))
        prompt = CRITIC_PROMPT.format(answer=input_text)
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        return response.content.strip()