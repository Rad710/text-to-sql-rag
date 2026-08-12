# 0030 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Why this task.** Owner flagged the frontend structure as not senior-level: flat `src/`,
  all components in one folder, tests co-located with source, no pages/routing (auth was a conditional
  render inside a ~200-line `App.tsx`), and — worst — an anonymous `void (async () => {…})()` IIFE in the
  mount effect ("horrible code"). Also asked for `async/await` + `Promise.all` over `.then` chains and
  4-space formatting. Behavior is fine; this is structure + formatting only.

- 2026-08-12: **Layout: layered vs. feature-based.** Proposed a feature-based `features/{auth,chat}/…`
  layout first; owner rejected it ("where did you get the features folder idea? i have never seen that").
  Chose **conventional layered** instead — `pages/ components/ hooks/ context/ api/ lib/ tests/` — the
  familiar Vite/React shape. `src/components/ui/**` and `src/components/assistant-ui/**` stay exactly where
  they are (generated shadcn/assistant-ui primitives that import each other via `@/components/…`; Biome
  already lint-excludes those paths). Only our own code moves. `@/* → src/*` alias unchanged.

- 2026-08-12: **Routing.** Adopted `react-router` v8.3.0 (the unified package). `App.tsx` becomes
  `<BrowserRouter><AuthProvider><TooltipProvider><AppRoutes/>`. `AppRoutes`: `/login` → `LoginPage`, `/`
  behind `ProtectedRoute` → `ChatPage`, `*` → redirect `/`. `ProtectedRoute`: `loading` → "Cargando…";
  no user → `<Navigate to="/login" replace/>`; else `<Outlet/>`. This replaces the old boolean render.

- 2026-08-12: **Killing the IIFE.** Root cause of the IIFE was one effect doing two awaits at once (load
  the user *and* the mode label) and wrapping them to `await Promise.all`. Split responsibilities:
  `AuthProvider` owns `user`/`loading` and loads the user in a **named** `async function loadUser()` guarded
  by an `active` cleanup flag (the React-docs pattern); the header mode label moves to its own
  `useServerMode()` hook with its own simple effect. No more anonymous self-invoking function, and each
  effect does one thing.

- 2026-08-12: **Tests location.** Owner wanted tests out of the source folders. Chose one top-level
  `src/tests/` tree mirroring source (`tests/`, `tests/api/`, `tests/lib/`). `vitest.config.ts` updated:
  `include:["src/tests/**/*.test.{ts,tsx}"]`, `setupFiles:["./src/tests/setup.ts"]`. `App.test.tsx` is now
  routing-aware (unauth `<App/>` lands on `/login`; authed renders `ChatPage`).

- 2026-08-12: **e2e.** The 3 Playwright specs need no changes: `goto("/")` on a fresh session redirects to
  `/login`, and Playwright auto-waits for the "Registrate" button that appears there; post-register the
  `LoginPage` redirect lands on `/`. CI runs them in mock mode. Verified the same journey manually in the
  browser (the running local API is in live mode, so the mock-dependent specs aren't run locally).

- 2026-08-12: **Verification.** `pnpm format` reindented the whole frontend to 4-space; `pnpm build` (tsc)
  clean — proves every moved import resolves; `pnpm lint` clean; `pnpm test` 22/22. Browser: unauth `/` →
  `/login` (form renders), login → `/` (ChatPage: header + mode label + sidebar with the "hola"
  conversation + welcome + composer), logout → `/login`; 0 console errors. Backend untouched. One cohesive
  restructure commit.
