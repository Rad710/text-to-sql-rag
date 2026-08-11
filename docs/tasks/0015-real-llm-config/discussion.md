# 0015 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Task opened. Follows the owner's deploy answer: the app will be served in two flavors —
  **mock-only** and **real-LLM with request limits** — "both should be prepared", and the full app will be
  tested locally against **Ollama or vLLM**. This task prepares the real-LLM path (config + docs +
  verification); rate limiting + the deploy-mode switch are task 0022. Mock stays the default (no key).
- 2026-08-11: **Done — the wiring already existed.** `Settings` (`llm_base_url` / `llm_api_key` /
  `llm_model`, all env-driven) and `OpenAIProvider._get_client()` (passes `base_url` + `api_key` into the
  lazy `openai.OpenAI(...)`) were implemented back in task 0007, so this task was: (1) a unit test proving
  the client is built with the configured `base_url`/`api_key` (Ollama example) plus a model-passthrough
  assertion; (2) a README **"Using a real model (Ollama / vLLM)"** section with copy-paste env commands;
  (3) fixed a stale `uvicorn app.main:app` → `app.api:app` in the README quickstart. `.env.example` is
  sandbox-protected (denied), so the env vars are documented in the README instead. 100 tests green.
  Live smoke against a real model is the owner's to run.
