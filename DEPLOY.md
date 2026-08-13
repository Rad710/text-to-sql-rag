# Deploy

Production deployment for the text-to-SQL RAG assistant. The target is a **single Linux VM running
docker-compose** (decision: task [0014](docs/tasks/0014-deploy-live/)); the public URL runs the
**mock-only demo** — deterministic, no API cost, safe to leave open. The real-LLM path is the same
stack with a few env vars flipped (see below).

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

All configuration is a single **`.env`** (gitignored — never commit real values). Copy the committed
template and fill in the secrets:

```bash
cp .env.example .env
```

Then edit `.env` and set at least these (see the comments in the file for the rest):

- `JWT_SECRET` — a unique **≥32-byte** value: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `QUERY_DB_ROOT_PASSWORD`, `QUERY_DB_PASSWORD` — the MySQL admin + read-only-user passwords
- `APP_DB_PASSWORD` — the Postgres `app` user password
- keep `LLM_MODE=mock` for the mock demo; set `WEB_PORT=8080` if port 80 is taken

For a **live** (real-LLM) deploy, set `LLM_MODE=openai` with `LLM_BASE_URL` / `LLM_MODEL` /
`LLM_API_KEY` at an OpenAI-compatible server, plus stricter `RATE_LIMIT_PER_MIN` / `RATE_LIMIT_PER_DAY`
to bound per-account cost (see §5).

## 2. Bring it up

The `app` and `web` images are pre-built by the **release workflow** (`.github/workflows/release.yml`) and
published to GHCR (`ghcr.io/rad710/text-to-sql-rag/{app,web}`). The VM just pulls them — no source build:

```bash
docker compose -f docker/docker-compose.prod.yml pull      # fetch app + web from GHCR
docker compose -f docker/docker-compose.prod.yml up -d
```

Pin a specific release with `IMAGE_TAG=v1.2.3` in `.env` (defaults to `latest`). GHCR packages start
**private**; to pull them either make the two packages public (repo → Packages → each → Package settings →
Change visibility → Public) or authenticate on the VM first with a token that has `read:packages`:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u rad710 --password-stdin
```

No published images yet (or want to build on the box)? Build from source instead — the compose file keeps a
`build:` fallback: `docker compose -f docker/docker-compose.prod.yml up -d --build`.

First boot: MySQL starts, the one-shot **Flyway** service applies `mock-db/migration/*` (schema +
synthetic seed + read-only grant) and exits, Postgres starts, the app runs `alembic upgrade head`, then
nginx comes up. Watch progress with:

```bash
docker compose -f docker/docker-compose.prod.yml ps
docker compose -f docker/docker-compose.prod.yml logs -f app
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
- Or add certs + a `443` server block to `docker/nginx.conf` and publish `443` on `web`.

## 5. Demo ↔ live (real LLM)

The hosted demo runs the mock LLM. To run a real model, stand up an OpenAI-compatible server
(Ollama or vLLM) reachable from the box and set in `.env`:

```dotenv
LLM_MODE=openai
LLM_BASE_URL=http://your-ollama-or-vllm:11434/v1
LLM_MODEL=llama3.1
LLM_API_KEY=ollama
RATE_LIMIT_PER_MIN=20      # bound per-account cost (decisions 0010, 0012)
RATE_LIMIT_PER_DAY=100
```

then `docker compose -f docker/docker-compose.prod.yml up -d` (recreates `app`). See the README "Rate limits"
and decisions [0010](docs/decisions/0010-rate-limiting-deploy-modes.md) /
[0012](docs/decisions/0012-drop-deploy-mode.md) / [0015](docs/tasks/0015-real-llm-config/).

## 6. Update / teardown / backup

```bash
docker compose -f docker/docker-compose.prod.yml pull && \
  docker compose -f docker/docker-compose.prod.yml up -d              # deploy the latest published images
docker compose -f docker/docker-compose.prod.yml logs -f                     # tail logs
docker compose -f docker/docker-compose.prod.yml down                        # stop (keeps volumes)
docker compose -f docker/docker-compose.prod.yml down -v                     # stop + DROP data volumes

# Back up the app store (users/conversations/feedback):
docker compose -f docker/docker-compose.prod.yml exec postgres pg_dump -U app dyr_app > dyr_app_backup.sql
```

Data lives in the named volumes `pgdata` (app store) and `mysqldata` (synthetic DB — reproducible from
`mock-db/migration`, so not critical to back up).

## 7. SQL MCP server (optional)

The standalone MCP server (`app/mcp_server.py`, README "SQL MCP server") is a separate, optional tool —
it is **not** part of this compose stack. Its default **stdio** transport is the safe local mode (a
client launches it as a subprocess; no network surface). If you run the **`--http`** transport, treat it
like the API: it exposes read-only SQL execution over the network, so bind it to localhost or put
auth/TLS in front before exposing it publicly. The SQL-safety layer still blocks writes either way, but
HTTP without a proxy is an open query surface.
