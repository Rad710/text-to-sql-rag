---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-13     # YYYY-MM-DD, last touched
depends_on: [0017, 0019]
decision: 0006          # governs why the table lives in the tool_result, not the prose
---

# 0041 — Reloaded conversations show the SQL and result table (persist tool steps)

## Goal
Opening an existing conversation should look like the turn did when it streamed live: the collapsible
`run_sql` step (with the SQL) and the structured result table. Today a reloaded conversation shows only
the assistant's prose — for the mock provider that's the content-free filler *"I queried the database
and ran the SQL to answer your question."* — so old conversations look empty/broken. The fix is to
**persist the tool calls and their structured results** alongside the prose, and rebuild the same
assistant-ui parts on reload.

## Context
Reproduced live on the deployed VM (2026-08-13) — see [`discussion.md`](discussion.md) for the trace.
The rich UI is built **only** from live SSE `tool_start` / `tool_result` events; none of that is saved:

- **Store schema** — `messages` holds only `role` + a plain-text `content` column
  (`backend/app/store/models.py:68`). There is nowhere to put tool calls or the structured `run_sql`
  rows.
- **`/chat`** captures only the `answer` event's text and persists that via `recorder.finish`
  (`backend/app/api.py:151-156`); `tool_start` / `tool_result` events are streamed to the browser and
  dropped for persistence.
- **Live rendering** turns those events into assistant-ui **tool-call parts**
  (`frontend/src/lib/runtime.ts:132-185`) — the SQL step + table (`RunSqlTool`).
- **Reload** maps a stored message as bare text, `content: m.content`
  (`frontend/src/pages/ChatPage.tsx:63`), so there are no tool-call parts to render.

Why it's starkest with the mock: [decision 0006](../../decisions/0006-structured-results-over-sse.md)
deliberately moved the table out of the answer prose into the structured `tool_result`, so the prose is
intentionally content-free (`backend/app/llm/client.py:40-43`). With the `tool_result` unsaved, a
reloaded mock turn has nothing meaningful left. This task **extends** 0006 (persist what it streams) and
builds on the datastore of [decision 0008](../../decisions/0008-app-datastore-postgres.md) /
tasks [0017](../0017-app-persistence-foundation/), [0019](../0019-conversation-history/).

**Open design choice** (decide first, in `discussion.md`): how to store the structured parts. Leading
option is a nullable JSON column on `messages` (simplest — one migration, reconstruct directly);
alternatives are a normalized `message_parts` table or replaying a stored raw event stream. Not chosen
yet — see `discussion.md` and confirm before building.

## Plan
Concrete, ordered. Live and reload should share **one** part-building mapping so they can't drift.

1. **Decide + record the persistence shape** (`discussion.md`; a short decision record if non-trivial):
   JSON column on `messages` vs. a `message_parts` table. Keep the security-critical layers untouched.
2. **Store schema + migration** — add the chosen field (e.g. a nullable `tool_data` JSON column) to
   `Message` in `backend/app/store/models.py`; generate the Alembic migration under `backend/alembic/`.
3. **Persist the steps** — capture `tool_start` / `tool_result` events in the `/chat` stream
   (`backend/app/api.py`) and pass them to the recorder; extend `save_message` / `ConversationRecorder`
   in `backend/app/store/conversations.py` to write the structured tool data with the assistant message.
4. **Return them on read** — include the tool data in `GET /conversations/{id}` (the store router /
   response model) without leaking raw SQL errors or stack traces to the client (coding conventions).
5. **Rebuild parts on reload** — extend `HistoryMessage` (`frontend/src/api/conversations.ts`) and the
   mapping in `frontend/src/pages/ChatPage.tsx` to reconstruct assistant-ui tool-call parts. Factor the
   live event→part logic out of `frontend/src/lib/runtime.ts` into a shared helper both paths call so a
   reloaded turn renders identically to a live one (same `RunSqlTool` table).
6. **Backfill/graceful old rows** — pre-existing messages have no tool data; they must still render
   (prose only, no crash). No destructive migration of historical rows.
7. **Tests** — backend: recorder persists + `GET /conversations/{id}` returns tool data; a legacy
   message with null tool data still serialises. Frontend: `ChatPage`/reload renders the SQL step +
   table from stored tool data; a legacy prose-only message renders without error. Extend the Playwright
   e2e (`frontend/e2e/`) so the re-login/reload journey asserts the table is present, not just the prose.
8. **Quality gates + browser verify** — `pytest`, `ruff check`, `ruff format --check`, `mypy`, frontend
   vitest + e2e all green; then reload an existing conversation in the browser and confirm the SQL step
   and table render with 0 console errors.

## Done when
- [x] Design choice recorded in `discussion.md` — a nullable JSON `tool_data` column on `messages`
      (option A). Additive, so no new decision record needed.
- [x] `messages` persists the structured tool calls/results; migration `b2c3d4e5f6a7` adds the column
      and applies cleanly (`alembic upgrade head` verified against Postgres).
- [x] `/chat` saves the `run_sql` call (SQL) and its structured result with the assistant turn.
- [x] `GET /conversations/{id}` returns the tool data; only rows/preview are stored — no raw
      model-facing SQL/error text leaks.
- [x] Reloading an existing conversation renders the `run_sql` step + result table identically to a live
      turn (browser-verified after a full page reload, 0 console errors); live and reload share the one
      `toolCallParts` helper.
- [x] Legacy messages (no tool data) still render prose-only (null `tool_data` → plain string content).
- [x] Unit tests (backend `_persistable_result` + capturing recorder; frontend `toolCallParts`) + the
      Playwright reload assertion cover it; integration round-trip asserts `tool_data` survives Postgres.
- [x] All four backend gates + frontend biome/tsc/vitest are green.

---
Log → [`discussion.md`](discussion.md)
