---
status: in-progress
updated: 2026-08-11
depends_on: [0019, 0023]
decision: null
---

# 0026 — Responsive sidebar (mobile drawer)

## Goal
Fix the broken mobile layout: the fixed 240px conversation sidebar didn't collapse on narrow screens, so
the chat was crushed into ~150px and message bubbles wrapped one letter per line. Make the sidebar a
static column on desktop and an **off-canvas drawer** (hamburger + slide-in + backdrop) on mobile.

## Context
Found in the screenshot-driven QA pass (the app was desktop-only). Owner chose approach A — a collapsible
drawer that overlays the content — with the toggle held in minimal React state (the layout/positioning/
transition stay pure CSS via Tailwind breakpoints; only the `open` boolean is React, so it can auto-close
when a conversation is selected).

## Plan
1. `ConversationList.tsx` — controlled by `open` / `onClose`. Mobile: `fixed inset-y-0 left-0 z-40 w-72`
   drawer, `-translate-x-full` → `translate-x-0`, solid `bg-background`, `shadow-lg`, + a `bg-black/40`
   backdrop button. Desktop: `md:static md:translate-x-0 md:w-60 md:bg-muted/20` static column.
2. `App.tsx` — `sidebarOpen` state; a `Menu` (lucide) hamburger in the header shown only `md:hidden`;
   `startNew`/`openConversation` set it false (auto-close on select); header truncates the title and
   hides the subtitle + username below `sm`.
3. `e2e/app.spec.ts` — a mobile test asserting the drawer's geometry (off-screen `x < 0` until the
   hamburger is clicked, then `x >= 0`).

## Done when
- [x] Mobile: sidebar off-canvas, hamburger opens a drawer over a dimmed backdrop, auto-closes on select;
      chat is full-width and readable (no one-letter-per-line wrapping). Browser-verified at 390px.
- [x] Desktop unchanged: static sidebar, no hamburger, subtitle/username visible. Browser-verified.
- [x] e2e drawer geometry test added; `pnpm e2e` 3/3, unit 21, lint/build green.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
