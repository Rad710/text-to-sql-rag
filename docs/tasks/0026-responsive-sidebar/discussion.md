# 0026 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Surfaced by the screenshot QA pass — at 390px the fixed `w-60` sidebar didn't collapse, so
  the thread was ~150px wide and user bubbles wrapped one letter per line. Owner picked approach A
  (collapsible overlay drawer).
- 2026-08-11: Brief course-correction — I started reaching for React state; owner asked to keep it
  CSS-driven. Clarified the split: the responsive layout, drawer positioning, slide transition, and
  backdrop are all pure CSS (Tailwind `md:` + `translate-x`); only the open/close **toggle** needs state.
  Owner chose "minimal React state" over the pure-CSS checkbox hack because it auto-closes cleanly when a
  conversation is selected (the checkbox hack can't do that without a ref anyway).
- 2026-08-11: Implemented — `ConversationList` is now `open`/`onClose`-controlled (mobile: fixed
  off-canvas drawer + `bg-black/40` backdrop; desktop: `md:static` column). `App` holds `sidebarOpen`, a
  `md:hidden` hamburger (lucide `Menu`) opens it, and `startNew`/`openConversation` close it. Header
  truncates the title and hides the subtitle/username below `sm` so it fits a phone.
- 2026-08-11: Browser-verified at 390px (hamburger → drawer slides in over dimmed content → tap a
  conversation → drawer closes, thread full-width and readable) and at 1280px (unchanged static sidebar,
  no hamburger). Added an e2e test asserting the drawer geometry (off-screen `x<0` closed → `x>=0` open) —
  `toBeVisible` wouldn't have caught an off-canvas element. `pnpm e2e` 3/3, unit 21, lint/build green.
