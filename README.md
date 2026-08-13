# text-to-sql-rag

A **text-to-SQL RAG assistant** over a freight/logistics database: ask a question in natural language and
get an answer, backed by retrieval-augmented schema grounding and safe, read-only SQL. Built as an
**agentic tool-loop** — the model searches the schema (RAG) and runs read-only queries, rerunning and
refining until it can answer.

> **Status: in active development.** The design and task tracker are complete; implementation is landing
> task by task. Follow along in [`docs/`](docs/).

## What it does

Natural-language question (e.g. *"¿cuánto facturamos por ruta el mes pasado?"*) → the assistant retrieves
the relevant tables via RAG, writes a read-only `SELECT`, runs it against a **synthetic** MySQL database,
and answers in plain language. The demo schema models **DYR Transportes**, a Paraguayan trucking business
(drivers, routes, shipments, client billing, and driver settlements). All data is synthetic — no real
business data or PII.

## Architecture

A bounded **agentic tool-calling loop** with two tools:

- `search_schema(question)` — RAG over DDL + business-rule docs + example queries (ChromaDB)
- `run_sql(query)` — `sqlglot`-validated, `LIMIT`-enforced, executed as a read-only DB user

The model calls `search_schema`, drafts SQL, calls `run_sql`, and self-corrects on errors before
answering. See [`docs/architecture.md`](docs/architecture.md).

**Stack:** Python 3.12 · FastAPI · ChromaDB · `sqlglot` · MySQL 8 (Alembic) · OpenAI-compatible LLM client.
Runs with **no API key** via a built-in mock provider.

## Quickstart

All configuration lives in a single **`.env`** (read by both the app and docker compose). Copy the
template and set the `change-me` secrets — the mock LLM needs no API key:

```bash
cp .env.example .env      # then edit the change-me* values (see the comments in the file)
```

**Run the whole app in Docker** — nginx + API + MySQL + Postgres behind one URL, migrations on boot.
Compose files live under [`docker/`](docker/); pass `--env-file .env` (Compose looks for `.env` next to
the compose file, not the repo root):

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build
# → http://localhost   (set WEB_PORT=8080 in .env if port 80 is taken)
```

### Local development (hot reload)

Databases in Docker; API + frontend as dev servers. Three steps (frontend in its own terminal):

```bash
# 1. databases — MySQL (Flyway seeds the mock schema) + Postgres.
#    Pass --env-file: Compose reads .env next to the compose file, not the repo root.
docker compose -f docker/docker-compose.yml --env-file .env up -d mysql postgres flyway

# 2. backend API — migrate the app store, then serve (mock LLM, hot reload). Runs from backend/.
cd backend && uv run alembic upgrade head && uv run uvicorn app.api:app --reload   # → :8000

# 3. frontend (new terminal)
cd frontend && pnpm install && pnpm dev                                            # → :5173
```

Open **http://localhost:5173** — `LLM_MODE=mock` needs no API key. `alembic upgrade head` is idempotent,
so re-running step 2 is safe; the migration is required because host-run `uvicorn` (unlike the Docker
image) does not apply it automatically.

> **Port already in use?** The DBs publish `3306` / `5432`. If one is taken, run that DB standalone on a
> free port and point `.env` at it — e.g. Postgres on `55432`:
> `docker run -d --name dyr-postgres -e POSTGRES_USER=app -e POSTGRES_PASSWORD=change-me-app -e POSTGRES_DB=dyr_app -p 55432:5432 postgres:17`,
> then set `APP_DB_PORT=55432` in `.env` (same idea with `QUERY_DB_PORT` for MySQL).

### Using a real model (Ollama / vLLM)

The LLM client is **OpenAI-compatible**, so it can target any local model server — just set these in
`.env` (the deterministic mock stays the default when `LLM_MODE=mock`):

```dotenv
LLM_MODE=openai
LLM_BASE_URL=http://localhost:11434/v1   # Ollama; vLLM is usually http://localhost:8000/v1
LLM_MODEL=llama3.1
LLM_API_KEY=ollama                       # any placeholder for Ollama; a real key for a cloud endpoint
```

then start the API as above. `LLM_API_KEY` is optional for Ollama; set it if your server requires one.

## Rate limits

`/chat` is rate-limited **per authenticated user** ([decision 0010](docs/decisions/0010-rate-limiting-deploy-modes.md),
[0012](docs/decisions/0012-drop-deploy-mode.md)) via two env knobs — a per-minute rate and an optional
per-day cap. The mock LLM stays the default.

| Var | Default | Meaning |
|-----|---------|---------|
| `RATE_LIMIT_PER_MIN` | `60` | max `/chat` calls per user per minute |
| `RATE_LIMIT_PER_DAY` | `0` | per-user daily cap (cost ceiling); `0` = no daily limit |

The defaults suit the mock demo (safe to leave open — deterministic, no cost). For a real-LLM deploy,
set stricter values to bound per-account cost and point `LLM_*` at a real model with a real `JWT_SECRET`:

```dotenv
# .env — real-LLM deploy
LLM_MODE=openai
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1
RATE_LIMIT_PER_MIN=20
RATE_LIMIT_PER_DAY=100
JWT_SECRET=<generate one: python -c "import secrets; print(secrets.token_urlsafe(48))">
```

The
limiter is per-user and in-memory (per process; resets on restart). Over the limit, `/chat` returns
`429` with `Retry-After` and the SPA shows a friendly message. **Note:** auth endpoints are not
rate-limited (see decision 0010).

## SQL MCP server (stretch)

The schema-search + read-only `run_sql` capabilities are also exposed as a standalone **Model Context
Protocol** server, so any MCP client (Claude Desktop/Code, the MCP Inspector) can query the synthetic DB
directly — with the exact same SQL-safety guarantees (it reuses the validator + read-only execution, so
writes are rejected). Install the extra and run it:

```bash
cd backend
uv sync --extra mcp
uv run python -m app.mcp_server          # stdio (for a local client)
uv run python -m app.mcp_server --http   # streamable HTTP on 127.0.0.1:8848/mcp
```

Register it with an MCP client (stdio) — e.g. a `mcpServers` entry:

```json
{
  "mcpServers": {
    "dyr-sql": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"],
      "cwd": "/absolute/path/to/text-to-sql-rag",
      "env": { "DB_HOST": "127.0.0.1", "DB_USER": "llm_readonly", "DB_NAME": "dyrtransportes" }
    }
  }
}
```

See [`docs/tasks/0011-sql-mcp-server/`](docs/tasks/0011-sql-mcp-server/).

## Deploy

<!-- Once hosted, put the clickable URL here:  **Live demo:** https://your-domain -->
_Live demo: not yet hosted — deploy it yourself in a few minutes with the runbook below._

A production `docker-compose` runs the whole stack behind **nginx** (serves the built SPA and proxies
the API — one origin, no CORS): FastAPI (mock mode + Alembic migrations on boot), the synthetic MySQL
query DB, and the Postgres app store.

The `app` + `web` images are built and pushed to **GHCR** by the release workflow
(`.github/workflows/release.yml`, on a `v*` tag); the deploy just pulls them:

```bash
cp .env.example .env   # set the change-me secrets (a real JWT_SECRET), then:
docker compose -f docker/docker-compose.prod.yml pull
docker compose -f docker/docker-compose.prod.yml up -d
# → the app is served on http://localhost (nginx); API is internal-only
```

(No published images yet? The compose file keeps a `build:` fallback — add `--build` to build from source.)
Full runbook — GHCR visibility/auth, the `.env` template, TLS, and the demo↔live switch — is in
[`DEPLOY.md`](DEPLOY.md).

## SQL safety

The assistant runs model-written SQL, so read-only is enforced in depth: a `SELECT`-only DB user,
`sqlglot` AST validation, a code-enforced `LIMIT`, and a hardened read-only connection (timeout + row cap).
See [`docs/decisions/0003-sql-safety-defense-in-depth.md`](docs/decisions/0003-sql-safety-defense-in-depth.md).

## Development

This repo is built with a disciplined, auditable AI-assisted workflow — numbered task folders, an
immutable decision log, and per-task commits. See [`docs/ai-workflow.md`](docs/ai-workflow.md) and start
at [`docs/README.md`](docs/README.md).

**Pre-commit hooks** run the same gates as CI (ruff, ruff-format, mypy + basic hygiene) before each
commit. Enable them once from the repo root (config: [`.pre-commit-config.yaml`](.pre-commit-config.yaml)):

```bash
uvx pre-commit install          # then hooks run automatically on git commit
uvx pre-commit run --all-files  # run them on demand across the repo
```

CI's quality job also reports test coverage (`pytest --cov`) and fails under an 80% floor.

**End-to-end tests** (Playwright, `frontend/e2e/`) drive a real browser through the whole journey —
register → ask → tool steps + result table + chart → feedback → multi-turn → re-login restores history —
against a live stack. CI runs them on every push (the `e2e` job boots MySQL + Postgres + the API in mock
mode). To run locally, start the stack (API on `:8000` + the databases), then:

```bash
cd frontend && pnpm exec playwright install chromium   # one-time
pnpm e2e                                                # starts Vite and runs the specs
```

## License

MIT — see [`LICENSE`](LICENSE) (added in task 0001).
