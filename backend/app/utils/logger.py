"""
Centralised logging configuration for the entire application.

Design decisions:
    - One StreamHandler attached to the root "app" logger — all child loggers
      (app.api, app.agents, app.tools, …) inherit it automatically.
    - Duplicate-handler guard: calling get_logger() N times for the same name
      never attaches N copies of the handler.
    - No FileHandler here — in production, stdout is captured by the process
      supervisor (uvicorn, Docker, systemd). Add a FileHandler or a third-party
      sink (structlog, loguru) at the call site if needed.
"""

import logging

# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------

_LOG_FORMAT: str = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Root application logger — configured once, inherited by all children
# ---------------------------------------------------------------------------

_root_logger = logging.getLogger("app")

if not _root_logger.handlers:                   # guard against double-attach
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    _root_logger.addHandler(_handler)
    _root_logger.setLevel(logging.INFO)
    _root_logger.propagate = False              # don't bubble up to root logger


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """
    Return a named child logger under the "app" hierarchy.

    Usage:
        logger = get_logger(__name__)
        logger.info("Starting pipeline for query: %s", query)

    Args:
        name: Typically __name__ of the calling module. Becomes
              "app.<module_path>" in log output.

    Returns:
        A logging.Logger instance that inherits the root app handler,
        formatter, and log level.
    """
    return logging.getLogger(name)