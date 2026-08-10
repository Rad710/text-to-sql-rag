---
status: done
updated: 2026-08-10
depends_on: [0003]
decision: null
---

# 0005 — RAG corpus + idempotent ChromaDB seeding

## Goal
Build the retrieval corpus and load it into ChromaDB so the `search_schema` tool (0006) has something to
search: the introspected DDL (0003) + hand-written business-rule docs + curated NL→SQL example pairs, seeded
**idempotently** (content-hashed IDs — unchanged items skipped, removed items pruned). Runs fully offline
(a deterministic hashing embedder — no model download, no network).

## Context
See [`../../architecture.md`](../../architecture.md) (RAG section) and [`../../reference.md`](../../reference.md)
(business rules + canonical questions). Reuses `app.schema` renderers (0003). ChromaDB is used with
**precomputed embeddings** (`embedding_function=None`) so no ONNX model is ever downloaded.

## Plan
1. `app/embeddings.py` — pure `OfflineEmbedder` (deterministic feature-hashing of words + char trigrams,
   L2-normalized) + an `Embedder` protocol + `get_embedder()`.
2. `app/corpus.py` — `CorpusItem` (content-hash `id`), static `DOCS` (business rules) + `EXAMPLES` (NL→SQL),
   and `build_corpus(schema)` combining DDL items with them.
3. `app/engine.py` — `RagStore`: lazy ChromaDB `PersistentClient` (telemetry off), 3 collections
   (`ddl`/`documentation`/`question_sql`), `sync_corpus()` (add new, prune removed, skip unchanged), and a
   low-level `query()`.
4. Tests: `test_embeddings.py` (determinism/dim/normalized/related-closer), `test_corpus.py` (stable IDs +
   **every EXAMPLE SQL passes `validate_read_only`**), `test_engine.py` (chroma in a tmp dir: sync counts,
   idempotent re-sync, prune, query relevance).

## Done when
- [x] `build_corpus(schema)` yields DDL + doc + example items with stable content-hash IDs.
- [x] Every curated EXAMPLE SQL passes the 0004 validator (cross-module invariant, tested).
- [x] `RagStore.sync_corpus()` is idempotent (re-sync adds/deletes nothing) and prunes removed items.
- [x] Runs offline (no model download — precomputed embeddings); unit gates green (66); heavy deps
      lazily imported. Live-pipeline integration test seeds from the real 7-table schema (76 total).

---
Log → [`discussion.md`](discussion.md)
