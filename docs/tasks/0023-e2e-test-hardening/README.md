---
status: in-progress
updated: 2026-08-11
depends_on: [0014]
decision: null
---

# 0023 — Thorough test pass + Playwright e2e + hardening

## Goal
Prove the whole app works end-to-end and lock it in with automated tests: a **Playwright e2e** suite
(wired into CI) exercising the real browser journey against a live stack, plus targeted backend tests for
gaps found during a thorough manual pass — and fix the two input-validation gaps that pass surfaced.

## Context
A full exploratory pass (API sweep + browser) found the backend solid — auth, cross-user isolation
(conversations + feedback → 404), feedback upsert/edge cases (422 on bad rating), multi-turn persistence,
and logout/re-login history reload all correct. Two robustness gaps: **register accepted an invalid email
and a 1-char password** (both `201`). Owner decided: fix both (422 + surfaced in the UI) and wire the
e2e suite into CI.

## Plan
1. **Validation fix** — `app/auth/router.py`: `RegisterRequest.email: EmailStr`, `password:
   Field(min_length=8, max_length=128)`, `name: Field(min_length=1)`; `LoginRequest.email: EmailStr`.
   Add `email-validator` dep. `frontend/src/auth.ts`: map `422` → a friendly Spanish message.
2. **Backend tests** — `tests/test_auth.py`: register rejects bad email / short password (422), accepts a
   valid one; plus integration coverage for the isolation/feedback edge cases verified manually
   (cross-user 404, feedback upsert one-per-message, bad rating 422) where not already covered.
3. **Playwright e2e** — add `@playwright/test`; `frontend/playwright.config.ts` (chromium, `webServer`
   runs `pnpm dev`); `frontend/e2e/app.spec.ts`: full journey (register unique user → ask → tool steps +
   result table + chart toggle → 👍 feedback → multi-turn → logout → re-login restores history) + the
   register-validation errors. `pnpm e2e` script; ignore Playwright artifacts.
4. **CI** — a new `e2e` job: MySQL + Postgres services, seed + `alembic upgrade`, start uvicorn (mock),
   `playwright install --with-deps chromium`, run `pnpm e2e`.
5. Docs: README "End-to-end tests" note; this task folder.

## Done when
- [x] Register rejects invalid email + short password (`422`), UI shows the message; valid still works.
      (EmailStr + Field min_length; frontend maps 422; backend unit test.)
- [x] Backend gates green (`pytest`/`ruff`/`mypy`), coverage floor holds (86%); register-validation unit
      test added; isolation/feedback edge cases confirmed already covered by `test_conversations`.
- [x] `pnpm e2e` passes locally against a live stack — 2/2 (full journey + short-password validation).
- [x] CI `e2e` job added (MySQL + Postgres + mock API + chromium); existing jobs unaffected. YAML valid;
      confirmed on push.
- [x] Browser/e2e reverified end-to-end after the validation change; 0 console errors.
- [ ] Committed.

## Findings (from the thorough pass)
- Fixed: register accepted an invalid email + a too-short password. Now `422`, surfaced in the UI.
- Backend otherwise solid: auth, cross-user isolation (conversations + feedback → 404), feedback upsert,
  bad rating → 422, multi-turn persistence, logout/re-login reload — all correct.
- Console polish (fixed): added an inline SVG favicon (data URI → no `/favicon.ico` 404), and `fetchMe`
  now decodes the JWT `exp` and skips the `/auth/me` probe for an already-expired token (clears it and
  shows login) — so a returning user with a lapsed token no longer triggers a console `401`. Browser-
  verified: fresh load and expired-token reload both show **0 console errors** and no `/auth/me` request.
  (A token that's invalid-but-unexpired still 401s server-side — rare in real use; the check stays
  conservative and only skips on a parsed, past `exp`.)

---
Log → [`discussion.md`](discussion.md)
