---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: [0010]      # task numbers that must finish first
decision: null          # decisions/NNNN that governs this task, if any
---

# 0030 — Restructure the frontend to a conventional layered layout

## Goal
The React app worked but its structure was not senior-level: nearly everything sat flat in `src/` plus a
single `src/components/` folder, unit tests were co-located with source, there were no pages or routing
(auth was a conditional render inside a 200-line `App.tsx`), and the mount effect used an anonymous
`void (async () => {…})()` IIFE. This task reorganizes the frontend into a familiar, conventional layered
layout — real `/login` and `/` routes with a route guard, a top-level tests tree, the IIFE removed, and
4-space formatting — **with no change to app behavior**. It reads like a codebase a reviewer expects.

## Context
Frontend introduced in [0010](../0010-react-frontend/); auth/history/feedback/charts/responsive work in
0016–0029 grew `App.tsx` into a monolith. Owner asked for a proper Vite/React structure (real pages,
separated tests), the anonymous IIFE gone, `async/await` + `Promise.all` over `.then` chains, and 4-space
formatting. After weighing feature-based vs. layered, owner chose **conventional layered** (rejected
`features/`) and **react-router** with real routes + a guard. Design log → [`discussion.md`](discussion.md).

## Plan
1. Prerequisite: commit **0029** first so this is a clean, cohesive restructure commit.
2. `pnpm add react-router@8.3.0`.
3. Move files with `git mv` (preserve history) into the layered tree:
   - `api/` — `auth.ts` (was `src/auth.ts`), `conversations.ts` (`history.ts`), `feedback.ts`, `server.ts`.
   - `lib/` — `runtime.ts`, `active-conversation.ts` (`conversation.ts`); `chart-data.ts` stays in `lib/`.
   - `components/` — `ConversationSidebar.tsx` (`ConversationList.tsx`), `LoginForm.tsx` (`LoginScreen.tsx`),
     `ResultView.tsx`, `ResultChart.tsx`, `RunSqlTool.tsx` (PascalCase). `ui/` + `assistant-ui/` untouched.
   - `tests/` — one top-level tree mirroring source (`setup.ts`, `App.test.tsx`, `api/auth.test.ts`,
     `lib/chart-data.test.ts`, `lib/runtime.test.ts`).
4. Add routing + context: `context/AuthProvider.tsx` (+ `hooks/useAuth.ts`), `hooks/useServerMode.ts`,
   `components/ProtectedRoute.tsx`, `components/AppRoutes.tsx`, `pages/LoginPage.tsx`, `pages/ChatPage.tsx`.
   Extract `components/ChatPane.tsx` + `components/Welcome.tsx` from the old `App.tsx`; new `App.tsx` is just
   `<BrowserRouter><AuthProvider><TooltipProvider><AppRoutes/>`.
5. Remove the IIFE: `AuthProvider` owns `user`/`loading`; its effect uses a **named** async function with an
   `active` cleanup flag (the React-docs pattern). The header mode label becomes its own `useServerMode()`
   hook, so the artificial `Promise.all` that forced the IIFE is gone.
6. Fix every import (cross-area via `@/…`, relative within an area); `biome.json` → `indentWidth: 4`, then
   `pnpm format`; `vitest.config.ts` → `include:["src/tests/**"]`, `setupFiles:["./src/tests/setup.ts"]`.

## Done when
- [x] Layered tree in place (`pages/ components/ hooks/ context/ api/ lib/ tests/`); `ui/`+`assistant-ui/`
      untouched; moves done with `git mv` (history preserved).
- [x] Anonymous IIFE removed; effects use named async functions with cleanup flags.
- [x] Real routes: `/login` + `/` behind a `ProtectedRoute`; auth state in `AuthProvider`/`useAuth`.
- [x] Whole frontend reformatted to 4-space (Biome), lint clean.
- [x] `pnpm build` (tsc) clean, `pnpm lint` clean, `pnpm test` green (22/22).
- [x] Browser-verified: unauth `/` → `/login`; login → `/` (ChatPage renders); logout → `/login`; 0 console
      errors.
- [x] App behavior unchanged; backend untouched (its gates stay green).

---
Log → [`discussion.md`](discussion.md)
