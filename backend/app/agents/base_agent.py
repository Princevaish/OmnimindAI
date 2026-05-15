"""
Base agent abstraction providing a common interface for all agents.
All concrete agents must extend BaseAgent and implement the run() method.
"""

from abc import ABC, abstractmethod
from langchain_groq import ChatGroq


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    Attributes:
        llm: The LangChain LLM instance used for inference.
    """

    def __init__(self, llm: ChatGroq) -> None:
        """
        Initialize the agent with an LLM instance.

        Args:
            llm: A configured LangChain-compatible LLM instance.
        """
        self.llm = llm

    @abstractmethod
    async def run(self, input_text: str) -> str:
        """
        Execute the agent logic for a given input.

        Args:
            input_text: The user query or task description.

        Returns:
            The agent's string output.
        """
        ...