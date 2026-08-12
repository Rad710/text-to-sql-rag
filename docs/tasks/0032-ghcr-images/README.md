---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: [0014, 0031]  # task numbers that must finish first
decision: null          # decisions/NNNN that governs this task, if any
---

# 0032 — Publish images to GHCR; prod pulls instead of building

## Goal
Instead of the production stack building the `app` and `web` images from source on the VM, publish them to
the **GitHub Container Registry** (`ghcr.io/rad710/text-to-sql-rag/{app,web}`) from CI and have
`docker-compose.prod.yml` **pull** them. Deploys become "pull + up" — fast, reproducible, and no build
toolchain on the server.

## Context
Builds on the deploy stack from [0014](../0014-deploy-live/) and the Docker relocation in
[0031](../0031-docker-folder/) (both images already build from the repo-root context). Owner chose a
**GitHub Actions workflow** (not manual pushes) and **prod-only** pulling (the dev base stack keeps
building). Design log → [`discussion.md`](discussion.md).

## Plan
1. Add `.github/workflows/release.yml`: on a `v*` tag or manual dispatch, a matrix over `{app, web}` logs
   in to GHCR with the built-in `GITHUB_TOKEN` (`permissions: packages: write`), computes tags/labels with
   `docker/metadata-action` (semver + `v*` ref + short SHA + `latest`), and builds/pushes each image from
   the repo-root context (`docker/Dockerfile`, `docker/frontend.Dockerfile`) with GHA layer caching.
2. `docker/docker-compose.prod.yml`: add `image: ghcr.io/rad710/text-to-sql-rag/{app,web}:${IMAGE_TAG:-latest}`
   to the `app` and `web` services, keeping `build:` as a from-source fallback.
3. Add `LABEL org.opencontainers.image.source=…` to `docker/Dockerfile` and the `serve` stage of
   `docker/frontend.Dockerfile` so the GHCR packages link to the repo even on manual builds.
4. Docs: `DEPLOY.md` §2/§6 become `pull` → `up -d` (with a GHCR visibility/login note + `IMAGE_TAG` pin);
   README's Deploy section switches to pull (Quickstart keeps `--build` for clone-and-run). `.env.example`
   gets an optional `IMAGE_TAG` line (owner applies — permission-blocked).

## Done when
- [x] `release.yml` exists, valid YAML, matrix builds+pushes both images to GHCR via `GITHUB_TOKEN`
      (tags: version + `v*` + short SHA + `latest`).
- [x] `docker-compose.prod.yml` `app`/`web` carry `image: ghcr.io/…:${IMAGE_TAG:-latest}` (+ `build:`
      fallback); `docker compose -f docker/docker-compose.prod.yml config` resolves to those refs.
- [x] Source labels on both images; DEPLOY.md + README describe the pull-based deploy + GHCR auth/visibility.
- [x] Backend/frontend code untouched; existing gates unaffected.

## Owner follow-ups (outside my permissions / require the remote)
- `.env.example`: add `IMAGE_TAG=latest` (optional pin) — permission-blocked from tooling.
- First release: `git tag v0.1.0 && git push origin v0.1.0` (or run the workflow manually), then make the
  two GHCR packages public (or `docker login ghcr.io` on the VM) so they can be pulled.

---
Log → [`discussion.md`](discussion.md)
