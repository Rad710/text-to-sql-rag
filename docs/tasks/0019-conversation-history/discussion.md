# 0019 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Opened. Key design point: the agent's `stream()` is sync but the store is async, so `/chat`
  becomes an **async endpoint** whose async generator iterates the sync stream and `await`s the DB writes
  (persist the user message before streaming; persist the assistant answer when the stream ends; emit a
  `conversation` event carrying the id). The agent's conversational context still comes from the
  client-sent `history` (0016) — persistence is for reload, not for feeding the model.
- 2026-08-11: **Stage A — backend (done).** `app/store/conversations.py` (resolve/create, save_message,
  list, get-with-messages + a `ConversationRecorder` seam) and `app/store/router.py` (`GET /conversations`,
  `GET /conversations/{id}`, 404 across users). `/chat` is now **async**: it resolves/saves the user turn
  via the injected recorder, emits a `conversation` event with the id, streams, then saves the assistant
  answer. The recorder is a FastAPI dependency so the DB-free `/chat` unit tests inject a no-op. Integration
  test (`test_conversations.py`, single-loop httpx): register two users → chat persists → `GET
  /conversations` lists it → `GET /conversations/{id}` returns the messages → the other user gets 404.
  112 unit + integration green; mypy strict clean.
