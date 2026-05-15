"""
Pydantic schemas for API request and response validation.
"""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Schema for incoming query requests."""

    query: str


class QueryResponse(BaseModel):
    """Schema for outgoing query responses."""

    response: str