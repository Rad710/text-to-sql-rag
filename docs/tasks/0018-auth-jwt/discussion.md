# 0018 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Task opened (decision 0009 — JWT). Stage A = backend (hashing/JWT/register/login/protected
  `/chat`); Stage B = the React login UI. `bcrypt` used directly (passlib's bcrypt compat is fragile on
  bcrypt 5); `pyjwt` for HS256 tokens. JWT signing secret from env (`JWT_SECRET`), dev default for local.
