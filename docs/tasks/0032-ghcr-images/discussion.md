# 0032 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Why.** Owner wants the prod stack to pull pre-built images from their GitHub registry
  rather than build on the box: "not use docker compose pulling the images from my github repo where i
  would push the images." Registry = GHCR (the natural "my GitHub" choice), images
  `ghcr.io/rad710/text-to-sql-rag/{app,web}` (owner lowercased, per GHCR rules; remote is
  `github.com:Rad710/text-to-sql-rag`).

- 2026-08-12: **Two choices confirmed before building.** (1) Build+push via a **GitHub Actions workflow**
  (auto, GITHUB_TOKEN, no secrets) rather than manual `docker push`. (2) **Prod-only** pulling — the dev
  base stack keeps `build:` so local edits still rebuild fast; only `docker-compose.prod.yml` references
  the registry.

- 2026-08-12: **Keep `build:` in prod alongside `image:`.** Pure `image:`-only would break `git clone` +
  run for anyone without registry access (private packages, or before the first release). Compose allows
  both keys: `docker compose … pull` uses the GHCR image; `… up --build` builds locally and tags it as the
  same `image:` ref. So the primary documented flow is pull, with `--build` as an explicit from-source
  fallback. (If the owner prefers strict pull-only, drop the `build:` blocks — one-line follow-up.)

- 2026-08-12: **Tagging.** `docker/metadata-action` emits `1.2.3` (semver from the `v1.2.3` tag), the raw
  `v1.2.3` ref, a short SHA, and `latest`. Prod pins via `${IMAGE_TAG:-latest}` in the compose file, so a
  deploy can target a specific release by setting `IMAGE_TAG` in `.env` (defaults to `latest`).

- 2026-08-12: **GHCR ↔ repo link + visibility.** Added `LABEL org.opencontainers.image.source` to both
  images (the workflow's metadata-action also injects it, but the LABEL covers manual builds too) so GHCR
  attaches the package to the repo. Noted in DEPLOY.md that GHCR packages start **private** — pull needs
  either making them public or `docker login ghcr.io` with a `read:packages` token.

- 2026-08-12: **Multi-stage label placement.** First put the source LABEL on the frontend `build` stage —
  wrong: labels only persist in the stage they're declared, and the final image is the `serve` stage.
  Moved it to `serve`.

- 2026-08-12: **Verification.** `release.yml` parses (both matrix images app/web; steps checkout →
  buildx → login → metadata → build-push; `permissions: packages: write`). `docker compose -f
  docker/docker-compose.prod.yml config` resolves the `app`/`web` services to
  `ghcr.io/rad710/text-to-sql-rag/{app,web}:latest` with the `build:` fallback intact. Actually pushing to
  GHCR and pulling on a VM is the owner's step (needs the remote + a pushed tag); can't be exercised from
  here.
