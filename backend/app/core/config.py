"""
Application configuration using Pydantic BaseSettings.

Design decisions:
    - .env path is resolved to an absolute path at module load time using
      pathlib, eliminating all working-directory-dependent loading failures.
    - Settings() is never instantiated at module level — only inside the
      lru_cache-decorated get_settings() — so the .env file is read exactly
      once, on first call, after the Python path is fully initialised.
    - All other modules obtain settings via:
          from app.core.config import get_settings
          settings = get_settings()

Directory layout assumed:
    backend/
    ├── .env                  ← environment file
    └── app/
        └── core/
            └── config.py     ← this file

Path resolution:
    __file__                  → backend/app/core/config.py
    .parent                   → backend/app/core/
    .parent                   → backend/app/
    .parent                   → backend/              ← BASE_DIR
    BASE_DIR / ".env"         → backend/.env
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Absolute path to the .env file — never relative, never working-dir-dependent
# ---------------------------------------------------------------------------

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
ENV_FILE: Path = BASE_DIR / ".env"


# ---------------------------------------------------------------------------
# Settings schema
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Application settings populated from environment variables and the .env file.

    Field validation rules:
        - All three str fields are required (no default) so a missing key
          raises a clear ValidationError at startup rather than an AttributeError
          somewhere deep in the pipeline.
        - MODEL_NAME has a sensible default so the .env entry is optional.
    """

    GROQ_API_KEY: str
    MODEL_NAME: str = "llama3-70b-8192"
    TAVILY_API_KEY: str

    model_config = {                       # Pydantic v2 style
        "env_file": str(ENV_FILE),         # must be str, not Path
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",                 # silently skip unknown .env keys
    }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Instantiate, cache, and return the application Settings object.

    The @lru_cache(maxsize=1) decorator guarantees that Settings() is
    constructed exactly once per process lifetime, regardless of how many
    modules call get_settings().

    Debug lines print only the first 10 characters of each secret so the
    key is identifiable in logs without being fully exposed.

    Returns:
        Fully validated Settings instance.

    Raises:
        pydantic_settings.ValidationError: if a required field is missing
            from both the environment and the .env file.
        FileNotFoundError: never — pydantic-settings silently skips a missing
            .env file, so the ValidationError above surfaces first.
    """
    print(f"[config] loading .env from: {ENV_FILE}")
    print(f"[config] .env exists: {ENV_FILE.is_file()}")

    settings = Settings()

    # Partial key display — enough to confirm the correct key was loaded
    print(f"[config] GROQ_API_KEY  : {settings.GROQ_API_KEY[:10]}…")
    print(f"[config] TAVILY_API_KEY: {settings.TAVILY_API_KEY[:10]}…")
    print(f"[config] MODEL_NAME    : {settings.MODEL_NAME}")

    return settings