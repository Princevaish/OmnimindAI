"""
Custom exception hierarchy for the application.

All domain exceptions inherit from AppException so FastAPI exception
handlers can catch them with a single handler registration, while still
allowing fine-grained catches in business logic (ToolException,
AgentException, etc.).

Usage:
    raise ToolException("Tavily returned no results", details={"query": q})
    raise AgentException("Planner failed", details={"stage": "planner"})
"""

from typing import Any


class AppException(Exception):
    """
    Base exception for all application-level errors.

    Attributes:
        message: Human-readable error description.
        details: Optional structured context (query, stage, tool name, etc.)
                 passed through to the error response and logs.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.details: dict[str, Any] = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details})"


class ToolException(AppException):
    """
    Raised when an external tool (web search, retriever, calculator…)
    fails or returns unusable output.
    """


class AgentException(AppException):
    """
    Raised when an agent stage (planner, researcher, critic) or the
    LangGraph pipeline encounters an unrecoverable error.
    """