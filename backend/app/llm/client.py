"""The LLM client: a provider-agnostic tool-calling interface.

Two providers behind one protocol. ``MockProvider`` (the default) is deterministic and needs no key
or network — it drives the full agent loop by inspecting the message history. ``OpenAIProvider``
talks to any OpenAI-compatible endpoint. Every call returns token usage + an estimated cost.

Messages are plain OpenAI-format dicts (the lingua franca) — ``{"role": "user"|"assistant"|"tool"|
"system", ...}``. The real provider passes them straight through; the mock reads them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from app.config import Settings, get_settings
from app.llm.prompts import GENERAL_ANSWER_EN, GENERAL_ANSWER_ES
from app.rag.corpus import EXAMPLES

_TOKEN_RE = re.compile(r"[a-z0-9_]+")

# Non-accented language markers (accented text is detected directly). Ambiguous words are omitted.
_ES_WORD_TEXT = (
    "chofer choferes ruta rutas planillas planilla gastos gasto viajes viaje liquidaciones recibo "
    "recibos peso producto productos mes cada por con sin del ingresos impagas pendiente cobrar "
    "facturacion"
)
_EN_WORD_TEXT = (
    "how many much route routes driver drivers revenue shipments shipment billing expenses expense "
    "receipt weight product products month monthly freight unpaid pending payrolls settlements "
    "split"
)
_ES_WORDS = frozenset(_ES_WORD_TEXT.split())
_EN_WORDS = frozenset(_EN_WORD_TEXT.split())

# Prose only — the result table is rendered by the frontend from the structured tool_result
# (decision 0006), so the mock answer no longer embeds it.
_ANSWER_PROSE = {
    "es": "Consulté la base de datos y ejecuté la consulta SQL para responder tu pregunta.",
    "en": "I queried the database and ran the SQL to answer your question.",
}
_GENERAL_ANSWER = {"es": GENERAL_ANSWER_ES, "en": GENERAL_ANSWER_EN}


def _detect_lang(text: str) -> str:
    lowered = text.lower()
    if any(ch in lowered for ch in "áéíóúñ¿¡"):
        return "es"
    tokens = set(_TOKEN_RE.findall(lowered))
    es_hits, en_hits = len(tokens & _ES_WORDS), len(tokens & _EN_WORDS)
    if es_hits == 0 and en_hits == 0:
        return "es"  # domain default
    return "es" if es_hits >= en_hits else "en"


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
        )


ZERO_USAGE = Usage(prompt_tokens=0, completion_tokens=0, cost_usd=0.0)


@dataclass(frozen=True, slots=True)
class LlmResponse:
    content: str | None
    tool_calls: list[ToolCall]
    usage: Usage


class LlmProvider(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        language: str | None = None,
    ) -> LlmResponse: ...


def _estimate_cost(prompt_tokens: int, completion_tokens: int, settings: Settings) -> float:
    return (
        prompt_tokens / 1_000_000 * settings.llm_price_input_per_1m
        + completion_tokens / 1_000_000 * settings.llm_price_output_per_1m
    )


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _match_example(question: str) -> tuple[str, int]:
    """Best-matching curated example SQL for ``question`` (by shared-token count) and its score."""
    q_tokens = set(_tokens(question))
    best_sql, best_score = "", 0
    for example_q, sql in EXAMPLES:
        score = len(q_tokens & set(_tokens(example_q)))
        if score > best_score:
            best_sql, best_score = sql, score
    return best_sql, best_score


class MockProvider:
    """Deterministic provider: question → search_schema → run_sql → answer, from history alone."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        language: str | None = None,
    ) -> LlmResponse:
        settings = get_settings()
        question = _latest_user_message(messages)
        made = _tool_calls_made(messages)
        sql, score = _match_example(question)
        # The UI language (task 0040) wins when set; else detect it from the question.
        lang = language if language in ("es", "en") else _detect_lang(question)

        content: str | None
        tool_calls: list[ToolCall] = []

        if score == 0:
            # Not a recognizable database question — answer directly, in the question's language.
            content = _GENERAL_ANSWER[lang]
        elif "search_schema" not in made:
            content = None
            tool_calls = [ToolCall("call_search", "search_schema", {"question": question})]
        elif "run_sql" not in made:
            content = None
            tool_calls = [ToolCall("call_run", "run_sql", {"query": sql})]
        else:
            content = _ANSWER_PROSE[lang]

        prompt_tokens = max(1, sum(len(str(m.get("content") or "")) for m in messages) // 4)
        completion_tokens = (len(content) // 4 if content else 0) + (20 if tool_calls else 0)
        cost = _estimate_cost(prompt_tokens, completion_tokens, settings)
        usage = Usage(prompt_tokens, completion_tokens, cost)
        return LlmResponse(content=content, tool_calls=tool_calls, usage=usage)


# --- Markdown tool protocol (used by OpenAIProvider) -------------------------------------------
# Local models are far more reliable emitting a fenced code block than JSON function-call args, so
# we drive the loop as a plain-text transcript: the model replies with one ```sql / ```schema block
# (or prose = final answer), and we translate to/from the agent loop's function-call shape here.
_FENCE_RE = re.compile(r"```([A-Za-z_]*)[^\n]*\n(.*?)```", re.DOTALL)


def _parse_action(content: str) -> tuple[list[ToolCall], str | None]:
    """A fenced `sql`/`schema` block → the matching ToolCall; otherwise the text is the answer."""
    match = _FENCE_RE.search(content or "")
    if match:
        lang, body = match.group(1).lower(), match.group(2).strip()
        if lang == "sql" or (not lang and re.match(r"(?is)\s*(select|with)\b", body)):
            return [ToolCall("call_run", "run_sql", {"query": body})], None
        if lang in ("schema", "search", "search_schema"):
            return [ToolCall("call_search", "search_schema", {"question": body})], None
    return [], (content or None)


def _render_history_as_text(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Rewrite the function-call messages as a plain transcript: past tool calls become the fenced
    blocks the model would have written; tool results come back as a `Result:` user turn."""
    out: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role"))
        if role == "assistant" and message.get("tool_calls"):
            blocks: list[str] = []
            for call in message["tool_calls"]:
                fn = call.get("function", {})
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                if fn.get("name") == "run_sql":
                    blocks.append(f"```sql\n{args.get('query') or args.get('sql') or ''}\n```")
                elif fn.get("name") == "search_schema":
                    blocks.append(f"```schema\n{args.get('question') or ''}\n```")
            out.append({"role": "assistant", "content": "\n".join(blocks)})
        elif role == "tool":
            out.append({"role": "user", "content": f"Result:\n{message.get('content') or ''}"})
        else:
            out.append({"role": role, "content": str(message.get("content") or "")})
    return out


class OpenAIProvider:
    """Any OpenAI-compatible endpoint, driven with the markdown tool protocol (no JSON calls)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self._settings.llm_base_url, api_key=self._settings.llm_api_key
            )
        return self._client

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        language: str | None = None,
    ) -> LlmResponse:
        # `tools`/`language` unused here: we prompt a fenced-block protocol instead of JSON
        # function-calling, and the answer-language directive is already in the system prompt.
        response = self._get_client().chat.completions.create(
            model=self._settings.llm_model, messages=_render_history_as_text(messages)
        )
        message = response.choices[0].message
        tool_calls, content = _parse_action(message.content or "")

        usage = response.usage
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        return LlmResponse(
            content=content,
            tool_calls=tool_calls,
            usage=Usage(
                prompt_tokens,
                completion_tokens,
                _estimate_cost(prompt_tokens, completion_tokens, self._settings),
            ),
        )


def get_llm(settings: Settings | None = None) -> LlmProvider:
    """Return the configured provider — the deterministic mock by default (no key needed)."""
    resolved = settings or get_settings()
    return OpenAIProvider(resolved) if resolved.llm_mode == "openai" else MockProvider()


def _latest_user_message(messages: list[dict[str, Any]]) -> str:
    """The current question — the last user turn (multi-turn: not the first). Task 0016."""
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def _tool_calls_made(messages: list[dict[str, Any]]) -> set[str]:
    made: set[str] = set()
    for message in messages:
        if message.get("role") == "assistant":
            for call in message.get("tool_calls") or []:
                name = call.get("function", {}).get("name")
                if name:
                    made.add(name)
    return made
