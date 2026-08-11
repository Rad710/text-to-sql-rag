# 0016 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Implemented. API `ChatRequest` gained a `Turn {role, content}` model + `history` list;
  threaded `history` through `stream`/`ask`/`answer_question`/`stream_answer`, which now build
  `[system, *history, {user: question}]`. The mock's `_first_user_message` became `_latest_user_message`
  so a multi-turn convo answers the current question, not the first. The frontend adapter sends
  `{question, history}`, mapping prior turns to `{role, content}` text and **stripping the UI-only
  token/cost footer** from assistant turns (verified: turn 2's `/chat` body carried clean prior turns).
  Tests: `test_history_is_prepended_before_the_question`, `test_mock_keys_off_the_latest_user_turn`,
  `test_chat_accepts_conversation_history` + `test_chat_rejects_bad_history_role`, and a frontend body
  assertion. 104 backend tests + frontend green; browser-verified via Playwright (network inspection).
- 2026-08-11: **Known limitation** — the deterministic keyword mock can't use the context, so follow-ups
  read as fresh questions until a real model is wired (task 0015). The plumbing (context → model) is done.
