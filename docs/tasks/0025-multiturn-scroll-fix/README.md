---
status: in-progress
updated: 2026-08-11
depends_on: [0010, 0023]
decision: null
---

# 0025 — Fix runaway layout on the second message (+ regression guard)

## Goal
Fix a browser-reported bug: sending a **second** message made the page grow blank space endlessly, the
scrollbar shrank to nothing, and the answer was unreachable. Pin the height cascade so the thread scrolls
internally, and add an e2e assertion so this class of bug can't return.

## Context
Reported by the owner while running the app. Reproduced with Playwright: after the 2nd message the
document height grew ~10,600 px every 300 ms (unbounded). Cause: assistant-ui's thread viewport has a
**scroll-to-bottom spacer** (an empty div sized so the last message can reach the top). The app root uses
Tailwind `h-full` (`height: 100%`), but **`html` / `body` / `#root` had no height set**, so `h-full`
resolved to content height — the viewport was never clamped to the screen. With one message the content
fit (spacer ≈ 0); the second message overflowed, and the unclamped viewport + spacer fed each other into
an infinite growth loop.

The existing e2e did send a 2nd message, but only asserted the answer *text* was visible —
`toBeVisible` ignores runaway height, so it passed while the UI was broken.

## Plan
1. `frontend/src/index.css` — pin the cascade: `html, body, #root { height: 100%; }` in `@layer base`,
   so the app's `h-full` chain resolves to the viewport and the thread scrolls internally.
2. `frontend/e2e/app.spec.ts` — after the multi-turn step, assert `document.scrollHeight` stays bounded
   (< 3× viewport) so a runaway layout fails the test.

## Done when
- [x] Second message no longer grows the page; the answer is reachable (height stays ~1 viewport).
      Browser-verified: height series flat at 720 px (was 334k→451k and climbing).
- [x] e2e regression assertion added and passing; it would fail on the old behaviour (~450k px).
- [x] Frontend gates green (`pnpm lint` / `build` / `test`, 21 unit; `pnpm e2e` 2/2).
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
