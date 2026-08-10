---
status: accepted
date: 2026-08-10
---

# 0005 — Custom FastAPI SSE API + Vite/React/TS frontend (assistant-ui), not a chat framework

## Context
The interface must showcase **software-engineering** skill — API design, streaming, and a real frontend —
and must stand apart from the reference implementations (which both use Chainlit). Batteries-included chat
frameworks (Chainlit/Streamlit/Gradio) hide exactly that: they provide the server, the streaming, and the
UI, so they signal a data-science/prototyping role rather than "engineer who ships a product," and they
make our repo look like the reference repos. We already work in **React + Vite + TypeScript** (the
`dyrtransportes_react` project), so a custom frontend is low-risk and plays to existing skills. This amends
the UI half of [decision 0001](0001-tech-stack.md) (which proposed a thin static page).

## Decision
We will build **our own** interface in two parts:

- **Backend:** a **FastAPI** app that runs the agent and **streams its events over SSE** (tool start →
  generated SQL → rows → answer tokens → usage/cost → done), plus `/health`. We own the API and the
  streaming protocol.
- **Frontend:** a **Vite + React + TypeScript** SPA using **assistant-ui** (agent-chat components:
  streaming, tool-call rendering, token/cost) to render the conversation and the generated SQL as
  collapsible steps. assistant-ui is *frontend components only* — the API and streaming remain ours.

## Consequences
- Good: full-stack SWE signal (API + SSE streaming + frontend), differentiated from the reference repos,
  reuses our React/TS skills, polished (assistant-ui) without hand-rolling CSS.
- Bad / cost: a second (Node/TS) build pipeline and more work than a framework; the agent loop must be
  refactored to **emit events** (a streaming generator alongside the existing sync `answer_question`); the
  project only pays off if it is **deployed live**, so deployment becomes a first-class task.

## Alternatives considered
- **Chainlit / Streamlit / Gradio** — fastest and polished, but hide the API/streaming/frontend, signal a
  data-science role, and look like the reference repos. Rejected.
- **Next.js** — it is its own backend (API routes / server components), so pairing it with our FastAPI
  duplicates the backend and undercuts the "I built the API" signal. Rejected in favour of a Vite SPA.
- **Hand-rolled HTML/CSS** — attempted; unpolished. Rejected.
- **Vercel AI SDK template** — documented friction streaming its tool-step (data) protocol from a FastAPI
  (non-Node) backend. Rejected.
