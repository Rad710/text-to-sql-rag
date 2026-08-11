---
status: done
updated: 2026-08-11
depends_on: [0009, 0010]
---

# 0016 — Multi-turn conversation (thread history through the loop)

## Goal
Fix the single-turn flaw the E2E test exposed: thread **conversation history** through `/chat`, the agent
loop, and the frontend adapter so follow-ups ("¿y cuál es la de mayor facturación?") have context.

## Context
`/chat` previously took only `{question}` and the agent built `[system, user]` — each question was
independent. The frontend adapter sent only the last message. With a real LLM (task 0015), passing prior
turns as context is all that's needed; the keyword mock is limited but must at least key off the **latest**
question, not the first.

## Plan
1. **API** (`app/api.py`): a `Turn {role, content}` model; `ChatRequest.history: list[Turn] = []`; pass it
   into `stream(...)`.
2. **Agent** (`app/agent.py`): `history` param on `stream_answer`/`answer_question`/`ask`/`stream`; build
   `[system, *history, {user: question}]`.
3. **Mock** (`app/llm/client.py`): answer the **latest** user turn (`_latest_user_message`), not the first.
4. **Frontend** (`runtime.ts`): send `{question, history}` — prior turns as `{role, content}` text, with the
   UI-only token/cost footer stripped from assistant turns.

## Done when
- [x] `/chat` accepts `history`; the agent prepends it before the question (unit + API tests).
- [x] The mock keys off the latest user turn (test).
- [x] The frontend adapter sends `history` (empty on the first turn; populated after) — frontend test +
      **browser-verified** (turn 2's POST body carries both prior turns, footer stripped, 0 console errors).
- [x] `ruff`/`mypy`/`pytest` (104) + Biome/build/vitest green. Committed.

> **Note:** with the deterministic keyword **mock**, follow-ups still won't be answered contextually — that
> needs a real model (task 0015 / Ollama/vLLM). This task delivers the plumbing; the context now reaches
> the model.

---
Log → [`discussion.md`](discussion.md)
