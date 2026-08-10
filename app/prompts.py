"""System prompt, tool schemas, and canned text for the LLM.

Kept as versioned constants (not inline string-building) so prompt changes are reviewable. The tool
schemas mirror the two tools the agent loop exposes: `search_schema` (RAG) and `run_sql` (validated,
read-only execution).
"""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """\
You are a data assistant for DYR Transportes, a Paraguayan freight company. Answer the user's \
questions about its database.

How to work:
- First call `search_schema` with the user's question to get the relevant tables, columns, join \
hints, and example queries. Use ONLY the tables and columns it returns.
- Then call `run_sql` with a SINGLE read-only MySQL `SELECT` (or `WITH ... SELECT`). Never write \
`INSERT`/`UPDATE`/`DELETE`/DDL — `run_sql` will reject them.
- Every business table has a `deleted` flag; always filter `WHERE deleted = 0`.
- If `run_sql` returns an error, or an empty or clearly implausible result, read the message and \
revise the query, then try again.
- When you have the data, answer the user in Spanish, concisely, using ONLY the query results. \
Never invent tables, columns, or numbers.

If the question is not about the database, answer briefly without calling any tool.
"""

SEARCH_SCHEMA_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_schema",
        "description": (
            "Retrieve the relevant tables, columns, foreign-key join hints, business rules, and "
            "example queries for a natural-language question about the freight database."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The user's question, in natural language.",
                }
            },
            "required": ["question"],
        },
    },
}

RUN_SQL_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": (
            "Execute a single read-only MySQL SELECT against the freight database and return the "
            "rows. Rejects anything that is not a single SELECT/CTE."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A single read-only SELECT statement.",
                }
            },
            "required": ["query"],
        },
    },
}

TOOLS: list[dict[str, Any]] = [SEARCH_SCHEMA_TOOL, RUN_SQL_TOOL]

# Answer for questions that aren't about the database (mock mode + a fallback for real mode).
GENERAL_ANSWER = (
    "Puedo responder preguntas sobre la base de datos de DYR Transportes: viajes y cobranzas, "
    "choferes, rutas, productos, facturación (planillas) y liquidaciones. ¿Qué te gustaría saber?"
)
