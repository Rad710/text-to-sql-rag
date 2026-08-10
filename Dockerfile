# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (cached layer) from the lockfile-ish project metadata.
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY app ./app

EXPOSE 8000
# Mock LLM mode by default — the image runs with no API key.
ENV LLM_MODE=mock
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
