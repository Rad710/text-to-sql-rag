---
status: in-progress
updated: 2026-08-11
depends_on: [0019, 0020]
decision: null
---

# 0028 — Polish fixes: regenerate dup, session expiry, number formatting

Three issues found in the polish audit (the "are there others we didn't check?" pass):

## #1 — Regenerate double-persisted (correctness)
Clicking the action bar's **Refresh/regenerate** re-POSTed `/chat`, which persists every turn — so the
stored conversation grew a **duplicate turn** (verified: a 1-turn convo became 4 messages) while the UI
showed one, diverging on reload. Proper regenerate needs replace-in-place in the store, which we don't
have. **Fix:** remove the Reload button (and its unused icon import) until the store supports replace.

## #2 — Session expiry left a raw 401 (UX)
An expired/invalid token mid-session made `/chat` return 401, which the SPA rendered as "⚠️ 401" in the
thread while keeping you "logged in". **Fix:** an `onUnauthorized` seam in `auth.ts`; the runtime calls
`notifyUnauthorized()` on a 401 (clears the token) and App resets to the login screen.

## #3 — Raw numbers (cosmetic)  → filed as #4 below
Result tables showed `8000000.00`. **Fix:** `formatCellValue` (es locale) groups measures
(`8.000.000`) and right-aligns numeric cells; the "es" locale leaves 4-digit years ungrouped, so it
doesn't mangle year columns.

## Files
- `components/assistant-ui/thread.tsx` — drop `ActionBarPrimitive.Reload` + the `RefreshCwIcon` import.
- `auth.ts` — `onUnauthorized` / `notifyUnauthorized`. `runtime.ts` — 401 → notify + friendly text.
  `App.tsx` — register `logout` as the unauthorized handler.
- `lib/chart-data.ts` — `formatCellValue`. `components/result-view.tsx` — format + right-align cells.
- Tests: `chart-data.test.ts` (formatting), `App.test.tsx` (cell shows `8.000.000`).

## Done when
- [x] Regenerate button gone; no duplicate turns written (was the repro). Browser-verified action bar.
- [x] A 401 mid-session bounces to login (token cleared), no raw "401" in the thread. Browser-verified
      with a corrupted token.
- [x] Numeric cells grouped + right-aligned; years not mangled. Browser-verified ("8.000.000").
- [x] `pnpm lint`/`build`/`test` green (22 unit); `pnpm e2e` 3/3.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
