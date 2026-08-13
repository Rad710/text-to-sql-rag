# 0039 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-13: **Origin.** Owner reviewed the frontend and flagged global-var usage / hacky patterns and
  asked for a file-by-file audit. Audit result: the React fundamentals are largely sound; the real
  issues concentrate in four files — `api/auth.ts` (`unauthorizedHandler` global), `lib/active-conversation.ts`,
  `api/feedback.ts` (id global), and `lib/runtime.ts` (module-singleton adapter + usage-string regex).
  Biome + tsc were already clean; deps current. So: patterns, not lint/versions.
- 2026-08-13: **Auth fork.** The `localStorage` JWT is the one security issue. Owner rejected the
  "acceptable for a demo" framing and chose **hardened bearer JWT (short-lived access + refresh + strict
  CSP)** over httpOnly cookies. Honest caveat recorded in decision 0013: no-cookies means the refresh
  token sits in `localStorage`, so the security is from short access TTL + rotation/reuse-detection +
  CSP, not from hiding the token.
- 2026-08-13: **Refresh-store depth.** Chose the production-correct `refresh_tokens` table with rotation
  + reuse detection (replaying a revoked `jti` revokes the whole family) over a lighter per-user
  `token_version`.
- 2026-08-13: **De-string-ify.** `runtime.ts` used to concatenate the usage footer into the answer text
  part and strip it back with a regex. Now answer and usage are **separate** parts; `historyText` drops
  the trailing usage part structurally (we only ever emit one answer + one usage part) — no regex.
- 2026-08-13: **Verified.** Backend: ruff/format/mypy + 132 unit tests (refresh/reuse/logout covered by
  the opt-in integration flow). Frontend: biome + tsc + 21 tests + production build. e2e has no token
  assumptions (drives the UI). `.env.example` change (JWT_ACCESS_EXPIRY_MIN / JWT_REFRESH_EXPIRY_DAYS
  replacing JWT_EXPIRY_MIN) handed to the owner — file is permission-blocked for the agent.
