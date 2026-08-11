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
- 2026-08-11: **Stage B — frontend (done).** `conversation.ts` (module-level active-id + a listener the
  adapter fires on the `conversation` event), `history.ts` (authenticated `listConversations` /
  `getConversationMessages`), `ConversationList.tsx` (sidebar: list + "new chat"). `runtime.ts` now sends
  `conversation_id` and calls `notifyConversation` on the event. `App.tsx` restructured: a sidebar + a
  `ChatPane` keyed so switching conversations remounts a fresh `useLocalRuntime(adapter, { initialMessages })`
  seeded from the loaded messages; the listener highlights + refreshes the list without remounting mid-turn.
  Browser QA caught a real bug — `/conversations` was missing from the Vite dev proxy (frontend got the SPA
  HTML → JSON parse error); added it. Verified via Playwright: ask → conversation appears in the sidebar →
  new chat → ask again (2 convos) → click the first → its messages reload. 0 console errors. Note: reload
  restores the prose exchange (persisted role+content), not the ephemeral tool-step/table render.
