---
status: accepted
date: 2026-08-10
---

# 0002 — Build the core as a hybrid-agentic tool-loop, not a fixed pipeline

## Context
Both private reference implementations use a **fixed pipeline** (`retrieve → generate → validate →
execute → format`) with no self-correction — on a SQL error they dead-end and ask the user to rephrase.
That is deterministic and testable, but rigid: it answers multi-step questions poorly and cannot recover
from its own mistakes. A more current design gives the model tools and lets it iterate.

## Decision
We will build the core as a **bounded agentic tool-calling loop**. The model is given two tools and loops
(capped at N steps) until it answers:

- `search_schema(question)` — RAG over DDL + business-rule docs + Q→SQL examples (ChromaDB). Retrieval
  becomes a **tool**, so "RAG" in the name stays honest.
- `run_sql(query)` — validate (sqlglot) → enforce `LIMIT` → execute read-only → return rows or the DB error.

The model calls `search_schema` to pull the tables it needs, drafts SQL, calls `run_sql`, and **reruns and
refines** on an error or odd result. Self-correction is native to the loop. All tools are **pure, unit-
tested functions**; the loop orchestration is thin. The full SQL-safety layer ([0003](0003-sql-safety-defense-in-depth.md))
is the guardrail on `run_sql`.

## Consequences
- Good: native rerun/self-correction; handles multi-step questions; stronger "builds agents" signal than a
  RAG pipeline; safety work is reused as tool guardrails; RAG remains central (as a tool).
- Bad / cost: less deterministic and more tokens/latency than a fixed pipeline; end-to-end testing is
  harder — mitigated by keeping tools pure + testing the loop against a mock provider with scripted tool
  calls, and by a hard max-iterations cap.

## Alternatives considered
- **Fixed pipeline + one-shot repair** — simpler and cheapest; rejected as the core because it under-sells
  the design and can't do multi-step. (Kept as the conceptual fallback; the pure tools would still work in
  a pipeline if we ever want a deterministic mode.)
- **Full open-ended agent (arbitrary tools, no cap)** — rejected: unbounded cost/latency and a larger
  safety surface for a demo.
