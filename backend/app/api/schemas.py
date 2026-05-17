"""
API request and response schemas.

The structured response format separates the clean answer from
internal reasoning metadata so the frontend never has to parse
or sanitize raw agent output.
"""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Incoming user query."""
    query: str


class QueryResponse(BaseModel):
    """
    Structured response returned to the frontend.

    Fields:
        response:       The clean final answer — the ONLY text rendered in chat.
        thinking_steps: Short UI-friendly labels for the ThinkingPipeline.
        tools_used:     Keys shown as tool badges ("web_search", "rag", etc.)
        plan:           Internal reasoning text — NEVER rendered in chat bubbles.
    """
    response: str
    thinking_steps: list[str] = []
    tools_used: list[str] = []
    plan: str = ""