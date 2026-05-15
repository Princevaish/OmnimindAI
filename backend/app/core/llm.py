"""
LLM initialization module using LangChain's ChatGroq integration.
Provides a reusable LLM instance across the project.
"""

from langchain_groq import ChatGroq
from app.core.config import get_settings

settings = get_settings()


def get_llm() -> ChatGroq:
    """
    Instantiate and return a ChatGroq LLM instance.

    Returns:
        ChatGroq: Configured LangChain ChatGroq instance.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.MODEL_NAME,
    )