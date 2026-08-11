# 0023 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Thorough exploratory pass (curl API sweep + Playwright browser) against a live stack
  (mock LLM, throwaway Postgres :55432, live MySQL). Backend came back **solid**: register/login, wrong
  password + unknown user → 401, `/auth/me` token handling, `/chat` auth + 422 body validation,
  conversation ownership (cross-user + unknown → 404), feedback upsert (one-per-message, flip +1→−1),
  bad rating → 422, cross-user + unknown message → 404, multi-turn persistence (1 convo / 4 msgs), and
  logout→re-login history reload. Two robustness gaps found: **register accepted an invalid email
  (`notanemail` → 201) and a 1-char password (→ 201)** — no input validation.
- 2026-08-11: Owner decided: fix both gaps + wire the e2e into CI. Fix — `RegisterRequest.email:
  EmailStr`, `password: Field(min_length=8, max_length=128)`, `name: Field(min_length=1)`; `LoginRequest.
  email: EmailStr`; added `email-validator`. Frontend maps a 422 → "Revisá el email y que la contraseña
  tenga al menos 8 caracteres". Backend unit test (422 for bad email / short password / empty name, no DB
  via a stubbed session).
- 2026-08-11: **The stricter email validation bit the tests** — EmailStr rejects the reserved `.test` TLD
  ("special-use or reserved name"), so fixtures using `@dyr.test` on the register path now 422. Correct
  behavior (you can't email a `.test` address); switched register-path fixtures to `@example.com` (the
  direct `User(...)` constructions in test_store/test_api stay — they don't validate). Also had to bump
  two test passwords that were < 8 chars (`s3cret!` → `s3cret!pw`, the dup-register `x` → a valid one) so
  they exercise the 409/flow instead of tripping the new 422.
- 2026-08-11: Playwright e2e — `@playwright/test` 1.62, `frontend/playwright.config.ts` (chromium,
  `webServer` runs `pnpm dev`; the API/DBs are external), `frontend/e2e/app.spec.ts` (full journey +
  short-password validation message). Scoped vitest to `src/**/*.test.{ts,tsx}` so it no longer tries to
  run the `*.spec.ts` e2e files; excluded Playwright output from Biome + gitignore.
- 2026-08-11: e2e first run **caught a real environment bug**: the full journey 500'd on register with
  `relation "users" does not exist`. Root cause: the integration suite I'd just run drops the app tables
  for isolation (leaving only `alembic_version`), so the shared throwaway PG had no schema for the live
  app. Not a product bug — a local sequencing artifact (CI gives each job a fresh DB). Recreated the
  schema (drop `alembic_version` + `alembic upgrade head`) and both e2e tests pass in ~4s.
- 2026-08-11: CI `e2e` job added (MySQL + Postgres services, seed + alembic, uv + pnpm, `playwright
  install --with-deps chromium`, start uvicorn mock in background, `pnpm e2e`). Verified locally: e2e 2/2,
  backend 128 unit + 22 integration green, coverage 86%, frontend lint/build/vitest green, ruff/mypy clean.
