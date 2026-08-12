"""Standalone read-only SQL **MCP server** over the synthetic DYR Transportes DB (task 0011).

Exposes the same two capabilities the agent loop uses, as Model-Context-Protocol tools any MCP
client (Claude Desktop/Code, the MCP Inspector, …) can call:

- ``search_schema(question)`` — RAG over the annotated DDL + business docs + Q→SQL examples
  (reuses :class:`app.rag.engine.RagStore`).
- ``run_sql(query)`` — the full SQL-safety pipeline: ``sqlglot`` validate → enforced ``LIMIT`` →
  read-only user + timeout + row cap (reuses :func:`app.safety.execution.run_sql`). It never
  mutates data and never raises for a bad query — a rejection comes back as an ``ERROR:`` message.

Nothing here re-implements safety or retrieval; it is a thin MCP adapter over the existing layers,
so the guarantees (decision 0003) hold identically. Run it over **stdio** (default, for a local
client) or **streamable HTTP** (``--http``):

    uv run python -m app.mcp_server            # stdio
    uv run python -m app.mcp_server --http     # http on 127.0.0.1:8848 (/mcp)

Requires the ``mcp`` extra:  ``uv sync --extra mcp``.
"""

from __future__ import annotations

import argparse

from mcp.server import MCPServer

from app.rag.corpus import build_corpus
from app.rag.engine import RagStore
from app.rag.introspect import introspect_from_settings
from app.rag.schema import SchemaInfo
from app.safety.execution import format_result
from app.safety.execution import run_sql as _run_sql

server = MCPServer(
    name="dyr-sql",
    instructions=(
        "Read-only SQL assistant over the synthetic DYR Transportes freight database. Call "
        "search_schema first to retrieve the relevant tables/DDL, then run_sql to execute a single "
        "read-only SELECT. All queries are validated and capped; writes are impossible."
    ),
)

# Built once on first tool call (introspect MySQL + seed the RAG store) — never on import, so the
# module stays import-safe with no DB/network. Mirrors the API's get_service seam (app/api.py).
_service: tuple[RagStore, SchemaInfo] | None = None


def get_service() -> tuple[RagStore, SchemaInfo]:
    """Memoized (RAG store, schema); introspects the DB and seeds Chroma on first use."""
    global _service
    if _service is None:
        from app.config import get_settings

        schema = introspect_from_settings()
        store = RagStore(path=get_settings().chroma_path)
        store.sync_corpus(build_corpus(schema))
        _service = (store, schema)
    return _service


@server.tool(
    description=(
        "Retrieve the relevant database schema for a natural-language question: annotated DDL, "
        "business-rule notes, and example question→SQL pairs. Call this before writing SQL."
    )
)
def search_schema(question: str) -> str:
    """Return the RAG-retrieved schema context for ``question`` as prompt-ready text."""
    store, schema = get_service()
    return store.search_schema(question, schema).as_prompt()


@server.tool(
    description=(
        "Execute a single read-only SELECT against the DYR Transportes DB and return the rows as a "
        "Markdown table. The query is validated (single SELECT/CTE only) and a LIMIT enforced; "
        "DML/DDL and multiple statements are rejected. Returns 'ERROR: …' for a rejected query."
    )
)
def run_sql(query: str) -> str:
    """Validate, bound, and execute ``query`` read-only; return a Markdown table or an error."""
    return format_result(_run_sql(query))


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: stdio by default, ``--http`` for the streamable-HTTP transport."""
    parser = argparse.ArgumentParser(description="DYR Transportes read-only SQL MCP server.")
    parser.add_argument(
        "--http", action="store_true", help="serve over streamable HTTP instead of stdio"
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (with --http)")
    parser.add_argument("--port", type=int, default=8848, help="HTTP port (with --http)")
    args = parser.parse_args(argv)

    if args.http:
        server.run("streamable-http", host=args.host, port=args.port)
    else:
        server.run("stdio")


if __name__ == "__main__":
    main()
