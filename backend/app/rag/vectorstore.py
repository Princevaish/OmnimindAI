"""
Vector store initialization using Chroma and HuggingFace embeddings.
Provides a singleton-style accessor for the shared vector store instance.
"""

from functools import lru_cache
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PERSIST_DIR: str = "./chroma_db"
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"


@lru_cache()
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return a cached HuggingFace embeddings instance.

    Returns:
        HuggingFaceEmbeddings using the configured sentence-transformer model.
    """
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def get_vectorstore() -> Chroma:
    """
    Initialize and return a Chroma vector store with HuggingFace embeddings.

    Returns:
        A Chroma instance backed by the local persistence directory.
    """
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=get_embeddings(),
    )