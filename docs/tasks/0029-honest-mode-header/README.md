---
status: in-progress
updated: 2026-08-12
depends_on: [0015]
decision: null
---

# 0029 — Header shows the real runtime mode (+ test hermeticity)

## Goal
The header's `text-to-SQL · RAG · mock mode` was a **hardcoded string** — it said "mock mode" even when
running against a real LLM. Make it reflect the actual mode. Also fix a test-hermeticity gap the live-LLM
work exposed: the suite read a developer's `.env` and broke when it was flipped to `LLM_MODE=openai`.

## Context
Found while testing live mode (Ollama). Two issues:
- The frontend can't know the backend's LLM mode without asking, so `/health` now surfaces it.
- `app/config.py` calls `load_dotenv(override=False)` at import, so a local `.env` with
  `LLM_MODE=openai` leaked into pytest and made `test_chat_streams_sse_events` hit the real Ollama
  instead of the mock (CI unaffected — no `.env` there).

## Plan
1. `app/api.py` — `/health` also returns `llm_mode`, `deploy_mode`, and `model` (the model name when
   openai, else `"mock"`).
2. `frontend/src/App.tsx` — fetch `/health` on mount; header shows `text-to-SQL · RAG · {label}` where
   label is `"mock mode"` (mock) or the model name (openai). `App.test.tsx` mocks `/health`.
3. `tests/conftest.py` — force `LLM_MODE=mock` before `app.config` imports, so the suite is hermetic
   regardless of a local `.env`.

## Done when
- [x] `/health` returns the mode; header shows the real model (browser-verified: "llama3.2:3b" in openai
      mode, "mock mode" in mock).
- [x] `tests/conftest.py` forces mock; full unit suite green (128) regardless of `.env`.
- [x] `pnpm lint`/`build`/`test` green (22); `ruff`/`mypy`/`pytest` green.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
