"""
API routes — includes upload endpoint with full ingestion pipeline
and RAG debug endpoints for diagnosing retrieval failures.
"""

import io
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.api.schemas import QueryRequest, QueryResponse
from app.services.agent_service import run_agent_pipeline
from app.tools.web_search import web_search
from app.rag.ingest import ingest_bytes
from app.rag.retriever import retrieve_docs_with_metadata
from app.rag.vectorstore import get_vectorstore_stats
from app.exceptions.custom_exceptions import AgentException
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest) -> QueryResponse:
    logger.info("POST /ask — query: %r", request.query)
    try:
        result = await run_agent_pipeline(request.query)
        logger.info("POST /ask — OK  tools=%s", result.tools_used)
        return result
    except AgentException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        logger.error("POST /ask — unexpected: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Pipeline failed.") from exc


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    """
    Upload and ingest a document into the RAG vector store.

    Accepts: PDF, TXT, MD, DOCX
    Returns: Full ingestion statistics including chunk count and vector count.
    """
    filename = file.filename or "upload"
    logger.info("POST /upload — filename=%r  content_type=%s", filename, file.content_type)

    # Validate file type
    allowed_extensions = {"pdf", "txt", "md", "docx"}
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {allowed_extensions}",
        )

    try:
        file_bytes = await file.read()
        logger.info("POST /upload — read %d bytes", len(file_bytes))
    except Exception as exc:
        logger.error("POST /upload — file read failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to read uploaded file.") from exc

    result = ingest_bytes(file_bytes, filename)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return {
        "status": "ok",
        "message": f"Successfully ingested {filename}",
        **result,
    }


@router.get("/debug/rag/stats")
async def rag_stats() -> dict:
    """RAG debug: vector store statistics."""
    logger.info("GET /debug/rag/stats")
    return get_vectorstore_stats()


@router.get("/debug/rag/retrieve")
async def rag_retrieve(q: str, k: int = 4) -> dict:
    """
    RAG debug: run a retrieval query and return chunks with similarity scores.
    Use this to diagnose why a specific query isn't finding documents.
    """
    logger.info("GET /debug/rag/retrieve — q=%r  k=%d", q, k)
    try:
        results = retrieve_docs_with_metadata(q, k=k)
        return {
            "query": q,
            "k": k,
            "count": len(results),
            "results": results,
        }
    except Exception as exc:
        logger.error("GET /debug/rag/retrieve — %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/debug/websearch")
async def debug_websearch(q: str = "latest AI news") -> dict:
    logger.info("GET /debug/websearch — q=%r", q)
    try:
        snippets = web_search(q)
        return {"query": q, "count": len(snippets), "results": snippets}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Web search failed.") from exc