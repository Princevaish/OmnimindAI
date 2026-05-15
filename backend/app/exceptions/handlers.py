"""
FastAPI exception handlers.

Register these in app/main.py:
    from app.exceptions.handlers import app_exception_handler, generic_exception_handler
    from app.exceptions.custom_exceptions import AppException

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception,    generic_exception_handler)

Response shape (both handlers):
    {
        "error":   "<human-readable message>",
        "type":    "<ExceptionClassName>",
        "details": { … }          # present only for AppException subclasses
    }
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions.custom_exceptions import AppException
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle all AppException subclasses (ToolException, AgentException, …).

    HTTP status: 400 Bad Request — the pipeline failed due to a known,
    describable condition (bad input, tool failure, agent error).

    Args:
        request: The incoming FastAPI Request (used for path logging).
        exc:     The AppException instance raised by business logic.

    Returns:
        JSONResponse with status 400 and structured error body.
    """
    logger.warning(
        "AppException on %s %s — %s: %s | details=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
        exc.message,
        exc.details,
    )
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "type": type(exc).__name__,
            "details": exc.details,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for any unhandled Exception.

    HTTP status: 500 Internal Server Error.

    Logs a full traceback via exc_info=True so the stack trace is
    visible in uvicorn / application logs without leaking it to the client.

    Args:
        request: The incoming FastAPI Request.
        exc:     Any unhandled exception.

    Returns:
        JSONResponse with status 500 and a generic error body.
    """
    logger.error(
        "Unhandled exception on %s %s — %s: %s",
        request.method,
        request.url.path,
        type(exc).__name__,
        str(exc),
        exc_info=True,                      # writes full traceback to log
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected internal error occurred.",
            "type": type(exc).__name__,
        },
    )