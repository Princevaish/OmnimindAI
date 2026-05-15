"""
RAG retriever exposed as a named tool compatible with the tool registry.
Wraps retrieve_docs for use by agents.
"""

from app.rag.retriever import retrieve_docs


def retriever_tool(query: str) -> list[str]:
    """
    Tool wrapper around the RAG retriever.

    Args:
        query: The user query or topic to retrieve context for.

    Returns:
        A list of relevant document chunk strings.
    """
    return retrieve_docs(query)