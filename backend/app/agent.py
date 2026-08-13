"""The bounded agentic tool-loop — where retrieval, generation, and safety compose.

The model is given two tools and iterates (capped at ``max_iterations``): call the LLM → dispatch
its `search_schema` / `run_sql` tool calls → feed the results back → repeat until it produces a
final answer. Self-correction is native: a `run_sql` error or empty result is fed back verbatim, so
the model can revise and retry within the same loop.

The tools are injected as plain callables, so the loop is testable with stubs (no DB, no network).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from app.config import Settings, get_settings
from app.llm.client import ZERO_USAGE, LlmProvider, LlmResponse, Usage, get_llm
from app.llm.prompts import SYSTEM_PROMPT, TOOLS
from app.rag.engine import RagStore
from app.rag.schema import SchemaInfo
from app.safety.execution import RunResult, format_result
from app.safety.execution import run_sql as execute_sql

_LANGUAGE_NAMES = {"es": "Spanish", "en": "English"}
_FALLBACK = {
    "es": "No pude generar una respuesta.",
    "en": "I couldn't generate an answer.",
}
_EXHAUSTED = {
    "es": "No pude completar la consulta dentro del número de pasos permitido.",
    "en": "I couldn't complete the query within the allowed number of steps.",
}


def _lang(language: str | None) -> str:
    """Normalize the requested UI language (task 0040); Spanish is the domain default."""
    return language if language in ("es", "en") else "es"


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


@dataclass(frozen=True, slots=True)
class AgentEvent:
    """One streamed step of the loop (for SSE). ``type`` ∈ tool_start | tool_result | answer |
    usage | done; ``data`` is JSON-serializable."""

    type: str
    data: dict[str, Any]


def stream_answer(
    question: str,
    llm: LlmProvider,
    tools: AgentTools,
    max_iterations: int,
    history: list[dict[str, Any]] | None = None,
    language: str | None = None,
) -> Iterator[AgentEvent]:
    """Drive the bounded tool-loop, yielding events as it runs (the single source of truth).

    ``history`` is prior conversation turns (``{role, content}`` text) prepended before the current
    question so the model has context for follow-ups (task 0016). ``language`` (task 0040) is the UI
    language — when set, the answer + fallback messages use it (the real LLM via a system directive,
    the mock via ``complete(language=…)``) rather than following the question's language.
    """
    lang = _lang(language)
    system = SYSTEM_PROMPT
    if language in ("es", "en"):
        system += (
            f"\n\nAlways write the final answer in {_LANGUAGE_NAMES[language]}, "
            "regardless of the language of the question."
        )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        *(history or []),
        {"role": "user", "content": question},
    ]
    usage = ZERO_USAGE

    for iteration in range(1, max_iterations + 1):
        response = llm.complete(messages, TOOLS, language=language)
        usage = usage + response.usage

        if not response.tool_calls:
            yield AgentEvent("answer", {"text": response.content or _FALLBACK[lang]})
            yield from _finish(usage, iteration)
            return

        messages.append(_assistant_message(response))
        for call in response.tool_calls:
            yield AgentEvent("tool_start", {"name": call.name, "arguments": call.arguments})
            content, structured = _run_tool(call.name, call.arguments, tools, question)
            yield AgentEvent(
                "tool_result",
                {
                    "name": call.name,
                    "arguments": call.arguments,
                    "preview": content[:200],
                    **structured,
                },
            )
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

    yield AgentEvent("answer", {"text": _EXHAUSTED[lang]})
    yield from _finish(usage, max_iterations)


def _finish(usage: Usage, iterations: int) -> Iterator[AgentEvent]:
    yield AgentEvent(
        "usage",
        {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.cost_usd,
            "iterations": iterations,
        },
    )
    yield AgentEvent("done", {})


def answer_question(
    question: str,
    llm: LlmProvider,
    tools: AgentTools,
    max_iterations: int,
    history: list[dict[str, Any]] | None = None,
    language: str | None = None,
) -> AgentResult:
    """Run the loop to completion and fold its events into an ``AgentResult``."""
    answer = _FALLBACK[_lang(language)]
    sql: list[str] = []
    trace: list[ToolInvocation] = []
    usage = ZERO_USAGE
    iterations = 0

    for event in stream_answer(question, llm, tools, max_iterations, history, language):
        if event.type == "tool_result":
            name, arguments = event.data["name"], event.data["arguments"]
            trace.append(ToolInvocation(name, arguments, event.data["preview"]))
            if name == "run_sql":
                sql.append(_sql_arg(arguments))
        elif event.type == "answer":
            answer = event.data["text"]
        elif event.type == "usage":
            usage = Usage(
                event.data["prompt_tokens"], event.data["completion_tokens"], event.data["cost_usd"]
            )
            iterations = event.data["iterations"]

    return AgentResult(answer=answer, sql=sql, trace=trace, usage=usage, iterations=iterations)


def _sql_arg(arguments: dict[str, Any]) -> str:
    """Extract the SQL from a ``run_sql`` tool call.

    The tool schema names the parameter ``query``, but smaller local models (e.g. ``llama3.1``)
    often emit ``sql`` instead. Accept either so a well-formed query isn't dropped as "empty SQL".
    The sqlglot validator + read-only DB user still enforce read-only whichever key the model used.
    """
    return str(arguments.get("query") or arguments.get("sql") or "")


def _run_tool(
    name: str, arguments: dict[str, Any], tools: AgentTools, question: str
) -> tuple[str, dict[str, Any]]:
    """Run a tool. Returns (model-facing text, structured payload for the SSE event).

    The text is what the LLM reads; the structured payload (run_sql rows) is what the frontend
    renders as a table (decision 0006).
    """
    if name == "search_schema":
        return tools.search_schema(str(arguments.get("question") or question)), {}
    if name == "run_sql":
        result = tools.run_sql(_sql_arg(arguments))
        if result.error:
            return format_result(result), {}
        structured = {
            "columns": result.columns,
            "rows": result.as_cells(),
            "row_count": result.row_count,
            "truncated": result.truncated,
        }
        return format_result(result), structured
    return f"ERROR: unknown tool '{name}'", {}


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
    store: RagStore,
    schema: SchemaInfo,
    settings: Settings | None = None,
    llm: LlmProvider | None = None,
    history: list[dict[str, Any]] | None = None,
    language: str | None = None,
) -> AgentResult:
    """High-level entry point used by the API: assemble tools + provider and run the loop."""
    resolved = settings or get_settings()
    provider = llm or get_llm(resolved)
    tools = build_tools(store, schema, resolved)
    return answer_question(
        question, provider, tools, resolved.agent_max_iterations, history, language
    )


def stream(
    question: str,
    *,
    store: RagStore,
    schema: SchemaInfo,
    settings: Settings | None = None,
    llm: LlmProvider | None = None,
    history: list[dict[str, Any]] | None = None,
    language: str | None = None,
) -> Iterator[AgentEvent]:
    """Streaming counterpart of :func:`ask` — yields agent events for the SSE endpoint."""
    resolved = settings or get_settings()
    provider = llm or get_llm(resolved)
    tools = build_tools(store, schema, resolved)
    return stream_answer(
        question, provider, tools, resolved.agent_max_iterations, history, language
    )
