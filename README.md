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

```bash
# run with the built-in mock LLM — no API key, no model server required
uv run uvicorn app.api:app --reload
# frontend: cd frontend && pnpm install && pnpm dev
```

### Using a real model (Ollama / vLLM)

The LLM client is **OpenAI-compatible**, so it can target any local model server. Point it there via env
(the deterministic mock stays the default when `LLM_MODE` is unset):

```bash
# Ollama:  `ollama serve` + `ollama pull llama3.1`
LLM_MODE=openai LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=llama3.1 LLM_API_KEY=ollama \
  uv run uvicorn app.api:app --reload

# vLLM (OpenAI-compatible server, default port 8000):
LLM_MODE=openai LLM_BASE_URL=http://localhost:8000/v1 LLM_MODEL=<served-model> \
  uv run uvicorn app.api:app --reload
```

`LLM_API_KEY` is optional for Ollama (any placeholder works); set it if your server requires one.

## Deploy modes

The app ships in two flavors via `DEPLOY_MODE` ([decision 0010](docs/decisions/0010-rate-limiting-deploy-modes.md)),
which sets sane **per-user** `/chat` rate-limit defaults; the mock LLM stays the default in both.

| Mode | LLM | `/chat` per-user limit | Use |
|------|-----|------------------------|-----|
| `demo` (default) | mock | 60/min, no daily cap | safe to leave open — deterministic, no cost |
| `live` | real (Ollama/vLLM) | 20/min **and** 100/day | real-LLM deploy; the daily cap bounds per-account cost |

```bash
# demo (default): nothing to set
uv run uvicorn app.api:app

# live: real LLM + stricter limits (set LLM_* per the section above)
DEPLOY_MODE=live LLM_MODE=openai LLM_BASE_URL=... LLM_MODEL=... \
  JWT_SECRET=<a-real-32B+-secret> uv run uvicorn app.api:app
```

The defaults are overridable: `RATE_LIMIT_PER_MIN` and `RATE_LIMIT_PER_DAY` (`0` = no daily cap). The
limiter is per-user and in-memory (per process; resets on restart). Over the limit, `/chat` returns
`429` with `Retry-After` and the SPA shows a friendly message. **Note:** auth endpoints are not
rate-limited (see decision 0010).

## SQL MCP server (stretch)

The schema-search + read-only `run_sql` capabilities are also exposed as a standalone **Model Context
Protocol** server, so any MCP client (Claude Desktop/Code, the MCP Inspector) can query the synthetic DB
directly — with the exact same SQL-safety guarantees (it reuses the validator + read-only execution, so
writes are rejected). Install the extra and run it:

```bash
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

```bash
# create a .env with secrets (template in DEPLOY.md), then:
docker compose -f docker-compose.prod.yml up -d --build
# → the app is served on http://localhost (nginx); API is internal-only
```

Full runbook — the `.env` template, TLS, and the demo↔live switch — is in [`DEPLOY.md`](DEPLOY.md).

## SQL safety

The assistant runs model-written SQL, so read-only is enforced in depth: a `SELECT`-only DB user,
`sqlglot` AST validation, a code-enforced `LIMIT`, and a hardened read-only connection (timeout + row cap).
See [`docs/decisions/0003-sql-safety-defense-in-depth.md`](docs/decisions/0003-sql-safety-defense-in-depth.md).

## Development

This repo is built with a disciplined, auditable AI-assisted workflow — numbered task folders, an
immutable decision log, and per-task commits. See [`docs/ai-workflow.md`](docs/ai-workflow.md) and start
at [`docs/README.md`](docs/README.md).

**Pre-commit hooks** run the same gates as CI (ruff, ruff-format, mypy + basic hygiene) before each
commit. Enable them once after `uv sync`:

```bash
uv run pre-commit install          # then hooks run automatically on git commit
uv run pre-commit run --all-files  # run them on demand across the repo
```

CI's quality job also reports test coverage (`pytest --cov`) and fails under an 80% floor.

## License

MIT — see [`LICENSE`](LICENSE) (added in task 0001).
