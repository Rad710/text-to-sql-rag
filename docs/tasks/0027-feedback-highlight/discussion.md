# 0027 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Owner: clicking like/dislike gave no visual confirmation — "I do not know if it was liked
  or not". (I'd flagged this in the screenshot-QA pass as a minor polish item.)
- 2026-08-11: Checked the installed `@assistant-ui/react` — `ActionBarFeedbackPositive` already renders
  `{ "data-submitted": "true" }` when `isSubmitted` (the local runtime records the choice when the
  feedback adapter's `submit` is called). So the state existed; only the *style* was missing. Fixed by
  styling the submitted state on the FeedbackPositive/Negative buttons: `data-[submitted]:text-primary
  data-[submitted]:[&_svg]:fill-current` → the chosen thumb turns primary and filled.
- 2026-08-11: Browser-verified — after 👍: data-submitted="true", svg fill = primary (solid); 👎 stays
  muted outline. Clicking 👎 flips it (👍 → outline, 👎 → filled) and POSTs rating −1 (upsert). Added an
  App.test assertion (clicked thumb has data-submitted, the other doesn't) — this also confirmed the local
  runtime tracks the state in jsdom. 21 unit tests, lint/build green.
