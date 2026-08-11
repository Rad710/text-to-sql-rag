# 0011 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Picked up as the final (stretch) task. Owner chose **both transports** — stdio default +
  `--http` (streamable HTTP). Kept it a thin adapter: reuse `app.safety.execution.run_sql` +
  `RagStore.search_schema` verbatim so decision 0003's guarantees hold identically; no re-implementation.
- 2026-08-11: SDK reality check — the official `mcp` package is at **2.0.0** and the old
  `mcp.server.fastmcp.FastMCP` path is gone; the high-level class is now `MCPServer` (import
  `from mcp.server import MCPServer`), with `@server.tool()` and `run(transport="stdio"|"streamable-http")`.
  Adjusted to the new API after introspecting the installed package. Added `mcp` as an opt-in `[mcp]`
  extra (core API stays lean) and to the dev group so CI exercises it.
- 2026-08-11: Verified end-to-end with a real client (`mcp` stdio client launching
  `python -m app.mcp_server`): `initialize` + `list_tools` → both tools; `run_sql('SELECT COUNT(*) …
  FROM shipment')` → Markdown table (n=16) against live MySQL; `run_sql('DELETE FROM shipment')` →
  `ERROR: rejected: only read-only SELECT queries are allowed (got Delete)` — safety layer blocks the
  write through the MCP path, no crash, no mutation. Unit tests cover the wiring without a DB. Gates:
  ruff/mypy/pytest green (127 unit tests), coverage 86%.
