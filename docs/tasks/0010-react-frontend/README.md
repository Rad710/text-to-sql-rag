---
status: done
updated: 2026-08-10
depends_on: [0009]
decision: 0005
---

# 0010 — Vite + React + TypeScript frontend (assistant-ui)

## Goal
The clickable UI ([decision 0005](../../decisions/0005-custom-fastapi-sse-react-frontend.md)): a Vite +
React + TS single-page app that consumes the SSE `/chat` API, rendering the conversation and the
**generated SQL** as it streams, plus token/cost. Bilingual (answers follow the question's language).

## Context
Consumes the streaming API from [0009](../0009-streaming-api/). Uses **assistant-ui** for the runtime +
chat primitives (streaming, autoscroll, composer) and `react-markdown` for rendering — styled with our own
CSS so it looks bespoke and stays under our control. assistant-ui is frontend-only; we own the API.

## Plan
1. `frontend/` — Vite + React 19 + TS scaffold (package.json, vite.config with a `/chat` dev proxy,
   tsconfig, index.html, main.tsx, index.css).
2. `frontend/src/runtime.ts` — a `ChatModelAdapter` (assistant-ui `useLocalRuntime`) that POSTs to `/chat`,
   parses our SSE events, and builds a progressive markdown message (SQL code block → answer → token/cost).
3. `frontend/src/App.tsx` — Thread composed from `ThreadPrimitive`/`MessagePrimitive`/`ComposerPrimitive`
   + `MarkdownTextPrimitive`; bilingual suggestion chips; header.

## Done when
- [x] `pnpm build` (tsc + vite) is clean; the app typechecks against assistant-ui's real API.
- [x] The SSE adapter consumes the `/chat` stream (tool steps → SQL → answer → usage). Verified live via
      the Vite dev proxy: the full ordered event stream reaches the browser origin.
- [x] Bilingual suggestions + composer; SQL rendered as a code block, answer + token/cost footer.
- [~] In-browser render QA: **not auto-verified** in this environment — the bundled headless browser
      (patchright) executes no JS and the Playwright MCP isn't loaded here. Build + typecheck + SSE wiring
      are green; a Playwright-MCP pass is queued for a session where the MCP is connected (see discussion).

---
Log → [`discussion.md`](discussion.md)
