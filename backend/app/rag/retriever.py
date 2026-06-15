"""
RAG retrieval with detailed logging and confidence scores.

The key diagnostic addition is logging the actual retrieved chunks
and their similarity scores — this immediately reveals whether
retrieval is finding the right content or returning nothing.
"""

from langchain_chroma import Chroma
from app.rag.vectorstore import get_vectorstore
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_K = 4
_SCORE_THRESHOLD = 0.3       # Cosine similarity — lower = less similar
                              # Chroma returns distance (lower = better match)


def retrieve_docs(query: str, k: int = _DEFAULT_K) -> list[str]:
    """
    Retrieve top-k relevant document chunks with similarity filtering.

    Args:
        query: The search query string.
        k:     Number of results to return.

    Returns:
        List of relevant page_content strings (may be empty).
    """
    logger.info("retrieve_docs — query=%r  k=%d", query, k)

    vectorstore = get_vectorstore()

    # Check collection is non-empty before searching
    try:
        count = vectorstore._collection.count()
        logger.info("retrieve_docs — collection has %d documents", count)
        if count == 0:
            logger.warning(
                "retrieve_docs — collection is EMPTY. "
                "No documents have been ingested yet."
            )
            return []
    except Exception as exc:
        logger.warning("retrieve_docs — could not check collection size: %s", exc)

    # Use similarity_search_with_score for diagnostic logging
    try:
        results_with_scores = vectorstore.similarity_search_with_score(query, k=k)
    except Exception as exc:
        logger.error("retrieve_docs — similarity_search failed: %s", exc, exc_info=True)
        return []

    logger.info("retrieve_docs — raw results: %d", len(results_with_scores))

    chunks: list[str] = []
    for i, (doc, score) in enumerate(results_with_scores):
        # Chroma returns L2 distance (lower = more similar)
        # Convert to a 0-1 similarity score for readability
        similarity = max(0.0, 1.0 - score)
        logger.info(
            "retrieve_docs — result[%d]  score=%.4f  similarity=%.4f  "
            "source=%r  preview=%r",
            i,
            score,
            similarity,
            doc.metadata.get("source", "unknown"),
            doc.page_content[:100],
        )
        chunks.append(doc.page_content)

    if not chunks:
        logger.warning(
            "retrieve_docs — no chunks returned for query %r. "
            "Check: (1) documents are ingested, "
            "(2) query is semantically related to content, "
            "(3) collection name matches between ingestion and retrieval.",
            query,
        )

    return chunks


def retrieve_docs_with_metadata(query: str, k: int = _DEFAULT_K) -> list[dict]:
    """
    Extended retrieval returning chunks with scores and metadata.
    Used by the RAG debug endpoint and citation system.

    Returns:
        List of dicts: {content, score, similarity, source, metadata}
    """
    logger.info("retrieve_docs_with_metadata — query=%r  k=%d", query, k)

    vectorstore = get_vectorstore()
    results: list[dict] = []

    try:
        raw = vectorstore.similarity_search_with_score(query, k=k)
    except Exception as exc:
        logger.error("retrieve_docs_with_metadata — failed: %s", exc, exc_info=True)
        return []

    for doc, score in raw:
        similarity = round(max(0.0, 1.0 - score), 4)
        results.append({
            "content":    doc.page_content,
            "preview":    doc.page_content[:150] + "…" if len(doc.page_content) > 150 else doc.page_content,
            "score":      round(float(score), 4),
            "similarity": similarity,
            "source":     doc.metadata.get("source", "unknown"),
            "metadata":   doc.metadata,
        })

    logger.info(
        "retrieve_docs_with_metadata — returned %d results  "
        "top_similarity=%.4f",
        len(results),
        results[0]["similarity"] if results else 0.0,
    )
    return results