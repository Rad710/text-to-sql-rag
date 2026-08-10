"""Application settings.

A frozen, env-driven dataclass. Importing this module performs **no** database or network
I/O — it only reads environment variables (and, best-effort, a local ``.env``). The heavy
clients (DB driver, vector store, LLM) are constructed lazily by the modules that need them,
never here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv

# Best-effort: load a local .env if present. Reads a file only — no DB/network. Missing is fine.
load_dotenv(override=False)

LlmMode = Literal["mock", "openai"]


def _get(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None and raw.strip() else default


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application configuration, resolved from the environment."""

    # LLM — mock is the default so the app runs with no API key.
    llm_mode: LlmMode = "mock"
    llm_base_url: str = "http://localhost:8000/v1"
    llm_api_key: str = "not-needed"
    llm_model: str = "gpt-4o-mini"

    # Query-target database (synthetic DYR Transportes; wired in task 0002).
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "llm_readonly"
    db_password: str = ""
    db_name: str = "dyrtransportes"

    # Safety / agent limits (enforced in later tasks).
    result_limit: int = 500
    agent_max_iterations: int = 6

    # RAG store location (task 0005).
    chroma_path: str = ".chroma"

    @property
    def is_mock(self) -> bool:
        return self.llm_mode == "mock"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, resolved once from the environment and cached."""
    mode_raw = _get("LLM_MODE", "mock").lower()
    llm_mode: LlmMode = "openai" if mode_raw == "openai" else "mock"
    return Settings(
        llm_mode=llm_mode,
        llm_base_url=_get("LLM_BASE_URL", "http://localhost:8000/v1"),
        llm_api_key=_get("LLM_API_KEY", "not-needed"),
        llm_model=_get("LLM_MODEL", "gpt-4o-mini"),
        db_host=_get("DB_HOST", "localhost"),
        db_port=_get_int("DB_PORT", 3306),
        db_user=_get("DB_USER", "llm_readonly"),
        db_password=_get("DB_PASSWORD", ""),
        db_name=_get("DB_NAME", "dyrtransportes"),
        result_limit=_get_int("RESULT_LIMIT", 500),
        agent_max_iterations=_get_int("AGENT_MAX_ITERATIONS", 6),
        chroma_path=_get("CHROMA_PATH", ".chroma"),
    )
