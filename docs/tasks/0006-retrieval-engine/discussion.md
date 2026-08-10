# 0006 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Merge is a **priority append** (iterate sources P1→P4, append each unseen table) rather than a
  score-sort — deterministic, and "highest-priority source wins ties" falls out naturally (a table is
  attributed to the first tier that yields it). Semantic hits are passed nearest-first so within-tier order
  is similarity order. DDL for chosen tables is rendered fresh from the live `SchemaInfo` (authoritative),
  not read back from the Chroma documents — the ddl collection is only used to *rank* tables semantically.
- 2026-08-10: Built + verified. `app/retrieval.py` holds the pure tiers + `RetrievedContext.as_prompt()`;
  `RagStore.search_schema()` orchestrates the Chroma queries + merge + two-tier rendering. Live check on the
  7-table schema: "revenue per route" → top tables led by `route`/`shipment`, `driver` shown as a summary,
  prompt carries annotated DDL + docs + few-shots. 9 new unit + 1 integration test. Stopword list built by
  splitting a named string (dodges SIM905 + keeps it compact). Done.
