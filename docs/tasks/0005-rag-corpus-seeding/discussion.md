# 0005 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: ChromaDB 1.5.9 probed — using **precomputed embeddings** (`embedding_function=None`, pass
  `embeddings=` on add/query) sidesteps Chroma's default ONNX embedder entirely, so nothing downloads a
  model. Telemetry disabled via `Settings(anonymized_telemetry=False)`.
- 2026-08-10: Real (sentence-transformers) embedder deferred — the offline hashing embedder is the default
  and mock mode is the default, so a real model isn't needed yet; `get_embedder()` is the extension point
  for when real LLM mode lands. Cross-module invariant added: every curated EXAMPLE SQL must pass the 0004
  validator (mirrors the reference repos' "canned SQL is valid" test).
- 2026-08-10: Built + verified. `OfflineEmbedder` (feature-hashing, L2-normalized) is pure; `RagStore`
  syncs via content-hash id diffing (add new / prune removed / skip unchanged). Chroma engine tests run
  in-process in a tmp dir (~1s, no MySQL). 66 unit + a live-schema integration test (introspect 7 tables →
  seed → query) = 76 total. Chroma line-length wrapping was the only friction. Done.
