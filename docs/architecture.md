# Architecture

How the assistant is designed. For *why*, see [`decisions/`](decisions/README.md); for the DB shape, see
[`reference.md`](reference.md). This describes the **target** design — modules land task by task
([`tasks/README.md`](tasks/README.md)).

## The loop

The core is a **bounded agentic tool-calling loop** ([decision 0002](decisions/0002-agentic-tool-loop.md)),
not a fixed pipeline. The model receives two tools and iterates (hard cap on steps) until it produces a
natural-language answer:

```
                    ┌─────────────────────────────────────────────┐
  user question ──▶ │  agent loop  (max N tool-call iterations)    │ ──▶ answer (Spanish)
                    │                                              │
                    │   search_schema(question)                    │
                    │      └▶ RAG over Chroma: DDL + docs + Q→SQL   │
                    │   run_sql(query)                             │
                    │      └▶ sqlglot validate → enforce LIMIT      │
                    │         → execute read-only → rows | error    │
                    └─────────────────────────────────────────────┘
```

Typical trace: `search_schema` (find the tables) → draft SQL → `run_sql` → on error/empty, read the DB
message and **refine** → `run_sql` again → format the rows into an answer. Self-correction is native to the
loop; there is no separate repair stage.

## Modules

Grouped into layered sub-packages by concern ([decision 0007](decisions/0007-layered-package-structure.md)).

| Module | Responsibility | Purity |
|---|---|---|
| `app/config.py` | Frozen dataclass settings, env-driven, no DB/network on import | pure |
| `app/safety/validator.py` | `sqlglot` read-only validation (single SELECT, no DML/DDL, dialect=mysql) | **pure** |
| `app/safety/limits.py` | Enforce/clamp `LIMIT` by rewriting the AST | **pure** |
| `app/safety/execution.py` | Hardened `run_sql` (validate → LIMIT → read-only exec) + model-facing `format_result` | impure (lazy I/O) |
| `app/rag/schema.py` | Schema model + annotated DDL / join-annotation / summary rendering | **pure** |
| `app/rag/introspect.py` | Read `information_schema` → `SchemaInfo` (live DB) | impure (lazy I/O) |
| `app/rag/corpus.py` | Build the RAG corpus (DDL + docs + Q→SQL examples) from `SchemaInfo` | **pure** |
| `app/rag/retrieval.py` | 4-tier candidate merge + table/join/keyword extraction | **pure** |
| `app/rag/embeddings.py` | Offline hashing embedder (mock/CI) + lazy real embedder | mixed |
| `app/rag/engine.py` | ChromaDB client, seed sync, `search_schema` | impure (lazy I/O) |
| `app/llm/client.py` | OpenAI-compatible client + **mock provider (default)**, per-call cost | impure (lazy) |
| `app/llm/prompts.py` | System prompt + `search_schema`/`run_sql` tool schemas | **pure** |
| `app/agent.py` | The bounded tool-loop: dispatch tool calls, cap iterations, stream events | orchestration |
| `app/api.py` | FastAPI SSE `/chat` + `/health` | impure |

**Pure/impure separation** ([decision 0001](decisions/0001-tech-stack.md)): everything security- or
decision-critical (`safety/validator`, `safety/limits`, `rag/retrieval`, the mock provider) is
stdlib/`sqlglot`-only and unit-tested with no DB, vector store, or model. Heavy deps (Chroma, the MySQL
driver, the OpenAI client) are imported lazily inside the functions that need them, so CI stays fast and
the pure logic is trivially testable.

## RAG (the `search_schema` tool)

Retrieval is **real** (embeddings + vector search), exposed to the model as a tool. Corpus (task 0005),
each item content-hashed to a deterministic ID for idempotent re-seeding:

- **DDL** — annotated `CREATE TABLE` per table, with `-- joins: <table>` comments encoding FK edges.
- **docs** — business-rule notes (soft-delete filter, denormalized `shipment` columns, money units).
- **question_sql** — curated NL→SQL few-shot pairs (the question is embedded; SQL rides in metadata).

`search_schema` (task 0006) embeds the question once and merges candidates by priority: **P1** semantic
(nearest DDL) · **P2** example-driven (tables parsed out of retrieved example SQL) · **P3** relationship-
following (pull tables named in the chosen tables' `-- joins:` annotations) · **P4** keyword (stopword-
filtered substring match). Highest-priority source wins ties. It returns full DDL for the top tables plus
one-line summaries for the rest — the model sees what exists without paying full token cost.

Single source of truth: DDL + annotations are **derived from schema introspection** (task 0003), not
hand-duplicated — improving on the reference designs, where the RAG DDL and the migration DDL drift by hand.

## SQL safety (the `run_sql` tool)

Four independent layers ([decision 0003](decisions/0003-sql-safety-defense-in-depth.md)): a MySQL
`SELECT`-only user · `sqlglot` AST validation (run at tool + execute layers) · code-enforced `LIMIT` ·
read-only session + statement timeout + row cap + fresh connection per query. `run_sql` returns either
capped rows or the DB error message — the error is fed back into the loop so the model can self-correct.

## LLM & mock

The `openai` SDK points at any OpenAI-compatible endpoint ([decision 0001](decisions/0001-tech-stack.md)).
The **mock provider is the default**: it scripts deterministic tool calls (`search_schema` → `run_sql`) and
canned answers for the demo questions, so the *full loop* — retrieval, validation, execution, formatting —
runs against the *real* synthetic DB with **no API key**. A test asserts every mock SQL passes the real
validator, keeping mock and safety in lockstep.

## Request flow (task 0009)

`POST /chat` → agent loop → streamed tokens/steps back to the thin static chat page. Admin/debug mode can
surface the intermediate tool calls and SQL; end users see only the answer.
