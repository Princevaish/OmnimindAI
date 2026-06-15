"""
RAG retriever exposed as a named tool.
"""

from app.rag.retriever import retrieve_docs


def retriever_tool(query: str) -> list[str]:
    """
    Tool wrapper around the RAG retriever.

    Args:
        query: The user query or topic to retrieve context for.

    Returns:
        List of relevant document chunk strings.
    """
    return retrieve_docs(query)