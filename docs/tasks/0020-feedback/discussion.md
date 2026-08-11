# 0020 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Opened. Feedback FKs a persisted assistant message, so the id must reach the client: `/chat`
  emits a `message` event with the saved assistant id, and `GET /conversations/{id}` includes message ids.
  `set_feedback` upserts one rating per message, owner-checked through message→conversation→user.
- 2026-08-11: **Stage A — backend (done).** `save_message` now returns the new id; the recorder's
  `finish` returns the assistant message id; `/chat` emits a `message` event carrying it. Added
  `set_feedback` (owner-checked via message→conversation→user, upsert one-per-message) + a `feedback_router`
  (`POST /feedback` with `rating: Literal[-1, 1]` → 422 on anything else). `GET /conversations/{id}` messages
  now include `id`. Integration (in `test_conversations.py`): rate → 204, re-rate → 204 (upsert), other
  user → 404, bad rating → 422. 112 unit + integration green; mypy strict clean.
