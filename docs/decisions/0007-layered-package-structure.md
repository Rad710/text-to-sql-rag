---
status: accepted
date: 2026-08-11
---

# 0007 — Group `app/` into layered sub-packages by concern

## Context
`app/` was a flat package of 14 single-concern modules. That is idiomatic Python at this size and not
in itself wrong, but the architecture — SQL safety, the RAG pipeline, the LLM client, the agent that
composes them — was not visible from the layout. For a portfolio codebase where the structure is part
of the signal, the layering should be legible at a glance.

## Decision
We will group the modules into sub-packages by architectural concern, keeping the composition root and
cross-cutting config at the top level:

```
app/
  safety/   validator.py  limits.py  execution.py      # SQL guardrails (decision 0003)
  rag/      schema.py  introspect.py  corpus.py         # retrieval-augmented schema grounding
            embeddings.py  engine.py  retrieval.py
  llm/      client.py (the provider)  prompts.py        # __init__.py is an empty package marker
  agent.py  api.py  config.py                            # orchestration · HTTP/SSE · shared config
```

Imports are updated to the new paths explicitly (no re-export shims): the provider is
`app.llm.client`, not code hidden in `__init__.py`. The pure/impure split and lazy-I/O convention
(CLAUDE.md) are unaffected — only file locations change.

## Consequences
- Good: the layering reads as architecture; related modules sit together; import paths state which
  layer a dependency comes from (`app.safety.validator`, `app.rag.engine`).
- Bad / cost: a wide, mechanical import churn across `app/`, `tests/`, `evaluation/`; git history for
  moved files follows the rename. `app.api:app` (uvicorn/compose entrypoint) is unchanged.

## Alternatives considered
- **Keep the flat layout** — defensible at this size, but leaves the architecture implicit; rejected for
  a codebase meant to showcase design.
- **Re-export everything from `app/__init__.py` to keep old paths** — hides the structure behind import
  shims; rejected as the kind of indirection this record is meant to remove.
