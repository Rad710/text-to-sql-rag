# 0010 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: assistant-ui 0.11 has no pre-styled `Thread` export (styled UI moved to shadcn-style
  scaffolding / a separate package with uncertain 0.11 compat). Chose to compose from the exported
  **primitives** (`ThreadPrimitive`/`MessagePrimitive`/`ComposerPrimitive` + `MarkdownTextPrimitive`) with
  our own CSS — reliable, no extra deps, and we own the styling. Runtime: `useLocalRuntime` +
  a `ChatModelAdapter` that parses our generic SSE (keeps the backend protocol clean, not coupled to
  assistant-ui's wire format).
- 2026-08-10: esbuild's install script is blocked by this machine's pnpm security policy; approved it via
  `pnpm-workspace.yaml` (`onlyBuiltDependencies: [esbuild]`). React 19 + Vite 6.
- 2026-08-10: **Browser QA blocked by environment.** The bundled patchright browser (from a VS Code
  extension) executes zero page JS (35–66s loads, empty `#root`, no console output) — a broken binary, not
  our app. The configured Playwright MCP (`npx @playwright/mcp --headless`) is scoped to other projects and
  MCP servers only attach at session start, so it can't be hot-loaded here. Added a project `.mcp.json`
  (gitignored) so a session launched from `~/myprojects/text-to-sql-rag` loads it. Verified instead: clean
  `pnpm build`, tsc against the real assistant-ui types, and the SSE stream reaching the browser origin
  through the Vite proxy (curl). A Playwright-MCP render pass will run once the MCP is connected.
- 2026-08-10 (later): **The UI crashed on first real browser load** (user opened Chrome). assistant-ui
  `0.11.58`'s legacy `useLocalRuntime` throws `Cannot set properties of undefined (setting
  '_getInitializePromise')` in `LocalThreadRuntimeCore` under React 19 — blank page. Root cause: I marked
  0010 "done" without ever rendering it in a browser (only tsc/build/curl passed), so the crash slipped
  through.
- 2026-08-10: **Mistake — I then replaced assistant-ui with a hand-rolled chat.** The user (rightly)
  objected: they chose assistant-ui; don't swap a chosen library out on your own. **Reverted** to the
  assistant-ui code and **upgraded 0.11.58 → 0.15.12** (the current line; 0.11's legacy runtime is the
  bug). It builds (`pnpm build` clean, tsc against 0.15), but **is not yet browser-verified** — the upgrade
  (package.json + pnpm-lock) is uncommitted. Lesson captured in memory: never call a UI done unseen in a
  real browser; don't swap a chosen lib.
- 2026-08-10: **Playwright MCP couldn't be loaded** to test: this session's cwd is `/home/his/text-to-sql-rag`
  (not `~/myprojects/text-to-sql-rag`), and the `playwright` MCP is only configured for other projects — so
  restarting didn't attach it (no process, no `mcp__playwright__*` tools). Added `.mcp.json` (gitignored) in
  `~/myprojects/text-to-sql-rag` **and** in the current cwd. Resolution: **next session must launch from
  `~/myprojects/text-to-sql-rag`** (loads the MCP + fixes the cwd quirk), then verify the chat with
  Playwright and fix any remaining assistant-ui `0.15` runtime issue.
- 2026-08-10 (resolved): **Browser render verified — task complete.** Launched the full stack from
  `~/myprojects/text-to-sql-rag` (MySQL healthy, `uv run uvicorn app.api:app` on :8000, `pnpm dev` on
  :5173) and drove it with the Playwright MCP. The page loads with **no crash** (the only console entry is
  a harmless `favicon.ico` 404); the React-19 `_getInitializePromise` crash is gone on assistant-ui
  `0.15.12`. Clicked a suggestion chip → the SSE stream renders in-browser: user bubble → generated SQL as
  a `sql` code block → answer → token/cost footer (`3 steps · 3564 tokens · $0.0000`). Screenshot saved as
  `render-verified.png`. **Still uncommitted** — the per-task commit (assistant-ui `0.15` upgrade) + the
  status flip to `done` are left for the next session working this repo on its own branch.
- 2026-08-10 (session 2): **Adopted assistant-ui's styled Thread + restored decision 0005's tool-call
  rendering (which had been ignored).** The prior adapter flattened the SSE stream into one Markdown blob —
  `search_schema` invisible, `run_sql` a plain code block, `tool_result` dropped — contradicting decision
  0005 ("assistant-ui … **tool-call rendering** … generated SQL as **collapsible steps**"). Fixes:
  - Ran assistant-ui's shadcn/Tailwind registry (`shadcn init --template vite -b base -p nova` +
    `add …/thread.json`) to generate the styled `Thread` (Tailwind v4 via `@tailwindcss/vite`, Base-UI
    flavor, `@/` alias, `components/ui/*` + `components/assistant-ui/*`). Replaced the hand-rolled primitives
    + CSS that decision 0005 had explicitly wanted to avoid ("polished … without hand-rolling CSS").
  - Rewrote `runtime.ts` to map SSE events → native assistant-ui **tool-call parts**: `search_schema` +
    `run_sql` now render as collapsible steps (SQL as `argsText`, tool result preview) via
    `ToolFallback`/`ToolGroup`; the answer + token/cost footer follow as a trailing text part.
  - Backend `format_result` now emits a **GFM Markdown table** (was header + a `----` line, which Markdown
    rendered as a stray setext heading); the frontend renders it as a real table.
  - **Regression guard:** vitest + Testing Library (jsdom) suite that actually mounts `<App/>` — catching the
    mount-time runtime-crash class that `tsc`/`vite build`/curl all missed last time — plus a mocked SSE
    stream asserting the tool-step group + answer + usage. A `frontend` CI job runs `pnpm build` + `pnpm
    test`. Test deps pinned to latest (vitest 4, jsdom 30, jest-dom 7).
  - Browser-verified via the Playwright MCP: collapsible "2 tool calls" → `search_schema`/`run_sql` steps →
    answer table; typed input + English/Spanish both work; 0 console errors.
- 2026-08-10 (session 2): **Open scope surfaced, not decided.** Auth, feedback, conversation
  history/persistence, and multi-turn were never actually scoped for this build — they belong to the
  reference Chainlit app (see prior session `e8453d31`), and the only forward-looking note advised against
  over-building auth/history. To be written up as separate tasks + decisions before any build. The stack is
  currently single-turn (`/chat` takes one `question`; the adapter sends only the latest message).
- 2026-08-11: **Structured results + codebase modernization (separate concerns, done this session).**
  - **Decision 0006** — the UI table no longer comes from backend Markdown: the SSE `run_sql` `tool_result`
    now carries structured `{columns, rows}`, the frontend renders a real table (custom `run_sql` tool UI),
    and the mock answer is prose. `format_result` stays model-facing text only.
  - **Strict typing** — `store: RagStore` (was `Any`) + mypy `strict = true` (commit 209b31b).
  - **Decision 0007** — `app/` regrouped into `safety/`, `rag/`, `llm/` sub-packages; imports rewritten.
  - **Toolchain** — Vite 8, TypeScript 7, `@vitejs/plugin-react` 6, and **Biome** as the lint/formatter
    (the frontend had none). Chose Biome over Prettier+ESLint because `typescript-eslint` doesn't support
    TS 7 yet (peer dep `<6.1.0`), whereas Biome's own parser does — keeps us on latest TS with working lint.
  - All gates green (mypy strict, 99 tests; Biome, build tsc7+vite8, 2 vitest); browser-verified on Vite 8.
  - **Still open:** the Chainlit-parity scope decision (auth / feedback / history / multi-turn) — 0010 stays
    `in-progress` until that's decided.
