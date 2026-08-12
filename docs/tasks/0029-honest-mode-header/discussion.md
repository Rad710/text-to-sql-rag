# 0029 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-12: While testing live mode I noticed the header always said "mock mode" — a hardcoded string
  in App.tsx, independent of the real `LLM_MODE`. Fixed by surfacing the mode from `/health`
  (`llm_mode`, `deploy_mode`, `model`) and having the header fetch + display it. Browser-verified: in
  openai mode the header reads "text-to-SQL · RAG · llama3.2:3b"; in mock it reads "mock mode".
- 2026-08-12: Fixing the header surfaced a second issue — flipping `.env` to `LLM_MODE=openai` for the
  live run broke `test_chat_streams_sse_events` (it hit the real Ollama, so the deterministic "run_sql"
  assertion failed). Root cause: `config.py` `load_dotenv(override=False)` reads the dev's `.env` in
  pytest. CI never saw it (no `.env` committed). Added `tests/conftest.py` that sets
  `os.environ["LLM_MODE"]="mock"` before `app.config` is imported (conftest loads first; override=False
  respects the preset), so the suite is hermetic regardless of a local `.env`. Full unit suite green (128)
  with `.env` still on openai.
- 2026-08-12: Code-review feedback (owner): the header's /health fetch used a `.then/.catch` chain —
  refactored to `async/await` with `Promise.all` for the two independent mount fetches (auth + mode),
  extracted into `src/server.ts` (`fetchServerMode`). Also tidied adjacent promise chains for
  consistency: `refreshList` (await), the login `onAuthed` callback (await), and the runtime's 429-detail
  parse (try/await instead of `.then().catch()`). Gates green (22 frontend tests, lint/build; 128 backend).
