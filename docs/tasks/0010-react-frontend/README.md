---
status: done
updated: 2026-08-11
depends_on: [0009]
decision: [0005, 0006]
---

> ✅ **DONE.** The frontend renders the conversation, collapsible tool-call steps, the result table, and
> token/cost — styled, bilingual, regression-tested, browser-verified. Landed and committed:
> 1. **Crash fix:** the `0.11.58` React-19 `useLocalRuntime` crash (`_getInitializePromise`) — resolved by
>    upgrading to assistant-ui `0.15`, browser-verified; plus a **vitest + jsdom** mount/stream suite and a
>    **frontend CI job** so the crash class can't ship "done" again.
> 2. **Styled Thread + native tool-call rendering** (restores the decision-0005 standard that had been
>    ignored): assistant-ui's shadcn/Tailwind `Thread`; SSE tool events map to **tool-call parts**, so
>    `search_schema` + `run_sql` render as **collapsible steps**, and `run_sql`'s **structured rows render
>    as a real table** ([decision 0006](../../decisions/0006-structured-results-over-sse.md)) instead of
>    backend-formatted Markdown. Browser-verified.
> 3. **Toolchain modernized** (separate concern, done alongside): Vite 8, TypeScript 7, Biome lint/format.
> 4. **Chainlit-parity scope now decided** — multi-turn, auth, history/persistence, and feedback are
>    scheduled as their own tasks **0016 / 0018 / 0019 / 0020** (with decisions 0008 JWT-store note / 0009).

# 0010 — Vite + React + TypeScript frontend (assistant-ui)

## Goal
The clickable UI ([decision 0005](../../decisions/0005-custom-fastapi-sse-react-frontend.md)): a Vite +
React + TS single-page app that consumes the SSE `/chat` API, rendering the conversation and the
**generated SQL** as it streams, plus token/cost. Bilingual (answers follow the question's language).

## Context
Consumes the streaming API from [0009](../0009-streaming-api/). Uses **assistant-ui**'s shadcn/Tailwind
styled `Thread` (runtime + streaming + tool-call step rendering + Markdown), themed to the DYR brand.
assistant-ui is frontend-only; we own the API and the SSE protocol.

## Plan
1. `frontend/` — Vite + React 19 + TS scaffold (package.json, vite.config with a `/chat` dev proxy,
   tsconfig, index.html, main.tsx, index.css).
2. `frontend/src/runtime.ts` — a `ChatModelAdapter` (assistant-ui `useLocalRuntime`) that POSTs to `/chat`
   and maps our SSE events to assistant-ui message parts: `search_schema`/`run_sql` → **tool-call parts**
   (SQL + structured rows), then answer + token/cost.
3. `frontend/src/App.tsx` — the styled `Thread` with a branded bilingual welcome + a custom `run_sql`
   tool renderer (`components/run-sql-tool.tsx`) that draws the result table from the structured rows.

## Done when
- [x] `pnpm build` (tsc + vite) is clean; the app typechecks against assistant-ui's real API.
- [x] The SSE adapter consumes the `/chat` stream (tool steps → SQL → answer → usage). Verified live via
      the Vite dev proxy: the full ordered event stream reaches the browser origin (curl).
- [x] Bilingual suggestions + composer; answer + token/cost footer.
- [x] **The chat actually renders + works in a real browser** — verified via the Playwright MCP (loaded
      the app, clicked a suggestion, tool steps + result table + answer + token/cost streamed in, no crash).
      Durable proof lives in the `vitest` jsdom suite + the frontend CI job, not a point-in-time screenshot.
- [x] **Styled Thread + tool-call rendering (decisions 0005/0006)** — adopted assistant-ui's shadcn/Tailwind
      styled `Thread`; the SSE tool events map to native **tool-call parts**, so `search_schema` + `run_sql`
      render as **collapsible steps**; `run_sql`'s **structured rows render as a real table** (the backend
      streams `{columns, rows}`, the frontend owns the table) and the answer is prose. Browser-verified.
- [x] **Regression guard** — a `vitest` + `@testing-library/react` (jsdom) suite that mounts `<App />`
      (catches mount-time runtime crashes) and drives a mocked SSE stream (tool-call steps → answer → usage);
      a `frontend` CI job runs `pnpm build` + `pnpm test`. `pnpm test` green (2/2).
- [x] **Chainlit-parity scope decided** (auth / feedback / history / multi-turn) → scheduled as tasks
      0016 / 0018 / 0019 / 0020 (+ decisions 0008, 0009).
- [x] Committed and `status: done`.

---
Log → [`discussion.md`](discussion.md)
