---
status: done
updated: 2026-08-10
depends_on: [0001]
decision: 0001
---

# 0007 — LLM client (OpenAI-compatible + mock)

## Goal
Introduce the model behind a small, provider-agnostic interface the agent loop (0008) will drive: an
OpenAI-compatible client for real mode and a **deterministic mock provider that is the default** (so the
whole app runs with no API key). Both speak tool-calling. Every call reports token usage + an estimated
cost.

## Context
Governed by [decision 0001](../../decisions/0001-tech-stack.md) (OpenAI-compatible client, mock-default).
The mock reuses the curated `EXAMPLES` from [`app/corpus.py`](../0005-rag-corpus-seeding/) as its canned
NL→SQL map, so its SQL keeps passing the 0004 validator (same invariant). Tool schemas mirror the two
tools the agent exposes: `search_schema` (0006) and `run_sql` (0004 + execution, 0008).

## Plan
1. `app/prompts.py` — the system prompt (call `search_schema` → `run_sql`, single read-only SELECT, filter
   `deleted = 0`, answer in Spanish from results only, self-correct on error) + the `search_schema` /
   `run_sql` tool schemas + a canned general-answer string.
2. `app/llm.py` — `LlmResponse`/`ToolCall`/`Usage` value types; `LlmProvider` protocol; `MockProvider`
   (state machine over the message history: question → `search_schema` call → `run_sql` call → final
   answer; general questions answered directly) and `OpenAIProvider` (lazy `openai` SDK, tool-calling,
   usage→cost); `get_llm()` factory (mock by default).
3. `app/config.py` — add `llm_price_input_per_1m` / `llm_price_output_per_1m` for cost estimation.
4. `tests/test_llm.py` — the mock state machine; its `run_sql` SQL passes the validator; usage/cost;
   `get_llm()` default; tool-schema shape.

## Done when
- [x] `get_llm()` returns the mock provider by default (no key needed); `OpenAIProvider` selected when
      `LLM_MODE=openai`.
- [x] The mock drives a full turn sequence (search_schema → run_sql → answer) purely from message history,
      and answers general questions directly (verified live).
- [x] The mock's `run_sql` SQL passes `validate_read_only` (cross-module invariant, tested).
- [x] Every response carries token counts + an estimated cost; unit gates green (85); `openai` lazy.

---
Log → [`discussion.md`](discussion.md)
