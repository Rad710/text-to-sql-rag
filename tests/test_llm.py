"""Tests for the LLM client: the mock state machine, invariants, usage, and the factory."""

from __future__ import annotations

import json
from typing import Any

from app.config import Settings
from app.llm import (
    MockProvider,
    OpenAIProvider,
    Usage,
    _estimate_cost,
    get_llm,
)
from app.prompts import SYSTEM_PROMPT, TOOLS
from app.validator import validate_read_only

SYS: dict[str, Any] = {"role": "system", "content": SYSTEM_PROMPT}
mock = MockProvider()


def _user(text: str) -> dict[str, Any]:
    return {"role": "user", "content": text}


def _assistant_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "x",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
        ],
    }


def _tool_result(content: str) -> dict[str, Any]:
    return {"role": "tool", "tool_call_id": "x", "content": content}


def test_first_turn_calls_search_schema() -> None:
    r = mock.complete([SYS, _user("total revenue per route")], TOOLS)
    assert r.content is None
    assert [tc.name for tc in r.tool_calls] == ["search_schema"]
    assert r.tool_calls[0].arguments["question"]


def test_second_turn_calls_run_sql_with_valid_sql() -> None:
    messages = [
        SYS,
        _user("total freight revenue per route"),
        _assistant_call("search_schema", {"question": "..."}),
        _tool_result("(schema context)"),
    ]
    r = mock.complete(messages, TOOLS)
    assert [tc.name for tc in r.tool_calls] == ["run_sql"]
    # cross-module invariant: the mock's SQL is a valid read-only SELECT.
    validate_read_only(r.tool_calls[0].arguments["query"])


def test_third_turn_returns_final_answer() -> None:
    messages = [
        SYS,
        _user("total revenue per route"),
        _assistant_call("search_schema", {"question": "x"}),
        _tool_result("ctx"),
        _assistant_call("run_sql", {"query": "SELECT 1"}),
        _tool_result("route | revenue\nAsuncion->CDE | 100"),
    ]
    r = mock.complete(messages, TOOLS)
    assert r.tool_calls == []
    assert r.content is not None and "100" in r.content


def test_general_question_answered_directly() -> None:
    r = mock.complete([SYS, _user("hola, como estas")], TOOLS)
    assert r.tool_calls == []
    assert r.content


def test_usage_is_reported() -> None:
    r = mock.complete([SYS, _user("total revenue per route")], TOOLS)
    assert r.usage.prompt_tokens > 0
    assert r.usage.total_tokens >= r.usage.prompt_tokens


def test_cost_estimate_from_prices() -> None:
    s = Settings(llm_price_input_per_1m=1.0, llm_price_output_per_1m=2.0)
    assert _estimate_cost(1_000_000, 500_000, s) == 2.0  # 1.0 input + 1.0 output


def test_usage_adds() -> None:
    total = Usage(10, 5, 0.1) + Usage(1, 2, 0.2)
    assert (total.prompt_tokens, total.completion_tokens) == (11, 7)
    assert abs(total.cost_usd - 0.3) < 1e-9


def test_get_llm_default_is_mock() -> None:
    assert isinstance(get_llm(Settings()), MockProvider)


def test_get_llm_openai_mode() -> None:
    assert isinstance(get_llm(Settings(llm_mode="openai")), OpenAIProvider)


def test_tool_schemas_shape() -> None:
    assert {t["function"]["name"] for t in TOOLS} == {"search_schema", "run_sql"}
