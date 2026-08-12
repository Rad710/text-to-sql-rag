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

You work in steps. Each step, reply with EXACTLY ONE fenced code block and nothing else:

- To see the schema, tag the block `schema` and describe what you need in words:
    ```schema
    total revenue per route
    ```
- To query, tag the block `sql` with a SINGLE read-only MySQL SELECT (or WITH ... SELECT):
    ```sql
    SELECT origin, destination, SUM(price) AS revenue FROM shipment WHERE deleted=0 GROUP BY 1,2
    ```

Rules:
- Send the `schema` block FIRST; use ONLY the tables/columns it returns — never invent names.
- Then send one `sql` block. Never write INSERT/UPDATE/DELETE/DDL. Every business table has a \
`deleted` flag; filter `WHERE deleted = 0`.
- If a query errors or returns an empty/odd result, read it and send a corrected `sql` block.
- When the results answer it, reply with the final answer as PLAIN PROSE (no code block), \
in the user's language (Spanish or English), using only the query results.
- If the question is not about the database, reply directly in one short prose sentence, no block.
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

# Answers for questions that aren't about the database (mock mode + a fallback for real mode).
GENERAL_ANSWER_ES = (
    "Puedo responder preguntas sobre la base de datos de DYR Transportes: viajes y cobranzas, "
    "choferes, rutas, productos, facturación (planillas) y liquidaciones. ¿Qué te gustaría saber?"
)
GENERAL_ANSWER_EN = (
    "I can answer questions about the DYR Transportes database: shipments and collections, "
    "drivers, routes, products, billing (planillas) and driver settlements. "
    "What would you like to know?"
)
