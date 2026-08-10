---
status: accepted
date: 2026-08-10
---

# 0001 — Python/FastAPI + MySQL + ChromaDB + OpenAI-compatible client, mock-default

## Context
A public, recruiter-facing text-to-SQL RAG demo over the DYR Transportes freight schema. It must run for a
reviewer with **zero setup and no API key or GPU**, yet still demonstrate a real LLM integration. The real
DYR Transportes backend is Python/Flask on MySQL; two private reference implementations use Chainlit +
ChromaDB + an OpenAI-compatible vLLM backend.

## Decision
We will build a **FastAPI** service (Python 3.12) with a thin static HTML/JS chat page. Retrieval uses
**ChromaDB** (embedded). The LLM is accessed through the **`openai` SDK against any OpenAI-compatible
endpoint**, with a **deterministic mock provider as the default** so the app runs with no key. The query
target is a **synthetic MySQL 8** database (Alembic migrations) mirroring the real DYR Transportes schema.

## Consequences
- Good: runs instantly in mock mode; MySQL stays faithful to the real project and shows MySQL fluency; the
  OpenAI-compatible client works with cloud or self-hosted models; FastAPI gives clean async + OpenAPI docs.
- Good: mock-default keeps CI fast and dependency-light (heavy deps lazily imported).
- Bad / cost: MySQL's read-only story is grant-based (no Postgres `REVOKE CREATE` role); we compensate with
  a strict `SELECT`-only user (see [0003](0003-sql-safety-defense-in-depth.md)). ChromaDB adds an embedding
  dependency for real retrieval (offline hashing embedder used in mock/CI).

## Alternatives considered
- **PostgreSQL query target** — cleaner read-only role, matches the references; rejected to stay faithful to
  the real MySQL-based DYR Transportes project.
- **Chainlit UI** (as in the references) — great chat UX but heavier and less "I built the stack" signal;
  rejected in favour of FastAPI + a thin static page.
- **Anthropic-only client** — excellent quality but ties the demo to one vendor; the OpenAI-compatible
  client is more portable (and still points at any hosted model).
