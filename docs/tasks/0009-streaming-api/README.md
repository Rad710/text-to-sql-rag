---
status: done
updated: 2026-08-10
depends_on: [0008]
decision: 0005
---

# 0009 — Agent event-streaming + FastAPI SSE API

## Goal
The backend we own for the custom UI ([decision 0005](../../decisions/0005-custom-fastapi-sse-react-frontend.md)):
refactor the agent loop to **emit events** as it runs, and expose a **FastAPI `/chat` endpoint that streams
those events over SSE** — so the frontend (0010) can show the generated SQL, the tool steps, the answer,
and the token/cost live. Plus `/health`.

## Context
Builds on the agent ([0008](../0008-agentic-loop/)). Keep the existing sync `answer_question` (tests, eval
harness 0012 use it) and add a streaming generator beside it — same loop, yielding typed events instead of
returning one blob. assistant-ui (0010) consumes a structured stream; we emit a clean typed event protocol
(and can adopt `assistant-stream` for its transport if it simplifies the wire format).

## Plan
1. `app/agent.py` — add `stream_answer(question, llm, tools, max_iterations) -> Iterator[AgentEvent]`
   emitting: `tool_start`, `sql`, `tool_result`, `answer`, `usage`, `done` (dataclass events). Refactor the
   shared loop body so sync + streaming don't duplicate logic.
2. `app/api.py` — FastAPI app: `GET /health`; `POST /chat` returning an SSE stream (`text/event-stream`)
   of the agent events (via `sse-starlette` or `StreamingResponse`); a lazily-built, cached `(store, schema)`;
   CORS for the Vite dev server.
3. `pyproject.toml` — add `fastapi`, `uvicorn[standard]`, `sse-starlette` (+ `httpx` dev for the test client).
4. Tests: `test_agent_stream.py` (stub LLM → the event sequence, incl. self-correction) + `test_api.py`
   (`/health`; `/chat` streams SSE events end-to-end with an injected fake service; a live integration test).

## Done when
- [x] `stream_answer` yields the correct ordered events (tool_start → tool_result → answer → usage → done)
      for a happy path and a self-correction — tested with a stub, no DB. `answer_question` now folds those
      events, so it stays the single loop (existing agent tests still pass).
- [x] `POST /chat` streams SSE events (tool steps + generated SQL + answer + token/cost); `GET /health` 200.
      Verified live: full ordered event stream for a Spanish question.
- [x] Endpoint tested without a DB (dependency override) + a live integration test.
- [x] Unit gates green (97); `sse-starlette` avoided — plain `StreamingResponse` + manual SSE.
      No token streaming yet (mock returns whole responses); step-level streaming is the useful granularity.

---
Log → [`discussion.md`](discussion.md)
