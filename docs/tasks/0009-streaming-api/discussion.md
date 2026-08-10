# 0009 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Scope reset from "FastAPI + hand-rolled static page" to "streaming backend for a custom
  React UI" after choosing [decision 0005](../../decisions/0005-custom-fastapi-sse-react-frontend.md)
  (custom FastAPI SSE + Vite/React/TS + assistant-ui over Chainlit). The earlier redundant FastAPI stub +
  hand-rolled HTML were removed. The bilingual backend (examples/prompt/language detection) and the
  OpenAIProvider tests done during that detour were kept — they're UI-independent.
- 2026-08-10: Keep the sync `answer_question` (tests + eval 0012) and add a streaming generator beside it,
  sharing the loop body — don't fork the logic. Emit a typed event protocol so the UI can render tool steps
  (the generated SQL especially) as they happen.
