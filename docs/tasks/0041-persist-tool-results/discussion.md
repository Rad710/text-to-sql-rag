# 0041 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-13: **Bug reproduced on the deployed VM** (Playwright, logged in as the Ivan demo user).
  Opening an existing conversation shows only the assistant prose and no SQL step / result table. The
  stored payload for one conversation was exactly:
  `{"role":"assistant","content":"I queried the database and ran the SQL to answer your question."}` —
  i.e. only the content-free mock filler. During a live turn the same question renders the `run_sql`
  step and a result table. (The one console error — Cloudflare `beacon.min.js` blocked by CSP — is
  unrelated.)

- 2026-08-13: **Root cause = persistence gap, not a rendering glitch.** The rich UI is built only from
  live SSE `tool_start` / `tool_result` events (`frontend/src/lib/runtime.ts:132-185`), and none of it
  is saved: the `messages` table stores only `role` + text `content` (`store/models.py:68`); `/chat`
  persists only the `answer` text (`api.py:151-156`); reload maps a stored message as bare text
  (`ChatPage.tsx:63`). Starkest with the mock because decision 0006 intentionally moved the table out of
  the prose into the structured `tool_result`, which we never persist (`llm/client.py:40-43`). Gap was
  introduced in task 0019 (conversation history) — it persisted prose only.

- 2026-08-13: **Open — how to persist the structured parts.** Options weighed:
  - **A. Nullable JSON column on `messages`** (e.g. `tool_data`) holding the assistant tool-call parts
    (tool name, args incl. SQL, structured result rows). One migration; reconstruct directly; matches
    the "one writable schema, Alembic" datastore. Legacy rows are just `NULL` → render prose-only.
    *Leading option — simplest change that fully fixes it.*
  - **B. Normalized `message_parts` table** (one row per tool call/result). More faithful, queryable,
    but more schema + join work than this fix needs right now.
  - **C. Persist the raw SSE event stream per assistant message and replay it on reload.** Most general
    (survives future event types) but stores transport detail and couples storage to the wire format.
  - Leaning **A**. Confirm with the owner before building; if it changes the datastore contract enough,
    add a short decision record that links back to 0006 and 0008.

- 2026-08-13: **Design note for the build** — factor the live event→assistant-ui-part mapping out of
  `runtime.ts` into a shared helper so the reload path (`ChatPage`) reconstructs identical parts. If
  they diverge, live and reloaded turns will render differently again. This is the main correctness risk
  of the task.

- 2026-08-13: **Built option A + verified end to end.** Backend: nullable `tool_data` JSON column on
  `messages` (models + Alembic `b2c3d4e5f6a7`); `/chat` accumulates tool steps from the stream
  (`_persistable_result` keeps run_sql rows / preview, never raw model text) → `recorder.finish` →
  `save_message`; `MessageOut` returns it. Frontend: extracted the event→part mapping into
  `lib/tool-parts.ts` (`toolCallParts` + `ToolStep`); `runtime.ts` (live) and `ChatPage` (reload) now
  both build parts through it, so a reloaded turn is identical to a live one. `HistoryMessage` carries
  `tool_data`.
  - **Verification** (isolated throwaway stack — own creds, ports 3306/5434, not `.env` or any other
    project): API round-trip showed the assistant turn persisting `tool_data = [search_schema, run_sql]`
    with the run_sql result `columns=[origin, destination, revenue], row_count=4`, user turn `null`.
    Browser (mock mode): asked a question → live SQL step + 4-row table; **full page reload** → reopened
    from persistence renders the identical SQL step + table, 0 console errors. The only intentional
    difference is the missing usage footer (steps·tokens·cost) — UI chrome, not persisted.
  - Gates green: backend ruff/format/mypy/pytest (+2 new unit tests), frontend biome/tsc/vitest (+3 new
    `tool-parts` tests), integration round-trip (`test_conversations` now asserts `tool_data`).
