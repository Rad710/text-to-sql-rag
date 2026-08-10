"""The bounded agentic tool-loop — where retrieval, generation, and safety compose.

The model is given two tools and iterates (capped at ``max_iterations``): call the LLM → dispatch
its `search_schema` / `run_sql` tool calls → feed the results back → repeat until it produces a
final answer. Self-correction is native: a `run_sql` error or empty result is fed back verbatim, so
the model can revise and retry within the same loop.

The tools are injected as plain callables, so the loop is testable with stubs (no DB, no network).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings, get_settings
from app.execution import RunResult, format_result
from app.execution import run_sql as execute_sql
from app.llm import ZERO_USAGE, LlmProvider, LlmResponse, Usage, get_llm
from app.prompts import SYSTEM_PROMPT, TOOLS
from app.schema import SchemaInfo

_FALLBACK = "No pude generar una respuesta."
_EXHAUSTED = "No pude completar la consulta dentro del número de pasos permitido."


@dataclass(frozen=True, slots=True)
class AgentTools:
    search_schema: Callable[[str], str]  # question → retrieved context (as a prompt block)
    run_sql: Callable[[str], RunResult]  # query → structured result


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    name: str
    arguments: dict[str, Any]
    result_preview: str


@dataclass(frozen=True, slots=True)
class AgentResult:
    answer: str
    sql: list[str] = field(default_factory=list)  # run_sql queries attempted, in order
    trace: list[ToolInvocation] = field(default_factory=list)
    usage: Usage = ZERO_USAGE
    iterations: int = 0


def answer_question(
    question: str, llm: LlmProvider, tools: AgentTools, max_iterations: int
) -> AgentResult:
    """Drive the bounded tool-loop and return the answer plus a trace."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    usage = ZERO_USAGE
    trace: list[ToolInvocation] = []
    sql_attempts: list[str] = []

    for iteration in range(1, max_iterations + 1):
        response = llm.complete(messages, TOOLS)
        usage = usage + response.usage

        if not response.tool_calls:
            return AgentResult(
                answer=response.content or _FALLBACK,
                sql=sql_attempts,
                trace=trace,
                usage=usage,
                iterations=iteration,
            )

        messages.append(_assistant_message(response))
        for call in response.tool_calls:
            content = _dispatch(call.name, call.arguments, tools, question, sql_attempts)
            trace.append(ToolInvocation(call.name, call.arguments, content[:200]))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

    return AgentResult(
        answer=_EXHAUSTED, sql=sql_attempts, trace=trace, usage=usage, iterations=max_iterations
    )


def _dispatch(
    name: str,
    arguments: dict[str, Any],
    tools: AgentTools,
    question: str,
    sql_attempts: list[str],
) -> str:
    if name == "search_schema":
        return tools.search_schema(str(arguments.get("question") or question))
    if name == "run_sql":
        query = str(arguments.get("query") or "")
        sql_attempts.append(query)
        return format_result(tools.run_sql(query))
    return f"ERROR: unknown tool '{name}'"


def _assistant_message(response: LlmResponse) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": response.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in response.tool_calls
        ],
    }


def build_tools(store: Any, schema: SchemaInfo, settings: Settings) -> AgentTools:
    """Wire the real tools: `search_schema` over the RAG store, `run_sql` against MySQL."""
    return AgentTools(
        search_schema=lambda q: store.search_schema(q, schema).as_prompt(),
        run_sql=lambda query: execute_sql(query, settings),
    )


def ask(
    question: str,
    *,
    store: Any,
    schema: SchemaInfo,
    settings: Settings | None = None,
    llm: LlmProvider | None = None,
) -> AgentResult:
    """High-level entry point used by the API: assemble tools + provider and run the loop."""
    resolved = settings or get_settings()
    provider = llm or get_llm(resolved)
    tools = build_tools(store, schema, resolved)
    return answer_question(question, provider, tools, resolved.agent_max_iterations)
