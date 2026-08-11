"""Unit tests for the agent loop (stub LLM + fake tools — no DB, no network)."""

from __future__ import annotations

from typing import Any

import pytest

from app.agent import _EXHAUSTED, AgentTools, answer_question, stream_answer
from app.llm.client import LlmResponse, ToolCall, Usage
from app.safety.execution import RunResult


class StubLLM:
    """Returns a scripted sequence of responses, ignoring the messages."""

    def __init__(self, responses: list[LlmResponse]) -> None:
        self._responses = responses
        self._i = 0

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> LlmResponse:
        response = self._responses[self._i]
        self._i += 1
        return response


class AlwaysToolLLM:
    """Always asks for a tool call — never finishes (to exercise the iteration cap)."""

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> LlmResponse:
        return _call("run_sql", {"query": "SELECT 1"})


def _call(name: str, args: dict[str, Any]) -> LlmResponse:
    calls = [ToolCall(f"c-{name}", name, args)]
    return LlmResponse(content=None, tool_calls=calls, usage=Usage(5, 5, 0.0))


def _answer(text: str) -> LlmResponse:
    return LlmResponse(content=text, tool_calls=[], usage=Usage(5, 3, 0.0))


def _tools(run_sql: Any) -> AgentTools:
    return AgentTools(search_schema=lambda q: "(schema context)", run_sql=run_sql)


def test_happy_path() -> None:
    responses = [
        _call("search_schema", {"question": "q"}),
        _call("run_sql", {"query": "SELECT 1"}),
        _answer("La respuesta es 42."),
    ]
    result = answer_question(
        "q", StubLLM(responses), _tools(lambda q: RunResult(sql=q, columns=["n"], rows=[(42,)])), 6
    )
    assert result.answer == "La respuesta es 42."
    assert result.sql == ["SELECT 1"]
    assert [t.name for t in result.trace] == ["search_schema", "run_sql"]
    assert result.iterations == 3
    assert result.usage.total_tokens > 0


def test_self_correction_after_sql_error() -> None:
    responses = [
        _call("search_schema", {"question": "q"}),
        _call("run_sql", {"query": "SELECT bad"}),
        _call("run_sql", {"query": "SELECT good"}),
        _answer("listo"),
    ]

    def run_sql(query: str) -> RunResult:
        if "bad" in query:
            return RunResult(sql=query, error="Unknown column 'bad' in 'field list'")
        return RunResult(sql=query, columns=["n"], rows=[(1,)])

    result = answer_question("q", StubLLM(responses), _tools(run_sql), 6)
    assert result.sql == ["SELECT bad", "SELECT good"]  # retried after the error
    assert result.answer == "listo"
    run_previews = [t.result_preview for t in result.trace if t.name == "run_sql"]
    assert "ERROR" in run_previews[0]  # the error was fed back into the loop


def test_iteration_cap() -> None:
    result = answer_question(
        "q", AlwaysToolLLM(), _tools(lambda q: RunResult(sql=q, columns=["n"], rows=[(1,)])), 3
    )
    assert result.iterations == 3
    assert result.answer == _EXHAUSTED


def test_general_answer_without_tools() -> None:
    tools = _tools(lambda q: RunResult(sql=q))
    result = answer_question("hola", StubLLM([_answer("¡Hola!")]), tools, 6)
    assert result.answer == "¡Hola!"
    assert result.sql == [] and result.trace == []
    assert result.iterations == 1


def test_unknown_tool_is_reported() -> None:
    responses = [_call("weird_tool", {}), _answer("done")]
    result = answer_question("q", StubLLM(responses), _tools(lambda q: RunResult(sql=q)), 6)
    assert result.trace[0].result_preview.startswith("ERROR: unknown tool")
    assert result.answer == "done"


def test_stream_emits_ordered_events() -> None:
    responses = [
        _call("search_schema", {"question": "q"}),
        _call("run_sql", {"query": "SELECT 1"}),
        _answer("42"),
    ]
    tools = _tools(lambda q: RunResult(sql=q, columns=["n"], rows=[(1,)]))
    events = list(stream_answer("q", StubLLM(responses), tools, 6))

    assert [e.type for e in events] == [
        "tool_start",
        "tool_result",
        "tool_start",
        "tool_result",
        "answer",
        "usage",
        "done",
    ]
    run_starts = [e for e in events if e.type == "tool_start" and e.data["name"] == "run_sql"]
    assert run_starts[0].data["arguments"]["query"] == "SELECT 1"  # SQL streamed to the UI
    # run_sql carries structured rows for the frontend to render as a table (decision 0006).
    run_result = next(e for e in events if e.type == "tool_result" and e.data["name"] == "run_sql")
    assert run_result.data["columns"] == ["n"]
    assert run_result.data["rows"] == [["1"]]
    assert run_result.data["row_count"] == 1
    usage = next(e for e in events if e.type == "usage")
    assert usage.data["iterations"] == 3 and usage.data["total_tokens"] > 0


def test_stream_self_correction_emits_two_run_sql() -> None:
    responses = [
        _call("search_schema", {"question": "q"}),
        _call("run_sql", {"query": "SELECT bad"}),
        _call("run_sql", {"query": "SELECT good"}),
        _answer("ok"),
    ]

    def run_sql(query: str) -> RunResult:
        if "bad" in query:
            return RunResult(sql=query, error="boom")
        return RunResult(sql=query, columns=["n"], rows=[(1,)])

    events = list(stream_answer("q", StubLLM(responses), _tools(run_sql), 6))
    runs = [e for e in events if e.type == "tool_start" and e.data["name"] == "run_sql"]
    assert [r.data["arguments"]["query"] for r in runs] == ["SELECT bad", "SELECT good"]


def test_history_is_prepended_before_the_question() -> None:
    """Prior turns are threaded into the LLM messages ahead of the current question (task 0016)."""
    captured: list[dict[str, Any]] = []

    class CapturingLLM:
        def complete(
            self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
        ) -> LlmResponse:
            captured.extend(messages)
            return _answer("ok")

    history = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
    ]
    answer_question(
        "second question", CapturingLLM(), _tools(lambda q: RunResult(sql=q)), 6, history
    )
    pairs = [(m["role"], m["content"]) for m in captured]
    assert ("user", "first question") in pairs
    assert ("assistant", "first answer") in pairs
    assert captured[-1] == {"role": "user", "content": "second question"}


@pytest.mark.integration
def test_ask_end_to_end(tmp_path: Any) -> None:
    """Real mock LLM + real RAG store + live MySQL: question → answer."""
    import pymysql

    from app.agent import ask
    from app.rag.corpus import build_corpus
    from app.rag.embeddings import OfflineEmbedder
    from app.rag.engine import RagStore
    from app.rag.introspect import introspect_from_settings

    try:
        schema = introspect_from_settings()
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable: {exc}")

    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(schema))

    result = ask("total freight revenue per route", store=store, schema=schema)
    assert result.answer
    assert result.sql  # at least one run_sql attempt
    assert any(t.name == "run_sql" for t in result.trace)
