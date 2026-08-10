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
