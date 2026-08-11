---
status: done
updated: 2026-08-11
depends_on: [0007, 0009]
---

# 0015 — Real-LLM config (Ollama / vLLM), mock stays default

## Goal
Let the app run against a **real** OpenAI-compatible model server — a local **Ollama** or **vLLM** — via
environment config, while the deterministic **mock provider stays the default** (zero-setup, no key). This
unblocks meaningful end-to-end testing (multi-turn, feedback) with a real model and the "real-LLM +
rate-limited" deploy flavor (see [decision 0005] deploy note; the two deploy modes the owner described).

## Context
`app/llm/client.py` already has an `OpenAIProvider` (lazy `openai` client) selected when `LLM_MODE=openai`.
Ollama and vLLM both expose an OpenAI-compatible `/v1` endpoint, so this is mostly **config + wiring +
docs + verification**, not new architecture. Ollama needs no real API key (a dummy is fine); vLLM may.
Keep the pure/impure split and mock-default (decisions 0001, 0007).

## Plan
1. **Config** (`app/config.py`): ensure `Settings` exposes `llm_mode`, `llm_base_url`, `llm_model`,
   `llm_api_key` (env-driven; sensible defaults). Add `llm_base_url` if missing.
2. **Client** (`app/llm/client.py`): pass `base_url` (and optional `api_key`) into the lazy `OpenAI(...)`
   construction; tolerate a missing/dummy key for Ollama.
3. **Docs**: `.env.example` + README — how to run against Ollama (`ollama serve` + `ollama pull <model>`)
   and vLLM (OpenAI-compatible server), setting `LLM_MODE=openai`, `LLM_BASE_URL`, `LLM_MODEL`.
4. **Test**: a unit test that `OpenAIProvider` is built with `base_url`/`model` from `Settings` (no network,
   inject a fake client as the existing tests do).

## Done when
- [x] `Settings` exposes `llm_base_url` (+ `llm_model`, `llm_api_key`); `OpenAIProvider` passes them into
      the client — **already wired in task 0007**; this task verified it.
- [x] README documents the Ollama and vLLM setups; mock remains the default with no key. (`.env.example`
      is sandbox-protected here, so the env vars are documented in the README; config already reads them.)
- [x] Unit test covers the `base_url`/model wiring (`test_openai_client_points_at_configured_endpoint` +
      a model assertion); `ruff`/`mypy`/`pytest` green (100 tests).
- [x] Committed.

> **Owner smoke-test (not a task deliverable):** a live end-to-end run against a real Ollama/vLLM is the
> owner's to do (no model server in this environment). The OpenAI-compatible path is the standard one and
> is unit-verified; if the live run surfaces anything, reopen.

---
Log → [`discussion.md`](discussion.md)
