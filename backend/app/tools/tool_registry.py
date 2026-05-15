"""
Central registry for all tools available to agents.

All tools are registered at import time. Agents retrieve tools
via get_tools() rather than importing callables directly — this
keeps the agent layer decoupled from tool implementation details.
"""

from typing import Callable
from app.tools.web_search import web_search
from app.tools.retriever_tool import retriever_tool
from app.tools.system_tools import get_current_date

_registry: dict[str, Callable] = {}


def register_tool(name: str, func: Callable) -> None:
    """
    Register a callable tool under a given name.

    Args:
        name: Unique identifier for the tool.
        func: The callable to register.
    """
    _registry[name] = func


def get_tools() -> dict[str, Callable]:
    """
    Retrieve all registered tools.

    Returns:
        A shallow copy of the tool registry dict.
    """
    return dict(_registry)


# ---------------------------------------------------------------------------
# Registration — executed once at import time
# ---------------------------------------------------------------------------
register_tool("web_search", web_search)
register_tool("retriever_tool", retriever_tool)
register_tool("get_current_date", get_current_date)