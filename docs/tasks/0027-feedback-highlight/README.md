---
status: in-progress
updated: 2026-08-11
depends_on: [0020]
decision: null
---

# 0027 — Highlight the selected 👍/👎 feedback

## Goal
After clicking like/dislike on an answer, the chosen button stays visibly highlighted, so the user knows
their rating registered. Before, both thumbs looked identical after a click — no confirmation.

## Context
The action bar uses assistant-ui's `ActionBarPrimitive.FeedbackPositive/Negative`, which already set
`data-submitted="true"` on the selected button (the local runtime tracks the choice). They just had no
style for that state, so nothing changed visually. Purely a styling fix.

## Plan
1. `components/assistant-ui/thread.tsx` — add `data-[submitted]:text-primary
   data-[submitted]:[&_svg]:fill-current` to the FeedbackPositive/Negative `TooltipIconButton`s, so the
   chosen thumb turns primary-colored and **filled** (vs muted outline when unselected).
2. `App.test.tsx` — assert the clicked thumb gets `data-submitted="true"` and the other does not.

## Done when
- [x] Clicking 👍/👎 highlights the chosen thumb (filled, primary); clicking the other flips it. Still
      POSTs the rating (one-per-message upsert). Browser-verified (data-submitted + filled svg; switch works).
- [x] `App.test.tsx` asserts the highlight; `pnpm lint`/`build`/`test` green (21 tests).
- [ ] Committed.

## Note
The highlight reflects the current session's click. Reloading a conversation does not re-show a prior
rating as highlighted (feedback state isn't fetched back on reload) — a known, minor limitation, not in
scope here.

---
Log → [`discussion.md`](discussion.md)
