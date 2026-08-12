"""Tests for the LLM client: the mock state machine, invariants, usage, and the factory."""

from __future__ import annotations

import json
from types import SimpleNamespace as NS
from typing import Any
from unittest.mock import patch

import openai

from app.config import Settings
from app.llm.client import (
    MockProvider,
    OpenAIProvider,
    Usage,
    _detect_lang,
    _estimate_cost,
    get_llm,
)
from app.llm.prompts import SYSTEM_PROMPT, TOOLS
from app.safety.validator import validate_read_only

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
    # After both tools ran, the mock returns a final prose answer (the result table is rendered
    # by the frontend from the structured tool_result, not echoed here — decision 0006).
    assert r.content is not None and "queried the database" in r.content


def test_general_question_answered_directly() -> None:
    r = mock.complete([SYS, _user("hola, como estas")], TOOLS)
    assert r.tool_calls == []
    assert r.content


def test_mock_keys_off_the_latest_user_turn() -> None:
    """Multi-turn (task 0016): the mock answers the *latest* question, not the first."""
    messages = [
        SYS,
        _user("hola, como estas"),
        {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"},
        _user("total revenue per route"),
    ]
    r = mock.complete(messages, TOOLS)
    assert [tc.name for tc in r.tool_calls] == ["search_schema"]  # the DB question, not "hola"


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


# --- OpenAIProvider: fake the client to test request-building + response-parsing (no network) ---


def _fake_response(
    content: str | None, tool_calls: list[tuple[str, str, str]], pt: int, ct: int
) -> Any:
    calls = [NS(id=i, function=NS(name=n, arguments=a)) for i, n, a in tool_calls]
    message = NS(content=content, tool_calls=calls or None)
    return NS(choices=[NS(message=message)], usage=NS(prompt_tokens=pt, completion_tokens=ct))


class _FakeClient:
    def __init__(self, response: Any) -> None:
        self.captured: dict[str, Any] = {}

        def create(**kwargs: Any) -> Any:
            self.captured = kwargs
            return response

        completions = type("C", (), {"create": staticmethod(create)})
        self.chat = type("Chat", (), {"completions": completions})


def test_openai_provider_parses_tool_calls_and_cost() -> None:
    settings = Settings(llm_mode="openai", llm_price_input_per_1m=1.0, llm_price_output_per_1m=2.0)
    provider = OpenAIProvider(settings)
    fake = _FakeClient(_fake_response(None, [("id1", "run_sql", '{"query": "SELECT 1"}')], 100, 50))
    provider._client = fake  # inject the fake client

    resp = provider.complete([{"role": "user", "content": "x"}], TOOLS)

    assert [tc.name for tc in resp.tool_calls] == ["run_sql"]
    assert resp.tool_calls[0].arguments == {"query": "SELECT 1"}
    assert resp.usage.prompt_tokens == 100 and resp.usage.completion_tokens == 50
    assert resp.usage.cost_usd == 100 / 1_000_000 * 1.0 + 50 / 1_000_000 * 2.0
    # tools + the configured model were passed through to the API call
    assert fake.captured["tools"] == TOOLS
    assert fake.captured["tool_choice"] == "auto"
    assert fake.captured["model"] == "gpt-4o-mini"


def test_openai_provider_parses_plain_content() -> None:
    provider = OpenAIProvider(Settings(llm_mode="openai"))
    provider._client = _FakeClient(_fake_response("hello", [], 10, 5))
    resp = provider.complete([{"role": "user", "content": "x"}], None)
    assert resp.content == "hello"
    assert resp.tool_calls == []


def test_openai_client_points_at_configured_endpoint() -> None:
    """Built with the configured base_url/api_key — so it can target a local Ollama or vLLM
    server (task 0015), not just api.openai.com."""
    settings = Settings(
        llm_mode="openai",
        llm_base_url="http://localhost:11434/v1",  # e.g. Ollama
        llm_api_key="ollama",
    )
    provider = OpenAIProvider(settings)
    with patch.object(openai, "OpenAI") as make_client:
        provider._get_client()
    make_client.assert_called_once_with(base_url="http://localhost:11434/v1", api_key="ollama")


def test_tool_schemas_shape() -> None:
    assert {t["function"]["name"] for t in TOOLS} == {"search_schema", "run_sql"}


def test_detect_language() -> None:
    assert _detect_lang("facturación total por ruta") == "es"
    assert _detect_lang("how many shipments per driver") == "en"
    assert _detect_lang("planillas sin cobrar y su total pendiente") == "es"


def test_spanish_db_question_enters_tool_path() -> None:
    r = mock.complete([SYS, _user("planillas sin cobrar y su total pendiente")], TOOLS)
    assert [tc.name for tc in r.tool_calls] == ["search_schema"]


def test_answer_language_matches_question() -> None:
    def convo(q: str) -> list[dict[str, Any]]:
        return [
            SYS,
            _user(q),
            _assistant_call("search_schema", {"question": q}),
            _tool_result("ctx"),
            _assistant_call("run_sql", {"query": "SELECT 1"}),
            _tool_result("rows"),
        ]

    es = mock.complete(convo("facturación total por ruta"), TOOLS).content
    en = mock.complete(convo("total freight revenue per route"), TOOLS).content
    assert es is not None and es.startswith("Consulté")
    assert en is not None and en.startswith("I queried")
