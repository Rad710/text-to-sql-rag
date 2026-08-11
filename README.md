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

## SQL safety

The assistant runs model-written SQL, so read-only is enforced in depth: a `SELECT`-only DB user,
`sqlglot` AST validation, a code-enforced `LIMIT`, and a hardened read-only connection (timeout + row cap).
See [`docs/decisions/0003-sql-safety-defense-in-depth.md`](docs/decisions/0003-sql-safety-defense-in-depth.md).

## Development

This repo is built with a disciplined, auditable AI-assisted workflow — numbered task folders, an
immutable decision log, and per-task commits. See [`docs/ai-workflow.md`](docs/ai-workflow.md) and start
at [`docs/README.md`](docs/README.md).

## License

MIT — see [`LICENSE`](LICENSE) (added in task 0001).
