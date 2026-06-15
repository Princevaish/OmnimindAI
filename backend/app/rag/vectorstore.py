"""
Vector store initialization using Chroma and HuggingFace embeddings.

KEY FIXES vs previous version:
  - get_vectorstore() is NOT cached — returns a fresh Chroma handle each
    call so post-ingestion documents are always visible to retrievers.
  - Embeddings are cached (model loading is expensive, ~500ms).
  - A module-level _collection_name constant ensures ingestion and retrieval
    always target the same named collection.
  - get_vectorstore_stats() enables the RAG debug panel.
"""

import os
from functools import lru_cache
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)

CHROMA_PERSIST_DIR: str = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL:    str = "all-MiniLM-L6-v2"
COLLECTION_NAME:    str = "omnimind_documents"


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return a cached HuggingFace embeddings instance.
    Loading the sentence-transformer model takes ~500ms — cache it.
    """
    logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
    emb = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    logger.info("Embedding model loaded — vector dim: 384")
    return emb


def get_vectorstore() -> Chroma:
    """
    Return a Chroma vector store handle.

    NOT cached — each call returns a fresh handle so that documents
    added after server startup are immediately visible.
    The underlying Chroma collection persists to CHROMA_PERSIST_DIR.
    """
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=get_embeddings(),
    )


def get_vectorstore_stats() -> dict:
    """
    Return debug statistics about the current vector store state.
    Used by the RAG debug endpoint.
    """
    try:
        vs = get_vectorstore()
        collection = vs._collection                     # Chroma internal
        count = collection.count()
        # Sample up to 5 documents for preview
        sample = collection.get(limit=5, include=["documents", "metadatas"])
        return {
            "collection_name": COLLECTION_NAME,
            "persist_dir":     CHROMA_PERSIST_DIR,
            "document_count":  count,
            "sample_docs": [
                {
                    "preview": doc[:120] + "…" if len(doc) > 120 else doc,
                    "metadata": meta,
                }
                for doc, meta in zip(
                    sample.get("documents", []),
                    sample.get("metadatas", []),
                )
            ],
        }
    except Exception as exc:
        logger.error("get_vectorstore_stats failed: %s", exc)
        return {"error": str(exc), "document_count": 0}