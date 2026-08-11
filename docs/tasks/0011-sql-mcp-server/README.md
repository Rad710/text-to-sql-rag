---
status: in-progress
updated: 2026-08-11
depends_on: [0004, 0006]
decision: null
---

# 0011 — Standalone read-only SQL MCP server (stretch)

## Goal
Expose the assistant's two core capabilities — schema search and safe read-only SQL — as a standalone
**Model Context Protocol** server, so any MCP client (Claude Desktop/Code, the MCP Inspector) can query
the synthetic DYR Transportes DB directly, with the same safety guarantees. A differentiator showing the
retrieval + SQL-safety layers are cleanly reusable outside the app's own agent loop.

## Context
Pure reuse — no new safety or retrieval logic. `run_sql` wraps [`app.safety.execution.run_sql`](../../../app/safety/execution.py)
(sqlglot validate → enforced LIMIT → read-only user + timeout + row cap, decision 0003; never mutates,
never raises), and `search_schema` wraps [`RagStore.search_schema`](../../../app/rag/engine.py). The MCP
layer is a thin adapter, mirroring the API's lazy `get_service` seam (`app/api.py`).

Decision (owner, 2026-08-11): support **both** transports — **stdio** by default (local client launches
it as a subprocess) and **streamable HTTP** via `--http`. SDK: the official `mcp` package (2.0), opt-in
via the `[mcp]` extra so the core API stays lean.

## Plan
1. `app/mcp_server.py` — an `MCPServer` with two `@server.tool()`s (`search_schema`, `run_sql`) over the
   reused layers; lazy `get_service` (introspect + seed Chroma on first call); `main()` with argparse
   (`--http`/`--host`/`--port`), stdio default; `python -m app.mcp_server`.
2. `pyproject.toml` — `[project.optional-dependencies] mcp = ["mcp>=2.0"]`; also in the dev group so CI
   tests it.
3. `tests/test_mcp_server.py` — tool wiring: `run_sql` formats rows / surfaces a safety rejection as
   `ERROR:` text; `search_schema` returns retrieved context; both tools registered (`list_tools`).
4. README — a short "SQL MCP server" section + a ready-to-paste client `mcpServers` config.

## Done when
- [x] `app/mcp_server.py` exposes `search_schema` + `run_sql` over reused safety/RAG; stdio + `--http`.
- [x] Unit tests green (`ruff`/`mypy`/`pytest`); coverage floor holds.
- [x] Verified end-to-end with a real MCP client over stdio: handshake + `list_tools` shows both;
      `run_sql` returns rows against live MySQL and **rejects a `DELETE`** as `ERROR:` text (no mutation).
- [x] README documents running it + a client config.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
