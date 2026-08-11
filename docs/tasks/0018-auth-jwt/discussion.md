# 0018 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Task opened (decision 0009 — JWT). Stage A = backend (hashing/JWT/register/login/protected
  `/chat`); Stage B = the React login UI. `bcrypt` used directly (passlib's bcrypt compat is fragile on
  bcrypt 5); `pyjwt` for HS256 tokens. JWT signing secret from env (`JWT_SECRET`), dev default for local.
- 2026-08-11: **Stage A — backend (done).** `app/auth/`: `security.py` (bcrypt + PyJWT HS256),
  `service.py` (async register/authenticate over the store), `router.py` (`/auth/register`, `/auth/login`,
  `/auth/me`), `deps.py` (`get_current_user` from the Bearer token, 401 on missing/invalid). Wired the
  router in and required a valid token on `/chat`. Config gained `jwt_secret`/`jwt_algorithm`/
  `jwt_expiry_min` (env; dev default lengthened to ≥32 bytes to satisfy PyJWT). Tests: pure hash + JWT
  round-trips, `/chat` 401-without-token, and an integration register→login→me flow driven with an httpx
  `AsyncClient` in a single event loop (TestClient spins a loop per request, which breaks a module-global
  async engine). 112 unit + integration green; mypy strict clean.
- 2026-08-11: **Stage B — frontend (done).** `auth.ts` (token in localStorage + `login`/`register`/
  `fetchMe`), `LoginScreen.tsx` (bilingual login/register form with error handling), `App.tsx` gated:
  loading → login → authenticated app (header shows the name + a "Salir" logout). `runtime.ts` sends
  `Authorization: Bearer …` on `/chat`; the Vite dev proxy now forwards `/auth`. Tests reworked: mount →
  login screen (unauth), and an authenticated flow asserting the Bearer header + the streamed table.
  **Browser-verified** via Playwright: registered a user → the protected `/chat` streamed the result
  behind the token → logout returned to the login screen, 0 console errors.
