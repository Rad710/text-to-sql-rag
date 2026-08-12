# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Link the GHCR package to the repo (see .github/workflows/release.yml).
LABEL org.opencontainers.image.source="https://github.com/Rad710/text-to-sql-rag"

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
# Migrations run on boot (see docker-entrypoint.sh), so the app store schema is applied automatically.
COPY alembic ./alembic
COPY alembic.ini ./
# Build context is the repo root (see docker/docker-compose*.yml); this file now lives under docker/.
COPY docker/docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
# Mock LLM mode by default — the image runs with no API key.
ENV LLM_MODE=mock
# Apply migrations, then serve. Override the entrypoint if you need to run migrations separately.
ENTRYPOINT ["/app/docker-entrypoint.sh"]
