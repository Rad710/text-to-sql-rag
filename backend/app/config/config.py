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
from urllib.parse import quote

from dotenv import load_dotenv

# Best-effort: load a local .env if present. Reads a file only — no DB/network. Missing is fine.
load_dotenv(override=False)

LlmMode = Literal["mock", "openai"]
DeployMode = Literal["demo", "live"]

# Allowed CORS origins for the frontend dev/preview servers (Vite).
_DEFAULT_CORS = ("http://localhost:5173", "http://localhost:4173")


def _get(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None and raw.strip() else default


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None and raw.strip() else default


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application configuration, resolved from the environment."""

    # LLM — mock is the default so the app runs with no API key.
    llm_mode: LlmMode = "mock"
    llm_base_url: str = "http://localhost:8000/v1"
    llm_api_key: str = "not-needed"
    llm_model: str = "gpt-4o-mini"
    # USD per 1M tokens, for cost estimation (0.0 = unknown pricing → reported as $0).
    llm_price_input_per_1m: float = 0.0
    llm_price_output_per_1m: float = 0.0

    # Query database — read-only MySQL the assistant reads (decision 0004/0011).
    query_db_host: str = "localhost"
    query_db_port: int = 3306
    query_db_user: str = "llm_readonly"
    query_db_password: str = ""
    query_db_name: str = "dyrtransportes"

    # App datastore — Postgres (decision 0008); assembled into a DSN by `app_database_url`.
    app_db_host: str = "localhost"
    app_db_port: int = 5432
    app_db_user: str = "app"
    app_db_password: str = "app"
    app_db_name: str = "dyr_app"

    # Auth (decision 0009) — JWT signing. Secret MUST be overridden in any real deploy.
    jwt_secret: str = "dev-insecure-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    jwt_expiry_min: int = 60 * 24  # 1 day

    # Deploy flavor (decision 0010). "demo" = mock LLM, generous limits, no daily cap; "live" = real
    # LLM, stricter per-minute rate + a per-user daily cap (cost control). Sets *defaults* only —
    # the two knobs below still win when set explicitly in the environment.
    deploy_mode: DeployMode = "demo"
    # Per-user rate limit on /chat (keyed by JWT subject). per_day == 0 disables the daily cap.
    rate_limit_per_min: int = 60
    rate_limit_per_day: int = 0  # 0 = no daily ceiling (demo default)

    # Safety / agent limits.
    result_limit: int = 500
    agent_max_iterations: int = 6
    statement_timeout_ms: int = 5000  # kills runaway queries (MySQL max_execution_time)

    # RAG vector store location (persisted via a docker volume in compose).
    chroma_path: str = ".chroma"

    # Web API — allowed CORS origins for the Vite frontend (task 0009/0010).
    cors_origins: tuple[str, ...] = _DEFAULT_CORS

    @property
    def is_mock(self) -> bool:
        return self.llm_mode == "mock"

    @property
    def app_database_url(self) -> str:
        pw = quote(self.app_db_password, safe="")
        return (
            f"postgresql+asyncpg://{self.app_db_user}:{pw}"
            f"@{self.app_db_host}:{self.app_db_port}/{self.app_db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, resolved once from the environment and cached."""
    mode_raw = _get("LLM_MODE", "mock").lower()
    llm_mode: LlmMode = "openai" if mode_raw == "openai" else "mock"
    # Deploy flavor drives the rate-limit *defaults*; explicit env knobs still override below.
    deploy_mode: DeployMode = "live" if _get("DEPLOY_MODE", "demo").lower() == "live" else "demo"
    default_per_min, default_per_day = (20, 100) if deploy_mode == "live" else (60, 0)
    return Settings(
        llm_mode=llm_mode,
        deploy_mode=deploy_mode,
        rate_limit_per_min=_get_int("RATE_LIMIT_PER_MIN", default_per_min),
        rate_limit_per_day=_get_int("RATE_LIMIT_PER_DAY", default_per_day),
        llm_base_url=_get("LLM_BASE_URL", "http://localhost:8000/v1"),
        llm_api_key=_get("LLM_API_KEY", "not-needed"),
        llm_model=_get("LLM_MODEL", "gpt-4o-mini"),
        llm_price_input_per_1m=_get_float("LLM_PRICE_INPUT_PER_1M", 0.0),
        llm_price_output_per_1m=_get_float("LLM_PRICE_OUTPUT_PER_1M", 0.0),
        query_db_host=_get("QUERY_DB_HOST", "localhost"),
        query_db_port=_get_int("QUERY_DB_PORT", 3306),
        query_db_user=_get("QUERY_DB_USER", "llm_readonly"),
        query_db_password=_get("QUERY_DB_PASSWORD", ""),
        query_db_name=_get("QUERY_DB_NAME", "dyrtransportes"),
        app_db_host=_get("APP_DB_HOST", "localhost"),
        app_db_port=_get_int("APP_DB_PORT", 5432),
        app_db_user=_get("APP_DB_USER", "app"),
        app_db_password=_get("APP_DB_PASSWORD", "app"),
        app_db_name=_get("APP_DB_NAME", "dyr_app"),
        # Dev default is ≥32 bytes (PyJWT warns below that for HS256); a real deploy overrides it.
        jwt_secret=_get("JWT_SECRET", "dev-insecure-secret-change-me-in-production-0123456789"),
        jwt_algorithm=_get("JWT_ALGORITHM", "HS256"),
        jwt_expiry_min=_get_int("JWT_EXPIRY_MIN", 60 * 24),
        result_limit=_get_int("RESULT_LIMIT", 500),
        agent_max_iterations=_get_int("AGENT_MAX_ITERATIONS", 6),
        statement_timeout_ms=_get_int("STATEMENT_TIMEOUT_MS", 5000),
        cors_origins=tuple(o.strip() for o in _get("CORS_ORIGINS", "").split(",") if o.strip())
        or _DEFAULT_CORS,
    )
