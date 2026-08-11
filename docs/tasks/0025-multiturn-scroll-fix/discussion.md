# 0025 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Owner hit it live: "second message starts to add blanks, the scroll bar becomes tiny and
  keeps getting tinier and moving up, and I don't even see the response." Reproduced with Playwright
  against the running dev stack — sampled `document.documentElement.scrollHeight` after the 2nd message:
  `334821 → 345459 → … → 451839` over 3.6 s (≈ +10,600 px / 300 ms, unbounded).
- 2026-08-11: Diagnosed by walking the DOM for very tall nodes. The leaf was an **empty `<div>` with an
  inline `height: 1,688,000px`** inside `mb-14 flex flex-col gap-y-6 empty:hidden` — assistant-ui's
  auto-scroll spacer. The whole chain up to the app root (`flex h-full flex-col`) had grown, i.e. nothing
  clamped it to the viewport. Confirmed `index.css` set **no height** on `html/body/#root`, so `h-full`
  (height:100%) had no fixed ancestor to resolve against → unclamped viewport → spacer feedback loop.
  First message fit within the screen (spacer ≈ 0) → looked fine; the 2nd overflowed → runaway.
- 2026-08-11: Fix — `html, body, #root { height: 100%; }` in `@layer base`. After HMR, re-ran the 2-message
  flow: height series flat at **720 px** across 12 samples, tallest element 1340 px, the second answer
  (driver table + text + feedback bar) fully visible. 0 console errors.
- 2026-08-11: Added an e2e regression assertion (bounded `scrollHeight` after multi-turn) — the old test
  passed through this bug because `toBeVisible` ignores runaway height. `pnpm e2e` 2/2, unit 21, lint/build
  green. Lesson logged for future UI tests: assert layout/geometry, not just element presence.
