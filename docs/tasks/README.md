# Tasks — backlog

**One task in progress at a time.** Work the lowest-numbered `in-progress` task to its "Done when"
checklist, mark it `done`, then pick the next. The numbered list is the agreed build order.

### Structure (strict — every task follows it)

- **Folder per task:** `NNNN-slug/` (zero-padded, sequential, numbers never reused). Copy
  [`_template/`](_template/) to start one.
  - `README.md` — the spec. Required sections: **Goal**, **Context** (unless trivial), **Plan**,
    **Done when**. Frontmatter `status` is the source of truth.
  - `discussion.md` — append-only, dated log of decisions / options / dead ends.
  - `research.md` — findings + evidence. **Optional** — only when the task needed real digging.
- **Status:** `proposed → in-progress → done` (also `blocked`, `deferred`, `superseded`). Keep the row in
  the table in sync with the folder's `status`.
- **Definition of done** = the "Done when" checklist. A task is done ONLY when every box passes.
- **One task `in-progress` at a time**; commit per task on its own branch (see
  [`../ai-workflow.md`](../ai-workflow.md)).

## Scheduled (build order)

| # | Task | Status | Depends on |
|---|------|--------|-----------|
| [0001](0001-project-scaffold/) | Project scaffold + tooling — FastAPI skeleton, config, ruff/mypy/pytest, CI, docker-compose base, mock-default run | done | — |
| [0002](0002-synthetic-mysql-db/) | Synthetic DYR Transportes MySQL DB — init-SQL schema + obviously-fake seed + read-only user | done | 0001 |
| [0003](0003-schema-introspection/) | Schema introspection → single-source annotated DDL (tables, columns, join annotations) | done | 0002 |
| [0004](0004-sql-safety-layer/) | SQL safety layer — `sqlglot` validator + enforced `LIMIT` (pure + tested) | done | 0001 |
| [0005](0005-rag-corpus-seeding/) | RAG corpus (DDL + business-rule docs + Q→SQL examples) + idempotent content-hashed ChromaDB seeding | done | 0003 |
| [0006](0006-retrieval-engine/) | Retrieval engine — 4-tier merge + relationship-following (pure + tested); backs `search_schema` | done | 0005 |
| [0007](0007-llm-client/) | LLM client — OpenAI-compatible + mock provider (default) + prompts + tool schemas + per-call token/cost accounting | done | 0001 |
| [0008](0008-agentic-loop/) | Agentic orchestration — bounded tool-loop (`search_schema` + `run_sql`) + hardened execution + **execution-guided self-correction** (feed DB errors/empty results back for a repair pass), tested | done | 0004, 0006, 0007 |
| [0009](0009-streaming-api/) | Agent **event-streaming** + **FastAPI SSE API** (backend we own) — refactor the loop to emit events (tool start → SQL → rows → answer → usage) + a `/chat` SSE endpoint + `/health` | done | 0008 |
| [0010](0010-react-frontend/) | **Vite + React + TypeScript frontend** (assistant-ui) — styled `Thread` + **tool-call step rendering** + structured result table (decisions 0005/0006), regression tests + CI, browser-verified. Chainlit-parity scope now decided → decomposed into 0016/0018/0019/0020 | done | 0009 |
| 0011 | **Stretch:** standalone read-only SQL MCP server (schema-search + `run_sql` tools) over the synthetic DB | proposed | 0004, 0006 |
| [0012](0012-eval-harness/) | **Evaluation harness** — a golden `(question → gold SQL)` set + an execution-accuracy runner (compare result sets, not string match) wired into CI; plus `docs/failure-modes.md` | done | 0008 |
| 0013 | Dev-experience polish — `.pre-commit-config.yaml` (ruff + ruff-format + mypy) + coverage reporting (`pytest-cov`) in CI | proposed | 0001 |
| [0015](0015-real-llm-config/) | **Real-LLM config** — point the OpenAI-compatible client at a local **Ollama/vLLM** endpoint (base URL / model / optional key) via env; mock stays the default; verify + document | done | 0007, 0009 |
| [0016](0016-multi-turn/) | **Multi-turn conversation** — thread conversation history through `/chat` + the agent loop + the frontend adapter (follow-ups get context) | done | 0009, 0010 |
| [0017](0017-app-persistence-foundation/) | **App persistence foundation** — a separate **Postgres** service + SQLAlchemy (async) + Alembic; schema for `users` / `conversations` / `messages` / `feedback` ([decision 0008](../decisions/0008-app-datastore-postgres.md)) | done | 0001 |
| [0018](0018-auth-jwt/) | **Auth (JWT)** — register/login, bcrypt password hashing, signed JWT, protected `/chat`, React login UI ([decision 0009](../decisions/0009-auth-jwt.md)) | done | 0017, 0010 |
| [0019](0019-conversation-history/) | **Conversation history + thread-list UI** — persist conversations/messages and reload them (backed by 0017; the UI thread list) | done | 0016, 0017 |
| [0020](0020-feedback/) | **Feedback 👍/👎 (persisted)** — thumbs on answers saved to the `feedback` table (feeds the few-shot-curation idea) | done | 0017, 0010 |
| 0021 | **Result charts** — render a bar/line (**Recharts**) when the query result shape fits | proposed | 0010 |
| 0022 | **Rate limiting + deploy modes** — per-IP limit on `/chat` + config for the two deploy flavors (mock-only · real-LLM-with-limits) | proposed | 0009, 0015 |
| 0014 | **Deploy live** (the showcase must be clickable) — full docker-compose (API + built frontend + MySQL + Postgres), a hosted URL, README + `ai-workflow.md` finalization. **Sequenced last**, after 0015–0022 | proposed | 0010, 0018, 0022 |

## Backlog — open, unscheduled

- Query result → optional chart (the UI renders a simple bar/line when the shape fits)
- Few-shot example curation from a feedback table (thumbs up/down persisted, promoted to the corpus)
- Enrich the schema corpus with column descriptions + sample values (stronger schema-linking)
- Postgres dialect variant (prove the safety layer is dialect-parameterised)
- Second, larger/messier schema to demonstrate schema-linking at scale

## Done

- [0001](0001-project-scaffold/) — FastAPI skeleton + config + ruff/mypy/pytest + CI + Docker; runs in mock
  mode with no key. Gates green locally (8 tests), live-smoke-tested.
- [0002](0002-synthetic-mysql-db/) — synthetic MySQL DB via init SQL (7 business tables + fake seed +
  `SELECT`-only user); `docker compose up` auto-applies it. Read-only guarantee proven by 6 integration
  tests + a CI integration job.
- [0003](0003-schema-introspection/) — `information_schema` introspection → pure annotated-DDL renderer
  (`app/schema.py` + `app/introspect.py`) with bidirectional FK `-- joins:` annotations + compact
  summaries. The single source of truth for the RAG layer. 5 unit + 3 integration tests.
- [0004](0004-sql-safety-layer/) — `app/validator.py` (sqlglot AST read-only validation) + `app/limits.py`
  (code-enforced LIMIT). Pure, 31 new unit tests. The guardrails for the `run_sql` tool.
- [0005](0005-rag-corpus-seeding/) — RAG corpus (`app/corpus.py`) + offline embedder (`app/embeddings.py`)
  + ChromaDB store (`app/engine.py`) with idempotent content-hashed seeding. Runs offline (precomputed
  embeddings, no model download). 13 unit + 1 live-pipeline integration test.
- [0006](0006-retrieval-engine/) — 4-tier retrieval merge (`app/retrieval.py`: semantic/example/
  relationship/keyword) + `RagStore.search_schema()` assembling the two-tier context (full DDL + summaries
  + docs + few-shots). The RAG payoff. 9 unit + 1 integration test.
- [0007](0007-llm-client/) — provider-agnostic LLM client (`app/llm.py`): deterministic `MockProvider`
  (default, drives the loop from history) + `OpenAIProvider` (lazy) + `app/prompts.py` (system prompt +
  tool schemas) + per-call token/cost accounting. 10 unit tests.
- [0008](0008-agentic-loop/) — the bounded agentic loop (`app/agent.py`) + hardened `run_sql` execution
  (`app/execution.py`: validator + LIMIT + read-only user + timeout + row cap) + native self-correction.
  End-to-end works: NL question → search_schema → run_sql → answer. 5 unit + 6 integration tests.
- [0009](0009-streaming-api/) — agent refactored to **stream events** (`stream_answer`; `answer_question`
  folds them) + a **FastAPI SSE `/chat`** API (`app/api.py`) + `/health`. Streams tool steps + generated
  SQL + answer + token/cost live. The backend we own for the custom UI. 4 unit + 1 integration test.
- [0010](0010-react-frontend/) — **Vite + React 19 + TS** frontend with assistant-ui's styled `Thread`
  (shadcn/Tailwind): SSE events → native **tool-call steps** + a **result table** from structured rows
  (decisions 0005/0006), bilingual, prose answers, token/cost. Toolchain: Vite 8 / TS 7 / Biome. Regression
  suite (vitest/jsdom) + frontend CI job; browser-verified. Chainlit-parity split into 0016/0018/0019/0020.
- [0015](0015-real-llm-config/) — **real-LLM config** verified + documented: the OpenAI-compatible client
  targets a local **Ollama/vLLM** via `LLM_MODE=openai` + `LLM_BASE_URL`/`LLM_MODEL` (wiring pre-existed
  from 0007); mock stays default. Unit test for the base_url/model wiring + README section.
- [0016](0016-multi-turn/) — **multi-turn**: `/chat` carries `history` (a `Turn` list), threaded through the
  agent loop (`[system, *history, question]`); mock keys off the latest turn; the frontend sends prior turns
  (footer stripped). Browser-verified (turn 2's POST carries clean context). 104 backend tests.
- [0017](0017-app-persistence-foundation/) — **app persistence foundation**: a separate **Postgres 17**
  service + async **SQLAlchemy 2.0** (`app/store/`: `User`/`Conversation`/`Message`/`Feedback` + lazy async
  engine) + **Alembic** (initial migration). Pure metadata tests + an opt-in live round-trip; CI runs a
  Postgres service + `alembic upgrade head`. The writable store for auth/history/feedback (0018–0020).
- [0018](0018-auth-jwt/) — **auth (JWT)**: `app/auth/` (bcrypt + PyJWT), `/auth/register|login|me`, a
  protected `/chat`, and a React login/register screen with logout; the Bearer token flows from the SPA to
  `/chat`. Unit + integration (register→login→me) + browser-verified. Builds on the store (0017).
- [0019](0019-conversation-history/) — **conversation history**: `/chat` persists each turn under the
  user's conversation (a `ConversationRecorder` seam); `GET /conversations[/{id}]` (owner-scoped); a React
  sidebar lists/opens/creates conversations and reloads a thread's messages into a re-seeded runtime.
  Integration + browser-verified.
- [0020](0020-feedback/) — **feedback 👍/👎**: `POST /feedback` (owner-checked upsert, one per message);
  `/chat` emits the assistant message id + `GET /conversations/{id}` carries ids; thumbs in the action bar
  (idiomatic assistant-ui `FeedbackAdapter`) POST it. Integration + browser-verified (row in Postgres).
- [0012](0012-eval-harness/) — **evaluation harness** (`evaluation/`): 8 gold cases + an execution-accuracy
  runner (result-set compare, not string match) → **8/8 = 100%** mock accuracy, wired into CI; plus
  `docs/failure-modes.md`. The headline "how well / where it breaks" artifact. 2 unit + 1 integration test.
