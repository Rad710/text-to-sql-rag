---
status: done
updated: 2026-08-10
depends_on: [0005]
decision: null
---

# 0006 — Retrieval engine (4-tier merge → search_schema)

## Goal
Turn the seeded corpus into the `search_schema(question)` tool the agent calls: pick the relevant tables
via a 4-tier priority merge, then assemble the context (full DDL for the top tables + compact summaries for
the rest + business-rule docs + few-shot examples). This is the RAG payoff — the best pattern from `his_ai`,
including **relationship-following**.

## Context
Builds on the store from [0005](../0005-rag-corpus-seeding/) and the pure renderers from
[0003](../0003-schema-introspection/). See [`../../architecture.md`](../../architecture.md) (RAG section).
Keep the merge pure; keep the Chroma queries + assembly on `RagStore`.

## Plan
1. `app/retrieval.py` — **pure**: `extract_tables_from_sql` (sqlglot), `keyword_tables`,
   `follow_relationships` (via `SchemaInfo.join_partners`), `merge_candidates` (priority: P1 semantic →
   P2 example → P3 relationship → P4 keyword; highest-priority source wins ties), and `RetrievedContext`
   with `as_prompt()`.
2. `app/engine.py` — add `RagStore.search_schema(question, schema, …)`: query the three collections, run
   the pure merge, render full DDL for the top-N tables + summaries for the rest, return a
   `RetrievedContext`.
3. `tests/test_retrieval.py` — pure: table extraction, keyword match, relationship-following, merge order +
   tie-breaking, `as_prompt` shape.
4. `tests/test_search.py` — Chroma-backed (temp dir, hand schema): `search_schema` returns relevant tables,
   two-tier presentation (full DDL vs summaries), examples/docs included; + a live-schema integration test.

## Done when
- [x] The 4 tiers each work in isolation (pure unit tests) and merge with correct priority + tie-breaking
      (6 tests in `test_retrieval.py`).
- [x] `search_schema` returns a `RetrievedContext` whose top tables are relevant and whose `as_prompt()`
      carries full DDL + summaries + docs + examples (verified live: `route`/`shipment` surface for
      "revenue per route", two-tier presentation confirmed).
- [x] Relationship-following pulls a joined table the query didn't name directly (tested: `driver` appears
      for "revenue by shipment").
- [x] Unit gates green (75); live-schema integration test passes (11 integration total).

---
Log → [`discussion.md`](discussion.md)
