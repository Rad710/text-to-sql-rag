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
| 0003 | Schema introspection → single-source annotated DDL (tables, columns, join annotations) | proposed | 0002 |
| 0004 | SQL safety layer — `sqlglot` validator + enforced `LIMIT` + connection hardening (pure + tested) | proposed | 0001 |
| 0005 | RAG corpus (DDL + business-rule docs + Q→SQL examples) + idempotent content-hashed ChromaDB seeding | proposed | 0003 |
| 0006 | Retrieval engine — 4-tier merge + relationship-following (pure + tested); backs `search_schema` | proposed | 0005 |
| 0007 | LLM client — OpenAI-compatible + mock provider (default) + prompts + tool schemas | proposed | 0001 |
| 0008 | Agentic orchestration — bounded tool-loop (`search_schema` + `run_sql`), intent + follow-up handling | proposed | 0004, 0006, 0007 |
| 0009 | FastAPI endpoints + thin static chat UI (streaming) | proposed | 0008 |
| 0010 | Full docker-compose + README + docs polish + `ai-workflow.md` finalization | proposed | 0009 |
| 0011 | **Stretch:** standalone read-only SQL MCP server (schema-search + `run_sql` tools) over the synthetic DB | proposed | 0004, 0006 |

## Backlog — open, unscheduled

- Query result → optional chart (the UI renders a simple bar/line when the shape fits)
- Few-shot example curation from a feedback table (thumbs up/down persisted, promoted to the corpus)
- Evaluation harness: a fixed set of NL→SQL questions with expected result shapes, run in CI against the
  synthetic DB (regression guard for prompt/retrieval changes)
- Postgres dialect variant (prove the safety layer is dialect-parameterised)

## Done

- [0001](0001-project-scaffold/) — FastAPI skeleton + config + ruff/mypy/pytest + CI + Docker; runs in mock
  mode with no key. Gates green locally (8 tests), live-smoke-tested.
- [0002](0002-synthetic-mysql-db/) — synthetic MySQL DB via init SQL (7 business tables + fake seed +
  `SELECT`-only user); `docker compose up` auto-applies it. Read-only guarantee proven by 6 integration
  tests + a CI integration job.
