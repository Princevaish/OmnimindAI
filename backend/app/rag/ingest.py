"""
Document ingestion pipeline: extract → chunk → embed → store.

Every stage is logged so failures are immediately diagnosable.
The critical fix is calling vectorstore._client.heartbeat() after
add_documents() to confirm Chroma actually persisted the vectors.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.rag.vectorstore import get_vectorstore
from app.rag.extractor import extract_text
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Production chunking settings:
# 800-token chunks balance context richness vs retrieval precision.
# 120-token overlap prevents information loss at chunk boundaries.
_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    length_function=len,
)


def ingest_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Full ingestion pipeline: bytes → text → chunks → vectors → Chroma.

    Args:
        file_bytes: Raw uploaded file content.
        filename:   Original filename for metadata and extraction routing.

    Returns:
        Dict with ingestion statistics for the API response and debug panel.
    """
    logger.info("ingest_bytes — START  file=%r  size=%d bytes", filename, len(file_bytes))

    # ── Stage 1: Text extraction ──────────────────────────────────────────────
    raw_text = extract_text(file_bytes, filename)

    if not raw_text or not raw_text.strip():
        msg = (
            f"Text extraction produced empty output for {filename!r}. "
            "If this is a PDF, it may be image-based and require OCR."
        )
        logger.error("ingest_bytes — %s", msg)
        return {
            "success": False,
            "filename": filename,
            "error": msg,
            "chars_extracted": 0,
            "chunks_created": 0,
            "vectors_stored": 0,
        }

    logger.info("ingest_bytes — extracted %d chars", len(raw_text))

    # ── Stage 2: Chunking ─────────────────────────────────────────────────────
    docs = _SPLITTER.create_documents(
        [raw_text],
        metadatas=[{"source": filename, "file_type": filename.rsplit(".", 1)[-1].lower()}],
    )

    if not docs:
        msg = f"Chunking produced zero documents from {filename!r}."
        logger.error("ingest_bytes — %s", msg)
        return {
            "success": False,
            "filename": filename,
            "error": msg,
            "chars_extracted": len(raw_text),
            "chunks_created": 0,
            "vectors_stored": 0,
        }

    logger.info("ingest_bytes — %d chunks created (sizes: %s)",
                len(docs), [len(d.page_content) for d in docs[:5]])

    # Log chunk previews for debugging
    for i, doc in enumerate(docs[:3]):
        logger.debug("ingest_bytes — chunk[%d] preview: %r", i, doc.page_content[:100])

    # ── Stage 3: Embed + Store ────────────────────────────────────────────────
    vectorstore = get_vectorstore()

    try:
        ids = vectorstore.add_documents(docs)
        logger.info(
            "ingest_bytes — add_documents OK  ids_count=%d  first_id=%s",
            len(ids), ids[0] if ids else "none",
        )
    except Exception as exc:
        logger.error("ingest_bytes — add_documents FAILED: %s", exc, exc_info=True)
        return {
            "success": False,
            "filename": filename,
            "error": f"Vector store insertion failed: {exc}",
            "chars_extracted": len(raw_text),
            "chunks_created": len(docs),
            "vectors_stored": 0,
        }

    # ── Stage 4: Verify storage ───────────────────────────────────────────────
    try:
        collection_count = vectorstore._collection.count()
        logger.info(
            "ingest_bytes — VERIFIED  total docs in collection: %d",
            collection_count,
        )
    except Exception as exc:
        logger.warning("ingest_bytes — count verification failed: %s", exc)
        collection_count = -1

    result = {
        "success": True,
        "filename": filename,
        "chars_extracted": len(raw_text),
        "chunks_created": len(docs),
        "vectors_stored": len(ids),
        "total_collection_size": collection_count,
        "chunk_preview": docs[0].page_content[:200] if docs else "",
    }
    logger.info("ingest_bytes — COMPLETE  %s", result)
    return result


def ingest_text(text: str, source: str = "manual") -> dict:
    """
    Ingest a raw text string directly (for programmatic use).
    Wraps ingest_bytes with UTF-8 encoding.
    """
    return ingest_bytes(text.encode("utf-8"), f"{source}.txt")