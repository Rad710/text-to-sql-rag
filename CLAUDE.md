# CLAUDE.md

Guidance for Claude Code (and any contributor) working in this repository.

## Project overview

A **text-to-SQL RAG assistant** over the *DYR Transportes* freight/logistics schema (a Paraguayan
trucking business). A user asks a question in natural language ("¿cuánto facturamos por ruta el mes
pasado?"); the assistant retrieves the relevant schema via RAG, writes read-only SQL, runs it against
a synthetic MySQL database, and answers in plain language.

The demo database is **synthetic** — obviously-fake seed data modelled on the real DYR Transportes
schema. No real business data, PII, or credentials live in this repo.

## Architecture (target)

**Hybrid-agentic**, not a fixed pipeline. The model drives a bounded tool-calling loop:

```
question ─▶ agent loop (max N steps) ─▶ answer
              │
              ├─ tool: search_schema(question)  → RAG over DDL + docs + Q→SQL examples (Chroma)
              └─ tool: run_sql(query)           → validate (sqlglot) → enforce LIMIT → execute read-only
```

The model calls `search_schema` to pull the tables/DDL it needs, drafts SQL, calls `run_sql`, and — on
an error or empty/odd result — **reruns and refines** before answering. Self-correction is native to the
loop. See [`docs/architecture.md`](docs/architecture.md) for the full design and
[`docs/decisions/0002-agentic-tool-loop.md`](docs/decisions/0002-agentic-tool-loop.md) for why.

## Tech stack

- **Language:** Python 3.12
- **API:** FastAPI + Uvicorn; a thin static HTML/JS chat page served by the app (no build step)
- **LLM client:** `openai` SDK against any **OpenAI-compatible** endpoint (cloud or self-hosted). A
  deterministic **mock provider is the default** — the app runs with no API key.
- **Agent:** function/tool calling via the chat-completions tools API; bounded loop
- **RAG:** ChromaDB (embedded PersistentClient) over DDL, business-rule docs, and Q→SQL example pairs
- **SQL safety:** `sqlglot` (AST-level validation) + code-enforced `LIMIT` + a read-only DB user
- **Query DB:** MySQL 8 (synthetic DYR Transportes schema); migrations via Alembic
- **Tests:** pytest. **Lint/format:** ruff. **Types:** mypy. **CI:** GitHub Actions.
- **Packaging:** Docker + docker-compose (app + MySQL + mock LLM by default)

Pin dependency versions. Keep the security- and decision-critical logic (SQL validation, LIMIT
enforcement, retrieval merge, mock provider) **pure and stdlib/sqlglot-only** so it unit-tests without a
DB, vector store, or model; import heavy I/O (Chroma, the DB driver, the OpenAI client) lazily.

## How we work (strict)

Work is tracked as numbered, self-contained **task folders** under [`docs/tasks/`](docs/tasks/) — this is
the project's only context store (there is no `HANDOFF.md`). Start every session at
[`docs/README.md`](docs/README.md).

- **One task in progress at a time.** Work only the task marked `in-progress` in
  [`docs/tasks/README.md`](docs/tasks/README.md); finish it to its "Done when" checklist before the next.
  No "while I'm here" changes.
- **Each task is a folder** `NNNN-slug/`: `README.md` (spec: Goal · Context · Plan · Done when),
  `discussion.md` (append-only dated log), optional `research.md`. Copy
  [`docs/tasks/_template/`](docs/tasks/_template/) to start one.
- **Decisions are immutable.** Never rewrite an accepted record in
  [`docs/decisions/`](docs/decisions/) to reverse it — supersede it with a new numbered record that
  links both ways.
- **Reference facts have one home** — the schema and constants live in
  [`docs/reference.md`](docs/reference.md); link to it, never restate it.
- **Commit in batches, per task.** One feature/task per branch, small focused commits — never one giant
  "did everything" commit. The task folder + commit history are part of the deliverable (recruiters
  read them). See [`docs/ai-workflow.md`](docs/ai-workflow.md).

## Core principles

- **Simplicity first.** Make each change as small as it can be. Touch only what the task needs.
- **No laziness / no fake work.** Find root causes; no temporary hacks. If tests fail, say so with the
  output. Never claim done without proof.
- **Verify before "done".** Every "Done when" box must actually pass. Run the tests; show the result.
- **Ask before picking** when there are multiple real options with trade-offs — don't unilaterally build
  one and call it decided.

## SQL safety — non-negotiable

The assistant executes model-written SQL, so read-only is enforced in depth (see
[`docs/decisions/0003-sql-safety-defense-in-depth.md`](docs/decisions/0003-sql-safety-defense-in-depth.md)):

1. **DB-level read-only user** — the app connects as a MySQL user with `SELECT`-only grants. This is the
   real guarantee; everything else is belt-and-braces.
2. **`sqlglot` validation** — parse the statement; require a single `SELECT`/CTE; reject any DML/DDL,
   multiple statements, and dangerous functions. Run it at both the tool layer and the execute layer.
3. **Enforced `LIMIT`** — inject/clamp a `LIMIT` in code, not by prompting.
4. **Connection hardening** — read-only session, statement timeout, row cap, fresh connection per query.

Never weaken any of these to make a query work. If a legitimate query is blocked, fix the validator with
a test, don't remove the check.

## Coding conventions

- **Naming:** English for code. Domain terms from the freight business may stay Spanish where they don't
  translate cleanly (`shipment`, `driver_payroll`, `flete`). User-facing answer text: Spanish.
- **Style:** ruff (format + lint), 4-space indent. Type hints on public functions; mypy clean.
- **Structure:** pure/impure split (above). Config as a frozen dataclass, env-driven, no DB/network on
  import. One clear module per concern (`validator`, `retrieval`, `llm`, `agent`, `engine`, `mock`).
- **Errors:** raise typed exceptions; never leak raw SQL or stack traces to the end user.

## Build & dev commands

*(Filled in by task 0001 — the scaffold. Placeholder until then.)*

```bash
# run the app (mock LLM by default — no key needed)
uvicorn app.main:app --reload

# tests / lint / types
pytest
ruff check . && ruff format --check .
mypy app

# full stack (app + MySQL + migrations)
docker compose up
```

## Reference repos (do not copy secrets or business logic)

This project is a clean-room build. Two private repos informed the *design* only — never copy their
data, prompts, credentials, or client-specific logic here. Their patterns are re-implemented from
scratch against the public synthetic schema.
