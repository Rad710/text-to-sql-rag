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
| [0011](0011-sql-mcp-server/) | **Stretch:** standalone read-only SQL MCP server (schema-search + `run_sql` tools) over the synthetic DB | done | 0004, 0006 |
| [0012](0012-eval-harness/) | **Evaluation harness** — a golden `(question → gold SQL)` set + an execution-accuracy runner (compare result sets, not string match) wired into CI; plus `docs/failure-modes.md` | done | 0008 |
| [0013](0013-devex-precommit-coverage/) | Dev-experience polish — `.pre-commit-config.yaml` (ruff + ruff-format + mypy) + coverage reporting (`pytest-cov`) in CI | done | 0001 |
| [0015](0015-real-llm-config/) | **Real-LLM config** — point the OpenAI-compatible client at a local **Ollama/vLLM** endpoint (base URL / model / optional key) via env; mock stays the default; verify + document | done | 0007, 0009 |
| [0016](0016-multi-turn/) | **Multi-turn conversation** — thread conversation history through `/chat` + the agent loop + the frontend adapter (follow-ups get context) | done | 0009, 0010 |
| [0017](0017-app-persistence-foundation/) | **App persistence foundation** — a separate **Postgres** service + SQLAlchemy (async) + Alembic; schema for `users` / `conversations` / `messages` / `feedback` ([decision 0008](../decisions/0008-app-datastore-postgres.md)) | done | 0001 |
| [0018](0018-auth-jwt/) | **Auth (JWT)** — register/login, bcrypt password hashing, signed JWT, protected `/chat`, React login UI ([decision 0009](../decisions/0009-auth-jwt.md)) | done | 0017, 0010 |
| [0019](0019-conversation-history/) | **Conversation history + thread-list UI** — persist conversations/messages and reload them (backed by 0017; the UI thread list) | done | 0016, 0017 |
| [0020](0020-feedback/) | **Feedback 👍/👎 (persisted)** — thumbs on answers saved to the `feedback` table (feeds the few-shot-curation idea) | done | 0017, 0010 |
| [0021](0021-result-charts/) | **Result charts** — render a bar/line (**Recharts**) when the query result shape fits | done | 0010 |
| [0022](0022-rate-limiting-deploy-modes/) | **Rate limiting + deploy modes** — per-**user** limit on `/chat` + `DEPLOY_MODE` config for the two flavors (demo · live) ([decision 0010](../decisions/0010-rate-limiting-deploy-modes.md)) | done | 0009, 0015 |
| [0014](0014-deploy-live/) | **Deploy live** (the showcase must be clickable) — production docker-compose (nginx SPA+proxy + API + MySQL + Postgres), `DEPLOY.md` runbook, README Deploy section. Artifacts built + locally verified; owner does the VM/DNS/TLS + hosted URL | done | 0010, 0018, 0022 |
| [0023](0023-e2e-test-hardening/) | **Thorough test pass + Playwright e2e + hardening** — full manual pass, register input-validation fix (422 + UI message), a browser e2e suite wired into CI | done | 0014 |
| [0024](0024-env-file-config/) | **Single `.env` as source of truth** — complete `.env.example`; README + DEPLOY use `.env` instead of inline env on the command line | done | 0014, 0022 |
| [0025](0025-multiturn-scroll-fix/) | **Fix runaway layout on the 2nd message** — pin the height cascade (`html/body/#root`) so the thread scrolls internally; + e2e regression guard | done | 0010, 0023 |
| [0026](0026-responsive-sidebar/) | **Responsive sidebar (mobile drawer)** — off-canvas hamburger drawer + backdrop on mobile, static column on desktop; + e2e geometry test | done | 0019, 0023 |
| [0027](0027-feedback-highlight/) | **Highlight selected 👍/👎** — style the `data-submitted` state so the chosen rating is filled/primary | done | 0020 |
| [0028](0028-polish-fixes/) | **Polish fixes** — remove double-persisting regenerate, graceful logout on mid-session 401, grouped/right-aligned number formatting in result tables | done | 0019, 0020 |
| [0029](0029-honest-mode-header/) | **Honest mode header** — `/health` surfaces the real LLM/deploy mode; header shows it (not hardcoded "mock"); `conftest` forces mock so tests ignore a local `.env` | done | 0015 |
| [0030](0030-frontend-restructure/) | **Frontend restructure** — conventional layered layout (`pages/ components/ hooks/ context/ api/ lib/ tests/`) + react-router (`/login` + guarded `/`) + `AuthProvider`; anonymous IIFE removed; 4-space formatting. Behavior unchanged | done | 0010 |
| [0031](0031-docker-folder/) | **Docker folder** — move all six Docker files (`Dockerfile`, both `docker-compose*.yml`, `docker-entrypoint.sh`, frontend image + `nginx.conf`) into `docker/`; repo-root build context; pinned project name; docs use `-f docker/…`. Behavior unchanged | done | 0014 |
| [0032](0032-ghcr-images/) | **GHCR images** — a `release.yml` workflow builds + pushes the `app`/`web` images to `ghcr.io/rad710/text-to-sql-rag/*` on a `v*` tag; prod compose pulls them (`image:` + `${IMAGE_TAG}`), keeping a `build:` fallback | done | 0014, 0031 |
| [0033](0033-config-package/) | **`app/config/` package** — group `config.py` + `ratelimit.py` into a sub-package with a re-exporting `__init__`; imports unchanged. First step of the repo reorg (plan 0033–0035) | done | — |
| [0034](0034-mock-db-flyway/) | **`mock-db/` + Flyway** — rename `db/` → `mock-db/`; replace the init-SQL + shell grant with Flyway versioned migrations (`V1/V2/V3`) run as a one-shot compose service + in CI ([decision 0011](../decisions/0011-flyway-mock-db-migrations.md), supersedes 0004) | done | — |
| [0035](0035-backend-consolidation/) | **`backend/` consolidation** — move all Python (`app`, `tests`, `evaluation`, `alembic`, `pyproject`, `uv.lock`) under `backend/` mirroring `frontend/`; rename `Dockerfile`→`backend.Dockerfile`; repoint CI/docker/docs. Behavior unchanged | done | 0033, 0034 |
| [0036](0036-run-sql-arg-alias/) | **`run_sql` arg alias** — accept `sql` as an alias for the `query` argument so local models (llama3.1) that misname it aren't rejected as "empty SQL"; frontend renders bare SQL either way | done | — |
| [0037](0037-chitchat-prompt/) | **Chit-chat prompt cleanup** — reword the non-DB system-prompt rule to a single general instruction (no enumerated greetings). Reduces but can't fully stop `llama3.1:8b` from narrating its reasoning — a model limit, not wording | done | — |

## Backlog — open, unscheduled

- Few-shot example curation from a feedback table (thumbs up/down persisted, promoted to the corpus)
- Enrich the schema corpus with column descriptions + sample values (stronger schema-linking)
- Postgres dialect variant (prove the safety layer is dialect-parameterised)
- Second, larger/messier schema to demonstrate schema-linking at scale

## Done

- [0037](0037-chitchat-prompt/) — **chit-chat prompt cleanup**: in live mode (`llama3.1:8b`) greetings got
  rambling nonsense that leaked the model's reasoning ("No schema or SQL call necessary…"). Reworded the
  non-DB rule to a single **general** instruction (owner's call — no enumerated greeting strings): use the
  tools only when the user asks for data, otherwise answer directly with no preamble. Honest outcome: the
  rule is right, but across four phrasings tested live the leak persisted non-deterministically on this 8B
  model — confirmed model-dependent by a quick search, not a wording fix. Kept the clean general prompt;
  the real fix for live chit-chat quality is a stronger model (mock stays the deterministic demo default).
  Same class of limit as `llama3.1:8b` garbling harder data questions (tool calls emitted as text).
- [0036](0036-run-sql-arg-alias/) — **`run_sql` arg alias**: live-mode testing with local `llama3.1:8b`
  showed ~half of data questions returning confidently-wrong answers — the model named the `run_sql`
  argument `sql` instead of the schema's `query`, so the backend read an empty string and the validator
  rejected `"empty SQL"`, after which the model hallucinated "no data". Now the agent accepts `query` **or**
  `sql` (`app/agent.py` `_sql_arg`), and the frontend renders bare SQL for either name (`lib/runtime.ts`).
  Safe — the sqlglot validator + read-only user still enforce read-only. New unit test; verified live: the
  previously-failing driver query now returns the correct table + answer, plus JOINs and general chit-chat
  all behave, 0 console errors.
- [0035](0035-backend-consolidation/) — **`backend/` consolidation**: moved all Python (`app/`, `tests/`,
  `evaluation/`, `alembic/` + `alembic.ini`, `pyproject.toml`, `uv.lock`, `.python-version`) under a new
  `backend/` dir mirroring `frontend/` (the full-stack-fastapi-template layout); package stays `app/` and
  pyproject internals are unchanged (they resolve from `backend/` as CWD). Renamed
  `docker/Dockerfile`→`docker/backend.Dockerfile` and prefixed its COPY paths with `backend/` (context is
  still the repo root); repointed both compose files. CI runs the Python steps with
  `working-directory: backend` (Flyway + frontend steps unchanged); `.dockerignore` switched to `**/`-globs;
  README/CLAUDE run `uv` from `backend/`; pre-commit driven via `uvx` from the root with the mypy hook using
  `uv run --directory backend`. Root is now `backend/ frontend/ docker/ mock-db/ docs/ .github/`. Verified:
  gates green from `backend/` (128 passed), backend image builds, compose configs resolve, CI YAML parses.
  Closes the repo reorg (0033–0035).
- [0034](0034-mock-db-flyway/) — **`mock-db/` + Flyway**: renamed `db/` → `mock-db/` (the folder only ever
  stood up a *mock* of the DYR schema — the real one lives in a separate prod project and the app
  introspects it live). Replaced the `db/init/*` first-boot scripts + `03_grant_readonly.sh` with **Flyway**
  versioned migrations `mock-db/migration/{V1__schema,V2__seed,V3__readonly_user}.sql` (grant password via a
  `${db_password}` placeholder). A one-shot `flyway/flyway:11` compose service migrates once MySQL is healthy
  (app waits on `service_completed_successfully`); CI runs the same migrations via `docker run`. Decision
  **0011** (supersedes 0004). Smoke-tested against a throwaway MySQL: V1–V3 apply, 7 tables + seed, and
  `llm_readonly` can SELECT but is denied DDL (ERROR 1142).
- [0033](0033-config-package/) — **`app/config/` package**: grouped the two loose cross-cutting modules
  (`app/config.py` settings + `app/ratelimit.py` limiter) into an `app/config/` sub-package
  (`config.py` + `ratelimit.py` + a re-exporting `__init__.py`) so `from app.config import …` keeps working
  for all 17 importers; only the 3 `app.ratelimit` sites changed. Moves via `git mv`. Gates green (128
  passed). First step of the repo reorg (plan: 0033 config → 0034 mock-db+Flyway → 0035 `backend/`).
- [0032](0032-ghcr-images/) — **GHCR images**: prod no longer builds on the VM. A new
  `.github/workflows/release.yml` (matrix over `app`/`web`) builds both images from the repo-root context
  and pushes them to `ghcr.io/rad710/text-to-sql-rag/{app,web}` on a `v*` tag (or manual dispatch), authed
  with the built-in `GITHUB_TOKEN` — tags = semver + `v*` ref + short SHA + `latest`.
  `docker/docker-compose.prod.yml` now pulls them (`image: …:${IMAGE_TAG:-latest}`) with a `build:`
  fallback kept for clone-and-run; both images carry an `org.opencontainers.image.source` label. DEPLOY.md
  + README describe the `pull → up -d` flow (+ GHCR visibility/login, `IMAGE_TAG` pin). Verified: workflow
  YAML valid, prod compose resolves to the GHCR refs. Owner does the first tag push + package-visibility.
- [0031](0031-docker-folder/) — **docker folder**: the repo root had six loose Docker files (backend
  `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`, `docker-entrypoint.sh`, plus
  `frontend/Dockerfile` + `frontend/nginx.conf`). Collected all of them under `docker/` (moves via
  `git mv`). Both images now build from the **repo-root context** (`context: ..`, `dockerfile: docker/…`)
  so the frontend build can reach `docker/nginx.conf`; `.dockerignore` consolidated to the root (the only
  place Docker reads it) and `frontend/.dockerignore` removed; `name: text-to-sql-rag` pinned in both
  compose files so container/volume names don't shift to `docker_*`. README/DEPLOY/CLAUDE commands updated
  to `-f docker/…` (run from the repo root). Verified: both compose files resolve + **both images build**;
  backend untouched. One follow-up left for the owner: a one-line `.env.example` edit (permission-blocked).
- [0030](0030-frontend-restructure/) — **frontend restructure**: reorganized the React app from a flat
  `src/` + one components folder + co-located tests + a 200-line `App.tsx` with an anonymous
  `void (async()=>{})()` IIFE into a **conventional layered layout** (`pages/ components/ hooks/ context/
  api/ lib/ tests/`). Added **react-router** (`/login` + a guarded `/` via `ProtectedRoute`) with auth in
  an `AuthProvider`/`useAuth` context; the IIFE is gone (named async effects + an `active` cleanup flag,
  header mode label split into `useServerMode()`); whole frontend reformatted to 4-space. Generated
  `ui/`+`assistant-ui/` primitives untouched; moves via `git mv` (history preserved). Behavior unchanged;
  backend untouched. build/lint clean, 22/22 unit tests, routing browser-verified (0 console errors).
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
- [0029](0029-honest-mode-header/) — **honest mode header**: the header hardcoded "mock mode" even under a
  real LLM. `/health` now returns `llm_mode`/`deploy_mode`/`model` and the header shows the real value
  (verified: "llama3.2:3b" in openai mode). Also added `tests/conftest.py` forcing `LLM_MODE=mock` so the
  suite is hermetic — a dev's `.env=openai` no longer makes unit tests hit the real Ollama.
- [0028](0028-polish-fixes/) — **polish fixes** (from the audit): (1) removed the regenerate button that
  re-POSTed `/chat` and wrote a **duplicate turn** to the store (verified: 1 turn → 4 messages); (2) a
  mid-session **401 now bounces to login** (an `onUnauthorized` seam clears the token) instead of leaving a
  raw "⚠️ 401" in the thread; (3) result tables **group + right-align numbers** (`8.000.000`) via the `es`
  locale (which leaves 4-digit years ungrouped). Browser-verified; 22 unit + e2e 3/3.
- [0027](0027-feedback-highlight/) — **feedback highlight**: clicking 👍/👎 gave no confirmation. The
  assistant-ui primitives already set `data-submitted` on the chosen button; added a style for it
  (`data-[submitted]:text-primary` + filled svg) so the selected thumb is filled/primary and clicking the
  other flips it. App.test asserts the highlight. Browser-verified.
- [0026](0026-responsive-sidebar/) — **responsive sidebar**: the fixed 240px sidebar crushed the chat on
  phones (bubbles wrapped one letter per line). Now a static column on desktop and an **off-canvas
  drawer** on mobile — a `md:hidden` hamburger slides it in over a dimmed backdrop, and it auto-closes on
  select. Layout/transition are pure CSS (Tailwind `md:` + `translate-x`); only the open toggle is React.
  Browser-verified at 390px + 1280px; e2e asserts the drawer geometry.
- [0025](0025-multiturn-scroll-fix/) — **multi-turn scroll fix**: a second message ran the layout away
  (blank space grew unbounded, scrollbar vanished, answer unreachable) — assistant-ui's scroll-to-bottom
  spacer fed back on an **unclamped** viewport because `html/body/#root` had no height, so the app's
  `h-full` cascade never resolved to the screen. Fixed with `html, body, #root { height: 100% }`;
  browser-verified the height stays ~1 viewport, and added an e2e assertion (bounded `scrollHeight`) that
  the presence-only test had missed.
- [0024](0024-env-file-config/) — **single `.env` source of truth**: completed the stale `.env.example`
  (all config vars + compose secrets, sectioned/commented) and rewrote README + DEPLOY so every command
  reads `.env` (`cp .env.example .env` + edit) instead of inline `VAR=… uv run …`. No code change
  (`config.py` already loads `.env`); verified both compose files resolve and the full host-run flow
  (alembic → API → register → /chat) works from `.env` alone.
- [0023](0023-e2e-test-hardening/) — **e2e + test hardening**: a thorough exploratory pass (API sweep +
  browser) confirmed the backend solid (auth, cross-user isolation → 404, feedback upsert, multi-turn,
  history reload); fixed the two gaps it found — register now rejects an invalid email + a <8-char
  password (`422`, surfaced in the UI: EmailStr + Field). A **Playwright** suite (`frontend/e2e/`) drives
  the full browser journey (register → ask → table/chart → feedback → multi-turn → re-login restores
  history) + the validation error, **wired into CI** (a new `e2e` job: MySQL + Postgres + mock API +
  chromium). vitest scoped to `src`; backend register-validation unit test.
- [0011](0011-sql-mcp-server/) — **SQL MCP server** (stretch): `app/mcp_server.py` exposes `search_schema`
  + `run_sql` as Model-Context-Protocol tools over the synthetic DB, reusing the safety + RAG layers
  verbatim (decision 0003 holds through the adapter). Both transports — stdio default + `--http`
  (streamable HTTP); `mcp` 2.0 as an opt-in `[mcp]` extra. Verified end-to-end with a real MCP client:
  lists both tools, returns rows, and rejects a `DELETE` as `ERROR:` text. 4 unit tests.
- [0014](0014-deploy-live/) — **deploy live**: production `docker-compose.prod.yml` — **nginx** serves the
  built SPA and reverse-proxies the API (one origin, SSE-safe), in front of FastAPI (mock mode + Alembic
  migrations on boot via `docker-entrypoint.sh`), MySQL, and Postgres. Multi-stage `frontend/Dockerfile`
  (+`nginx.conf`, `.dockerignore`), `DEPLOY.md` runbook, README Deploy section. Verified the full stack
  locally end-to-end through nginx (auth → question → chart → persisted feedback), 0 console errors; the
  owner does the VM/DNS/TLS + hosted URL.
- [0013](0013-devex-precommit-coverage/) — **dev-experience polish**: `.pre-commit-config.yaml`
  (ruff-check --fix + ruff-format pinned to our ruff, a local `uv run mypy` hook, basic hygiene hooks) so
  the CI gates run locally pre-commit; `pytest-cov` wired into the CI quality job with a `fail_under = 80`
  floor (unit coverage ~87%). README documents `pre-commit install`. Tooling only.
- [0022](0022-rate-limiting-deploy-modes/) — **rate limiting + deploy modes**: a pure in-memory
  `RateLimiter` (`app/ratelimit.py`, per-minute rate + optional per-day cap) enforced **per user** on
  `/chat` (429 + Retry-After); a `DEPLOY_MODE=demo|live` knob sets the defaults (demo 60/min; live 20/min
  + 100/day) with `RATE_LIMIT_PER_MIN`/`_PER_DAY` overrides; the SPA renders a friendly Spanish 429.
  Decision 0010. 7 limiter + 3 config + 1 api tests, 2 frontend 429 tests; browser-verified.
- [0021](0021-result-charts/) — **result charts**: a pure `analyzeResult` fit-heuristic (`frontend/src/lib/
  chart-data.ts`) + a `ResultView` with a **Tabla/Gráfico** toggle that `React.lazy`-loads a Recharts
  bar/line (`result-chart.tsx`, split to its own chunk). Bar for a categorical/composite axis (`origin ·
  destination`), line for a single temporal column; multi-series for extra numeric columns. 13 unit cases +
  App.test toggle assertion; browser-verified (bar + multi-series), 0 console errors.
- [0012](0012-eval-harness/) — **evaluation harness** (`evaluation/`): 8 gold cases + an execution-accuracy
  runner (result-set compare, not string match) → **8/8 = 100%** mock accuracy, wired into CI; plus
  `docs/failure-modes.md`. The headline "how well / where it breaks" artifact. 2 unit + 1 integration test.
