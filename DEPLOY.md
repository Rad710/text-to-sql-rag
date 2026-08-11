# Deploy

Production deployment for the text-to-SQL RAG assistant. The target is a **single Linux VM running
docker-compose** (decision: task [0014](docs/tasks/0014-deploy-live/)); the public URL runs the
**mock-only demo** (`DEPLOY_MODE=demo`) — deterministic, no API cost, safe to leave open. The real-LLM
(`live`) path is the same stack with a few env vars flipped (see below).

## Architecture

```
                     :80 (put TLS in front)
Internet ─▶ web (nginx) ─┬─ /                 → built SPA (static)
                         └─ /chat /auth /...   → proxy → app (FastAPI :8000, internal)
                                                          ├─ mysql   (synthetic query DB, read-only user)
                                                          └─ postgres (app store: users/convos/feedback)
```

One origin (nginx) → no CORS. Only nginx publishes a port; the app, MySQL and Postgres stay on the
internal compose network. The app applies Alembic migrations on boot and builds the RAG corpus on the
first `/chat`.

## Prerequisites

- A Linux VM with **Docker** + **Docker Compose v2** (`docker compose version`).
- Ports: `80` open to the internet (and `443` if you terminate TLS on the box).
- This repo checked out on the VM.

## 1. Configure secrets

The prod compose requires a few secrets via a local **`.env`** (gitignored — never commit real values).
Create `.env` next to `docker-compose.prod.yml`:

```dotenv
# Deploy flavor: demo = mock LLM (safe/free public demo); live = real LLM + strict limits (decision 0010)
DEPLOY_MODE=demo
LLM_MODE=mock

# JWT signing secret — MUST be >=32 bytes, unique per deploy. Generate one:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET=replace-with-a-long-random-secret

# MySQL (synthetic query DB): root bootstraps the container; llm_readonly is the app's read-only user
MYSQL_ROOT_PASSWORD=replace-mysql-root
DB_USER=llm_readonly
DB_PASSWORD=replace-readonly

# Postgres (app store) password for the `app` user
APP_DB_PASSWORD=replace-postgres

# --- live mode only (DEPLOY_MODE=live): point at a real OpenAI-compatible server ---
# LLM_BASE_URL=http://your-ollama-or-vllm:11434/v1
# LLM_MODEL=llama3.1
# LLM_API_KEY=ollama
```

## 2. Bring it up

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First boot: MySQL applies `db/init/*` (schema + synthetic seed + read-only grant), Postgres starts, the
app runs `alembic upgrade head`, then nginx comes up. Watch progress with:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app
```

## 3. Verify

```bash
curl -fsS http://localhost/health         # {"status":"ok",...} proxied through nginx
```

Then open `http://<vm-ip-or-domain>/` → register a user → ask "facturación total por ruta" → you should
see the tool steps, a result table (toggle to the chart), and be able to 👍/👎 the answer.

## 4. TLS (recommended)

nginx here listens on plain `:80`. For HTTPS, put a TLS terminator in front — simplest options:

- **Caddy** on the host (automatic Let's Encrypt): reverse-proxy `yourdomain` → `localhost:80`.
- **Cloudflare** proxy in front of the VM.
- Or add certs + a `443` server block to `frontend/nginx.conf` and publish `443` on `web`.

## 5. Demo ↔ live (real LLM)

The hosted demo is `DEPLOY_MODE=demo` (mock). To run a real model, stand up an OpenAI-compatible server
(Ollama or vLLM) reachable from the box and set in `.env`:

```dotenv
DEPLOY_MODE=live      # 20 req/min + 100/day per user (decision 0010)
LLM_MODE=openai
LLM_BASE_URL=http://your-ollama-or-vllm:11434/v1
LLM_MODEL=llama3.1
LLM_API_KEY=ollama
```

then `docker compose -f docker-compose.prod.yml up -d` (recreates `app`). See the README "Deploy modes"
and decisions [0010](docs/decisions/0010-rate-limiting-deploy-modes.md) / [0015](docs/tasks/0015-real-llm-config/).

## 6. Update / teardown / backup

```bash
git pull && docker compose -f docker-compose.prod.yml up -d --build   # deploy a new version
docker compose -f docker-compose.prod.yml logs -f                     # tail logs
docker compose -f docker-compose.prod.yml down                        # stop (keeps volumes)
docker compose -f docker-compose.prod.yml down -v                     # stop + DROP data volumes

# Back up the app store (users/conversations/feedback):
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U app dyr_app > dyr_app_backup.sql
```

Data lives in the named volumes `pgdata` (app store) and `mysqldata` (synthetic DB — reproducible from
`db/init`, so not critical to back up).
