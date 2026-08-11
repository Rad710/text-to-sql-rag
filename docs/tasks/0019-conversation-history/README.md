---
status: in-progress
updated: 2026-08-11
depends_on: [0016, 0017]
---

# 0019 — Conversation history + persistence

## Goal
Persist conversations and messages per user (Postgres store, 0017) and let the user **reload** past
conversations — a thread-list sidebar + "new chat". Builds on multi-turn (0016) and auth (0018).

## Context
`/chat` is currently stateless. Now each turn is saved to the `conversations`/`messages` tables owned by
the authenticated user, so the SPA can list and reopen them. The **agent's context** still comes from the
client-sent `history` (0016); persistence is for reload. The store is async and the agent's `stream()` is
sync — resolve by making `/chat` an **async endpoint with an async generator** that iterates the sync
stream and `await`s the DB writes around it.

## Plan
**Stage A — backend** (this commit): `ChatRequest.conversation_id?`; `/chat` becomes async — resolve/
create the user's conversation, persist the user message, stream (emitting a `conversation` event with the
id), and persist the assistant answer when the stream ends. A `conversations` service + router:
`GET /conversations` (the user's list) and `GET /conversations/{id}` (its messages, 404 if not owned).
Integration tests (chat persists → list → load).
**Stage B — frontend** (next commit): a thread-list sidebar (list + select + new chat) that loads a
conversation's messages into the thread and threads the `conversation_id` on subsequent turns; tests +
browser verification.

## Done when
- [ ] `/chat` persists the user + assistant messages under the user's conversation and emits its id;
      `GET /conversations` and `GET /conversations/{id}` return the user's data (and 404 across users).
- [ ] Integration tests (chat → persisted → listed → loaded) green; `ruff`/`mypy`/`pytest` green.
- [ ] Thread-list UI: list, open a past conversation (messages reload), new chat; tests + browser-verified.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
