# 0028 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: From the polish audit. Owner picked #1 (regenerate dup), #2 (session expiry), #4 (number
  formatting) to fix now.
- 2026-08-11: **#1** — confirmed the bug in the DB: a fresh 1-turn conversation showed **4 messages** after
  one Refresh click (regenerate re-POSTs /chat, which always persists). Correct regenerate would replace
  the last assistant message, which the store doesn't support. Chose to **remove the Reload button** (and
  the now-unused `RefreshCwIcon` import — tsc `noUnusedLocals` would otherwise fail the build) rather than
  ship a divergent history. Documented as "until the store supports replace-in-place".
- 2026-08-11: **#2** — `runtime.ts` only yielded "⚠️ {status}" for non-429 errors and never cleared the
  token, so an expired session lingered. Added an `onUnauthorized` seam (auth.ts) — the runtime calls
  `notifyUnauthorized()` on 401 (clears token + notifies), App registers `logout`, so it returns to the
  login screen. Browser-verified by injecting a garbage token then sending a message → bounced to login.
- 2026-08-11: **#4** — `formatCellValue` in chart-data.ts using `Intl.NumberFormat("es")`. Picked `es`
  (not `es-PY`) deliberately: its minimumGroupingDigits=2 means 4-digit numbers (years like 2024) are NOT
  grouped, while 5+ digit measures are (`8.000.000`, `165.500`) — so no year-mangling and no manual
  threshold. Numeric cells also right-align + `tabular-nums`. Updated App.test's cell assertion to the
  grouped value; added a formatter unit test.
- 2026-08-11: Verified — build/lint/test green (22 unit), e2e 3/3; browser-checked all three (grouped
  right-aligned table, no Refresh button, 401→login).
