"""
Document ingestion pipeline for the RAG system.
Splits raw text into chunks and stores them in the vector store.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.rag.vectorstore import get_vectorstore

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
)


def ingest_text(text: str) -> None:
    """
    Split a raw text string into chunks and persist them in the vector store.

    Args:
        text: The raw text content to ingest.
    """
    chunks: list[Document] = _splitter.create_documents([text])
    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)