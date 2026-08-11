---
status: done
updated: 2026-08-11
depends_on: [0017, 0010]
---

# 0020 — Feedback 👍/👎 (persisted)

## Goal
Let users rate an answer 👍/👎; persist it to the `feedback` table (0017), one per message. This is the
signal the "few-shot curation from a feedback table" backlog idea would later promote to the corpus.

## Context
Feedback attaches to a persisted **assistant message** (`feedback.message_id`). So `/chat` must surface
the assistant message's id (a `message` SSE event after it's saved), and `GET /conversations/{id}` must
include message ids, so the SPA can target either a live or a reloaded answer.

## Plan
**Stage A — backend** (this commit): `save_message` returns the new id; the recorder's `finish` returns
the assistant message id; `/chat` emits a `message` event carrying it. A `set_feedback` service
(owner-checked via message→conversation→user, upsert one-per-message) + `POST /feedback` (`{message_id,
rating: -1|1}`). `GET /conversations/{id}` messages gain `id`. Integration tests.
**Stage B — frontend** (next commit): 👍/👎 controls on assistant answers that POST `/feedback` for the
message id (from the `message` event, or a reloaded message's id); tests + browser verification.

## Done when
- [x] `POST /feedback` upserts one rating per message, owner-checked (404 across users, 422 on bad rating);
      `/chat` emits the assistant `message` id; `GET /conversations/{id}` includes message ids.
- [x] Integration tests green; `ruff`/`mypy`/`pytest` green.
- [x] 👍/👎 UI wired to `/feedback`; tests + browser-verified.
- [x] Committed.

---
Log → [`discussion.md`](discussion.md)
