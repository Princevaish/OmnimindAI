"""
RAG retrieval module.
Performs similarity search against the vector store and returns relevant text chunks.
"""

from app.rag.vectorstore import get_vectorstore


def retrieve_docs(query: str, k: int = 4) -> list[str]:
    """
    Retrieve the top-k most relevant document chunks for a given query.

    Args:
        query: The search query string.
        k:     Number of top results to retrieve. Defaults to 4.

    Returns:
        A list of page content strings from the most relevant chunks.
    """
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in results]