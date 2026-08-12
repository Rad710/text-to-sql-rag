#!/bin/sh
# Apply any pending app-store migrations, then start the API. `alembic upgrade head` is idempotent
# (a no-op when already at head), so running it on every boot is safe. Postgres must be reachable —
# in compose the app waits for the postgres healthcheck (depends_on: condition: service_healthy).
set -e

echo "==> alembic upgrade head"
uv run --no-dev alembic upgrade head

echo "==> starting uvicorn on 0.0.0.0:8000"
exec uv run --no-dev uvicorn app.api:app --host 0.0.0.0 --port 8000
